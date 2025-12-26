import pytest
from sqlmodel import SQLModel, create_engine, Session, select
from unittest.mock import AsyncMock

from app.models.card import Card, CardType
from app.models.game import Game, GameStatus
from app.services.card import CardService
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
    return CardService()


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


def insert_card(session, card_id=1, game_id=1, owner=None, card_type=CardType.EVENT):
    card = CardFactory(
        id=card_id,
        game_id=game_id,
        owner=owner,
        name=f"card-{card_id}",
        content="content",
        card_type=card_type,
    )
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


@pytest.mark.asyncio
async def test_create_card(mocker, session, service):
    game = insert_game(session, game_id=1, status=GameStatus.TURN_START)
    mock_notify = mocker.patch("app.services.card.notify_game_players", new=AsyncMock())

    card = CardFactory(
        id=10,
        game_id=game.id,
        owner=None,
        name="new-card",
        content="body",
        card_type=CardType.EVENT,
    )

    data = card.model_dump()

    created = await service.create(session, data)

    assert created.id == 10
    stored = session.exec(select(Card).where(Card.id == created.id)).first()
    assert stored is not None
    mock_notify.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_card_bulk(mocker, session, service):
    game = insert_game(session, game_id=1, status=GameStatus.TURN_START)
    mock_notify = mocker.patch("app.services.card.notify_game_players", new=AsyncMock())

    cards = [CardFactory(
        id=10 +  i,
        game_id=game.id,
        owner=None,
        name="new-card",
        content="body",
        card_type=CardType.EVENT,
    ) for i in range(3)]

    data = [c.model_dump() for c in cards]

    created = await service.create_bulk(session, data)

    assert len(created) == 3
    assert all(c.id for c in created)
    mock_notify.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_card(mocker, session, service):
    game = insert_game(session, game_id=2, status=GameStatus.TURN_START)

    card = insert_card(session, card_id=11, game_id=game.id)
    mock_notify = mocker.patch("app.services.card.notify_game_players", new=AsyncMock())

    updated = await service.update(session, card.id, {"turn_discarded": 3})

    assert updated.turn_discarded == 3
    mock_notify.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_card_returns_none_when_missing(mocker, session, service):
    mock_notify = mocker.patch("app.services.card.notify_game_players", new=AsyncMock())

    result = await service.update(session, 999, {"turn_discarded": 4})

    assert result is None
    mock_notify.assert_not_called()


@pytest.mark.asyncio
async def test_bulk_update_success(mocker, session, service):
    game = insert_game(session, game_id=3, status=GameStatus.TURN_START)

    card_one = insert_card(session, card_id=20, game_id=game.id)
    card_two = insert_card(session, card_id=21, game_id=game.id)
    mock_notify = mocker.patch("app.services.card.notify_game_players", new=AsyncMock())

    data = [
        {"owner": 5, "turn_discarded": 1},
        {"owner": 6, "turn_discarded": 2},
    ]
    result = await service.bulk_update(session, [card_one.id, card_two.id], data)

    assert len(result) == 2
    assert result[0].owner == 5
    assert result[1].turn_discarded == 2
    mock_notify.assert_awaited_once()


@pytest.mark.asyncio
async def test_bulk_update_returns_none_when_card_missing(mocker, session, service):
    game = insert_game(session, game_id=4, status=GameStatus.TURN_START)

    card = insert_card(session, card_id=30, game_id=game.id)
    mock_notify = mocker.patch("app.services.card.notify_game_players", new=AsyncMock())

    result = await service.bulk_update(session, [card.id, 999], [{"owner": 2}, {"owner": 3}])

    assert result is None
    mock_notify.assert_not_called()


@pytest.mark.asyncio
async def test_delete_card_and_removes(mocker, session, service):
    game = insert_game(session, game_id=5, status=GameStatus.TURN_START)

    card = insert_card(session, card_id=40, game_id=game.id)
    mock_notify = mocker.patch("app.services.card.notify_game_players", new=AsyncMock())

    deleted_id = await service.delete(session, card.id)

    assert deleted_id == card.id
    assert session.get(Card, card.id) is None
    mock_notify.assert_awaited_once()
