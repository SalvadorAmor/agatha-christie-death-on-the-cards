import React from "react";
import PlayerService from "../../services/Player";
import { useState, useEffect } from "react";
import { data } from "react-router";
function Game_Item({ game, selected, players }) {
  return (
    <button
      type="button"
      className={`
        relative w-250 flex flex-row justify-between items-center p-3 rounded-lg transition-all duration-200 cursor-pointer
        ${
          selected
            ? "shadow-[0_0_20px_#ff4d4d] bg-red-900 border-white"
            : "borderwhite"
        }
        hover:bg-red-500 mb-5 hover:shadow-[0_0_20px_#ff4d4d"]
      `}
      data-selected={selected ? "true" : "false"}
    >
      {!selected && (<div className="absolute inset-0 bg-white opacity-25 rounded-lg"></div>)}

       <div className="relative flex-1 text-left font-semibold text-lg text-white">
        {game.name}  #{game.id}
      </div>
      <div className="relative text-white">
        {players.length}/{game.max_players}
      </div>
    </button>
  );
}

export default Game_Item;
