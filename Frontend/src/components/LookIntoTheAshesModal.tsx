import React, { useEffect, useState } from "react";
import { redButtonStyle } from "./Button";

type DiscardedCard = { id: number; name: string };
type Props = {
  open: boolean;
  cards: DiscardedCard[];
  onConfirm: (chosenCardId: number) => void;
};

export default function LookIntoTheAshesModal({ open, cards, onConfirm }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  useEffect(() => {
    if (open) setSelectedId(null);
  }, [open]);

  if (!open) return null;

  const confirm = () => {
    if (selectedId != null) onConfirm(selectedId);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 backdrop-blur-sm bg-black/40 z-0 fade" />
      <div
        className="relative rounded-3xl bg-[#230812] p-6 w-fit z-10 fade-pop"
        role="dialog"
        aria-modal="true"
        aria-label="Elegí la carta que quieras incorporar a tu mano"
      >
        <h1 className="text-center text-2xl font-extrabold text-white mb-9">
          Elegí la carta que quieras incorporar a tu mano
        </h1>

        <div className="flex mt-5 items-end justify-center gap-6">
          {cards.map((c) => {
            const selected = selectedId === c.id;
            return (
              <button key={c.id} onClick={() => setSelectedId(c.id)}>
                <img
                  src={`/images/cards/${c.name}.png`}
                  alt={c.name}
                  className={`h-auto w-[200px] rounded-xl ${selected ? " border-4 border-[#bb8512] rounded-2xl scale-[1.1]" : ""}`}
                />
              </button>
            );
          })}
        </div>

        <div className="mt-5 flex justify-center">
          <button
            onClick={confirm}
            disabled={selectedId == null}
            className={`rounded-xl px-5 py-2 text-white ${
              selectedId == null ? "bg-gray-500 cursor-not-allowed" : `${redButtonStyle}`
            }`}
          >
            Confirmar
          </button>
        </div>
      </div>
    </div>
  );
}