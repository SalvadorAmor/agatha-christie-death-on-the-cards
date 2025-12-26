from pydantic import BaseModel
from sqlmodel import Session
from typing import Optional
from datetime import datetime, timezone

from app.services.base import BaseService
from app.models.chat import Chat
from app.models.websocket import notify_game_players, WebsocketMessage

class CreateChatMessage(BaseModel):
    game_id: int
    owner_name: Optional[str] = None
    content: str

class ChatService(BaseService[Chat]):
    _metaclass = Chat

    async def create(self, session: Session, data: dict) -> Optional[Chat]:
        data_with_timestamp = {**data, "timestamp": datetime.now(timezone.utc).isoformat()}
        result = await super().create(session, data_with_timestamp)
        if result:
            session.refresh(result)
            await notify_game_players(game_id=result.game_id, message=WebsocketMessage(model="chat", action="create", data=result.model_dump(), dest_game=result.game_id, dest_user=None))
        return result