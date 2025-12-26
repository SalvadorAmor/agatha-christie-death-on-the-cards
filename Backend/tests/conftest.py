from datetime import datetime, UTC
from typing import Optional

import pytest
from factory import LazyAttribute
from factory.fuzzy import FuzzyInteger, FuzzyText, FuzzyDateTime
from starlette.testclient import TestClient

from app.controllers.game import CreateGameDTO, UpdateGameDTO, GameWithPlayerDTO
from app.controllers.player import CreatePlayerDTO
from app.main import base_app
import factory
import random

from app.models.event_table import EventTable
from app.models.game import Game, GameStatus
from app.models.player import Player
from app.services.game import GameFilter
from app.models.card import Card, CardType
from app.controllers.card import UpdateCardDTO

class GameFactory(factory.Factory):
    class Meta:
        model = Game

    id: int = FuzzyInteger(1, 1000)
    status: GameStatus = LazyAttribute(lambda o: random.choice([GameStatus.WAITING, GameStatus.STARTED, GameStatus.FINALIZED]))
    owner: int = FuzzyInteger(1,1000)
    name: str = FuzzyText(length=12, prefix="game_")
    min_players: int = 2
    max_players: int = FuzzyInteger(2, 6)
    current_turn: int = FuzzyInteger(1, 50)
    timestamp:datetime = datetime.now()
    player_in_action:Optional[int] = None
    password: Optional[str] = FuzzyText(length=12)

class CreateGameDTOFactory(factory.Factory):
    class Meta:
        model = CreateGameDTO
    game_name: str = FuzzyText(length=12, prefix="game_")
    password: Optional[str] = FuzzyText(length=12)
    min_players: Optional[int] = FuzzyInteger(2, 6)
    max_players: int = FuzzyInteger(2, 6)
    player_name: str = factory.Faker('first_name')
    avatar: str = FuzzyText(length=60)
    birthday: datetime = FuzzyDateTime(start_dt=datetime(year=2000, month=1, day=1, tzinfo=UTC), end_dt=datetime(year=2024, month=1, day=1, tzinfo=UTC))

class UpdateGameDTOFactory(factory.Factory):
    class Meta:
        model = UpdateGameDTO
    status: Optional[GameStatus] = None
    token: str = FuzzyText(length=12)
    current_turn: Optional[int] = None

class CardFactory(factory.Factory):
    class Meta:
        model = Card
    id: int = FuzzyInteger(1,1000)
    game_id: int = FuzzyInteger(1, 1000)
    owner: Optional[int] = None
    name: str = FuzzyText(length=12, prefix="card_")
    content: str = ""
    turn_discarded: Optional[int] = None
    discarded_order: Optional[int] = None
    turn_played: Optional[int] = None
    set_id: Optional[int] = None
    card_type: CardType = LazyAttribute(lambda o: random.choice([CardType.INSTANT, CardType.DETECTIVE, CardType.DEVIOUS, CardType.EVENT]))
    pile_order: int = FuzzyInteger(1,100)


class UpdateCardDTOFactory(factory.Factory):
    class Meta:
        model = UpdateCardDTO
    turn_discarded:Optional[int] = FuzzyInteger(1, 100)
    owner:Optional[int] = FuzzyInteger(1, 100)
    token:str = FuzzyText(length=12)
    
class PlayerFactory(factory.Factory):
    class Meta:
            model = Player

    id: int = FuzzyInteger(1,1000)
    game_id: int = FuzzyInteger(1,1000)
    name:str = FuzzyText(length=20, prefix="player_")
    date_of_birth: datetime = FuzzyDateTime(start_dt=datetime(year=2000, month=1, day=1, tzinfo=UTC),
                                            end_dt=datetime(year=2024, month=1, day=1, tzinfo=UTC))
    avatar: str = FuzzyText(length=20, prefix="avatar_")
    social_disgrace:bool = False
    token: str = FuzzyText(length=20, prefix="token_")
    position: int = FuzzyInteger(1,6)

class EventTableFactory(factory.Factory):
    class Meta:
        model = EventTable

    id: int = FuzzyInteger(1, 1000)
    game_id: int = FuzzyInteger(1, 1000)
    action: str = FuzzyText(length=15, prefix="action_")
    turn_played: int = FuzzyInteger(1, 50)
    player_id: int = FuzzyInteger(1, 1000)
    target_player: Optional[int] = None
    target_set: Optional[int] = None
    target_card: Optional[int] = None
    target_secret: Optional[int] = None
    completed_action: bool = False

class CreatePlayerDTOFactory(factory.Factory):
    class Meta:
            model = CreatePlayerDTO
    player_name: str = FuzzyText(length=6, prefix="p_")
    player_date_of_birth: datetime = FuzzyDateTime(start_dt=datetime(year=2000, month=1, day=1, tzinfo=UTC),
                                                    end_dt=datetime(year=2024, month=1, day=1, tzinfo=UTC))
    avatar: str = FuzzyText(length=20, prefix="avatar_")

class GameWithPlayerFactory(factory.Factory):
    class Meta:
        model = GameWithPlayerDTO
    game: Game = factory.SubFactory(GameFactory)
    player: Player = factory.SubFactory(PlayerFactory)


class EventTableFactory(factory.Factory):
    class Meta:
        model = EventTable

    id = factory.Sequence(lambda n: n + 1)
    game = factory.SubFactory(GameFactory)
    game_id = factory.SelfAttribute("game.id")
    player = factory.SubFactory(PlayerFactory)
    player_id = factory.SelfAttribute("player.id")

    action = "point_your_suspicions"
    turn_played = 1

    target_player = factory.LazyAttribute(lambda _: None)
    target_set = factory.LazyAttribute(lambda _: None)
    target_card = factory.LazyAttribute(lambda _: None)
    target_secret = factory.LazyAttribute(lambda _: None)

    completed_action = False


@pytest.fixture
def test_client():
    return TestClient(app=base_app)
