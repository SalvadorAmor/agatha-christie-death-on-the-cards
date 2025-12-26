from datetime import datetime, UTC

import pytest
from sqlmodel import SQLModel, create_engine, Session, select
from unittest.mock import AsyncMock

from app.models.player import Player
from app.services.player import PlayerService


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
    return PlayerService()


def insert_player(session, player_id=1, game_id=1, token="token-1"):
    player = Player(
        id=player_id,
        game_id=game_id,
        name=f"player-{player_id}",
        date_of_birth=datetime.now(UTC),
        avatar="avatar",
        token=token,
        position=0,
    )
    session.add(player)
    session.commit()
    session.refresh(player)
    return player


@pytest.mark.asyncio
async def test_read_by_token_returns_player(session, service):
    player = insert_player(session, player_id=5, game_id=3, token="abc")

    result = await service.read_by_token(session, "abc")

    assert result.id == player.id


@pytest.mark.asyncio
async def test_read_by_token_returns_none_when_missing(session, service):
    result = await service.read_by_token(session, "missing")
    assert result is None


@pytest.mark.asyncio
async def test_create_player(mocker, session, service):
    mock_notify = mocker.patch("app.services.player.notify_game_players", new=AsyncMock())
    mock_notify_lobby = mocker.patch("app.services.player.notify_lobby", new=AsyncMock())

    player_model = Player(
        id=10,
        game_id=2,
        name="new-player",
        date_of_birth=datetime.now(UTC),
        avatar="avatar",
        token="tok-new",
        position=1,
    )

    data = player_model.model_dump()

    created = await service.create(session, data)

    assert created.id == 10
    assert session.exec(select(Player).where(Player.id == created.id)).first() is not None
    mock_notify.assert_awaited_once()
    mock_notify_lobby.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_player(mocker, session, service):
    player = insert_player(session, player_id=20, game_id=5, token="tok-20")
    mock_notify = mocker.patch("app.services.player.notify_game_players", new=AsyncMock())

    updated = await service.update(session, player.id, {"position": 2})

    assert updated.position == 2
    mock_notify.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_player_returns_none_when_missing(mocker, session, service):
    mock_notify = mocker.patch("app.services.player.notify_game_players", new=AsyncMock())

    result = await service.update(session, 999, {"position": 2})

    assert result is None
    mock_notify.assert_not_called()


@pytest.mark.asyncio
async def test_delete_player_and_removes(mocker, session, service):
    player = insert_player(session, player_id=30, game_id=4, token="tok-30")
    mock_notify = mocker.patch("app.services.player.notify_game_players", new=AsyncMock())
    mock_notify_lobby = mocker.patch("app.services.player.notify_lobby", new=AsyncMock())

    deleted_id = await service.delete(session, player.id)

    assert deleted_id == player.id
    assert session.get(Player, player.id) is None
    mock_notify.assert_awaited_once()
    mock_notify_lobby.assert_awaited_once()
