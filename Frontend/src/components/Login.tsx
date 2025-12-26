import React, { useState } from "react";
import { useEffect } from "react";
import logo from "../assets/game-logo.png";
import poirot from "../assets/pfp-hercule-poirot.jpg";
import marple from "../assets/pfp-miss-marple.jpg";
import pyne from "../assets/pfp-parker-pyne.jpg";
import satterhwaite from "../assets/pfp-mr-satterhwaite.jpg";
import brent from "../assets/pfp-lady-eileen-brent.jpg";
import tommy from "../assets/pfp-tommy-beresford.jpg";
import tuppence from "../assets/pfp-tuppence-beresford.jpg";
import oliver from "../assets/pfp-ariadne-oliver.jpg";
import { whiteButtonStyle } from "./Button";

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

export default function Login({ setPrePlayerData }) {

  useEffect(() => {
    sessionStorage.clear();
  }, []);

  const [avatarIndex, setAvatarIndex] = useState(0);
  const [name, setName] = useState("");
  const [birth, setBirth] = useState("");
  const [error, setError] = useState("");


  const current = AVATARS[avatarIndex];
  const prev = () =>
    setAvatarIndex((i) => (i - 1 + AVATARS.length) % AVATARS.length);
  const next = () => setAvatarIndex((i) => (i + 1) % AVATARS.length);

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!name || name.length > 16) {
      setError("Nombre inválido (máx 16 caracteres).");
      return;
    }
    const date = new Date(birth);
    if (!birth || isNaN(date.getTime()) || date > new Date()) {
      setError("Fecha inválida.");
      return;
    }
    setPrePlayerData({ name, birthdate: date.toISOString(), avatar: current.id });
    setError("");
  }

return (
  <div className="min-h-screen w-full flex flex-col bg-[#470620]">

    <header className="w-full flex justify-center pt-6 pb-4">
      <img src={logo} alt="Death on the Cards" className="w-[260px]" />
    </header>

    <main className="flex-1 w-full flex items-start justify-center">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-[560px] bg-[#230812] rounded-xl border border-black/30 shadow-[0_10px_30px_rgba(0,0,0,1)] px-10 py-8 mt-4 flex flex-col gap-6"
      >
        <div className="flex items-center justify-center gap-3">
          <button
            type="button"
            onClick={prev}
            className="rounded-full w-6 h-6 flex items-center justify-center bg-white text-black cursor-pointer hover:bg-[#ca8ba1]">
            ‹
          </button>

          <div className="flex flex-col items-center max-w-24 text-nowrap">
            <div className="w-24 h-24 rounded-full border-2 border-white overflow-hidden">
              <img
                src={current.src}
                alt={current.label}
                className="w-full h-full object-cover"
              />
            </div>
            <span className="mt-2 text-sm font-semibold text-white text-center"> {current.label} </span>
          </div>
          <button
            type="button"
            onClick={next}
            className="rounded-full w-6 h-6 flex items-center justify-center bg-white text-black cursor-pointer hover:bg-[#ca8ba1]">
            ›
          </button>
        </div>

        <label className="flex flex-col gap-2">
          <input
            className="w-full rounded-xl bg-white text-black placeholder:text-gray-500 px-4 py-2.5"
            type="text"
            placeholder="Nombre de usuario"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </label>

        <label className="flex flex-col gap-2">
          <input
            className="w-full rounded-xl bg-white text-black placeholder:text-gray-500 px-4 py-2.5"
            type="date"
            placeholder="DD/MM/YYYY"
            value={birth}
            onChange={(e) => setBirth(e.target.value)}
          />
        </label>

        {error && (<p className="text-white text-sm text-center">{error}</p>)}

    <div className="w-full flex justify-center pb-8 pt-4">
        <button
          type="submit"
          className={`${whiteButtonStyle}min-w-[260px]`}>
          Ingresar
        </button>
    </div>  
      </form>
    </main>
  </div>
);
}