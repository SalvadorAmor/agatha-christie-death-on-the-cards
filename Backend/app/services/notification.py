from typing import Optional

from sqlmodel import Session, select

from app.controllers.websocket import GAME_CONNECTIONS, LOBBY_CONNECTIONS
from app.models.player import Player
from app.models.websocket import WebsocketMessage
import logging

_logger = logging.getLogger(__name__)

async def read_by_token(self, session: Session, token: str) -> Optional[Player]:
    statement = select(Player).where(Player.token == token)
    result = session.exec(statement).all()
    return result[0] if result else None

