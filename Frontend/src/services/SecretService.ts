const API_URL = "http://localhost:8000/api";

const SecretService = {

  search: async (filter: object) => {
  const headers = {'Content-Type': 'application/json'}
  const result = await fetch(`${API_URL}/secret/search`, {headers: headers, method: 'POST', body: JSON.stringify(filter)})
  if (result.ok) {
    return result.json();
  } else {
    console.warn("Error al obtener secretos");
    return [];
  }},

  update: async (oid: number, data: object) => {
    const headers = {'Content-Type': 'application/json'}
    const result = await fetch(`${API_URL}/secret/${oid}`, {headers: headers, method: 'PATCH', body: JSON.stringify(data)})
    if (result.ok) {
      return result.json();
    } else {
      console.warn("Error al actualizar secreto");
      return null;
    }
  }
}

export default SecretService