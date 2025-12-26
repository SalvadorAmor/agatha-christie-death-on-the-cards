from typing import List, Optional

from fastapi import HTTPException
from sqlmodel import Session

from app.models.game import GameStatus
from app.models.player import Player
from app.services.card import CardService, get_new_discarded_order
from app.services.event_table import EventTableService
from app.services.game import GameService, not_so_fast_status
from app.models.card import Card, CardType
from app.services.player import PlayerService
from app.services.chat import ChatService
from app.controllers.card_effects.devious_detect import devious_detect


async def card_trade(card: Card, session:Session=None, issuer_player: Optional[Player] = None, target_players: List[int]=[], target_cards: List[int]=[], **kwargs):
    game_service = GameService()
    event_table_service = EventTableService()
    player_service = PlayerService()
    chat_service = ChatService()

    game = game_service.read(session=session, oid=card.game_id)
    player = player_service.read(session=session, oid=card.owner)

    if game.status == GameStatus.TURN_START:
        # Pongo la carta en juego y cambio el estado del juego
        await CardService().update(session=session,oid=card.id,data={"turn_played":game.current_turn})

        await chat_service.create(session=session, data={"game_id": game.id, 
                                                         "content": f"{player.name} jugó la carta CARD TRADE"})

        canceled = await not_so_fast_status(game, session, card.id)

        if canceled:
            await CardService().update(session=session, oid=card.id, data={"turn_discarded": game.current_turn,
                                                                           "discarded_order": get_new_discarded_order(
                                                                               session=session, game_id=game.id),
                                                                           "owner": None})
            await game_service.update(session=session, oid=card.game_id,
                                      data={"status": GameStatus.FINALIZE_TURN, "player_in_action": None})
            await chat_service.create(session=session, data={"game_id": game.id, 
                                                             "content": f"La carta CARD TRADE fue cancelada"})
            return 200

        await game_service.update(session=session, oid=game.id, data={"status": GameStatus.WAITING_FOR_CHOOSE_PLAYER, "player_in_action": card.owner})
    elif game.status == GameStatus.WAITING_FOR_CHOOSE_PLAYER:
        if not target_players:
            raise HTTPException(status_code=400, detail="Debes señalar a un jugador")
        if target_players[0] == card.owner:
            raise HTTPException(status_code=400, detail="No puedes señalarte a ti mismo")
        await event_table_service.create(session=session, data={
            "game_id": game.id,
            "player_id": card.owner,
            "action": "card_trade",
            "turn_played": game.current_turn,
            "target_player": target_players[0],
            "completed_action": True
        })
        target_player = player_service.read(session=session, oid=target_players[0])
        await chat_service.create(session=session, data={"game_id": game.id, 
                                                         "content": f"{player.name} eligió a {target_player.name} para intercambiar una carta"})
        await game_service.update(session=session, oid=game.id, data={"status": GameStatus.SELECT_CARD_TO_TRADE})

    elif game.status == GameStatus.SELECT_CARD_TO_TRADE:
        if not target_cards:
            raise HTTPException(status_code=400, detail="Debes señalar una carta")
        my_cards = CardService().search(session=session, filterby={"game_id__eq": game.id, "owner__eq": issuer_player.id, "turn_discarded__is_null": True})
        if target_cards[0] not in [c.id for c in my_cards]:
            raise HTTPException(status_code=400, detail="La carta señalada no te pertenece")

        target_card = CardService().read(session=session, oid=target_cards[0])

        first_event_table = event_table_service.search(session=session, filterby={
            "game_id__eq": card.game_id,
            "turn_played__eq": game.current_turn,
            "action__eq": "card_trade",
            "target_card__is_null": True
        })

        await event_table_service.create(session=session, data={
            "game_id": game.id,
            "player_id": issuer_player.id,
            "action": "card_trade",
            "turn_played": game.current_turn,
            "target_card": target_cards[0],
            "target_player": first_event_table[0].target_player if issuer_player.id == first_event_table[0].player_id else first_event_table[0].player_id,
            "completed_action": target_card.card_type != CardType.DEVIOUS
        })

        selected_cards_event = event_table_service.search(session=session, filterby={
            "game_id__eq": card.game_id,
            "turn_played__eq": game.current_turn,
            "action__eq": "card_trade",
            "target_card__is_null": False
        })


        if len(selected_cards_event) >= 2:
            selected_card_event_1 = selected_cards_event[0]
            card1 = CardService().read(session=session, oid=selected_card_event_1.target_card)
            selected_card_event_2 = selected_cards_event[1]
            card2 = CardService().read(session=session, oid=selected_card_event_2.target_card)
            # Un swap de toda la vida
            card1_owner = card1.owner
            await CardService().update(session=session, oid=card1.id, data={"owner": card2.owner})
            await CardService().update(session=session, oid=card2.id, data={"owner": card1_owner})

            await CardService().update(session=session, oid=card.id, data={"turn_discarded": game.current_turn,
                                                                     "discarded_order": get_new_discarded_order(
                                                                        session=session, game_id=game.id),
                                                                     "owner": None,
                                                                     "turn_played": None})
            
            await chat_service.create(session=session, data={"game_id": game.id, 
                                                            "content": f"Se han intercambiado las cartas"})
            
            await devious_detect(session=session, game=game)
            

    return 200





__ALL__ = ["card_trade"]