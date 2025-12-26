from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field




class Player(SQLModel, table=True):
    id:int = Field(primary_key=True)
    game_id:Optional[int] = Field(foreign_key="game.id",default=None)
    name:str = Field(max_digits=20)
    date_of_birth:datetime
    avatar:str
    social_disgrace:bool = Field(default=False)
    token:Optional[str] = Field(default=None, unique=True, index=True)
    position:Optional[int] = Field(default=None)

class PublicPlayer(SQLModel):
    id: int
    game_id: int
    name: str
    social_disgrace:bool
    date_of_birth: datetime
    avatar: str
    position:Optional[int]
