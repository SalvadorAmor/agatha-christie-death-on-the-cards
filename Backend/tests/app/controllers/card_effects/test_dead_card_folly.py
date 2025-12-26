from fastapi.exceptions import HTTPException

import pytest
from unittest.mock import AsyncMock, MagicMock

from requests.packages import target
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session

from app.controllers.card import PlayerOrders
from app.controllers.card_effects.card_trade import card_trade
from app.controllers.card_effects.dead_card_folly import dead_card_folly
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
async def test_cancel_dead_card_folly(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.TURN_START, current_turn=1, player_in_action=None)
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="card-trade")
    players = [PlayerFactory(id=i, game_id=game.id, token=f"token_{i}") for i in range(1, 4)]

    mocker.patch('app.controllers.card_effects.dead_card_folly.not_so_fast_status', return_value=True)

    session.add(game)
    session.add(playing_card)
    session.add_all(players)

    session.commit()

    # when

    # Jugador 1 juega la carta
    await dead_card_folly(card=playing_card, session=session, issuer_player=players[0])

    # then
    events = EventTableService().search(session=session, filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn, "action__eq": "dead_card_folly", "target_player__is_null": False})
    assert len(events) == 0
    session.refresh(game)
    assert game.status == GameStatus.FINALIZE_TURN
    assert game.player_in_action is None
    session.refresh(playing_card)
    assert playing_card.turn_discarded == game.current_turn
    session.close()


@pytest.mark.asyncio
async def test_dead_card_folly_play_card(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.TURN_START, current_turn=1, player_in_action=None)
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="dead-card-folly")
    players = [PlayerFactory(id=i, game_id=game.id, token=f"token_{i}") for i in range(1, 4)]

    mocker.patch('app.controllers.card_effects.dead_card_folly.not_so_fast_status', return_value=False)

    session.add(game)
    session.add(playing_card)
    session.add_all(players)

    session.commit()

    # when

    # Jugador 1 juega la carta
    await dead_card_folly(card=playing_card, session=session, issuer_player=players[0], player_order=None)

    # then
    events = EventTableService().search(session=session, filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn, "action__in": ["dead_card_folly_clockwise", "dead_card_folly_trade", "dead_card_folly_counter-clockwise"]})
    assert len(events) == 0
    session.refresh(game)
    assert game.status == GameStatus.WAITING_TO_CHOOSE_DIRECTION
    assert game.player_in_action == playing_card.owner
    session.close()


@pytest.mark.asyncio
async def test_dead_card_folly_select_order_empty(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.WAITING_TO_CHOOSE_DIRECTION, current_turn=1, player_in_action=1)
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="dead-card-folly", turn_played=game.current_turn)
    players = [PlayerFactory(id=i, game_id=game.id, token=f"token_{i}") for i in range(1, 4)]

    mocker.patch('app.controllers.card_effects.dead_card_folly.not_so_fast_status', return_value=False)

    session.add(game)
    session.add(playing_card)
    session.add_all(players)

    session.commit()

    # when

    # Jugador 1 juega la carta
    with pytest.raises(HTTPException):
        await dead_card_folly(card=playing_card, session=session, issuer_player=players[0], player_order=None)

        # then
        events = EventTableService().search(session=session,
                                            filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn,
                                                      "action__in": ["dead_card_folly_clockwise",
                                                                     "dead_card_folly_trade",
                                                                     "dead_card_folly_counter-clockwise"]})
        assert len(events) == 0
        session.refresh(game)
        assert game.status == GameStatus.WAITING_TO_CHOOSE_DIRECTION
        assert game.player_in_action == playing_card.owner
        session.close()


@pytest.mark.parametrize("order_choice, expected_action", [
    (PlayerOrders.CLOCKWISE, "dead_card_folly_clockwise"),
    (PlayerOrders.COUNTER_CLOCKWISE, "dead_card_folly_counter-clockwise"),
])
@pytest.mark.asyncio
async def test_dead_card_folly_select_order(session, mocker, order_choice, expected_action):
    # given
    game = GameFactory(id=1, status=GameStatus.WAITING_TO_CHOOSE_DIRECTION, current_turn=1, player_in_action=1)
    players = [PlayerFactory(id=i, game_id=game.id, token=f"token_{i}") for i in range(1, 4)]
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="dead-card-folly", turn_played=1)

    mocker.patch('app.controllers.card_effects.dead_card_folly.not_so_fast_status', return_value=False)

    session.add(game)
    session.add(playing_card)
    session.add_all(players)

    session.commit()

    # when

    # Jugador 1 juega la carta
    await dead_card_folly(card=playing_card, session=session, issuer_player=players[0], player_order=order_choice)

    # then
    events = EventTableService().search(session=session, filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn, "action__in": ["dead_card_folly_clockwise", "dead_card_folly_trade", "dead_card_folly_counter-clockwise"]})
    assert len(events) == 1
    assert events[0].action == expected_action
    session.refresh(game)
    assert game.status == GameStatus.SELECT_CARD_TO_TRADE
    assert game.player_in_action is None
    session.close()


@pytest.mark.asyncio
async def test_dead_card_folly_select_card_empty(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.SELECT_CARD_TO_TRADE, current_turn=1, player_in_action=None)
    players = [PlayerFactory(id=i, game_id=game.id, token=f"token_{i}") for i in range(1, 4)]
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="dead-card-folly", turn_played=1)
    event_order_selected = EventTableFactory(id=1, game_id=game.id, player_id=players[0].id, action="dead_card_folly_clockwise", turn_played=game.current_turn)

    mocker.patch('app.controllers.card_effects.dead_card_folly.not_so_fast_status', return_value=False)

    session.add(game)
    session.add(playing_card)
    session.add_all(players)
    session.add(event_order_selected)

    session.commit()

    # when

    # Jugador 1 juega la carta
    with pytest.raises(HTTPException):
        await dead_card_folly(card=playing_card, session=session, issuer_player=players[0], target_cards=[])

        # then
        events = EventTableService().search(session=session,
                                            filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn,
                                                      "action__in": ["dead_card_folly_clockwise",
                                                                     "dead_card_folly_trade",
                                                                     "dead_card_folly_counter-clockwise"]})
        assert len(events) == 1
        session.refresh(game)
        assert game.status == GameStatus.SELECT_CARD_TO_TRADE
        assert game.player_in_action is None
        session.close()


@pytest.mark.asyncio
async def test_dead_card_folly_select_card_not_mine(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.SELECT_CARD_TO_TRADE, current_turn=1, player_in_action=None)
    players = [PlayerFactory(id=i, game_id=game.id, position=i, token=f"token_{i}") for i in range(1, 4)]
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="dead-card-folly", turn_played=1)
    target_card = CardFactory(id=99, game_id=game.id, turn_discarded=None, owner=2, name="asdf")
    event_order_selected = EventTableFactory(id=1, game_id=game.id, player_id=players[0].id, action="dead_card_folly_clockwise", turn_played=game.current_turn)

    mocker.patch('app.controllers.card_effects.dead_card_folly.not_so_fast_status', return_value=False)

    session.add(game)
    session.add(playing_card)
    session.add_all(players)
    session.add(event_order_selected)
    session.add(target_card)

    session.commit()

    # when

    # Jugador 1 juega la carta
    with pytest.raises(HTTPException):
        await dead_card_folly(card=playing_card, session=session, issuer_player=players[0], target_cards=[target_card.id])

        # then
        events = EventTableService().search(session=session,
                                            filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn,
                                                      "action__in": ["dead_card_folly_clockwise",
                                                                     "dead_card_folly_trade",
                                                                     "dead_card_folly_counter-clockwise"]})
        assert len(events) == 1
        session.refresh(game)
        assert game.status == GameStatus.SELECT_CARD_TO_TRADE
        assert game.player_in_action is None
        session.close()

@pytest.mark.asyncio
async def test_dead_card_folly_select_card(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.SELECT_CARD_TO_TRADE, current_turn=1, player_in_action=None)
    players = [PlayerFactory(id=i, game_id=game.id, token=f"token_{i}", position=i-1) for i in range(1, 4)]
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="dead-card-folly", turn_played=1)
    target_card = CardFactory(id=99, game_id=game.id, turn_discarded=None, owner=1, name="asdf")
    event_order_selected = EventTableFactory(id=1, game_id=game.id, player_id=players[0].id, action="dead_card_folly_clockwise", turn_played=game.current_turn)

    mocker.patch('app.controllers.card_effects.dead_card_folly.not_so_fast_status', return_value=False)

    session.add(game)
    session.add(playing_card)
    session.add_all(players)
    session.add(event_order_selected)
    session.add(target_card)

    session.commit()

    # when

    # Jugador 1 juega la carta
    await dead_card_folly(card=playing_card, session=session, issuer_player=players[0], target_cards=[target_card.id])

    # then
    events = EventTableService().search(session=session,
                                        filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn,
                                                  "action__in": ["dead_card_folly_clockwise",
                                                                 "dead_card_folly_trade",
                                                                 "dead_card_folly_counter-clockwise"]})
    assert len(events) == 2
    session.refresh(game)
    assert game.status == GameStatus.SELECT_CARD_TO_TRADE
    assert game.player_in_action is None
    session.close()

@pytest.mark.asyncio
async def test_dead_card_folly_select_card_last(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.SELECT_CARD_TO_TRADE, current_turn=1, player_in_action=None)
    players = [PlayerFactory(id=i, game_id=game.id, token=f"token_{i}", position=i-1) for i in range(1, 4)]
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="dead-card-folly", turn_played=1)
    target_card = CardFactory(id=99, game_id=game.id, turn_discarded=None, owner=1, name="asdf")
    event_order_selected = EventTableFactory(id=1, game_id=game.id, player_id=players[0].id, action="dead_card_folly_clockwise", turn_played=game.current_turn)
    other_players_target_cards = [CardFactory(id=100+i, game_id=game.id, turn_discarded=None, owner=players[i+1].id, name=f"card_{i+1}") for i in range(len(players)-1)]
    session.add_all(other_players_target_cards)
    events_card_trades = [EventTableFactory(id=i+2, game_id=game.id, player_id=players[i-1].id, action="dead_card_folly_trade",target_card=other_players_target_cards[i-1].id, target_player=players[i-1 % len(players)].id, turn_played=game.current_turn, completed_action=False) for i in range(1, len(players))]
    session.add_all(events_card_trades)

    mocker.patch('app.controllers.card_effects.dead_card_folly.not_so_fast_status', return_value=False)

    session.add(game)
    session.add(playing_card)
    session.add_all(players)
    session.add(event_order_selected)
    session.add(target_card)

    session.commit()

    # when

    # Jugador 1 juega la carta
    await dead_card_folly(card=playing_card, session=session, issuer_player=players[0], target_cards=[target_card.id])

    # then
    events = EventTableService().search(session=session,
                                        filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn,
                                                  "action__in": ["dead_card_folly_clockwise",
                                                                 "dead_card_folly_trade",
                                                                 "dead_card_folly_counter-clockwise"]})
    assert len(events) == 4
    session.refresh(game)
    for card in other_players_target_cards:
        session.refresh(card)
        targeting_event = filter(lambda e: e.target_card == card.id, events)
        targeting_event = list(targeting_event)[0]
        assert card.owner == targeting_event.target_player
        
    assert game.player_in_action is None
    session.close()