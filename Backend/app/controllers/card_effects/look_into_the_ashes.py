from fastapi import HTTPException
from typing import List
from sqlmodel import Session

from app.models.card import Card
from app.models.game import GameStatus
from app.services.card import CardService,get_new_discarded_order
from app.services.game import GameService, not_so_fast_status
from app.services.player import PlayerService
from app.services.chat import ChatService


async def look_into_the_ashes(card: Card, session: Session, target_players: List[int]=[],
                            target_secrets: List[int] = [], target_cards: List[int]=[], target_sets: List[int]=[], **kwargs):
    card_service = CardService()
    player_service = PlayerService()
    game_service = GameService()
    chat_service = ChatService()

    game = game_service.read(session=session, oid=card.game_id)

    last_five_discarded = card_service.search(session=session,
                                             filterby={"game_id__eq": card.game_id, 'discarded_order__is_null': False},
                                             sortby="discarded_order__desc", limit=5)


    if not len(last_five_discarded):
        raise HTTPException(status_code=412, detail= "No hay cartas en la pila de descarte, no se puede jugar")

    player = player_service.read(session=session, oid=card.owner)

    if card.turn_played is None and game.status == GameStatus.TURN_START:

        await card_service.update(session=session, oid=card.id, data={"turn_played": game.current_turn})

        await chat_service.create(session=session, data={"game_id": game.id, 
                                                         "content": f"{player.name} jugó la carta LOOK INTO THE ASHES"})

        canceled = await not_so_fast_status(game, session,card.id)

        if canceled:
            await card_service.update(session=session, oid=card.id,data={"owner": None, "turn_discarded": game.current_turn,
                                                                         "discarded_order": get_new_discarded_order(session=session,game_id=game.id)})
            await game_service.update(session=session, oid=card.game_id,
                                      data={"status": GameStatus.FINALIZE_TURN, "player_in_action": None})
            await chat_service.create(session=session, data={"game_id": game.id, 
                                                             "content": f"Se canceló la carta LOOK INTO THE ASHES"})
            return

        await game_service.update(session=session, oid=game.id, data={"status": GameStatus.WAITING_FOR_CHOOSE_DISCARDED, "player_in_action":player.id})

    elif card.turn_played is not None and game.status == GameStatus.WAITING_FOR_CHOOSE_DISCARDED:

        if len(target_cards) != 1:
            raise HTTPException(400, "Cantidad erronea de cartas objetivos")

        if card.turn_played != game.current_turn:
            raise HTTPException(400, "No se puede relanzar una carta jugada")

        target_card_id = target_cards[0]
        target_card = card_service.read(session=session, oid=target_card_id)

        if not target_card:
            raise HTTPException(404, "Carta objetivo no existente")

        if target_card.game_id != card.game_id:
            raise HTTPException(400, "Carta no existente en esta partida")

        if target_card not in last_five_discarded:
            raise HTTPException(status_code=400, detail="Solo se puede agarrar una de las 5 ultimas descartadas")

        await card_service.update(session=session, oid=target_card_id, data={"turn_discarded": None,"turn_played":None,
                                                                             "discarded_order": None,"owner": player.id,
                                                                             "content":""})

        new_discarded_order = get_new_discarded_order(session=session, game_id=card.game_id)

        await card_service.update(session=session, oid=card.id, data={"turn_discarded": game.current_turn,
                                                                      "discarded_order": new_discarded_order,"owner": None})

        await game_service.update(session=session, oid=game.id, data={"status": GameStatus.FINALIZE_TURN, "player_in_action":None})

        await chat_service.create(session=session, data={"game_id": game.id, 
                                                         "content": f"{player.name} ya eligió una carta de la pila de descarte"})

    else:
        raise HTTPException(400, "Ya no se puede jugar eventos")
    
__ALL__ = ["look_into_the_ashes"]