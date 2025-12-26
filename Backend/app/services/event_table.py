from pydantic import BaseModel
from typing import Optional, List
from sqlmodel import Session, SQLModel

from app.services.base import BaseService
from app.models.event_table import EventTable
from app.models.websocket import WebsocketMessage, notify_game_players

class PublicEventTable(SQLModel):
    id : int
    game_id: int
    action: str
    turn_played: int
    player_id: Optional[int] = None
    target_player: Optional[int]
    target_set: Optional[int]
    target_card: Optional[int]
    target_secret: Optional[int]
    completed_action: bool

class EventTableFilter(BaseModel):
    turn_played__eq: Optional[int] = None
    game_id__eq: Optional[int] = None
    player_id__eq: Optional[int] = None
    completed_action__eq: Optional[bool] = None
    action__eq: Optional[str] = None
    action__in: Optional[List[str]] = None

class EventTableService(BaseService[EventTable]):
    _metaclass = EventTable
    
    async def update(self, session, oid: int, data: dict) -> Optional[EventTable]:
        result = await super().update(session, oid, data)
        if result:
            session.refresh(result)
            await notify_game_players(result.game_id, WebsocketMessage(model="event_table", action="update", data=result.model_dump(), dest_game=result.game_id, dest_user=None))
        return result
