const API_URL = "http://localhost:8000/api"; 

export type ChatMessage = {
  id: number;
  game_id: number;
  owner_name?: string | null;
  content: string;
  timestamp: string;
};

const ChatService = {
  search: async (gameId: number): Promise<ChatMessage[]> => {
    try {
      const res = await fetch(`${API_URL}/chat/${gameId}`);
      if (res.ok) return res.json();
      return [];
    } catch (error) {
      console.error("Error obteniendo mensajes chat:", error);
      return [];
    }
  },

  create: async (dto: { game_id: number; owner_id: number; content: string }): Promise<ChatMessage | null> => {
    try {
      const res = await fetch(`${API_URL}/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dto),
      });
      if (res.ok) return await res.json();
      return null;
    } catch (error) {
      console.error("Error creando mensaje chat:", error);
      return null;
    }
  },
};

export default ChatService;