import React, { useState, useEffect } from 'react'
import {useNavigate, useParams} from 'react-router'
import GameService from "../../services/GameService.ts";
import PlayerService from "../../services/PlayerService.ts";
import logo from "../../assets/game-logo.png";
import estrellaDorada from "../../assets/estrella-dorada.png";
import poirot from "../../assets/pfp-hercule-poirot.jpg";
import marple from "../../assets/pfp-miss-marple.jpg";
import satterhwaite from "../../assets/pfp-mr-satterhwaite.jpg";
import pyne from "../../assets/pfp-parker-pyne.jpg";
import brent from "../../assets/pfp-lady-eileen-brent.jpg";
import tommy from "../../assets/pfp-tommy-beresford.jpg";
import tuppence from "../../assets/pfp-tuppence-beresford.jpg";
import oliver from "../../assets/pfp-ariadne-oliver.jpg";
import WebSocketManager from "../../components/WebSocketManager.tsx";
import CardService from "../../services/CardService.ts";
import { whiteButtonStyle, redButtonStyle } from '../../components/Button.jsx';
import "./Lobby.css";

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

function Lobby() {
  const { gameId } = useParams();
  const [game, setGame] = useState(null);
  const [players, setPlayers] = useState([]);
  const [player , setPlayer] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (gameId) {
        GameService.read(parseInt(gameId))
        .then(data => {
          setGame(data);
          console.log(data);
        })
      .catch ((error) =>  {
        console.error("Error cargando partida.", error);
      })

        PlayerService.search({game_id__eq: parseInt(gameId)})
        .then(data => {
          setPlayers(data);
        })
      .catch ((error) => {
        console.error("Error cargando jugadores.", error);
      })
    }
  }, [gameId]);

  useEffect(() => {
    const localPlayer = localStorage.getItem("player");
    if (localPlayer) {
      setPlayer(JSON.parse(localPlayer))
    }
  }, []);

  useEffect(() => {
    if (!player || !game || !gameId) { return }
    const wsmanager = new WebSocketManager(player.token);
    wsmanager.registerOnUpdate((data) => {
      if (data.id === parseInt(gameId)) {setGame(data);}
    }, 'game');
    wsmanager.registerOnDelete( data => {if (data.id === parseInt(gameId)) { alert("El juego ha sido eliminado por el dueño."); navigate(`/`);}
    }, 'game');
    wsmanager.registerOnCreate(data => {
      console.log("Player update received", data);
      if (data.game_id === parseInt(gameId)) {
        PlayerService.search({game_id__eq: parseInt(gameId)}).then(ps => {
          setPlayers(ps);
        });
      }
    }, 'player');
    wsmanager.registerOnDelete(data => {if (data.game_id === parseInt(gameId)) {PlayerService.search({game_id__eq: parseInt(gameId)}).then(ps => {setPlayers(ps);});}
    }, 'player');
    return () => {
      wsmanager.close();
    }
  }, [player, game]);

  useEffect(() => {
    if (!game) return;
    if (game.status === "started") {
      navigate(`/game/${game.id}`);
    }
  }, [game]);

  const handleComenzar = () => {
    if (player && game) {
      if (player.id === game.owner) {
        GameService.update(game.id, {token: player.token, status: "started"}).then(r => {
          if (r != null) {
            setGame(r); navigate(`/game/${game.id}`);
          } else {
            alert("Ha ocurrido un error al iniciar la partida")
          }
        })
      }
    }
  }

  const handleAbandonar = () => {
    if (player) {
      if (player.id != game.owner){
        PlayerService.delete(player.id, {token: player.token}).then(r => {
          if (r != null) {
            navigate(`/`);
          } else {
            alert("Ha ocurrido un error al salir de la partida")
          }
        })
      }
      else{
        GameService.delete(game.id,{token: player.token}).then(r => {
          if (r != null) {
            navigate(`/`);
          } else {
            alert("Ha ocurrido un error al salir de la partida")
          }
        })
      }
    }
  }

  if (!game || !player) {
    return (
      <div className={'min-h-screen w-full flex flex-col bg-[#470620]'}>
        <h1>Cargando...</h1>
      </div>
    )
  } else {
    return (
      <div className={'min-h-screen w-full flex flex-col bg-[#470620]'}>
        <header>
          <div className="absolute flex justify-center pb-8 pt-4 right-5">
            <button onClick={handleAbandonar} className={redButtonStyle}>
              Abandonar
            </button>
          </div>
          <div className="w-full flex justify-center">
            <img src={logo} alt="Death on the Cards" className="w-[260px]"/>
          </div>
        </header>
        <div className={"flex-1 w-full flex items-start justify-center"}>
          <article
            className={"w-full max-w-[560px] bg-[#230812] rounded-xl border border-black/30 shadow-[0_10px_30px_rgba(0,0,0,1)] px-10 py-8 mt-4 flex flex-col gap-6"}>
          <h2 style={{color: 'white', fontWeight: 'bold', fontSize: 25}}>{game.name} #{game.id}</h2>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr"}}>
            {
              players.map((p) => {
                return (
                  <div key={p.id} style={{color: "white", fontSize: 19, textAlign: "start", display: "flex", flexDirection: "row", padding: 5}} className="slide-in-bottom">
                    <div className="w-20 h-20 rounded-full border-2 border-white overflow-hidden">
                      <img
                        src={(AVATARS.find(a => a.id === p.avatar) || AVATARS[0]).src}
                        alt={""}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <div style={{display: "flex", alignItems: "center"}}>
                      <p style={{padding: 5, fontWeight: "bold"}}>{p.name}</p>
                      {p.id === game.owner && <img src={estrellaDorada} className={"w-[27px] padding-3"} alt={"Dueño"}/>}
                    </div>
                  </div>

                )
              })
            }
          </div>
          <div style={{color: "white"}}>
            {players.length}/{game.max_players} Jugadores
            </div>
          </article>
        </div>
        <footer>
          <div className="w-full flex justify-center pb-8 pt-4">
            <button disabled={players.length < game.min_players}
            onClick={handleComenzar} className={`min-w-[260px] rounded-xl text-black font-semibold px-6 py-2.5 ${game.owner === player.id && players.length >= game.min_players ? `${whiteButtonStyle}` : "bg-gray-600"}`}>
              Comenzar
            </button>
          </div>
        </footer>
      </div>
    )
  }
}

export default Lobby
