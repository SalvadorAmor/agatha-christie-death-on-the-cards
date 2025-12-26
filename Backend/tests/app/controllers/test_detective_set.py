from unittest.mock import AsyncMock, ANY

import pytest
from app.models.card import Card, CardType
from app.models.detective_set import DetectiveSet
from app.models.game import GameStatus
from app.models.secret import Secret, SecretType
from tests.conftest import PlayerFactory, CardFactory, GameFactory


@pytest.fixture
def fake_set():
    fake_player = PlayerFactory()
    fake_card_detective = CardFactory(id=1, owner=fake_player.id, card_type=CardType.DETECTIVE)
    return DetectiveSet(id=1, owner=fake_player.id, detectives=[fake_card_detective], turn_played=2,game_id=1)


@pytest.mark.asyncio
async def test_create_detective_set_invalid_token(mocker, test_client):
    mocker.patch('app.controllers.detective_set.PlayerService.read_by_token', return_value=None)

    dto = {"detectives": [1]}
    response = test_client.post("/api/detective_set?token=invalid", json=dto)

    assert response.status_code == 401
    assert response.json()["detail"] == "Token inválido"


@pytest.mark.asyncio
async def test_create_detective_set_card_not_found(mocker, test_client):
    fake_game = GameFactory(status=GameStatus.TURN_START)
    fake_player = PlayerFactory(token="abc", game_id=fake_game.id)
    mocker.patch('app.controllers.detective_set.PlayerService.read_by_token', return_value=fake_player)
    mocker.patch('app.controllers.detective_set.CardService.read', return_value=None)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)

    dto = {"detectives": [1]}
    response = test_client.post("/api/detective_set?token=abc", json=dto)

    assert response.status_code == 404
    assert response.json()["detail"] == "Carta 1 no encontrada"



@pytest.mark.asyncio
async def test_create_detective_set_social_disgrace(mocker, test_client):
    fake_game = GameFactory(status=GameStatus.WAITING)
    fake_player = PlayerFactory(token="abc", game_id=fake_game.id,social_disgrace=True)
    mocker.patch('app.controllers.detective_set.PlayerService.read_by_token', return_value=fake_player)

    response = test_client.post("/api/detective_set?token=abc", json={"detectives": [1]})

    assert response.status_code == 400
    assert response.json()["detail"] == "En desgracia social no se puede jugar un set"


@pytest.mark.asyncio
async def test_create_detective_set_invalid_game_status(mocker, test_client):
    fake_game = GameFactory(status=GameStatus.WAITING)
    fake_player = PlayerFactory(token="abc", game_id=fake_game.id)
    mocker.patch('app.controllers.detective_set.PlayerService.read_by_token', return_value=fake_player)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)

    response = test_client.post("/api/detective_set?token=abc", json={"detectives": [1]})

    assert response.status_code == 400
    assert response.json()["detail"] == "No se puede crear el set: Ya se realizo una accion"


@pytest.mark.asyncio
async def test_create_detective_set_wrong_type(mocker, test_client):
    fake_game = GameFactory(status=GameStatus.TURN_START)
    fake_player = PlayerFactory(token="abc", game_id=fake_game.id)
    fake_card_other = Card(id=2, owner=fake_player.id, card_type=CardType.EVENT)
    fake_card_other.game_id = fake_game.id

    mocker.patch('app.controllers.detective_set.PlayerService.read_by_token', return_value=fake_player)
    mocker.patch('app.controllers.detective_set.CardService.read', return_value=fake_card_other)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)

    dto = {"detectives": [2]}
    response = test_client.post("/api/detective_set?token=abc", json=dto)

    assert response.status_code == 400
    assert response.json()["detail"] == "Solo se pueden crear sets con cartas detective"


@pytest.mark.asyncio
async def test_create_detective_set_card_already_in_set(mocker, test_client):
    fake_game = GameFactory(status=GameStatus.TURN_START)
    fake_player = PlayerFactory(token="abc", game_id=fake_game.id)
    card_in_set = CardFactory(owner=fake_player.id,card_type=CardType.DETECTIVE,set_id=99,game_id=fake_game.id)

    mocker.patch('app.controllers.detective_set.PlayerService.read_by_token', return_value=fake_player)
    mocker.patch('app.controllers.detective_set.CardService.read', return_value=card_in_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)

    response = test_client.post("/api/detective_set?token=abc", json={"detectives": [card_in_set.id]})

    assert response.status_code == 400
    assert response.json()["detail"] == "Alguna de las cartas ya se encuentra en un set"

@pytest.mark.asyncio
async def test_create_detective_set_not_owner(mocker, test_client):
    fake_game = GameFactory(status=GameStatus.TURN_START)
    fake_player = PlayerFactory(token="abc", game_id=fake_game.id)
    fake_card_detective = CardFactory(id=1, owner=fake_player.id, card_type=CardType.DETECTIVE, game_id=fake_game.id)
    fake_card_detective.owner = fake_player.id + 1  # distinto jugador
    mocker.patch('app.controllers.detective_set.PlayerService.read_by_token', return_value=fake_player)
    mocker.patch('app.controllers.detective_set.CardService.read', return_value=fake_card_detective)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)

    dto = {"detectives": [1]}
    response = test_client.post("/api/detective_set?token=abc", json=dto)

    assert response.status_code == 401
    assert response.json()["detail"] == "No puedes usar cartas que no te pertenecen"


@pytest.mark.asyncio
async def test_create_detective_set_ok(mocker, test_client, fake_set):
    fake_game = GameFactory(status=GameStatus.TURN_START)
    fake_player = PlayerFactory(token="abc", game_id=fake_game.id)
    fake_card_detective = CardFactory(id=1, owner=fake_player.id, card_type=CardType.DETECTIVE, game_id=fake_game.id)

    mocker.patch('app.controllers.detective_set.PlayerService.read_by_token', return_value=fake_player)
    mocker.patch('app.controllers.detective_set.CardService.read', return_value=fake_card_detective)
    mock_create = mocker.patch('app.controllers.detective_set.DetectiveSetService.create', return_value=fake_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.GameService.update')
    mock_not_so_fast = mocker.patch('app.controllers.detective_set.not_so_fast_status', new_callable=AsyncMock)
    mocker.patch('app.controllers.detective_set.ChatService.create')
    mock_not_so_fast.return_value = False

    dto = {"detectives": [1]}
    response = test_client.post("/api/detective_set?token=abc", json=dto)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fake_set.id
    mock_create.assert_called_once()

@pytest.mark.asyncio
async def test_create_detective_set_choose_player(mocker, test_client):
    fake_game = GameFactory(status=GameStatus.TURN_START)
    fake_player = PlayerFactory(token="abc", game_id=fake_game.id)
    detective_card = CardFactory(owner=fake_player.id,card_type=CardType.DETECTIVE,name="mr-satterthwaite",game_id=fake_game.id,)
    created_set = DetectiveSet(id=3, owner=fake_player.id, detectives=[detective_card],turn_played=2,game_id=fake_game.id)

    mocker.patch('app.controllers.detective_set.PlayerService.read_by_token', return_value=fake_player)
    mocker.patch('app.controllers.detective_set.CardService.read', return_value=detective_card)
    mocker.patch('app.controllers.detective_set.DetectiveSetService.create', return_value=created_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.GameService.update', new_callable=AsyncMock)
    mocker.patch('app.controllers.detective_set.ChatService.create')
    mock_not_so_fast = mocker.patch('app.controllers.detective_set.not_so_fast_status', new_callable=AsyncMock)
    mock_not_so_fast.return_value = False

    response = test_client.post("/api/detective_set?token=abc", json={"detectives": [detective_card.id]})

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_detective_set_canceled_finalize_turn(mocker, test_client):
    fake_game = GameFactory(status=GameStatus.TURN_START)
    fake_player = PlayerFactory(token="abc", game_id=fake_game.id)
    detective_card = CardFactory(owner=fake_player.id, card_type=CardType.DETECTIVE, name="hercule-poirot", game_id=fake_game.id, set_id=None,)
    created_set = DetectiveSet(id=4, owner=fake_player.id, detectives=[detective_card], turn_played=fake_game.current_turn, game_id=fake_game.id,)

    mocker.patch('app.controllers.detective_set.PlayerService.read_by_token', return_value=fake_player)
    mocker.patch('app.controllers.detective_set.CardService.read', return_value=detective_card)
    mocker.patch('app.controllers.detective_set.DetectiveSetService.create', new_callable=AsyncMock, return_value=created_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.ChatService.create')
    mock_game_update = mocker.patch('app.controllers.detective_set.GameService.update', new_callable=AsyncMock)
    mock_bulk_update = mocker.patch('app.controllers.detective_set.CardService.bulk_update', new_callable=AsyncMock)
    mock_not_so_fast = mocker.patch('app.controllers.detective_set.not_so_fast_status', new_callable=AsyncMock)
    mock_not_so_fast.return_value = True

    response = test_client.post("/api/detective_set?token=abc", json={"detectives": [detective_card.id]})

    assert response.status_code == 200
    mock_game_update.assert_awaited_once()
    mock_bulk_update.assert_not_called()


@pytest.mark.asyncio
async def test_create_detective_set_canceled_returns_cards_when_lady_eileen(mocker, test_client):
    fake_game = GameFactory(status=GameStatus.TURN_START)
    fake_player = PlayerFactory(token="abc", game_id=fake_game.id)
    lady_card = CardFactory(owner=fake_player.id, card_type=CardType.DETECTIVE, name="lady-eileen-bundle-brent", game_id=fake_game.id, set_id=None,)
    other_card = CardFactory(owner=fake_player.id, card_type=CardType.DETECTIVE, name="harley-quin-wildcard", game_id=fake_game.id, set_id=None,)
    detective_ids = [lady_card.id, other_card.id]
    created_set = DetectiveSet(id=5, owner=fake_player.id, detectives=[lady_card, other_card], turn_played=fake_game.current_turn, game_id=fake_game.id,)

    mocker.patch('app.controllers.detective_set.PlayerService.read_by_token', return_value=fake_player)
    mocker.patch('app.controllers.detective_set.CardService.read', side_effect=[lady_card, other_card])
    mocker.patch('app.controllers.detective_set.DetectiveSetService.create', new_callable=AsyncMock, return_value=created_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.DetectiveSetService.delete', return_value=1)
    mocker.patch('app.controllers.detective_set.ChatService.create')
    mock_game_update = mocker.patch('app.controllers.detective_set.GameService.update', new_callable=AsyncMock)
    mock_bulk_update = mocker.patch('app.controllers.detective_set.CardService.bulk_update', new_callable=AsyncMock)
    mock_not_so_fast = mocker.patch('app.controllers.detective_set.not_so_fast_status', new_callable=AsyncMock)
    mock_not_so_fast.return_value = True

    response = test_client.post("/api/detective_set?token=abc", json={"detectives": detective_ids})

    assert response.status_code == 200
    mock_game_update.assert_awaited_once()
    mock_bulk_update.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_detective_set_not_found(mocker, test_client):
    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=None)

    response = test_client.post("/api/detective_set/update/99", json={"token": "abc", "add_card": 1})

    assert response.status_code == 404
    assert response.json()["detail"] == "No se puede actualizar el set: Set no encontrado"


@pytest.mark.asyncio
async def test_update_detective_set_invalid_status(mocker, test_client, fake_set):
    fake_game = GameFactory(status=GameStatus.WAITING)
    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=fake_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)

    response = test_client.post(f"/api/detective_set/update/{fake_set.id}", json={"token": "abc", "add_card": 1})

    assert response.status_code == 412
    assert response.json()["detail"] == "No se puede actualizar el set: No es el comienzo de turno"


@pytest.mark.asyncio
async def test_update_detective_set_token_mismatch(mocker, test_client, fake_set):
    fake_game = GameFactory(status=GameStatus.TURN_START)
    owner_player = PlayerFactory(id=fake_set.owner, token="valid_token")
    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=fake_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=owner_player)

    response = test_client.post(f"/api/detective_set/update/{fake_set.id}", json={"token": "invalid", "add_card": 1})

    assert response.status_code == 401
    assert response.json()["detail"] == "No se puede actualizar el set: Token invalido"


@pytest.mark.asyncio
async def test_update_detective_set_missing_card(mocker, test_client, fake_set):
    fake_game = GameFactory(status=GameStatus.TURN_START)
    owner_player = PlayerFactory(id=fake_set.owner, token="valid_token")
    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=fake_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=owner_player)
    mocker.patch('app.controllers.detective_set.CardService.read', return_value=None)

    response = test_client.post(f"/api/detective_set/update/{fake_set.id}", json={"token": owner_player.token, "add_card": 10})

    assert response.status_code == 404
    assert response.json()["detail"] == "No se puede actualizar el set: Detective no encontrado"


@pytest.mark.asyncio
async def test_update_detective_set_card_already_in_set(mocker, test_client, fake_set):
    fake_game = GameFactory(status=GameStatus.TURN_START)
    owner_player = PlayerFactory(id=fake_set.owner, token="valid_token")
    used_card = CardFactory(owner=owner_player.id, set_id=123, card_type=CardType.DETECTIVE)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=fake_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=owner_player)
    mocker.patch('app.controllers.detective_set.CardService.read', return_value=used_card)

    response = test_client.post(
        f"/api/detective_set/update/{fake_set.id}",
        json={"token": owner_player.token, "add_card": used_card.id},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "No se puede actualizar el set: Detective en set"


@pytest.mark.asyncio
async def test_update_detective_set_card_wrong_owner(mocker, test_client, fake_set):
    fake_game = GameFactory(status=GameStatus.TURN_START)
    owner_player = PlayerFactory(id=fake_set.owner, token="valid_token")
    other_player = PlayerFactory()
    foreign_card = CardFactory(owner=other_player.id, set_id=None, card_type=CardType.DETECTIVE)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=fake_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=owner_player)
    mocker.patch('app.controllers.detective_set.CardService.read', return_value=foreign_card)

    response = test_client.post(
        f"/api/detective_set/update/{fake_set.id}",
        json={"token": owner_player.token, "add_card": foreign_card.id},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "No se puede actualizar el set: No es dueño de la carta"


@pytest.mark.asyncio
async def test_update_detective_set_invalid_detective_for_set(mocker, test_client, fake_set):
    fake_set.detectives[0].name = "existing_detective"
    fake_game = GameFactory(status=GameStatus.TURN_START)
    owner_player = PlayerFactory(id=fake_set.owner, token="valid_token")
    wrong_card = CardFactory(owner=owner_player.id, name="other_detective", card_type=CardType.DETECTIVE)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=fake_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=owner_player)
    mocker.patch('app.controllers.detective_set.CardService.read', return_value=wrong_card)

    response = test_client.post(
        f"/api/detective_set/update/{fake_set.id}",
        json={"token": owner_player.token, "add_card": wrong_card.id},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "No se puede actualizar el set: El detective corresponde al set"


@pytest.mark.asyncio
async def test_update_detective_set_tuppence_pair(mocker, test_client, fake_set):
    fake_set.detectives[0].name = "tuppence-beresford"
    fake_set.detectives[0].card_type = CardType.DETECTIVE
    fake_game = GameFactory(id=fake_set.game_id, status=GameStatus.TURN_START)
    owner_player = PlayerFactory(id=fake_set.owner, token="valid_token", game_id=fake_game.id)
    new_card = CardFactory(owner=owner_player.id, name="tommy-beresford", card_type=CardType.DETECTIVE, game_id=fake_game.id)
    updated_set = DetectiveSet(id=fake_set.id, owner=fake_set.owner, detectives=[*fake_set.detectives, new_card], turn_played=fake_set.turn_played, game_id=fake_set.game_id,)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=fake_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=owner_player)
    mocker.patch('app.controllers.detective_set.CardService.read', return_value=new_card)
    mocker.patch('app.controllers.detective_set.ChatService.create')
    mocker.patch('app.controllers.detective_set.set_next_game_status', return_value=GameStatus.WAITING_FOR_CHOOSE_PLAYER)
    mock_update = mocker.patch('app.controllers.detective_set.DetectiveSetService.update', new_callable=AsyncMock, return_value=updated_set)
    mock_game_update = mocker.patch('app.controllers.detective_set.GameService.update', new_callable=AsyncMock)

    response = test_client.post(f"/api/detective_set/update/{fake_set.id}", json={"token": owner_player.token, "add_card": new_card.id},)

    assert response.status_code == 200
    assert response.json()["id"] == updated_set.id
    mock_update.assert_awaited_once()
    mock_game_update.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_detective_set_ok(mocker, test_client, fake_set):
    fake_set.detectives[0].name = "matching_detective"
    fake_game = GameFactory(id=fake_set.game_id, status=GameStatus.TURN_START)
    owner_player = PlayerFactory(id=fake_set.owner, token="valid_token")
    new_card = CardFactory(owner=owner_player.id, name="matching_detective", card_type=CardType.DETECTIVE)
    updated_set = DetectiveSet(
        id=fake_set.id,
        owner=fake_set.owner,
        detectives=[*fake_set.detectives, new_card],
        turn_played=fake_set.turn_played,
        game_id=fake_set.game_id,
    )

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=fake_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=owner_player)
    mock_card_read = mocker.patch('app.controllers.detective_set.CardService.read', return_value=new_card)
    mocker.patch('app.controllers.detective_set.set_next_game_status', return_value=GameStatus.WAITING_FOR_CHOOSE_PLAYER)
    mocker.patch('app.controllers.detective_set.not_so_fast_status', new_callable=AsyncMock, return_value=False)
    mocker.patch('app.controllers.detective_set.ChatService.create')
    mock_update = mocker.patch('app.controllers.detective_set.DetectiveSetService.update', new_callable=AsyncMock, return_value=updated_set)
    mock_game_update = mocker.patch('app.controllers.detective_set.GameService.update', new_callable=AsyncMock)

    response = test_client.post(
        f"/api/detective_set/update/{fake_set.id}",
        json={"token": owner_player.token, "add_card": new_card.id},
    )

    assert response.status_code == 200
    assert response.json()["id"] == updated_set.id
    mock_card_read.assert_called_once_with(session=ANY, oid=new_card.id)
    mock_update.assert_awaited_once()
    mock_game_update.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_detective_set_canceled_returns_cards_when_lady_eileen(mocker, test_client, fake_set):
    lady_card = CardFactory(owner=fake_set.owner, name="lady-eileen-bundle-brent", card_type=CardType.DETECTIVE, game_id=fake_set.game_id)
    fake_set.detectives = [lady_card]
    fake_game = GameFactory(id=fake_set.game_id, status=GameStatus.TURN_START)
    owner_player = PlayerFactory(id=fake_set.owner, token="valid_token", game_id=fake_game.id)
    new_card = CardFactory(owner=owner_player.id, name="lady-eileen-bundle-brent", card_type=CardType.DETECTIVE, game_id=fake_game.id)
    updated_set = DetectiveSet(id=fake_set.id, owner=fake_set.owner, detectives=[*fake_set.detectives, new_card], turn_played=fake_set.turn_played, game_id=fake_set.game_id,)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=fake_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=owner_player)
    mocker.patch('app.controllers.detective_set.CardService.read', return_value=new_card)
    mocker.patch('app.controllers.detective_set.set_next_game_status', return_value=GameStatus.WAITING_FOR_CHOOSE_PLAYER)
    mocker.patch('app.controllers.detective_set.DetectiveSetService.delete', return_value=1)
    mocker.patch('app.controllers.detective_set.ChatService.create')
    mock_update = mocker.patch('app.controllers.detective_set.DetectiveSetService.update', new_callable=AsyncMock, return_value=updated_set)
    mock_game_update = mocker.patch('app.controllers.detective_set.GameService.update', new_callable=AsyncMock)
    mock_bulk_update = mocker.patch('app.controllers.detective_set.CardService.bulk_update', new_callable=AsyncMock)
    mock_not_so_fast = mocker.patch('app.controllers.detective_set.not_so_fast_status', new_callable=AsyncMock, return_value=True)

    response = test_client.post(f"/api/detective_set/update/{fake_set.id}", json={"token": owner_player.token, "add_card": new_card.id},)

    assert response.status_code == 200
    mock_update.assert_awaited_once()
    mock_not_so_fast.assert_awaited_once()
    mock_bulk_update.assert_awaited_once()
    mock_game_update.assert_awaited_once()

@pytest.mark.asyncio
async def test_search_detective_sets_invalid_token(mocker, test_client):
    mocker.patch('app.controllers.detective_set.PlayerService.read_by_token', return_value=None)

    response = test_client.post("/api/detective_set/search?token=bad", json={})
    assert response.status_code == 401
    assert response.json()["detail"] == "Token inválido"


@pytest.mark.asyncio
async def test_search_detective_sets_ok(mocker, test_client, fake_set):
    fake_player = PlayerFactory(token="abc")
    mocker.patch('app.controllers.detective_set.PlayerService.read_by_token', return_value=fake_player)
    mock_search = mocker.patch('app.controllers.detective_set.DetectiveSetService.search', return_value=[fake_set])

    response = test_client.post("/api/detective_set/search?token=abc", json={})
    assert response.status_code == 200
    data = response.json()
    assert data[0]["id"] == fake_set.id
    mock_search.assert_called_once()


@pytest.mark.asyncio
async def test_get_detective_set_invalid_token(mocker, test_client):
    mocker.patch('app.controllers.detective_set.PlayerService.read_by_token', return_value=None)

    response = test_client.get("/api/detective_set/1?token=invalid")
    assert response.status_code == 401
    assert response.json()["detail"] == "Token inválido"


@pytest.mark.asyncio
async def test_get_detective_set_not_found(mocker, test_client):
    fake_player = PlayerFactory(token="abc")
    mocker.patch('app.controllers.detective_set.PlayerService.read_by_token', return_value=fake_player)
    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=None)

    response = test_client.get("/api/detective_set/99?token=abc")
    assert response.status_code == 404
    assert response.json()["detail"] == "Set no encontrado"


@pytest.mark.asyncio
async def test_get_detective_set_ok(mocker, test_client, fake_set):
    fake_player = PlayerFactory(token="abc")
    mocker.patch('app.controllers.detective_set.PlayerService.read_by_token', return_value=fake_player)
    mock_read = mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=fake_set)

    response = test_client.get("/api/detective_set/1?token=abc")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fake_set.id
    mock_read.assert_called_once()


@pytest.mark.asyncio
async def test_post_detective_set_action_not_found(mocker, test_client):
    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=None)

    response = test_client.post("/api/detective_set/1", json={"token": "abc"})

    assert response.status_code == 404
    assert response.json()["detail"] == "No se puede realizar la accion: Set no encontrado"


@pytest.mark.asyncio
async def test_post_detective_set_action_invalid_turn(mocker, test_client):
    player_in_action = PlayerFactory(token="abc")
    played_set = DetectiveSet(id=1, owner=player_in_action.id, game_id=1, turn_played=1, detectives=[])
    fake_game = GameFactory(id=played_set.game_id, status=GameStatus.WAITING_FOR_CHOOSE_PLAYER, current_turn=2, player_in_action=player_in_action.id)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=played_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=player_in_action)

    response = test_client.post(f"/api/detective_set/{played_set.id}", json={"token": "abc"})

    assert response.status_code == 412
    assert response.json()["detail"] == "No se puede realizar la accion: Turno invalido"


@pytest.mark.asyncio
async def test_post_detective_set_action_missing_target_player(mocker, test_client):
    player_in_action = PlayerFactory(token="abc")
    played_set = DetectiveSet(id=2, owner=player_in_action.id, game_id=5, turn_played=3, detectives=[])
    fake_game = GameFactory(id=played_set.game_id, status=GameStatus.WAITING_FOR_CHOOSE_PLAYER, current_turn=played_set.turn_played, player_in_action=player_in_action.id)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=played_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=player_in_action)

    response = test_client.post(f"/api/detective_set/{played_set.id}", json={"token": player_in_action.token})

    assert response.status_code == 400
    assert response.json()["detail"] == "No se puede realizar la accion: Es necesario elegir un jugador"


@pytest.mark.asyncio
async def test_post_detective_set_action_self_target(mocker, test_client):
    player_in_action = PlayerFactory(token="abc")
    played_set = DetectiveSet(id=3, owner=player_in_action.id, game_id=7, turn_played=4, detectives=[])
    fake_game = GameFactory(id=played_set.game_id, status=GameStatus.WAITING_FOR_CHOOSE_PLAYER, current_turn=played_set.turn_played, player_in_action=player_in_action.id)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=played_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=player_in_action)

    response = test_client.post(f"/api/detective_set/{played_set.id}", json= {"token": player_in_action.token, "target_player": played_set.owner})

    assert response.status_code == 406
    assert response.json()["detail"] == "No se puede realizar la accion: No se puede seleccionar a uno mismo"


@pytest.mark.asyncio
async def test_post_detective_set_action_not_target_player(mocker, test_client):
    player_in_action = PlayerFactory(token="abc")
    played_set = DetectiveSet(id=4, owner=player_in_action.id, game_id=9, turn_played=2, detectives=[])
    fake_game = GameFactory(id=played_set.game_id, status=GameStatus.WAITING_FOR_CHOOSE_PLAYER, current_turn=played_set.turn_played, player_in_action=player_in_action.id)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=played_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', side_effect=[player_in_action, None])

    response = test_client.post(f"/api/detective_set/{played_set.id}", json={"token": player_in_action.token, "target_player": 999})

    assert response.status_code == 400
    assert response.json()["detail"] == "No se puede realizar la accion: Es necesario seleccionar un jugador"


@pytest.mark.asyncio
async def test_post_detective_set_action_target_player_other_game(mocker, test_client):
    player_in_action = PlayerFactory(token="abc", game_id=10)
    target_player = PlayerFactory(game_id=player_in_action.game_id + 1, id=player_in_action.id+1)
    played_set = DetectiveSet(id=5, owner=player_in_action.id, game_id=player_in_action.game_id, turn_played=1, detectives=[])
    fake_game = GameFactory(id=played_set.game_id, status=GameStatus.WAITING_FOR_CHOOSE_PLAYER, current_turn=played_set.turn_played, player_in_action=player_in_action.id)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=played_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', side_effect=[player_in_action, target_player])

    response = test_client.post(f"/api/detective_set/{played_set.id}", json={"token": player_in_action.token, "target_player": target_player.id})

    assert response.status_code == 400
    assert response.json()["detail"] == "No se puede realizar la accion: El jugador seleccionado no se encuentra en la partida"


@pytest.mark.asyncio
async def test_post_detective_set_action_token_mismatch_choose_player(mocker, test_client):
    player_in_action = PlayerFactory(token="valid_token", game_id=12)
    target_player = PlayerFactory(game_id=player_in_action.game_id)
    played_set = DetectiveSet(id=6, owner=player_in_action.id, game_id=player_in_action.game_id, turn_played=2, detectives=[])
    fake_game = GameFactory(id=played_set.game_id, status=GameStatus.WAITING_FOR_CHOOSE_PLAYER, current_turn=played_set.turn_played, player_in_action=player_in_action.id)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=played_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', side_effect=[player_in_action, target_player])

    response = test_client.post(f"/api/detective_set/{played_set.id}", json={"token": "wrong_token", "target_player": target_player.id})

    assert response.status_code == 412
    assert response.json()["detail"] == "No se puede realizar la accion: Token invalido"


@pytest.mark.asyncio
async def test_post_detective_set_action_choose_player_ok(mocker, test_client):
    player_in_action = PlayerFactory(token="valid_token", game_id=14)
    target_player = PlayerFactory(game_id=player_in_action.game_id)
    played_set = DetectiveSet(id=7, owner=player_in_action.id, game_id=player_in_action.game_id, turn_played=5, detectives=[])
    fake_game = GameFactory(id=played_set.game_id, status=GameStatus.WAITING_FOR_CHOOSE_PLAYER, current_turn=played_set.turn_played, player_in_action=player_in_action.id)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=played_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', side_effect=[player_in_action, target_player])
    mock_update = mocker.patch('app.controllers.detective_set.GameService.update', new_callable=AsyncMock)
    mocker.patch('app.controllers.detective_set.ChatService.create')

    payload = {"token": player_in_action.token, "target_player": target_player.id}
    response = test_client.post(f"/api/detective_set/{played_set.id}", json=payload)

    assert response.status_code == 200
    mock_update.assert_awaited_once()

@pytest.mark.asyncio
async def test_post_detective_set_action_missing_secret(mocker, test_client):
    player_in_action = PlayerFactory(token="abc")
    played_set = DetectiveSet(id=8, owner=player_in_action.id, game_id=20, turn_played=1, detectives=[])
    fake_game = GameFactory(id=played_set.game_id, status=GameStatus.WAITING_FOR_CHOOSE_SECRET, current_turn=played_set.turn_played, player_in_action=player_in_action.id)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=played_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=player_in_action)

    response = test_client.post(f"/api/detective_set/{played_set.id}", json={"token": player_in_action.token})

    assert response.status_code == 400
    assert response.json()["detail"] == "No se puede realizar la accion: Es necesario elegir un secreto"


@pytest.mark.asyncio
async def test_post_detective_set_action_token_mismatch_secret(mocker, test_client):
    player_in_action = PlayerFactory(token="correct", game_id=22)
    played_set = DetectiveSet(id=9, owner=player_in_action.id, game_id=player_in_action.game_id, turn_played=2, detectives=[])
    fake_game = GameFactory(id=played_set.game_id, status=GameStatus.WAITING_FOR_CHOOSE_SECRET, current_turn=played_set.turn_played, player_in_action=player_in_action.id)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=played_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=player_in_action)

    response = test_client.post(f"/api/detective_set/{played_set.id}", json={"token": "invalid", "target_secret": 123})

    assert response.status_code == 412
    assert response.json()["detail"] == "No se puede realizar la accion: Token invalido"


@pytest.mark.asyncio
async def test_post_detective_set_action_secret_not_found(mocker, test_client):
    player_in_action = PlayerFactory(token="token", game_id=30)
    played_set = DetectiveSet(id=10, owner=player_in_action.id, game_id=player_in_action.game_id, turn_played=1, detectives=[])
    fake_game = GameFactory(id=played_set.game_id, status=GameStatus.WAITING_FOR_CHOOSE_SECRET, current_turn=played_set.turn_played, player_in_action=player_in_action.id)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=played_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=player_in_action)
    mocker.patch('app.controllers.detective_set.SecretService.read', return_value=None)

    response = test_client.post(f"/api/detective_set/{played_set.id}", json={"token": player_in_action.token, "target_secret": 321})

    assert response.status_code == 404
    assert response.json()["detail"] == "No se puede realizar la accion: Secreto no encontrado"


@pytest.mark.asyncio
async def test_post_detective_set_action_secret_other_game(mocker, test_client):
    player_in_action = PlayerFactory(token="valid", game_id=40)
    played_set = DetectiveSet(id=11, owner=player_in_action.id, game_id=player_in_action.game_id, turn_played=3, detectives=[])
    fake_game = GameFactory(id=played_set.game_id, status=GameStatus.WAITING_FOR_CHOOSE_SECRET, current_turn=played_set.turn_played, player_in_action=player_in_action.id)
    secret = Secret(id=1, game_id=played_set.game_id + 1, owner=player_in_action.id, name="secret", content="content", revealed=False, type=SecretType.OTHER)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=played_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=player_in_action)
    mocker.patch('app.controllers.detective_set.SecretService.read', return_value=secret)

    response = test_client.post(f"/api/detective_set/{played_set.id}", json={"token": player_in_action.token, "target_secret": secret.id})

    assert response.status_code == 404
    assert response.json()["detail"] == "No se puede realizar la accion: El secreto seleccionado no se encuentra en la partida"


@pytest.mark.asyncio
async def test_post_detective_set_action_secret_requires_own_secret(mocker, test_client):
    player_in_action = PlayerFactory(token="valid", game_id=45)
    detective_card = CardFactory(owner=player_in_action.id, card_type=CardType.DETECTIVE, name="mr-satterthwaite", game_id=player_in_action.game_id)
    played_set = DetectiveSet(id=12,owner=player_in_action.id, game_id=player_in_action.game_id, turn_played=5, detectives=[detective_card])
    fake_game = GameFactory(id=played_set.game_id, status=GameStatus.WAITING_FOR_CHOOSE_SECRET, current_turn=played_set.turn_played, player_in_action=player_in_action.id,)
    secret = Secret(id=99, game_id=played_set.game_id, owner=player_in_action.id + 1, name="secret", content="content", revealed=False, type=SecretType.OTHER,)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=played_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=player_in_action)
    mocker.patch('app.controllers.detective_set.SecretService.read', return_value=secret)

    payload = {"token": player_in_action.token, "target_secret": secret.id}
    response = test_client.post(f"/api/detective_set/{played_set.id}", json=payload)

    assert response.status_code == 412
    assert response.json()["detail"] == "No se puede realizar la accion: Se debe seleccionar un secreto propio"


@pytest.mark.asyncio
async def test_post_detective_set_action_secret_update_parker(mocker, test_client):
    player_in_action = PlayerFactory(token="valid", game_id=50)
    parker_card = CardFactory(name="parker-pyne", owner=player_in_action.id, card_type=CardType.DETECTIVE, game_id=player_in_action.game_id)
    played_set = DetectiveSet(id=12, owner=player_in_action.id, game_id=player_in_action.game_id, turn_played=6, detectives=[parker_card])
    fake_game = GameFactory(id=played_set.game_id, status=GameStatus.WAITING_FOR_CHOOSE_SECRET, current_turn=played_set.turn_played, player_in_action=player_in_action.id)
    secret = Secret(id=7, game_id=played_set.game_id, owner=player_in_action.id, name="secret", content="content", revealed=True, type=SecretType.OTHER)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=played_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=player_in_action)
    mocker.patch('app.controllers.detective_set.SecretService.read', return_value=secret)
    mock_secret_update = mocker.patch('app.controllers.detective_set.SecretService.update', new_callable=AsyncMock)
    mock_game_update = mocker.patch('app.controllers.detective_set.GameService.update', new_callable=AsyncMock)
    mocker.patch('app.controllers.detective_set.ChatService.create')

    payload = {"token": player_in_action.token, "target_secret": secret.id}
    response = test_client.post(f"/api/detective_set/{played_set.id}", json=payload)

    assert response.status_code == 200
    mock_secret_update.assert_awaited_once()
    mock_game_update.assert_awaited_once()


@pytest.mark.asyncio
async def test_post_detective_set_action_secret_update_wildcard_transfer(mocker, test_client):
    player_in_action = PlayerFactory(token="valid", game_id=60)
    card_a = Card(owner=player_in_action.id, card_type=CardType.DETECTIVE, name="mr-satterthwaite", id=1, game_id=player_in_action.game_id, content="a")
    card_b = Card(owner=player_in_action.id, card_type=CardType.DETECTIVE, name="harley-quin-wildcard", id=2, game_id=player_in_action.game_id, content="b")
    played_set = DetectiveSet(id=13, owner=player_in_action.id, game_id=player_in_action.game_id, turn_played=7, detectives=[card_a, card_b])
    fake_game = GameFactory(id=played_set.game_id, status=GameStatus.WAITING_FOR_CHOOSE_SECRET, current_turn=played_set.turn_played, player_in_action=player_in_action.id)
    secret = Secret(id=9, game_id=played_set.game_id, owner=player_in_action.id, name="secret", content="content", revealed=False, type=SecretType.OTHER)
    another_secret = Secret(id=10, game_id=played_set.game_id, owner=player_in_action.id, name="hidden", content="hidden", revealed=False, type=SecretType.OTHER,)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=played_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=player_in_action)
    mocker.patch('app.controllers.detective_set.SecretService.read', return_value=secret)
    mock_secret_update = mocker.patch('app.controllers.detective_set.SecretService.update', new_callable=AsyncMock)
    mock_game_update = mocker.patch('app.controllers.detective_set.GameService.update', new_callable=AsyncMock)
    mocker.patch('app.controllers.detective_set.ChatService.create')
    mock_secret_search = mocker.patch(
        'app.controllers.detective_set.SecretService.search',
        side_effect=[[secret], [another_secret]],
    )

    payload = {"token": player_in_action.token, "target_secret": secret.id}
    response = test_client.post(f"/api/detective_set/{played_set.id}", json=payload)

    assert response.status_code == 200
    mock_game_update.assert_awaited_once()
    assert mock_game_update.await_args.kwargs["data"] == {"status": GameStatus.FINALIZE_TURN, "player_in_action": None}
    assert mock_secret_update.await_count == 2
    first_update_kwargs = mock_secret_update.await_args_list[0].kwargs
    assert first_update_kwargs["oid"] == secret.id
    assert first_update_kwargs["data"] == {"revealed": True}
    second_update_kwargs = mock_secret_update.await_args_list[1].kwargs
    assert second_update_kwargs["oid"] == secret.id
    assert second_update_kwargs["data"] == {"owner": played_set.owner, "revealed": False}
    assert mock_secret_search.call_count == 2
    first_call_kwargs = mock_secret_search.call_args_list[0].kwargs
    assert first_call_kwargs == {
        "session": ANY,
        "filterby": {"owner__eq": secret.owner, "revealed__eq": False},
    }
    second_call_kwargs = mock_secret_search.call_args_list[1].kwargs
    assert second_call_kwargs == {
        "session": ANY,
        "filterby": {"game_id__eq": secret.game_id, "revealed__eq": False},
    }


@pytest.mark.asyncio
async def test_post_detective_set_action_secret_murderer_revealed(mocker, test_client):
    player_in_action = PlayerFactory(token="valid", game_id=75)
    detective_card = CardFactory(owner=player_in_action.id, card_type=CardType.DETECTIVE, name="generic-detective", game_id=player_in_action.game_id)
    played_set = DetectiveSet(id=16, owner=player_in_action.id, game_id=player_in_action.game_id, turn_played=4, detectives=[detective_card])
    fake_game = GameFactory(id=played_set.game_id, status=GameStatus.WAITING_FOR_CHOOSE_SECRET, current_turn=played_set.turn_played, player_in_action=player_in_action.id)
    secret = Secret(id=21, game_id=played_set.game_id, owner=player_in_action.id, name="youre-the-murderer", content="content", revealed=False, type=SecretType.MURDERER)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=played_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=player_in_action)
    mocker.patch('app.controllers.detective_set.SecretService.read', return_value=secret)
    mock_secret_update = mocker.patch('app.controllers.detective_set.SecretService.update', new_callable=AsyncMock)
    mock_game_update = mocker.patch('app.controllers.detective_set.GameService.update', new_callable=AsyncMock)
    mocker.patch('app.controllers.detective_set.ChatService.create')

    payload = {"token": player_in_action.token, "target_secret": secret.id}
    response = test_client.post(f"/api/detective_set/{played_set.id}", json=payload)

    assert response.status_code == 200
    mock_secret_update.assert_awaited_once()
    assert mock_secret_update.await_args.kwargs["data"] == {"revealed": True}
    mock_game_update.assert_awaited_once()
    assert mock_game_update.await_args.kwargs["data"] == {"status": GameStatus.FINALIZED, "player_in_action": None}


@pytest.mark.asyncio
async def test_post_detective_set_action_secret_parker_pyne(mocker, test_client):
    player_in_action = PlayerFactory(token="valid", game_id=70,social_disgrace=True)
    parker_card = CardFactory(owner=player_in_action.id, card_type=CardType.DETECTIVE, name="parker-pyne", game_id=player_in_action.game_id)
    played_set = DetectiveSet(id=14, owner=player_in_action.id, game_id=player_in_action.game_id, turn_played=8, detectives=[parker_card])
    fake_game = GameFactory(id=played_set.game_id, status=GameStatus.WAITING_FOR_CHOOSE_SECRET, current_turn=played_set.turn_played, player_in_action=player_in_action.id)
    secret = Secret(id=10, game_id=played_set.game_id, owner=player_in_action.id, name="secret", content="content", revealed=False, type=SecretType.OTHER)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=played_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=player_in_action)
    mocker.patch('app.controllers.detective_set.SecretService.read', return_value=secret)
    mocker.patch('app.controllers.detective_set.PlayerService.update', return_value=player_in_action)
    mock_secret_update = mocker.patch('app.controllers.detective_set.SecretService.update', new_callable=AsyncMock)
    mock_game_update = mocker.patch('app.controllers.detective_set.GameService.update', new_callable=AsyncMock)
    mocker.patch('app.controllers.detective_set.ChatService.create')

    response = test_client.post(f"/api/detective_set/{played_set.id}", json={"token": player_in_action.token, "target_secret": secret.id})

    assert response.status_code == 200
    mock_secret_update.assert_awaited_once()
    mock_game_update.assert_awaited_once()



@pytest.mark.asyncio
async def test_post_detective_set_action_secret_social_disgrace(mocker, test_client):
    player_in_action = PlayerFactory(token="valid", game_id=80)
    detective_card = CardFactory(owner=player_in_action.id, card_type=CardType.DETECTIVE, name="another-detective", game_id=player_in_action.game_id)
    played_set = DetectiveSet(id=15, owner=player_in_action.id, game_id=player_in_action.game_id, turn_played=9, detectives=[detective_card])
    fake_game = GameFactory(id=played_set.game_id, status=GameStatus.WAITING_FOR_CHOOSE_SECRET, current_turn=played_set.turn_played, player_in_action=player_in_action.id)
    secret = Secret(id=11, game_id=played_set.game_id, owner=player_in_action.id, name="secret", content="content", revealed=True, type=SecretType.OTHER)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=played_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=player_in_action)
    mocker.patch('app.controllers.detective_set.SecretService.read', return_value=secret)
    mocker.patch('app.controllers.detective_set.PlayerService.update', return_value=player_in_action)
    mock_secret_update = mocker.patch('app.controllers.detective_set.SecretService.update', new_callable=AsyncMock)
    mock_game_update = mocker.patch('app.controllers.detective_set.GameService.update', new_callable=AsyncMock)
    mock_secret_search = mocker.patch('app.controllers.detective_set.SecretService.search', return_value=[])
    mocker.patch('app.controllers.detective_set.ChatService.create')

    response = test_client.post(f"/api/detective_set/{played_set.id}", json={"token": player_in_action.token, "target_secret": secret.id})

    assert response.status_code == 200
    mock_secret_update.assert_awaited_once()
    mock_game_update.assert_awaited_once()


@pytest.mark.asyncio
async def test_post_detective_set_action_secret_revealed_without_parker(mocker, test_client):
    player_in_action = PlayerFactory(token="valid", game_id=80)
    detective_card = CardFactory(owner=player_in_action.id, card_type=CardType.DETECTIVE, name="another-detective", game_id=player_in_action.game_id)
    played_set = DetectiveSet(id=15, owner=player_in_action.id, game_id=player_in_action.game_id, turn_played=9, detectives=[detective_card])
    fake_game = GameFactory(id=played_set.game_id, status=GameStatus.WAITING_FOR_CHOOSE_SECRET, current_turn=played_set.turn_played, player_in_action=player_in_action.id)
    secret = Secret(id=11, game_id=played_set.game_id, owner=player_in_action.id, name="secret", content="content", revealed=True, type=SecretType.OTHER)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=played_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=player_in_action)
    mocker.patch('app.controllers.detective_set.SecretService.read', return_value=secret)
    mock_secret_update = mocker.patch('app.controllers.detective_set.SecretService.update', new_callable=AsyncMock)
    mock_game_update = mocker.patch('app.controllers.detective_set.GameService.update', new_callable=AsyncMock)
    mock_secret_search = mocker.patch('app.controllers.detective_set.SecretService.search', return_value=[secret])
    mocker.patch('app.controllers.detective_set.ChatService.create')

    response = test_client.post(f"/api/detective_set/{played_set.id}", json={"token": player_in_action.token, "target_secret": secret.id})

    assert response.status_code == 200
    mock_secret_update.assert_awaited_once()
    mock_game_update.assert_awaited_once()



@pytest.mark.asyncio

async def test_post_detective_set_action_bad_game_status(mocker, test_client):
    player_in_action = PlayerFactory(token="abc")
    played_set = DetectiveSet(id=2, owner=player_in_action.id, game_id=5, turn_played=3, detectives=[])
    fake_game = GameFactory(id=played_set.game_id, status=GameStatus.TURN_START, current_turn=played_set.turn_played, player_in_action=player_in_action.id)

    mocker.patch('app.controllers.detective_set.DetectiveSetService.read', return_value=played_set)
    mocker.patch('app.controllers.detective_set.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.detective_set.PlayerService.read', return_value=player_in_action)

    response = test_client.post(f"/api/detective_set/{played_set.id}", json={"token": player_in_action.token})

    assert response.status_code == 400
    assert response.json()["detail"] == "No se puede realizar la accion: Estado de partida invalido"
