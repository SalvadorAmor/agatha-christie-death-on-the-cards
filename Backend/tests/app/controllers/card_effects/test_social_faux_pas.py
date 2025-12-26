from fastapi import HTTPException
import pytest
from unittest.mock import AsyncMock

from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session

from app.controllers.card_effects.social_faux_pas import social_faux_pas
from app.models.card import CardType
from app.models.event_table import EventTable
from app.models.game import GameStatus
from app.models.secret import Secret, SecretType
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
async def test_social_faux_pas_card_not_in_play(session):
    game = GameFactory(id=1, status=GameStatus.WAITING_FOR_CHOOSE_SECRET, current_turn=2)
    card = CardFactory(
        id=10,
        game_id=game.id,
        name="social-faux-pas",
        turn_played=1,
        card_type=CardType.DEVIOUS,
    )

    session.add(game)
    session.add(card)
    session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await social_faux_pas(card=card, session=session, target_secrets=[1])

    assert exc_info.value.status_code == 400
    assert "devious" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_social_faux_pas_requires_secret_selection(session):
    game = GameFactory(id=2, status=GameStatus.WAITING_FOR_CHOOSE_SECRET, current_turn=3)
    card = CardFactory(
        id=11,
        game_id=game.id,
        name="social-faux-pas",
        turn_played=game.current_turn,
        card_type=CardType.DEVIOUS,
    )

    session.add(game)
    session.add(card)
    session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await social_faux_pas(card=card, session=session, target_secrets=[])

    assert exc_info.value.status_code == 412


@pytest.mark.asyncio
async def test_social_faux_pas_event_player_mismatch(session):
    player = PlayerFactory(id=20, game_id=1)
    game = GameFactory(
        id=player.game_id,
        status=GameStatus.WAITING_FOR_CHOOSE_SECRET,
        current_turn=4,
        player_in_action=999,
    )
    card = CardFactory(
        id=12,
        game_id=game.id,
        name="social-faux-pas",
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
        await social_faux_pas(card=card, session=session, target_secrets=[55])

    assert exc_info.value.status_code == 400
    assert "evento devious incorrecto" in exc_info.value.detail.lower()

@pytest.mark.asyncio
async def test_social_faux_pas_reveals_secret_and_finalizes_game(session, mocker):
    player = PlayerFactory(id=50, game_id=3)
    secret = Secret(
        id=70,
        game_id=player.game_id,
        owner=player.id,
        name="test-secret",
        content="content",
        type=SecretType.OTHER,
    )
    game = GameFactory(
        id=player.game_id,
        status=GameStatus.WAITING_FOR_CHOOSE_SECRET,
        current_turn=6,
        player_in_action=player.id,
    )
    card = CardFactory(
        id=14,
        game_id=game.id,
        name="social-faux-pas",
        owner=player.id,
        turn_played=game.current_turn,
        discarded_order=None,
        turn_discarded=None,
        card_type=CardType.DEVIOUS,
    )
    event = EventTable(
        id=32,
        game_id=game.id,
        action="card_trade",
        turn_played=game.current_turn,
        player_id=player.id,
        target_card=card.id,
        target_player=player.id,
        completed_action=True,
    )

    mock_chat_create = mocker.patch(
        "app.controllers.card_effects.social_faux_pas.ChatService.create", new_callable=AsyncMock
    )
    mock_reveal_secret = mocker.patch(
        "app.controllers.card_effects.social_faux_pas.reveal_secret", new_callable=AsyncMock
    )
    mock_reveal_secret.return_value = "game_finalized"
    mock_devious_detect = mocker.patch(
        "app.controllers.card_effects.social_faux_pas.devious_detect", new_callable=AsyncMock
    )

    session.add(game)
    session.add(player)
    session.add(card)
    session.add(event)
    session.add(secret)
    session.commit()

    result = await social_faux_pas(card=card, session=session, target_secrets=[secret.id])

    assert result == 200
    mock_reveal_secret.assert_awaited_once()
    mock_devious_detect.assert_not_awaited()
    assert mock_chat_create.await_count == 1

    session.refresh(card)
    assert card.turn_discarded == game.current_turn
    assert card.owner is None
    assert card.turn_played is None


@pytest.mark.asyncio
async def test_social_faux_pas_reveals_secret_and_triggers_devious_detect(session, mocker):
    player = PlayerFactory(id=60, game_id=4)
    secret = Secret(
        id=80,
        game_id=player.game_id,
        owner=player.id,
        name="test-secret",
        content="content",
        type=SecretType.OTHER,
    )
    game = GameFactory(
        id=player.game_id,
        status=GameStatus.WAITING_FOR_CHOOSE_SECRET,
        current_turn=7,
        player_in_action=player.id,
    )
    card = CardFactory(
        id=15,
        game_id=game.id,
        name="social-faux-pas",
        owner=player.id,
        turn_played=game.current_turn,
        discarded_order=None,
        turn_discarded=None,
        card_type=CardType.DEVIOUS,
    )
    event = EventTable(
        id=33,
        game_id=game.id,
        action="card_trade",
        turn_played=game.current_turn,
        player_id=player.id,
        target_card=card.id,
        target_player=player.id,
        completed_action=True,
    )

    mock_chat_create = mocker.patch(
        "app.controllers.card_effects.social_faux_pas.ChatService.create", new_callable=AsyncMock
    )
    mock_reveal_secret = mocker.patch(
        "app.controllers.card_effects.social_faux_pas.reveal_secret", new_callable=AsyncMock
    )
    mock_reveal_secret.return_value = "effect_applied"
    mock_devious_detect = mocker.patch(
        "app.controllers.card_effects.social_faux_pas.devious_detect", new_callable=AsyncMock
    )

    session.add(game)
    session.add(player)
    session.add(card)
    session.add(event)
    session.add(secret)
    session.commit()

    result = await social_faux_pas(card=card, session=session, target_secrets=[secret.id])

    assert result is None
    mock_reveal_secret.assert_awaited_once()
    secret_passed = mock_reveal_secret.await_args.kwargs["secret"]
    assert secret_passed.id == secret.id
    mock_devious_detect.assert_awaited_once()
    assert mock_chat_create.await_count == 1

    session.refresh(card)
    assert card.turn_discarded == game.current_turn
    assert card.owner is None
    assert card.turn_played is None
