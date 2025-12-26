import React, { useState } from "react";
import GameService from "../services/GameService";
import type { CreateGameDTO } from "../services/GameService";
import { useNavigate } from "react-router-dom";
import { redButtonStyle, whiteButtonStyle } from "./Button";

type Prop = {
  onClose: () => void;
  prePlayerData: {
    name: string;
    birthdate: string;
    avatar: string;
  };
};

export default function CreateGameDialog({ onClose, prePlayerData }: Prop) {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [maxPlayers, setMaxPlayers] = useState(4);
  const [minPlayers, setMinPlayers] = useState(2);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!name.trim()) {
      setError("El nombre no puede estar vacío.");
      return;
    }

    if (maxPlayers < 2 || maxPlayers > 6) {
      setError("La partida debe tener entre 2 y 6 jugadores.");
      return;
    }

    if (minPlayers < 2 || minPlayers > 6) {
      setError("La partida debe tener entre 2 y 6 jugadores.");
      return;
    }

    if (maxPlayers < minPlayers) {
      setError("La cantidad máxima de jugadores no puede ser menor que la mínima.");
      return;
    }

    setError("");

    const dto: CreateGameDTO = {
      game_name: name,
      min_players: minPlayers,
      max_players: maxPlayers,
      player_name: prePlayerData.name,
      avatar: prePlayerData.avatar,
      birthday: prePlayerData.birthdate,
    };

    try {
      const response: { player: any } = await GameService.create(dto);
      if (response != null) {
        localStorage.setItem("player", JSON.stringify(response.player));
        navigate(`/lobby/${response.player.game_id}`);
        onClose();
      } else {
        setError("Error al navegar al lobby.");
      }
    } catch (err: any) {
      setError(err?.message || "Error creando la partida.");
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 backdrop-blur-sm bg-black/40 fade" />
      <div className="relative w-[520px] rounded-4xl bg-[#230812] p-8 shadow-[0_20px_60px_rgba(0,0,0,0.8)] fade-pop">
        <h1 className="text-center text-xl font-extrabold text-white slide-in-bottom">
          Crear Partida
        </h1>

        <form
          onSubmit={handleSubmit}
          className="w-full max-w-[560px] px-10 py-8 mt-4 flex flex-col gap-6 slide-in-bottom"
        >
          <label className="flex flex-col gap-1">
            <span className="text-white">Nombre</span>
            <input
              className="w-full rounded-xl bg-white text-black px-4 py-2.5"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-white">Cantidad mínima de jugadores</span>
            <input
              role="minimo"
              id="min"
              className="w-full rounded-xl bg-white text-black px-4 py-2.5"
              type="number"
              value={minPlayers}
              onChange={(e) => setMinPlayers(Number(e.target.value))}
            />

            <span className="text-white mt-5">Cantidad máxima de jugadores</span>
            <input
              role="maximo"
              id="max"
              className="w-full rounded-xl bg-white text-black px-4 py-2.5"
              type="number"
              value={maxPlayers}
              onChange={(e) => setMaxPlayers(Number(e.target.value))}
            />
          </label>

          {error && (
            <p className="text-white text-sm text-center">{error}</p>
          )}

          <div className="flex justify-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className={redButtonStyle}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className={whiteButtonStyle}
            >
              Confirmar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}