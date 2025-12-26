from fastapi import HTTPException
from typing import List
from sqlmodel import Session

from app.services.detective_set import set_next_game_status
from app.models.card import Card
from app.models.game import GameStatus
from app.services.card import CardService, get_new_discarded_order
from app.services.detective_set import DetectiveSetService
from app.services.game import GameService, not_so_fast_status
from app.services.chat import ChatService
from app.services.player import PlayerService


async def another_victim(card: Card, session: Session, target_players: List[int]=[],
                target_secrets: List[int]=[], target_cards: List[int]=[], target_sets: List[int]=[], **kwargs):
    game_service = GameService()
    card_service = CardService()
    set_service = DetectiveSetService()
    chat_service = ChatService()
    player_service = PlayerService()

    game = game_service.read(session=session, oid=card.game_id)
    player = player_service.read(session=session, oid=card.owner)

    if card.turn_played is None and game.status == GameStatus.TURN_START:

        sets_in_game = set_service.search(session=session,filterby={"game_id__eq":game.id})
        other_players_sets = [s for s in sets_in_game if s.owner != card.owner]

        if not other_players_sets:

            await card_service.update(session=session, oid=card.id,data={"owner": None, "turn_discarded": game.current_turn,
                                                                         "discarded_order": get_new_discarded_order(session=session,game_id=game.id)})

            await game_service.update(session=session, oid=game.id, data={"status": GameStatus.FINALIZE_TURN, "player_in_action": None})

            await chat_service.create(session=session, data={"game_id": game.id, 
                                                            "content": f"La carta ANOTHER VICTIM se jugó sin sets, se descarta"})
            
            return
        
        await chat_service.create(session=session, data={"game_id": game.id, 
                                                        "content": f"{player.name} jugó la carta ANOTHER VICTIM"})

        await card_service.update(session=session, oid=card.id, data={"turn_played": game.current_turn})
        canceled = await not_so_fast_status(game, session,card.id)

        if canceled:
            await card_service.update(session=session, oid=card.id,data={"owner": None, "turn_discarded": game.current_turn,
                                                                            "discarded_order": get_new_discarded_order(session=session,game_id=game.id)})
            await game_service.update(session=session, oid=card.game_id,data={"status": GameStatus.FINALIZE_TURN, "player_in_action": None})
            await chat_service.create(session=session, data={"game_id": game.id, "content": "la carta ANOTHER VICTIM fue cancelada"})

            return

        await game_service.update(session=session, oid=game.id,data={"status": GameStatus.WAITING_FOR_CHOOSE_SET,
                                                                     "player_in_action": card.owner})

    elif card.turn_played is not None and game.status == GameStatus.WAITING_FOR_CHOOSE_SET:

        if not target_sets:
            raise HTTPException(400, "No fue seleccionado el set a robar")

        stolen_set = await set_service.read(session=session,id=target_sets[0])

        if not stolen_set:
            raise HTTPException(404, "No se encontro el set a robar")

        stolen_player = player_service.read(session=session, oid=stolen_set.owner)

        if stolen_set.game_id != game.id:
            raise HTTPException(400, "El set seleccionado no se encuentra en esta partida")

        if stolen_set.owner == card.owner:
            raise HTTPException(status_code=400, detail="No se puede robar un set propio")

        await set_service.update(session=session,id=stolen_set.id,data={"owner":card.owner, "turn_played":game.current_turn})

        await game_service.update(session=session, oid=game.id, data={"status": set_next_game_status(stolen_set, session, game),
                                                                      "player_in_action": card.owner})
        await card_service.update(session=session, oid=card.id, data={"owner": None,
                                                                      "turn_discarded": game.current_turn,
                                                                      "discarded_order": get_new_discarded_order(session=session, game_id=game.id)})
        
        set_cards_not_wilds = [x for x in stolen_set.detectives if x.name != "harley-quin-wildcard" and x.name != "ariadne-oliver"]
        detective_name =  set_cards_not_wilds[0].name.replace("_", " ").upper()
        await chat_service.create(session=session, data={"game_id": game.id, 
                                                         "content": f"{player.name} robó el set {detective_name} de {stolen_player.name}"})

    else:
        raise HTTPException(400, "Ya no se puede jugar eventos")
    
__ALL__ = ["another_victim"]