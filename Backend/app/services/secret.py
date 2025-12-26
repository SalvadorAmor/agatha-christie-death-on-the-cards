from pydantic import BaseModel
from app.models.secret import SecretType, Secret
from app.models.websocket import WebsocketMessage, notify_game_players
from app.services.base import BaseService
from typing import Optional, List

class CreateSecret(BaseModel):
    game_id: int
    owner: Optional[int] = None
    name: str
    content: str
    revealed: bool
    type: SecretType
    
class SecretFilter(BaseModel):
    id__eq: Optional[int] = None
    game_id__eq: Optional[int] = None
    owner__eq: Optional[int] = None
    revealed__eq: Optional[bool] = None
    type__in: Optional[List[SecretType]] = None


class SecretService(BaseService[Secret]):
    _metaclass = Secret

    async def create(self, session, data: dict) -> Optional[Secret]:
        result = await super().create(session, data)
        if result:
            session.refresh(result)
            await notify_game_players(game_id=result.game_id, message=WebsocketMessage(model="secret", action="create", data=result.model_dump(), dest_game=result.game_id, dest_user=None))
        return result

    async def create_bulk(self, session, data: List[dict]) -> List[Secret]:
        objs = [self._metaclass(**item) for item in data]
        session.add_all(objs)
        session.commit()
        for obj in objs:
            session.refresh(obj)
        await notify_game_players(objs[0].game_id, WebsocketMessage(model="secret", action="create", data=[o.model_dump() for o in objs], dest_game=objs[0].game_id, dest_user=None))
        return objs


    async def update(self, session, oid: int, data: dict) -> Optional[Secret]:
        result = await super().update(session, oid, data)
        if result:
            session.refresh(result)
            await notify_game_players(game_id=result.game_id, message=WebsocketMessage(model="secret", action="update", data=result.model_dump(), dest_game=result.game_id, dest_user=None))
        return result

    async def delete(self, session, oid: int) -> Optional[int]:
        model_data = session.get(Secret, oid).model_dump()
        result = await super().delete(session, oid)
        if model_data and result:
            await notify_game_players(model_data['game_id'], WebsocketMessage(model="secret", action="delete", data=model_data, dest_game=model_data['game_id'], dest_user=None))
        return result