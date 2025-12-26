from sqlmodel import Session

from app.services.event_table import EventTableService
from app.services.game import GameService
from app.services.card import CardService, get_new_discarded_order
from app.services.chat import ChatService

from app.models.game import Game, GameStatus

from app.services.game import not_so_fast_status
from app.services.player import PlayerService


async def devious_detect(session: Session, game: Game):
    event_table_service = EventTableService()
    card_service = CardService()
    game_service = GameService()
    chat_service = ChatService()
    player_service = PlayerService()

    current_events = event_table_service.search(session=session, filterby={"game_id__eq":game.id, 
                                                                           "turn_played__eq": game.current_turn,
                                                                           "action__in": ["card_trade","dead_card_folly_trade"],
                                                                           "completed_action__eq": False})

    
    if len(current_events) != 0:
        event = current_events[0]

        await event_table_service.update(session=session, oid=event.id, data={"completed_action": True})
        card = card_service.read(session=session, oid=event.target_card)
        await card_service.update(session=session, oid=card.id, data={"turn_played": game.current_turn})

        if card.name == "social-faux-pas":
            player_to_reveal = player_service.read(session=session, oid=event.target_player)
            await chat_service.create(session=session, data={"game_id": game.id, "content": f"{player_to_reveal.name} reicibió un SOCIAL FAUX PAUS "})

            canceled = await not_so_fast_status(game, session, card.id)
        
            if canceled:
                await CardService().update(session=session, oid=card.id, data={"turn_discarded": game.current_turn, "discarded_order": get_new_discarded_order(session=session, game_id=game.id), 
                                                                               "owner": None, "turn_played": None})
                await game_service.update(session=session, oid=card.game_id, data={"status": GameStatus.FINALIZE_TURN, "player_in_action": None})
                await chat_service.create(session=session, data={"game_id": game.id, 
                                                                "content": f"La devious SOCIAL FAUX PAS fue cancelada"})
                await devious_detect(session=session, game=game)
            else:
                await game_service.update(session=session, oid=game.id, data={"status": GameStatus.WAITING_FOR_CHOOSE_SECRET,
                                                                              "player_in_action": event.target_player})
                
        elif card.name == "blackmailed":

            await game_service.update(session=session, oid=game.id, data={"status": GameStatus.WAITING_FOR_CHOOSE_SECRET,
                                                                    "player_in_action": event.player_id })
        
    else:
        await game_service.update(session=session, oid=game.id, data={"status": GameStatus.FINALIZE_TURN})




    

