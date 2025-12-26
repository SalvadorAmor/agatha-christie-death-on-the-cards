import asyncio
from unittest.mock import AsyncMock, ANY, call

import pytest
from conftest import CardFactory, UpdateCardDTOFactory, PlayerFactory
from requests import session
from fastapi import HTTPException

from app.controllers.card_effects.cards_off_the_table import cards_off_the_table
from app.models.card import PublicCard, CardType
from app.models.detective_set import DetectiveSet
from app.models.game import GameStatus
from app.models.secret import Secret, SecretType
from app.services.card import CardFilter
from tests.conftest import GameFactory

def test_cards_off_the_table_initial_play(mocker):
    fake_game = GameFactory(status=GameStatus.TURN_START, current_turn=3)
    fake_player = PlayerFactory(game_id=fake_game.id)
    fake_card = CardFactory(game_id=fake_game.id, turn_played=None,owner = fake_player.id)

    mock_game_read = mocker.patch('app.controllers.card_effects.cards_off_the_table.GameService.read', return_value=fake_game)
    mock_card_update = mocker.patch('app.controllers.card_effects.cards_off_the_table.CardService.update', new_callable=AsyncMock)
    mock_game_update = mocker.patch('app.controllers.card_effects.cards_off_the_table.GameService.update', new_callable=AsyncMock)
    mock_player_read = mocker.patch('app.controllers.card_effects.cards_off_the_table.PlayerService.read', return_value = fake_player)
    mocker.patch('app.controllers.card_effects.cards_off_the_table.ChatService.create')

    asyncio.run(cards_off_the_table(card=fake_card, session=None, target_players=[]))

    mock_game_read.assert_called_once_with(session=None, oid=fake_card.game_id)
    mock_card_update.assert_called_once()
    mock_game_update.assert_called_once()


def test_cards_off_the_table_requires_single_target_player(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_PLAYER, current_turn=4)
    fake_card = CardFactory(game_id=fake_game.id, turn_played=4)

    mocker.patch('app.controllers.card_effects.cards_off_the_table.GameService.read', return_value=fake_game)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(cards_off_the_table(card=fake_card, session=None, target_players=[]))

    assert exc_info.value.status_code == 400
    assert "Cantidad erronea" in exc_info.value.detail


def test_cards_off_the_table_same_turn_required(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_PLAYER, current_turn=6)
    fake_card = CardFactory(game_id=fake_game.id, turn_played=5)

    mocker.patch('app.controllers.card_effects.cards_off_the_table.GameService.read', return_value=fake_game)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(cards_off_the_table(card=fake_card, session=None, target_players=[1]))

    assert exc_info.value.status_code == 400
    assert "No se puede relanzar una carta jugada" in exc_info.value.detail


def test_cards_off_the_table_target_player_not_found(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_PLAYER, current_turn=2)
    fake_card = CardFactory(game_id=fake_game.id, turn_played=2)

    mocker.patch('app.controllers.card_effects.cards_off_the_table.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.cards_off_the_table.PlayerService.read', return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(cards_off_the_table(card=fake_card, session=None, target_players=[123]))

    assert exc_info.value.status_code == 404
    assert "Jugador objetivo no existente" in exc_info.value.detail


def test_cards_off_the_table_target_player_wrong_game(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_PLAYER, current_turn=7)
    fake_card = CardFactory(game_id=fake_game.id, turn_played=7)
    other_game_id = fake_game.id + 1
    target_player = PlayerFactory(id=42, game_id=other_game_id)

    mocker.patch('app.controllers.card_effects.cards_off_the_table.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.cards_off_the_table.PlayerService.read', return_value=target_player)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(cards_off_the_table(card=fake_card, session=None, target_players=[target_player.id]))

    assert exc_info.value.status_code == 400
    assert "Jugador no existente en esta partida" in exc_info.value.detail

def test_cards_off_the_table_finished_turn(mocker):
    fake_game = GameFactory(status=GameStatus.FINALIZE_TURN, current_turn=7)
    fake_card = CardFactory(game_id=fake_game.id, turn_played=7)

    mocker.patch('app.controllers.card_effects.cards_off_the_table.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.cards_off_the_table.ChatService.create')

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(cards_off_the_table(card=fake_card, session=None, target_players=[]))

    assert exc_info.value.status_code == 400
    assert "Ya no se puede jugar eventos" in exc_info.value.detail


def test_cards_off_the_table_discards_not_so_fast_cards(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_PLAYER, current_turn=9)
    fake_card = CardFactory(game_id=fake_game.id, turn_played=9, id=15)
    target_player = PlayerFactory(game_id=fake_game.id)
    not_so_fast_cards = [
        CardFactory(id=301, game_id=fake_game.id, owner=target_player.id, name="not-so-fast"),
        CardFactory(id=302, game_id=fake_game.id, owner=target_player.id, name="not-so-fast"),
    ]

    mocker.patch('app.controllers.card_effects.cards_off_the_table.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.cards_off_the_table.PlayerService.read', return_value=target_player)
    mock_card_search = mocker.patch('app.controllers.card_effects.cards_off_the_table.CardService.search', return_value=not_so_fast_cards)
    mock_get_last = mocker.patch('app.controllers.card_effects.cards_off_the_table.get_new_discarded_order', side_effect=[20, 30])
    mock_card_update = mocker.patch('app.controllers.card_effects.cards_off_the_table.CardService.update', new_callable=AsyncMock)
    mock_game_update = mocker.patch('app.controllers.card_effects.cards_off_the_table.GameService.update', new_callable=AsyncMock)
    mocker.patch('app.controllers.card_effects.cards_off_the_table.ChatService.create')

    asyncio.run(cards_off_the_table(card=fake_card, session=None, target_players=[target_player.id]))

    mock_card_search.assert_called_once_with(session=None, filterby={'owner__eq': target_player.id, 'name__eq': 'not-so-fast'})
    assert mock_get_last.call_count == 2

    awaited_calls = mock_card_update.await_args_list
    assert len(awaited_calls) == len(not_so_fast_cards) + 1

    mock_game_update.assert_called_once()

