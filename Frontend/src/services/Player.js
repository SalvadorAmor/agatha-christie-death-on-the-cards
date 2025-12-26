const API_URL = "http://localhost:8000/api"


const PlayerService={
    getPlayers:async(filters)=>{
        const response = await fetch(`${API_URL}/player/search`, {method:"POST", body: JSON.stringify(filters), headers: {'Content-Type': "application/json"}})
        if (response.ok) {
            return response.json()
        }else{
            console.log("error obteniendo jugadores");
        }
    },
}
export default PlayerService; 