from fastapi import HTTPException
import pytest
from unittest.mock import AsyncMock

from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session

from app.controllers.card_effects.blackmailed import blackmailed
from app.models.card import CardType
from app.models.event_table import EventTable
from app.models.game import GameStatus
from tests.conftest import CardFactory, GameFactory, PlayerFactory


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
async def test_blackmailed_card_not_in_play(session):
    game = GameFactory(id=1, status=GameStatus.WAITING_FOR_CHOOSE_SECRET, current_turn=2)
    card = CardFactory(
        id=10,
        game_id=game.id,
        name="blackmailed",
        turn_played=1,
        card_type=CardType.DEVIOUS,
    )

    session.add(game)
    session.add(card)
    session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await blackmailed(card=card, session=session, target_secrets=[1])

    assert exc_info.value.status_code == 400
    assert "devious" in exc_info.value.detail


@pytest.mark.asyncio
async def test_blackmailed_requires_secret_selection(session):
    game = GameFactory(id=2, status=GameStatus.WAITING_FOR_CHOOSE_SECRET, current_turn=3)
    card = CardFactory(
        id=11,
        game_id=game.id,
        name="blackmailed",
        turn_played=game.current_turn,
        card_type=CardType.DEVIOUS,
    )

    session.add(game)
    session.add(card)
    session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await blackmailed(card=card, session=session, target_secrets=[])

    assert exc_info.value.status_code == 412


@pytest.mark.asyncio
async def test_blackmailed_event_player_mismatch(session):
    player = PlayerFactory(id=20, game_id=1)
    game = GameFactory(
        id=player.game_id,
        status=GameStatus.WAITING_FOR_CHOOSE_SECRET,
        current_turn=1,
        player_in_action=99,
    )
    card = CardFactory(
        id=12,
        game_id=game.id,
        name="blackmailed",
        owner=player.id,
        turn_played=game.current_turn,
        card_type=CardType.DEVIOUS,
    )
    event = EventTable(
        id=30,
        game_id=game.id,
        action="card_trade",
        turn_played=game.current_turn,
        player_id=player.id,
        target_card=card.id,
        target_player=player.id,
        completed_action=True,
    )

    session.add(game)
    session.add(player)
    session.add(card)
    session.add(event)
    session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await blackmailed(card=card, session=session, target_secrets=[55])

    assert exc_info.value.status_code == 400
    assert "Evento devious incorrecto" in exc_info.value.detail


@pytest.mark.asyncio
async def test_blackmailed_reveals_secret_and_chains_devious_detect(session, mocker):
    player = PlayerFactory(id=40, game_id=2)
    player = PlayerFactory(id=2, game_id=2)
    game = GameFactory(
        id=player.game_id,
        status=GameStatus.WAITING_FOR_CHOOSE_SECRET,
        current_turn=4,
        player_in_action=player.id,
    )
    card = CardFactory(
        id=13,
        game_id=game.id,
        name="blackmailed",
        owner=player.id,
        turn_played=game.current_turn,
        discarded_order=None,
        turn_discarded=None,
        card_type=CardType.DEVIOUS,
    )
    event = EventTable(
        id=31,
        game_id=game.id,
        action="card_trade",
        turn_played=game.current_turn,
        player_id=player.id,
        target_card=card.id,
        completed_action=True,
        target_player=2
    )

    mock_notify = mocker.patch(
        "app.controllers.card_effects.blackmailed.notify_game_players", new_callable=AsyncMock
    )
    mock_devious_detect = mocker.patch(
        "app.controllers.card_effects.blackmailed.devious_detect", new_callable=AsyncMock
    )

    session.add(game)
    session.add(player)
    session.add(card)
    session.add(event)
    session.commit()

    secret_id = 77

    await blackmailed(card=card, session=session, target_secrets=[secret_id])

    mock_notify.assert_awaited_once()
    notify_args = mock_notify.await_args
    assert notify_args.args[0] == game.id
    assert notify_args.args[1].data == {"secret_id": secret_id, "dest_user": player.id}

    mock_devious_detect.assert_awaited_once()

    session.refresh(card)
    assert card.turn_discarded == game.current_turn
    assert card.owner is None
    assert card.turn_played is None
    assert card.discarded_order == 0
