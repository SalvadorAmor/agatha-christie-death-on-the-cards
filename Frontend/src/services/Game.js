const API_URL = "http://localhost:8000/api"


const GameService={
    getGame:async(gid)=>{
        const response = await fetch(`${API_URL}/game/${gid}`)
        if (response.ok) {
            return response.json()
        }else{
            console.log("error obteniendo game");
        }
    },

    getGames:async(filters)=>{
        const response = await fetch(`${API_URL}/game/search`, {method:"POST", body: JSON.stringify(filters), headers: {'Content-Type': "application/json"}})
        if (response.ok) {
            return response.json();
        }else{
            console.log("error obteniendo juegos");
        }
    }

}
export default GameService; 