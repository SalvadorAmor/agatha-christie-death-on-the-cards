from datetime import datetime, UTC, timedelta

import pytest
from sqlmodel import SQLModel, create_engine, Session, select
from unittest.mock import AsyncMock, call

from app.models.game import Game, GameStatus
from app.models.player import Player
from app.services.game import GameService, not_so_fast_status
from tests.conftest import GameFactory


@pytest.fixture
def engine():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture
def service():
    return GameService()


def insert_game(session, game_id, status=GameStatus.WAITING):
    game = Game(
        id=game_id,
        name=f"game-{game_id}",
        status=status,
        min_players=2,
        max_players=6,
        current_turn=0,
        owner=0,
        player_in_action=None,
        password=None,
    )
    session.add(game)
    session.commit()
    session.refresh(game)
    return game


@pytest.mark.asyncio
async def test_create_game(mocker, session, service):
    mock_notify_players = mocker.patch("app.services.game.notify_game_players", new=AsyncMock())
    mock_notify_lobby = mocker.patch("app.services.game.notify_lobby", new=AsyncMock())

    game_model = Game(
        id=10,
        name="new-game",
        status=GameStatus.WAITING,
        min_players=2,
        max_players=4,
        current_turn=0,
        owner=0,
        player_in_action=None,
        password=None,
    )

    data = game_model.model_dump()

    created = await service.create(session, data)

    assert created.id == 10
    assert session.exec(select(Game).where(Game.id == created.id)).first() is not None
    mock_notify_lobby.assert_awaited_once()
    mock_notify_players.assert_not_called()


@pytest.mark.asyncio
async def test_update_game_service(mocker, session, service):
    game = insert_game(session, game_id=20, status=GameStatus.WAITING)
    mock_notify_players = mocker.patch("app.services.game.notify_game_players", new=AsyncMock())

    updated = await service.update(session, game.id, {"status": GameStatus.STARTED})

    assert updated.status == GameStatus.STARTED
    mock_notify_players.assert_awaited_once()



@pytest.mark.asyncio
async def test_delete_game_cleans_players(mocker, session, service):
    game = insert_game(session, game_id=30, status=GameStatus.WAITING)
    players = [
        Player(id=1, name="p1", game_id=game.id, date_of_birth=datetime.now(UTC), avatar="a1", token="t1", position=0),
        Player(id=2, name="p2", game_id=game.id, date_of_birth=datetime.now(UTC), avatar="a2", token="t2", position=1),
    ]
    session.add_all(players)
    session.commit()

    mock_notify_players = mocker.patch("app.services.game.notify_game_players", new=AsyncMock())
    mock_notify_lobby = mocker.patch("app.services.game.notify_lobby", new=AsyncMock())

    deleted_id = await service.delete(session, game.id)

    assert deleted_id == game.id
    assert session.get(Game, game.id) is None
    remaining_players = session.exec(select(Player).where(Player.game_id == game.id)).all()
    assert remaining_players == []
    mock_notify_players.assert_awaited_once()
    mock_notify_lobby.assert_awaited_once()


@pytest.mark.asyncio
async def test_not_so_fast_status_returns_false_without_cancelation(mocker):
    fake_game = GameFactory(id=101, status=GameStatus.TURN_START, current_turn=5, timestamp=None,)
    updated_timestamp = datetime.now()
    updated_game = Game(**fake_game.model_dump(exclude={"status", "timestamp"}), status=GameStatus.WAITING_FOR_CANCEL_ACTION, timestamp=updated_timestamp)

    session = mocker.Mock()
    session.refresh = mocker.Mock()

    mocker.patch("app.services.game.asyncio.sleep", new=AsyncMock())
    mocker.patch("app.services.game.NOT_SO_FAST_TIME", 0)
    canceled_times_event = mocker.Mock(target_card=0)
    mocker.patch(
        "app.services.game.EventTableService.create",
        new=AsyncMock(side_effect=[canceled_times_event, mocker.Mock()]),
    )
    mock_update = mocker.patch("app.services.game.GameService.update", new=AsyncMock(return_value=updated_game))

    result = await not_so_fast_status(fake_game, session)

    assert result is False
    mock_update.assert_awaited_once()
    assert session.refresh.call_args_list
    assert session.refresh.call_args_list[0] == call(updated_game)
    assert session.refresh.call_args_list[-1] == call(canceled_times_event)


@pytest.mark.asyncio
async def test_not_so_fast_status_emits_timer_updates(mocker):
    base_timestamp = datetime(2024, 1, 1, 12, 0, 0)
    fake_game = GameFactory(id=303, status=GameStatus.TURN_START, current_turn=3, timestamp=None)
    updated_game = Game(**fake_game.model_dump(exclude={"status", "timestamp"}), status=GameStatus.WAITING_FOR_CANCEL_ACTION, timestamp=base_timestamp,)

    session = mocker.Mock()
    session.refresh = mocker.Mock()

    mocker.patch("app.services.game.asyncio.sleep", new=AsyncMock())
    mock_notify = mocker.patch("app.services.game.notify_game_players", new=AsyncMock())
    canceled_times_event = mocker.Mock(target_card=1)
    mocker.patch("app.services.game.EventTableService.create", new=AsyncMock(side_effect=[canceled_times_event, mocker.Mock()]),)
    mocker.patch("app.services.game.GameService.update", new=AsyncMock(return_value=updated_game))
    mocker.patch("app.services.game.NOT_SO_FAST_TIME", 2)

    datetime_sequence = [
        base_timestamp,
        base_timestamp + timedelta(seconds=1),
        base_timestamp + timedelta(seconds=3),
    ]
    datetime_mock = mocker.patch("app.services.game.datetime")
    datetime_mock.now.side_effect = datetime_sequence

    result = await not_so_fast_status(fake_game, session)

    assert result is True
    mock_notify.assert_awaited_once()
    session.refresh.assert_called_with(canceled_times_event)
