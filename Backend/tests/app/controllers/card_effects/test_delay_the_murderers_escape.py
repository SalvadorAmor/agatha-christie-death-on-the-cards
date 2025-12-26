import random
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from more_itertools.more import side_effect
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session

from app.controllers.card_effects.delay_the_murderers_escape import delay_the_murderers_escape
from app.models.game import GameStatus
from app.services.card import CardService
from app.services.game import GameService
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
async def test_delay_the_murderers_escape_canceled_by_not_so_fast(mocker):
    mocked_game = GameFactory(status=GameStatus.TURN_START)
    playing_card = CardFactory(game_id=mocked_game.id)
    mocked_player = PlayerFactory(id = playing_card.owner, game_id = mocked_game.id)

    mocker.patch('app.controllers.card_effects.delay_the_murderers_escape.GameService.read', return_value=mocked_game)
    mocker.patch('app.controllers.card_effects.delay_the_murderers_escape.not_so_fast_status', return_value=True)
    mock_card_delete = mocker.patch('app.controllers.card_effects.delay_the_murderers_escape.CardService.delete', new_callable=AsyncMock)
    mock_game_update = mocker.patch('app.controllers.card_effects.delay_the_murderers_escape.GameService.update', new_callable=AsyncMock)
    mock_card_search = mocker.patch('app.controllers.card_effects.delay_the_murderers_escape.CardService.search')
    mock_player_read = mocker.patch('app.controllers.card_effects.delay_the_murderers_escape.PlayerService.read', return_vale=mocked_player)
    mock_log_create = mocker.patch('app.controllers.card_effects.delay_the_murderers_escape.ChatService.create')
    mocker.patch('app.controllers.card_effects.delay_the_murderers_escape.CardService.update',return_value=playing_card)
    await delay_the_murderers_escape(card=playing_card, session=None)

    mock_player_read.assert_called_once_with(session=None, oid=playing_card.owner)
    assert mock_log_create.call_count == 2
    mock_card_delete.assert_awaited_once_with(session=None, oid=playing_card.id)
    mock_game_update.assert_awaited_once_with(
        session=None,
        oid=playing_card.game_id,
        data={'status': GameStatus.FINALIZE_TURN, 'player_in_action': None},
    )
    mock_card_search.assert_not_called()



@pytest.mark.asyncio
async def test_delay_the_murderers_escape_play_card(session, mocker):
    # given
    mocked_game = GameFactory(status=GameStatus.TURN_START)
    playing_card = CardFactory(id=0, game_id=mocked_game.id, turn_discarded=None, owner=1, name="delay-the-murderers-escape")
    mocked_player = PlayerFactory(id = playing_card.owner, game_id = mocked_game.id)
    current_cards = [CardFactory(id=i+1,game_id=mocked_game.id, turn_discarded=None, owner=None, pile_order=i) for i in range(0, 20)]

    mock_notify_game_players = mocker.patch("app.controllers.card_effects.delay_the_murderers_escape.notify_game_players")
    mock_not_so_fast = mocker.patch("app.controllers.card_effects.delay_the_murderers_escape.not_so_fast_status", return_value=False)
    mock_player_read = mocker.patch('app.controllers.card_effects.delay_the_murderers_escape.PlayerService.read', return_vale=mocked_player)
    mock_log_create = mocker.patch('app.controllers.card_effects.delay_the_murderers_escape.ChatService.create')

    session.add(mocked_game)
    session.add(playing_card)
    session.add_all(current_cards)

    session.commit()

    # when
    await delay_the_murderers_escape(card=playing_card, session=session)

    # then
    session.refresh(mocked_game)
    assert mocked_game.status == GameStatus.WAITING_FOR_ORDER_DISCARD
    result_pile = CardService().search(session=session, filterby={"turn_discarded__is_null": True, "owner__is_null": True}, sortby="pile_order__desc")
    assert len(result_pile) == 20
    session.close()

@pytest.mark.asyncio
@pytest.mark.parametrize("discarded_cards_count", [0, 5, 7])
async def test_delay_the_murderers_escape_empty_order(session, mocker, discarded_cards_count):
    # given
    mocked_game = GameFactory(status=GameStatus.WAITING_FOR_ORDER_DISCARD)
    playing_card = CardFactory(id=0, game_id=mocked_game.id, turn_discarded=None, owner=1, name="delay-the-murderers-escape")
    current_cards = [CardFactory(id=i+1,game_id=mocked_game.id, turn_discarded=None, owner=None, pile_order=i) for i in range(0, 20)]
    discarded_cards = [CardFactory(id=i+21, game_id=mocked_game.id, discarded_order=i) for i in range(0, discarded_cards_count)]

    mock_notify_game_players = mocker.patch("app.controllers.card_effects.delay_the_murderers_escape.notify_game_players")
    mock_not_so_fast = mocker.patch("app.controllers.card_effects.delay_the_murderers_escape.not_so_fast_status", return_value=False)

    session.add(mocked_game)
    session.add(playing_card)
    session.add_all(discarded_cards)
    session.add_all(current_cards)

    session.commit()

    # when
    with pytest.raises(HTTPException):
        await delay_the_murderers_escape(card=playing_card, session=session)

        # then
        result_pile = CardService().search(session=session, filterby={"turn_discarded__is_null": True, "owner__is_null": True}, sortby="pile_order__desc")
        assert len(result_pile) == 20
        session.close()

@pytest.mark.asyncio
@pytest.mark.parametrize("discarded_cards_count", [3, 5, 7])
async def test_delay_the_murderers_escape(session, mocker, discarded_cards_count):
    # given
    mocked_game = GameFactory(status=GameStatus.WAITING_FOR_ORDER_DISCARD)
    playing_card = CardFactory(id=0, game_id=mocked_game.id, turn_discarded=None, owner=1, name="delay-the-murderers-escape")
    mocked_player = PlayerFactory(id = playing_card.owner, game_id = mocked_game.id)
    current_cards = [CardFactory(id=i+1,game_id=mocked_game.id, turn_discarded=None, owner=None, pile_order=i) for i in range(0, 20)]
    discarded_cards = [CardFactory(id=i+21, game_id=mocked_game.id, discarded_order=i) for i in range(0, discarded_cards_count)]

    mock_notify_game_players = mocker.patch("app.controllers.card_effects.delay_the_murderers_escape.notify_game_players")
    mocker.patch('app.controllers.card_effects.delay_the_murderers_escape.not_so_fast_status', return_value=False)
    mock_log_create = mocker.patch('app.controllers.card_effects.delay_the_murderers_escape.ChatService.create')

    session.add(mocked_game)
    session.add(playing_card)
    session.add(mocked_player)
    session.add_all(discarded_cards)
    session.add_all(current_cards)

    session.commit()

    # when
    discarded_cards = CardService().search(session=session, filterby={"game_id__eq": mocked_game.id, "discarded_order__is_null": False})
    discarded_order = [dc.id for dc in discarded_cards]
    random.shuffle(discarded_order)
    await delay_the_murderers_escape(card=playing_card, session=session, target_cards=discarded_order)

    # then
    result_pile = CardService().search(session=session, filterby={"turn_discarded__is_null": True, "owner__is_null": True}, sortby="pile_order__desc")
    assert len(result_pile) == 20 + discarded_cards_count
    assert mock_log_create.call_count == 1
    if discarded_cards_count:
        mock_notify_game_players.assert_called()
    session.close()
