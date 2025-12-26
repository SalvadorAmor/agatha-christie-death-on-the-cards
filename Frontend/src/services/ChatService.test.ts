import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import ChatService from "./ChatService";

const API_URL = "http://localhost:8000/api";
const mockFetch = vi.fn();
(global as any).fetch = mockFetch;

describe("ChatService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe("search", () => {
    it("devuelve datos exitosamente", async () => {
      const gameId = 1;
      const mockMessages = [
        { id: 1, game_id: 1, owner_name: "Player1", content: "Hello", timestamp: "2023-01-01T00:00:00Z" },
        { id: 2, game_id: 1, owner_name: null, content: "Evento", timestamp: "2023-01-01T00:01:00Z" },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockMessages,
      });

      const data = await ChatService.search(gameId);

      expect(mockFetch).toHaveBeenCalledWith(`${API_URL}/chat/${gameId}`);
      expect(data).toEqual(mockMessages);
    });

    it("maneja error de red", async () => {
      const gameId = 1;
      mockFetch.mockRejectedValueOnce(new Error("Network error"));

      const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
      const data = await ChatService.search(gameId);

      expect(errorSpy).toHaveBeenCalledWith("Error obteniendo mensajes chat:", expect.any(Error));
      expect(data).toEqual([]);
      errorSpy.mockRestore();
    });

    it("maneja respuesta no ok", async () => {
      const gameId = 1;
      mockFetch.mockResolvedValueOnce({ ok: false });

      const data = await ChatService.search(gameId);

      expect(data).toEqual([]);
    });
  });

  describe("create", () => {
    it("POST devuelve json exitosamente", async () => {
      const dto = { game_id: 1, owner_id: 123, content: "Test message" };
      const mockMessage = {
        id: 1,
        game_id: 1,
        owner_name: "Player123",
        content: "Test message",
        timestamp: "2023-01-01T00:00:00Z",
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockMessage,
      });

      const data = await ChatService.create(dto);

      expect(mockFetch).toHaveBeenCalledWith(`${API_URL}/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dto),
      });
      expect(data).toEqual(mockMessage);
    });

    it("maneja error de red", async () => {
      const dto = { game_id: 1, owner_id: 123, content: "Test message" };
      mockFetch.mockRejectedValueOnce(new Error("Network error"));

      const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
      const data = await ChatService.create(dto);

      expect(errorSpy).toHaveBeenCalledWith("Error creando mensaje chat:", expect.any(Error));
      expect(data).toBeNull();
      errorSpy.mockRestore();
    });

    it("maneja respuesta no ok", async () => {
      const dto = { game_id: 1, owner_id: 123, content: "Test message" };
      mockFetch.mockResolvedValueOnce({ ok: false });

      const data = await ChatService.create(dto);

      expect(data).toBeNull();
    });
  });
});
