import random
import secrets
from datetime import datetime
from typing import Optional, List

from fastapi import Depends, APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.database.engine import db_session
from app.models.card import CardType
from app.models.game import PublicGame, GameStatus
from app.models.player import Player
from app.models.secret import SecretType
from app.services.card import CreateCard, get_new_discarded_order
from app.services.detective_set import DetectiveSetService
from app.services.event_table import EventTableService
from app.services.game import GameService, CreateGame, GameFilter
from app.services.secret import CreateSecret, SecretService
from app.services.player import PlayerService, CreatePlayer
from app.services.card import CardService

# {"name":"", "content":"", "card_type":CardType,"amount":1},
CARDS = [
    #DEVIOUS
    {"name":"blackmailed", "content":"", "card_type":CardType.DEVIOUS,"amount":1},
    {"name":"social-faux-pas", "content":"", "card_type":CardType.DEVIOUS,"amount":3},
    #DETECTIVES
    {"name":"harley-quin-wildcard", "content":"", "card_type":CardType.DETECTIVE,"amount":4},
    {"name":"ariadne-oliver", "content":"", "card_type":CardType.DETECTIVE,"amount":3},
    {"name":"miss-marple", "content":"", "card_type":CardType.DETECTIVE,"amount":3},
    {"name":"parker-pyne", "content":"", "card_type":CardType.DETECTIVE,"amount":3},
    {"name":"tommy-beresford", "content":"", "card_type":CardType.DETECTIVE,"amount":2},
    {"name":"lady-eileen-bundle-brent", "content":"", "card_type":CardType.DETECTIVE,"amount":3},
    {"name":"tuppence-beresford", "content":"", "card_type":CardType.DETECTIVE,"amount":2},
    {"name":"hercule-poirot", "content":"", "card_type":CardType.DETECTIVE,"amount":3},
    {"name":"mr-satterthwaite", "content":"", "card_type":CardType.DETECTIVE,"amount":2},
    #EVENT
    {"name":"delay-the-murderers-escape", "content":"", "card_type":CardType.EVENT,"amount":3},
    {"name":"point-your-suspicions", "content":"", "card_type":CardType.EVENT,"amount":3},
    {"name":"dead-card-folly", "content":"", "card_type":CardType.EVENT,"amount":3},
    {"name":"another-victim", "content":"", "card_type":CardType.EVENT,"amount":2},
    {"name":"look-into-the-ashes", "content":"", "card_type":CardType.EVENT,"amount":3},
    {"name":"card-trade", "content":"", "card_type":CardType.EVENT,"amount":3},
    {"name":"and-then-there-was-one-more", "content":"", "card_type":CardType.EVENT,"amount":2},
    {"name":"early-train-to-paddington", "content":"", "card_type":CardType.EVENT,"amount":2},
    {"name":"cards-off-the-table", "content":"", "card_type":CardType.EVENT,"amount":1}
]

INSTANT_CARDS ={"name":"not-so-fast", "content":"", "card_type":CardType.INSTANT,"amount":10}
DEFAULT_SECRET={"name":"varios", "content":"", "type":SecretType.OTHER}
MURDER_SECRET={"name":"youre-the-murderer", "content":"", "type":SecretType.MURDERER}
ACCOMPLICE_SECRET= {"name":"youre-the-accomplice", "content":"", "type":SecretType.ACCOMPLICE}
AGATHA_DOY=259
game_router = APIRouter(prefix="/api/game")


class CreateGameDTO(BaseModel):
    game_name: str
    password: Optional[str] = None
    min_players: Optional[int] = None
    max_players: int
    player_name: str
    avatar: str
    birthday: datetime

class GameWithPlayerDTO(BaseModel):
    game: PublicGame
    player: Player

class UpdateGameDTO(BaseModel):
    status: Optional[GameStatus] = None
    current_turn: Optional[int] = None
    token: str

class DeleteGameDTO(BaseModel):
    token: str

@game_router.get('/{gid}', response_model=PublicGame)
def get_game(gid: int, session: Session = Depends(db_session)):
    service = GameService()
    game = service.read(session=session, oid=gid)

    if not game:
        raise HTTPException(404, detail="Juego no encontrado")
    return game

@game_router.post('/')
async def create_game(dto: CreateGameDTO, session: Session = Depends(db_session)):
    game_service = GameService()

    if dto.min_players:
        if dto.min_players < 2 or dto.min_players > 6:
            raise HTTPException(400, detail="La cantidad minima de jugadores debe estar entre 2 y 6")

    if dto.max_players < 2 or dto.max_players > 6:
        raise HTTPException(400, "La cantidad maxima de jugadores debe estar entre 2 y 6")

    if dto.max_players < dto.min_players:
        raise HTTPException(400, "La cantidad maxima de jugadores no debe ser menor a la cantidad minima")

    if dto.password:
        if len(dto.password) > 12:
            raise HTTPException(400, "La contraseña debe ser como maximo de 12 caracteres")

    if len(dto.game_name) > 12:
        raise HTTPException(400, "El nombre no debe superar los 12 caracteres")

    player_service = PlayerService()
    token = secrets.token_urlsafe(32)
    create_player_data = CreatePlayer(name=dto.player_name, date_of_birth=dto.birthday, token=token, avatar=dto.avatar)

    player = await player_service.create(session=session, data=create_player_data.model_dump())

    create_game_data = CreateGame(name=dto.game_name, password=dto.password, min_players=dto.min_players, max_players=dto.max_players, owner=player.id)
    game = await game_service.create(session=session, data=create_game_data.model_dump())

    player = await player_service.update(session=session, oid=player.id, data={"game_id": game.id})

    game_service.refresh(session, game)

    return GameWithPlayerDTO(game=game, player=player)

@game_router.delete('/{gid}', response_model=int)
async def delete_game(gid: int,dto: DeleteGameDTO, session: Session = Depends(db_session)):
    game_service = GameService()
    player_service = PlayerService()
    game = game_service.read(session=session, oid=gid)

    if not game:
        raise HTTPException(404, "No se pudo encontrar el juego")

    if game.status != GameStatus.WAITING:
        raise HTTPException(status_code=400,detail="No se puede eliminar una partida empezada")

    player = player_service.read(session=session,oid=game.owner)

    if player.token != dto.token:
        raise HTTPException(status_code=401, detail="No se puede eliminar partida por: Token Invalido")

    game.owner = None

    did = await game_service.delete(session=session,oid=gid)
    return did

def create_cards_for_game(gid:int, players: List[Player]):
    players_amount = len(players)
    expanded_cards = [c for c in CARDS for _ in range(c["amount"])]
    expanded_instant_cards = [INSTANT_CARDS for _ in range(INSTANT_CARDS["amount"]-players_amount)]
    prepare_cards_to_create = [*expanded_cards, *expanded_instant_cards]
    random.shuffle(prepare_cards_to_create)
    cards_to_create = [
        CreateCard(
            game_id=gid,
            name=card["name"],
            content=card["content"],
            card_type=card["card_type"],
            pile_order=i
        ) for i, card in enumerate(prepare_cards_to_create)]

    for i in range(players_amount*5):
        cards_to_create[-(i+1)].owner = players[i % players_amount].id

    cards_to_create.extend([CreateCard(
            game_id=gid,
            name=INSTANT_CARDS["name"],
            content=INSTANT_CARDS["content"],
            card_type=INSTANT_CARDS["card_type"],
            pile_order=i + len(prepare_cards_to_create),
            owner=players[(i+1) % players_amount].id
        ) for i in range(players_amount)])

    return cards_to_create

def create_murder_for_game(gid:int,pid:int):
    return CreateSecret(
                game_id=gid,
                owner=pid,
                name=MURDER_SECRET["name"],
                content=MURDER_SECRET["content"],
                revealed=False,
                type=MURDER_SECRET["type"]
            )

def create_secrets_for_game(gid:int,players:list[Player]):
    game_secrets = []
    random.shuffle(players)
    murder= players[0]
    accomplice = players[1]

    for p in players:
        has_secret = 1 if p == murder or p == accomplice else 0
        for i in range(3 - has_secret):
            game_secrets.append(
                CreateSecret(
                    game_id=gid,
                    owner=p.id,
                    name=DEFAULT_SECRET["name"],
                    content=DEFAULT_SECRET["content"],
                    revealed=False,
                    type=DEFAULT_SECRET["type"]
                )
            )

    game_secrets.append(create_murder_for_game(gid=gid,pid=murder.id))
    secret_data = ACCOMPLICE_SECRET if len(players) > 4 else DEFAULT_SECRET
    game_secrets.append(CreateSecret(
            game_id=gid,
            owner=accomplice.id,
            name=secret_data["name"],
            content=secret_data["content"],
            revealed=False,
            type=secret_data["type"]
            ))
    return game_secrets



@game_router.patch('/{gid}', response_model=PublicGame)
async def update_game(gid: int, dto: UpdateGameDTO, session: Session = Depends(db_session)):
    game_service = GameService()
    player_service = PlayerService()
    card_service = CardService()
    event_service = EventTableService()

    game = game_service.read(session=session,oid=gid)

    if not game:
        raise HTTPException(404, "No se pudo encontrar el juego")

    players = player_service.search(session=session,filterby={"game_id__eq":gid})

    if dto.status == GameStatus.STARTED and len(players) < 2:
        raise HTTPException(status_code=412,detail="Se necesitan minimo dos jugadores para empezar")

    if game.status == GameStatus.WAITING and dto.status == GameStatus.STARTED:
        owner = [p for p in players if p.id == game.owner]

        if owner[0].token != dto.token:
            raise HTTPException(401, "Token invalido")

        # Sorteo posiciones
        players.sort(key=lambda player: abs(player.date_of_birth.timetuple().tm_yday - AGATHA_DOY))
        for i in range(len(players)):
            players[i].position = i

        # Reparto secretos
        secrets = create_secrets_for_game(gid=gid,players=players)
        secret_service=SecretService()
        await secret_service.create_bulk(session=session,data=[s.model_dump(exclude_none=True) for s in secrets])

        # Reparto cartas
        cards = create_cards_for_game(gid=gid, players=players)
        card_service=CardService()
        await card_service.create_bulk(session=session, data=[c.model_dump(exclude_none=True) for c in cards])

        first_discarded = card_service.search(session=session,
                                              filterby={'game_id__eq': game.id,'turn_discarded__is_null': True,'owner__is_null': True},
                                              sortby="pile_order__desc",
                                              limit=1)[0]
        await card_service.update(session=session, oid=first_discarded.id, data={"turn_discarded":-1, "discarded_order":0})
        await game_service.update(session=session,oid=game.id,data={"status":GameStatus.STARTED})

        updated_game = await game_service.update(session=session, oid=gid, data={"status": GameStatus.TURN_START})
        return updated_game

    elif dto.current_turn:

        if game.status not in {GameStatus.FINALIZE_TURN,GameStatus.FINALIZE_TURN_DRAFT}:
            raise HTTPException(428, "No se puede terminar turno sin descartar o jugar una carta")

        amount_players = len(players)
        current_player = player_service.search(session=session,
                                               filterby={'position__eq':(game.current_turn % amount_players), 'game_id__eq': game.id})

        if current_player[0].token != dto.token:
            raise HTTPException(401, "Token invalido")

        current_player_cards = len(card_service.search(session=session,
                                                       filterby={'owner__eq':current_player[0].id, 'game_id__eq':game.id, "set_id__is_null":True}))

        if current_player_cards < 6:
            cards_to_pick = 6 - current_player_cards
            cards_to_update = card_service.search(session=session,
                                                  filterby={'game_id__eq': game.id, 'discarded_order__is_null': True, 'content__eq':"" ,
                                                            'owner__is_null': True}, limit=cards_to_pick,offset=3)

            for card in cards_to_update:
                await card_service.update(session=session, oid=card.id, data={'owner': current_player[0].id})

            if cards_to_update:
                cards_filter = card_service.search(session=session, filterby={"game_id__eq": gid,"owner__is_null": True,
                                                                              "turn_discarded__is_null": True,  'content__eq':""}, offset=3)

                if len(cards_filter) == 0:
                    dto.status = GameStatus.FINALIZED

        dto.status = GameStatus.FINALIZED if dto.status == GameStatus.FINALIZED else GameStatus.TURN_START

        not_so_fast_events = event_service.search(session=session, filterby={"game_id__eq": game.id, "turn_played__eq": game.current_turn,
                                                                             "action__eq": "to_cancel", "target_card__is_null":False})

        if not_so_fast_events:
            new_discarded_order = get_new_discarded_order(session=session, game_id=game.id)

            played_not_so_fast_cards = [e.target_card for e in not_so_fast_events]

            update_data = [{"turn_discarded": game.current_turn, "discarded_order": new_discarded_order + i, "owner": None}
                           for i,c in enumerate(played_not_so_fast_cards)]

            updated_cards = await card_service.bulk_update(session=session, oids=played_not_so_fast_cards, data=update_data)

        updated_game = await game_service.update(session=session, oid=gid,data={"current_turn":dto.current_turn, "status": dto.status})
        return updated_game

    else:
        raise HTTPException(status_code=400, detail="Actualizacion de partida invalida")

@game_router.post('/search', response_model=list[PublicGame])
def search_game(dto: GameFilter, session: Session = Depends(db_session)):
    service = GameService()
    games = service.search(session=session, filterby=dto.model_dump(exclude_none=True))
    return games