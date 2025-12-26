import pytest
from sqlmodel import SQLModel, create_engine, Session, select
from unittest.mock import AsyncMock

from app.models.secret import Secret, SecretType
from app.services.secret import SecretService


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
    return SecretService()


def insert_secret(session, secret_id=1, game_id=1, owner=1, revealed=False):
    secret = Secret(
        id=secret_id,
        game_id=game_id,
        owner=owner,
        name=f"secret-{secret_id}",
        content="content",
        revealed=revealed,
        type=SecretType.OTHER,
    )
    session.add(secret)
    session.commit()
    session.refresh(secret)
    return secret


@pytest.mark.asyncio
async def test_create_secret(mocker, session, service):
    mock_notify = mocker.patch("app.services.secret.notify_game_players", new=AsyncMock())

    secret = Secret(
        id=10,
        game_id=2,
        owner=5,
        name="new-secret",
        content="body",
        revealed=False,
        type=SecretType.OTHER,
    )

    data = secret.model_dump()

    created = await service.create(session, data)

    assert created.id == 10
    assert session.exec(select(Secret).where(Secret.id == created.id)).first() is not None
    mock_notify.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_bulk_secret(mocker, session, service):
    mock_notify = mocker.patch("app.services.secret.notify_game_players", new=AsyncMock())

    secret = [
        Secret(
            id=10 + i,
            game_id=2,
            owner=5,
            name="new-secret",
            content="body",
            revealed=False,
            type=SecretType.OTHER,
        ) for i in range(3)
    ]

    data = [s.model_dump() for s in secret]

    created = await service.create_bulk(session, data)

    assert len(created) == 3
    assert all(s.id for s in created)
    mock_notify.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_secret(mocker, session, service):
    secret = insert_secret(session, secret_id=20, game_id=3, owner=6, revealed=False)
    mock_notify = mocker.patch("app.services.secret.notify_game_players", new=AsyncMock())

    updated = await service.update(session, secret.id, {"revealed": True})

    assert updated.revealed is True
    mock_notify.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_secret_returns_none_when_missing(mocker, session, service):
    mock_notify = mocker.patch("app.services.secret.notify_game_players", new=AsyncMock())

    result = await service.update(session, 999, {"revealed": True})

    assert result is None
    mock_notify.assert_not_called()


@pytest.mark.asyncio
async def test_delete_secret_and_removes(mocker, session, service):
    secret = insert_secret(session, secret_id=30, game_id=4, owner=7, revealed=False)
    mock_notify = mocker.patch("app.services.secret.notify_game_players", new=AsyncMock())

    deleted_id = await service.delete(session, secret.id)

    assert deleted_id == secret.id
    assert session.get(Secret, secret.id) is None
    mock_notify.assert_awaited_once()
