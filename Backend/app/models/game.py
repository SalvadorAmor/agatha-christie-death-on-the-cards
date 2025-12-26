from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship

from app.models.player import Player


class GameStatus(str, Enum):
    WAITING = "waiting"
    STARTED = "started"
    TURN_START = "turn_start"
    WAITING_FOR_CHOOSE_PLAYER = "waiting_for_choose_player"
    WAITING_FOR_CHOOSE_DISCARDED = "waiting_for_choose_discarded"
    WAITING_FOR_CHOOSE_PLAYER_AND_SECRET = "waiting_for_choose_player_and_secret"
    WAITING_FOR_CHOOSE_SECRET = "waiting_for_choose_secret"
    WAITING_FOR_POINT_YOUR_SUSPICIONS = "waiting_for_point_your_suspicions"
    WAITING_FOR_CHOOSE_SECRET_PYS = "waiting_for_choose_secret_pys"
    WAITING_FOR_CHOOSE_SET = "waiting_for_choose_set"
    WAITING_FOR_CANCEL_ACTION = "waiting_for_cancel_action"
    WAITING_FOR_ORDER_DISCARD = "waiting_for_order_discard"
    WAITING_TO_CHOOSE_DIRECTION = "waiting_to_choose_direction"
    SELECT_CARD_TO_TRADE = "select_card_to_trade"
    FINALIZE_TURN = "finalize_turn"
    FINALIZE_TURN_DRAFT = "finalize_turn_draft"
    FINALIZED = "finalized"

class PublicGame(SQLModel):
    id: int = Field(primary_key=True)
    status: GameStatus = Field(default=GameStatus.WAITING)
    name: str = Field(max_digits=20)
    min_players: int = Field(default=2)
    max_players: int = Field(default=6)
    current_turn: int = Field(default=0)
    owner: Optional[int] = Field(foreign_key="player.id")
    timestamp: Optional[datetime] = Field(default=None)
    player_in_action: Optional[int] = Field(foreign_key="player.id")

class Game(PublicGame, table=True):
    password: Optional[str] = Field(default=None)