import random
from typing import List

from fastapi import HTTPException
from sqlmodel import Session

from app.models.game import GameStatus
from app.models.websocket import notify_game_players, WebsocketMessage
from app.services.card import CardService, get_new_discarded_order
from app.services.game import GameService, not_so_fast_status
from app.models.card import Card
from app.services.chat import ChatService
from app.services.player import PlayerService


async def delay_the_murderers_escape(card: Card,  session:Session=None, target_cards: List[int] = [], **kwargs):
    card_service = CardService()
    game_service = GameService()
    chat_service = ChatService()
    player_service = PlayerService()

    game = game_service.read(session=session, oid=card.game_id)
    player = player_service.read(session=session, oid=card.owner)

    if game.status == GameStatus.TURN_START:
        await card_service.update(session=session, oid=card.id, data={"turn_played": game.current_turn})
        await chat_service.create(session=session, data={"game_id": game.id, 
                                                     "content": f"{player.name} jugó un DELAY THE MURDERERS ESCAPE"})

        canceled = await not_so_fast_status(game, session, card.id)
        if canceled:
            await card_service.delete(session=session, oid=card.id)
            await game_service.update(session=session, oid=card.game_id,
                                        data={"status": GameStatus.FINALIZE_TURN, "player_in_action": None})
            await chat_service.create(session=session, data={"game_id": game.id, "content": "la carta DELAY THE MURDERERS ESCAPE fue cancelada"})
            return 200

        await game_service.update(session=session, oid=card.game_id, data={'player_in_action': card.owner, 'status': GameStatus.WAITING_FOR_ORDER_DISCARD})

    elif game.status == GameStatus.WAITING_FOR_ORDER_DISCARD:
        if not target_cards:
            raise HTTPException(status_code=412, detail="Se deben seleccionar cartas")

        cards = card_service.search(session=session, filterby={"game_id__eq": card.game_id,"turn_discarded__is_null": True, "owner__is_null": True, "content__eq":""}, sortby="pile_order__desc")
        draft = cards[0:3]
        not_draft = cards[3:]

        discarded_cards = card_service.search(session=session, filterby={"game_id__eq": card.game_id, "discarded_order__is_null": False}, sortby="discarded_order__desc")
        last_5 = discarded_cards[0:min(5, len(discarded_cards))]

        last_5.sort(key=lambda c: target_cards.index(c.id) if c.id in target_cards else len(target_cards))

        # No se puede usar el update bulk acá, entonces tengo que hacer uso de sqlmodel para commitear al final
        for c in last_5:
            c.discarded_order = None
            c.turn_discarded = None
            c.turn_played = None
            c.owner = None
            c.content = ""

        not_draft.extend(last_5)

        for i, c in enumerate(reversed(draft)):
            c.pile_order = len(not_draft) + i

        for i, c in enumerate(not_draft):
            c.pile_order = i


        await card_service.delete(session=session, oid=card.id)
        if discarded_cards:
            notified_card = discarded_cards[0]
            session.refresh(notified_card)
            await notify_game_players(game_id=game.id, message=WebsocketMessage(model="card", action="update", data=notified_card.model_dump(), dest_game=game.id, dest_user=None))
        session.commit()
        session.refresh(game)
        await game_service.update(session=session, oid=game.id, data={"status": GameStatus.FINALIZE_TURN})
        await chat_service.create(session=session, data={"game_id": game.id, 
                                                         "content": f"{player.name} pasó cartas de la pila de descarte al mazo"})
    return 200





__ALL__ = ["delay_the_murderers_escape"]