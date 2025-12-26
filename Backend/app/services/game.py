from datetime import datetime, timedelta

import asyncio

from sqlalchemy.sql.expression import delete
from sqlmodel import Session
from app.models.player import Player
from app.models.websocket import WebsocketMessage, notify_game_players, notify_lobby
from app.services.base import BaseService, T
from app.models.game import Game, GameStatus
from pydantic import BaseModel
from typing import Optional
import logging

from app.services.event_table import EventTableService

_logger = logging.getLogger(__name__)

NOT_SO_FAST_TIME = 6

class CreateGame(BaseModel):
    """ Informacion base para crear un Game """
    name: str
    password: Optional[str] = None
    min_players: Optional[int] = 2
    max_players: Optional[int] = 6
    owner: int


class GameFilter(BaseModel):
    """ Filtro para Games """
    id__eq: Optional[int] = None
    password__is_null: Optional[bool] = None
    status__eq: Optional[GameStatus] = None


class GameService(BaseService[Game]):
    _metaclass = Game

    async def update(self, session: Session, oid: int, data: dict) -> Optional[Game]:
        result = await super().update(session, oid, data)
        if result:
            session.refresh(result)
            await notify_game_players(game_id=result.id, message=WebsocketMessage(model="game", action="update", data=result.model_dump(), dest_game=result.id, dest_user=None))
        return result

    async def create(self, session: Session, data: dict) -> Optional[T]:
        result = await super().create(session, data)
        if result:
            session.refresh(result)
            await notify_lobby(message=WebsocketMessage(model="game", action="create", data=result.model_dump(), dest_game=None, dest_user=None))
        return result

    async def delete(self, session: Session, oid: int) -> Optional[int]:
        session.exec(delete(Player).where(Player.game_id == oid))
        model_data = session.get(Game, oid).model_dump()
        result = await super().delete(session, oid)
        if model_data and result:
            await notify_game_players(model_data['id'], WebsocketMessage(model="game", action="delete", data=model_data, dest_game=model_data['id'], dest_user=None))
            await notify_lobby(WebsocketMessage(model="game", action="delete", data=model_data, dest_game=None, dest_user=None))
        return result

async def not_so_fast_status(game: Game, session: Session, obj_id: Optional[int] = None):
    game_service = GameService()
    event_service = EventTableService()

    canceled_times_event= await event_service.create(session=session,data={"game_id":game.id,"turn_played":game.current_turn,"action":"canceled_times", "target_card":0})

    await event_service.create(session=session,data={"game_id":game.id,"turn_played":game.current_turn,"action":"to_cancel"})

    game = await game_service.update(session=session, oid=game.id, data={"status": GameStatus.WAITING_FOR_CANCEL_ACTION, "timestamp": datetime.now()})

    last_timestamp: Optional[datetime] = None

    while game.timestamp != last_timestamp:
        last_timestamp = game.timestamp

        wake_up = last_timestamp + timedelta(seconds=NOT_SO_FAST_TIME)

        while True:

            seconds_left = max((wake_up - datetime.now()).total_seconds(), 0)
            session.refresh(game)

            if seconds_left <= 0 or game.timestamp != last_timestamp:
                break

            await notify_game_players(game.id, WebsocketMessage(model="timer", action="update_seconds",
                                                                data={"remaining_seconds": int(seconds_left)},
                                                                dest_game=game.id))
            

            await asyncio.sleep(1)

    session.refresh(canceled_times_event)

    return canceled_times_event.target_card % 2 != 0