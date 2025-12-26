from enum import Enum

from app.models.game import GameStatus
from app.models.secret import Secret, SecretType
from app.services.game import GameService
from app.services.player import PlayerService
from app.services.secret import SecretService


async def reveal_secret(session, secret: Secret):
    game_service = GameService()
    player_service = PlayerService()
    secret_service = SecretService()
    await secret_service.update(session=session, oid=secret.id, data={"revealed": True})

    if secret.name == "youre-the-murderer":
        await game_service.update(session=session, oid=secret.game_id, data={"status": GameStatus.FINALIZED,
                                                                      "player_in_action": None})
        return "game_finalized"

    secrets_left = secret_service.search(session=session,
                                         filterby={"owner__eq": secret.owner, "revealed__eq": False})

    if not secrets_left:
        await player_service.update(session=session, oid=secret.owner, data={"social_disgrace": True})

    game_hidden_secrets = secret_service.search(session=session,filterby={"game_id__eq": secret.game_id, "revealed__eq": False})

    murder_accomplice = {s.owner for s in game_hidden_secrets if
                         s.type == SecretType.MURDERER or s.type == SecretType.ACCOMPLICE}

    if all(s.owner in murder_accomplice for s in game_hidden_secrets):

        await game_service.update(session=session, oid=secret.game_id,data={"status": GameStatus.FINALIZED, "player_in_action": None})

        return "game_finalized"

    return "effect_applied"

class PlayerOrders(Enum):
    CLOCKWISE = "clockwise"
    COUNTER_CLOCKWISE = "counter-clockwise"