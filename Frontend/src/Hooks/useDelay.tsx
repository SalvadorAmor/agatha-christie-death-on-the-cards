import { useEffect, useState } from "react";
import CardService from "../services/CardService";

type Game = {
  id: number;
  status: string;
  player_in_action: number;
  current_turn: number;
};

type Player = {
    id: number;
    token: string
};

type Card = {
    id: number;
    name: string;
    discarded_order?: number
};

type Params = {
  game: Game | null;
  myPlayer: Player | null;
  discardDeck: Card[];
};

export default function useDelay({ game, myPlayer, discardDeck }: Params) {
  const [open, setOpen] = useState(false);
  const [cards, setCards] = useState<Card[]>([]);
  

  // solo si me toca
  const enable = !!game && !!myPlayer && game.status === "waiting_for_order_discard" && game.player_in_action === myPlayer.id;

  useEffect(() => {
  console.log("[useDelay] enable =", enable);
  console.log("[useDelay] discardDeck =", discardDeck.map(c => c.name));

    if (!enable) return;

    // las cinco cartas
    const top5 = (discardDeck ?? []).slice(-5);
    setCards(top5);
    setOpen(true);
  }, [enable, discardDeck]);

  const confirm = async (chosenOrder: number[]) => {
  console.log("[useDelay.confirm] called with", chosenOrder);
  console.log("[useDelay.confirm] game.status =", game?.status);

    if (!game || !myPlayer) return;

    const playedThisTurn = await CardService.search({
      game_id__eq: game.id,
      turn_played__eq: game.current_turn,
    });

    // busco la carta que se jugó
    const eventCard = playedThisTurn?.[0];
    if (!eventCard) return;

  // devuelvo la info
  await CardService.playCardWithTargets(eventCard.id , myPlayer.token, {
    target_players: [],
    target_secrets: [],
    target_cards: chosenOrder,
    target_sets: [],
  });
  setOpen(false);
  setCards([]);
  console.log(game.status);
  };

  const close = () => setOpen(false);

  return { open, cards, confirm, close };
}