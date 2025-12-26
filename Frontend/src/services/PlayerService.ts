const API_URL = "http://localhost:8000/api";

const PlayerService = {
  read: async (oid: number) => {
    const result = await fetch(`${API_URL}/player/${oid}`, {});
    if (result.ok) {
      return result.json()
    } else {
      console.warn("Error al obtener jugador")
      return null;
    }
  },

  update: async (oid: number, data: object) => {
    const headers = {'Content-Type': 'application/json'}
    const result = await fetch(`${API_URL}/player/${oid}`, {headers: headers, method: 'PATCH', body: JSON.stringify(data)})
    if (result.ok) {
      return result.json();
    } else {
      console.warn("Error al actualizar jugador");
      return null;
    }
  },

  search: async (filter: object) => {
    const headers = {'Content-Type': 'application/json'}
    const result = await fetch(`${API_URL}/player/search`, {headers: headers, method: 'POST', body: JSON.stringify(filter)})
    if (result.ok) {
      return result.json();
    } else {
      console.warn("Error al obtener jugadores");
      return [];
    }
  },

  delete: async (oid: number, data) => {
    const headers = {'Content-Type': 'application/json'}
    const result = await fetch(`${API_URL}/player/${oid}`, {headers: headers, method: 'DELETE', body: JSON.stringify(data)})
    if (result.ok) {
      return result.json();
    } else {
      console.warn("Error al borrar jugador");
      return null;
    }
  },

  create: async (oid: number, data) => {
    console.log(data)
    const headers = {'Content-Type': 'application/json'}
    const result = await fetch(`${API_URL}/player/${oid}`, {headers: headers, method: 'POST', body: JSON.stringify(data)})
    if (result.ok) {
      return result.json();
    } else {
      console.warn("Error al unirse a partida");
      return null;
    }
  },

}

export default PlayerService;