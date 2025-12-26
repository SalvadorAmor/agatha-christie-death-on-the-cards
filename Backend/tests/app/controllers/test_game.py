import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.controllers.game import DeleteGameDTO
from app.models.game import PublicGame, GameStatus
from app.services.game import GameFilter
from app.models.card import Card
from tests.conftest import GameFactory, CreateGameDTOFactory, UpdateGameDTOFactory, GameWithPlayerFactory, \
    PlayerFactory, CardFactory, EventTableFactory


def test_game_not_found(mocker, test_client):
    # Given
    mock_service = mocker.patch('app.controllers.game.GameService.read', return_value=None)

    # When
    response = test_client.get('/api/game/999')

    # Then
    assert response.status_code == 404
    mock_service.assert_called_once()

def test_game_ok(mocker, test_client):
    # Given
    fake_game = GameFactory(password=None)
    mock_service = mocker.patch('app.controllers.game.GameService.read', return_value=fake_game)

    # When
    response = test_client.get('/api/game/999')

    # Then
    assert response.status_code == 200
    mock_service.assert_called_once()
    assert response.json() == fake_game.model_dump(mode="json", exclude={'password'})


@pytest.mark.parametrize('min_players_cases', [1,7])
def test_create_game_bad_min_players(min_players_cases, test_client):
    # Given
    fake_create_game_dto = CreateGameDTOFactory(min_players=min_players_cases)

    # When
    response = test_client.post('/api/game', json=fake_create_game_dto.model_dump(mode='json'))

    # Then
    assert response.status_code == 400


@pytest.mark.parametrize('max_players_cases', [1,7])
def test_create_game_bad_max_players(max_players_cases, test_client):
    # Given
    fake_create_game_dto = CreateGameDTOFactory(min_players=2, max_players=max_players_cases)

    # When
    response = test_client.post('/api/game', json=fake_create_game_dto.model_dump(mode='json'))

    # Then
    assert response.status_code == 400

def test_create_game_bad_min_max_players(test_client):
    # Given
    fake_create_game_dto = CreateGameDTOFactory(min_players=4, max_players=2)

    # When
    response = test_client.post('/api/game', json=fake_create_game_dto.model_dump(mode='json'))

    # Then
    assert response.status_code == 400

def test_create_game_bad_password(test_client):
    # Given
    fake_create_game_dto = CreateGameDTOFactory(min_players=2, max_players=4, password="123456789123456789")

    # When
    response = test_client.post('/api/game', json=fake_create_game_dto.model_dump(mode='json'))

    # Then
    assert response.status_code == 400

def test_create_game_bad_game_name(test_client):
    # Given
    fake_create_game_dto = CreateGameDTOFactory(min_players=2, max_players=4, game_name="123456789123456789")

    # When
    response = test_client.post('/api/game', json=fake_create_game_dto.model_dump(mode='json'))

    # Then
    assert response.status_code == 400

def test_create_game_ok(mocker, test_client):
    # Given
    fake_create_game_dto = CreateGameDTOFactory(min_players=2, max_players=4, game_name="123456789")
    fake_game = GameFactory(**fake_create_game_dto.model_dump(), name=fake_create_game_dto.game_name)
    fake_player =  PlayerFactory()
    mock_service = mocker.patch('app.controllers.game.GameService.create', return_value=fake_game)
    mock_service2 = mocker.patch('app.controllers.game.PlayerService.create', return_value=fake_player)
    fake_player.game_id = fake_game.id
    mock_update_player = mocker.patch('app.controllers.game.PlayerService.update', return_value=fake_player)
    mock_refresh_game = mocker.patch('app.controllers.game.GameService.refresh')

    # When
    response = test_client.post('/api/game', json=fake_create_game_dto.model_dump(mode='json'))

    # Then
    assert response.status_code == 200
    mock_service.assert_called_once()
    mock_service2.assert_called_once()
    mock_update_player.assert_called_once()
    mock_refresh_game.assert_called()

def test_delete_game_not_found(mocker, test_client):
     # Given
     mock_service = mocker.patch('app.controllers.game.GameService.read', return_value=None)
     delete_game_dto = DeleteGameDTO(token="test")
     # When
     response = test_client.request("DELETE", '/api/game/999', json=delete_game_dto.model_dump(mode='json'))

     # Then
     assert response.status_code == 404
     mock_service.assert_called_once()

def test_delete_game_invalid_token(mocker, test_client):
    # Given
    fake_player=PlayerFactory(id=1,token="test")
    fake_game=GameFactory(password=None,owner=1,status = GameStatus.WAITING)
    delete_game_dto = DeleteGameDTO(token="almendra")
    mock_service = mocker.patch('app.controllers.game.GameService.delete', return_value=999)
    mock_service2= mocker.patch('app.controllers.game.GameService.read', return_value=fake_game)
    mock_service3= mocker.patch('app.controllers.game.PlayerService.read', return_value=fake_player)
    # When
    response = test_client.request("DELETE",'/api/game/999', json=delete_game_dto.model_dump(mode='json'))
    # Then
    assert response.status_code == 401
    mock_service3.assert_called_once()
    mock_service2.assert_called_once()


def test_delete_game_invalid_status(mocker, test_client):
    # Given
    fake_player=PlayerFactory(id=1,token="test")
    fake_game=GameFactory(password=None,owner=1,status = GameStatus.FINALIZE_TURN)
    delete_game_dto = DeleteGameDTO(token="test")
    mock_service = mocker.patch('app.controllers.game.GameService.delete', return_value=999)
    mock_service2= mocker.patch('app.controllers.game.GameService.read', return_value=fake_game)
    # When
    response = test_client.request("DELETE",'/api/game/999', json=delete_game_dto.model_dump(mode='json'))
    # Then
    assert response.status_code == 400
    mock_service2.assert_called_once()


def test_delete_game_ok(mocker, test_client):
    # Given
    fake_player=PlayerFactory(id=1,token="test")
    fake_game=GameFactory(password=None,owner=1,status=GameStatus.WAITING)
    delete_game_dto = DeleteGameDTO(token="test")
    mock_service = mocker.patch('app.controllers.game.GameService.delete', return_value=999)
    mock_service2= mocker.patch('app.controllers.game.GameService.read', return_value=fake_game)
    mock_service3= mocker.patch('app.controllers.game.PlayerService.read', return_value=fake_player)
    # When
    response = test_client.request("DELETE",'/api/game/999', json=delete_game_dto.model_dump(mode='json'))
    # Then
    assert response.status_code == 200
    mock_service.assert_called_once()
    mock_service2.assert_called_once()
    mock_service3.assert_called_once()

def test_update_game_not_found(mocker, test_client):
    # Given
    fake_update_dto = UpdateGameDTOFactory(status=GameStatus.WAITING,token="test")
    mock_service = mocker.patch('app.controllers.game.GameService.read', return_value=None)

    # When
    response = test_client.patch('/api/game/999', json=fake_update_dto.model_dump(mode='json'))

    # Then
    assert response.status_code == 404
    mock_service.assert_called_once()


def test_update_game_not_enough_players(mocker, test_client):
    # Given
    fake_players = [PlayerFactory(id=1)]
    fake_update_dto = UpdateGameDTOFactory(status=GameStatus.STARTED, token="test")
    fake_game = GameFactory(status=GameStatus.WAITING, owner=1, current_turn=1)
    mock_service_game_read = mocker.patch('app.controllers.game.GameService.read', return_value=fake_game)
    mock_service_player_search = mocker.patch('app.controllers.game.PlayerService.search', return_value=fake_players)
    # When
    response = test_client.patch('/api/game/999', json=fake_update_dto.model_dump(mode='json'))

    # Then
    assert response.status_code == 412
    mock_service_game_read.assert_called_once()

def test_update_game_turn_ok(mocker, test_client):
    # Given
    fake_update_dto = UpdateGameDTOFactory(current_turn = 1, token="random")
    fake_game = GameFactory(id = 1, current_turn = 0, status = GameStatus.FINALIZE_TURN)
    fake_player = PlayerFactory(position = 0, id = 1, game_id = 1, token="random")
    fake_player_card = CardFactory(id=3, owner= fake_player.id, game_id = 1)
    fake_card_to_pick = CardFactory(id=2, game_id=1)
    fake_card_updated = CardFactory(**fake_card_to_pick.model_dump(exclude='owner'), owner = fake_player.id)
    fake_updated_game = GameFactory(**fake_update_dto.model_dump())
    not_so_fast_card = CardFactory(id=5, owner=fake_player.id, game_id=fake_game.id)
    not_so_fast_event = EventTableFactory(target_card=not_so_fast_card.id)

    mock_service_game = mocker.patch('app.controllers.game.GameService.read', return_value=fake_game)
    mock_service_players = mocker.patch('app.controllers.game.PlayerService.search', side_effect=[[fake_player], [fake_player]])
    mock_service_cards = mocker.patch('app.controllers.game.CardService.search', side_effect=[[fake_player_card], [fake_card_to_pick], []])
    mock_service_update_card = mocker.patch('app.controllers.game.CardService.update', new_callable=AsyncMock, return_value=fake_card_updated)
    mock_get_discard_order = mocker.patch('app.controllers.game.get_new_discarded_order', return_value=10)
    mock_bulk_update = mocker.patch('app.controllers.game.CardService.bulk_update', new_callable=AsyncMock, return_value=[not_so_fast_card])
    mock_event_search = mocker.patch('app.controllers.game.EventTableService.search', return_value=[not_so_fast_event])
    mock_service = mocker.patch('app.controllers.game.GameService.update', new_callable=AsyncMock, return_value=fake_updated_game)

    # When
    response = test_client.patch('/api/game/999', json=fake_update_dto.model_dump(mode='json'))

    # Then
    assert response.status_code == 200
    mock_service.assert_called_once()
    mock_service_game.assert_called_once()
    assert len(mock_service_players.mock_calls) == 2
    assert len(mock_service_cards.mock_calls) == 3
    mock_service_update_card.assert_awaited_once()
    mock_event_search.assert_called_once()
    assert mock_bulk_update.await_count == 1
    bulk_kwargs = mock_bulk_update.await_args.kwargs
    assert bulk_kwargs["oids"] == [not_so_fast_card.id]
    assert bulk_kwargs["data"][0]["turn_discarded"] == fake_game.current_turn
    assert bulk_kwargs["data"][0]["discarded_order"] == mock_get_discard_order.return_value
    update_kwargs = mock_service.await_args.kwargs["data"]
    assert update_kwargs["status"] == GameStatus.FINALIZED
    assert response.json()['current_turn'] == 1

def test_update_game_status_invalid_token(mocker, test_client):
    fake_players = PlayerFactory.create_batch(5)
    fake_players.append(PlayerFactory(id=1,token="wrong"))
    fake_update_dto = UpdateGameDTOFactory(status=GameStatus.STARTED, token="test")
    fake_game = GameFactory(status=GameStatus.WAITING, owner=1, current_turn=1)
    mock_service_game_read = mocker.patch('app.controllers.game.GameService.read', return_value=fake_game)
    mock_service_player_search = mocker.patch('app.controllers.game.PlayerService.search', return_value=fake_players)
    # When
    response = test_client.patch('/api/game/999', json=fake_update_dto.model_dump(mode='json'))
    assert response.status_code == 401
    mock_service_game_read.assert_called_once()
    mock_service_player_search.assert_called_once()

def test_update_game_invalid(mocker, test_client):
    # Given
    fake_update_dto = UpdateGameDTOFactory(status=GameStatus.FINALIZED, token="random")
    fake_game = GameFactory(id = 1, current_turn = 0)
    fake_player = PlayerFactory(position = 0, id = 1, game_id = 1, token="random")

    mock_service_game = mocker.patch('app.controllers.game.GameService.read', return_value=fake_game)
    mock_service_players = mocker.patch('app.controllers.player.PlayerService.search', return_value=[fake_player])

    # When
    response = test_client.patch('/api/game/999', json=fake_update_dto.model_dump(mode='json'))

    # Then
    assert response.status_code == 400
    mock_service_game.assert_called_once()
    mock_service_players.assert_called_once()

def test_update_game_ok_whit_accomplice(mocker, test_client):
    fake_players = [PlayerFactory(id=1,token="test")]
    fake_players.append(PlayerFactory(id=2))
    fake_players.append(PlayerFactory(id=3))
    fake_players.append(PlayerFactory(id=4))
    fake_players.append(PlayerFactory(id=5))
    fake_update_dto = UpdateGameDTOFactory(status=GameStatus.STARTED, token="test")
    fake_game = GameFactory(status=GameStatus.WAITING, owner=1, current_turn=1)
    fake_card = CardFactory(id=1, turn_discarded=None, game_id=1)
    mock_service_game_read = mocker.patch('app.controllers.game.GameService.read', return_value=fake_game)
    mock_service_player_search = mocker.patch('app.controllers.game.PlayerService.search', return_value=fake_players)
    mock_service_card_create = mocker.patch('app.controllers.game.CardService.create', return_value=None)
    mock_service_secret_create = mocker.patch('app.controllers.game.SecretService.create', return_value=None)
    mock_service_secret_create = mocker.patch('app.controllers.game.SecretService.create_bulk', return_value=None)

    mock_service_card_search = mocker.patch('app.controllers.game.CardService.search', return_value=[fake_card])
    mock_service_card_update = mocker.patch('app.controllers.game.CardService.update', return_value=None)
    mock_service_card_create_bull = mocker.patch('app.controllers.game.CardService.create_bulk', return_value=None)

    mock_service_game_update = mocker.patch('app.controllers.game.GameService.update', return_value=fake_game)
    # When
    response = test_client.patch('/api/game/999', json=fake_update_dto.model_dump(mode='json'))
    assert response.status_code == 200
    mock_service_game_read.assert_called_once()
    mock_service_player_search.assert_called_once()
    assert len(mock_service_game_update.mock_calls) == 2

def test_update_game_not_discarded_cards(mocker, test_client):
        # Given
        fake_update_dto = UpdateGameDTOFactory(current_turn = 1, token="random")
        fake_game = GameFactory(id = 1, current_turn = 0,status=GameStatus.TURN_START)
        fake_player = PlayerFactory(position=0, id=1, game_id=1, token="random")

        mocker_service_players = mocker.patch('app.controllers.player.PlayerService.search', return_value=[fake_player])
        mocker_service = mocker.patch('app.controllers.game.GameService.read', return_value = fake_game)

        # When
        response = test_client.patch('/api/game/999', json=fake_update_dto.model_dump(mode='json'))

        # Then
        assert response.status_code == 428
        mocker_service.assert_called_once()
        mocker_service_players.assert_called_once()

def test_update_game_bad_token(mocker, test_client):
        # Given
        fake_update_dto = UpdateGameDTOFactory(current_turn = 1, token="mal_token")
        fake_discarded_card = CardFactory(id = 1, turn_discarded= 0, game_id = 1)
        fake_game = GameFactory(id = 1, current_turn = 0,status = GameStatus.FINALIZE_TURN)
        fake_player = PlayerFactory(position = 0, id = 1, game_id = 1, token="buen_token")


        mocker_service = mocker.patch('app.controllers.game.GameService.read', return_value = fake_game)
        mock_service_players = mocker.patch('app.controllers.player.PlayerService.search', return_value=[fake_player])

        # When
        response = test_client.patch('/api/game/999', json=fake_update_dto.model_dump(mode='json'))

        # Then
        assert response.status_code == 401
        mocker_service.assert_called_once()
        assert len(mock_service_players.mock_calls) == 2


def test_search_game_bad_token(mocker, test_client):
    # Given
    fake_game_filter = GameFilter(id__eq=1, password__is_null=True, status__eq=None)
    mock_service = mocker.patch('app.controllers.game.GameService.search', return_value=[])

    # When
    response = test_client.post('/api/game/search', json=fake_game_filter.model_dump(mode='json'))

    # Then
    assert response.status_code == 200
    mock_service.assert_called_once()
    assert response.json() == []

def test_search_game_multi(mocker, test_client):
    # Given
    fake_game_filter = GameFilter(id__eq=1, password__is_null=True, status__eq=None)
    fake_games = GameFactory.create_batch(size=10)
    mock_service = mocker.patch('app.controllers.game.GameService.search', return_value=fake_games)

    # When
    response = test_client.post('/api/game/search', json=fake_game_filter.model_dump(mode='json'))

    # Then
    assert response.status_code == 200
    mock_service.assert_called_once()
    assert len(response.json()) == 10
