import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, ANY, call

import pytest
from dulwich.porcelain import status
from conftest import CardFactory, UpdateCardDTOFactory, PlayerFactory, EventTableFactory
from requests import session
from fastapi import HTTPException

from app.controllers.card import early_train_to_paddington, cards_off_the_table, look_into_the_ashes, \
    and_then_there_was_one_more, UpdateCardsDTO, another_victim, NOT_SO_FAST_TIME
from app.models.card import PublicCard, CardType
from app.models.detective_set import DetectiveSet
from app.models.game import GameStatus
from app.models.secret import Secret, SecretType
from app.services.card import CardFilter
from tests.conftest import GameFactory


def fake_set():
    fake_player = PlayerFactory()
    fake_card_detective = CardFactory(id=1, owner=fake_player.id, card_type=CardType.DETECTIVE)
    return DetectiveSet(id=1, owner=fake_player.id, detectives=[fake_card_detective], turn_played=2,game_id=1)

def test_card_not_found(mocker, test_client):
    # Given
    mocker_service = mocker.patch('app.controllers.card.CardService.read', return_value = None)

    # When
    response = test_client.get('/api/card/999')

    # Then
    assert response.status_code == 404
    mocker_service.assert_called_once()

def test_card_ok(mocker, test_client):
    # Given
    fake_card = CardFactory(owner = None)
    mocker_service = mocker.patch('app.controllers.card.CardService.read', return_value = fake_card)

    # When
    response = test_client.get('/api/card/999')

    # Then
    assert response.status_code == 200
    mocker_service.assert_called_once()
    assert response.json() == PublicCard(**fake_card.model_dump()).model_dump(mode='json')


def test_update_cards_not_cids(test_client):
    dto = UpdateCardDTOFactory(turn_discarded=1, owner=None, token='token-1')

    response = test_client.patch('/api/card', json={"cids": [], "dto": dto.model_dump(mode='json')})

    assert response.status_code == 422
    assert response.json()['detail'] == "No se mandaron cartas a descartar"


def test_update_cards_card_not_found(mocker, test_client):
    dto = UpdateCardDTOFactory(turn_discarded=0, owner=None, token='token-1')
    mocker.patch('app.controllers.card.CardService.read', return_value=None)

    response = test_client.patch('/api/card', json={"cids": [1], "dto": dto.model_dump(mode='json')})

    assert response.status_code == 404
    assert response.json()['detail'] == "No se pudo encontrar la carta"


def test_update_cards_card_without_owner(mocker, test_client):
    card = CardFactory(owner=None, turn_discarded=None, game_id=1)
    dto = UpdateCardDTOFactory(turn_discarded=1, owner=None, token='token-1')
    mocker.patch('app.controllers.card.CardService.read', return_value=card)

    response = test_client.patch('/api/card', json={"cids": [card.id], "dto": dto.model_dump(mode='json')})

    assert response.status_code == 404
    assert response.json()['detail'] == "La carta no tiene dueño"


def test_update_cards_card_already_discarded(mocker, test_client):
    card = CardFactory(owner=5, turn_discarded=3, game_id=1)
    dto = UpdateCardDTOFactory(turn_discarded=3, owner=None, token='token-1')
    mocker.patch('app.controllers.card.CardService.read', return_value=card)

    response = test_client.patch('/api/card', json={"cids": [card.id], "dto": dto.model_dump(mode='json')})

    assert response.status_code == 400
    assert response.json()['detail'] == "No se puede descartar una carta descartada"


def test_update_cards_card_in_set(mocker, test_client):
    card = CardFactory(owner=5, turn_discarded=None, game_id=1, set_id=123)
    dto = UpdateCardDTOFactory(turn_discarded=1, owner=None, token='token-1')
    mocker.patch('app.controllers.card.CardService.read', return_value=card)

    response = test_client.patch('/api/card', json={"cids": [card.id], "dto": dto.model_dump(mode='json')})

    assert response.status_code == 400
    assert response.json()['detail'] == "No se puede descartar una carta en set"


def test_update_cards_invalid_token(mocker, test_client):
    card = CardFactory(owner=5, turn_discarded=None, game_id=7)
    player = PlayerFactory(id=card.owner, game_id=card.game_id, token='otro-token')
    dto = UpdateCardDTOFactory(turn_discarded=2, owner=None, token='token-1')

    mocker.patch('app.controllers.card.CardService.read', return_value=card)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=player)

    response = test_client.patch('/api/card', json={"cids": [card.id], "dto": dto.model_dump(mode='json')})

    assert response.status_code == 401
    assert response.json()['detail'] == "No se puede descartar la carta: Token invalido"


def test_update_cards_game_not_found(mocker, test_client):
    game_id = 11
    card = CardFactory(owner=9, turn_discarded=None, game_id=game_id)
    player = PlayerFactory(id=card.owner, game_id=game_id, token='token-1')
    dto = UpdateCardDTOFactory(turn_discarded=4, owner=None, token=player.token)

    mocker.patch('app.controllers.card.CardService.read', return_value=card)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=player)
    mocker.patch('app.controllers.card.GameService.read', return_value=None)

    response = test_client.patch('/api/card', json={"cids": [card.id], "dto": dto.model_dump(mode='json')})

    assert response.status_code == 404
    assert response.json()['detail'] == "No se pudo encontrar el juego"


def test_update_cards_bad_game_status(mocker, test_client):
    game = GameFactory(current_turn=5, status=GameStatus.WAITING_FOR_CHOOSE_PLAYER)
    player = PlayerFactory(game_id=game.id, token='token-1')
    card = CardFactory(owner=player.id, turn_discarded=None, game_id=game.id)
    dto = UpdateCardDTOFactory(turn_discarded=3, owner=None, token=player.token)

    mocker.patch('app.controllers.card.CardService.read', return_value=card)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=player)
    mocker.patch('app.controllers.card.GameService.read', return_value=game)

    response = test_client.patch('/api/card', json={"cids": [card.id], "dto": dto.model_dump(mode='json')})

    assert response.status_code == 400
    assert response.json()['detail'] == "No se puede descartar la carta: Estado de partida invalida"

def test_update_cards_bad_turn(mocker, test_client):
    game = GameFactory(current_turn=5, status=GameStatus.TURN_START)
    player = PlayerFactory(game_id=game.id, token='token-1')
    card = CardFactory(owner=player.id, turn_discarded=None, game_id=game.id)
    dto = UpdateCardDTOFactory(turn_discarded=3, owner=None, token=player.token)

    mocker.patch('app.controllers.card.CardService.read', return_value=card)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=player)
    mocker.patch('app.controllers.card.GameService.read', return_value=game)

    response = test_client.patch('/api/card', json={"cids": [card.id], "dto": dto.model_dump(mode='json')})

    assert response.status_code == 400
    assert response.json()['detail'] == "Se debe descartar en el turno actual"


def test_update_cards_not_your_turn(mocker, test_client):
    game = GameFactory(current_turn=1, status=GameStatus.TURN_START)
    player = PlayerFactory(game_id=game.id, token='token-1', position=0)
    other_player = PlayerFactory(game_id=game.id, position=1)
    card = CardFactory(owner=player.id, turn_discarded=None, game_id=game.id)
    dto = UpdateCardsDTO(turn_discarded=game.current_turn, token=player.token)

    mocker.patch('app.controllers.card.CardService.read', return_value=card)
    mocker.patch('app.controllers.card.PlayerService.read', side_effect=[player, player])
    mocker.patch('app.controllers.card.GameService.read', return_value=game)
    mocker.patch('app.controllers.card.PlayerService.search', return_value=[player, other_player])

    response = test_client.patch('/api/card', json={"cids": [card.id], "dto": dto.model_dump(mode='json')})

    assert response.status_code == 412
    assert response.json()['detail'] == "No se puede descartar la carta: No es tu turno"


def test_update_cards_social_disgrace(mocker, test_client):
    game = GameFactory(current_turn=3, status=GameStatus.TURN_START)
    player = PlayerFactory(game_id=game.id, token='token-1', position=1,social_disgrace=True)
    other_player = PlayerFactory(game_id=game.id, position=0)
    card = CardFactory(owner=player.id, turn_discarded=None, game_id=game.id)
    other_card = CardFactory(id=card.id+1,owner=player.id, turn_discarded=None, game_id=game.id)
    cids = [card.id,other_card.id]
    dto = UpdateCardsDTO(turn_discarded=game.current_turn,token=player.token)

    mocker.patch('app.controllers.card.CardService.read', side_effect=[card, other_card])
    mocker.patch('app.controllers.card.PlayerService.read', return_value=player)
    mocker.patch('app.controllers.card.GameService.read', return_value=game)
    mocker.patch('app.controllers.card.PlayerService.search', return_value=[player, other_player])

    response = test_client.patch('/api/card', json={"cids": cids, "dto": dto.model_dump(mode='json')})

    assert response.status_code == 400
    assert response.json()['detail'] == "En desgracia social solo se permite descartar una carta"


def test_update_cards_bad_hand_cards(mocker, test_client):
    game = GameFactory(current_turn=3, status=GameStatus.TURN_START)
    player = PlayerFactory(game_id=game.id, token='token-1', position=1)
    other_player = PlayerFactory(game_id=game.id, position=0)
    card = CardFactory(owner=player.id, turn_discarded=None, game_id=game.id)
    dto = UpdateCardsDTO(turn_discarded=game.current_turn,token=player.token)

    mocker.patch('app.controllers.card.CardService.read', return_value=card)
    mocker.patch('app.controllers.card.PlayerService.read', side_effect=[player, player])
    mocker.patch('app.controllers.card.GameService.read', return_value=game)
    mocker.patch('app.controllers.card.PlayerService.search', return_value=[player, other_player])
    mocker.patch('app.controllers.card.CardService.search', return_value=[])

    response = test_client.patch('/api/card', json={"cids": [card.id], "dto": dto.model_dump(mode='json')})

    assert response.status_code == 400
    assert response.json()['detail'] == "No se pueden descartar las cartas: No tenes esa cantidad en mano"


def test_update_cards_early_train_to_paddington(mocker, test_client):
    game = GameFactory(current_turn=4, status=GameStatus.TURN_START)
    player = PlayerFactory(game_id=game.id, token='token-1', position=game.current_turn % 2)
    other_player = PlayerFactory(id=26, game_id=game.id, position=(game.current_turn + 1) % 2)
    card_one = CardFactory(owner=player.id, turn_discarded=None, game_id=game.id)
    card_two = CardFactory(owner=player.id, turn_discarded=None, game_id=game.id)
    dto = UpdateCardsDTO(turn_discarded=game.current_turn,token=player.token)

    mocker.patch('app.controllers.card.CardService.read', side_effect=[card_one, card_two])
    mocker.patch('app.controllers.card.PlayerService.read', side_effect=[player, player, player])
    mocker.patch('app.controllers.card.GameService.read', return_value=game)
    mocker.patch('app.controllers.card.PlayerService.search', return_value=[player, other_player])

    hand_cards = CardFactory.create_batch(size=2, game_id=game.id, owner=player.id,name="early-train-to-paddington")
    mocker.patch('app.controllers.card.CardService.search', return_value=hand_cards)
    mocker.patch('app.controllers.card.get_new_discarded_order', return_value=10)
    mocker.patch('app.controllers.card.early_train_to_paddington',return_value=None)

    card_update = mocker.patch('app.controllers.card.CardService.bulk_update',return_value = hand_cards )
    game_update = mocker.patch('app.controllers.card.GameService.update')

    response = test_client.patch('/api/card', json={"cids": [card_one.id, card_two.id], "dto": dto.model_dump(mode='json')})

    assert response.status_code == 200
    assert len(response.json()) == 2
    game_update.assert_awaited_once()


def test_update_cards_ok(mocker, test_client):
    game = GameFactory(current_turn=4, status=GameStatus.TURN_START)
    player = PlayerFactory(game_id=game.id, token='token-1', position=game.current_turn % 2)
    other_player = PlayerFactory(id=26, game_id=game.id, position=(game.current_turn + 1) % 2)
    card_one = CardFactory(owner=player.id, turn_discarded=None, game_id=game.id)
    card_two = CardFactory(owner=player.id, turn_discarded=None, game_id=game.id)
    dto = UpdateCardsDTO(turn_discarded=game.current_turn,token=player.token)

    mocker.patch('app.controllers.card.CardService.read', side_effect=[card_one, card_two])
    mocker.patch('app.controllers.card.PlayerService.read', side_effect=[player, player, player])
    mocker.patch('app.controllers.card.GameService.read', return_value=game)
    mocker.patch('app.controllers.card.PlayerService.search', return_value=[player, other_player])

    hand_cards = CardFactory.create_batch(size=2, game_id=game.id, owner=player.id)
    mocker.patch('app.controllers.card.CardService.search', return_value=hand_cards)
    mocker.patch('app.controllers.card.get_new_discarded_order', return_value=10)

    card_update = mocker.patch('app.controllers.card.CardService.bulk_update',return_value = hand_cards )
    game_update = mocker.patch('app.controllers.card.GameService.update')

    response = test_client.patch('/api/card', json={"cids": [card_one.id, card_two.id], "dto": dto.model_dump(mode='json')})

    assert response.status_code == 200
    assert len(response.json()) == 2
    game_update.assert_awaited_once()


def test_update_card_not_found(mocker, test_client):
    fake_update_dto = UpdateCardDTOFactory(owner=1, turn_discarded=None, token='token-1')
    mock_service = mocker.patch('app.controllers.card.CardService.read', return_value=None)

    response = test_client.patch('/api/card/999', json=fake_update_dto.model_dump(mode='json'))

    assert response.status_code == 404
    mock_service.assert_called_once()


def test_update_card_not_owner(mocker, test_client):
    fake_card = CardFactory(owner=None, turn_discarded=None)
    fake_update_dto = UpdateCardDTOFactory(owner=None, turn_discarded=None, token='token-1')
    mocker.patch('app.controllers.card.CardService.read', return_value=fake_card)

    response = test_client.patch('/api/card/1', json=fake_update_dto.model_dump(mode='json'))

    assert response.status_code == 422


def test_update_card_game_not_found(mocker, test_client):
    fake_card = CardFactory(owner=None, turn_discarded=None, game_id=1)
    fake_update_dto = UpdateCardDTOFactory(owner=5, turn_discarded=None, token='token-1')
    mocker.patch('app.controllers.card.CardService.read', return_value=fake_card)
    mock_game_service = mocker.patch('app.controllers.card.GameService.read', return_value=None)

    response = test_client.patch('/api/card/5', json=fake_update_dto.model_dump(mode='json'))

    assert response.status_code == 404
    mock_game_service.assert_called_once()


def test_update_card_invalid_game_status(mocker, test_client):
    fake_game = GameFactory(id=1, status=GameStatus.TURN_START)
    fake_card = CardFactory(owner=None, turn_discarded=None, game_id=fake_game.id)
    fake_player = PlayerFactory(id=5, game_id=fake_game.id, token='token-1')
    fake_update_dto = UpdateCardDTOFactory(owner=fake_player.id, token=fake_player.token)

    mocker.patch('app.controllers.card.CardService.read', return_value=fake_card)
    mocker.patch('app.controllers.card.GameService.read', return_value=fake_game)

    response = test_client.patch(f'/api/card/{fake_card.id}', json=fake_update_dto.model_dump(mode='json'))

    assert response.status_code == 400
    assert response.json()['detail'] == "No se puede agarrar la carta: Estado de partida invalido"


def test_update_card_player_not_found(mocker, test_client):
    fake_card = CardFactory(owner=None, turn_discarded=None, game_id=2)
    fake_game = GameFactory(id=2, status=GameStatus.FINALIZE_TURN_DRAFT)
    fake_update_dto = UpdateCardDTOFactory(owner=6, turn_discarded=None, token='token-1')
    mocker.patch('app.controllers.card.CardService.read', return_value=fake_card)
    mocker.patch('app.controllers.card.GameService.read', return_value=fake_game)
    mock_player = mocker.patch('app.controllers.card.PlayerService.read', return_value=None)

    response = test_client.patch('/api/card/6', json=fake_update_dto.model_dump(mode='json'))

    assert response.status_code == 404
    mock_player.assert_called_once()


def test_update_card_player_not_in_game(mocker, test_client):
    fake_card = CardFactory(owner=None, turn_discarded=None, game_id=3)
    fake_game = GameFactory(id=3,status=GameStatus.FINALIZE_TURN_DRAFT)
    fake_player = PlayerFactory(game_id=999, token='token-1')
    fake_update_dto = UpdateCardDTOFactory(owner=fake_player.id, turn_discarded=None, token=fake_player.token)
    mocker.patch('app.controllers.card.CardService.read', return_value=fake_card)
    mocker.patch('app.controllers.card.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=fake_player)

    response = test_client.patch('/api/card/7', json=fake_update_dto.model_dump(mode='json'))

    assert response.status_code == 400


def test_update_card_invalid_token(mocker, test_client):
    fake_game = GameFactory(id=4, current_turn=0,status=GameStatus.FINALIZE_TURN_DRAFT)
    fake_player = PlayerFactory(id=8, game_id=fake_game.id, token='otro-token', position=0)
    fake_card = CardFactory(owner=None, turn_discarded=None, game_id=fake_game.id)
    fake_update_dto = UpdateCardDTOFactory(owner=fake_player.id, turn_discarded=None, token='token-1')

    mocker.patch('app.controllers.card.CardService.read', return_value=fake_card)
    mocker.patch('app.controllers.card.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=fake_player)

    response = test_client.patch('/api/card/8', json=fake_update_dto.model_dump(mode='json'))

    assert response.status_code == 401


def test_update_card_not_your_turn(mocker, test_client):
    fake_game = GameFactory(current_turn=1,status=GameStatus.FINALIZE_TURN_DRAFT)
    fake_player = PlayerFactory(game_id=fake_game.id, token='token-1', position=0)
    other_player = PlayerFactory(game_id=fake_game.id, position=1)
    players_in_game = [fake_player, other_player]
    fake_card = CardFactory(owner=None, turn_discarded=None, game_id=fake_game.id)
    fake_update_dto = UpdateCardDTOFactory(owner=fake_player.id, turn_discarded=None, token=fake_player.token)

    mocker.patch('app.controllers.card.CardService.read', return_value=fake_card)
    mocker.patch('app.controllers.card.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card.PlayerService.search', return_value=players_in_game)

    response = test_client.patch('/api/card/10', json=fake_update_dto.model_dump(mode='json'))

    assert response.status_code == 412



def test_update_card_too_many_cards(mocker, test_client):
    fake_game = GameFactory(current_turn=0,status=GameStatus.FINALIZE_TURN_DRAFT)
    fake_player = PlayerFactory(game_id=fake_game.id, token='token-1', position=0)
    other_player = PlayerFactory(game_id=fake_game.id, position=1)
    players_in_game = [fake_player, other_player]
    fake_card = CardFactory(owner=None, turn_discarded=None, game_id=fake_game.id)
    fake_update_dto = UpdateCardDTOFactory(owner=fake_player.id, turn_discarded=None, token=fake_player.token)

    mocker.patch('app.controllers.card.CardService.read', return_value=fake_card)
    mocker.patch('app.controllers.card.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card.PlayerService.search', return_value=players_in_game)
    mocker.patch('app.controllers.card.DetectiveSetService.search', return_value=[fake_set()])

    discard_list = [CardFactory(game_id=fake_game.id, turn_discarded=fake_game.current_turn)]
    player_cards = CardFactory.create_batch(size=6, game_id=fake_game.id, owner=fake_player.id)
    mocker.patch('app.controllers.card.CardService.search', side_effect=[player_cards])

    response = test_client.patch('/api/card/12', json=fake_update_dto.model_dump(mode='json'))

    assert response.status_code == 412


def test_update_card_not_in_draft(mocker, test_client):
    fake_game = GameFactory(current_turn=3,status=GameStatus.FINALIZE_TURN_DRAFT)
    fake_player = PlayerFactory(game_id=fake_game.id, token='token-1', position=fake_game.current_turn % 2)
    other_player = PlayerFactory(game_id=fake_game.id, position=1)
    players_in_game = [fake_player, other_player]
    fake_card = CardFactory(owner=None, turn_discarded=None, game_id=fake_game.id)
    fake_update_dto = UpdateCardDTOFactory(owner=fake_player.id, turn_discarded=None, token=fake_player.token)

    mocker.patch('app.controllers.card.CardService.read', return_value=fake_card)
    mocker.patch('app.controllers.card.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card.PlayerService.search', return_value=players_in_game)
    mocker.patch('app.controllers.card.DetectiveSetService.search', return_value=[fake_set()])

    discard_list = [CardFactory(game_id=fake_game.id, turn_discarded=fake_game.current_turn)]
    player_cards = CardFactory.create_batch(size=3, game_id=fake_game.id, owner=fake_player.id)
    draft_cards = [CardFactory(id=999, owner=None, turn_discarded=None, game_id=fake_game.id)]
    mocker.patch('app.controllers.card.CardService.search', side_effect=[discard_list, player_cards, draft_cards])

    response = test_client.patch(f'/api/card/{fake_card.id}', json=fake_update_dto.model_dump(mode='json'))

    assert response.status_code == 400


def test_update_card_ok(mocker, test_client):
    fake_game = GameFactory(id=10, current_turn=6,status=GameStatus.FINALIZE_TURN_DRAFT)
    fake_player = PlayerFactory(id=18, game_id=10, token='token-1', position=fake_game.current_turn % 2)
    other_player = PlayerFactory(id=19, game_id=10, position=1)
    players_in_game = [fake_player, other_player]
    fake_card = CardFactory(id=60, owner=None, turn_discarded=None, game_id=10)
    fake_update_dto = UpdateCardDTOFactory(owner=18, turn_discarded=None, token=fake_player.token)
    updated_card = CardFactory(id=60, owner=18, game_id=10, turn_discarded=fake_card.turn_discarded)

    mocker.patch('app.controllers.card.CardService.read', return_value=fake_card)
    mocker.patch('app.controllers.card.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card.DetectiveSetService.search', return_value=[fake_set()])
    mock_player_search=mocker.patch('app.controllers.card.PlayerService.search', return_value=players_in_game)

    discard_list = [CardFactory(game_id=fake_game.id, turn_discarded=fake_game.current_turn)]
    player_cards = CardFactory.create_batch(size=2, game_id=fake_game.id, owner=fake_player.id)
    draft_cards = [CardFactory(id=70, owner=None, turn_discarded=None, game_id=fake_game.id), fake_card]
    mock_card_search=mocker.patch('app.controllers.card.CardService.search', side_effect=[player_cards, draft_cards])
    mock_card_update = mocker.patch('app.controllers.card.CardService.update', new_callable=AsyncMock)
    mock_card_update.return_value = updated_card

    response = test_client.patch(f'/api/card/{fake_card.id}', json=fake_update_dto.model_dump(mode='json'))

    assert response.status_code == 200
    assert len(mock_player_search.mock_calls) == 1
    assert len(mock_card_search.mock_calls) == 2
    mock_card_update.assert_called_once()


def test_update_card_updates_game_status_when_needed(mocker, test_client):
    fake_game = GameFactory(id=11, current_turn=4, status=GameStatus.FINALIZE_TURN)
    fake_player = PlayerFactory(id=21, game_id=fake_game.id, token='token-1', position=fake_game.current_turn % 2)
    other_player = PlayerFactory(id=22, game_id=fake_game.id, position=(fake_player.position + 1) % 2)
    players_in_game = [fake_player, other_player]
    fake_card = CardFactory(id=101, owner=None, turn_discarded=None, game_id=fake_game.id)
    fake_update_dto = UpdateCardDTOFactory(owner=fake_player.id, token=fake_player.token)
    updated_card = CardFactory(id=fake_card.id, owner=fake_player.id, game_id=fake_game.id)

    mocker.patch('app.controllers.card.CardService.read', return_value=fake_card)
    mocker.patch('app.controllers.card.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card.PlayerService.search', return_value=players_in_game)
    mocker.patch('app.controllers.card.DetectiveSetService.search', return_value=[fake_set()])

    player_cards = CardFactory.create_batch(size=2, game_id=fake_game.id, owner=fake_player.id)
    draft_cards = [CardFactory(id=707, owner=None, turn_discarded=None, game_id=fake_game.id), fake_card]
    mocker.patch('app.controllers.card.CardService.search', side_effect=[player_cards, draft_cards])

    mock_card_update = mocker.patch('app.controllers.card.CardService.update', new_callable=AsyncMock, return_value=updated_card)
    mock_game_update = mocker.patch('app.controllers.card.GameService.update', new_callable=AsyncMock)

    response = test_client.patch(f'/api/card/{fake_card.id}', json=fake_update_dto.model_dump(mode='json'))

    assert response.status_code == 200
    mock_card_update.assert_awaited_once()
    mock_game_update.assert_awaited_once()


def test_search_card(mocker, test_client):
    # Given
    card_filter = CardFilter(id__eq=1, game_id__eq=1, owner__eq=1, card_type__in=[])
    card = CardFactory()
    mocker_service = mocker.patch('app.controllers.card.CardService.search', return_value=[card])
    # When
    response = test_client.post('/api/card/search', json=card_filter.model_dump(mode='json'))
    # Then
    assert response.status_code == 200
    mocker_service.assert_called_once()


def test_cancel_action_event_not_found(mocker, test_client):
    mocker.patch('app.controllers.card.EventTableService.read', return_value=None)

    response = test_client.post('/api/card/cancel_action/11', json={"not_so_fast": 22, "token": "tok"})

    assert response.status_code == 404
    assert response.json()['detail'] == "No se puede cancelar la accion: No se encontró el evento"


def test_cancel_action_not_so_fast_not_found(mocker, test_client):
    cancel_event = EventTableFactory(game_id=1, turn_played=3, action="to_cancel", completed_action=False)
    mocker.patch('app.controllers.card.EventTableService.read', return_value=cancel_event)
    mocker.patch('app.controllers.card.CardService.read', return_value=None)

    response = test_client.post('/api/card/cancel_action/12', json={"not_so_fast": 99, "token": "tok"})

    assert response.status_code == 404
    assert response.json()['detail'] == "No se puede cancelar la accion: Carta no encontrada"


def test_cancel_action_not_last_cancelable_event(mocker, test_client):
    game = GameFactory(status=GameStatus.WAITING_FOR_CANCEL_ACTION)
    player = PlayerFactory(game_id=game.id, token='token-valido')
    not_so_fast = CardFactory(game_id=game.id, owner=player.id)
    cancel_event = EventTableFactory(id=13, game_id=game.id, turn_played=game.current_turn, action="to_cancel", completed_action=True)
    last_event = EventTableFactory(id=999, game_id=game.id, turn_played=game.current_turn, action="to_cancel", completed_action=False)

    mocker.patch('app.controllers.card.EventTableService.read', return_value=cancel_event)
    mocker.patch('app.controllers.card.EventTableService.search', return_value=[last_event])
    mocker.patch('app.controllers.card.CardService.read', return_value=not_so_fast)
    mocker.patch('app.controllers.card.GameService.read', return_value=game)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=player)

    response = test_client.post('/api/card/cancel_action/13', json={"not_so_fast": not_so_fast.id, "token": player.token})

    assert response.status_code == 400
    assert response.json()['detail'] == "No se puede cancelar la accion: No es la ultima accion cancelable"


def test_cancel_action_invalid_game_status(mocker, test_client):
    game = GameFactory(status=GameStatus.TURN_START)
    not_so_fast = CardFactory(game_id=game.id)
    cancel_event = EventTableFactory(game_id=game.id, turn_played=game.current_turn, action="to_cancel", completed_action=False)

    mocker.patch('app.controllers.card.EventTableService.read', return_value=cancel_event)
    mocker.patch('app.controllers.card.CardService.read', return_value=not_so_fast)
    mocker.patch('app.controllers.card.GameService.read', return_value=game)

    response = test_client.post('/api/card/cancel_action/14', json={"not_so_fast": not_so_fast.id, "token": "tok"})

    assert response.status_code == 400
    assert response.json()['detail'] == "No se puede cancelar la accion: Estado de partida invalido"


def test_cancel_action_invalid_token(mocker, test_client):
    game = GameFactory(status=GameStatus.WAITING_FOR_CANCEL_ACTION)
    player = PlayerFactory(game_id=game.id, token='token-valido')
    not_so_fast = CardFactory(game_id=game.id, owner=player.id)
    cancel_event = EventTableFactory(game_id=game.id, turn_played=game.current_turn, action="to_cancel", completed_action=False)

    mocker.patch('app.controllers.card.EventTableService.read', return_value=cancel_event)
    mocker.patch('app.controllers.card.EventTableService.search', return_value=[cancel_event])
    mocker.patch('app.controllers.card.CardService.read', return_value=not_so_fast)
    mocker.patch('app.controllers.card.GameService.read', return_value=game)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=player)

    response = test_client.post('/api/card/cancel_action/15', json={"not_so_fast": not_so_fast.id, "token": "otro-token"})

    assert response.status_code == 401
    assert response.json()['detail'] == "No se puede cancelar la accion: Token inválido"


def test_cancel_action_invalid_turn(mocker, test_client):
    game = GameFactory(status=GameStatus.WAITING_FOR_CANCEL_ACTION, current_turn=8)
    player = PlayerFactory(game_id=game.id, token='secret')
    not_so_fast = CardFactory(game_id=game.id, owner=player.id)
    cancel_event = EventTableFactory(game_id=game.id, turn_played=game.current_turn + 1, action="to_cancel", completed_action=False)

    mocker.patch('app.controllers.card.EventTableService.read', return_value=cancel_event)
    mocker.patch('app.controllers.card.CardService.read', return_value=not_so_fast)
    mocker.patch('app.controllers.card.GameService.read', return_value=game)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=player)

    response = test_client.post('/api/card/cancel_action/17', json={"not_so_fast": not_so_fast.id, "token": player.token})

    assert response.status_code == 400
    assert response.json()['detail'] == "No se puede cancelar la accion: Turno invalido"


from app.database.engine import db_session


def test_cancel_action_success(mocker, test_client):
    timestamp = datetime.now()
    game = GameFactory(status=GameStatus.WAITING_FOR_CANCEL_ACTION, timestamp=timestamp, current_turn=7)
    player = PlayerFactory(game_id=game.id, token='token-valido')
    not_so_fast = CardFactory(game_id=game.id, owner=player.id)
    cancel_event = EventTableFactory(game_id=game.id, turn_played=game.current_turn, action="to_cancel", completed_action=False)
    

    dummy_session = mocker.Mock()
    dummy_session.commit.return_value = None
    dummy_session.refresh.return_value = None

    def fake_db_session():
        yield dummy_session

    test_client.app.dependency_overrides[db_session] = fake_db_session

    mocker.patch('app.controllers.card.EventTableService.read', return_value=cancel_event)
    canceled_times_event = EventTableFactory(
        game_id=game.id,
        turn_played=game.current_turn,
        action="canceled_times",
        target_card=0,
        completed_action=False,
    )
    mock_event_search = mocker.patch(
        'app.controllers.card.EventTableService.search',
        side_effect=[[cancel_event], [canceled_times_event]],
    )
    mock_event_create = mocker.patch('app.controllers.card.EventTableService.create', new_callable=AsyncMock, return_value=None)
    mocker.patch('app.controllers.card.CardService.read', return_value=not_so_fast)
    mocker.patch('app.controllers.card.GameService.read', return_value=game)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=player)
    mock_get_order = mocker.patch('app.controllers.card.get_new_discarded_order', return_value=55)
    mock_card_update = mocker.patch('app.controllers.card.CardService.update', new_callable=AsyncMock, return_value=not_so_fast)
    mocker.patch('app.controllers.card.ChatService.create')

    response = test_client.post('/api/card/cancel_action/16', json={"not_so_fast": not_so_fast.id, "token": player.token})

    assert response.status_code == 200
    assert response.json() == 200
    dummy_session.commit.assert_called_once()
    dummy_session.refresh.assert_not_called()
    assert cancel_event.completed_action is True
    assert mock_event_search.call_count == 2
    first_call_kwargs = mock_event_search.call_args_list[0].kwargs
    assert first_call_kwargs["filterby"] == {
        "game_id__eq": game.id,
        "turn_played__eq": game.current_turn,
        "action__eq": "to_cancel",
        "completed_action__eq": False,
    }
    second_call_kwargs = mock_event_search.call_args_list[1].kwargs
    assert second_call_kwargs["filterby"] == {
        "game_id__eq": game.id,
        "turn_played__eq": game.current_turn,
        "action__eq": "canceled_times",
    }
    mock_event_create.assert_awaited_once_with(
        session=dummy_session,
        data={
            "game_id": game.id,
            "turn_played": game.current_turn,
            "target_card": not_so_fast.id,
            "action": "to_cancel",
        },
    )
    mock_card_update.assert_awaited_once()
    card_update_kwargs = mock_card_update.await_args.kwargs
    assert card_update_kwargs["session"] == dummy_session
    assert card_update_kwargs["oid"] == not_so_fast.id
    assert card_update_kwargs["data"] == {
        "owner": None,
        "content": "nsf",
    }

    test_client.app.dependency_overrides.pop(db_session, None)


def test_cancel_action_success_uses_event_filters(mocker, test_client):
    timestamp = datetime.now()
    game = GameFactory(status=GameStatus.WAITING_FOR_CANCEL_ACTION, timestamp=timestamp, current_turn=10)
    player = PlayerFactory(game_id=game.id, token='token-valido')
    not_so_fast = CardFactory(game_id=game.id, owner=player.id)
    cancel_event = EventTableFactory(game_id=game.id, turn_played=game.current_turn, action="to_cancel", completed_action=False)

    dummy_session = mocker.Mock()
    dummy_session.commit.return_value = None
    dummy_session.refresh.return_value = None

    def fake_db_session():
        yield dummy_session

    test_client.app.dependency_overrides[db_session] = fake_db_session

    mocker.patch('app.controllers.card.EventTableService.read', return_value=cancel_event)
    canceled_times_event = EventTableFactory(
        game_id=game.id,
        turn_played=game.current_turn,
        action="canceled_times",
        target_card=0,
        completed_action=False,
    )
    mock_event_search = mocker.patch(
        'app.controllers.card.EventTableService.search',
        side_effect=[[cancel_event], [canceled_times_event]],
    )
    mock_event_create = mocker.patch('app.controllers.card.EventTableService.create', new_callable=AsyncMock, return_value=None)
    mocker.patch('app.controllers.card.CardService.read', return_value=not_so_fast)
    mocker.patch('app.controllers.card.GameService.read', return_value=game)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=player)
    mock_get_order = mocker.patch('app.controllers.card.get_new_discarded_order', return_value=70)
    mock_card_update = mocker.patch('app.controllers.card.CardService.update', new_callable=AsyncMock, return_value=not_so_fast)
    mocker.patch('app.controllers.card.ChatService.create')

    response = test_client.post('/api/card/cancel_action/99', json={"not_so_fast": not_so_fast.id, "token": player.token})

    assert response.status_code == 200
    dummy_session.commit.assert_called_once()
    dummy_session.refresh.assert_not_called()
    assert mock_event_search.call_count == 2
    mock_event_create.assert_awaited_once()
    assert cancel_event.completed_action is True
    mock_card_update.assert_awaited_once()


    test_client.app.dependency_overrides.pop(db_session, None)


def test_play_card_ok(mocker, test_client):
    # Given
    fake_card = CardFactory(id=1, owner=2, game_id=1, name="EjemploCarta")
    fake_player = PlayerFactory(id=2, token="token123", position=0, game_id=1)
    fake_game = GameFactory(id=1, current_turn=0)
    fake_players = [fake_player, PlayerFactory(id=3, position=1)]

    # Mock de servicios
    mocker.patch('app.controllers.card.CardService.read', return_value=fake_card)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card.PlayerService.read_by_token', return_value=fake_player)
    mocker.patch('app.controllers.card.PlayerService.search', return_value=fake_players)
    mocker.patch('app.controllers.card.GameService.read', return_value=fake_game)

    mock_action = mocker.AsyncMock(return_value={"ok": True})
    mocker.patch.dict('app.controllers.card.CARD_ACTIONS', {"EjemploCarta": mock_action})

    # When
    response = test_client.post(
        f"/api/card/play_card/{fake_card.id}?token={fake_player.token}",
        json={"target_players": [3], "target_secrets": [], "target_cards": [], "target_sets": []},
    )

    # Then
    assert response.status_code == 200
    mock_action.assert_called_once()


def test_play_card_card_not_found(mocker, test_client):
    mocker.patch('app.controllers.card.CardService.read', return_value=None)

    response = test_client.post(
        "/api/card/play_card/1?token=token123",
        json={"target_players": [], "target_secrets": [], "target_cards": [], "target_sets": []},
    )

    assert response.status_code == 404
    assert "Carta no encontrada" in response.text


def test_play_card_player_not_found(mocker, test_client):
    fake_card = CardFactory(id=1, owner=2, game_id=1, name="EjemploCarta")

    mocker.patch('app.controllers.card.CardService.read', return_value=fake_card)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=None)

    response = test_client.post(
        f"/api/card/play_card/{fake_card.id}?token=token123",
        json={"target_players": [], "target_secrets": [], "target_cards": [], "target_sets": []},
    )

    assert response.status_code == 404
    assert "Jugador no encontrado" in response.text


def test_play_card_token_invalid(mocker, test_client):
    fake_card = CardFactory(id=1, owner=2, game_id=1, name="EjemploCarta")
    fake_player = PlayerFactory(id=2, token="token123", position=0, game_id=1)
    fake_game = GameFactory(id=1, current_turn=0, player_in_action = fake_player.id + 1, status=GameStatus.TURN_START)

    mocker.patch('app.controllers.card.CardService.read', return_value=fake_card)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card.PlayerService.read_by_token', return_value=None)
    mocker.patch('app.controllers.card.PlayerService.search', return_value=[fake_player])
    mocker.patch('app.controllers.card.GameService.read', return_value=fake_game)

    response = test_client.post(
        f"/api/card/play_card/{fake_card.id}?token={fake_player.token}",
        json={"target_players": [], "target_secrets": [], "target_cards": [], "target_sets": []},
    )

    assert response.status_code == 401


def test_play_card_social_disgrace(mocker, test_client):
    fake_card = CardFactory(id=1, owner=2, game_id=1, name="EjemploCarta")
    fake_player = PlayerFactory(id=2, token="token123", position=0, game_id=1,social_disgrace=True)
    fake_game = GameFactory(id=1, current_turn=0, player_in_action = fake_player.id + 1, status=GameStatus.TURN_START)

    mocker.patch('app.controllers.card.CardService.read', return_value=fake_card)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card.PlayerService.read_by_token', return_value=fake_player)
    mocker.patch('app.controllers.card.PlayerService.search', return_value=[fake_player])
    mocker.patch('app.controllers.card.GameService.read', return_value=fake_game)

    response = test_client.post(
        f"/api/card/play_card/{fake_card.id}?token={fake_player.token}",
        json={"target_players": [], "target_secrets": [], "target_cards": [], "target_sets": []},
    )

    assert response.status_code == 400
    assert "No se pueden jugar cartas en desgracia social" in response.text


def test_play_card_game_not_found(mocker, test_client):
    fake_card = CardFactory(id=1, owner=2, game_id=1, name="EjemploCarta")
    fake_player = PlayerFactory(id=2, token="token123", position=0, game_id=1)

    mocker.patch('app.controllers.card.CardService.read', return_value=fake_card)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card.PlayerService.read_by_token', return_value=fake_player)
    mocker.patch('app.controllers.card.PlayerService.search', return_value=[fake_player])
    mocker.patch('app.controllers.card.GameService.read', return_value=None)

    response = test_client.post(
        f"/api/card/play_card/{fake_card.id}?token={fake_player.token}",
        json={"target_players": [], "target_secrets": [], "target_cards": [], "target_sets": []},
    )

    assert response.status_code == 404
    assert "Juego no encontrado" in response.text


def test_play_card_without_name(mocker, test_client):
    fake_card = CardFactory(id=1, owner=2, game_id=1, name=None)
    fake_player = PlayerFactory(id=2, token="token123", position=0, game_id=1)
    fake_game = GameFactory(id=1, current_turn=0)

    mocker.patch('app.controllers.card.CardService.read', return_value=fake_card)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card.PlayerService.read_by_token', return_value=fake_player)
    mocker.patch('app.controllers.card.PlayerService.search', return_value=[fake_player])
    mocker.patch('app.controllers.card.GameService.read', return_value=fake_game)

    response = test_client.post(
        f"/api/card/play_card/{fake_card.id}?token={fake_player.token}",
        json={"target_players": [], "target_secrets": [], "target_cards": [], "target_sets": []},
    )

    assert response.status_code == 400
    assert "La carta no tiene nombre definido" in response.text


def test_play_card_not_implemented(mocker, test_client):
    # Given
    fake_card = CardFactory(id=1, owner=2, game_id=1, name="CartaNoImplementada")
    fake_player = PlayerFactory(id=2, token="token123", position=0, game_id=1)
    fake_game = GameFactory(id=1, current_turn=0)
    fake_players = [fake_player]

    mocker.patch('app.controllers.card.CardService.read', return_value=fake_card)
    mocker.patch('app.controllers.card.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card.PlayerService.read_by_token', return_value=fake_player)
    mocker.patch('app.controllers.card.PlayerService.search', return_value=fake_players)
    mocker.patch('app.controllers.card.GameService.read', return_value=fake_game)
    mocker.patch.dict('app.controllers.card.CARD_ACTIONS', {})

    # When
    response = test_client.post(
        f"/api/card/play_card/{fake_card.id}?token={fake_player.token}",
        json={"target_players": [], "target_secrets": [], "target_cards": [], "target_sets": []},
    )

    # Then
    assert response.status_code == 404
