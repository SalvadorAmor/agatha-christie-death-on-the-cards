import Game_Item from "./game_item";
import React, { useEffect, useState } from "react";
import Button, {whiteButtonStyle} from "../Button";
import GameService from "../../services/Game";
import { useNavigate } from "react-router-dom";
import logo from "../../assets/game-logo.png";
import PlayerService from "../../services/Player";
import PlayerServiceOK from "../../services/PlayerService";
import CreateGameDialog from "../CreateGameDialog";
import WebSocketManager from "../WebSocketManager.js";


function Game_List({ prePlayerData }) {
  const [showCreateGameDialog, setShowCreateGameDialog] = useState(false);
  const [showJoinGameDialog, setShowJoinGameDialog] = useState(false);
  const [selectedgame, setSelectedgame] = useState(null);
  const [gamesList, setGamesList] = useState([]);
  const [playerList, setPlayerList] = useState([]);
  const [carouselIndex, setCarouselIndex] = useState(0);
  const itemsPerPage = 3;
  const navigate = useNavigate();

  useEffect(() => {
    GameService.getGames({ status__eq: "waiting" }).then((data) => {
      setGamesList(data);
    });

    PlayerService.getPlayers({}).then(data => {
      setPlayerList(data);
    })

    const wsmanager = new WebSocketManager( null);
    wsmanager.registerOnCreate(data => {
        console.log(data);
        setGamesList(prevGames => [...prevGames, data]);
    }, 'game');
    wsmanager.registerOnCreate(data => {
        console.log(data);
        setPlayerList(prevPlayers => [...prevPlayers, data]);
    }, 'player');
    wsmanager.registerOnDelete(data => {
        console.error(data)
        setPlayerList(prevPlayers => prevPlayers.filter(player => player.id !== data.id));
    }, 'player');
   wsmanager.registerOnDelete(data => {
    setGamesList(prevGames => prevGames.filter(game => game.id !== data.id));
    setSelectedgame(currentSelected => {
      if (currentSelected && currentSelected.id === data.id) {return null;}
      return currentSelected;
    });
  }, 'game');
    return () => {
        wsmanager.close();
    }
  }, []);

  const handlePrev = () => {
    setCarouselIndex((prev) => Math.max(prev - itemsPerPage, 0));
  };

  const handleNext = () => {
    setCarouselIndex((prev) =>
      Math.min(prev + itemsPerPage, gamesList.length - 1)
    );
  };

    const handleJoinGame = () => {
  console.log(prePlayerData)
    const CreatePlayerDTO = {player_name:prePlayerData.name, player_date_of_birth:prePlayerData.birthdate, avatar:prePlayerData.avatar}
    PlayerServiceOK.create(selectedgame.id, CreatePlayerDTO).then(response=>{
      if (response != null){
        localStorage.setItem("player",JSON.stringify(response))
        navigate(`/lobby/${response.game_id}`)
      }
      else{
        alert("Ha ocurrido un error al unirse a la partida")
      }
    })
  };

  // const handleLeave = () => {
  //   sessionStorage.clear();
  // };

  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-start bg-[#470620] overflow-x-hidden overflow-y-auto px-4 sm:px-8 md:px-16 py-6">
      <div className="flex justify-center items-center mb-8">
        <img src={logo} alt="Death on the Cards" className="w-56 sm:w-64 md:w-72" />
      </div>
      {/* carrusel */}
      <div className="w-full max-w-[1100px] mx-auto bg-[#20010D] rounded-xl p-6 my-6 flex flex-col items-center justify-center gap-6">
        <div className=" flex items-center">
          {/* lo que va adentro del carrusel */}
          <div className="flex-col overflow-x-hidden scroll-smooth gap-4 w-full justify-center">
            {gamesList.length > 0 ? (
              gamesList.map((game, index) => (
                <div
                  key={game.id}
                  className={`flex-none w-full px-4 transition-transform duration-300 ${
                    index >= carouselIndex &&
                    index <
                      Math.min(carouselIndex + itemsPerPage, gamesList.length)
                      ? "block"
                      : "hidden"
                  }`}
                  onClick={()=> setSelectedgame(selectedgame?.id === game.id ? null : game)}
                >
                <div className="w-full rounded-xl overflow-hidden">
                  <Game_Item
                    game={game}
                    selected={selectedgame?.id === game.id}
                    players={playerList.filter(player => player.game_id === game.id)}
                  />
                </div>
                </div>
              ))
            ) : (
              <h1 className="text-white text-2l font-semibold mb-4">
                No hay partidas disponibles
              </h1>
            )}
          </div>
        </div>

        {/* Unirse/Crear */}
        <div className="flex flex-col items-center justify-center gap-x-10 mt-6 ">
          <div className="flex flex-row items-center justify-center mt-6">
            {/* atras */}
            <button
              onClick={handlePrev}
              disabled={carouselIndex === 0}
              className=" text-white px-4 py-2 rounded hover:shadow-[0_0_20px_#ff4d4d] disabled:opacity-25"
            >
              {"<"}
            </button>
            {/* adelante */}
            <button
              onClick={handleNext}
              disabled={carouselIndex + itemsPerPage >= gamesList.length}
              className="text-white px-4 py-2 rounded hover:shadow-[0_0_20px_#ff4d4d] disabled:opacity-25"
            >
              {">"}
            </button>
          </div>
        </div>
      </div>
      <div className="inline-flex items-center justify-center gap-x-10 bg-[#20010D] w-full max-w-[1100px] mx-auto rounded-xl p-6 my-6 gap-6">
        <Button
          className={`${whiteButtonStyle}
                        disabled:opacity-40 
                        disabled:cursor-not-allowed
                        disabled:hover:shadow-none disabled:hover:scale-100`}
          label="Unirse a Partida"
          disabled={selectedgame === null}
          onClick={handleJoinGame}
        />
        <Button
          className={`${whiteButtonStyle}`}
          label="Crear Partida"
          onClick={() => setShowCreateGameDialog(true)}
        />
      </div>

      {showCreateGameDialog && (
        <CreateGameDialog
          onClose={() => setShowCreateGameDialog(false)}
          prePlayerData={prePlayerData}
        />
      )}
    </div>
  );
}

export default Game_List;