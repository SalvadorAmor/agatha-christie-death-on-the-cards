from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship

from app.models.card import Card


class DetectiveSet(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner: int = Field(foreign_key="player.id")
    game_id: int = Field(foreign_key="game.id")
    turn_played: int
    detectives: List[Card] = Relationship(
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
        }
    )

class PublicDetectiveSet(SQLModel):
    id: int
    game_id:int
    owner: int
    turn_played: int
    detectives: List[Card] = []

