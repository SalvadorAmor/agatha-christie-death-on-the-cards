import pytest
from sqlmodel import SQLModel, create_engine, Session, select
from unittest.mock import AsyncMock

from app.models.event_table import EventTable
from app.models.game import Game, GameStatus
from app.services.event_table import EventTableService
from tests.conftest import CardFactory


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
    return EventTableService()

def insert_game(session, game_id, status=GameStatus.TURN_START):
    game = Game(
        id=game_id,
        name=f"game-{game_id}",
        status=status,
        min_players=2,
        max_players=4,
        current_turn=0,
        owner=0,
        player_in_action=None,
        password=None,
    )
    session.add(game)
    session.commit()
    session.refresh(game)
    return game

def insert_event_table(
    session,
    event_id=1,
    game_id=1,
    action="action_1",
    turn_played=1,
    player_id=1,
    target_player=None,
    target_set=None,
    target_card=None,
    target_secret=None,
    completed_action=False,
):
    event = EventTable(
        id=event_id,
        game_id=game_id,
        action=action,
        turn_played=turn_played,
        player_id=player_id,
        target_player=target_player,
        target_set=target_set,
        target_card=target_card,
        target_secret=target_secret,
        completed_action=completed_action,
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event

@pytest.mark.asyncio
async def test_update_event_table(mocker, session, service):
    game = insert_game(session, game_id=2, status=GameStatus.TURN_START)

    event_table = insert_event_table(session, event_id=11, game_id=game.id)
    mock_notify = mocker.patch("app.services.event_table.notify_game_players", new=AsyncMock())

    updated = await service.update(session, event_table.id, {"completed_action": True})

    assert updated.completed_action == True
    mock_notify.assert_awaited_once()