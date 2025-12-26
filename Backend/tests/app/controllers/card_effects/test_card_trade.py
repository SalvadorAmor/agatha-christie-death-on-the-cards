from fastapi.exceptions import HTTPException

import pytest
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session

from app.controllers.card_effects.card_trade import card_trade
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
async def test_cancel_card_trade(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.TURN_START, current_turn=1, player_in_action=None)
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="card-trade")
    players = [PlayerFactory(id=i, game_id=game.id, token=f"token_{i}") for i in range(1, 4)]

    mocker.patch('app.controllers.card_effects.card_trade.not_so_fast_status', return_value=True)

    session.add(game)
    session.add(playing_card)
    session.add_all(players)

    session.commit()

    # when

    # Jugador 1 juega la carta
    await card_trade(card=playing_card, session=session, issuer_player=players[0])

    # then
    events = EventTableService().search(session=session, filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn, "action__eq": "card_trade", "target_player__is_null": False})
    assert len(events) == 0
    session.refresh(game)
    assert game.status == GameStatus.FINALIZE_TURN
    assert game.player_in_action is None
    session.refresh(playing_card)
    assert playing_card.turn_discarded == game.current_turn
    session.close()


@pytest.mark.asyncio
async def test_card_trade(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.TURN_START, current_turn=1, player_in_action=None)
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="card-trade")
    players = [PlayerFactory(id=i, game_id=game.id, token=f"token_{i}") for i in range(1, 4)]

    mocker.patch('app.controllers.card_effects.card_trade.not_so_fast_status', return_value=False)

    session.add(game)
    session.add(playing_card)
    session.add_all(players)

    session.commit()

    # when

    # Jugador 1 juega la carta
    await card_trade(card=playing_card, session=session, issuer_player=players[0])

    # then
    events = EventTableService().search(session=session, filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn, "action__eq": "point_your_suspicions", "target_player__is_null": False})
    assert len(events) == 0
    session.refresh(game)
    assert game.status == GameStatus.WAITING_FOR_CHOOSE_PLAYER
    assert game.player_in_action == playing_card.owner
    session.close()


@pytest.mark.asyncio
async def test_card_trade_choose_player(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.WAITING_FOR_CHOOSE_PLAYER, current_turn=1, player_in_action=None)
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="card-trade")
    players = [PlayerFactory(id=i, game_id=game.id) for i in range(1, 4)]

    session.add(game)
    session.add(playing_card)
    session.add_all(players)

    session.commit()

    # when

    # Jugador 1 juega la carta
    await card_trade(card=playing_card, session=session, target_players=[2], issuer_player=players[0])

    # then
    events = EventTableService().search(session=session, filterby={"game_id__eq": game.id, "player_id__eq": playing_card.owner, "turn_played__eq": game.current_turn, "action__eq": "card_trade", "target_player__is_null": False})
    assert len(events) == 1
    session.refresh(game)
    assert game.status == GameStatus.SELECT_CARD_TO_TRADE
    assert game.player_in_action is None
    session.close()

@pytest.mark.asyncio
async def test_card_trade_choose_player_empty(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.WAITING_FOR_CHOOSE_PLAYER, current_turn=1, player_in_action=None)
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="card-trade")
    players = [PlayerFactory(id=i, game_id=game.id) for i in range(1, 4)]

    session.add(game)
    session.add(playing_card)
    session.add_all(players)

    session.commit()

    # when

    # Jugador 1 juega la carta
    with pytest.raises(HTTPException):
        await card_trade(card=playing_card, session=session, target_players=[], issuer_player=players[0])

        # then
        events = EventTableService().search(session=session,
                                            filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn,
                                                      "action__eq": "card_trade",
                                                      "target_player__is_null": False})
        assert len(events) == 0
        session.refresh(game)
        assert game.status == GameStatus.WAITING_FOR_CHOOSE_PLAYER
        assert game.player_in_action is None
        session.close()


@pytest.mark.asyncio
async def test_card_trade_choose_point_myself(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.WAITING_FOR_CHOOSE_PLAYER, current_turn=1, player_in_action=None)
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="card-trade")
    players = [PlayerFactory(id=i, game_id=game.id) for i in range(1, 4)]

    session.add(game)
    session.add(playing_card)
    session.add_all(players)

    session.commit()

    # when

    # Jugador 1 juega la carta
    with pytest.raises(HTTPException):
        await card_trade(card=playing_card, session=session, target_players=[players[0].id], issuer_player=players[0])

        # then
        events = EventTableService().search(session=session,
                                            filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn,
                                                      "action__eq": "card_trade",
                                                      "target_player__is_null": False})
        assert len(events) == 0
        session.refresh(game)
        assert game.status == GameStatus.WAITING_FOR_CHOOSE_PLAYER
        assert game.player_in_action is None
        session.close()

@pytest.mark.asyncio
async def test_card_trade_choose_empty_card_trade(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.SELECT_CARD_TO_TRADE, current_turn=1, player_in_action=None)
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=1, name="card-trade")
    players = [PlayerFactory(id=i, game_id=game.id) for i in range(1, 4)]

    session.add(game)
    session.add(playing_card)
    session.add_all(players)

    session.commit()

    # when

    # Jugador 1 juega la carta
    with pytest.raises(HTTPException):
        await card_trade(card=playing_card, session=session, target_cards=[], issuer_player=players[0])

        # then
        events = EventTableService().search(session=session,
                                            filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn,
                                                      "action__eq": "card_trade",
                                                      "target_player__is_null": False})
        assert len(events) == 0
        session.refresh(game)
        assert game.status == GameStatus.SELECT_CARD_TO_TRADE
        assert game.player_in_action is None
        session.close()

@pytest.mark.asyncio
async def test_card_trade_choose_another_players_card(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.SELECT_CARD_TO_TRADE, current_turn=1, player_in_action=None)
    players = [PlayerFactory(id=i, game_id=game.id) for i in range(1, 4)]
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=players[0].id, name="card-trade")
    my_cards = [CardFactory(id=i, game_id=game.id, owner=players[0].id, turn_discarded=None) for i in range(1,7)]

    session.add(game)
    session.add(playing_card)
    session.add_all(players)
    session.add_all(my_cards)

    session.commit()

    # when

    # Jugador 1 juega la carta
    with pytest.raises(HTTPException):
        await card_trade(card=playing_card, session=session, target_cards=[99], issuer_player=players[0])

        # then
        events = EventTableService().search(session=session,
                                            filterby={"game_id__eq": game.id,
                                                      "turn_played__eq": game.current_turn,
                                                      "action__eq": "card_trade",
                                                      "target_card__is_null": False})
        assert len(events) == 1
        session.refresh(game)
        assert game.status == GameStatus.SELECT_CARD_TO_TRADE
        assert game.player_in_action is None
        session.close()


@pytest.mark.asyncio
async def test_card_trade_choose_card(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.SELECT_CARD_TO_TRADE, current_turn=1, player_in_action=None)
    players = [PlayerFactory(id=i, game_id=game.id) for i in range(1, 4)]
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=players[0].id, name="card-trade")
    my_cards = [CardFactory(id=i, game_id=game.id, owner=players[0].id, turn_discarded=None) for i in range(1,7)]
    selected_card_player = EventTableFactory(id=1, game_id=game.id, player_id=players[1].id, action="card_trade", turn_played=game.current_turn, target_card=None, target_player=2)


    session.add(game)
    session.add(playing_card)
    session.add_all(players)
    session.add_all(my_cards)
    session.add(selected_card_player)


    session.commit()

    # when

    # Jugador 1 juega la carta
    await card_trade(card=playing_card, session=session, target_cards=[my_cards[1].id], issuer_player=players[0])

    # then
    events = EventTableService().search(session=session,
                                        filterby={"game_id__eq": game.id,
                                                  "turn_played__eq": game.current_turn,
                                                  "action__eq": "card_trade",
                                                  "target_card__is_null": False})
    assert len(events) == 1
    session.refresh(game)
    assert game.status == GameStatus.SELECT_CARD_TO_TRADE
    assert game.player_in_action is None
    session.close()

@pytest.mark.asyncio
async def test_card_trade_cards(session, mocker):
    # given
    game = GameFactory(id=1, status=GameStatus.SELECT_CARD_TO_TRADE, current_turn=1, player_in_action=None)
    players = [PlayerFactory(id=i, game_id=game.id) for i in range(1, 4)]
    playing_card = CardFactory(id=0, game_id=game.id, turn_discarded=None, owner=players[0].id, name="card-trade")
    my_cards = [CardFactory(id=i, game_id=game.id, owner=players[0].id, turn_discarded=None) for i in range(1,7)]
    other_player_card = CardFactory(id=10, game_id=game.id, owner=players[1].id, turn_discarded=None)
    selected_card_player = EventTableFactory(id=1, game_id=game.id, player_id=players[1].id, action="card_trade", turn_played=game.current_turn, target_card=other_player_card.id, target_player=None)
    first_event = EventTableFactory(id=2, game_id=game.id, player_id=players[1].id, action="card_trade", turn_played=game.current_turn, target_card=None, target_player=2)

    session.add(game)
    session.add(playing_card)
    session.add_all(players)
    session.add_all(my_cards)
    session.add(other_player_card)
    session.add(selected_card_player)
    session.add(first_event)

    session.commit()

    # when

    # Jugador 1 juega la carta
    await card_trade(card=playing_card, session=session, target_cards=[my_cards[1].id], issuer_player=players[0])

    # then
    events = EventTableService().search(session=session,
                                        filterby={"game_id__eq": game.id,
                                                  "turn_played__eq": game.current_turn,
                                                  "action__eq": "card_trade",
                                                  "target_card__is_null": False})
    assert len(events) == 2
    session.refresh(game)
    assert game.player_in_action is None
    session.refresh(other_player_card)
    assert other_player_card.owner == players[0].id
    session.refresh(my_cards[0])
    assert my_cards[1].owner == players[1].id
    session.close()