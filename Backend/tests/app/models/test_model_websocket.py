import pytest
from unittest.mock import AsyncMock, Mock
from app.models.websocket import GAME_CONNECTIONS, LOBBY_CONNECTIONS, WebsocketMessage
from app.models.websocket import notify_game_players, notify_lobby

@pytest.mark.asyncio
async def test_notify_game_players_success():
    # Given
    fake_ws = AsyncMock()
    GAME_CONNECTIONS[1] = {42: fake_ws}

    message = WebsocketMessage(action="test", model="game", dest_user=None, dest_game=1, data={"info": "ok"})

    # When
    await notify_game_players(1, message)

    # Then
    fake_ws.send_text.assert_awaited_once_with(message.model_dump_json())

    # Cleanup
    GAME_CONNECTIONS.clear()


@pytest.mark.asyncio
async def test_notify_game_players_exception(caplog):
    # Given
    fake_ws = AsyncMock()
    fake_ws.send_text.side_effect = Exception("fail")
    GAME_CONNECTIONS[1] = {42: fake_ws}

    message = WebsocketMessage(action="test", model="game", dest_user=None, dest_game=1, data={"info": "ok"})

    # When
    with caplog.at_level("WARNING"):
        await notify_game_players(1, message)

    # Then
    assert "Error enviando mensaje websocket a user 42 en game 1" in caplog.text

    # Cleanup
    GAME_CONNECTIONS.clear()


@pytest.mark.asyncio
async def test_notify_lobby_success():
    # Given
    fake_ws1 = AsyncMock()
    fake_ws2 = AsyncMock()
    LOBBY_CONNECTIONS.extend([fake_ws1, fake_ws2])

    message = WebsocketMessage(action="test", model="lobby", dest_user=None, dest_game=None, data={"info": "ok"})

    # When
    await notify_lobby(message)

    # Then
    fake_ws1.send_text.assert_awaited_once_with(message.model_dump_json())
    fake_ws2.send_text.assert_awaited_once_with(message.model_dump_json())

    # Cleanup
    LOBBY_CONNECTIONS.clear()


@pytest.mark.asyncio
async def test_notify_lobby_exception(caplog):
    # Given
    fake_ws = AsyncMock()
    fake_ws.send_text.side_effect = Exception("fail")
    LOBBY_CONNECTIONS.append(fake_ws)

    message = WebsocketMessage(action="test", model="lobby", dest_user=None, dest_game=None, data={"info": "ok"})

    # When
    with caplog.at_level("WARNING"):
        await notify_lobby(message)

    # Then
    assert "Error enviando mensaje websocket a lobby" in caplog.text

    # Cleanup
    LOBBY_CONNECTIONS.clear()
