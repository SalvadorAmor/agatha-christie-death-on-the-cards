from typing import Union, Optional

from pydantic import BaseModel

from typing import Dict, List

from starlette.websockets import WebSocket

import logging

_logger = logging.getLogger(__name__)

GAME_CONNECTIONS: Dict[int, Dict[int, WebSocket]] = {}
LOBBY_CONNECTIONS: List[WebSocket] = []


class WebsocketMessage(BaseModel):
    action: str
    model: str
    dest_user: Optional[int] = None
    dest_game: Optional[int]
    data: dict | List[dict]

async def notify_game_players(game_id: int, message: WebsocketMessage):
    for user_id, connection in GAME_CONNECTIONS.get(game_id, {}).items():
        try:
            await connection.send_text(message.model_dump_json())
        except Exception as e:
            _logger.warning(f"Error enviando mensaje websocket a user {user_id} en game {game_id}: {e}")

async def notify_lobby(message: WebsocketMessage):
    for connection in LOBBY_CONNECTIONS:
        try:
            await connection.send_text(message.model_dump_json())
        except Exception as e:
            _logger.warning(f"Error enviando mensaje websocket a lobby: {e}")