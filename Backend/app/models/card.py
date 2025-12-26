from sqlmodel import SQLModel, Field, Relationship
from enum import Enum
#from app.models.game import Game
from typing import Optional

class CardType(str, Enum):
    EVENT = "event"
    DETECTIVE = "detective"
    DEVIOUS = "devious"
    INSTANT = "instant"

class Card(SQLModel, table=True):
    id: int = Field(primary_key=True)
    game_id: int = Field(foreign_key="game.id")
    owner: Optional[int] = Field(foreign_key="player.id", default=None)
    name: str = Field(max_digits=20)
    content: str = Field(max_digits=100)
    turn_discarded: Optional[int] = Field(default=None)
    discarded_order: Optional[int] = Field(default=None)
    turn_played: Optional[int] = Field(default=None)
    card_type: CardType
    pile_order: int
    set_id: Optional[int] = Field(foreign_key="detectiveset.id", default=None)

class PublicCard(SQLModel):
    id: int
    name: str
    owner: Optional[int]
    content: str
    turn_discarded: Optional[int]
    discarded_order: Optional[int]
    turn_played: Optional[int]
    card_type: CardType
    set_id: Optional[int]