from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlmodel import Session
from pydantic import BaseModel

from app.controllers.utils import reveal_secret
from app.database.engine import db_session
from app.models.detective_set import DetectiveSet, PublicDetectiveSet
from app.models.game import GameStatus

from app.services.detective_set import (
    DetectiveSetService,
    CreateDetectiveSet,
    DetectiveSetFilter, set_next_game_status, set_have_detectives, DETECTIVES_CHOOSE_PLAYERS,
)
from app.services.card import CardService, get_new_discarded_order
from app.models.card import CardType, Card
from app.services.game import GameService, not_so_fast_status
from app.services.player import PlayerService
from app.services.secret import SecretService
from app.services.chat import ChatService

import asyncio

set_router = APIRouter(prefix="/api/detective_set")


class CreateDetectiveSetDTO(BaseModel):
    detectives: List[int]

class UpdateDetectiveSetDTO(BaseModel):
    add_card: Optional[int] = None
    token: Optional[str] = None

class SetActionDTO(BaseModel):
    target_player: Optional[int] = None
    target_secret: Optional[int] = None
    token: str

TUPPENCE = ["tuppence-beresford","tommy-beresford"]

@set_router.post("/", response_model=PublicDetectiveSet)
async def create_detective_set(
    dto: CreateDetectiveSetDTO,
    token: str = Query(...),
    session: Session = Depends(db_session),
):
    player_service = PlayerService()
    card_service = CardService()
    set_service = DetectiveSetService()
    game_service = GameService()
    chat_service = ChatService()

    player = await player_service.read_by_token(session, token)
    if not player:
        raise HTTPException(status_code=401, detail="Token inválido")

    if player.social_disgrace:
        raise HTTPException(status_code=400, detail="En desgracia social no se puede jugar un set")

    game = game_service.read(session=session,oid=player.game_id)

    if game.status != GameStatus.TURN_START:
        raise HTTPException(status_code=400, detail="No se puede crear el set: Ya se realizo una accion")

    # Verificar que todas las cartas sean del tipo detective y del mismo jugador
    cards: List[Card] = []
    for cid in dto.detectives:
        card = card_service.read(session, cid)
        if not card:
            raise HTTPException(status_code=404, detail=f"Carta {cid} no encontrada")
        if card.card_type != CardType.DETECTIVE:
            raise HTTPException(status_code=400, detail="Solo se pueden crear sets con cartas detective")
        if card.owner != player.id:
            raise HTTPException(status_code=401, detail="No puedes usar cartas que no te pertenecen")
        if card.set_id:
            raise HTTPException(status_code=400, detail="Alguna de las cartas ya se encuentra en un set")
        cards.append(card)


    data = CreateDetectiveSet(detectives=dto.detectives,game_id=game.id,owner=player.id, turn_played=game.current_turn)
    detective_set = await set_service.create(session, data)

    detective_names = {d.name for d in detective_set.detectives}
    canceled = False

    detective_name_not_wild = [d for d in detective_names if d != "harley-quin-wildcard" and d != "ariadne-oliver"]
    detective_name =  detective_name_not_wild[0].replace("-", " ").upper()

    await chat_service.create(session=session, data={"game_id": game.id, "content": f"{player.name} creó un set de {detective_name}"})

    if not {"tommy-beresford","tuppence-beresford"} <= detective_names:
        canceled = await not_so_fast_status(game, session,detective_set.id)

    if canceled:
        if set_have_detectives(detective_set,["lady-eileen-bundle-brent"]):
            update_data = [{"set_id":None} for _ in detective_set.detectives]
            card_ids = [d.id for d in detective_set.detectives]
            await chat_service.create(session=session, data={"game_id":game.id ,"content":f"Se canceló el set de {detective_name} y volvió a la mano del jugador"})

            await card_service.bulk_update(session=session, oids=card_ids, data=update_data)
            await set_service.delete(session=session,id=detective_set.id)
        await chat_service.create(session=session, data={"game_id":game.id ,"content":f"Se canceló el set de {detective_name}"})
        await game_service.update(session=session, oid=game.id,data={"status": GameStatus.FINALIZE_TURN, "player_in_action": None})
    else:
        await game_service.update(session=session, oid=game.id, data={"status": set_next_game_status(detective_set, session, game),
                                                                     "player_in_action": player.id})

    return detective_set

@set_router.post("/update/{sid}", response_model=PublicDetectiveSet)
async def update_detective_sets(sid:int,dto:UpdateDetectiveSetDTO,session: Session = Depends(db_session)):
    set_service = DetectiveSetService()
    game_service = GameService()
    card_service = CardService()
    player_service = PlayerService()
    chat_service = ChatService()

    detective_set = await set_service.read(session=session,id=sid)

    if not detective_set:
        raise HTTPException(404,"No se puede actualizar el set: Set no encontrado")

    game = game_service.read(session=session,oid=detective_set.game_id)

    if game.status != GameStatus.TURN_START:
        raise HTTPException(412,"No se puede actualizar el set: No es el comienzo de turno")

    player = player_service.read(session=session,oid=detective_set.owner)

    if player.token != dto.token:
        raise HTTPException(401, "No se puede actualizar el set: Token invalido")

    detective = card_service.read(session=session,oid=dto.add_card)

    if not detective:
        raise HTTPException(404, "No se puede actualizar el set: Detective no encontrado")

    if detective.set_id:
        raise HTTPException(400, "No se puede actualizar el set: Detective en set")

    if detective.owner != player.id:
        raise HTTPException(400, "No se puede actualizar el set: No es dueño de la carta")

    is_tuppence_set = set_have_detectives(detective_set,TUPPENCE) and detective.name in TUPPENCE

    if not set_have_detectives(d_set=detective_set, d_names=[detective.name]) and not is_tuppence_set:
        raise HTTPException(400, "No se puede actualizar el set: El detective corresponde al set")

    updated_set = await set_service.update(session=session,data={"detectives":detective,"turn_played":game.current_turn},id=detective_set.id)

    await chat_service.create(session=session, data={"game_id": game.id, "content": f"{player.name} agregó un {detective.name.replace("-", " ").upper()} a su set"})

    detective_names = {d.name for d in updated_set.detectives}
    canceled = False

    detective_name_not_wild = [d for d in detective_names if d != "harley-quin-wildcard" and d != "ariadne-oliver"]
    detective_name =  detective_name_not_wild[0].replace("-", " ").upper()

    if not {"tommy-beresford", "tuppence-beresford"} <= detective_names:
        canceled = await not_so_fast_status(game, session,updated_set.id)

    if canceled:
        if set_have_detectives(detective_set, ["lady-eileen-bundle-brent"]):
            update_data = [{"set_id": None} for _ in detective_set.detectives]
            card_ids = [d.id for d in detective_set.detectives]

            await chat_service.create(session=session, data={"game_id": game.id,"content": f"Se canceló el set de {detective_name} y volvió a la mano del jugador"})
            
            await card_service.bulk_update(session=session, oids=card_ids, data=update_data)

        await game_service.update(session=session, oid=game.id, data={"status": GameStatus.FINALIZE_TURN, "player_in_action": None})
    else:
        await game_service.update(session=session, oid=game.id, data={"status": set_next_game_status(detective_set, session, game),
                                                                      "player_in_action": player.id})
    return updated_set


@set_router.post("/search", response_model=List[PublicDetectiveSet])
async def search_detective_sets(
    filter: DetectiveSetFilter,
    token: str = Query(...),
    session: Session = Depends(db_session),
):
    player_service = PlayerService()
    set_service = DetectiveSetService()

    player = await player_service.read_by_token(session, token)
    if not player:
        raise HTTPException(status_code=401, detail="Token inválido")

    result = set_service.search(session, filter.model_dump())
    return result


@set_router.get("/{sid}", response_model=PublicDetectiveSet)
async def get_detective_set(
    sid: int,
    token: str = Query(...),
    session: Session = Depends(db_session),
):
    player_service = PlayerService()
    set_service = DetectiveSetService()

    player = await player_service.read_by_token(session, token)
    if not player:
        raise HTTPException(status_code=401, detail="Token inválido")

    detective_set = await set_service.read(session, sid)
    if not detective_set:
        raise HTTPException(status_code=404, detail="Set no encontrado")

    return detective_set

def detectives_in_set(name:List[str],d_set:DetectiveSet):
    return all([any(detective.name == d_name for detective in d_set.detectives) for d_name in name])

@set_router.post("/{sid}")
async def post_detective_set_action(sid:int,dto:SetActionDTO,session: Session = Depends(db_session)):
    set_service = DetectiveSetService()
    game_service = GameService()
    player_service = PlayerService()
    secret_service = SecretService()
    chat_service = ChatService()

    played_set = await set_service.read(session=session,id=sid)

    if not played_set:
        raise HTTPException(status_code=404, detail="No se puede realizar la accion: Set no encontrado")

    game = game_service.read(session=session,oid=played_set.game_id)

    player_in_action = player_service.read(session=session, oid=game.player_in_action)

    if played_set.turn_played != game.current_turn:
        raise HTTPException(status_code=412, detail="No se puede realizar la accion: Turno invalido")

    if game.status == GameStatus.WAITING_FOR_CHOOSE_PLAYER:

        if not dto.target_player:
            raise HTTPException(status_code=400, detail="No se puede realizar la accion: Es necesario elegir un jugador")

        if dto.target_player == played_set.owner:
            raise HTTPException(status_code=406, detail="No se puede realizar la accion: No se puede seleccionar a uno mismo")

        target_player = player_service.read(session=session,oid=dto.target_player)

        if not target_player:
            raise HTTPException(status_code=400, detail="No se puede realizar la accion: Es necesario seleccionar un jugador")

        if target_player.game_id != game.id:
            raise HTTPException(400, "No se puede realizar la accion: El jugador seleccionado no se encuentra en la partida")

        if player_in_action.token != dto.token:
            raise HTTPException(status_code=412, detail="No se puede realizar la accion: Token invalido")

        await chat_service.create(session=session, data={"game_id": game.id, "content": f"{target_player.name} fué seleccionado para revelar un secreto"})

        await game_service.update(session=session, oid=game.id, data={"status":GameStatus.WAITING_FOR_CHOOSE_SECRET,
                                                                      "player_in_action": dto.target_player})

    elif game.status == GameStatus.WAITING_FOR_CHOOSE_SECRET:

        if not dto.target_secret:
            raise HTTPException(status_code=400,detail="No se puede realizar la accion: Es necesario elegir un secreto")

        if player_in_action.token != dto.token:
            raise HTTPException(status_code=412, detail="No se puede realizar la accion: Token invalido")

        secret = secret_service.read(session=session,oid=dto.target_secret)

        if not secret:
            raise HTTPException(status_code=404, detail="No se puede realizar la accion: Secreto no encontrado")

        if secret.game_id != game.id:
            raise HTTPException(status_code=404, detail="No se puede realizar la accion: El secreto seleccionado no se encuentra en la partida")

        ariadne_played_this_turn = any(d.name == "ariadne-oliver" and d.turn_played == game.current_turn for d in played_set.detectives)

        # Si es un set en el que se elige un jugador, el secreto a elegir debe ser propio
        if (set_have_detectives(played_set,DETECTIVES_CHOOSE_PLAYERS) or ariadne_played_this_turn) and secret.owner != player_in_action.id:

            raise HTTPException(status_code=412, detail="No se puede realizar la accion: Se debe seleccionar un secreto propio")

        # Parker Pyne
        if set_have_detectives(played_set,["parker-pyne"]) and not ariadne_played_this_turn:

            if not secret.revealed:
                HTTPException(status_code=412, detail="No se puede realizar la accion: El secreto debe estar revelado")

            secret_owner = player_service.read(session=session,oid=secret.owner)

            if secret_owner.social_disgrace:
                await player_service.update(session=session, oid=secret.owner, data={"social_disgrace": False})

            await secret_service.update(session=session, oid=secret.id, data={"revealed":False})

            await chat_service.create(session=session, data={"game_id": game.id, "content": f"el secreto de {secret_owner.name} fué ocultado"})
        else:

            if secret.revealed:
                HTTPException(status_code=412, detail="No se puede realizar la accion: El secreto debe estar oculto")

            secret_owner = player_service.read(session=session,oid=secret.owner)
            rs_result = await reveal_secret(session, secret)
            await chat_service.create(session=session, data={"game_id": game.id, "content": f"el secreto de {secret_owner.name} fué revelado"})

            if rs_result == "game_finalized":
                return 200

            if detectives_in_set(["mr-satterthwaite","harley-quin-wildcard"],played_set):
                secret_owner = player_service.read(session=session,oid=secret.owner)
                player = player_service.read(session=session, oid=played_set.owner)
                await chat_service.create(session=session, data={"game_id": game.id, "content": f"el secreto de {secret_owner.name} fué robado y ocultado en los secretos de {player.name}"})
                await secret_service.update(session=session, oid=secret.id, data={"owner":played_set.owner,"revealed": False})

        await game_service.update(session=session, oid=game.id, data={"status":GameStatus.FINALIZE_TURN,"player_in_action":None})

    else:
        raise HTTPException(status_code=400, detail="No se puede realizar la accion: Estado de partida invalido")

    return 200
