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

async def ariadne_oliver(card: Card, session: Session, target_players: List[int]=[],
                        target_secrets: List[int]=[], target_cards: List[int]=[], target_sets: List[int]=[], **kwargs):
    game_service = GameService()
    card_service = CardService()
    set_service = DetectiveSetService()
    player_service = PlayerService()
    chat_service = ChatService()

    game = game_service.read(session=session, oid=card.game_id)
    player = player_service.read(session=session, oid=card.owner)

    if card.turn_played is None and game.status == GameStatus.TURN_START:

        sets_in_game = set_service.search(session=session, filterby={"game_id__eq": game.id})
        other_players_sets = [s for s in sets_in_game if s.owner != card.owner]

        if not other_players_sets:
            raise HTTPException(400, "No se puede jugar el set Ariadne Oliver: No hay sets para agregarse")
        
        await chat_service.create(session=session, data={"game_id": game.id, 
                                                         "content": f"{player.name} jugó la carta ARIADNE OLIVER"})

        await card_service.update(session=session, oid=card.id, data={"turn_played": game.current_turn})

        canceled = await not_so_fast_status(game, session, card.id)

        if canceled:
            await CardService().update(session=session, oid=card.id, data={"turn_discarded": game.current_turn,
                                                                           "discarded_order": get_new_discarded_order(session=session, game_id=game.id),
                                                                           "owner": None})
            await game_service.update(session=session, oid=card.game_id,data={"status": GameStatus.FINALIZE_TURN, "player_in_action": None})
            return 200

        await game_service.update(session=session, oid=game.id, data={"status": GameStatus.WAITING_FOR_CHOOSE_SET, "player_in_action": card.owner})

    elif card.turn_played is not None and game.status == GameStatus.WAITING_FOR_CHOOSE_SET:

        if not target_sets:
            raise HTTPException(400, "No fue seleccionado el set a robar")

        detective_set = await set_service.read(session=session,id=target_sets[0])

        if not detective_set:
            raise HTTPException(404, "No se encontro el set a robar")

        if detective_set.game_id != game.id:
            raise HTTPException(400, "El set seleccionado no se encuentra en esta partida")
        
        stolen_player = player_service.read(session=session, oid=detective_set.owner)

        await set_service.update(session=session,data={"turn_played":game.current_turn,"detectives":card},id=detective_set.id)

        await game_service.update(session=session, oid=game.id, data={"status": GameStatus.WAITING_FOR_CHOOSE_SECRET,
                                                                      "player_in_action": detective_set.owner})
        
        set_cards_not_wilds = [x for x in detective_set.detectives if x.name != "harley-quin-wildcard" and x.name != "ariadne-oliver"]
        detective_name =  set_cards_not_wilds[0].name.replace("_", " ").upper()

        await chat_service.create(session=session, data={"game_id": game.id, 
                                                         "content": f"{player.name} agregó ARIADNE OLIVER al set {detective_name} de {stolen_player.name}"})

    else:
        raise HTTPException(400, "No se puede bajar el set Ariadne Oliver")

__ALL__ = ["ariadne_oliver"]