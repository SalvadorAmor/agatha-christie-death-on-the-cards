from sqlmodel import SQLModel, Field, Relationship
from enum import Enum

class SecretType(str, Enum):
    MURDERER = "murderer"
    ACCOMPLICE = "accomplice"
    OTHER = "other"


class Secret(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="game.id")
    owner: int = Field(foreign_key="player.id")
    name: str = Field(max_length=40)
    content: str = Field(max_length=100)
    revealed: bool = Field(default=False)
    type: SecretType
    