from datetime import datetime, UTC

import pytest
from sqlmodel import SQLModel, create_engine, Session, select
from unittest.mock import AsyncMock

from app.models.chat import Chat
from app.models.player import Player
from app.services.chat import ChatService


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
    return ChatService()

@pytest.mark.asyncio
async def test_create_message(mocker, session, service):
    mock_notify_players = mocker.patch("app.services.chat.notify_game_players", new=AsyncMock())

    message_model = Chat(
            id=1,
            game_id=1,
            owner_name="jugador_1",
            content="hola",
            timestamp="2024-01-01T00:00:00Z",
            )

    data = message_model.model_dump()

    created = await service.create(session, data)

    assert created.id == 1
    assert session.exec(select(Chat).where(Chat.id == created.id)).first() is not None
    mock_notify_players.assert_called_once()
