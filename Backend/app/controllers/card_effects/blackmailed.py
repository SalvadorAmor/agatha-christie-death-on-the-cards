from sqlmodel import Session
from typing import List
from fastapi import HTTPException

from app.models.websocket import notify_game_players, WebsocketMessage
from app.models.card import Card
from app.models.game import GameStatus

from app.services.game import GameService
from app.services.event_table import EventTableService
from app.services.player import PlayerService
from app.services.card import CardService, get_new_discarded_order
from app.services.chat import ChatService

from app.controllers.card_effects.devious_detect import devious_detect

async def blackmailed(card: Card, session: Session, target_players: List[int]=[],
                target_secrets: List[int]=[], target_cards: List[int]=[], target_sets: List[int]=[], **kwargs):
    
    game_service = GameService()
    event_table_service = EventTableService()
    player_service = PlayerService()
    card_service = CardService()
    chat_service = ChatService()

    game = game_service.read(session=session, oid=card.game_id)

    if card.turn_played != game.current_turn:
        raise HTTPException(400, "La devious no esta en juego")

    if game.status == GameStatus.WAITING_FOR_CHOOSE_SECRET:

        if len(target_secrets) == 0:
            raise HTTPException(412, "Debes seleccionar secretos a revelar en privado")

        event = event_table_service.search(session=session, filterby={"target_card__eq": card.id, 
                                                                      "turn_played__eq": game.current_turn,
                                                                      "completed_action__eq": True})
        
        player_in_action = player_service.read(session=session, oid=event[0].player_id)
        player_to_reveal = player_service.read(session=session, oid=event[0].target_player)

        if game.player_in_action != player_in_action.id:
            raise HTTPException(400, "Evento devious incorrecto")
        
        await notify_game_players(game.id,
                                  WebsocketMessage(model="devious", action="show-secret", 
                                                          data={"secret_id": target_secrets[0], "dest_user": player_in_action.id}, 
                                                          dest_game=game.id))
        
        await chat_service.create(session=session, data={"game_id": game.id, "content":f"{player_to_reveal.name} reicibió un BLACKMAILED y le mostro un secreto a {player_in_action.name}"})
        
        await card_service.update(session=session, oid=card.id, data={"turn_discarded": game.current_turn,
                                                                      "owner": None,
                                                                      "discarded_order": get_new_discarded_order(session=session, game_id=game.id),
                                                                      "turn_played": None})
        
        await devious_detect(session=session, game=game)
    
        
__ALL__ = ["blackmailed"]