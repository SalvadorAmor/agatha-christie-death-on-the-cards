from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from pydantic import BaseModel
from typing import List
from app.database.engine import db_session

from app.models.chat import Chat
from app.models.game import GameStatus
from app.services.game import GameService
from app.services.player import PlayerService
from app.services.chat import CreateChatMessage, ChatService

chat_router = APIRouter(prefix="/api/chat")

class CreateChatMessageDTO(BaseModel):
    game_id: int
    owner_id: int
    content: str

@chat_router.post("/", response_model=Chat)
async def create_chat_message(dto: CreateChatMessageDTO, session: Session = Depends(db_session)):

    game_service = GameService()
    player_service = PlayerService()
    chat_service = ChatService()

    game = game_service.read(session=session, oid=dto.game_id)
    if not game:
        raise HTTPException(404, "Juego no existente")
    
    player = player_service.read(session=session, oid=dto.owner_id)

    if not player:
        raise HTTPException(404, "Jugador no existente")
    if player.game_id != dto.game_id:
        raise HTTPException(412, "El jugador debe ser de la partida")
    
    if len(dto.content) > 300:
        raise HTTPException(412, "El mensaje es demasiado largo")
    
    if game.status in [GameStatus.WAITING, GameStatus.FINALIZED]:
        raise HTTPException(412, "No se pueden mandar mensajes en este momento de la partida")
    
    create_message_data = CreateChatMessage(game_id=dto.game_id, owner_name= player.name, content=dto.content)

    message = await chat_service.create(session=session, data=create_message_data.model_dump())

    return message

@chat_router.get("/{gid}", response_model=List[Chat])
def search_messages(gid: int, session: Session = Depends(db_session)):

    chat_service = ChatService()
    game_service = GameService()

    game = game_service.read(session=session, oid=gid)
    if not game:
        raise HTTPException(404, "Juego no existente")

    messages = chat_service.search(session=session, filterby={"game_id__eq": gid})

    return messages