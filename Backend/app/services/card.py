from pydantic import BaseModel
from sqlmodel import Session

from app.models.card import CardType, Card
from app.models.websocket import WebsocketMessage, notify_game_players
from app.services.base import BaseService, T
from typing import Optional, List
import logging

_logger = logging.getLogger(__name__)

class CreateCard(BaseModel):
    game_id: int
    owner: Optional[int] = None
    name: str
    content: str
    card_type: CardType
    pile_order: int

class CardFilter(BaseModel):
    id__eq: Optional[int] = None
    game_id__eq: Optional[int] = None
    owner__eq: Optional[int] = None
    owner__is_null: Optional[bool] = None
    card_type__in: Optional[List[CardType]] = None
    turn_discarded__eq: Optional[int] = None
    turn_discarded__is_null: Optional[bool] = None
    set_id__eq: Optional[int] = None
    set_id__is_null: Optional[bool] = None
    discarded_order__is_null: Optional[bool] = None
    turn_played__eq: Optional[int] = None
    turn_played__is_null: Optional[bool] = None
    content__eq:Optional[str] = None

class CardService(BaseService[Card]):
    _metaclass = Card

    async def create(self, session, data: dict) -> Optional[Card]:
        result = await super().create(session, data)
        if result:
            session.refresh(result)
            await notify_game_players(result.game_id, WebsocketMessage(model="card", action="create", data=result.model_dump(), dest_game=result.game_id, dest_user=None))
        return result

    async def create_bulk(self, session, data: List[dict]) -> List[Card]:
        objs = [self._metaclass(**item) for item in data]
        session.add_all(objs)
        session.commit()
        for obj in objs:
            session.refresh(obj)
        await notify_game_players(objs[0].game_id, WebsocketMessage(model="card", action="create", data=[o.model_dump() for o in objs], dest_game=objs[0].game_id, dest_user=None))
        return objs

    async def bulk_update(self, session: Session, oids: List[int], data:List[dict]) -> Optional[List[Card]]:
        updated_objects = []

        for i, oid in enumerate(oids):
            updated_object = session.get(self._metaclass, oid)
            if not updated_object:
                return None
            for k, v in data[i].items():
                setattr(updated_object, k, v)
            updated_objects.append(updated_object)

        session.commit()

        for obj in updated_objects:
            session.refresh(obj)

        if updated_objects:
            await notify_game_players(updated_objects[0].game_id, WebsocketMessage(model="card", action="update",
                                                                                   data=[c.model_dump() for c in updated_objects],
                                                                                   dest_game=updated_objects[0].game_id,
                                                                                   dest_user=None))
        return updated_objects

    def search(self, session: Session, filterby: dict, sortby: Optional[str] = "pile_order__desc", limit: Optional[int] = None, offset: Optional[int] = None) -> List[Card]:
        return super().search(session, filterby, sortby, limit, offset)


    async def update(self, session, oid: int, data: dict) -> Optional[Card]:
        result = await super().update(session, oid, data)
        if result:
            session.refresh(result)
            await notify_game_players(result.game_id, WebsocketMessage(model="card", action="update", data=result.model_dump(), dest_game=result.game_id, dest_user=None))
        return result

    async def delete(self, session, oid: int) -> Optional[int]:
        model_data = session.get(Card, oid).model_dump()
        result = await super().delete(session, oid)
        if model_data and result:
            await notify_game_players(model_data['game_id'], WebsocketMessage(model="card", action="delete", data=model_data, dest_game=model_data['game_id'], dest_user=None))
        return result

def get_new_discarded_order(session: Session, game_id: int):
    card_service = CardService()
    last_discarded_card = card_service.search(session=session,
                                            filterby={"game_id__eq": game_id, 'discarded_order__is_null': False},
                                            sortby="discarded_order__desc", limit=1)

    new_discarded_order = last_discarded_card[0].discarded_order + 1 if last_discarded_card else 0
    return new_discarded_order