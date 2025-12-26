import React, { useEffect, useState } from "react";
import { redButtonStyle } from "./Button";

type DiscardedCard = { id: number; name: string };

type Props = {
  open: boolean;
  cards: DiscardedCard[];
  onConfirm: (chosenOrder: number[]) => void;
};

export default function DelayModal({ open, cards, onConfirm }: Props) {
  const [selectedOrder, setSelectedOrder] = useState<number[]>([]);

  useEffect(() => {
    if (open) setSelectedOrder([]);
  }, [open]);

  const selectedCards = (id: number) => {
    if (selectedOrder.includes(id)) {
      setSelectedOrder(selectedOrder.filter((c) => c !== id));
    } else {
      setSelectedOrder([...selectedOrder, id]);
    }
  };
  if (!open) return null;

  const confirm = () => {
    if (selectedOrder.length > 0) onConfirm(selectedOrder);
    console.log("[Modal] selectedId =", selectedOrder);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className={`absolute inset-0 backdrop-blur-sm bg-black/40 fade`} />
      <div className={`relative rounded-3xl bg-[#230812] p-6 w-fit fade-pop`}>
        <h1 className="text-center text-2xl font-extrabold text-white mb-9">
          Elegí las cartas a devolver en el orden que quieras que vuelvan al mazo
        </h1>

        <div className="flex mt-5 items-end justify-center gap-6">
          {cards.map((c) => {
            const index = selectedOrder.indexOf(c.id);
            const selected = index !== -1;
            return (
              <button
                key={c.id}
                onClick={() => selectedCards(c.id)}
                className="relative"
              >
                <img
                  src={`/images/cards/${c.name}.png`}
                  alt={c.name}
                  className={`h-auto w-[200px] rounded-xl transition-transform duration-200
                    ${selected ? "border-4 border-[#bb8512] rounded-2xl scale-[1.1]" : "hover:scale-105"}
                  `}
                />
                {selected && (
                  <span className="absolute top-2 left-2 bg-[#bb8512] text-white text-lg font-bold rounded-full px-3 py-1">
                    {index + 1}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        <div className="mt-5 flex justify-center">
          <button
            onClick={confirm}
            disabled={selectedOrder.length < cards.length}
            className={`rounded-xl px-5 py-2 text-white ${
              selectedOrder.length != cards.length
                ? "bg-gray-500 cursor-not-allowed"
                : `${redButtonStyle}`
            }`}
          >
            Confirmar
          </button>
        </div>
      </div>
    </div>
  );
}
