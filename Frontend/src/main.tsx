import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./containers/App/App.tsx";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Lobby from "./containers/Lobby/Lobby.tsx";
import Game from "./containers/Game/Game.tsx";
// @ts-ignore
import Game_List from "./components/Home/game_list.jsx";

createRoot(document.getElementById("root")!).render(
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<App/>}/>
      {/* <Route path="/game/:gameId" element={<Game/>}/> */}
      <Route path="/lobby/:gameId" element={<Lobby/>}/>
      <Route path="/login"/>
      <Route path="/login"/>
      <Route path="/*" element={<App/>}/>
     <Route path="/api/games" element={<Game_List/>}/>
      <Route path="/game/:gid" element={<Game />} />
    </Routes>   
  </BrowserRouter>
);
