from datetime import datetime
from typing import Optional
from sqlmodel import Session, select

from pydantic import BaseModel

from app.models.player import Player
from app.models.websocket import WebsocketMessage, notify_game_players, notify_lobby
from app.services.base import BaseService
import logging

_logger = logging.getLogger(__name__)

class CreatePlayer(BaseModel):
    name: str
    game_id:Optional[int] = None
    date_of_birth:datetime
    avatar: str
    token:str

class PlayerFilter(BaseModel):
    id__eq: Optional[int] = None
    name__eq: Optional[str] = None
    game_id__eq: Optional[int] = None
    position__eq: Optional[int] = None

class PlayerService(BaseService[Player]):
    _metaclass = Player

    async def read_by_token(self, session: Session, token: str) -> Optional[Player]:
        statement = select(Player).where(Player.token == token)
        result = session.exec(statement).all()
        return result[0] if result else None


    async def create(self, session: Session, data: dict) -> Optional[Player]:
        result = await super().create(session, data)
        if result:
            session.refresh(result)
            await notify_game_players(game_id=result.game_id, message=WebsocketMessage(model="player", action="create", data=result.model_dump(), dest_game=result.game_id, dest_user=None))
            await notify_lobby(WebsocketMessage(model="player", action="create", data=result.model_dump(), dest_game=result.game_id, dest_user=None))
        return result


    async def update(self, session: Session, oid: int, data: dict) -> Optional[Player]:
        result = await super().update(session, oid, data)
        if result:
            session.refresh(result)
            await notify_game_players(game_id=result.game_id, message=WebsocketMessage(model="player", action="update", data=result.model_dump(), dest_game=result.game_id, dest_user=None))
        return result


    async def delete(self, session: Session, oid: int) -> Optional[int]:
        model_data = session.get(Player, oid).model_dump()
        result = await super().delete(session, oid)
        if model_data and result:
            await notify_game_players(model_data['game_id'], WebsocketMessage(model="player", action="delete", data=model_data, dest_game=model_data['game_id'], dest_user=None))
            await notify_lobby(WebsocketMessage(model="player", action="delete", data=model_data, dest_game=model_data['game_id'], dest_user=None))
        return result