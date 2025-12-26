import asyncio
from unittest.mock import AsyncMock, ANY, call

import pytest
from conftest import CardFactory, UpdateCardDTOFactory, PlayerFactory
from requests import session
from fastapi import HTTPException

from app.controllers.card_effects.look_into_the_ashes import look_into_the_ashes
from app.models.card import PublicCard, CardType
from app.models.detective_set import DetectiveSet
from app.models.game import GameStatus
from app.models.secret import Secret, SecretType
from app.services.card import CardFilter
from tests.conftest import GameFactory

def test_look_into_the_ashes_requires_discarded_cards(mocker):
    fake_game = GameFactory(status=GameStatus.TURN_START)
    fake_card = CardFactory(game_id=fake_game.id, owner=1)
    fake_player = PlayerFactory(id=fake_card.owner, game_id=fake_game.id)

    mocker.patch('app.controllers.card_effects.look_into_the_ashes.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.CardService.search', return_value=[])
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.PlayerService.read', return_value=fake_player)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(look_into_the_ashes(fake_card, None))

    assert exc_info.value.status_code == 412
    assert exc_info.value.detail == "No hay cartas en la pila de descarte, no se puede jugar"


def test_look_into_the_ashes_initial_play_sets_waiting_state(mocker):
    fake_game = GameFactory(status=GameStatus.TURN_START, current_turn=3)
    fake_player = PlayerFactory(game_id=fake_game.id)
    fake_card = CardFactory(game_id=fake_game.id, owner=fake_player.id, turn_played=None)
    last_discards = CardFactory.create_batch(size=3, game_id=fake_game.id)

    mocker.patch('app.controllers.card_effects.look_into_the_ashes.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.CardService.search', return_value=last_discards)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.PlayerService.read', return_value=fake_player)
    mock_card_update = mocker.patch('app.controllers.card_effects.look_into_the_ashes.CardService.update', new_callable=AsyncMock)
    mock_game_update = mocker.patch('app.controllers.card_effects.look_into_the_ashes.GameService.update', new_callable=AsyncMock)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.not_so_fast_status', return_value=False)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.ChatService.create')

    asyncio.run(look_into_the_ashes(fake_card, None, [], [], [], []))

    mock_card_update.assert_called_once()
    mock_game_update.assert_called_once()


def test_look_into_the_ashes_canceled_by_not_so_fast(mocker):
    fake_game = GameFactory(status=GameStatus.TURN_START, current_turn=4)
    fake_player = PlayerFactory(game_id=fake_game.id)
    fake_card = CardFactory(game_id=fake_game.id, owner=fake_player.id, turn_played=None)
    last_discards = CardFactory.create_batch(size=2, game_id=fake_game.id)

    mocker.patch('app.controllers.card_effects.look_into_the_ashes.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.CardService.search', return_value=last_discards)
    mock_card_update = mocker.patch('app.controllers.card_effects.look_into_the_ashes.CardService.update', new_callable=AsyncMock)
    mock_game_update = mocker.patch('app.controllers.card_effects.look_into_the_ashes.GameService.update', new_callable=AsyncMock)
    mock_get_order = mocker.patch('app.controllers.card_effects.look_into_the_ashes.get_new_discarded_order', return_value=18)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.not_so_fast_status', return_value=True)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.ChatService.create')

    asyncio.run(look_into_the_ashes(fake_card, None, [], [], [], []))

    mock_card_search = mocker.patch('app.controllers.card_effects.delay_the_murderers_escape.CardService.search')
    mock_game_update.assert_awaited_once_with(
        session=None,
        oid=fake_game.id,
        data={'status': GameStatus.FINALIZE_TURN, 'player_in_action': None},
    )
    mock_get_order.assert_called_once()


def test_look_into_the_ashes_requires_last_five_card(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_DISCARDED, current_turn=4)
    fake_player = PlayerFactory(game_id=fake_game.id)
    fake_card = CardFactory(game_id=fake_game.id, owner=fake_player.id, turn_played=fake_game.current_turn)
    last_discards = CardFactory.create_batch(size=2, game_id=fake_game.id)
    target_card = CardFactory(game_id=fake_game.id)

    mocker.patch('app.controllers.card_effects.look_into_the_ashes.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.CardService.search', return_value=last_discards)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.CardService.read', return_value=target_card)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.not_so_fast_status', return_value=False)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(look_into_the_ashes(fake_card, None, [], [], [target_card.id], []))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Solo se puede agarrar una de las 5 ultimas descartadas"


def test_look_into_the_ashes_requires_single_target(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_DISCARDED, current_turn=5)
    fake_player = PlayerFactory(game_id=fake_game.id)
    fake_card = CardFactory(game_id=fake_game.id, owner=fake_player.id, turn_played=fake_game.current_turn)
    last_discards = CardFactory.create_batch(size=5, game_id=fake_game.id)

    mocker.patch('app.controllers.card_effects.look_into_the_ashes.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.CardService.search', return_value=last_discards)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.not_so_fast_status', return_value=False)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(look_into_the_ashes(fake_card, None, [], [], [], []))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Cantidad erronea de cartas objetivos"


def test_look_into_the_ashes_requires_same_turn(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_DISCARDED, current_turn=6)
    fake_player = PlayerFactory(game_id=fake_game.id)
    fake_card = CardFactory(game_id=fake_game.id, owner=fake_player.id, turn_played=fake_game.current_turn - 1)
    last_discards = CardFactory.create_batch(size=3, game_id=fake_game.id)
    target_card = CardFactory(id=88, game_id=fake_game.id)

    mocker.patch('app.controllers.card_effects.look_into_the_ashes.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.CardService.search', return_value=last_discards)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.CardService.read', return_value=target_card)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.not_so_fast_status', return_value=False)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(look_into_the_ashes(fake_card, None, [], [], [target_card.id], []))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "No se puede relanzar una carta jugada"


def test_look_into_the_ashes_target_card_not_found(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_DISCARDED, current_turn=8)
    fake_player = PlayerFactory(game_id=fake_game.id)
    fake_card = CardFactory(game_id=fake_game.id, owner=fake_player.id, turn_played=fake_game.current_turn)
    last_discards = CardFactory.create_batch(size=4, game_id=fake_game.id)

    mocker.patch('app.controllers.card_effects.look_into_the_ashes.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.CardService.search', return_value=last_discards)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.CardService.read', return_value=None)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.not_so_fast_status', return_value=False)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(look_into_the_ashes(fake_card, None, [], [], [123], []))

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Carta objetivo no existente"


def test_look_into_the_ashes_target_card_wrong_game(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_DISCARDED, current_turn=7)
    fake_player = PlayerFactory(game_id=fake_game.id)
    fake_card = CardFactory(game_id=fake_game.id, owner=fake_player.id, turn_played=fake_game.current_turn)
    last_discards = CardFactory.create_batch(size=4, game_id=fake_game.id)
    other_game_card = CardFactory(game_id=fake_game.id + 1)

    mocker.patch('app.controllers.card_effects.look_into_the_ashes.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.CardService.search', return_value=last_discards)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.CardService.read', return_value=other_game_card)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.not_so_fast_status', return_value=False)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(look_into_the_ashes(fake_card, None, [], [], [other_game_card.id], []))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Carta no existente en esta partida"


def test_look_into_the_ashes_successful_recovery(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_DISCARDED, current_turn=9)
    fake_player = PlayerFactory(game_id=fake_game.id)
    fake_card = CardFactory(game_id=fake_game.id, owner=fake_player.id, turn_played=fake_game.current_turn)
    target_card = CardFactory(game_id=fake_game.id)
    last_discards = [CardFactory(game_id=fake_game.id) for _ in range(3)] + [target_card]

    mocker.patch('app.controllers.card_effects.look_into_the_ashes.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.CardService.search', return_value=last_discards)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.CardService.read', return_value=target_card)
    mock_get_last = mocker.patch('app.controllers.card_effects.look_into_the_ashes.get_new_discarded_order', return_value=30)
    mock_card_update = mocker.patch('app.controllers.card_effects.look_into_the_ashes.CardService.update', new_callable=AsyncMock)
    mock_game_update = mocker.patch('app.controllers.card_effects.look_into_the_ashes.GameService.update', new_callable=AsyncMock)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.not_so_fast_status', return_value=False)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.ChatService.create')

    asyncio.run(look_into_the_ashes(fake_card, None, [], [], [target_card.id], []))

    expected_calls = [
        call(session=None, oid=target_card.id, data={'turn_discarded': None, 'discarded_order': None,"content":"",'owner': fake_player.id, "turn_played":None}),
        call(session=None, oid=fake_card.id, data={'turn_discarded': fake_game.current_turn, 'discarded_order': mock_get_last.return_value, 'owner': None}),
    ]
    assert mock_card_update.await_args_list == expected_calls
    mock_game_update.assert_called_once()


def test_look_into_the_ashes_disallowed_status(mocker):
    fake_game = GameFactory(status=GameStatus.FINALIZED, current_turn=10)
    fake_player = PlayerFactory(game_id=fake_game.id)
    fake_card = CardFactory(game_id=fake_game.id, owner=fake_player.id, turn_played=None)
    last_discards = CardFactory.create_batch(size=2, game_id=fake_game.id)

    mocker.patch('app.controllers.card_effects.look_into_the_ashes.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.CardService.search', return_value=last_discards)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card_effects.look_into_the_ashes.not_so_fast_status', return_value=False)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(look_into_the_ashes(fake_card, None, [], [], [], []))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Ya no se puede jugar eventos"
