from fastapi.exceptions import HTTPException

import pytest
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session

from app.controllers.card_effects.point_your_suspicions import point_your_suspicions
from app.models.game import GameStatus
from app.models.secret import Secret, SecretType
from app.services.event_table import EventTableService
from app.services.game import GameService
from tests.conftest import GameFactory, CardFactory, PlayerFactory, EventTableFactory

@pytest.fixture
def engine():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session

@pytest.mark.asyncio
async def test_cancel_point_your_suspicions(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.TURN_START, current_turn=1, player_in_action=None)
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="point-your-suspicions")
    players = [PlayerFactory(id=i, game_id=game.id, token=f"token_{i}") for i in range(1, 4)]

    mock_notify_game_players = mocker.patch("app.controllers.card_effects.point_your_suspicions.notify_game_players", new_callable=AsyncMock)
    mocker.patch('app.controllers.card_effects.point_your_suspicions.not_so_fast_status', return_value=True)

    session.add(game)
    session.add(playing_card)
    session.add_all(players)

    session.commit()

    # when

    # Jugador 1 juega la carta
    await point_your_suspicions(card=playing_card, session=session, issuer_player=players[0])

    # then
    events = EventTableService().search(session=session, filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn, "action__eq": "point_your_suspicions", "target_player__is_null": False})
    assert len(events) == 0
    session.refresh(game)
    assert game.status == GameStatus.FINALIZE_TURN
    assert game.player_in_action is None
    session.refresh(playing_card)
    assert playing_card.turn_discarded == game.current_turn
    session.close()


@pytest.mark.asyncio
async def test_point_your_suspicions(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.TURN_START, current_turn=1, player_in_action=None)
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="point-your-suspicions")
    players = [PlayerFactory(id=i, game_id=game.id, token=f"token_{i}") for i in range(1, 4)]

    mock_notify_game_players = mocker.patch("app.controllers.card_effects.point_your_suspicions.notify_game_players", new_callable=AsyncMock)
    mocker.patch('app.controllers.card_effects.point_your_suspicions.not_so_fast_status', return_value=False)

    session.add(game)
    session.add(playing_card)
    session.add_all(players)

    session.commit()

    # when

    # Jugador 1 juega la carta
    await point_your_suspicions(card=playing_card, session=session, issuer_player=players[0])

    # then
    events = EventTableService().search(session=session, filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn, "action__eq": "point_your_suspicions", "target_player__is_null": False})
    assert len(events) == 0
    session.refresh(game)
    assert game.status == GameStatus.WAITING_FOR_CHOOSE_PLAYER
    assert game.player_in_action is None
    session.close()


@pytest.mark.asyncio
async def test_point_your_suspicions_choose_player(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.WAITING_FOR_CHOOSE_PLAYER, current_turn=1, player_in_action=None)
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="point-your-suspicions")
    players = [PlayerFactory(id=i, game_id=game.id) for i in range(1, 4)]

    mock_notify_game_players = mocker.patch("app.controllers.card_effects.point_your_suspicions.notify_game_players", new_callable=AsyncMock)

    session.add(game)
    session.add(playing_card)
    session.add_all(players)

    session.commit()

    # when

    # Jugador 1 juega la carta
    await point_your_suspicions(card=playing_card, session=session, target_players=[2], issuer_player=players[0])

    # then
    events = EventTableService().search(session=session, filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn, "action__eq": "point_your_suspicions", "target_player__is_null": False})
    assert len(events) == 1
    session.refresh(game)
    assert game.status == GameStatus.WAITING_FOR_CHOOSE_PLAYER
    assert game.player_in_action is None
    session.close()

@pytest.mark.asyncio
async def test_point_your_suspicions_choose_player_empty(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.WAITING_FOR_CHOOSE_PLAYER, current_turn=1, player_in_action=None)
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="point-your-suspicions")
    players = [PlayerFactory(id=i, game_id=game.id) for i in range(1, 4)]

    mock_notify_game_players = mocker.patch(
        "app.controllers.card_effects.point_your_suspicions.notify_game_players", new_callable=AsyncMock)
    session.add(game)
    session.add(playing_card)
    session.add_all(players)

    session.commit()

    # when

    # Jugador 1 juega la carta
    with pytest.raises(HTTPException):
        await point_your_suspicions(card=playing_card, session=session, target_players=[], issuer_player=players[0])

        # then
        events = EventTableService().search(session=session,
                                            filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn,
                                                      "action__eq": "point_your_suspicions",
                                                      "target_player__is_null": False})
        assert len(events) == 0
        session.refresh(game)
        assert game.status == GameStatus.WAITING_FOR_CHOOSE_PLAYER
        assert game.player_in_action is None
        session.close()

@pytest.mark.asyncio
async def test_point_your_suspicions_choose_player_not_in_game(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.WAITING_FOR_CHOOSE_PLAYER, current_turn=1, player_in_action=None)
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="point-your-suspicions")
    players = [PlayerFactory(id=i, game_id=game.id) for i in range(1, 4)]

    mock_notify_game_players = mocker.patch(
        "app.controllers.card_effects.point_your_suspicions.notify_game_players", new_callable=AsyncMock)
    session.add(game)
    session.add(playing_card)
    session.add_all(players)

    session.commit()

    # when

    # Jugador 1 juega la carta
    with pytest.raises(HTTPException):
        await point_your_suspicions(card=playing_card, session=session, target_players=[6], issuer_player=players[0])

        # then
        events = EventTableService().search(session=session,
                                            filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn,
                                                      "action__eq": "point_your_suspicions",
                                                      "target_player__is_null": False})
        assert len(events) == 0
        session.refresh(game)
        assert game.status == GameStatus.WAITING_FOR_CHOOSE_PLAYER
        assert game.player_in_action is None
        session.close()


@pytest.mark.asyncio
async def test_point_your_suspicions_all_players_have_targeted_another(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.WAITING_FOR_CHOOSE_PLAYER, current_turn=1, player_in_action=None)
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="point-your-suspicions")
    players = [PlayerFactory(id=i, game_id=game.id) for i in range(1, 4)]

    existing_events = [
        EventTableFactory(id=1, game_id=game.id, player_id=2, action="point_your_suspicions", turn_played=game.current_turn, target_player=3),
        EventTableFactory(id=2, game_id=game.id, player_id=3, action="point_your_suspicions", turn_played=game.current_turn, target_player=2),
    ]

    mock_notify_game_players = mocker.patch("app.controllers.card_effects.point_your_suspicions.notify_game_players", new_callable=AsyncMock)
    session.add(game)
    session.add(playing_card)
    session.add_all(players)
    session.add_all(existing_events)
    session.commit()

    # when

    # Jugador 1 juega la carta señalando al jugador 2
    await point_your_suspicions(card=playing_card, session=session, target_players=[2], issuer_player=players[0])

    # then
    events = EventTableService().search(session=session, filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn, "action__eq": "point_your_suspicions", "target_player__is_null": False})
    assert len(events) == len(players)
    session.refresh(game)
    assert game.status == GameStatus.WAITING_FOR_CHOOSE_SECRET
    assert game.player_in_action == 2

    session.close()


@pytest.mark.asyncio
async def test_point_your_suspicions_all_players_have_targeted_another_tie(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.WAITING_FOR_CHOOSE_PLAYER, current_turn=1, player_in_action=None)
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="point-your-suspicions")
    players = [PlayerFactory(id=i, game_id=game.id) for i in range(1, 4)]

    existing_events = [
        EventTableFactory(id=1, game_id=game.id, player_id=2, action="point_your_suspicions", turn_played=game.current_turn, target_player=3),
        EventTableFactory(id=2, game_id=game.id, player_id=3, action="point_your_suspicions", turn_played=game.current_turn, target_player=1),
    ]

    mock_notify_game_players = mocker.patch("app.controllers.card_effects.point_your_suspicions.notify_game_players", new_callable=AsyncMock)
    session.add(game)
    session.add(playing_card)
    session.add_all(players)
    session.add_all(existing_events)
    session.commit()

    # when

    # Jugador 1 juega la carta señalando al jugador 2
    await point_your_suspicions(card=playing_card, session=session, target_players=[2], issuer_player=players[0])

    # then
    events = EventTableService().search(session=session, filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn, "action__eq": "point_your_suspicions", "target_player__is_null": False})
    assert len(events) == len(players)
    session.refresh(game)
    assert game.status == GameStatus.WAITING_FOR_CHOOSE_PLAYER
    assert game.player_in_action == playing_card.owner

    session.close()

@pytest.mark.asyncio
async def test_point_your_suspicions_reveal_secret(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.WAITING_FOR_CHOOSE_SECRET, current_turn=1, player_in_action=2)
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="point-your-suspicions")
    players = [PlayerFactory(id=i, game_id=game.id) for i in range(1, 4)]
    secret = Secret(id=1, owner=2, game_id=game.id, revealed=False, type=SecretType.OTHER, name="test", content="test secret")

    existing_events = [
        EventTableFactory(id=1, game_id=game.id, player_id=2, action="point_your_suspicions", turn_played=game.current_turn, target_player=3),
        EventTableFactory(id=2, game_id=game.id, player_id=3, action="point_your_suspicions", turn_played=game.current_turn, target_player=2),
        EventTableFactory(id=3, game_id=game.id, player_id=1, action="point_your_suspicions", turn_played=game.current_turn, target_player=2),
    ]

    mock_notify_game_players = mocker.patch("app.controllers.card_effects.point_your_suspicions.notify_game_players", new_callable=AsyncMock)
    session.add(game)
    session.add(playing_card)
    session.add_all(players)
    session.add_all(existing_events)
    session.add(secret)
    session.commit()

    # when

    # Jugador 1 juega la carta señalando al jugador 2
    await point_your_suspicions(card=playing_card, session=session, target_secrets=[1], issuer_player=players[0])

    # then
    events = EventTableService().search(session=session, filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn, "action__eq": "point_your_suspicions", "target_player__is_null": False})
    assert len(events) == len(players)
    session.refresh(game)
    session.refresh(secret)
    assert game.status == GameStatus.FINALIZED
    assert game.player_in_action is None
    assert secret.revealed
    session.close()


@pytest.mark.asyncio
async def test_point_your_suspicions_reveal_secret_non_finalizing(session, mocker):
    # given
    game = GameFactory(id=2, status=GameStatus.WAITING_FOR_CHOOSE_SECRET, current_turn=3, player_in_action=3)
    playing_card = CardFactory(id=100, game_id=game.id, turn_discarded=None, owner=4, name="point-your-suspicions")
    players = [PlayerFactory(id=i, game_id=game.id) for i in range(3, 6)]
    target_secret = Secret(
        id=11,
        owner=game.player_in_action,
        game_id=game.id,
        revealed=False,
        type=SecretType.OTHER,
        name="target-secret",
        content="secret",
    )
    other_secret = Secret(id=12, owner=players[-1].id, game_id=game.id, revealed=False, type=SecretType.OTHER, name="other-secret", content="another secret",)

    existing_events = [
        EventTableFactory(id=21, game_id=game.id, player_id=players[0].id, action="point_your_suspicions", turn_played=game.current_turn, target_player=players[1].id,),
        EventTableFactory(id=22, game_id=game.id, player_id=players[1].id, action="point_your_suspicions", turn_played=game.current_turn, target_player=players[0].id,),
        EventTableFactory(id=23, game_id=game.id, player_id=players[2].id, action="point_your_suspicions", turn_played=game.current_turn, target_player=game.player_in_action,),
    ]

    mocker.patch("app.controllers.card_effects.point_your_suspicions.notify_game_players", new_callable=AsyncMock)

    session.add(game)
    session.add(playing_card)
    session.add_all(players)
    session.add_all(existing_events)
    session.add(target_secret)
    session.add(other_secret)
    session.commit()

    # when
    await point_your_suspicions(card=playing_card, session=session, target_secrets=[target_secret.id], issuer_player=players[0])

    # then
    events = EventTableService().search(session=session, filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn, "action__eq": "point_your_suspicions", "target_player__is_null": False,},)
    assert len(events) == len(players)
    session.refresh(game)
    session.refresh(target_secret)
    assert game.status == GameStatus.FINALIZE_TURN
    assert game.player_in_action is None
    assert target_secret.revealed
    session.close()


@pytest.mark.asyncio
async def test_point_your_suspicions_empty_target_secret(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.WAITING_FOR_CHOOSE_SECRET, current_turn=1, player_in_action=2)
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="point-your-suspicions")
    players = [PlayerFactory(id=i, game_id=game.id) for i in range(1, 4)]
    secret = Secret(id=1, owner=2, game_id=game.id, revealed=False, type=SecretType.OTHER, name="test", content="test secret")

    existing_events = [
        EventTableFactory(id=1, game_id=game.id, player_id=2, action="point_your_suspicions", turn_played=game.current_turn, target_player=3),
        EventTableFactory(id=2, game_id=game.id, player_id=3, action="point_your_suspicions", turn_played=game.current_turn, target_player=2),
        EventTableFactory(id=3, game_id=game.id, player_id=1, action="point_your_suspicions", turn_played=game.current_turn, target_player=2),
    ]

    mock_notify_game_players = mocker.patch("app.controllers.card_effects.point_your_suspicions.notify_game_players", new_callable=AsyncMock)
    session.add(game)
    session.add(playing_card)
    session.add_all(players)
    session.add_all(existing_events)
    session.add(secret)
    session.commit()

    # when

    # Jugador 1 juega la carta señalando al jugador 2
    with pytest.raises(HTTPException):
        await point_your_suspicions(card=playing_card, session=session, target_secrets=[], issuer_player=players[0])

        # then
        events = EventTableService().search(session=session, filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn, "action__eq": "point_your_suspicions", "target_player__is_null": False})
        assert len(events) == len(players)
        session.refresh(game)
        session.refresh(secret)
        assert game.status == GameStatus.WAITING_FOR_CHOOSE_SECRET
        assert 2 == game.player_in_action
        assert not secret.revealed
        session.close()

@pytest.mark.asyncio
async def test_point_your_suspicions_another_target_secret(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.WAITING_FOR_CHOOSE_SECRET, current_turn=1, player_in_action=2)
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="point-your-suspicions")
    players = [PlayerFactory(id=i, game_id=game.id) for i in range(1, 4)]
    secret = Secret(id=1, owner=1, game_id=game.id, revealed=False, type=SecretType.OTHER, name="test", content="test secret")

    existing_events = [
        EventTableFactory(id=1, game_id=game.id, player_id=2, action="point_your_suspicions", turn_played=game.current_turn, target_player=3),
        EventTableFactory(id=2, game_id=game.id, player_id=3, action="point_your_suspicions", turn_played=game.current_turn, target_player=2),
        EventTableFactory(id=3, game_id=game.id, player_id=1, action="point_your_suspicions", turn_played=game.current_turn, target_player=2),
    ]

    mock_notify_game_players = mocker.patch("app.controllers.card_effects.point_your_suspicions.notify_game_players", new_callable=AsyncMock)
    session.add(game)
    session.add(playing_card)
    session.add_all(players)
    session.add_all(existing_events)
    session.add(secret)
    session.commit()

    # when

    # Jugador 1 juega la carta señalando al jugador 2
    with pytest.raises(HTTPException):
        await point_your_suspicions(card=playing_card, session=session, target_secrets=[1], issuer_player=players[0])

        # then
        events = EventTableService().search(session=session, filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn, "action__eq": "point_your_suspicions", "target_player__is_null": False})
        assert len(events) == len(players)
        session.refresh(game)
        session.refresh(secret)
        assert game.status == GameStatus.WAITING_FOR_CHOOSE_SECRET
        assert 2 == game.player_in_action
        assert not secret.revealed
        session.close()

@pytest.mark.asyncio
async def test_point_your_suspicions_revealed_target_secret(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.WAITING_FOR_CHOOSE_SECRET, current_turn=1, player_in_action=2)
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="point-your-suspicions")
    players = [PlayerFactory(id=i, game_id=game.id) for i in range(1, 4)]
    secret = Secret(id=1, owner=2, game_id=game.id, revealed=True, type=SecretType.OTHER, name="test", content="test secret")

    existing_events = [
        EventTableFactory(id=1, game_id=game.id, player_id=2, action="point_your_suspicions", turn_played=game.current_turn, target_player=3),
        EventTableFactory(id=2, game_id=game.id, player_id=3, action="point_your_suspicions", turn_played=game.current_turn, target_player=2),
        EventTableFactory(id=3, game_id=game.id, player_id=1, action="point_your_suspicions", turn_played=game.current_turn, target_player=2),
    ]

    mock_notify_game_players = mocker.patch("app.controllers.card_effects.point_your_suspicions.notify_game_players", new_callable=AsyncMock)
    session.add(game)
    session.add(playing_card)
    session.add_all(players)
    session.add_all(existing_events)
    session.add(secret)
    session.commit()

    # when

    # Jugador 1 juega la carta señalando al jugador 2
    with pytest.raises(HTTPException):
        await point_your_suspicions(card=playing_card, session=session, target_secrets=[1],issuer_player=players[0])

        # then
        events = EventTableService().search(session=session, filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn, "action__eq": "point_your_suspicions", "target_player__is_null": False})
        assert len(events) == len(players)
        session.refresh(game)
        session.refresh(secret)
        assert game.status == GameStatus.WAITING_FOR_CHOOSE_SECRET
        assert 2 == game.player_in_action
        assert not secret.revealed
        session.close()
