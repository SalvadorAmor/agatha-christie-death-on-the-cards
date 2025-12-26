import React from "react";
import { useNavigate } from "react-router-dom";
import { redButtonStyle } from "./Button";

type WinDialogProps = {
  open: boolean;                         
  murdererEscaped: boolean; // true se escapo, false capturado
  murdererName: string;
  murdererAvatar: string;
  navigateTo?: string;
};

export default function WinDialog({
  open,
  murdererEscaped,
  murdererName, murdererAvatar,
  navigateTo = "/game_list",
}: WinDialogProps) {
  const navigate = useNavigate();

  if (!open) return null;

  const title = murdererEscaped ? "¡El asesino se escapó!" : "¡El asesino fue capturado!";

  const handleBack = () => {
    navigate(navigateTo);
  };


  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 backdrop-blur-sm bg-black/40 z-0 fade" />

      <div className="relative z-10 w-[520px] rounded-4xl bg-[#230812] p-8 shadow-[0_20px_60px_rgba(0,0,0,0.8)] fade-pop">
        <h1 className="text-center text-2xl font-extrabold text-white slide-in-bottom">
          {title}
        </h1>

        <div className="flex flex-col items-center justify-center mt-6 gap-4 slide-in-bottom">
          <img
            src={murdererAvatar}
            alt="asesino"
            className="w-30 h-30 rounded-full border-4 border-[#8D0000] object-cover"
          />
          <p className="text-white text-lg font-semibold">{murdererName}</p>
        </div>

        <div className="flex justify-center mt-8 slide-in-bottom">
          <button
            onClick={handleBack}
            className={redButtonStyle}
          >
            Volver al inicio
          </button>
        </div>
      </div>
    </div>
  );
}