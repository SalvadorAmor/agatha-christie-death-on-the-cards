from typing import Dict, List, Optional

from fastapi import APIRouter, WebSocket, Depends
from sqlmodel import Session
import json

from starlette.websockets import WebSocketDisconnect

from app.database.engine import db_session
from app.models.websocket import WebsocketMessage, GAME_CONNECTIONS, LOBBY_CONNECTIONS
from app.services.player import PlayerService

ws_router = APIRouter(prefix="/ws")

import logging
_logger = logging.getLogger(__name__)


@ws_router.websocket("/monolithic")
async def websocket(connection: WebSocket, token: Optional[str] = None):
    await connection.accept()
    if token: # TODO: No deberia tener comportamiento condicional
        session: Session = next(db_session())
        player = await PlayerService().read_by_token(session=session, token=token)
        if player is not None:
            if player.game_id not in GAME_CONNECTIONS:
                GAME_CONNECTIONS[player.game_id] = {}
            GAME_CONNECTIONS[player.game_id][player.id] = connection
            session.close()
            while True:
                try:
                    data = await connection.receive_text()
                    parsed_message = WebsocketMessage(**json.loads(data))
                    if parsed_message.dest_game:
                        if parsed_message.dest_game in GAME_CONNECTIONS:
                            users: Dict[int, WebSocket] = GAME_CONNECTIONS[parsed_message.dest_game]
                            for k, v in users.items():
                                await v.send_text(parsed_message.model_dump_json())
                except WebSocketDisconnect:
                    del GAME_CONNECTIONS[player.game_id][player.id]
                    break
                except Exception as e:
                    _logger.warning(f"Error en websocket: {e}")
                    break
        else:
            await connection.close()
            session.close()
    else: # Aca tenemos conexiones generales, sin Jugador
        LOBBY_CONNECTIONS.append(connection)
        while True:
            try:
                data = await connection.receive_text()
            except WebSocketDisconnect:
                LOBBY_CONNECTIONS.remove(connection)
                break
            for c in LOBBY_CONNECTIONS:
                try:
                    await c.send_text(data)
                except WebSocketDisconnect:
                    LOBBY_CONNECTIONS.remove(c)