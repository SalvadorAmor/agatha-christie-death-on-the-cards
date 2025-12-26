from sqlmodel import SQLModel, Field
from typing import Optional

class Chat(SQLModel, table = True):
    id: int = Field(primary_key= True)
    game_id: int = Field(foreign_key="game.id")
    owner_name: Optional[str] = Field(default=None)
    content: str
    timestamp: str