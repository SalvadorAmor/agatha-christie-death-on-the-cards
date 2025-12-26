from time import sleep
from unittest.mock import MagicMock, AsyncMock

import pytest
import json
from fastapi.testclient import TestClient
from more_itertools.more import side_effect
from starlette.websockets import WebSocketDisconnect

from app.models.websocket import GAME_CONNECTIONS, LOBBY_CONNECTIONS, WebsocketMessage
from tests.conftest import PlayerFactory


@pytest.mark.asyncio
async def test_ws_connect_with_invalid_token(mocker, test_client: TestClient):
    # Given
    previous_game_connections = len(LOBBY_CONNECTIONS)
    # When/Then
    # El servidor debería no aceptar la conexión
    with test_client.websocket_connect("/ws/monolithic"):
        assert len(LOBBY_CONNECTIONS) == previous_game_connections + 1


@pytest.mark.asyncio
async def test_ws_broadcast_to_game_players(mocker, test_client: TestClient):
    # Given
    fake_player = PlayerFactory(id=1, game_id=777, token="valid")
    mocker.patch("app.controllers.websocket.PlayerService.read_by_token", return_value=fake_player)

    message = WebsocketMessage(
        action="chat",
        model="message",
        dest_user=None,
        dest_game=777,
        data={"text": "hola"}
    )

    def send_text_side_effect():
        sleep(0.3)
        return message.model_dump_json()

    mock_receive_text = mocker.patch("starlette.websockets.WebSocket.receive_text", side_effect=send_text_side_effect)

    with test_client.websocket_connect("/ws/monolithic?token=valid") as ws1:
        ws1.send_text(message.model_dump_json())
        assert 1 in GAME_CONNECTIONS[777].keys()
    mock_receive_text.assert_called()


@pytest.mark.asyncio
async def test_ws_broadcast_to_game_players_ws_disconnect(mocker, test_client: TestClient):
    # Given
    fake_player = PlayerFactory(id=1, game_id=777, token="valid")
    mocker.patch("app.controllers.websocket.PlayerService.read_by_token", return_value=fake_player)

    message = WebsocketMessage(
        action="chat",
        model="message",
        dest_user=None,
        dest_game=777,
        data={"text": "hola"}
    )

    def receive_text_side_effect():
        sleep(0.3)
        return message.model_dump_json()

    mock_receive_text = mocker.patch("starlette.websockets.WebSocket.receive_text", side_effect=receive_text_side_effect)

    def send_text_side_effect(_):
        raise WebSocketDisconnect()

    mock_receive_text = mocker.patch("starlette.websockets.WebSocket.send_text", side_effect=send_text_side_effect)

    with test_client.websocket_connect("/ws/monolithic?token=valid") as ws1:
        ws1.send_text(message.model_dump_json())
    mock_receive_text.assert_called()


@pytest.mark.asyncio
async def test_ws_broadcast_to_game_players_exception(mocker, test_client: TestClient):
    # Given
    fake_player = PlayerFactory(id=1, game_id=777, token="valid")
    mocker.patch("app.controllers.websocket.PlayerService.read_by_token", return_value=fake_player)

    message = WebsocketMessage(
        action="chat",
        model="message",
        dest_user=None,
        dest_game=777,
        data={"text": "hola"}
    )

    def receive_text_side_effect():
        sleep(0.3)
        return message.model_dump_json()

    mock_receive_text = mocker.patch("starlette.websockets.WebSocket.receive_text", side_effect=receive_text_side_effect)

    def send_text_side_effect(_):
        raise Exception()

    mock_receive_text = mocker.patch("starlette.websockets.WebSocket.send_text", side_effect=send_text_side_effect)

    with test_client.websocket_connect("/ws/monolithic?token=valid") as ws1:
        ws1.send_text(message.model_dump_json())
    mock_receive_text.assert_called()


@pytest.mark.asyncio
async def test_ws_broadcast_to_game_players_not_found(mocker, test_client: TestClient):
    fake_session = MagicMock()
    mock_db_session = mocker.patch("app.database.engine.db_session", return_value=iter([fake_session]))

    mock_read_by_token = mocker.patch(
        "app.controllers.websocket.PlayerService.read_by_token",
        return_value=None
    )

    mock_send_text = mocker.patch("starlette.websockets.WebSocket.send_text")

    with test_client.websocket_connect("/ws/monolithic?token=invalid") as ws:
        sleep(0.1)
        ws.send_text("test")

    mock_send_text.assert_not_called()
    mock_read_by_token.assert_called_once()


@pytest.mark.asyncio
async def test_ws_lobby_broadcast_and_websocket_disconnect(mocker, test_client: TestClient):
    # Given
    LOBBY_CONNECTIONS.clear()

    mock_ws_ok = AsyncMock()
    mock_ws_disconnect = AsyncMock()
    mock_ws_error = AsyncMock()

    mock_ws_ok.send_text = AsyncMock()
    mock_ws_disconnect.send_text = AsyncMock(side_effect=WebSocketDisconnect())
    mock_ws_error.send_text = AsyncMock(side_effect=Exception("unexpected"))

    LOBBY_CONNECTIONS.extend([mock_ws_ok, mock_ws_disconnect, mock_ws_error])

    mock_receive_text = mocker.patch(
        "starlette.websockets.WebSocket.receive_text",
        side_effect=["test", WebSocketDisconnect()],
    )

    # When
    with test_client.websocket_connect("/ws/monolithic") as ws:
        ws.send_text("test")

    # Then
    mock_ws_ok.send_text.assert_awaited_with("test")

    assert mock_ws_disconnect not in LOBBY_CONNECTIONS

    assert mock_ws_error in LOBBY_CONNECTIONS

    assert mock_receive_text.called

    LOBBY_CONNECTIONS.clear()
