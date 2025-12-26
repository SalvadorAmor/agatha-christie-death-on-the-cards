  const API_URL = "http://localhost:8000/api";

  const EventTableService = {

    searchInTable: async (filter: object) => {
    const headers = {'Content-Type': 'application/json'}
    const result = await fetch(`${API_URL}/event_table/search`, {headers: headers, method: 'POST', body: JSON.stringify(filter)})
    if (result.ok) {
      return result.json();
    } else {
      console.warn("Error al obtener eventos de la event table");
      return [];
    }},

    cancelAction: async (event_id: number, not_so_fast: number, token: string) =>{
    const headers = {'Content-Type': 'application/json'}
    const result = await fetch(`${API_URL}/card/cancel_action/${event_id}`, {headers: headers, method: 'POST', body: JSON.stringify({not_so_fast: not_so_fast, token: token})})
      if (result.ok) {
      return result.json();
    } else {
      console.warn("Error al cancelar acción");
      return [];
    }
  },
  }

  export default EventTableService