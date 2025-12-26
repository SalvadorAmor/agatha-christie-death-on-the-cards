import asyncio
from enum import Enum
from operator import attrgetter
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Optional, List, Dict, Callable
from sqlmodel import Session
from pydantic import BaseModel

from app.controllers.card_effects.ariadne_oliver import ariadne_oliver
from app.controllers.card_effects.card_trade import card_trade
from app.controllers.card_effects.dead_card_folly import dead_card_folly
from app.controllers.card_effects.delay_the_murderers_escape import delay_the_murderers_escape
from app.controllers.card_effects.point_your_suspicions import point_your_suspicions
from app.controllers.card_effects.early_train_to_paddington import early_train_to_paddington
from app.controllers.card_effects.cards_off_the_table import cards_off_the_table
from app.controllers.card_effects.look_into_the_ashes import look_into_the_ashes
from app.controllers.card_effects.and_then_there_was_one_more import and_then_there_was_one_more
from app.controllers.card_effects.another_victim import another_victim
from app.controllers.card_effects.blackmailed import blackmailed
from app.controllers.card_effects.social_faux_pas import social_faux_pas
from app.controllers.utils import PlayerOrders
from app.database.engine import db_session
from app.models.card import PublicCard
from app.models.event_table import EventTable
from app.models.game import GameStatus
from app.models.websocket import notify_game_players, WebsocketMessage
from app.services.card import CardService, CardFilter, get_new_discarded_order
from app.services.event_table import EventTableService
from app.services.game import GameService, not_so_fast_status, NOT_SO_FAST_TIME
from app.services.player import PlayerService
from app.services.detective_set import DetectiveSetService
from app.services.secret import SecretService
from app.services.chat import ChatService


card_router = APIRouter(prefix="/api/card")

class UpdateCardDTO(BaseModel):
    owner: Optional[int] = None
    token: Optional[str] = None

class UpdateCardsDTO(BaseModel):
    turn_discarded: Optional[int] = None
    token: Optional[str] = None

class CancelActionDTO(BaseModel):
    not_so_fast:int
    token: str

@card_router.get('/{cid}', response_model = PublicCard)
def get_card(cid: int, session: Session = Depends(db_session)):
    service = CardService()
    card = service.read(session = session, oid = cid)

    if not card:
        raise HTTPException(404, detail="No se encontro la carta")

    return card

@card_router.patch('', response_model= List[PublicCard])
async def update_cards(cids:List[int] = Body(...), dto:UpdateCardsDTO = Body(...), session: Session = Depends(db_session)):
    card_service = CardService()
    player_service = PlayerService()
    game_service = GameService()

    if not len(cids):
        raise HTTPException(status_code=422, detail="No se mandaron cartas a descartar")

    cards = []

    for card_id in cids:
        card = card_service.read(session=session,oid=card_id)
        if not card:
            raise HTTPException(404, detail="No se pudo encontrar la carta")

        if not card.owner:
            raise HTTPException(404, detail="La carta no tiene dueño")

        if card.turn_discarded is not None:
            raise (HTTPException(status_code=400, detail="No se puede descartar una carta descartada"))

        if card.set_id:
            raise HTTPException(status_code=400, detail="No se puede descartar una carta en set")

        player = player_service.read(session=session, oid=card.owner)

        # Solo se puede pasar un token, es decir que todas las cartas tienen que pertenecer al mismo dueño y por lo tanto al mismo juego
        if player.token != dto.token:
            raise HTTPException(401, detail="No se puede descartar la carta: Token invalido")
        cards.append(card)

    game = game_service.read(session=session, oid=cards[0].game_id)

    if not game:
        raise HTTPException(404, "No se pudo encontrar el juego")

    if game.status not in {GameStatus.FINALIZE_TURN,GameStatus.TURN_START}:
        raise HTTPException(status_code=400, detail="No se puede descartar la carta: Estado de partida invalida")

    if dto.turn_discarded != game.current_turn:
        raise (HTTPException(status_code=400, detail="Se debe descartar en el turno actual"))

    player = player_service.read(session=session, oid=cards[0].owner)
    amount_players = len(player_service.search(session=session,filterby={"game_id__eq":game.id}))

    if player.position != game.current_turn % amount_players:
        raise HTTPException(status_code=412, detail="No se puede descartar la carta: No es tu turno")

    if player.social_disgrace and len(cards) > 1:
        raise HTTPException(status_code=400, detail="En desgracia social solo se permite descartar una carta")

    hand_cards = card_service.search(session=session,filterby={"game_id__eq":game.id, "owner__eq":player.id, "set_id__is_null":True})

    if len(cards) > len(hand_cards):
        raise HTTPException(status_code=400, detail="No se pueden descartar las cartas: No tenes esa cantidad en mano")

    new_discarded_order = get_new_discarded_order(session=session, game_id=game.id)

    update_data= []
    card_ids = []

    for i, c in enumerate(cards):
        update_data.append({"turn_discarded": game.current_turn,"discarded_order": new_discarded_order + i,"owner": None})
        card_ids.append(c.id)

    updated_cards = await card_service.bulk_update(session=session, oids=card_ids, data=update_data)

    action_in_discard = [c for c in updated_cards if c.name == "early-train-to-paddington" ]

    for c in action_in_discard:
        await early_train_to_paddington(c,session,True)

    if game.status in {GameStatus.TURN_START,GameStatus.FINALIZE_TURN, GameStatus.WAITING_FOR_CANCEL_ACTION}:
        await game_service.update(session=session, oid=game.id, data={"status": GameStatus.FINALIZE_TURN_DRAFT})

    return updated_cards

@card_router.patch('/{cid}', response_model= PublicCard)
async def update_card(cid:int, dto:UpdateCardDTO, session: Session = Depends(db_session)):
    card_service = CardService()
    player_service = PlayerService()
    game_service = GameService()

    card = card_service.read(session=session, oid=cid)

    if not card:
        raise HTTPException(404, detail="No se pudo encontrar la carta")

    if dto.owner is None:
        raise HTTPException(status_code=422, detail="Se debe indicar el dueño de la carta")

    game = game_service.read(session=session, oid=card.game_id)

    if not game:
        raise HTTPException(404, "No se pudo encontrar el juego")

    if game.status not in {GameStatus.FINALIZE_TURN_DRAFT,GameStatus.FINALIZE_TURN}:
        raise HTTPException(status_code=400, detail="No se puede agarrar la carta: Estado de partida invalido")

    player = player_service.read(session=session, oid=dto.owner)

    if not player:
        raise HTTPException(404, detail="No se pudo encontrar el jugador")

    if player.game_id != game.id:
        raise HTTPException(status_code=400, detail="El jugador no pertenece al juego")

    if player.token != dto.token:
        raise HTTPException(401, detail="No se puede agarrar la carta: Token invalido")

    amount_players = len(player_service.search(session=session, filterby={"game_id__eq": game.id}))
    actual_turn = game.current_turn % amount_players

    if player.position != actual_turn:
        raise HTTPException(status_code=412, detail="No se puede agarrar la carta: No es tu turno")


    player_cards = card_service.search(session=session,
                                       filterby={"game_id__eq": game.id, "owner__eq": player.id, "set_id__is_null":True})

    if len(player_cards) > 5:
        raise HTTPException(status_code=412, detail="No se pueden agarrar mas cartas")

    draft_cards = card_service.search(session=session,filterby={'game_id__eq': game.id, 'turn_discarded__is_null': True,
                                                                'owner__is_null': True, 'content__eq':""}, limit=3)

    if not card in draft_cards:
        raise HTTPException(status_code=400, detail="Solo se pueden agarrar cartas del draft")

    updated_card = await card_service.update(session=session, oid=card.id, data={"owner": player.id})

    if game.status != GameStatus.FINALIZE_TURN_DRAFT:
        await game_service.update(session=session, oid=game.id, data={"status":GameStatus.FINALIZE_TURN_DRAFT})

    return updated_card

@card_router.post('/search', response_model=List[PublicCard])
def search_card(dto:CardFilter, session: Session = Depends(db_session)):
    service = CardService()
    cards = service.search(session=session, filterby=dto.model_dump(exclude_none=True), sortby="pile_order__desc")
    return cards


@card_router.post('/cancel_action/{oid}')
async def cancel_action(oid:int,dto:CancelActionDTO,session: Session = Depends(db_session)):
    card_service = CardService()
    game_service = GameService()
    player_service = PlayerService()
    event_service = EventTableService()
    chat_service = ChatService()

    cancel_event = event_service.read(session=session, oid=oid)
    if not cancel_event:
        raise HTTPException(404, "No se puede cancelar la accion: No se encontró el evento")

    not_so_fast = card_service.read(session,dto.not_so_fast)

    if not not_so_fast:
        raise HTTPException(404,"No se puede cancelar la accion: Carta no encontrada")

    game = game_service.read(session,cancel_event.game_id)

    if game.status != GameStatus.WAITING_FOR_CANCEL_ACTION:
        raise HTTPException(400,"No se puede cancelar la accion: Estado de partida invalido")

    if cancel_event.turn_played != game.current_turn:
        raise HTTPException(400,"No se puede cancelar la accion: Turno invalido")

    player = player_service.read(session,not_so_fast.owner)

    if player.token != dto.token:
        raise HTTPException(status_code=401, detail="No se puede cancelar la accion: Token inválido")


    last_event = event_service.search(session=session, filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn,
                                                                 "action__eq": "to_cancel", "completed_action__eq": False,},
                                                                 sortby="id__desc", limit=1)

    canceled_times_event = event_service.search(session=session, filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn,
                                                                           "action__eq": "canceled_times"},sortby="id__desc", limit=1)[0]

    if not last_event or last_event[0].id != cancel_event.id:
        print(last_event)
        print(cancel_event)
        raise HTTPException(400,"No se puede cancelar la accion: No es la ultima accion cancelable")

    game.timestamp = datetime.now()

    # Necesito que esto sea atomico, si hago un update con await puede tomar otros endpoint
    cancel_event.completed_action = True
    canceled_times_event.target_card +=1

    session.commit()

    await chat_service.create(session=session, data={"game_id":game.id, "content": "Se jugó un NOT SO FAST para cancelar la acción"})

    await event_service.create(session=session, data={"game_id": game.id, "turn_played": game.current_turn,
                                                      "target_card": not_so_fast.id, "action": "to_cancel",},)

    await card_service.update(session=session,oid=not_so_fast.id,data={"owner": None, "content":"nsf"})

    return 200

CARD_ACTIONS: Dict[str, Callable] = {
    "early-train-to-paddington": early_train_to_paddington,
    "cards-off-the-table": cards_off_the_table,
    "look-into-the-ashes": look_into_the_ashes,
    "and-then-there-was-one-more": and_then_there_was_one_more,
    "another-victim": another_victim,
    "delay-the-murderers-escape": delay_the_murderers_escape,
    "point-your-suspicions": point_your_suspicions,
    "ariadne-oliver": ariadne_oliver,
    "card-trade": card_trade,
    "dead-card-folly": dead_card_folly,
    "blackmailed": blackmailed,
    "social-faux-pas": social_faux_pas
}

class PlayCardDTO(BaseModel):
    target_players: List[int] = []
    target_secrets: List[int] = []
    target_cards: List[int] = []
    target_sets: List[int] = []
    player_order: Optional[PlayerOrders] = None

@card_router.post("/play_card/{cid}")
async def play_card(
    cid: int,
    dto: PlayCardDTO,
    token: str = Query(..., description="Token"),
    session: Session = Depends(db_session)
):
    card_service = CardService()
    player_service = PlayerService()
    game_service = GameService()

    card = card_service.read(session=session, oid=cid)
    if not card:
        raise HTTPException(status_code=404, detail="Carta no encontrada")

    player = player_service.read(session=session, oid=card.owner)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    issuer_player = await player_service.read_by_token(session=session, token=token)
    if not issuer_player:
        raise HTTPException(status_code=401, detail="Token invalido")

    game = game_service.read(session=session, oid=player.game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Juego no encontrado")

    if player.social_disgrace and game.status == GameStatus.TURN_START:
        raise HTTPException(status_code=400,detail="No se pueden jugar cartas en desgracia social")

    card_name = getattr(card, "name", None)
    if not card_name:
        raise HTTPException(status_code=400, detail="La carta no tiene nombre definido")

    action = CARD_ACTIONS.get(card_name)
    if not action:
        raise HTTPException(status_code=404, detail=f"No se encontró una acción para la carta '{card_name}'")

    # TODO: Capaz queremos retornar algo del resultado de la acción
    await action(card, session, issuer_player=issuer_player, **dto.model_dump())

    return 200
