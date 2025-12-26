from unittest.mock import AsyncMock, ANY

from app.models.chat import Chat
from app.models.game import GameStatus
from tests.conftest import GameFactory, PlayerFactory


def test_create_chat_message_game_not_found(mocker, test_client):
    mocker.patch("app.controllers.chat.GameService.read", return_value=None)

    response = test_client.post("/api/chat/", json={"game_id": 1, "owner_id": 1, "content": "hola"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Juego no existente"


def test_create_chat_message_player_not_found(mocker, test_client):
    game = GameFactory(id=1, status=GameStatus.STARTED)

    mocker.patch("app.controllers.chat.GameService.read", return_value=game)
    mocker.patch("app.controllers.chat.PlayerService.read", return_value=None)

    response = test_client.post("/api/chat/", json={"game_id": game.id, "owner_id": 1, "content": "hola"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Jugador no existente"


def test_create_chat_message_player_not_in_game(mocker, test_client):
    game = GameFactory(id=1, status=GameStatus.STARTED)
    player = PlayerFactory(game_id=999)

    mocker.patch("app.controllers.chat.GameService.read", return_value=game)
    mocker.patch("app.controllers.chat.PlayerService.read", return_value=player)

    response = test_client.post("/api/chat/", json={"game_id": game.id, "owner_id": player.id, "content": "hola"})

    assert response.status_code == 412
    assert response.json()["detail"] == "El jugador debe ser de la partida"


def test_create_chat_message_content_too_long(mocker, test_client):
    game = GameFactory(id=1, status=GameStatus.STARTED)
    player = PlayerFactory(game_id=game.id)
    long_message = "x" * 301

    mocker.patch("app.controllers.chat.GameService.read", return_value=game)
    mocker.patch("app.controllers.chat.PlayerService.read", return_value=player)

    response = test_client.post("/api/chat/", json={"game_id": game.id, "owner_id": player.id, "content": long_message})

    assert response.status_code == 412
    assert response.json()["detail"] == "El mensaje es demasiado largo"


def test_create_chat_message_invalid_game_status(mocker, test_client):
    game = GameFactory(id=1, status=GameStatus.WAITING)
    player = PlayerFactory(game_id=game.id)

    mocker.patch("app.controllers.chat.GameService.read", return_value=game)
    mocker.patch("app.controllers.chat.PlayerService.read", return_value=player)

    response = test_client.post("/api/chat/", json={"game_id": game.id, "owner_id": player.id, "content": "hola"})

    assert response.status_code == 412
    assert (response.json()["detail"] == "No se pueden mandar mensajes en este momento de la partida")


def test_create_chat_message_success(mocker, test_client):
    game = GameFactory(id=1, status=GameStatus.STARTED)
    player = PlayerFactory(game_id=game.id)
    payload = {"game_id": game.id, "owner_id": player.id, "content": "hola"}
    created_message = Chat(
        id=1,
        game_id=game.id,
        owner_name=player.name,
        content=payload["content"],
        timestamp="2024-01-01T00:00:00Z",
    )

    mocker.patch("app.controllers.chat.GameService.read", return_value=game)
    mocker.patch("app.controllers.chat.PlayerService.read", return_value=player)
    mock_create = mocker.patch("app.controllers.chat.ChatService.create", new_callable=AsyncMock, return_value=created_message)

    response = test_client.post("/api/chat/", json=payload)

    assert response.status_code == 200
    assert response.json() == created_message.model_dump(mode="json")
    mock_create.assert_awaited_once_with(
        session=ANY,
        data={
            "game_id": game.id,
            "owner_name": player.name,
            "content": payload["content"],
        },
    )


def test_search_chat_messages_game_not_found(mocker, test_client):
    mocker.patch("app.controllers.chat.GameService.read", return_value=None)

    response = test_client.get("/api/chat/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "Juego no existente"


def test_search_chat_messages_success(mocker, test_client):
    game = GameFactory(id=1)
    messages = [
        Chat(
            id=1,
            game_id=game.id,
            owner_name="jugador_1",
            content="hola",
            timestamp="2024-01-01T00:00:00Z",
        ),
        Chat(
            id=2,
            game_id=game.id,
            owner_name="jugador_2",
            content="adios",
            timestamp="2024-01-01T01:00:00Z",
        ),
    ]

    mocker.patch("app.controllers.chat.GameService.read", return_value=game)
    mock_search = mocker.patch("app.controllers.chat.ChatService.search", return_value=messages)

    response = test_client.get(f"/api/chat/{game.id}")

    assert response.status_code == 200
    assert response.json() == [message.model_dump(mode="json") for message in messages]
    mock_search.assert_called_once_with(
        session=ANY,
        filterby={"game_id__eq": game.id},
    )
