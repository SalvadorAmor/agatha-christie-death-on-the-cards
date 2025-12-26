from datetime import datetime, UTC

import pytest
from sqlalchemy.testing import exclude

from app.controllers.player import DeletePlayerDTO
from app.models.game import GameStatus
from app.models.player import Player
from app.services.player import PlayerFilter
from tests.conftest import PlayerFactory, CreatePlayerDTOFactory, GameFactory


def test_player_not_found(mocker,test_client):
    mock_service = mocker.patch('app.controllers.player.PlayerService.read', return_value=None)
    response = test_client.get('/api/player/88')
    assert response.status_code == 404
    mock_service.assert_called_once()

def test_player_ok(mocker,test_client):
    fake_player = PlayerFactory()
    mock_service = mocker.patch('app.controllers.player.PlayerService.read', return_value=fake_player)
    response = test_client.get('/api/player/88')
    assert response.status_code == 200
    mock_service.assert_called_once()
    data = response.json()
    assert data == fake_player.model_dump(mode='json', exclude={'token'})

def test_create_player_ok(mocker, test_client):
    fake_create_player_dto = CreatePlayerDTOFactory()
    fake_player = PlayerFactory(**fake_create_player_dto.model_dump())
    mock_service = mocker.patch('app.controllers.player.PlayerService.create', return_value=fake_player)

    fake_game = GameFactory(id=1,current_turn=0,status=GameStatus.WAITING,max_players=6)
    fake_players = [fake_player,PlayerFactory(id=3,position=1)]

    mock_player_service_search = mocker.patch('app.controllers.card.PlayerService.search', return_value=fake_players)
    mock_game_service_read= mocker.patch('app.controllers.card.GameService.read', return_value=fake_game)

    response = test_client.post('/api/player/1', json=fake_create_player_dto.model_dump(mode='json'))
    assert response.status_code == 200
    mock_service.assert_called_once()
    mock_player_service_search.assert_called_once()
    mock_game_service_read.assert_called_once()

def test_create_player_full_game(mocker, test_client):
    fake_create_player_dto = CreatePlayerDTOFactory()

    fake_game = GameFactory(id=1,current_turn=10,status=GameStatus.WAITING)
    fake_players = PlayerFactory.create_batch(size=6)
    mock_player_service_search = mocker.patch('app.controllers.card.PlayerService.search', return_value=fake_players)
    mock_game_service_read= mocker.patch('app.controllers.card.GameService.read', return_value=fake_game)

    response = test_client.post('/api/player/1', json=fake_create_player_dto.model_dump(mode='json'))
    assert response.status_code == 400
    mock_player_service_search.assert_called_once()
    mock_game_service_read.assert_called_once()

def test_create_player_game_started(mocker, test_client):
    fake_create_player_dto = CreatePlayerDTOFactory()
    fake_game = GameFactory(id=1, current_turn=10, status=GameStatus.STARTED)
    mock_game_service_read= mocker.patch('app.controllers.card.GameService.read', return_value=fake_game)

    response = test_client.post('/api/player/1', json=fake_create_player_dto.model_dump(mode='json'))
    assert response.status_code == 400
    mock_game_service_read.assert_called_once()

def test_create_player_game_not_found(mocker, test_client):
    fake_create_player_dto = CreatePlayerDTOFactory()
    mock_game_service_read= mocker.patch('app.controllers.card.GameService.read', return_value=None)

    response = test_client.post('/api/player/1', json=fake_create_player_dto.model_dump(mode='json'))
    assert response.status_code == 404
    mock_game_service_read.assert_called_once()

def test_create_player_bad_birthday(mocker, test_client):
    fake_create_player_dto = CreatePlayerDTOFactory(player_date_of_birth=datetime(year=2100, month=1, day=1, tzinfo=UTC))
    fake_player = PlayerFactory(**fake_create_player_dto.model_dump())
    mock_service = mocker.patch('app.controllers.player.PlayerService.create', return_value=fake_player)
    response = test_client.post('/api/player/88',json=fake_create_player_dto.model_dump(mode='json'))
    assert response.status_code == 400

def test_create_player_bad_player_name(mocker, test_client):
    fake_create_player_dto = CreatePlayerDTOFactory(player_name="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    fake_player = PlayerFactory(**fake_create_player_dto.model_dump())
    mock_service = mocker.patch('app.controllers.player.PlayerService.create', return_value=fake_player)
    response = test_client.post('/api/player/88', json=fake_create_player_dto.model_dump(mode='json'))
    assert response.status_code == 400

def test_delete_player_ok(mocker, test_client):
    fake_player = PlayerFactory(token="1")
    fake_dto=DeletePlayerDTO(token="1")
    fake_game=GameFactory(status=GameStatus.WAITING)
    mock_service = mocker.patch('app.controllers.player.PlayerService.read',return_value=fake_player)
    mock_service = mocker.patch('app.controllers.player.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.player.PlayerService.delete', return_value=fake_player.id)
    response = test_client.request("DELETE","/api/player/88",json=fake_dto.model_dump(mode="json"),)
    assert response.status_code == 200

def test_delete_player_not_found(mocker, test_client):
    fake_player = PlayerFactory(token="1")
    fake_dto=DeletePlayerDTO(token="1")
    fake_game=GameFactory(status=GameStatus.WAITING)
    mock_service = mocker.patch('app.controllers.player.PlayerService.read',return_value=None)
    mock_service = mocker.patch('app.controllers.player.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.player.PlayerService.delete', return_value=fake_player.id)
    response = test_client.request("DELETE","/api/player/88",json=fake_dto.model_dump(mode="json"),)
    assert response.status_code == 404

def test_delete_player_invalid_token(mocker, test_client):
    fake_player = PlayerFactory(token="1")
    fake_dto=DeletePlayerDTO(token="99")
    fake_game=GameFactory(status=GameStatus.WAITING)
    mock_service = mocker.patch('app.controllers.player.PlayerService.read',return_value=fake_player)
    mock_service = mocker.patch('app.controllers.player.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.player.PlayerService.delete', return_value=fake_player.id)
    response = test_client.request("DELETE","/api/player/88",json=fake_dto.model_dump(mode="json"),)
    assert response.status_code == 401

def test_delete_player_start_game(mocker, test_client):
    fake_player = PlayerFactory(token="1")
    fake_dto=DeletePlayerDTO(token="1")
    fake_game=GameFactory(status=GameStatus.STARTED)
    mock_service = mocker.patch('app.controllers.player.PlayerService.read',return_value=fake_player)
    mock_service = mocker.patch('app.controllers.player.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.player.PlayerService.delete', return_value=fake_player.id)
    response = test_client.request("DELETE","/api/player/88",json=fake_dto.model_dump(mode="json"),)
    assert response.status_code == 400

def test_search_player_none(mocker,test_client):
    fake_player_filter = PlayerFilter(id__eq = 1,name__eq = "test",game_id__eq=1,position__eq=1)
    mock_service = mocker.patch('app.controllers.player.PlayerService.search', return_value=[])
    response = test_client.post('/api/player/search', json=fake_player_filter.model_dump(mode='json'))
    assert response.status_code == 200
    mock_service.assert_called_once()
    assert response.json() == []

def test_search_player_multi(mocker,test_client):
    fake_player_filter = PlayerFilter(id__eq = 1,name__eq =None,game_id__eq=1,position__eq=None)
    fake_players = PlayerFactory.create_batch(size=10)
    mock_service = mocker.patch('app.controllers.player.PlayerService.search', return_value=fake_players)
    response = test_client.post('/api/player/search', json=fake_player_filter.model_dump(mode='json'))
    assert response.status_code == 200
    mock_service.assert_called_once()
    assert len(response.json()) == 10