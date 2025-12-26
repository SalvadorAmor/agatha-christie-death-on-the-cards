/* eslint-disable react-hooks/rules-of-hooks */
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Card, DiscardedCard, TableCard } from "./components/Card.tsx";
import { Action } from "./components/Action.tsx"
import WinDialog from "../../components/WinDialog.tsx";

import PlayerService from "../../services/PlayerService";
import EventTableService from "../../services/EventTableService.ts";
import poirot from "../../assets/pfp-hercule-poirot.jpg";
import marple from "../../assets/pfp-miss-marple.jpg";
import pyne from "../../assets/pfp-parker-pyne.jpg";
import satterhwaite from "../../assets/pfp-mr-satterhwaite.jpg";
import brent from "../../assets/pfp-lady-eileen-brent.jpg";
import tommy from "../../assets/pfp-tommy-beresford.jpg";
import tuppence from "../../assets/pfp-tuppence-beresford.jpg";
import oliver from "../../assets/pfp-ariadne-oliver.jpg";
import CardService from "../../services/CardService.ts";
import SecretService from "../../services/SecretService.ts";
import { Secret } from "./components/Secret.tsx";
import GameService from "../../services/GameService.ts";
import dorso from "../../assets/dorso.png";
import lost from "../../assets/lost.png";
import WebSocketManager from "../../components/WebSocketManager.tsx";
import MyPlayerSets from "../../components/MyPlayerSets.tsx";
import SetService from "../../services/SetService.ts";
import OpponentPlayerSets from "../../components/OpponentPlayerSets.tsx";
import SelectedCardsActionBar from "./components/SelectedCardsActionBar.tsx";
import useLookIntoTheAshes from "../../Hooks/useLookIntoTheAshes.tsx";
import useDelay from "../../Hooks/useDelay.tsx";
import LookIntoTheAshesModal from "../../components/LookIntoTheAshesModal";
import DelayModal from "../../components/DelayModal.tsx";
import FollyModal from "../../components/FollyModal.tsx";
import type { C } from "vitest/dist/chunks/environment.d.cL3nLXbE.js";
import GameChat from "../../components/GameChat.tsx";
import ChatService from "../../services/ChatService.ts";
import { darkButtonStyle, redButtonStyle, whiteButtonStyle } from "../../components/Button.jsx";
import ShowPrivateSecretModal from "../../components/ShowPrivateSecretModal.tsx";
import useJustAdded from "../../Hooks/useJustAdded.ts";


const GameStatus = {
  WAITING: "waiting",
  STARTED: "started",
  TURN_START: "turn_start",
  WAITING_FOR_CHOOSE_PLAYER: "waiting_for_choose_player",
  WAITING_FOR_CHOOSE_DISCARDED: "waiting_for_choose_discarded",
  WAITING_FOR_ORDER_DISCARD: "waiting_for_order_discard",
  WAITING_FOR_CHOOSE_PLAYER_AND_SECRET: "waiting_for_choose_player_and_secret",
  WAITING_FOR_CHOOSE_SECRET: "waiting_for_choose_secret",
  WAITING_FOR_CHOOSE_SET: "waiting_for_choose_set",
  WAITING_FOR_CANCEL_ACTION: "waiting_for_cancel_action",
  SELECT_CARD_TO_TRADE: "select_card_to_trade",
  FINALIZE_TURN: "finalize_turn",
  WAITING_TO_CHOOSE_DIRECTION: "waiting_to_choose_direction",
  FINALIZE_TURN_DRAFT: "finalize_turn_draft",
  FINALIZED: "finalized",
} as const;

type GameStatus = typeof GameStatus[keyof typeof GameStatus];


export type Player = {
  id: number;
  name: string;
  avatar: string;
  position: number;
  board_position: number;
  token: string;
  social_disgrace: boolean;
};

export type Game = {
  id: number;
  name: string;
  status: GameStatus;
  current_turn: number;
  min_players: number;
  max_players: number;
  owner: number;
  player_in_action: number;
};

export type Secret = {
  id: number;
  owner: number;
  name: string;
  revealed: boolean;
  type: string;
};

export type Card = {
  id: number;
  name: string;
  owner: number;
  discarded_order: number;
  turn_played: number;
};

export type DetectiveSet = {
  id: number;
  owner: number;
  detectives: Card[];
  turn_played: number;
}

const ACTION_STATES: GameStatus[] = [GameStatus.WAITING_FOR_CHOOSE_PLAYER, GameStatus.WAITING_FOR_CHOOSE_SECRET, GameStatus.WAITING_FOR_CHOOSE_PLAYER_AND_SECRET,
                                    GameStatus.WAITING_FOR_CHOOSE_SET, GameStatus.WAITING_FOR_CANCEL_ACTION, GameStatus.SELECT_CARD_TO_TRADE]

const AVATARS = [
  { id: "detective1", label: "Hercule Poirot", src: poirot },
  { id: "detective2", label: "Miss Marple", src: marple },
  { id: "detective3", label: "Mr Satterhwaite", src: satterhwaite },
  { id: "detective4", label: "Parker Pyne", src: pyne },
  { id: "detective5", label: "Lady Eileen Brent", src: brent },
  { id: "detective6", label: "Tommy Beresford", src: tommy },
  { id: "detective7", label: "Tuppence Beresford", src: tuppence },
  { id: "detective8", label: "Ariadne Oliver", src: oliver },
] as const;

/*PANTALLA*/
const positionStyles: Record<string, string> = {
  bottom:
    "absolute bottom-10 md:left-90/100 lg:left-80/100 transform -translate-x-1/2",
  top: "absolute top-4 left-1/2 transform -translate-x-1/2",
  left: "absolute left-4 top-1/2 transform -translate-y-1/2",
  right: "absolute right-4 top-1/2 transform -translate-y-1/2",
  "left-top": "absolute left-8 top-1/4 transform -translate-y-1/2",
  "left-bottom": "absolute left-8 top-60/100 transform -translate-y-1/2",
  "right-top": "absolute right-8 top-1/4 transform -translate-y-1/2",
  "right-bottom": "absolute right-8 top-60/100 transform -translate-y-1/2",
};

/*Jugadores y pantalla --> ver ticket*/
function usePositions(count: number) {
  const map: Record<number, string[]> = {
    2: ["bottom", "top"],
    3: ["bottom", "right", "left"],
    4: ["bottom", "right", "top", "left"],
    5: ["bottom", "right-bottom", "right-top", "left-top", "left-bottom"],
    6: [
      "bottom",
      "right-bottom",
      "right-top",
      "top",
      "left-top",
      "left-bottom",
    ],
  };
  return map[count] || [];
}

const handleUpdateCards = async ( gameId, playerId, setCards, setDrawDeck, setDiscardDeck, setGame, setHasDiscarded, setPlayedCard ) => {
  const my_cs = await CardService.search({ owner__eq: playerId });
  setCards(my_cs.sort((card1: Card, card2: Card) => { return card1.id - card2.id }));
  const draw_cs = await CardService.search({
    game_id__eq: gameId,
    turn_discarded__is_null: true,
    owner__is_null: true,
    content__eq:"",
  });
  setDrawDeck(draw_cs);
  const discard_cs = await CardService.search({
    game_id__eq: gameId,
    turn_discarded__is_null: false,
    owner__is_null: true,
  });
  setDiscardDeck(discard_cs.sort((c1:Card, c2:Card) => {return c1.discarded_order - c2.discarded_order}));
  GameService.read(gameId).then(async (data) => {
    setGame(data);
    const discarded_this_turn = await CardService.search({
      turn_discarded__eq: data.current_turn,
      game_id__eq: gameId,
    });
    setHasDiscarded(discarded_this_turn.length > 0);
    CardService.search({game_id__eq:gameId, turn_played__eq:data.current_turn})
      .then((response:Card[]) => {setPlayedCard(response[0])})
  });
  
};

const updateCards = async ( data, gameId, playerId, setCards, setDrawDeck, setDiscardDeck, setGame, setHasDiscarded, setPlayedCard) => {
  if (Array.isArray(data)) {
    const first = data[0];
    if (first && first.game_id === gameId) {
      await handleUpdateCards( gameId, playerId, setCards, setDrawDeck, setDiscardDeck, setGame, setHasDiscarded, setPlayedCard );
    }
  } else {
    if (data.game_id === gameId) {
      await handleUpdateCards( gameId, playerId, setCards, setDrawDeck, setDiscardDeck, setGame, setHasDiscarded, setPlayedCard  );
    }
  }
};

const updatePlayers = async (data, gameId, setPlayers, myPlayerPosition) => {
  if (data.game_id === gameId) {
    PlayerService.search({ game_id__eq: gameId }).then((ps) => {
      const jugadoresPosiciones = ps.map((p: Player) => ({
        ...p,
        board_position: (p.position - myPlayerPosition + ps.length) % ps.length,
      }));

      const playersAlias = jugadoresPosiciones.map((j: Player) => ({
        ...j,
        avatar: (AVATARS.find((a) => a.id === j.avatar) || AVATARS[0]).src,
      }));

      playersAlias.sort(
        (p1: Player, p2: Player) => p1.board_position - p2.board_position
      );
      setPlayers(playersAlias);
    });
  }
};


const updateSecrets = async (data, gameId, setSecrets) => {
  if (data.game_id === gameId) {
    setSecrets(await SecretService.search({ game_id__eq: gameId }));
  }
};

const updateGame = (data, gameId, setGame) => {
  if (data.id && data.id === gameId) {
    setGame(data);
  }
};


export default function Game() {
  const { gid } = useParams<{ gid: string }>();
  const [game, setGame] = useState<Game | null>(null);
  const [players, setPlayers] = useState<Player[]>([]);
  const [myPlayer, setMyPlayer] = useState<Player | null>(null);
  const [cards, setCards] = useState<Card[]>([]);
  const [secrets, setSecrets] = useState<Secret[]>([]);
  const [selectedCards, setSelectedCards] = useState<number[]>([]);
  const [myTurn, setMyTurn] = useState<boolean | null >(null);
  const [hasDiscarded, setHasDiscarded] = useState(false);
  const navigate = useNavigate();
  const [drawDeck, setDrawDeck] = useState<Card[]>([]);
  const [discardDeck, setDiscardDeck] = useState<Card[]>([]);
  const [tableCards, setTableCards] = useState<Card[]>([]);
  const [pickedCards, setPickedCards] = useState<number[]>([]);
  const [choosePlayer, setChoosePlayer] = useState<boolean>(false);
  const [targetPlayer, setTargetPlayer] = useState<number | null>(null);
  const [chooseOwnPlayer, setChooseOwnPLayer] = useState<boolean>(false);
  const [chooseOwnSecret, setChooseOwnSecret] = useState<boolean>(false);
  const [chooseTheirSecret, setChooseTheirSecret] = useState<boolean>(false);
  const [chooseRevealedSecret, setChooseRevealedSecret] = useState<boolean>(false);
  const [targetSecret, setTargetSecret] = useState<number | null>(null);
  const [chooseSet, setChooseSet] = useState<boolean>(false);
  const [targetSet, setTargetSet] = useState<number | null>(null);
  const [targetName, setTargetName] = useState<string>("");
  const [socialDisgrace, setSocialDisgrace] = useState<boolean>(false);
  const [cancelActionSecondsLeft, setCancelActionSecondsLeft] = useState<number | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatOpen, setChatOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [eventPopup, setEventPopup] = useState<ChatMessage | null>(null);

  // const isInSocialDisgrace = myPlayer?.social_disgrace;


  const isInSocialDisgrace = myPlayer?.social_disgrace;
  
  const [playedCard, setPlayedCard] = useState<Card | null>(null)
  const [alreadyVoted, setAlreadyVoted] = useState<boolean>(false);
  const [selectedToTrade, setSelectedToTrade] = useState<boolean>(false);
  const [showSecretModalOpen, setShowSecretModalOpen] = useState(false);
  const [secretToShow, setSecretToShow] = useState<Secret | null>(null);
  
  const justAddedTable = useJustAdded(tableCards);

  useEffect(() => {
    if (!game) return;
    setSelectedCards([]); 
    if (game.status !== GameStatus.WAITING_FOR_CANCEL_ACTION) {
      setCancelActionSecondsLeft(null);
    }
    setPickedCards([]);
  }, [game?.status]);


  useEffect(() => {
    if (!gid) return;
    GameService.read(parseInt(gid)).then((g) => setGame(g));

    const localPlayer = localStorage.getItem("player");

    if (!localPlayer || JSON.parse(localPlayer).game_id != gid) {
      navigate("/");
    } else {
      const parsedPlayer = JSON.parse(localPlayer);
      PlayerService.read(parsedPlayer.id).then((p) => {
        const updatedPlayer = { ...p, token: parsedPlayer.token };
        localStorage.setItem("player", JSON.stringify(updatedPlayer));
        setMyPlayer(updatedPlayer);
      });
    }
  }, [gid, navigate]);

  useEffect(() => {
    if (!game || !myPlayer) return;

    PlayerService.search({ game_id__eq: game.id }).then((ps) => {
      const jugadoresPosiciones = ps.map((p: Player) => ({
        ...p,
        board_position:
          (p.position - myPlayer.position + ps.length) % ps.length,
      }));

      const playersAlias = jugadoresPosiciones.map((j: Player) => ({
        ...j,
        avatar: (AVATARS.find((a) => a.id === j.avatar) || AVATARS[0]).src,
      }));

      playersAlias.sort(
        (p1: Player, p2: Player) => p1.board_position - p2.board_position
      );
      setPlayers(playersAlias);
      // Sincronizo social disgrace con player si no se renderiza mal
      const myPlayerData = playersAlias.find(p => p.id === myPlayer.id);
        setSocialDisgrace(myPlayerData?.social_disgrace ?? false);
    });
  }, [game, myPlayer]);

  useEffect(() => {
    if (!game || !myPlayer || !players) return;

    CardService.search({ owner__eq: myPlayer.id, set_id__is_null: true }).then((cs) => {
      setCards(cs);
    });

    CardService.search({
      game_id__eq: game.id,
      turn_discarded__is_null: true,
      owner__is_null: true,
      content__eq:"",
    }).then((cs) => {
      setDrawDeck(cs); setTableCards(cs.slice(0, 3));
    });

    CardService.search({
      game_id__eq: game.id,
      turn_discarded__is_null: false,
      owner__is_null: true,
    }).then((cs) => setDiscardDeck(cs.sort((c1:Card, c2:Card) => {return c1.discarded_order - c2.discarded_order})));

    SecretService.search({ game_id__eq: game.id }).then((sec: Secret[]) => {
      setSecrets(sec.sort((a,b) => a.id - b.id));
    });

    setMyTurn(myPlayer.position === game.current_turn % players.length);
  }, [players, myPlayer, game]);

  useEffect(() => {
    if (!game) return;

    CardService.search({
      turn_discarded__eq: game.current_turn,
      game_id__eq: game.id,
    }).then((cardsDiscarded) => {
      setHasDiscarded(cardsDiscarded.length > 0);
    });
    CardService.search({game_id__eq:game.id, turn_played__eq:game.current_turn})
      .then((response:Card[]) => {
        console.log(response)
        setPlayedCard(response[0])})
  }, [game]);

  useEffect(() => {
    if(!game || !myPlayer || players.length == 0) return;

    if(game.status == GameStatus.WAITING_FOR_CHOOSE_PLAYER && 
      (game.player_in_action == myPlayer.id || game.player_in_action == null)){
        setChoosePlayer(true);
      setTargetName('jugador objetivo');
    }
    else if(game.status == GameStatus.WAITING_FOR_CHOOSE_SECRET && game.player_in_action == myPlayer.id){
      const current_position = game.current_turn % players.length; //para que la posicion actual dependa de "como va la ronda"
      const isMyTurn = myPlayer.position == current_position;
      if(playedCard && playedCard.turn_played == game.current_turn && game.player_in_action == myPlayer.id && playedCard?.name != "another-victim"){
        console.warn(playedCard)
        if(playedCard.name == "blackmailed"){
          console.warn("ajeno")
          setChooseTheirSecret(true);
          setChooseOwnSecret(false);
          setTargetName('secreto ajeno objetivo');
        }
        else{
          console.warn("propio")
          setChooseOwnSecret(true);
          setChooseTheirSecret(false);
          setTargetName('secreto propio objetivo');
        }
      }
      else{
        if(isMyTurn){
          setChooseTheirSecret(true);
          setTargetName('secreto ajeno objetivo');
        }
        else{
          setChooseOwnSecret(true);
          setTargetName('secreto propio objetivo');
        }
        SetService.search({turn_played__eq: game.current_turn, game_id__eq: game.id})
          .then((set) => {
            if(set.length > 1 || set.length == 0) return;

            const parkerPyne = set[0].detectives.some((detective: Card) => detective.name == 'parker-pyne');
            if(parkerPyne){
              setChooseOwnSecret(false);
              setChooseTheirSecret(false);
              setChooseRevealedSecret(true);
              setTargetName('secreto revelado objetivo');
            }
        })
      }
      
    }
    else if(game.status == GameStatus.WAITING_FOR_CHOOSE_PLAYER_AND_SECRET && game.player_in_action == myPlayer.id){
      setChooseRevealedSecret(true);
      setChoosePlayer(true);
      setChooseOwnPLayer(true);
      setTargetName('secreto revelado y jugador objetivo');
    }
    else if(game.status == GameStatus.WAITING_FOR_CHOOSE_SET && game.player_in_action == myPlayer.id){
      setChooseSet(true);
      const target = playedCard?.name == "another-victim" ? "set objetivo a robar" : "set a agregarse"
      setTargetName(target);
    }
    else if(game.status == GameStatus.SELECT_CARD_TO_TRADE){
      setTargetName('carta a tradear');
      if(playedCard?.name == "dead-card-folly"){
        setSelectedToTrade(true);
      }
    }
  },[game, myPlayer, players, playedCard])


  // Setup websockets
  useEffect(() => {
    if (!gid || !myPlayer) return;
    const gameId = parseInt(gid);
    if (isNaN(gameId)) return;
    const wsmanager = new WebSocketManager(myPlayer.token);
    wsmanager.registerOnUpdate((data) => { updateGame(data, gameId, setGame); }, "game");
    wsmanager.registerOnUpdate((data) => { updateCards( data, gameId, myPlayer.id, setCards, setDrawDeck, setDiscardDeck, setGame, setHasDiscarded, setPlayedCard ); }, "card");
    wsmanager.registerOnUpdate((data) => { updatePlayers(data, gameId, setPlayers, myPlayer.position); }, "player");
    wsmanager.registerOnUpdate((data) => { updateSecrets(data, gameId, setSecrets); }, "secret");
    wsmanager.registerOnAction((data) => {setCancelActionSecondsLeft(data.remaining_seconds);}, "timer", "update_seconds");
    
    wsmanager.registerOnCreate((data) => {
      setChatMessages(prev => {
        return [...prev, data];
      });
      if (!chatOpen) {
        setUnreadCount(c => c + 1);
      }
      if (!data.owner_name) {
        setEventPopup(data);
        setTimeout(() => setEventPopup(null), 5000);
      }
    }, "chat");
    
    wsmanager.registerOnAction((data) => {
      if(data.dest_user == myPlayer.id){
        const secretId = data.secret_id;
        if(secretId){
          setSecretToShow(secretId);
          setShowSecretModalOpen(true);
        }
      }
    }, "devious", "show-secret");

    return () => { wsmanager.close(); };
  }, [gid, myPlayer, chatOpen]);

  useEffect(() => {
    if (!game) return;
    ChatService.search(game.id)
      .then((msgs) => {
        setChatMessages(msgs);
      })
      .catch((err) => console.error("Error cargando mensajes:", err));
  }, [game?.id]); 


  useEffect(() => {
    if (!playedCard || !game || !players) return
    if(playedCard.name == "point-your-suspicions"){
      EventTableService.searchInTable({ game_id__eq: game.id, action__eq: "point_your_suspicions", turn_played__eq: game.current_turn})
        .then((response) => {
          if(response.length < players.length && response.some((event) => event.player_id == myPlayer?.id)){
            setAlreadyVoted(true);
          }
          else if(response.length >= players.length){
            setAlreadyVoted(false);
          }
        })
    }
    else if(playedCard.name == "card-trade"){
      EventTableService.searchInTable({ game_id__eq: game.id, action__eq: "card_trade", turn_played__eq: game.current_turn})
      .then((response) => {
        if(response.length < 3 && response.some((event) => event.player_id == myPlayer?.id) && response.length != 1){
          setAlreadyVoted(true);
        }
        else if(response.length >= 3){
          setAlreadyVoted(false);
        }
      })
    }
    else if(playedCard.name == "dead-card-folly"){
      EventTableService.searchInTable({ game_id__eq: game.id, action__eq: "dead_card_folly_trade", turn_played__eq: game.current_turn})
      .then((response) => {
        if(response.length < players.length && response.some((event) => event.player_id == myPlayer?.id)){
          setAlreadyVoted(true);
        }
        else if(response.length >= players.length){
          setAlreadyVoted(false);
        }
      })
    }
    if(playedCard.name == "card-trade"){
      EventTableService.searchInTable({ game_id__eq: game.id, action__eq: "card_trade", turn_played__eq: game.current_turn})
        .then((response) => {
          const trader = response.some((e) => !e.target_card && (e.player_id == myPlayer?.id || e.target_player == myPlayer?.id))
          const filterEvents =response.some((e) => e.player_id == myPlayer?.id && e.target_card != null)
          console.log(trader)
          console.log(!filterEvents)
          setSelectedToTrade(!filterEvents && trader)
        })
    }
  },[playedCard, game, players, myPlayer])

  // pongo el hook aca pq sino se rompe todo
  const ashes = useLookIntoTheAshes({ game, myPlayer, discardDeck });
  const delay = useDelay({ game, myPlayer, discardDeck });

  if (!game || !myPlayer) {
    return (
      <div
        className="flex justify-center items-center h-screen text-xl font-bold"
        style={{ backgroundColor: "#470620", color: "white" }}
      >
        Cargando…
      </div>
    );
  }

  const handlePassTurn = () => {
    if (!game || !myPlayer) return;

    GameService.update(game.id, {
      current_turn: game.current_turn + 1,
      token: myPlayer.token,
    });
  };

  function cardSelect(cardId: number) {
    if (!game) return;
    const card = cards.find(c => c.id === cardId);
    const status: GameStatus[] = [GameStatus.TURN_START, GameStatus.FINALIZE_TURN, GameStatus.WAITING_FOR_CHOOSE_SECRET, GameStatus.SELECT_CARD_TO_TRADE]
    if(game.status === "waiting_for_cancel_action" ){ //solo se puede seleccionar not so fast
      if (card.name === "not-so-fast") {
       setSelectedCards((prev) =>
        prev.includes(card.id)
          ? prev.filter((id) => id !== card.id)
          : [...prev, card.id]
      );
    }
     return;
    }
    if(game.status === GameStatus.SELECT_CARD_TO_TRADE ){ //solo se puede seleccionar not so fast
      if ((card.name === "card-trade" || card.name === "dead-card-folly") && playedCard?.id === card?.id) {
      return; 
      }
    }
    if ((!myTurn || !status.includes(game.status) || game.status == "waiting_for_choose_secret" ) && game.status != GameStatus.SELECT_CARD_TO_TRADE) return;
    else{
      if ((socialDisgrace || (game.status == GameStatus.SELECT_CARD_TO_TRADE)) && selectedCards.length >= 1 && !selectedCards.includes(cardId)) return;
    
    setSelectedCards((prev) =>
        prev.includes(cardId)
          ? prev.filter((id) => id !== cardId)
          : [...prev, cardId]
      );
    }
  }

  function cardPicker(cardId: number) {
    if (!myTurn) return;

    const missing = 6 - cards.length;

    setPickedCards((prev) => {
      if (prev.includes(cardId)) {
        return prev.filter((id) => id !== cardId); //deseleccionar
      } else if (prev.length < missing) {
        return [...prev, cardId];
      } else {
        return prev;
      }
    });
  }

  async function handlePick3() {
    const maxPick = 6 - cards.length;
    if (maxPick <= 0) return;
    const pickUp = pickedCards;
    pickUp.map((cid) =>
      CardService.update(cid, {
        owner: myPlayer?.id,
        token: myPlayer?.token,
      })
    );

    setPickedCards([]);
  }

  const handleTargetTheirSecret = ( pid: number, revealed: boolean ) => {
    if((chooseTheirSecret && !revealed) || (chooseRevealedSecret && revealed)){
      if(targetSecret == pid){
        setTargetSecret(null);
      }
      else{
        setTargetSecret(pid);
      }
    }
  }

  const handleTargetOwnSecret = ( pid: number, revealed: boolean ) => {
    if((chooseOwnSecret && !revealed) || (chooseRevealedSecret && revealed)){
      if(targetSecret == pid){
        setTargetSecret(null);
      }
      else{
        setTargetSecret(pid);
      }
    }
  }

  const handleTargetPlayer = (pid: number) => {
    if(choosePlayer){
      if(targetPlayer == pid){
        setTargetPlayer(null);
      }
      else{
        setTargetPlayer(pid);
      }
    }
  }

  
  const handlePlayAction = () => {
    if(game.status == GameStatus.WAITING_FOR_CHOOSE_PLAYER && 
      (game.player_in_action == myPlayer.id || game.player_in_action == null)){
        if(playedCard && playedCard.turn_played == game.current_turn && playedCard.name != "another-victim"){
          if(["point-your-suspicions"].includes(playedCard.name)){
            setAlreadyVoted(true);
          }
          CardService.playCardWithTargets(playedCard.id,myPlayer.token, {target_players: [targetPlayer]})
            .catch((error) => console.error(error))
      }
      else{
        SetService.search({turn_played__eq: game.current_turn, game_id__eq: game.id})
          .then((set:DetectiveSet[]) => {
            if(set.length == 0) return;
            SetService.set_action(set[0].id, {target_player: targetPlayer, token: myPlayer.token})
          })
          .catch((error) => console.error(error))
      }
      setChoosePlayer(false);
      setTargetPlayer(null);
      setTargetName("");
    }
    else if(game.status == GameStatus.WAITING_FOR_CHOOSE_SECRET && game.player_in_action == myPlayer.id){
      if(playedCard && playedCard.turn_played == game.current_turn && playedCard.name != "another-victim" && playedCard.name != "ariadne-oliver"){
        CardService.playCardWithTargets(playedCard.id,myPlayer.token, {target_secrets: [targetSecret]})
          .catch((error) => console.error(error))
      }
      else{
        SetService.search({turn_played__eq: game.current_turn, game_id__eq: game.id})
          .then((set:DetectiveSet[]) => {
            if(set.length == 0) return;
            SetService.set_action(set[0].id, {target_secret: targetSecret, token: myPlayer.token})
          })
          .catch((error) => console.error(error))
        }
        setChooseTheirSecret(false);
        setChooseOwnSecret(false);
        setChooseRevealedSecret(false);
        setTargetSecret(null);
        setTargetName("");
    }
    else if(game.status == GameStatus.WAITING_FOR_CHOOSE_PLAYER_AND_SECRET && game.player_in_action == myPlayer.id){
      const card_played = cards.find((card:Card) => card.turn_played == game.current_turn);
      if (!card_played) return;
      CardService.playCardWithTargets(card_played.id, myPlayer.token, {target_players: [targetPlayer], target_secrets: [targetSecret]})
        .catch( (error) => { console.error(error) })
      setTargetPlayer(null);
      setTargetSecret(null);
      setChooseOwnPLayer(false);
      setChoosePlayer(false);
      setChooseRevealedSecret(false);
      setTargetName("");
    }
    else if(game.status == GameStatus.WAITING_FOR_CHOOSE_SET && game.player_in_action == myPlayer.id){
      const card_played = cards.find((card:Card) => card.turn_played == game.current_turn);
      console.log(card_played)
      console.log(targetSet)
      if (!card_played) return;
      CardService.playCardWithTargets(card_played.id, myPlayer.token, {target_sets: [targetSet]})
        .catch( (error) => { console.error(error) })
      setTargetSet(null);
      setChooseSet(false);
      setTargetName("");
    }
    else if(game.status == GameStatus.SELECT_CARD_TO_TRADE){
      if(playedCard && playedCard.turn_played == game.current_turn) {
        if (["card-trade", "dead-card-folly"].includes(playedCard.name)) {
          setAlreadyVoted(true);
          setSelectedToTrade(false);
        }
        CardService.playCardWithTargets(playedCard.id, myPlayer.token, {target_cards: [selectedCards[0]]})
        .catch((error) => console.error(error))
      }
      setTargetName("");
      setSelectedCards([]);
    }
  }

  const positions = usePositions(players.length);

  const murdererSecret = secrets.find((s) => s.type === "murderer");
  const accompliceSecret = secrets.find((s) => s.type === "accomplice");
  const murdererId = murdererSecret?.owner;
  const accompliceId = accompliceSecret?.owner;
  const murdererPlayer = murdererSecret
    ? players.find((p) => p.id === murdererSecret.owner)
    : null;
  
  const showWin = game.status === GameStatus.FINALIZED;

  const regularDeckEmpty = drawDeck.length === 3; //mazo agotado
  const others = players.filter(p => p.id !== murdererId && p.id !== accompliceId); //todos los demás en desgracia social
  const allOthersInDisgrace = others.every(p => p.social_disgrace);
  const murdererEscaped = regularDeckEmpty || allOthersInDisgrace; //asesino escapa si mazo agotado O todos los demás en desgracia

  return (
    <>
      {showWin && ( // lo pongo arriba asi tapa todo
        <WinDialog
          open={true}
          murdererEscaped={murdererEscaped}
          murdererName={murdererPlayer?.name ?? ""}
          murdererAvatar={murdererPlayer?.avatar ?? ""}
        />
      )}
      <div
        className="relative w-full h-screen"
        style={{ backgroundColor: "#470620" }}
      >
        <div className="absolute top-4 left-4 text-center text-white font-bold z-10">
          <div className="text-2xl text-left">
            {game.name} #{game.id}
          </div>
          <div className="text-xl text-left text-gray-300">
            Turno de{" "}
            {players.find(
              (p) => p.position === game.current_turn % players.length
            )?.name || "N/A"}
          </div>
        </div>
        {players.map((p, idx) => {
          const pos = positions[idx];
          const isTurn = p.position === game.current_turn % players.length;
          const isPlayerInDisgrace = p.social_disgrace;
          return (
            <div
              key={p.id}
              className={`${positionStyles[pos]} flex flex-row items-center gap-4`}
            >
              {idx != 0 &&
                (pos === "right" ||
                  pos === "right-bottom" ||
                  pos === "right-top") && (
                  <div className="flex gap-2">
                    {secrets.map((secret) => {
                      if (p.id === secret.owner){
                        return (

                          <div  key={secret.id} onClick={() => handleTargetTheirSecret(secret.id, secret.revealed)}
                            className ={secret.revealed ? "flip-secret" : ""}>
                            <Secret secret={secret} chooseSecret={chooseTheirSecret} chooseRevealed={chooseRevealedSecret} isSelected={targetSecret == secret.id}/>
                          </div>
                        );
                      }
                    })}
                  </div>
                )}

              <div className="flex flex-col items-center w-32 md:w-36 shrink-0">
              <div className={`rounded-full border-4 object-cover w-20 h-20
                ${choosePlayer && (p.id != myPlayer.id || game.status === GameStatus.WAITING_FOR_CHOOSE_PLAYER_AND_SECRET) && (game.player_in_action == myPlayer.id || game.player_in_action == null) ? "hover:shadow-xl shadow-red-400 cursor-pointer" : ""}
                ${targetPlayer == p.id ? "shadow-xl shadow-red-400" : ""}
                ${isTurn ? "border-blue-800" : "border-gray-300"}`}>
                <img
                  src={p.avatar}
                  alt="avatar"
                  onClick={() => {if(p.id != myPlayer.id || game.status === GameStatus.WAITING_FOR_CHOOSE_PLAYER_AND_SECRET ) {handleTargetPlayer(p.id)}}}
                  className={`rounded-full object-cover w-full h-full ${isPlayerInDisgrace ? 'grayscale' : ""}`}
                />
              </div>
                <p className="mt-2 text-white font-semibold">{p.name}</p>
                {p.id === myPlayer.id && socialDisgrace && (
                  <p className="mt-1 text-sm text-white font-bold bg-black bg-opacity-75 p-2 rounded">
                    Estás en desgracia social, seleccioná solo una carta para descartar.
                  </p>
                )}
                {secrets.find(
                  (s) => s.owner === p.id && s.type === "murderer"
                ) &&
                  secrets.find(
                    (s) =>
                      s.owner === myPlayer.id &&
                      ["murderer", "accomplice"].includes(s.type)
                  ) && <p className="text-sm text-red-400">Asesino</p>}
                
                 {p.id === myPlayer.id ? (
                    <div className="mt-1">
                      <MyPlayerSets playerId={myPlayer.id} game={game} />
                    </div>
                 ) : (
                    <div className="mt-1">
                      <OpponentPlayerSets playerId={p.id} game={game} canSelect={chooseSet} setTargetSet={setTargetSet} targetSet={targetSet} />
                    </div>
                 )}
                
                {secrets.find(
                  (s) => s.owner === p.id && s.type === "accomplice"
                ) &&
                  secrets.find((s) =>
                      s.owner === myPlayer.id && ["murderer", "accomplice"].includes(s.type)) && <p className="text-sm text-red-400">Cómplice</p>}
              </div>
              {idx != 0 &&
                pos != "right" &&
                pos != "right-bottom" &&
                pos != "right-top" && (
                  <div className="flex gap-2">
                    {secrets.map((secret) => {
                      if (p.id === secret.owner){
                        return (
                          <div key={secret.id} onClick={() => handleTargetTheirSecret(secret.id, secret.revealed)}
                            className ={secret.revealed ? "flip-secret" : ""}>
                            <Secret secret={secret} chooseSecret={chooseTheirSecret} chooseRevealed={chooseRevealedSecret} isSelected={targetSecret == secret.id}/>
                          </div>
                        );
                      }
                    })}
                  </div>
                )}
            </div>
          );
        })}
        <div className="flex  gap-2 absolute bottom-10 left-2/100 transform">
          {secrets.map((secret: Secret) => {
            if (secret.owner === myPlayer!.id){
              return (
                <div key={secret.id} onClick={() => handleTargetOwnSecret(secret.id, secret.revealed)}
                className = {secret.revealed ? "flip-secret" : ""} >
                  <Secret secret={secret} mine={true} chooseSecret={chooseOwnSecret} chooseRevealed={chooseRevealedSecret} isSelected={targetSecret == secret.id} />
                </div>
              );
            }
          })}
        </div>
        <div className="w-full h-[90%] gap-2 flex justify-center items-end z-20">
          {/* {socialDisgrace && (
            <div className="absolute top-2/3 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-white font-bold bg-black bg-opacity-75 p-2 rounded z-50">
              Estás en desgracia social, seleccioná solo una carta para descartar.
            </div>
          )} */}
          {cards.map((c) => { 
            const canReact = game.status === GameStatus.WAITING_FOR_CANCEL_ACTION && c.name === "not-so-fast";
            return (
              !c.set_id && ( 
                <div
                  key={c.id}
                  data-testid="hand-card"
                  onClick={() => cardSelect(c.id)}
                  className={`cursor-pointer z-40 transition-transform duration-200
                    ${
                      selectedCards.includes(c.id)
                        ? "scale-110 -translate-y-4 border-4 border-red-900 rounded-2xl"
                        : ""
                    }
                    ${canReact ? "animate-pulse border-4 border-red-900 rounded-2xl shadow-lg" : ""}
                  `}
                >
                 <Card source={c.name} />
                </div>
            )
          );
})}

          <div className="absolute top-30/100 left-1/2 transform -translate-x-1/2 -translate-y-1/2 flex z-10">
            <div className="w-38 h-50 flex items-center justify-center">
              {drawDeck.length > 0 ? (
                <img src={dorso} alt="Dorso" className="rounded-xl md:w-15 lg:w-30" />
              ) : (
                <img src={lost} alt="Lost" className="rounded-xl md:w-15 lg:w-30" />
              )}
            </div>
            <div className="w-38 h-50 flex items-center justify-center">
              {discardDeck.length > 0 ? (
                <DiscardedCard
                  key={discardDeck[0].id}
                  source={
                    [...discardDeck].sort(
                      (c1, c2) => c2.discarded_order - c1.discarded_order
                    )[0].name
                  }
                />
              ) : null}
            </div>
          </div>
          
          {ACTION_STATES.includes(game.status) &&
            <div className={`absolute ${((game.player_in_action == myPlayer.id || game.player_in_action == null) && game.status != GameStatus.WAITING_FOR_CANCEL_ACTION && !alreadyVoted) || selectedToTrade 
                                                            ? "top-42/100" : "top-60/100"} left-1/2 transform -translate-x-1/2 -translate-y-1/2 flex z-30 w-3/4 h-8/100 justify-center`}>
              <Action
                action={handlePlayAction}
                target={((game.player_in_action == myPlayer.id || game.player_in_action == null) && !alreadyVoted && game.status != GameStatus.WAITING_FOR_CANCEL_ACTION) || selectedToTrade ?
                         targetName : (alreadyVoted ? "demas jugadores" : players.find((p) => p.id === game.player_in_action)?.name ?? "")}
                isPlayerInAction={ ((game.player_in_action == myPlayer.id || game.player_in_action == null) && game.status != GameStatus.WAITING_FOR_CANCEL_ACTION && !alreadyVoted) || selectedToTrade}
                isEnabled = {game.status == GameStatus.WAITING_FOR_CHOOSE_PLAYER_AND_SECRET ? 
                              targetPlayer != null && targetSecret != null : 
                              targetPlayer != null || targetSecret != null || targetSet != null
                              || selectedCards.length == 1}
                gameStat= {game.status}
                remainingSeconds={cancelActionSecondsLeft}
               />
            </div>
          }
          <div className="absolute bottom-full top-145 left-1/2 -translate-x-1/2 flex gap-4 z-10 items-end">
            {tableCards.map((cards) => (
              <div
                key={cards.id}
                data-testid="table-card"
                onClick={() => cardPicker(cards.id)}
                className={`cursor-pointer
                ${
                  pickedCards.includes(cards.id)
                    ? "scale-110 border-5 border-red-900 rounded-2xl"
                    : ""
                }
                ${justAddedTable.has(cards.id) ? "slide-in-top" : ""}`}
              >
                <TableCard source={cards.name} />
              </div>
            ))}
          </div>
          {(pickedCards.length != 0) &&
          (
          <div className="absolute bottom-full top-130 translate-x-80 slide-in-left">
            <button
              onClick={handlePick3}
              className={redButtonStyle}
            >
              Juntar carta
            </button>
          </div>)
          }
        </div>

        <div className="fixed bottom-10 right-10 z-50 flex items-center gap-3">
          <button
            onClick={() => {
              setChatOpen((o) => !o);
              if (unreadCount > 0) setUnreadCount(0);
            }}
            className={`px-4 py-2 ${darkButtonStyle} bg-[#230812] border-1 border-[#bb8512]`}> Chat
            {unreadCount > 0 && (
            <span className="inline-block ml-2 w-3 h-3 bg-[#bb8512] rounded-full animate-pulse" />
            )}
          </button>

          {myTurn && (
            <button
              onClick={handlePassTurn}
              disabled={![GameStatus.FINALIZE_TURN, GameStatus.FINALIZE_TURN_DRAFT].includes(game.status)}
              className={`py-2 px-4 font-bold rounded 
                ${
                  ([GameStatus.FINALIZE_TURN, GameStatus.FINALIZE_TURN_DRAFT].includes(game.status))
                  ? `${redButtonStyle}`
                  : "bg-gray-500 text-gray-200 cursor-not-allowed"
                }`}
            >
            Pasar turno
            </button>
          )}
        </div>

        <LookIntoTheAshesModal
          open={ashes.open}
          cards={ashes.cards}
          onConfirm={(id) => ashes.confirm(id)}
        />

        <DelayModal
          open={delay.open}
          cards={delay.cards}
          onConfirm={(order) => delay.confirm(order)}
        />

        {playedCard && myPlayer && <FollyModal
          open={game.status == GameStatus.WAITING_TO_CHOOSE_DIRECTION && game.player_in_action == myPlayer.id}
          //cards={iscardedCards}
          onConfirm={direction => {
            CardService.playCardWithTargets(playedCard.id,myPlayer?.token,{player_order:direction})
            console.log("Dirección:", direction); // "left" o "right"
          }}
        />}
        <SelectedCardsActionBar selectedCards={selectedCards} cards={cards} myPlayer={myPlayer} game={game} setCards={setCards} setSelectedCards={setSelectedCards} setHasDiscarded={setHasDiscarded} isInSocialDisgrace={socialDisgrace} />
        <ShowPrivateSecretModal open={true} secret={secretToShow} secrets={secrets} onClose={() => { setShowSecretModalOpen(false); setSecretToShow(null); }} />
      </div>
      
      {chatOpen && (
        <GameChat
          messages={chatMessages}
          onClose={() => setChatOpen(false)}
          myPlayerId={myPlayer.id}
          gameId={game.id}
        />
      )}
      
      {eventPopup && (
        <div className="absolute top-16 left-4 text-[#bb8512] text-xl font-semibold py-2 z-40 animate-fade-in slide-in-bottom">
          <p>{eventPopup.content}</p>
        </div>
      )}

    </>
  );
}

export { handleUpdateCards, updateCards, updatePlayers, updateSecrets, updateGame };
