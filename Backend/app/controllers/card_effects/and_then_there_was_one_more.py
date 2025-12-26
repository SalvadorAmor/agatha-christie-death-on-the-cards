from fastapi import HTTPException
from typing import List
from sqlmodel import Session

from app.models.card import Card
from app.models.game import GameStatus
from app.services.card import CardService, get_new_discarded_order
from app.services.game import GameService, not_so_fast_status
from app.services.player import PlayerService
from app.services.secret import SecretService
from app.services.chat import ChatService


async def and_then_there_was_one_more(card: Card, session: Session, target_players: List[int]=[],
                                    target_secrets: List[int]=[], target_cards: List[int]=[], target_sets: List[int]=[], **kwargs):
    game_service = GameService()
    card_service = CardService()
    player_service = PlayerService()
    secret_service = SecretService()
    chat_service = ChatService()

    game = game_service.read(session=session, oid=card.game_id)
    player_card = player_service.read(session=session, oid=card.owner)

    if card.turn_played is None and game.status == GameStatus.TURN_START:

        await card_service.update(session=session, oid=card.id, data={"turn_played": game.current_turn})

        secrets_revealed = secret_service.search(session=session, filterby={"game_id__eq": game.id, "revealed__eq": True})

        if not secrets_revealed:
            await card_service.update(session=session, oid=card.id, data={"owner": None, "turn_discarded": game.current_turn,
                                                                          "discarded_order": get_new_discarded_order(session=session, game_id=game.id)})

            await game_service.update(session=session, oid=game.id, data={"status": GameStatus.FINALIZE_TURN, "player_in_action":None})
            await chat_service.create(session=session, data={"game_id": game.id, 
                                                             "content": f"{player_card.name} jugó un AND THEN THERE WAS ONE MORE sin secretos revelados, se descarta"})
            return

        await chat_service.create(session=session, data={"game_id": game.id, 
                                                        "content": f"{player_card.name} jugó un AND THEN THERE WAS ONE MORE"})

        canceled = await not_so_fast_status(game, session, card.id)

        if canceled:
            await card_service.update(session=session, oid=card.id, data={"owner": None,"turn_discarded": game.current_turn,
                                                                          "discarded_order": get_new_discarded_order(session=session, game_id=game.id)})
            await game_service.update(session=session, oid=card.game_id,data={"status": GameStatus.FINALIZE_TURN, "player_in_action": None})
            await chat_service.create(session=session, data={"game_id": game.id, "content": "la carta AND THEN THERE WAS ONE MORE fue cancelada"})
            return

        await game_service.update(session=session, oid=game.id, data={"status": GameStatus.WAITING_FOR_CHOOSE_PLAYER_AND_SECRET,
                                                                      "player_in_action":card.owner})
    elif card.turn_played is not None and game.status == GameStatus.WAITING_FOR_CHOOSE_PLAYER_AND_SECRET:
        if not target_secrets:
            raise HTTPException(400, "Se debe mandar un secreto a revelar")
        if not target_players:
            raise HTTPException(400, "Se debe mandar un jugador objetivo")

        secret = secret_service.read(session=session, oid=target_secrets[0])
        if not secret:
            raise HTTPException(404, "Secreto no existente")
        
        player = player_service.read(session=session, oid=target_players[0])
        if not player:
            raise HTTPException(404, "Jugador objetivo no existente")
        
        if secret.game_id != game.id:
            raise HTTPException(400, "No se puede robar un secreto de otra partida")
        secrets_player = player_service.read(session=session, oid=secret.owner)
        if not secret.revealed:
            raise HTTPException(400, "No se puede robar un secreto oculto")
        
        await secret_service.update(session=session,oid=target_secrets[0],data={"owner": target_players[0], "revealed":False})

        if player.social_disgrace:
            await player_service.update(session=session, oid=secret.owner, data={"social_disgrace": False})

        await card_service.update(session=session, oid=card.id, data={"owner": None, 
                                                                      "turn_discarded": game.current_turn, 
                                                                      "discarded_order": get_new_discarded_order(session=session, game_id=game.id)})
        await game_service.update(session=session, oid=game.id, data={"status": GameStatus.FINALIZE_TURN, "player_in_action":None})
        
        await chat_service.create(session=session, data={"game_id": game.id, 
                                                         "content": f"El secreto revelado de {secrets_player.name} fue oculto en los secretos de {player.name}"})

    else:
        raise HTTPException(400, "Ya no se puede jugar eventos")
    
__ALL__ = ["and_then_there_was_one_more"]

