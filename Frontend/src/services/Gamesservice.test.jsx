import { describe, it, expect, vi, beforeEach } from "vitest";
import GameService from "./Game";

const mockFetch = vi.fn();

global.fetch = mockFetch;

describe("GameService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  //SOLO GET GAME
  it("getGame devuelve datos", async () => {
    const mockGame = { id: 1, name: "Partida 1" };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockGame,
    });

    const data = await GameService.getGame(1);

    expect(mockFetch).toHaveBeenCalledWith("http://localhost:8000/api/game/1");
    expect(data).toEqual(mockGame);
  });

  it("getGame maneja error ", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false });

    const consoleSpy = vi.spyOn(console, "log");
    const data = await GameService.getGame(999);

    expect(consoleSpy).toHaveBeenCalledWith("error obteniendo game");
    expect(data).toBeUndefined();
    consoleSpy.mockRestore();
  });

  //GET GAMES

  it("getGames devuelve datos", async () => {
    const filters = { status__eq: "waiting" };
    const mockGames = [{ id: 1, name: "Partida 1" }];
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockGames,
    });

    const data = await GameService.getGames(filters);

    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/game/search",
      {
        method: "POST",
        body: JSON.stringify(filters),
        headers: { "Content-Type": "application/json" },
      }
    );
    expect(data).toEqual(mockGames);
  });

  it("getGames maneja error cuando fetch no ok", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false });

    const consoleSpy = vi.spyOn(console, "log");
    const data = await GameService.getGames({});

    expect(consoleSpy).toHaveBeenCalledWith("error obteniendo juegos");
    expect(data).toBeUndefined();
    consoleSpy.mockRestore();
  });
});
