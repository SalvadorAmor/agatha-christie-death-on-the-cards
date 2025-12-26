const API_URL = "http://localhost:8000/api";

const CardService = {

  search: async (filter: object) => {
  const headers = {'Content-Type': 'application/json'}
  const result = await fetch(`${API_URL}/card/search`, {headers: headers, method: 'POST', body: JSON.stringify(filter)})
  if (result.ok) {
    return result.json();
  } else {
    console.warn("Error al obtener cartas");
    return [];
  }},

  update: async (oid: number, data: object) => {
    const headers = {'Content-Type': 'application/json'}
    const result = await fetch(`${API_URL}/card/${oid}`, {headers: headers, method: 'PATCH', body: JSON.stringify(data)})
    if (result.ok) {
      return result.json();
    } else {
      console.warn("Error al actualizar carta");
      return null;
    }
  },

  bulkUpdate: async (cids: number[], dto: object) => {
    const headers = {'Content-Type': 'application/json'};
    
    const result = await fetch(`${API_URL}/card`, {
      headers: headers, 
      method: 'PATCH', 
      body: JSON.stringify({ cids: cids, dto: dto })
    });
    
    if (result.ok) {
      return result.json();
    } else {
      const errorText = await result.text();
      console.error("Error response:", result.status, errorText);
      return null;
    }
  },

  playEvent: async (cid: number, token)=> {
    const result = await fetch(`${API_URL}/card/play_card/${cid}?token=${token}`,
      {
        method: 'POST',
        body: JSON.stringify({
          target_players: [],
          target_secrets: [],
          target_cards: [],
          target_sets: [],
        }),
        headers: {'Content-Type': 'application/json'}
      });
    if (result.ok) {
      return result.json();
    } else {
      console.warn("Error al jugar evento");
      return null;
    }
  },

  playCardWithTargets: async (
    cid: number,
    token: string,
    targets: object ) => {

  const payload = { ...targets, token };

  const res = await fetch(`${API_URL}/card/play_card/${cid}?token=${token}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const t = await res.text().catch(() => "");
    console.warn("Error al jugar evento:", res.status, t);
    return null;
  }
  try { return await res.json(); } catch { return {}; }
},
}

export default CardService