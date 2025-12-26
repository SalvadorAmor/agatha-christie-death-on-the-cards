import asyncio
from unittest.mock import AsyncMock, ANY, call

import pytest
from conftest import CardFactory, UpdateCardDTOFactory, PlayerFactory
from requests import session
from fastapi import HTTPException

from app.controllers.card_effects.and_then_there_was_one_more import and_then_there_was_one_more
from app.models.card import PublicCard, CardType
from app.models.detective_set import DetectiveSet
from app.models.game import GameStatus
from app.models.secret import Secret, SecretType
from app.services.card import CardFilter
from tests.conftest import GameFactory

def test_and_then_there_was_one_more_initial_play_sets_waiting_state(mocker):
    fake_game = GameFactory(status=GameStatus.TURN_START, current_turn=4)
    fake_card = CardFactory(game_id=fake_game.id, owner=11, turn_played=None)
    fake_secret = Secret(id=1, game_id=fake_game.id, owner=2, name="secret", content="", type=SecretType.OTHER)
    fake_player = PlayerFactory(id=fake_card.owner, game_id = fake_game.id)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.GameService.read', return_value=fake_game)
    mock_card_update = mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.CardService.update', new_callable=AsyncMock)
    mock_game_update = mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.GameService.update', new_callable=AsyncMock)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.SecretService.search', return_value=[fake_secret])
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.not_so_fast_status', return_value=False)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.ChatService.create')

    asyncio.run(and_then_there_was_one_more(fake_card, None, [], [], [], []))

    mock_card_update.assert_awaited_once_with(
        session=None, oid=fake_card.id, data={'turn_played': fake_game.current_turn}
    )
    mock_game_update.assert_awaited_once_with(
        session=None,
        oid=fake_game.id,
        data={'status': GameStatus.WAITING_FOR_CHOOSE_PLAYER_AND_SECRET, 'player_in_action': fake_card.owner},
    )


def test_and_then_there_was_one_more_canceled_by_not_so_fast(mocker):
    fake_game = GameFactory(status=GameStatus.TURN_START, current_turn=5)
    fake_card = CardFactory(game_id=fake_game.id, owner=10, turn_played=None)
    fake_player = PlayerFactory(id=fake_card.owner, game_id = fake_game.id)

    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.GameService.read', return_value=fake_game)
    mock_card_update = mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.CardService.update', new_callable=AsyncMock)
    mock_game_update = mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.GameService.update', new_callable=AsyncMock)
    mock_get_order = mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.get_new_discarded_order', return_value=42)
    mock_secret_search = mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.SecretService.search')
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.not_so_fast_status', return_value=True)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.ChatService.create')

    asyncio.run(and_then_there_was_one_more(fake_card, None, [], [], [], []))

    assert len(mock_card_update.mock_calls) == 2
    mock_game_update.assert_awaited_once()
    mock_secret_search.assert_called_once_with(session=None, filterby={"game_id__eq": fake_game.id, "revealed__eq": True})


def test_and_then_there_was_one_more_requires_secret_selection(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_PLAYER_AND_SECRET, current_turn=6)
    fake_card = CardFactory(game_id=fake_game.id, owner=12, turn_played=fake_game.current_turn)
    fake_player = PlayerFactory(id=fake_card.owner, game_id = fake_game.id)

    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.GameService.read', return_value=fake_game)
    mock_secret_read = mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.SecretService.read')
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.ChatService.create')


    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(and_then_there_was_one_more(fake_card, None, [1], [], [], []))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Se debe mandar un secreto a revelar"
    mock_secret_read.assert_not_called()


def test_and_then_there_was_one_more_requires_target_player(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_PLAYER_AND_SECRET, current_turn=7)
    fake_card = CardFactory(game_id=fake_game.id, owner=13, turn_played=fake_game.current_turn)
    fake_player = PlayerFactory(id=fake_card.owner, game_id = fake_game.id)

    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.GameService.read', return_value=fake_game)
    mock_secret_read = mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.SecretService.read')
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.ChatService.create')

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(and_then_there_was_one_more(fake_card, None, [], [2], [], []))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Se debe mandar un jugador objetivo"
    mock_secret_read.assert_not_called()


def test_and_then_there_was_one_more_secret_not_found(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_PLAYER_AND_SECRET, current_turn=8)
    fake_card = CardFactory(game_id=fake_game.id, owner=14, turn_played=fake_game.current_turn)
    fake_secret= Secret(id=1,game_id=fake_game.id,owner=2,name="secret",content="",type=SecretType.OTHER)
    fake_player = PlayerFactory(id=fake_card.owner, game_id = fake_game.id)

    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.SecretService.read', return_value=None)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.SecretService.search', return_value=[fake_secret])
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.ChatService.create')

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(and_then_there_was_one_more(fake_card, None, [1], [3], [], []))

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Secreto no existente"

def test_and_then_there_was_one_more_secret_not_revealed_secrets(mocker):
    fake_game = GameFactory(status=GameStatus.TURN_START, current_turn=8)
    fake_card = CardFactory(game_id=fake_game.id, owner=14, turn_played=None)
    fake_secret = Secret(id=1, game_id=fake_game.id, owner=2, name="secret", content="", type=SecretType.OTHER)
    fake_player = PlayerFactory(id=fake_card.owner, game_id = fake_game.id)

    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.SecretService.read', return_value=None)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.SecretService.search', return_value=[])
    mock_secret_service=mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.GameService.update', return_value=fake_game)
    mock_get_last = mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.get_new_discarded_order', return_value=30)
    mock_card_update = mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.CardService.update')
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.not_so_fast_status', return_value=False)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.ChatService.create')

    asyncio.run(and_then_there_was_one_more(fake_card, None, [], [], [], []))

    mock_secret_service.assert_called_once()
    mock_get_last.assert_called_once()
    assert len(mock_card_update.mock_calls) == 2

def test_and_then_there_was_one_more_target_player_not_found(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_PLAYER_AND_SECRET, current_turn=9)
    fake_card = CardFactory(game_id=fake_game.id, owner=15, turn_played=fake_game.current_turn)
    target_secret = Secret(
        id=21,
        game_id=fake_game.id,
        owner=fake_card.owner,
        name="secreto",
        content="",
        revealed=True,
        type=SecretType.OTHER,
    )

    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.SecretService.read', return_value=target_secret)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.PlayerService.read', return_value=None)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.SecretService.search', return_value=[target_secret])


    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(and_then_there_was_one_more(fake_card, None, [1], [target_secret.id], [], []))

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Jugador objetivo no existente"


def test_and_then_there_was_one_more_rejects_secret_from_other_game(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_PLAYER_AND_SECRET, current_turn=10)
    fake_card = CardFactory(game_id=fake_game.id, owner=16, turn_played=fake_game.current_turn)
    fake_player = PlayerFactory(id=fake_card.owner, game_id = fake_game.id)
    target_player = PlayerFactory(game_id=fake_game.id)
    target_secret = Secret(
        id=22,
        game_id=fake_game.id + 1,
        owner=target_player.id,
        name="otro",
        content="",
        revealed=True,
        type=SecretType.OTHER,
    )

    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.SecretService.read', return_value=target_secret)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.PlayerService.read', return_value=target_player)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.SecretService.search', return_value=[target_secret])
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.ChatService.create')

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(and_then_there_was_one_more(fake_card, None, [target_player.id], [target_secret.id], [], []))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "No se puede robar un secreto de otra partida"


def test_and_then_there_was_one_more_rejects_hidden_secret(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_PLAYER_AND_SECRET, current_turn=11)
    fake_card = CardFactory(game_id=fake_game.id, owner=17, turn_played=fake_game.current_turn)
    fake_player = PlayerFactory(id=fake_card.owner, game_id = fake_game.id)
    target_player = PlayerFactory(game_id=fake_game.id)
    target_secret = Secret(
        id=23,
        game_id=fake_game.id,
        owner=target_player.id,
        name="oculto",
        content="",
        revealed=False,
        type=SecretType.OTHER,
    )

    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.SecretService.read', return_value=target_secret)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.PlayerService.read', return_value=target_player)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.SecretService.search', return_value=[target_secret])
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.PlayerService.read', return_value=fake_player)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.ChatService.create')

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(and_then_there_was_one_more(fake_card, None, [target_player.id], [target_secret.id], [], []))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "No se puede robar un secreto oculto"


def test_and_then_there_was_one_more_successful_theft(mocker):
    fake_game = GameFactory(status=GameStatus.WAITING_FOR_CHOOSE_PLAYER_AND_SECRET, current_turn=12)
    fake_card = CardFactory(game_id=fake_game.id, owner=18, turn_played=fake_game.current_turn)
    acting_player = PlayerFactory(id=fake_card.owner, game_id=fake_game.id)
    target_player = PlayerFactory(game_id=fake_game.id, social_disgrace=True)
    victim_player = PlayerFactory(game_id=fake_game.id)
    target_secret = Secret(id=24, game_id=fake_game.id, owner=victim_player.id, name="revelado", content="", revealed=True, type=SecretType.OTHER,)

    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.SecretService.read', return_value=target_secret)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.SecretService.search', return_value=[target_secret])
    mock_player_read = mocker.patch(
        'app.controllers.card_effects.and_then_there_was_one_more.PlayerService.read',
        side_effect=[acting_player, target_player, victim_player],
    )
    mock_player_update = mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.PlayerService.update', new_callable=AsyncMock,)
    mock_get_last = mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.get_new_discarded_order', return_value=30)
    mock_secret_update = mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.SecretService.update', new_callable=AsyncMock,)
    mock_card_update = mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.CardService.update', new_callable=AsyncMock,)
    mock_game_update = mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.GameService.update', new_callable=AsyncMock,)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.ChatService.create', new_callable=AsyncMock)

    asyncio.run(and_then_there_was_one_more(fake_card, None, [target_player.id], [target_secret.id], [], []))

    mock_secret_update.assert_awaited_once_with(session=None, oid=target_secret.id, data={'owner': target_player.id, 'revealed': False})
    mock_player_update.assert_awaited_once_with(session=None, oid=target_secret.owner, data={'social_disgrace': False},)
    mock_card_update.assert_awaited_once_with(session=None, oid=fake_card.id, data={'owner': None, 'turn_discarded': fake_game.current_turn, 'discarded_order': mock_get_last.return_value},)
    mock_game_update.assert_awaited_once_with(session=None, oid=fake_game.id, data={'status': GameStatus.FINALIZE_TURN, 'player_in_action': None})
    assert mock_player_read.call_count == 3


def test_and_then_there_was_one_more_disallowed_status(mocker):
    fake_game = GameFactory(status=GameStatus.FINALIZED, current_turn=13)
    fake_card = CardFactory(game_id=fake_game.id, owner=19, turn_played=None)
    fake_player = PlayerFactory(id=fake_card.owner, game_id = fake_game.id)

    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.GameService.read', return_value=fake_game)
    mocker.patch('app.controllers.card_effects.and_then_there_was_one_more.PlayerService.read', return_value=fake_player)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(and_then_there_was_one_more(fake_card, None, [], [], [], []))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Ya no se puede jugar eventos"
