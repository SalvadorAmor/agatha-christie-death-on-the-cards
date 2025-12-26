from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List
from sqlmodel import Session
from pydantic import BaseModel

from app.controllers.utils import reveal_secret
from app.database.engine import db_session
from app.models.game import GameStatus
from app.models.secret import Secret
from app.services.game import GameService
from app.services.secret import SecretService, SecretFilter
from app.services.player import PlayerService
secret_router = APIRouter(prefix="/api/secret")

class UpdateSecretDTO(BaseModel):
    owner: Optional[int] = None
    revealed: Optional[bool] = None

@secret_router.get("/{sid}", response_model=Secret)
def get_secret(sid: int, session: Session = Depends(db_session)):
    service = SecretService()
    secret = service.read(session=session, oid=sid)

    if not secret:
        raise HTTPException(404, detail="Secreto no encontrado")

    return secret

@secret_router.patch("/{sid}", response_model=Secret)
async def update_secret(sid: int, token: str, dto: UpdateSecretDTO, session: Session = Depends(db_session)):
    secret_service = SecretService()
    secret = secret_service.read(session=session, oid=sid)
    
    if not secret:
        raise HTTPException(404, detail="Secreto no encontrado")
    
    player_service = PlayerService()
    player = player_service.read(session=session, oid=secret.owner)

    if not player:
        raise HTTPException(404, detail="Jugador no encontrado")
    
    if token != player.token:
        raise HTTPException(401, detail="Autorizacion invalida")

    secret_updated = await secret_service.update(session=session, oid=sid, data=dto.model_dump(exclude_none=True))
    
    return secret_updated

@secret_router.post("/search", response_model=List[Secret])
def search_secret(dto: SecretFilter, session:Session = Depends(db_session)):
    service = SecretService()
    secret = service.search(session=session, filterby=dto.model_dump(exclude_none=True))
    return secret
