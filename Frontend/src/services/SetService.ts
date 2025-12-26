const API_URL = "http://localhost:8000/api";

function getToken() {
  return JSON.parse(localStorage.getItem("player") || "{}")?.token;
}

function withToken(url: string) {
  const t = getToken();
  return t ? `${url}?token=${encodeURIComponent(t)}` : url;
}

const jsonHeaders = { "Content-Type": "application/json" };

const SetService = {
  read: async (oid: number) => {
    const result = await fetch(withToken(`${API_URL}/detective_set/${oid}`));
    if (result.ok) {
      return result.json();
    } else {
      console.warn("Error al obtener set");
      return null;
    }
  },

  search: async (filter: object) => {
    const result = await fetch(withToken(`${API_URL}/detective_set/search`), {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(filter),
    });
    if (result.ok) {
      return result.json();
    } else {
      console.warn("Error al obtener sets");
      return [];
    }
  },

  create: async (data: object) => {
    const result = await fetch(withToken(`${API_URL}/detective_set`), {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(data),
    });
    if (result.ok) {
      return result.json();
    } else {
      console.warn("Error al crear set");
      return null;
    }
  },

  set_action: async (sid: number, data: object) => {
    const result = await fetch((`${API_URL}/detective_set/${sid}`), {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(data),
    });
    if (result.ok) {
      return result.json();
    } else {
      console.warn("Error al jugar efecto de set");
      return null;
    }
  },

  update: async (sid: number, data: {add_card: number; token: string}) => {
    const result = await fetch(`${API_URL}/detective_set/update/${sid}`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(data),
    });
    if (result.ok) return result.json();
    console.warn("Error al actualizar set");
    return null;
  }
};

export default SetService;