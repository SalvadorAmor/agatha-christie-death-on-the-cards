const API_URL = "http://localhost:8000/api";

export type CreateGameDTO = {
  game_name: string;
  password?: string | null;
  min_players: number;
  max_players: number;
  player_name: string;
  avatar: string;
  birthday: string;
}

const GameService = {
  read: async (oid: number) => {
    const result = await fetch(`${API_URL}/game/${oid}`, {});
    if (result.ok) {
      return result.json();
    } else {
      console.warn("Error al obtener juego");
      return null;
    }
  },

  update: async (oid: number, data) => {
    const headers = {'Content-Type': 'application/json'}
    console.log(data);
    const result = await fetch(`${API_URL}/game/${oid}`, {headers: headers, method: 'PATCH', body: JSON.stringify(data)})
    if (result.ok) {
      return result.json();
    } else {
      console.warn("Error al actualizar juego");
      return null;
    }
  },
  
  create: async (dto: CreateGameDTO) => {
    const headers = { "Content-Type": "application/json" };
    const result = await fetch(`${API_URL}/game/`, {headers: headers, method: "POST", body: JSON.stringify(dto)});
    if (result.ok) {
      return result.json();
    } else {
      console.warn("Error al crear juego");
      return null;
    }
  },

  delete: async (gid: number, data) =>{
    const headers = { "Content-Type": "application/json" };
    const result = await fetch(`${API_URL}/game/${gid}`, {headers: headers, method: "DELETE", body: JSON.stringify(data)});
    if (result.ok) {
      return result.json();
    } else {
      console.warn("Error al crear juego");
      return null;
    }
  },
}

export default GameService;