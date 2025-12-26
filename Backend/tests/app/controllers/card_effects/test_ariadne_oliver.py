import asyncio
from unittest.mock import AsyncMock, call

import pytest
from fastapi import HTTPException

from app.controllers.card_effects.ariadne_oliver import ariadne_oliver
from app.models.detective_set import DetectiveSet
from app.models.game import GameStatus
from tests.conftest import CardFactory, GameFactory, PlayerFactory


def test_ariadne_oliver_requires_other_sets(mocker):
    fake_game = GameFactory(status=GameStatus.TURN_START, current_turn=3)
    fake_card = CardFactory(game_id=fake_game.id, owner=42, turn_played=None)
    fake_player = PlayerFactory(id = fake_card.owner, game_id = fake_game.id)

    mocker.patch('app.controllers.card_effects.ariadne_oliver.GameService.read', return_value=fake_game)
    mocker.patch(
        'app.controllers.card_effects.ariadne_oliver.DetectiveSetService.search',
        return_value=[DetectiveSet(id=1, owner=fake_card.owner, game_id=fake_game.id, turn_played=1, detectives=[])],
    )
    mocker.patch('app.controllers.card_effects.ariadne_oliver.PlayerService.read', return_value = fake_player)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(ariadne_oliver(fake_card, None, [], [], [], []))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "No se puede jugar el set Ariadne Oliver: No hay sets para agregarse"


def test_ariadne_oliver_initial_play_updates_state(mocker):
    fake_game = GameFactory(status=GameStatus.TURN_START, current_turn=5)
    fake_card = CardFactory(game_id=fake_game.id, owner=50, turn_played=None)
    opponent_set = DetectiveSet(id=2, owner=fake_card.owner + 1, game_id=fake_game.id, turn_played=0, detectives=[])
    fake_player = PlayerFactory(id = fake_card.owner, game_id = fake_game.id)

    mocker.patch('app.controllers.card_effects.ariadne_oliver.GameService.read', return_value=fake_game)
    mocker.patch(
        'app.controllers.card_effects.ariadne_oliver.DetectiveSetService.search',
        return_value=[opponent_set],
    )
    mock_card_update = mocker.patch('app.controllers.card_effects.ariadne_oliver.CardService.update', new_callable=AsyncMock)
    mock_game_update = mocker.patch('app.controllers.card_effects.ariadne_oliver.GameService.update', new_callable=AsyncMock)
    mocker.patch('app.controllers.card_effects.ariadne_oliver.PlayerService.read', return_value = fake_player)
    mocker.patch('app.controllers.card_effects.ariadne_oliver.ChatService.create')
    mocker.patch('app.controllers.card_effects.ariadne_oliver.not_so_fast_status', return_value = False)

    asyncio.run(ariadne_oliver(fake_card, None, [], [], [], []))

    mock_card_update.assert_awaited_once_with(
        session=None,
        oid=fake_card.id,
        data={'turn_played': fake_game.current_turn},
    )
    mock_game_update.assert_awaited_once_with(
        session=None,
        oid=fake_game.id,
        data={'status': GameStatus.WAITING_FOR_CHOOSE_SET, 'player_in_action': fake_card.owner},
    )

def test_ariadne_oliver_canceled(mocker):
    fake_game = GameFactory(status=GameStatus.TURN_START, current_turn=5)
    fake_card = CardFactory(game_id=fake_game.id, owner=50, turn_played=None)
    opponent_set = DetectiveSet(id=2, owner=fake_card.owner + 1, game_id=fake_game.id, turn_played=0, detectives=[])
    fake_player = PlayerFactory(id = fake_card.owner, game_id = fake_game.id)

    mocker.patch('app.controllers.card_effects.ariadne_oliver.GameService.read', return_value=fake_game)
    mocker.patch(
        'app.controllers.card_effects.ariadne_oliver.DetectiveSetService.search',
        return_value=[opponent_set],
    )
    mock_card_update = mocker.patch('app.controllers.card_effects.ariadne_oliver.CardService.update', new_callable=AsyncMock)
    mock_game_update = mocker.patch('app.controllers.card_effects.ariadne_oliver.GameService.update', new_callable=AsyncMock)
    mocker.patch('app.controllers.card_effects.ariadne_oliver.PlayerService.read', return_value = fake_player)
    mocker.patch('app.controllers.card_effects.ariadne_oliver.ChatService.create')
    mocker.patch('app.controllers.card_effects.ariadne_oliver.not_so_fast_status', return_value = True)
    mock_get_new_discarded_order = mocker.patch(
        'app.controllers.card_effects.ariadne_oliver.get_new_discarded_order',
        return_value=77,
    )

    result = asyncio.run(ariadne_oliver(fake_card, None, [], [], [], []))

    assert result == 200
    mock_card_update.assert_has_awaits(
        [
            call(session=None, oid=fake_card.id, data={'turn_played': fake_game.current_turn}),
            call(
                session=None,
                oid=fake_card.id,
                data={
                    'turn_discarded': fake_game.current_turn,
                    'discarded_order': mock_get_new_discarded_order.return_value,
                    'owner': None,
                },
            ),
        ],
    )
    mock_get_new_discarded_order.assert_called_once_with(session=None, game_id=fake_game.id)
    mock_game_update.assert_awaited_once_with(
        session=None,
        oid=fake_game.id,
        data={'status': GameStatus.FINALIZE_TURN, 'player_in_action': None},
    )


def test_ariadne_oliver_second_phase_requires_target_set(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_SET, current_turn=6)
    fake_card = CardFactory(game_id=fake_game.id, owner=60, turn_played=fake_game.current_turn)
    fake_player = PlayerFactory(id = fake_card.owner, game_id = fake_game.id)

    mocker.patch('app.controllers.card_effects.ariadne_oliver.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.ariadne_oliver.PlayerService.read', return_value = fake_player)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(ariadne_oliver(fake_card, None, [], [], [], []))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "No fue seleccionado el set a robar"


def test_ariadne_oliver_second_phase_set_not_found(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_SET, current_turn=7)
    fake_card = CardFactory(game_id=fake_game.id, owner=70, turn_played=fake_game.current_turn)
    fake_player = PlayerFactory(id = fake_card.owner, game_id = fake_game.id)

    mocker.patch('app.controllers.card_effects.ariadne_oliver.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.ariadne_oliver.PlayerService.read', return_value = fake_player)
    mocker.patch(
        'app.controllers.card_effects.ariadne_oliver.DetectiveSetService.read',
        new_callable=AsyncMock,
        return_value=None,
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(ariadne_oliver(fake_card, None, [], [], [], [999]))

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "No se encontro el set a robar"


def test_ariadne_oliver_second_phase_other_game(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_SET, current_turn=8)
    fake_card = CardFactory(game_id=fake_game.id, owner=80, turn_played=fake_game.current_turn)
    foreign_set = DetectiveSet(id=4, owner=90, game_id=fake_game.id + 1, turn_played=0, detectives=[])
    fake_player = PlayerFactory(id = fake_card.owner, game_id = fake_game.id)

    mocker.patch('app.controllers.card_effects.ariadne_oliver.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.ariadne_oliver.PlayerService.read', return_value = fake_player)
    mocker.patch(
        'app.controllers.card_effects.ariadne_oliver.DetectiveSetService.read',
        new_callable=AsyncMock,
        return_value=foreign_set,
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(ariadne_oliver(fake_card, None, [], [], [], [foreign_set.id]))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "El set seleccionado no se encuentra en esta partida"


def test_ariadne_oliver_second_phase_ok(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_SET, current_turn=9)
    fake_card = CardFactory(game_id=fake_game.id, owner=90, turn_played=fake_game.current_turn)
    fake_detective = CardFactory(game_id = fake_game.id, card_type = "detective")
    stolen_set = DetectiveSet(id=5, owner=33, game_id=fake_game.id, turn_played=0, detectives=[fake_detective])
    fake_player = PlayerFactory(id = fake_card.owner, game_id = fake_game.id)

    mocker.patch('app.controllers.card_effects.ariadne_oliver.GameService.read', return_value=fake_game)
    mocker.patch(
        'app.controllers.card_effects.ariadne_oliver.DetectiveSetService.read',
        new_callable=AsyncMock,
        return_value=stolen_set,
    )
    mock_set_update = mocker.patch(
        'app.controllers.card_effects.ariadne_oliver.DetectiveSetService.update',
        new_callable=AsyncMock,
        return_value=stolen_set,
    )
    mock_game_update = mocker.patch('app.controllers.card_effects.ariadne_oliver.GameService.update', new_callable=AsyncMock)
    mocker.patch('app.controllers.card_effects.ariadne_oliver.PlayerService.read', return_value = fake_player)
    mocker.patch('app.controllers.card_effects.ariadne_oliver.ChatService.create')

    asyncio.run(ariadne_oliver(fake_card, None, [], [], [], [stolen_set.id]))

    mock_set_update.assert_awaited_once_with(
        session=None,
        data={'turn_played': fake_game.current_turn, 'detectives': fake_card},
        id=stolen_set.id,
    )
    mock_game_update.assert_awaited_once_with(
        session=None,
        oid=fake_game.id,
        data={'status': GameStatus.WAITING_FOR_CHOOSE_SECRET, 'player_in_action': stolen_set.owner},
    )


def test_ariadne_oliver_invalid_state(mocker):
    fake_game = GameFactory(status=GameStatus.FINALIZE_TURN, current_turn=10)
    fake_card = CardFactory(game_id=fake_game.id, owner=99, turn_played=None)
    fake_player = PlayerFactory(id = fake_card.owner, game_id = fake_game.id)

    mocker.patch('app.controllers.card_effects.ariadne_oliver.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.ariadne_oliver.PlayerService.read', return_value = fake_player)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(ariadne_oliver(fake_card, None, [], [], [], []))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "No se puede bajar el set Ariadne Oliver"
