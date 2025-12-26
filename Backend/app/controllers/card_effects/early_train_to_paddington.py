from typing import List
from sqlmodel import Session


from app.models.card import Card
from app.models.game import GameStatus
from app.services.card import CardService, get_new_discarded_order
from app.services.game import GameService, not_so_fast_status
from app.services.chat import ChatService


async def early_train_to_paddington(card:Card,session: Session=None,in_discard:bool=False,target_players: List[int] = [],
                              target_secrets: List[int] = [], target_cards: List[int]=[], target_sets: List[int]=[], **kwargs):
    card_service = CardService()
    game_service = GameService()
    chat_service = ChatService()

    game = game_service.read(session=session, oid=card.game_id)

    await card_service.update(session=session,oid=card.id,data={"turn_played":game.current_turn})

    await chat_service.create(session=session, data={"game_id": game.id, 
                                                     "content": f"se jugó la carta EARLY TRAIN TO PADDINGTON"})

    canceled = await not_so_fast_status(game, session,card.id)

    if canceled:
        await card_service.delete(session=session, oid=card.id)
        await chat_service.create(session=session, data={"game_id": game.id, 
                                                         "content": f"Se canceló y eliminó la carta EARLY TRAIN TO PADDINGTON"})
        if in_discard:
            return
        else:
            await game_service.update(session=session, oid=card.game_id,data={"status": GameStatus.FINALIZE_TURN, "player_in_action": None})
            return

    # Las 3 primeras son del draft, y traemos una mas para ver si se acabo el mazo
    cards_to_update = card_service.search(session=session,
                                          filterby={'game_id__eq': card.game_id, 'discarded_order__is_null': True,
                                                    'owner__is_null': True}, limit=7, offset=3)

    new_discarded_order = get_new_discarded_order(session=session, game_id=card.game_id)

    for i,c in enumerate(cards_to_update[:6]):
        await card_service.update(session=session, oid=c.id, data={"turn_discarded": -1,"discarded_order": new_discarded_order + i,"owner": None})
    await card_service.delete(session=session, oid=card.id)

    if len(cards_to_update) < 7:
        await game_service.update(session=session, oid=card.game_id, data={"status":GameStatus.FINALIZED,"player_in_action":None})
    elif in_discard:
        await chat_service.create(session=session, data={"game_id": game.id, 
                                                         "content": f"Se jugó y eliminó la carta EARLY TRAIN TO PADDINGTON"})
        return
    else:
        await chat_service.create(session=session, data={"game_id": game.id, 
                                                         "content": f"Se jugó y eliminó la carta EARLY TRAIN TO PADDINGTON"})
        await game_service.update(session=session,oid=card.game_id,data={"status":GameStatus.FINALIZE_TURN, "player_in_action":None})
    
__ALL__ = ["early_train_to_paddington"]