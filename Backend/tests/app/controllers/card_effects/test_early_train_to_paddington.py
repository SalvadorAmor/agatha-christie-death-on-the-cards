import asyncio
from unittest.mock import AsyncMock, ANY, call

import pytest
from conftest import CardFactory, UpdateCardDTOFactory, PlayerFactory
from requests import session
from fastapi import HTTPException

from app.controllers.card_effects.early_train_to_paddington import early_train_to_paddington
from app.models.card import PublicCard, CardType
from app.models.detective_set import DetectiveSet
from app.models.game import GameStatus
from app.models.secret import Secret, SecretType
from app.services.card import CardFilter
from tests.conftest import GameFactory


def test_play_travel_to_paddington(mocker):
    fake_game = GameFactory(status=GameStatus.TURN_START)
    fake_card = CardFactory(game_id=fake_game.id,discarded_order=5)
    fake_cards_to_update = [fake_card]

    mock_service_game_read = mocker.patch('app.controllers.card_effects.early_train_to_paddington.GameService.read', return_value=fake_game)
    mock_service_game_update=mocker.patch('app.controllers.card_effects.early_train_to_paddington.GameService.update', return_value=fake_game)
    mock_service_card_update=mocker.patch('app.controllers.card_effects.early_train_to_paddington.CardService.update', return_value=fake_card)
    mock_service_card_search=mocker.patch('app.controllers.card_effects.early_train_to_paddington.CardService.search', return_value=fake_cards_to_update)
    mock_service_card_delete=mocker.patch('app.controllers.card_effects.early_train_to_paddington.CardService.delete', return_value=fake_card.id)
    mocker.patch('app.controllers.card_effects.early_train_to_paddington.not_so_fast_status', return_value=False)
    mocker.patch('app.controllers.card_effects.early_train_to_paddington.ChatService.create')

    asyncio.run(early_train_to_paddington(card=fake_card, session=None))

    mock_service_game_read.assert_called_once_with(session=None, oid=fake_card.game_id)
    mock_service_card_delete.assert_called_once()
    assert len(mock_service_game_update.mock_calls) == 1
    assert len(mock_service_card_update.mock_calls) == 2
    assert len(mock_service_card_search.mock_calls) == 2


def test_play_travel_to_paddington_canceled_finishes_turn(mocker):
    fake_game = GameFactory(status=GameStatus.TURN_START, current_turn=6)
    fake_card = CardFactory(game_id=fake_game.id, discarded_order=7)

    mocker.patch('app.controllers.card_effects.early_train_to_paddington.GameService.read', return_value=fake_game)
    mock_card_update = mocker.patch('app.controllers.card_effects.early_train_to_paddington.CardService.update', new_callable=AsyncMock)
    mock_card_delete = mocker.patch('app.controllers.card_effects.early_train_to_paddington.CardService.delete', new_callable=AsyncMock)
    mock_card_search = mocker.patch('app.controllers.card_effects.early_train_to_paddington.CardService.search')
    mock_game_update = mocker.patch('app.controllers.card_effects.early_train_to_paddington.GameService.update', new_callable=AsyncMock)
    mocker.patch('app.controllers.card_effects.early_train_to_paddington.not_so_fast_status', return_value=True)
    mocker.patch('app.controllers.card_effects.early_train_to_paddington.ChatService.create')

    asyncio.run(early_train_to_paddington(card=fake_card, session=None))

    mock_card_update.assert_awaited_once_with(
        session=None, oid=fake_card.id, data={'turn_played': fake_game.current_turn}
    )
    mock_card_delete.assert_awaited_once_with(session=None, oid=fake_card.id)
    mock_game_update.assert_awaited_once_with(
        session=None,
        oid=fake_game.id,
        data={'status': GameStatus.FINALIZE_TURN, 'player_in_action': None},
    )
    mock_card_search.assert_not_called()


def test_play_travel_to_paddington_canceled_in_discard(mocker):
    fake_game = GameFactory(status=GameStatus.TURN_START, current_turn=7)
    fake_card = CardFactory(game_id=fake_game.id, discarded_order=8)

    mocker.patch('app.controllers.card_effects.early_train_to_paddington.GameService.read', return_value=fake_game)
    mock_card_update = mocker.patch('app.controllers.card_effects.early_train_to_paddington.CardService.update', new_callable=AsyncMock)
    mock_card_delete = mocker.patch('app.controllers.card_effects.early_train_to_paddington.CardService.delete', new_callable=AsyncMock)
    mock_card_search = mocker.patch('app.controllers.card_effects.early_train_to_paddington.CardService.search')
    mock_game_update = mocker.patch('app.controllers.card_effects.early_train_to_paddington.GameService.update', new_callable=AsyncMock)
    mocker.patch('app.controllers.card_effects.early_train_to_paddington.not_so_fast_status', return_value=True)
    mocker.patch('app.controllers.card_effects.early_train_to_paddington.ChatService.create')

    asyncio.run(early_train_to_paddington(card=fake_card, session=None, in_discard=True))

    mock_card_update.assert_awaited_once()
    mock_card_delete.assert_awaited_once_with(session=None, oid=fake_card.id)
    mock_game_update.assert_not_awaited()
    mock_card_search.assert_not_called()


def test_play_travel_to_paddington_with_remaining_deck(mocker):
    fake_game = GameFactory(status=GameStatus.TURN_START, current_turn=4)
    fake_card = CardFactory(game_id=fake_game.id, discarded_order=5)
    cards_to_update = CardFactory.create_batch(size=7, game_id=fake_game.id)

    mocker.patch('app.controllers.card_effects.early_train_to_paddington.GameService.read', return_value=fake_game)
    mock_game_update = mocker.patch('app.controllers.card_effects.early_train_to_paddington.GameService.update')
    mock_card_update = mocker.patch('app.controllers.card_effects.early_train_to_paddington.CardService.update')
    mock_card_search = mocker.patch('app.controllers.card_effects.early_train_to_paddington.CardService.search', return_value=cards_to_update)
    mock_card_delete = mocker.patch('app.controllers.card_effects.early_train_to_paddington.CardService.delete')
    mocker.patch('app.controllers.card_effects.early_train_to_paddington.get_new_discarded_order', return_value=10)
    mocker.patch('app.controllers.card_effects.early_train_to_paddington.not_so_fast_status',return_value=False)
    mocker.patch('app.controllers.card_effects.early_train_to_paddington.ChatService.create')

    asyncio.run(early_train_to_paddington(card=fake_card, session=None))

    assert mock_card_search.call_count == 1
    assert mock_card_update.await_count == 7
    mock_card_delete.assert_awaited_once()
    mock_game_update.assert_awaited_once()

def test_play_travel_to_paddington_in_discard(mocker):
    fake_game = GameFactory(status=GameStatus.TURN_START, current_turn=4)
    fake_card = CardFactory(game_id=fake_game.id, discarded_order=5)
    cards_to_update = CardFactory.create_batch(size=7, game_id=fake_game.id)

    mocker.patch('app.controllers.card_effects.early_train_to_paddington.GameService.read', return_value=fake_game)
    mock_game_update = mocker.patch('app.controllers.card_effects.early_train_to_paddington.GameService.update')
    mock_card_update = mocker.patch('app.controllers.card_effects.early_train_to_paddington.CardService.update')
    mock_card_search = mocker.patch('app.controllers.card_effects.early_train_to_paddington.CardService.search', return_value=cards_to_update)
    mock_card_delete = mocker.patch('app.controllers.card_effects.early_train_to_paddington.CardService.delete')
    mocker.patch('app.controllers.card_effects.early_train_to_paddington.get_new_discarded_order', return_value=10)
    mocker.patch('app.controllers.card_effects.early_train_to_paddington.not_so_fast_status', return_value=False)
    mocker.patch('app.controllers.card_effects.early_train_to_paddington.ChatService.create')

    asyncio.run(early_train_to_paddington(card=fake_card, session=None,in_discard=True))

    assert mock_card_search.call_count == 1
    assert mock_card_update.await_count == 7
    mock_card_delete.assert_awaited_once()
