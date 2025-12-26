import { useState, useEffect } from "react";
import { buttonTransition} from "../../../components/Button";
type Prop = {
  target: string;
  action: () => void;
  isPlayerInAction: boolean;
  isEnabled: boolean;
  gameStat: string;
  remainingSeconds?: number | null;
};

export const Action = ({
  target,
  action,
  isPlayerInAction,
  isEnabled,
  gameStat,
  remainingSeconds,
}: Prop) => {
  const [animate, setAnimate] = useState(true);

  useEffect(() => {
    setAnimate(false);
    const id = requestAnimationFrame(() => setAnimate(true));
    return () => cancelAnimationFrame(id);
  }, [gameStat, target]);

  return (
    <div
      className={`bg-gradient-to-r from-transparent via-black/80 to-transparent w-3/4 flex flex-col justify-center items-center gap-2 ${
        animate ? "reveal-from-center" : ""
      }`}
    >
      {gameStat === "waiting_for_cancel_action" ? (
        <>
          <p className="text-amber-50 font-semibold animate-pulse text-bold">
            ¡Rápido! Esta acción se puede detener
          </p>
          {typeof remainingSeconds === "number" && (
            <p className="text-[#bb8512] text-sm font-bold">
              Tiempo restante: {remainingSeconds}s
            </p>
          )}
        </>
      ) : (
        <p className="text-amber-50 font-semibold">
          Esperando selección de {target}
        </p>
      )}

      {isPlayerInAction && (
        <button
          className={`w-40 rounded-lg font-semibold px-3 py-0.5 
                                ${
                                  isEnabled
                                    ? `${buttonTransition} bg-red-900 text-white font-semibold cursor-pointer`
                                    : "bg-gray-500 text-gray-200 cursor-not-allowed"
                                }`}
          onClick={() => {
            action();
          }}
          disabled={!isEnabled}
        >
          Realizar acción
        </button>
      )}
    </div>
  );
};