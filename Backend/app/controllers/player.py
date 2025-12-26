import secrets
from datetime import datetime, timezone
from app.models.game import GameStatus

from app.database.engine import db_session
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.models.player import PublicPlayer, Player
from app.services.game import GameService
from app.services.player import PlayerService, CreatePlayer, PlayerFilter


class CreatePlayerDTO(BaseModel):
    player_name: str
    player_date_of_birth: datetime
    avatar: str

class DeletePlayerDTO(BaseModel):
    token:str

player_router=APIRouter(prefix="/api/player")

@player_router.get(path='/{pid}', response_model=PublicPlayer)
def get_player(pid:int, session: Session = Depends(db_session)):
    service = PlayerService()
    player = service.read(session=session,oid=pid)

    if not player:
        raise HTTPException(404,detail="Jugador no encontrado")

    return player

@player_router.post('/search', response_model=list[PublicPlayer])
def search_player(dto: PlayerFilter, session: Session = Depends(db_session)):
    service = PlayerService()
    players = service.search(session=session, filterby=dto.model_dump(exclude_none=True))
    return players

@player_router.post(path='/{gid}', response_model=Player)
async def create_player(gid:int,dto:CreatePlayerDTO,session: Session = Depends(db_session)):
    if dto.player_date_of_birth > datetime.now(timezone.utc):
        raise HTTPException(400,detail="Fecha de nacimiento invalida")

    if len(dto.player_name) > 12:
        raise HTTPException(400, "El nombre de jugador no debe superar los 12 caracteres")

    game_service = GameService()
    game = game_service.read(session=session,oid=gid)

    if not game:
        raise HTTPException(status_code=404, detail="El juego a unirse no fue encontrado")

    if game.status != GameStatus.WAITING:
        raise HTTPException(status_code=400, detail="La partida ya ha comenzado")

    player_service = PlayerService()
    players_in_game = player_service.search(session=session,filterby={"game_id__eq":gid})

    if len(players_in_game) >= game.max_players:
        raise HTTPException(status_code=400, detail="Partida Llena")

    token = secrets.token_urlsafe(32)

    create_player_data = CreatePlayer(name=dto.player_name, game_id=gid, date_of_birth=dto.player_date_of_birth
                                      ,token=token, avatar=dto.avatar)

    player = await player_service.create(session=session, data=create_player_data.model_dump(exclude_none=True))

    return player

@player_router.delete('/{pid}', response_model=int)
async def delete_player(pid: int, dto:DeletePlayerDTO, session: Session = Depends(db_session)):
    service = PlayerService()
    player = service.read(session=session, oid=pid)

    if not player:
        raise HTTPException(404, "No se pudo encontrar el jugador a eliminar")
    if player.token != dto.token:
        raise HTTPException(401, detail="No se puede abandonar partida por: Token Invalido")

    gameservice = GameService()
    player_game = gameservice.read(session=session,oid=player.game_id)

    if player_game:
        if player_game.status == GameStatus.STARTED:
            raise HTTPException(400, detail="No se puede abandonar una partida en progreso")

    did = await service.delete(session=session, oid=pid)

    return did


