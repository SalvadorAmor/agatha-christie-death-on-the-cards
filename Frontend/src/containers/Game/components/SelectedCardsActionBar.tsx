import CardService from "../../../services/CardService.ts";
import SetService from "../../../services/SetService.ts";
import {useEffect, useState} from "react";
import type {Card, DetectiveSet, Player, Game} from "../Game.tsx"
import EventTableService from "../../../services/EventTableService.ts";
import { redButtonStyle } from "../../../components/Button.jsx";


type SelectedCardsActionBarProps = {
  selectedCards: number[],
  cards: Card[],
  myPlayer: Player | null,
  game: Game | null,
  setCards: (cards: Card[]) => void,
  setSelectedCards: (selectedCards: number[]) => void,
  setHasDiscarded: (hasDiscarded: boolean) => void,
  isInSocialDisgrace: boolean,
}


type ModalProps = {
  message: string;
  isSuccess: boolean;
  onClose: () => void;
  onConfirm?: () => void;
};

export const Modal: React.FC<ModalProps> = ({ message, isSuccess, onClose }) => {
  const isError = !isSuccess;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm">
      <div className="w-[520px] rounded-4xl bg-[#230812] p-8 shadow-[0_20px_60px_rgba(0,0,0,0.8)] max-w-sm mx-4 text-center">

        <div className="flex items-center justify-center mb-6">
          <h2 className={`text-2xl font-extrabold ${isError ? 'text-red-600' : 'text-green-500'}`}>
            {isError ? 'Set Inválido' : 'Set Válido'}
          </h2>
        </div>

        <p className="text-white mb-8 px-4" dangerouslySetInnerHTML={{ __html: message }}></p>

        <button
          onClick={onClose}
          className="rounded-xl bg-[#8D0000] text-white font-semibold px-6 py-2.5 cursor-pointer hover:bg-[#ca5a5a] w-full"
        >
          Entendido
        </button>
      </div>
    </div>
  );
};


type JugarSetState = {
  isOpen: boolean;
  isSuccess: boolean;
  message: string;
  onConfirm?: () => void;
}

const detectiveRules: Record<string, number> = {
  "hercule-poirot": 3,
  "miss-marple": 3,
  "parker-pyne": 2,
  "mr-satterthwaite": 2,
  "lady-eileen-bundle-brent": 2,
  "tommy-beresford": 2,
  "tuppence-beresford": 2
};

const isAriadne = (c?: Card) => c?.name === "ariadne-oliver";

function isCompatibleAdd (card: Card, set: DetectiveSet, myPlayerId: number): boolean {
    if (set.owner !== myPlayerId) return false;
    if (card.name === "harley-quin-wildcard" || isAriadne(card)) return false;

    const beresford = ["tommy-beresford", "tuppence-beresford"];

    const firstDetective = set.detectives.find((d) => (d.name !== "harley-quin-wildcard" && d.name !== "ariadne-oliver"));
    const sameDetective = card.name === firstDetective.name ||
        (beresford.includes(card.name) && beresford.includes(firstDetective.name));

    return sameDetective;
}

function isValidDetectiveSet(selectedCards: Card[]): boolean {
  if (selectedCards.length < 2) return false;
  if (selectedCards.some(isAriadne)) return false;

  const names = selectedCards.map((c) => c.name);
  console.log("Cartas seleccionadas:", names);
  const nonWildcards = names.filter((n) => n !== "harley-quin-wildcard");

  if (nonWildcards.length === 0) return false;

  const mainDetective = nonWildcards[0];
  const required = detectiveRules[mainDetective];

  if (required !== names.length) return false;

  // Caso de los hermanos beresford
  const hasTommy = names.includes("tommy-beresford");
  const hasTuppence = names.includes("tuppence-beresford");

  if (hasTommy && hasTuppence && (names.length === 2)) return true;

  const valid = names.every(
    (n) => n === mainDetective || n === "harley-quin-wildcard"
  );

  const enough = names.length == required;

  return (valid && enough);
}

const SelectedCardsActionBar = ({selectedCards, cards, myPlayer, game, setCards, setSelectedCards, setHasDiscarded, isInSocialDisgrace}: SelectedCardsActionBarProps) => {
  const [JugarSetState, setJugarSetState] = useState<JugarSetState>({
    isOpen: false,
    isSuccess: false,
    message: "",
  });
  const [ownSets, setOwnSets] = useState<DetectiveSet[]>([]);
  const [otherSets, setOtherSets] = useState<DetectiveSet[]>([]);

  useEffect(() => {
    if (!myPlayer || !game) return;
    SetService.search({ owner__eq: myPlayer.id }).then((sets) => {
      setOwnSets(Array.isArray(sets) ? sets : []);
    });
    SetService.search({ game_id__eq: game.id }).then((all) => {
    const allArr = Array.isArray(all) ? all : [];
    setOtherSets(allArr.filter((s) => s.owner !== myPlayer.id));
    });
  }, [myPlayer, game]);


  async function handlePlayEvent() {
    if (!myPlayer || !game || selectedCards.length !== 1) return;
    const selectedCardId = selectedCards[0];
    setSelectedCards([]);
    CardService.playEvent(selectedCardId, myPlayer.token)
   }

  async function handleDiscard() {
    if (!myPlayer || !game) return;
    if (isInSocialDisgrace && selectedCards.length !== 1) return;
    try {
      await CardService.bulkUpdate(selectedCards, { turn_discarded: game.current_turn, token: myPlayer.token });
      setSelectedCards([]);
      setHasDiscarded(true);
    } catch (error) { console.error("Error al descartar cartas:", error);}
  }

  async function handleCheckSet() {
    const selected = cards.filter((c) => selectedCards.includes(c.id));
    const valid = isValidDetectiveSet(selected);

    if (!valid) {
      setJugarSetState({
        isOpen: true,
        isSuccess: false,
        message: "Las cartas seleccionadas no forman un set de detective valido."
      });
    } else {
      if (!myPlayer || !game) {return;}
      const dto = { detectives: selected.map((c) => c.id) };
      const result = await SetService.create(dto);
      if (result) {
        setCards(prev => prev.filter(c => !selectedCards.includes(c.id)));
      }
      setSelectedCards([]);
    }
  }

  async function handleAddToSet(){
    if (!myPlayer || selectedCards.length !== 1) return;
    const card = cards.find((c) => c.id === selectedCards[0]);
    if (!card) return;

    const anySet = ownSets
      .filter((s) => isCompatibleAdd(card, s, myPlayer.id))
      .sort((a, b) => a.id - b.id)[0];
      
    if (!anySet) return;

    const ok = await SetService.update(anySet.id, {add_card: card.id, token: myPlayer.token});
    if (ok) {
      setCards(cards.filter((c) => c.id !== card.id));
      setSelectedCards([]);
    }
  }

  const oneCardSelected = selectedCards.length === 1 ? cards.find(i => i.id === selectedCards[0]) : undefined;

  
  async function handleCancelAction () {
    if(!game) return;
    const eventToCancel = await EventTableService.searchInTable({game_id__eq: game.id, turn_played__eq: game.current_turn, action__eq: "to_cancel", completed_action__eq: false});
    const not_so_fast = selectedCards[0];
    const token = myPlayer?.token;
    if (!eventToCancel || eventToCancel.length === 0) {
      console.warn("no hay nada para cancelar");
      setSelectedCards([]);
      return;
    }
    const cancelled = await EventTableService.cancelAction(eventToCancel[0].id, not_so_fast, token)
    console.log(eventToCancel);
    setSelectedCards([]);
  }


  const buttonClassname = "rounded-xl bg-red-900 text-white font-semibold px-6 py-2.5 cursor-pointer hover:bg-[#ca5a5a]";
  const disgraceButtonClassname = (isDisabled: boolean) => `rounded-xl font-semibold px-6 py-2.5 transition ${ isDisabled ? "bg-gray-500 text-gray-300 cursor-not-allowed" : `${redButtonStyle}` }`;
  const canPlayAriadne = isAriadne(oneCardSelected) && myPlayer;
  const hasAriadne = selectedCards.some(c => cards.find(i => i.id === c)?.name === "ariadne-oliver");
  const turn_end = game?.status === "finalize_turn" || game?.status === "finalize_turn_draft";
  
  return (
  selectedCards.length > 0 && game?.status != "select_card_to_trade" &&(
    <div className="flex justify-center gap-10">
      {(() => {
        const selected = cards.filter(c => selectedCards.includes(c.id));
        const isNotSoFast = selected.length === 1 && selected[0].name === "not-so-fast";
        if (!game) return;
        if ( isNotSoFast && game.status === "waiting_for_cancel_action") {
          return (
            <button
              onClick={handleCancelAction} //implementar handlecancelaction
              className={`${redButtonStyle} slide-in-bottom`}
            >
              Cancelar acción
            </button>
          );
        }

        return (
          <button onClick={handleDiscard} disabled={isInSocialDisgrace && selectedCards.length !== 1} className={`${redButtonStyle} slide-in-bottom mt-5`}>
            Descartar cartas
          </button>
        );
      })()}

       { !hasAriadne && selectedCards.every(c => cards.find(i => i.id === c)?.card_type	=== 'detective') && !turn_end && (
        <button onClick={handleCheckSet} disabled={isInSocialDisgrace} className={`${disgraceButtonClassname(isInSocialDisgrace)} slide-in-bottom mt-5`}>Jugar set</button>
      )}

      { selectedCards.every(c => cards.find(i => i.id === c)?.card_type	=== 'event') && selectedCards.length === 1 && !turn_end && (
        <button onClick={handlePlayEvent} disabled={isInSocialDisgrace} className={`${disgraceButtonClassname(isInSocialDisgrace)} slide-in-bottom mt-5`}>Jugar evento</button>
      )}

      { oneCardSelected && !isAriadne(oneCardSelected) && myPlayer && ownSets.some(s => isCompatibleAdd(oneCardSelected, s, myPlayer.id)) && !turn_end && (
        <button onClick={handleAddToSet} disabled={isInSocialDisgrace} className={`${disgraceButtonClassname(isInSocialDisgrace)} slide-in-bottom mt-5`}> Agregar al set </button>
      )}

      {canPlayAriadne && !turn_end && (
        <button onClick={handlePlayEvent} className={`${disgraceButtonClassname(isInSocialDisgrace)} slide-in-bottom mt-5`} disabled={isInSocialDisgrace}>Jugar carta</button>
      )}

      {JugarSetState.isOpen && (
        <Modal
          message={JugarSetState.message}
          isSuccess={JugarSetState.isSuccess}
          onClose={() => setJugarSetState({ isOpen: false, isSuccess: false, message: "" })}
          onConfirm={JugarSetState.onConfirm}
        />
      )}

    </div>
  )
);
}
export default SelectedCardsActionBar;