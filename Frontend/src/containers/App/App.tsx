import Login from "../../components/Login";
import Game_List from "../../components/Home/game_list.jsx"
import { useState } from "react";

type PrePlayer = {
  name: string;
  birthdate: string;
  avatar: string;
}

export default function App() {
  const [prePlayerData, setPrePlayerData] = useState<PrePlayer | null>();

  return (
    <>
      {!prePlayerData ? <Login setPrePlayerData={setPrePlayerData} /> : <Game_List prePlayerData={prePlayerData}/>}
    </>
  );
}


