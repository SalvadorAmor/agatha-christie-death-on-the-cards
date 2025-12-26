import React, { useEffect, useState } from "react";
import { redButtonStyle } from "./Button";

type DiscardedCard = { id: number; name: string };

type Props = {
  open: boolean;
  //cards: DiscardedCard[];
  onConfirm: (direction: string) => void;
};

export default function FollyModal({ open, onConfirm }: Props) {
  const [direction, setDirection] = useState<string>("");

  useEffect(() => {
    if (open) setDirection("");
  }, [open]);

   const confirm = () => {
    if (direction != "") {
      const side = direction == "left" ? "counter-clockwise" : "clockwise"
      onConfirm(side);
      console.log("[Modal] direction =", direction);
    }
  };
  if (!open) return null;


  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm fade">
      <div className="rounded-3xl bg-[#230812] p-6 w-fit fade-pop">
        <h1 className="text-center text-2xl font-extrabold text-white mb-9">
          Elegí la dirección en la que querés enviar las cartas
        </h1>
        <div className="flex justify-center gap-12 my-8">
          <button
            onClick={() => setDirection("left")}
            className="relative"
          >
            <img
              src="/images/Arrow/flecharoja.png"
              alt="izquierda"
              className={`h-auto w-[200px] rounded-xl scale-x-[-1] transition-all ${
                direction === "left"
                  ?"drop-shadow-[0_0_15px_rgba(187,133,18,1)] drop-shadow-[0_0_25px_rgba(187,133,18,0.8)] scale-110"
                  : "opacity-60 hover:opacity-100 hover:drop-shadow-[0_15px_30px_rgba(255,0,0,1)]"
              }`}
             
            />
            {direction === "left"}
            <p className="text-white text-center mt-3 font-semibold">Izquierda</p>
          </button>

          <button
            onClick={() => setDirection("right")}
            className="relative"
          >
            <img
              src="/images/Arrow/flecharoja.png"
              alt="derecha"
              className={`h-auto w-[200px] rounded-xl transition-all ${
                direction === "right"
                  ? "drop-shadow-[0_0_15px_rgba(187,133,18,1)] drop-shadow-[0_0_25px_rgba(187,133,18,0.8)] scale-110"
                  : "opacity-60 hover:opacity-100 hover:drop-shadow-[0_15px_30px_rgba(255,0,0,1)]"
              }`}
            />
            {direction === "right"}
            <p className="text-white text-center mt-3 font-semibold">Derecha</p>
          </button>
        </div>

        <div className="mt-5 flex justify-center">
          <button
            onClick={confirm}
            disabled={direction === ""}
            className={`rounded-xl px-5 py-2 text-white ${
              direction === ""
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