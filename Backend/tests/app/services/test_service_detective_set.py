import pytest
from sqlmodel import SQLModel, create_engine, Session, select
from unittest.mock import AsyncMock, MagicMock

from app.models.detective_set import DetectiveSet
from app.models.card import Card, CardType
from app.models.game import Game, GameStatus
from app.services.detective_set import DetectiveSetService, CreateDetectiveSet, set_next_game_status
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
def fake_card():
    return CardFactory(id=1, game_id=10, owner=5, card_type=CardType.DETECTIVE)


@pytest.fixture
def fake_set(session):
    ds = DetectiveSet(id=1, owner=5, turn_played=2,game_id=1)
    session.add(ds)
    session.commit()
    session.refresh(ds)
    return ds


@pytest.fixture
def service():
    return DetectiveSetService()


@pytest.mark.asyncio
async def test_read_found(session, service, fake_set):
    result = await service.read(session, fake_set.id)
    assert result is not None
    assert result.id == fake_set.id


@pytest.mark.asyncio
async def test_read_not_found(session, service):
    result = await service.read(session, 999)
    assert result is None


@pytest.mark.asyncio
async def test_create_ok(mocker, session, service, fake_card):
    mock_card_service = mocker.patch(
        "app.services.detective_set.CardService", return_value=AsyncMock()
    )
    instance = mock_card_service.return_value
    instance.read = MagicMock()
    instance.read.side_effect = [fake_card, fake_card]

    mock_notify = mocker.patch("app.services.detective_set.notify_game_players", new=AsyncMock())

    data = CreateDetectiveSet(detectives=[1], owner=5, turn_played=2,game_id=1)
    result = await service.create(session, data)

    assert result.id is not None
    instance.read.assert_called()
    mock_notify.assert_called()
    assert session.exec(select(DetectiveSet)).first() is not None


@pytest.mark.asyncio
async def test_create_no_valid_cards(mocker, session, service):
    mock_card_service = mocker.patch(
        "app.services.detective_set.CardService", return_value=AsyncMock()
    )
    instance = mock_card_service.return_value
    instance.read = MagicMock()
    instance.read.return_value = None

    mock_notify = mocker.patch("app.services.detective_set.notify_game_players", new=AsyncMock())

    data = CreateDetectiveSet(detectives=[99], owner=5,turn_played=3,game_id=1)
    result = await service.create(session, data)

    assert isinstance(result, DetectiveSet)
    mock_notify.assert_not_called()


@pytest.mark.asyncio
async def test_update_found(mocker, session, service, fake_set, fake_card):
    fake_set.detectives = [fake_card]
    session.add(fake_card)
    session.commit()


    mock_notify = mocker.patch("app.services.detective_set.notify_game_players", new=AsyncMock())

    updated = await service.update(session, {"owner": 99, "turn_played":2,"detectives":fake_card}, fake_set.id)
    assert updated.owner == 99
    assert updated.turn_played == 2
    mock_notify.assert_called()


@pytest.mark.asyncio
async def test_update_not_found(mocker, session, service):
    mocker.patch("app.services.detective_set.notify_game_players", new=AsyncMock())
    result = await service.update(session, {"owner": 88}, 999)
    assert result is None

@pytest.mark.asyncio
async def test_delete_found(mocker, session, service, fake_set, fake_card):
    fake_set.detectives = [fake_card]
    session.add(fake_card)
    session.commit()

    mock_notify = mocker.patch("app.services.detective_set.notify_game_players", new=AsyncMock())

    result = await service.delete(session, fake_set.id)
    assert result == fake_set.id
    mock_notify.assert_called()
    assert session.exec(select(DetectiveSet)).first() is None


@pytest.mark.asyncio
async def test_delete_not_found(mocker, session, service):
    mocker.patch("app.services.detective_set.notify_game_players", new=AsyncMock())
    result = await service.delete(session, 999)
    assert result is None


def _build_detective_set_with_name(name: str) -> DetectiveSet:
    detective_card = Card(
        id=1,
        game_id=1,
        owner=1,
        name=name,
        content="detective-card",
        card_type=CardType.DETECTIVE,
    )
    return DetectiveSet(id=1, owner=1, turn_played=1, game_id=1, detectives=[detective_card])


def _build_game(game_id: int = 1) -> Game:
    return Game(id=game_id, name="test-game", status=GameStatus.WAITING)


def test_set_next_game_status_parker_pyne_without_revealed_secrets(mocker, session):
    detective_set = _build_detective_set_with_name("parker-pyne")
    game = _build_game()
    mock_secret_search = mocker.patch(
        "app.services.detective_set.SecretService.search", return_value=[]
    )

    result = set_next_game_status(detective_set, session, game)

    assert result == GameStatus.FINALIZE_TURN
    mock_secret_search.assert_called_once_with(
        session=session, filterby={"revealed__eq": True, "game_id__eq": game.id}
    )


def test_set_next_game_status_parker_pyne_with_revealed_secrets(mocker, session):
    detective_set = _build_detective_set_with_name("parker-pyne")
    game = _build_game()
    mock_secret_search = mocker.patch(
        "app.services.detective_set.SecretService.search", return_value=[object()]
    )

    result = set_next_game_status(detective_set, session, game)

    assert result == GameStatus.WAITING_FOR_CHOOSE_SECRET
    mock_secret_search.assert_called_once_with(
        session=session, filterby={"revealed__eq": True, "game_id__eq": game.id}
    )
