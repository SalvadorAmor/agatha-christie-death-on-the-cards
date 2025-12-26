from typing import List, Optional

from fastapi import HTTPException
from sqlmodel import Session

from app.controllers.utils import PlayerOrders
from app.models.game import GameStatus
from app.models.player import Player
from app.services.card import CardService, get_new_discarded_order
from app.services.event_table import EventTableService
from app.services.game import GameService, not_so_fast_status
from app.models.card import Card, CardType
from app.services.player import PlayerService
from app.services.chat import ChatService
from app.controllers.card_effects.devious_detect import devious_detect


async def dead_card_folly(card: Card,  session:Session=None,     player_order: Optional[PlayerOrders] = None, target_cards: List[int]=[], issuer_player: Optional[Player]=None, **kwargs):
    game_service = GameService()
    player_service = PlayerService()
    event_table_service = EventTableService()
    chat_service = ChatService()

    game = game_service.read(session=session, oid=card.game_id)
    players = player_service.search(session=session, filterby={"game_id__eq": card.game_id})
    player = player_service.read(session=session, oid=card.owner)

    if game.status == GameStatus.TURN_START:
        # Pongo la carta en juego y cambio el estado del juego
        await CardService().update(session=session, oid=card.id, data={"turn_played":game.current_turn})

        await chat_service.create(session=session, data={"game_id": game.id, 
                                                            "content": f"{player.name} jugó la carta DEAD CARD FOLLY"})

        canceled = await not_so_fast_status(game, session, card.id)

        if canceled:
            await CardService().update(session=session, oid=card.id, data={"turn_discarded": game.current_turn, "discarded_order": get_new_discarded_order(session=session, game_id=game.id), "owner": None})
            await game_service.update(session=session, oid=card.game_id, data={"status": GameStatus.FINALIZE_TURN, "player_in_action": None})
            await chat_service.create(session=session, data={"game_id": game.id, 
                                                            "content": f"La carta DEAD CARD FOLLY fue cancelada"})
            return 200

        await game_service.update(session=session, oid=game.id, data={"status": GameStatus.WAITING_TO_CHOOSE_DIRECTION, "player_in_action": card.owner})
    elif game.status == GameStatus.WAITING_TO_CHOOSE_DIRECTION:
        if not player_order:
            raise HTTPException(status_code=400, detail="Debes elegir un orden")

        await event_table_service.create(session=session, data={
            "game_id": game.id,
            "player_id": issuer_player.id,
            "action": f"dead_card_folly_{player_order.value}",
            "turn_played": game.current_turn,
        })

        side = "derecha" if player_order.value == "clockwise" else "izquierda"

        await chat_service.create(session=session, data={"game_id": game.id, 
                                                             "content": f"Los intercambios se realizaran a la {side}"})


        await game_service.update(session=session, oid=game.id, data={"player_in_action": None, "status": GameStatus.SELECT_CARD_TO_TRADE})
    elif game.status == GameStatus.SELECT_CARD_TO_TRADE:
        if not target_cards:
            raise HTTPException(status_code=400, detail="Debes elegir una carta")

        target_card = CardService().read(session=session, oid=target_cards[0])
        if not target_card or target_card.owner != issuer_player.id:
            raise HTTPException(status_code=400, detail="Carta no válida")

        choosen_order_event = event_table_service.search(session=session, filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn, "action__in": ["dead_card_folly_clockwise", "dead_card_folly_counter-clockwise"]})

        next_player_position = (issuer_player.position + 1) % len(players) if choosen_order_event[0].action == "dead_card_folly_clockwise" else (issuer_player.position - 1) % len(players)
        next_player = filter(lambda p: p.position == next_player_position, players)
        next_player = list(next_player)[0]

        await event_table_service.create(session=session, data={
            "game_id": game.id,
            "player_id": issuer_player.id,
            "action": f"dead_card_folly_trade",
            "turn_played": game.current_turn,
            "target_card": target_card.id,
            "target_player": next_player.id,
            "completed_action": False
        })

        # Aca me interesan los trades no resueltos por si se interrumpio esto con la ejecucion de un devious
        trade_events = event_table_service.search(session=session, filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn, "action__eq": "dead_card_folly_trade"})
        pending_solve_events = list(filter(lambda e: not e.completed_action, trade_events))

        if len(trade_events) >= len(players):

            for event in pending_solve_events:
                await CardService().update(session=session, oid=event.target_card, data={"owner": event.target_player})

                target_card = CardService().read(session=session, oid=event.target_card)
                await event_table_service.update(session=session, oid=event.id, data={"completed_action": target_card.card_type != CardType.DEVIOUS})

            await CardService().update(session=session, oid=card.id, data={"turn_discarded": game.current_turn,
                                                                     "discarded_order": get_new_discarded_order(
                                                                        session=session, game_id=game.id),
                                                                     "owner": None,
                                                                     "turn_played":None})
            
            side = "derecha" if choosen_order_event[0].action == "dead_card_folly_clockwise" else "izquierda"
            
            await chat_service.create(session=session, data={"game_id": game.id, 
                                                             "content": f"La carta DEAD CARD FOLLY realizó todos los intercambios a la {side}"})
            await devious_detect(session=session, game=game)

    return 200





__ALL__ = ["delay_the_murderers_escape"]