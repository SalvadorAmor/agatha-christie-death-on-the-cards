from typing import List, Optional

from fastapi import HTTPException
from sqlmodel import Session

from app.controllers.utils import reveal_secret
from app.models.game import GameStatus
from app.models.player import Player
from app.models.websocket import notify_game_players, WebsocketMessage
from app.services.card import CardService, get_new_discarded_order
from app.services.event_table import EventTableService
from app.services.game import GameService, not_so_fast_status
from app.models.card import Card
from app.services.player import PlayerService
from app.services.secret import SecretService
from app.services.chat import ChatService


async def point_your_suspicions(card: Card,  session:Session=None, target_players: List[int]=[], target_secrets: List[int]=[], issuer_player: Optional[Player]=None, **kwargs):
    game_service = GameService()
    player_service = PlayerService()
    event_table_service = EventTableService()
    chat_service = ChatService()

    game = game_service.read(session=session, oid=card.game_id)
    player = player_service.read(session=session, oid=card.owner)
    players = player_service.search(session=session, filterby={"game_id__eq": card.game_id})
    votos_filter = {"game_id__eq": card.game_id, "turn_played__eq": game.current_turn, "action__eq": "point_your_suspicions", "target_player__is_null": False}
    events = event_table_service.search(session=session, filterby=votos_filter)

    if game.status == GameStatus.TURN_START:
        # Pongo la carta en juego y cambio el estado del juego
        await CardService().update(session=session, oid=card.id, data={"turn_played":game.current_turn})

        await chat_service.create(session=session, data={"game_id": game.id, 
                                                         "content": f"{player.name} jugó la carta POINT YOUR SUSPICIONS"})

        canceled = await not_so_fast_status(game, session, card.id)

        if canceled:
            await CardService().update(session=session, oid=card.id, data={"turn_discarded": game.current_turn, "discarded_order": get_new_discarded_order(session=session, game_id=game.id), "owner": None})
            await game_service.update(session=session, oid=card.game_id, data={"status": GameStatus.FINALIZE_TURN, "player_in_action": None})
            await chat_service.create(session=session, data={"game_id": game.id, 
                                                         "content": f"La carta POINT YOUR SUSPICIONS fue cancelada"})
            return 200

        await game_service.update(session=session, oid=game.id, data={"status": GameStatus.WAITING_FOR_CHOOSE_PLAYER, "player_in_action": None})
    elif game.status == GameStatus.WAITING_FOR_CHOOSE_PLAYER:
        if not target_players:
            raise HTTPException(status_code=400, detail="Debes señalar a un jugador")
        if target_players[0] not in [p.id for p in players]:
            raise HTTPException(status_code=400, detail="El jugador señalado no está en la partida")

        # Handeleo las elecciones de los jugadores
        await event_table_service.create(session=session, data={
            "game_id": game.id,
            "player_id": issuer_player.id,
            "action": "point_your_suspicions",
            "turn_played": game.current_turn,
            "target_player": target_players[0],
        })
        target_player = player_service.read(session=session, oid=target_players[0])
        await chat_service.create(session=session, data={"game_id": game.id, 
                                                         "content": f"{issuer_player.name} apuntó a {target_player.name} como sospechoso"})

        events = event_table_service.search(session=session, filterby=votos_filter)

        all_players_answered = len(events) >= len(players)
        if all_players_answered:
            vote_count = {}
            for event in events:
                if event.target_player not in vote_count:
                    vote_count[event.target_player] = 0
                vote_count[event.target_player] += 1

            # Check for ties among the most voted players
            max_votes = max(vote_count.values())
            most_voted_players = [player_id for player_id, count in vote_count.items() if count == max_votes]

            if len(most_voted_players) > 1:
                names = ""
                for voted_player in most_voted_players:
                    actual_player = player_service.read(session=session, oid=voted_player)
                    names = names + f"{actual_player.name}, "
                await chat_service.create(session=session, data={"game_id": game.id, 
                                                                 "content": f"{names} empataron, {player.name} desempata"})
                await game_service.update(session=session, oid=game.id, data={"player_in_action": card.owner, "status": GameStatus.WAITING_FOR_CHOOSE_PLAYER})
            else:
                most_voted_player_id = most_voted_players[0]
                player_suspicious = player_service.read(session=session, oid=most_voted_player_id)
                await chat_service.create(session=session, data={"game_id": game.id, 
                                                                 "content": f"{player_suspicious.name} fue elegido como sospechoso, debe revelar un secreto"})
                await game_service.update(session=session, oid=game.id, data={"player_in_action": most_voted_player_id, "status": GameStatus.WAITING_FOR_CHOOSE_SECRET})
    elif game.status == GameStatus.WAITING_FOR_CHOOSE_SECRET:
        if not target_secrets:
            raise HTTPException(status_code=400, detail="Debes señalar un secreto")

        secret = SecretService().read(session=session, oid=target_secrets[0])
        if secret.owner != game.player_in_action:
            raise HTTPException(status_code=400, detail="El secreto señalado no pertenece al jugador en acción")
        if secret.revealed:
            raise HTTPException(status_code=400, detail="El secreto señalado ya fue revelado")
        if await reveal_secret(session, secret) == "effect_applied":
            await game_service.update(session=session, oid=game.id, data={"status": GameStatus.FINALIZE_TURN, "player_in_action": None})
            await chat_service.create(session=session, data={"game_id": game.id, 
                                                             "content": f"El sospechoso reveló un secreto"})
            await CardService().update(session=session, oid=card.id, data={"turn_discarded": game.current_turn, "discarded_order": get_new_discarded_order(session=session, game_id=game.id), "owner": None})

    return 200





__ALL__ = ["delay_the_murderers_escape"]