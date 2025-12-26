import pytest
from unittest.mock import AsyncMock

from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session

from app.controllers.card_effects.devious_detect import devious_detect
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
async def test_devious_detect_social_faux_pas_branch(session):
    game = GameFactory(id=1, status=GameStatus.SELECT_CARD_TO_TRADE, current_turn=3, player_in_action=None)
    target_card = CardFactory(
        id=5,
        game_id=game.id,
        name="social-faux-pas",
        turn_played=None,
        card_type=CardType.DEVIOUS,
    )
    trade_event = EventTable(
        id=10,
        game_id=game.id,
        action="card_trade",
        turn_played=game.current_turn,
        player_id=20,
        target_player=21,
        target_card=target_card.id,
        completed_action=False,
    )
    fake_player = PlayerFactory(game_id=game.id,id=21)

    session.add(fake_player)
    session.add(game)
    session.add(target_card)
    session.add(trade_event)
    session.commit()

    await devious_detect(session=session, game=game)

    session.refresh(game)
    session.refresh(target_card)
    session.refresh(trade_event)

    assert trade_event.completed_action is True
    assert target_card.turn_played == game.current_turn
    assert game.status == GameStatus.WAITING_FOR_CHOOSE_SECRET
    assert game.player_in_action == trade_event.target_player


@pytest.mark.asyncio
async def test_devious_detect_social_faux_pas_canceled_flow(session, mocker):
    game = GameFactory(id=10, status=GameStatus.SELECT_CARD_TO_TRADE, current_turn=2, player_in_action=None)
    target_card = CardFactory(
        id=50,
        game_id=game.id,
        name="social-faux-pas",
        owner=99,
        turn_played=None,
        turn_discarded=None,
        discarded_order=None,
        card_type=CardType.DEVIOUS,
    )
    trade_event = EventTable(
        id=60,
        game_id=game.id,
        action="card_trade",
        turn_played=game.current_turn,
        player_id=88,
        target_player=77,
        target_card=target_card.id,
        completed_action=False,
    )
    fake_player = PlayerFactory(game_id=game.id, id=77)

    mock_not_so_fast = mocker.patch(
        "app.controllers.card_effects.devious_detect.not_so_fast_status", new_callable=AsyncMock
    )
    mock_not_so_fast.return_value = True
    mock_chat_create = mocker.patch(
        "app.controllers.card_effects.devious_detect.ChatService.create", new_callable=AsyncMock
    )

    session.add(fake_player)
    session.add(game)
    session.add(target_card)
    session.add(trade_event)
    session.commit()

    await devious_detect(session=session, game=game)

    mock_not_so_fast.assert_awaited_once_with(game, session, target_card.id)

    session.refresh(game)
    session.refresh(target_card)
    session.refresh(trade_event)

    assert trade_event.completed_action is True
    assert target_card.turn_discarded == game.current_turn
    assert target_card.owner is None
    assert target_card.turn_played is None
    assert game.status == GameStatus.FINALIZE_TURN
    assert game.player_in_action is None


@pytest.mark.asyncio
async def test_devious_detect_blackmailed_branch(session):
    game = GameFactory(id=2, status=GameStatus.SELECT_CARD_TO_TRADE, current_turn=4, player_in_action=None)
    target_card = CardFactory(
        id=6,
        game_id=game.id,
        name="blackmailed",
        turn_played=None,
        card_type=CardType.DEVIOUS,
    )
    trade_event = EventTable(
        id=11,
        game_id=game.id,
        action="dead_card_folly_trade",
        turn_played=game.current_turn,
        player_id=30,
        target_player=31,
        target_card=target_card.id,
        completed_action=False,
    )

    session.add(game)
    session.add(target_card)
    session.add(trade_event)
    session.commit()

    await devious_detect(session=session, game=game)

    session.refresh(game)
    session.refresh(target_card)
    session.refresh(trade_event)

    assert trade_event.completed_action is True
    assert target_card.turn_played == game.current_turn
    assert game.status == GameStatus.WAITING_FOR_CHOOSE_SECRET
    assert game.player_in_action == trade_event.player_id


@pytest.mark.asyncio
async def test_devious_detect_without_matching_events_finishes_turn(session):
    game = GameFactory(id=3, status=GameStatus.SELECT_CARD_TO_TRADE, current_turn=1, player_in_action=5)

    session.add(game)
    session.commit()

    await devious_detect(session=session, game=game)

    session.refresh(game)
    assert game.status == GameStatus.FINALIZE_TURN
    assert game.player_in_action == 5
