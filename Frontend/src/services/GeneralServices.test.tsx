import { describe, it, expect, vi, beforeEach } from "vitest";
import CardService from "./CardService";
import GameService from "./GameService";
import PlayerService from "./PlayerService";
import SecretService from "./SecretService";
import type { CreateGameDTO } from "./GameService";

const mockFetch = vi.fn();
global.fetch = mockFetch;


//CARD SERVICE
describe("CardService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // SEARCH
  //caso ok
  it("search devuelve datos ", async () => {
    const mockCards = [{ id: 1, name: "test-card" }];
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockCards,
    });

    const filter = { owner__eq: 1 };
    const data = await CardService.search(filter);

    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/card/search",
      {
        headers: { "Content-Type": "application/json" },
        method: "POST",
        body: JSON.stringify(filter),
      }
    );
    expect(data).toEqual(mockCards);
  });

  //caso borde
  it("search maneja error y devuelve array vacío", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false });

    const consoleSpy = vi.spyOn(console, "warn");
    const data = await CardService.search({});

    expect(consoleSpy).toHaveBeenCalledWith("Error al obtener cartas");
    expect(data).toEqual([]);
    consoleSpy.mockRestore();
  });

  // UPDATE
  //caso ok
  it("update devuelve datos", async () => {
    const mockCard = { id: 1, name: "updated-card" };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockCard,
    });

    const data = await CardService.update(1, { turn_discarded: 0 });

    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/card/1",
      {
        headers: { "Content-Type": "application/json" },
        method: "PATCH",
        body: JSON.stringify({ turn_discarded: 0 }),
      }
    );
    expect(data).toEqual(mockCard);
  });

  //caso borde
  it("update maneja error y devuelve null", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false });

    const consoleSpy = vi.spyOn(console, "warn");
    const data = await CardService.update(999, {});

    expect(consoleSpy).toHaveBeenCalledWith("Error al actualizar carta");
    expect(data).toBeNull();
    consoleSpy.mockRestore();
  });
});

// BULK UPDATE
// caso ok
it("bulkUpdate devuelve datos", async () => {
  const mockResponse = { updated: 2 };
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => mockResponse,
  });

  const cids = [1, 2];
  const dto = { owner: 5 };
  const data = await CardService.bulkUpdate(cids, dto);

  expect(mockFetch).toHaveBeenCalledWith(
    "http://localhost:8000/api/card",
    {
      headers: { "Content-Type": "application/json" },
      method: "PATCH",
      body: JSON.stringify({ cids: cids, dto: dto }),
    }
  );
  expect(data).toEqual(mockResponse);
});

// caso borde
it("bulkUpdate maneja error y devuelve null", async () => {
  mockFetch.mockResolvedValueOnce({
    ok: false,
    status: 400,
    text: async () => "Bad Request",
  });

  const consoleErrorSpy = vi.spyOn(console, "error");
  const data = await CardService.bulkUpdate([999], {});

  expect(consoleErrorSpy).toHaveBeenCalledWith(
    "Error response:",
    400,
    "Bad Request"
  );
  expect(data).toBeNull();
  consoleErrorSpy.mockRestore();
});

// PLAY EVENT
// caso ok
it("playEvent devuelve datos", async () => {
  const mockResponse = { success: true };
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => mockResponse,
  });

  const cid = 10;
  const token = "abc123";
  const data = await CardService.playEvent(cid, token);

  expect(mockFetch).toHaveBeenCalledWith(
    "http://localhost:8000/api/card/play_card/10?token=abc123",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target_players: [],
        target_secrets: [],
        target_cards: [],
        target_sets: [],
      }),
    }
  );
  expect(data).toEqual(mockResponse);
});

// caso borde
it("playEvent maneja error y devuelve null", async () => {
  mockFetch.mockResolvedValueOnce({ ok: false });

  const consoleSpy = vi.spyOn(console, "warn");
  const data = await CardService.playEvent(999, "token123");

  expect(consoleSpy).toHaveBeenCalledWith("Error al jugar evento");
  expect(data).toBeNull();
  consoleSpy.mockRestore();
});

//GAME SERVICE
describe("GameService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // READ
  //caso ok
  it("read devuelve datos", async () => {
    const mockGame = { id: 1, name: "Partida 1" };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockGame,
    });

    const data = await GameService.read(1);

    expect(mockFetch).toHaveBeenCalledWith("http://localhost:8000/api/game/1", {});
    expect(data).toEqual(mockGame);
  });

  //caso borde
  it("read maneja error y devuelve null", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false });

    const consoleSpy = vi.spyOn(console, "warn");
    const data = await GameService.read(9945529); //ID INEXISTENTE

    expect(consoleSpy).toHaveBeenCalledWith("Error al obtener juego");
    expect(data).toBeNull();
    consoleSpy.mockRestore();
  });

  // UPDATE
  //caso ok
  it("update devuelve datos", async () => {
    const mockGame = { id: 1, name: "Partida Actualizada" };
    const update = { current_turn: 2 };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockGame,
    });

    const data = await GameService.update(1, update);

    expect(mockFetch).toHaveBeenCalledWith("http://localhost:8000/api/game/1", {
      headers: { "Content-Type": "application/json" },
      method: "PATCH",
      body: JSON.stringify(update),
    });
    expect(data).toEqual(mockGame);
  });

  //caso borde
  it("update maneja error y devuelve null", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false });

    const consoleSpy = vi.spyOn(console, "warn");
    const data = await GameService.update(9945529, {});

    expect(consoleSpy).toHaveBeenCalledWith("Error al actualizar juego");
    expect(data).toBeNull();
    consoleSpy.mockRestore();
  });

  // CREATE
  //caso ok
  it("create devuelve datos", async () => {
    const dto: CreateGameDTO = {
      game_name: "Nueva Partida",
      min_players: 2,
      max_players: 6,
      player_name: "Jugador1",
      avatar: "detective1",
      birthday: "2000-01-01",
    };
    const mockGame = { id: 1, ...dto };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockGame,
    });

    const data = await GameService.create(dto);

    expect(mockFetch).toHaveBeenCalledWith("http://localhost:8000/api/game/", {
      headers: { "Content-Type": "application/json" },
      method: "POST",
      body: JSON.stringify(dto),
    });
    expect(data).toEqual(mockGame);
  });

  //caso borde
  it("create maneja error y devuelve null", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false }); //aca simula el fallo

    const consoleSpy = vi.spyOn(console, "warn");
    const data = await GameService.create({
      game_name: "Fail",
      min_players: 2,
      max_players: 6,
      player_name: "X",
      avatar: "detective1",
      birthday: "2000-01-01",
    });

    expect(consoleSpy).toHaveBeenCalledWith("Error al crear juego");
    expect(data).toBeNull();
    consoleSpy.mockRestore();
  });

  // DELETE
  //caso ok
  it("delete devuelve datos", async () => {
    const response = { token: "XYZ" };
    const mockResp = { ok: true };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResp,
    });

    const data = await GameService.delete(1, response);

    expect(mockFetch).toHaveBeenCalledWith("http://localhost:8000/api/game/1", {
      headers: { "Content-Type": "application/json" },
      method: "DELETE",
      body: JSON.stringify(response),
    });
    expect(data).toEqual(mockResp);
  });
//caso borde
  it("delete maneja error y devuelve null", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false });

    const consoleSpy = vi.spyOn(console, "warn");
    const data = await GameService.delete(9945529, {});

    expect(consoleSpy).toHaveBeenCalledWith("Error al crear juego");
    expect(data).toBeNull();
    consoleSpy.mockRestore();
  });
});

//PLAYER SERVICE

describe("PlayerService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // READ
  //caso ok
  it("read devuelve datos", async () => {
    const mockPlayer = { id: 1, name: "Jugador1" };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockPlayer,
    } as any);

    const data = await PlayerService.read(1);

    expect(mockFetch).toHaveBeenCalledWith("http://localhost:8000/api/player/1", {});
    expect(data).toEqual(mockPlayer);
  });


  //caso borde
  it("read maneja error y devuelve null", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false } as any);
    const consoleSpy = vi.spyOn(console, "warn");

    const data = await PlayerService.read(999);
    expect(consoleSpy).toHaveBeenCalledWith("Error al obtener jugador");
    expect(data).toBeNull();

    consoleSpy.mockRestore();
  });

  // UPDATE

  //caso ok
  it("update envía datos", async () => {
    const dto = { name: "NuevoNombre" };
    const mockResp = { ok: true };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResp,
    } as any);

    const data = await PlayerService.update(1, dto);

    expect(mockFetch).toHaveBeenCalledWith("http://localhost:8000/api/player/1", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dto),
    });
    expect(data).toEqual(mockResp);
  });


  //caso vorde
  it("update maneja error y devuelve null", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false } as any);
    const consoleSpy = vi.spyOn(console, "warn");

    const data = await PlayerService.update(1, { name: "X" });
    expect(consoleSpy).toHaveBeenCalledWith("Error al actualizar jugador");
    expect(data).toBeNull();

    consoleSpy.mockRestore();
  });

  // SEARCH

  //caso ok
  it("search devuelve lista de jugadores", async () => {
    const filter = { game_id__eq: 1 };
    const mockPlayers = [{ id: 1 }, { id: 2 }];
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockPlayers,
    } as any);

    const data = await PlayerService.search(filter);

    expect(mockFetch).toHaveBeenCalledWith("http://localhost:8000/api/player/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(filter),
    });
    expect(data).toEqual(mockPlayers);
  });


  //caso borde
  it("search maneja error y devuelve []", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false } as any);
    const consoleSpy = vi.spyOn(console, "warn");

    const data = await PlayerService.search({});
    expect(consoleSpy).toHaveBeenCalledWith("Error al obtener jugadores");
    expect(data).toEqual([]);

    consoleSpy.mockRestore();
  });

  // DELETE

  //caso ok
  it("delete envía datos y devuelve respuesta", async () => {
    const dto = { token: "XYZ" };
    const mockResp = { ok: true };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResp,
    } as any);

    const data = await PlayerService.delete(1, dto);

    expect(mockFetch).toHaveBeenCalledWith("http://localhost:8000/api/player/1", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dto),
    });
    expect(data).toEqual(mockResp);
  });


  //caso borde
  it("delete maneja error y devuelve null", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false } as any);
    const consoleSpy = vi.spyOn(console, "warn");

    const data = await PlayerService.delete(1, {});
    expect(consoleSpy).toHaveBeenCalledWith("Error al borrar jugador");
    expect(data).toBeNull();

    consoleSpy.mockRestore();
  });

  // CREATE

  //caso ok
  it("create envía datos y devuelve respuesta", async () => {
    const dto = { name: "JugadorNuevo" };
    const mockResp = { id: 5 };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResp,
    } as any);

    const data = await PlayerService.create(1, dto);

    expect(mockFetch).toHaveBeenCalledWith("http://localhost:8000/api/player/1", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dto),
    });
    expect(data).toEqual(mockResp);
  });


  //caso borde
  it("create maneja error y devuelve null", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false } as any);
    const consoleSpy = vi.spyOn(console, "warn");

    const data = await PlayerService.create(1, { name: "X" });
    expect(consoleSpy).toHaveBeenCalledWith("Error al unirse a partida");
    expect(data).toBeNull();

    consoleSpy.mockRestore();
  });
});

//SECRET SERCIVE

describe("SecretService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // SEARCH
  //caso ok
  it("search devuelve secretos correctamente", async () => {
    const filter = { game_id__eq: 1 };
    const mockSecrets = [{ id: 1 }, { id: 2 }];
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSecrets,
    } as any);

    const data = await SecretService.search(filter);

    expect(mockFetch).toHaveBeenCalledWith("http://localhost:8000/api/secret/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(filter),
    });
    expect(data).toEqual(mockSecrets);
  });

  //caso borde
  it("search maneja error y devuelve []", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false } as any);
    const consoleSpy = vi.spyOn(console, "warn");

    const data = await SecretService.search({});
    expect(consoleSpy).toHaveBeenCalledWith("Error al obtener secretos");
    expect(data).toEqual([]);

    consoleSpy.mockRestore();
  });

  // UPDATE
  //caso ok
  it("update envía datos y devuelve respuesta", async () => {
    const dto = { revealed: true };
    const mockResp = { id: 1, revealed: true };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResp,
    } as any);

    const data = await SecretService.update(1, dto);

    expect(mockFetch).toHaveBeenCalledWith("http://localhost:8000/api/secret/1", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dto),
    });
    expect(data).toEqual(mockResp);
  });

  //caso vorde
  it("update maneja error y devuelve null", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false } as any);
    const consoleSpy = vi.spyOn(console, "warn");

    const data = await SecretService.update(1, { revealed: true });
    expect(consoleSpy).toHaveBeenCalledWith("Error al actualizar secreto");
    expect(data).toBeNull();

    consoleSpy.mockRestore();
  });
});
