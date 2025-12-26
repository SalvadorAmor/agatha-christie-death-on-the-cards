from fastapi import HTTPException
from typing import List
from sqlmodel import Session


from app.models.card import Card
from app.models.game import GameStatus
from app.services.card import CardService, get_new_discarded_order
from app.services.game import GameService
from app.services.player import PlayerService
from app.services.chat import ChatService


async def cards_off_the_table(card: Card, session: Session, target_players: List[int],
                            target_secrets: List[int] = [], target_cards: List[int]=[], target_sets: List[int]=[], **kwargs):

    card_service = CardService()
    player_service = PlayerService()
    game_service = GameService()
    chat_service = ChatService()

    game = game_service.read(session=session, oid=card.game_id)

    if card.turn_played is None and game.status == GameStatus.TURN_START:

        player = player_service.read(session=session, oid=card.owner)
        await card_service.update(session=session, oid=card.id, data={"turn_played": game.current_turn})
        await game_service.update(session=session, oid=game.id, data={"status": GameStatus.WAITING_FOR_CHOOSE_PLAYER, "player_in_action":player.id})
        await chat_service.create(session=session, data={"game_id": game.id, 
                                                         "content": f"{player.name} jugó la carta CARDS OFF THE TABLE"})

    elif card.turn_played is not None and game.status == GameStatus.WAITING_FOR_CHOOSE_PLAYER:
        if len(target_players) != 1:
            raise HTTPException(400, "Cantidad erronea de jugadores objetivos")

        if card.turn_played != game.current_turn:
            raise HTTPException(400, "No se puede relanzar una carta jugada")

        target_player_id = target_players[0]
        target_player = player_service.read(session=session, oid=target_player_id)

        if not target_player:
            raise HTTPException(404, "Jugador objetivo no existente")

        if target_player.game_id != card.game_id:
            raise HTTPException(400, "Jugador no existente en esta partida")

        cards_to_discard = card_service.search(session=session, filterby={"owner__eq":target_player_id,
                                                                            "name__eq": "not-so-fast"})
        cards_discarded = 0
        if len(cards_to_discard) != 0:

            new_discarded_order = get_new_discarded_order(session=session, game_id=card.game_id)

            for iteration,actual_card in enumerate(cards_to_discard):
                await card_service.update(session=session, oid=actual_card.id, data={"turn_discarded": game.current_turn,
                                                                            "discarded_order": new_discarded_order + iteration,
                                                                            "owner": None})
            cards_discarded += 1

        new_discarded_order = get_new_discarded_order(session=session, game_id=card.game_id)


        await card_service.update(session=session, oid=card.id, data={"turn_discarded": game.current_turn,
                                                                    "discarded_order": new_discarded_order,
                                                                    "owner": None})

        await chat_service.create(session=session, data={"game_id": game.id, 
                                                         "content": f"la carta CARDS OFF THE TABLE descartó {cards_discarded} Not So Fast a {target_player.name}"})
        
        await game_service.update(session=session, oid=game.id, data={"status": GameStatus.FINALIZE_TURN, "player_in_action":None})
    else:
        raise HTTPException(400, "Ya no se puede jugar eventos")
    
__ALL__ = ["cards_off_the_table"]