import { useEffect, useState } from "react";
import SetService from "../services/SetService";
import type { Game } from "../containers/Game/Game"
import useJustAdded from "../Hooks/useJustAdded";

type DetectiveCard = { id: number; name: string };
type DetectiveSet = { id: number; detectives: DetectiveCard[] };

type Props = {
  playerId: number;
  game: Game;
};

export default function MySetsBubbles({ playerId, game }: Props) {
  const [sets, setSets] = useState<DetectiveSet[]>([]);
  const justAddedSets = useJustAdded(sets);

async function fetchSets() {
    const data = await SetService.search({ owner__eq: playerId });
    setSets(Array.isArray(data) ? data : []);
}

  useEffect(() =>{fetchSets();},[game.status]);

  if (!sets.length) return null;

return (
  <div className="inline-grid grid-cols-3 gap-3 items-center justify-items-center overflow-visible">
    {sets.map((set) => {
      const first =
        set.detectives.find((c) => c.name !== "harley-quin-wildcard");
      const isNew = justAddedSets.has(set.id);

      return (
        <div key={set.id} className={`relative group overflow-visible ${isNew ? "slide-in-bottom" : ""}`}
        >
          <button
            disabled
            className="w-10 h-10 rounded-full overflow-hidden flex items-center justify-center bg-white ring-2 ring-[#bb8512]"
          >
            <img
              src={`/images/cards/${first.name}.png`}
              alt={first.name}
              className="object-contain"
            />
          </button>

          <div
            className="absolute left-1/2 -translate-x-1/2 -top-[120px] hidden group-hover:flex z-[999] pointer-events-none overflow-visible">
            <div
              className="flex flex-nowrap items-center gap-2 w-max px-2 py-2 rounded-2xl bg-black/70 backdrop-blur-sm shadow-2xl">
              {set.detectives.map((d) => (
                <img
                  key={d.id}
                  src={`/images/cards/${d.name}.png`}
                  alt={d.name}
                  className="h-[100px] w-auto rounded-xl border border-[#bb8512] object-contain"
                />
              ))}
            </div>
          </div>
        </div>
      );
    })}
  </div>
);
}