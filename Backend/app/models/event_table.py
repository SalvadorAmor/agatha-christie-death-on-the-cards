from typing import Optional
from sqlmodel import SQLModel, Field

class EventTable(SQLModel, table = True):
    id: int = Field(primary_key=True)
    game_id: int = Field(foreign_key="game.id")
    action: str
    turn_played: int
    player_id: Optional[int] = Field(foreign_key="player.id")
    target_player: Optional[int] = Field(default=None)
    target_set: Optional[int] = Field(default=None)
    target_card: Optional[int] = Field(default=None)
    target_secret: Optional[int] = Field(default=None)
    completed_action: bool = Field(default=False)
    

