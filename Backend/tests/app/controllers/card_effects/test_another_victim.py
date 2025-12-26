import asyncio
from unittest.mock import AsyncMock, ANY, call

import pytest
from conftest import CardFactory, UpdateCardDTOFactory, PlayerFactory
from requests import session
from fastapi import HTTPException

from app.controllers.card_effects.another_victim import another_victim
from app.models.card import PublicCard, CardType
from app.models.detective_set import DetectiveSet
from app.models.game import GameStatus
from app.models.secret import Secret, SecretType
from app.services.card import CardFilter
from tests.conftest import GameFactory

def test_another_victim_initial_play_sets_waiting_state(mocker):
    fake_game = GameFactory(status=GameStatus.TURN_START, current_turn=5)
    fake_card = CardFactory(game_id=fake_game.id, owner=25, turn_played=None)
    fake_player = PlayerFactory(game_id = fake_game.id, id = fake_card.owner)

    mocker.patch('app.controllers.card_effects.another_victim.GameService.read', return_value=fake_game)
    mocker.patch(
        'app.controllers.card_effects.another_victim.DetectiveSetService.search',
        return_value=[
            DetectiveSet(id=1, owner=fake_card.owner, game_id=fake_game.id, turn_played=0, detectives=[]),
            DetectiveSet(id=2, owner=fake_card.owner + 1, game_id=fake_game.id, turn_played=0, detectives=[]),
        ],
    )
    mock_card_update = mocker.patch('app.controllers.card_effects.another_victim.CardService.update', new_callable=AsyncMock)
    mock_game_update = mocker.patch('app.controllers.card_effects.another_victim.GameService.update', new_callable=AsyncMock)
    mocker.patch('app.controllers.card_effects.another_victim.not_so_fast_status', return_value=False)
    mocker.patch('app.controllers.card_effects.another_victim.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card_effects.another_victim.ChatService.create')

    asyncio.run(another_victim(fake_card, None, [], [], [], []))

    mock_card_update.assert_awaited_once_with(
        session=None, oid=fake_card.id, data={'turn_played': fake_game.current_turn}
    )
    mock_game_update.assert_awaited_once_with(
        session=None,
        oid=fake_game.id,
        data={'status': GameStatus.WAITING_FOR_CHOOSE_SET, 'player_in_action': fake_card.owner},
    )


def test_another_victim_initial_play_without_targets_finishes_turn(mocker):
    fake_game = GameFactory(status=GameStatus.TURN_START, current_turn=4)
    fake_card = CardFactory(game_id=fake_game.id, owner=40, turn_played=None)
    fake_player = PlayerFactory(game_id = fake_game.id, id = fake_card.owner)

    mocker.patch('app.controllers.card_effects.another_victim.GameService.read', return_value=fake_game)
    mocker.patch(
        'app.controllers.card_effects.another_victim.DetectiveSetService.search',
        return_value=[
            DetectiveSet(id=1, owner=fake_card.owner, game_id=fake_game.id, turn_played=0, detectives=[]),
        ],
    )
    mock_get_order = mocker.patch('app.controllers.card_effects.another_victim.get_new_discarded_order', return_value=22)
    mock_card_update = mocker.patch('app.controllers.card_effects.another_victim.CardService.update', new_callable=AsyncMock)
    mock_game_update = mocker.patch('app.controllers.card_effects.another_victim.GameService.update', new_callable=AsyncMock)
    mocker.patch('app.controllers.card_effects.another_victim.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card_effects.another_victim.ChatService.create')

    asyncio.run(another_victim(fake_card, None, [], [], [], []))

    mock_get_order.assert_called_once_with(session=None, game_id=fake_game.id)
    mock_card_update.assert_awaited_once_with(
        session=None,
        oid=fake_card.id,
        data={'owner': None, 'turn_discarded': fake_game.current_turn, 'discarded_order': mock_get_order.return_value},
    )
    mock_game_update.assert_awaited_once_with(
        session=None,
        oid=fake_game.id,
        data={'status': GameStatus.FINALIZE_TURN, 'player_in_action': None},
    )


def test_another_victim_canceled_by_not_so_fast(mocker):
    fake_game = GameFactory(status=GameStatus.TURN_START, current_turn=6)
    fake_card = CardFactory(game_id=fake_game.id, owner=41, turn_played=None)
    other_set = DetectiveSet(id=3, owner=fake_card.owner + 1, game_id=fake_game.id, turn_played=0, detectives=[])
    fake_player = PlayerFactory(game_id = fake_game.id, id = fake_card.owner)

    mocker.patch('app.controllers.card_effects.another_victim.GameService.read', return_value=fake_game)
    mocker.patch(
        'app.controllers.card_effects.another_victim.DetectiveSetService.search',
        return_value=[
            DetectiveSet(id=2, owner=fake_card.owner, game_id=fake_game.id, turn_played=0, detectives=[]),
            other_set,
        ],
    )
    mock_card_update = mocker.patch('app.controllers.card_effects.another_victim.CardService.update', new_callable=AsyncMock)
    mock_game_update = mocker.patch('app.controllers.card_effects.another_victim.GameService.update', new_callable=AsyncMock)
    mock_get_order = mocker.patch('app.controllers.card_effects.another_victim.get_new_discarded_order', return_value=31)
    mocker.patch('app.controllers.card_effects.another_victim.not_so_fast_status', return_value=True)
    mocker.patch('app.controllers.card_effects.another_victim.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card_effects.another_victim.ChatService.create')


    asyncio.run(another_victim(fake_card, None, [], [], [], []))

    assert len(mock_card_update.mock_calls) == 2
    mock_game_update.assert_awaited_once()
    mock_get_order.assert_called_once_with(session=None, game_id=fake_game.id)


def test_another_victim_requires_target_set(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_SET, current_turn=6)
    fake_card = CardFactory(game_id=fake_game.id, owner=26, turn_played=fake_game.current_turn)
    fake_player = PlayerFactory(game_id = fake_game.id, id = fake_card.owner)


    mocker.patch('app.controllers.card_effects.another_victim.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.another_victim.PlayerService.read', return_value=fake_player)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(another_victim(fake_card, None, [], [], [], []))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "No fue seleccionado el set a robar"


def test_another_victim_set_not_found(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_SET, current_turn=7)
    fake_card = CardFactory(game_id=fake_game.id, owner=27, turn_played=fake_game.current_turn)
    fake_player = PlayerFactory(game_id = fake_game.id, id = fake_card.owner)

    mocker.patch('app.controllers.card_effects.another_victim.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.another_victim.DetectiveSetService.read', new_callable=AsyncMock, return_value=None)
    mocker.patch('app.controllers.card_effects.another_victim.PlayerService.read', return_value=fake_player)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(another_victim(fake_card, None, [], [], [], [11]))

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "No se encontro el set a robar"


def test_another_victim_set_from_other_game(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_SET, current_turn=8)
    fake_card = CardFactory(game_id=fake_game.id, owner=28, turn_played=fake_game.current_turn)
    stolen_set = DetectiveSet(id=fake_game.id + 99, owner=30, game_id=fake_game.id + 1, turn_played=2, detectives=[])
    fake_player = PlayerFactory(game_id = fake_game.id, id = fake_card.owner)

    mocker.patch('app.controllers.card_effects.another_victim.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.another_victim.DetectiveSetService.read', new_callable=AsyncMock, return_value=stolen_set)
    mocker.patch('app.controllers.card_effects.another_victim.PlayerService.read', return_value=fake_player)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(another_victim(fake_card, None, [], [], [], [stolen_set.id]))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "El set seleccionado no se encuentra en esta partida"


def test_another_victim_set_of_your_own(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_SET, current_turn=8)
    fake_card = CardFactory(game_id=fake_game.id, owner=30, turn_played=fake_game.current_turn)
    stolen_set = DetectiveSet(id=fake_game.id, owner=30, game_id=fake_game.id, turn_played=2, detectives=[])
    fake_player = PlayerFactory(game_id = fake_game.id, id = fake_card.owner)

    mocker.patch('app.controllers.card_effects.another_victim.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.another_victim.DetectiveSetService.read', new_callable=AsyncMock, return_value=stolen_set)
    mocker.patch('app.controllers.card_effects.another_victim.PlayerService.read', return_value=fake_player)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(another_victim(fake_card, None, [], [], [], [stolen_set.id]))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "No se puede robar un set propio"


def test_another_victim_ok(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_SET, current_turn=9)
    fake_card = CardFactory(game_id=fake_game.id, owner=29, turn_played=fake_game.current_turn)
    fake_detective = CardFactory(game_id = fake_game.id, owner = 29, card_type=CardType.DETECTIVE)
    stolen_set = DetectiveSet(id=fake_game.id, owner=31, game_id=fake_game.id, turn_played=3, detectives=[fake_detective])
    fake_player = PlayerFactory(game_id = fake_game.id, id = fake_card.owner)

    mocker.patch('app.controllers.card_effects.another_victim.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.another_victim.CardService.update', return_value=fake_card)
    mocker.patch('app.controllers.card_effects.another_victim.get_new_discarded_order', return_value=10)
    mocker.patch('app.controllers.card_effects.another_victim.DetectiveSetService.read', new_callable=AsyncMock, return_value=stolen_set)
    mocker.patch('app.controllers.card_effects.another_victim.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card_effects.another_victim.ChatService.create')
    mock_set_update = mocker.patch('app.controllers.card_effects.another_victim.DetectiveSetService.update', new_callable=AsyncMock)
    mock_status = mocker.patch('app.controllers.card_effects.another_victim.set_next_game_status', return_value=GameStatus.WAITING_FOR_CHOOSE_SECRET)
    mock_game_update = mocker.patch('app.controllers.card_effects.another_victim.GameService.update', new_callable=AsyncMock)

    asyncio.run(another_victim(fake_card, None, [], [], [], [stolen_set.id]))

    mock_set_update.assert_awaited_once()
    mock_status.assert_called_once()
    mock_game_update.assert_awaited_once()


def test_another_victim_disallowed_status(mocker):
    fake_game = GameFactory(status=GameStatus.FINALIZE_TURN, current_turn=10)
    fake_card = CardFactory(game_id=fake_game.id, owner=34, turn_played=None)
    fake_player = PlayerFactory(game_id = fake_game.id, id = fake_card.owner)

    mocker.patch('app.controllers.card_effects.another_victim.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.another_victim.PlayerService.read', return_value=fake_player)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(another_victim(fake_card, None, [], [], [], []))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Ya no se puede jugar eventos"
