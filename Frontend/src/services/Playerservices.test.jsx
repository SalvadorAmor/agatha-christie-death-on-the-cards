import { describe, it, expect, vi, beforeEach } from "vitest";
import PlayerService from "./Player";

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("PlayerService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("devuelve datos", async () => {
    const filters = { game_id__eq: 1 };
    const mockPlayers = [{ id: 1, name: "Jugador 1" }];
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockPlayers,
    });

    const data = await PlayerService.getPlayers(filters);

    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/player/search",
      {
        method: "POST",
        body: JSON.stringify(filters),
        headers: { "Content-Type": "application/json" },
      }
    );
    expect(data).toEqual(mockPlayers);
  });

  it("maneja error ", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false });

    const consoleSpy = vi.spyOn(console, "log");
    const data = await PlayerService.getPlayers({ game_id__eq: 999 });

    expect(consoleSpy).toHaveBeenCalledWith("error obteniendo jugadores");
    expect(data).toBeUndefined();
    consoleSpy.mockRestore();
  });
});
