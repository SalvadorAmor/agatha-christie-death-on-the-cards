from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from sqlalchemy.orm import joinedload
import logging

from app.models.detective_set import DetectiveSet
from app.models.card import Card, CardType
from app.models.game import GameStatus, Game
from app.services.base import BaseService
from app.services.card import CardService
from app.services.secret import SecretService
from app.models.websocket import WebsocketMessage, notify_game_players

_logger = logging.getLogger(__name__)


class CreateDetectiveSet(BaseModel):
    detectives: List[int]
    owner: int
    game_id:int
    turn_played:int


class DetectiveSetFilter(BaseModel):
    id__eq: Optional[int] = None
    game_id__eq: Optional[int] = None
    owner__eq: Optional[int] = None
    turn_played__eq: Optional[int] = None


class DetectiveSetService(BaseService[DetectiveSet]):
    _metaclass = DetectiveSet

    async def read(self, session: Session, id: int) -> Optional[DetectiveSet]:
        stmt = select(DetectiveSet).where(DetectiveSet.id == id).options(joinedload(DetectiveSet.detectives))
        result = session.exec(stmt).first()
        return result

    async def create(self, session: Session, data: CreateDetectiveSet) -> DetectiveSet:
        detective_set = DetectiveSet(owner=data.owner, turn_played=data.turn_played, game_id=data.game_id)
        session.add(detective_set)
        session.commit()
        session.refresh(detective_set)

        card_service = CardService()
        for cid in data.detectives:
            card = card_service.read(session, cid)
            if card and card.card_type == CardType.DETECTIVE:
                card.set_id = detective_set.id  # se asume que Card tiene set_id
                session.add(card)

        session.commit()
        session.refresh(detective_set)

        # Notificación vía websocket a todos los jugadores del juego de las cartas
        for card_id in data.detectives:
            card = card_service.read(session, card_id)
            if card:
                await notify_game_players(
                    card.game_id,
                    WebsocketMessage(model="detective_set", action="create", data=detective_set.model_dump(), dest_game=card.game_id)
                )

        return detective_set

    async def update(self, session: Session, data: Dict[str, Any], id: int) -> Optional[DetectiveSet]:
        detective_set = await self.read(session, id)
        if not detective_set:
            return None

        if "owner" in data:
            detective_set.owner = data["owner"]

        if "turn_played" in data:
            detective_set.turn_played = data["turn_played"]

        if "detectives" in data:
            detective = data["detectives"]
            detective.set_id = id
            detective_set.detectives.append(detective)

        session.add(detective_set)
        session.commit()
        session.refresh(detective_set)

        for card in detective_set.detectives:
            await notify_game_players(
                card.game_id,
                WebsocketMessage(model="detective_set", action="update", data=detective_set.model_dump(), dest_game=card.game_id)
            )

        return detective_set

    async def delete(self, session: Session, id: int) -> Optional[int]:
        detective_set = await self.read(session, id)
        if not detective_set:
            return None

        session.delete(detective_set)
        session.commit()

        for card in detective_set.detectives:
            await notify_game_players(
                card.game_id,
                WebsocketMessage(model="detective_set", action="delete", data=detective_set.model_dump(), dest_game=card.game_id)
            )

        return id

DETECTIVES_CHOOSE_PLAYERS = ["mr-satterthwaite","lady-eileen-bundle-brent","tuppence-beresford","tommy-beresford"]

def set_have_detectives(d_set:DetectiveSet,d_names:List[str]):
    return any(d.name in d_names for d in d_set.detectives)

def set_next_game_status(detective_set:DetectiveSet, session: Session, game: Game):
    if set_have_detectives(detective_set, DETECTIVES_CHOOSE_PLAYERS):
        return GameStatus.WAITING_FOR_CHOOSE_PLAYER
    elif set_have_detectives(detective_set, ["parker-pyne"]):
        secret_service = SecretService()
        secrets = secret_service.search(session=session, filterby={"revealed__eq": True, "game_id__eq": game.id}) 
        return GameStatus.FINALIZE_TURN if len(secrets) == 0 else GameStatus.WAITING_FOR_CHOOSE_SECRET 
    else:    
        return GameStatus.WAITING_FOR_CHOOSE_SECRET
