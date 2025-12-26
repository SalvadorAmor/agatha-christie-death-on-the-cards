import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import CardService from "./CardService";

const API = "http://localhost:8000/api";
const mockFetch = vi.fn();
(global as any).fetch = mockFetch;

describe("CardService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("search: devuelve datos", async () => {
    localStorage.setItem("player", JSON.stringify({ token: "jimin" }));
    const filters = { owner__eq: 55 };
    const mockSets = [{ id: 1, detectives: [] }];

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSets,
    });

    const data = await CardService.search(filters);

    expect(mockFetch).toHaveBeenCalledWith(
      `${API}/card/search`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(filters),
      }
    );
    expect(data).toEqual(mockSets);
  });

  it("search: maneja error", async () => {
    localStorage.setItem("player", JSON.stringify({ token: "jimin" }));
    mockFetch.mockResolvedValueOnce({ ok: false });

    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
    const data = await CardService.search({ owner__eq: 999 });

    expect(warnSpy).toHaveBeenCalledWith("Error al obtener cartas");
    expect(data).toEqual([]);
    warnSpy.mockRestore();
  });


  it("search: sin token", async () => {
    const filters = { owner__eq: 1 };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    });

    await CardService.search(filters);

    expect(mockFetch).toHaveBeenCalledWith(
      `${API}/card/search`,
      expect.any(Object)
    );
  });

  it("playCard: POST devuelve json", async () => {
    localStorage.setItem("player", JSON.stringify({ token: "jimin" }));
    const mockResponse = { success: true };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });
    const data = await CardService.playEvent(42, "jimin");

    expect(mockFetch).toHaveBeenCalledWith(
      `${API}/card/play_card/42?token=jimin`,
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
  })

  it("update: PATCH devuelve json", async () => {
    localStorage.setItem("player", JSON.stringify({ token: "jimin" }));
    const mockCard = { id: 10, name: "Test Card", type: "event" };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockCard,
    });
    const data = await CardService.update(10, { name: "Updated Card" });

    expect(mockFetch).toHaveBeenCalledWith(
      `${API}/card/10`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "Updated Card" }),
      }
    );
    expect(data).toEqual(mockCard);

  })

  it("update: maneja error", async () => {
    localStorage.setItem("player", JSON.stringify({ token: "jimin" }));
    mockFetch.mockResolvedValueOnce({ ok: false });

    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
    const data = await CardService.update(10, { name: "Updated Card" });

    expect(warnSpy).toHaveBeenCalledWith("Error al actualizar carta");
    expect(data).toBeNull();
    warnSpy.mockRestore();
  })

  it("bulkUpdate: PATCH devuelve json", async () => {
    localStorage.setItem("player", JSON.stringify({ token: "jimin" }));
    const mockCards = [
      { id: 1, name: "Card 1", type: "event" },
      { id: 2, name: "Card 2", type: "asset" },
    ];

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockCards,
    });
    const data = await CardService.bulkUpdate([1,2], { discarded_turn: 0 });
    expect(mockFetch).toHaveBeenCalledWith(
      `${API}/card`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cids: [1,2], dto: { discarded_turn: 0 } }),
      }
    );
    expect(data).toEqual(mockCards);
  });

  it("bulkUpdate: maneja error", async () => {
    localStorage.setItem("player", JSON.stringify({ token: "jimin" }));
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500, text: async () => "Ejemplo" });

    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    const data = await CardService.bulkUpdate([1,2], { discarded_turn: 0 });

    expect(errorSpy).toHaveBeenCalledWith("Error response:", 500, "Ejemplo");
    expect(data).toBeNull();
    errorSpy.mockRestore();
  })

  it("playEvent: maneja error", async () => {
    localStorage.setItem("player", JSON.stringify({ token: "jimin" }));
    mockFetch.mockResolvedValueOnce({ ok: false });

    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
    const data = await CardService.playEvent(42, "jimin");

    expect(warnSpy).toHaveBeenCalledWith("Error al jugar evento");
    expect(data).toBeNull();
    warnSpy.mockRestore();

  })
  
  it("playCardWithTargets: POST con token", async () => {
  localStorage.setItem("player", JSON.stringify({ token: "jimin" }));

  const mockResponse = { success: true, moved: [7] };
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => mockResponse,
  });

  const targets = {
    target_players: [1],
    target_secrets: [],
    target_cards: [7],
    target_sets: [],
  };

  const data = await CardService.playCardWithTargets(99, "jimin", targets);

  expect(mockFetch).toHaveBeenCalledWith(
    `${API}/card/play_card/99?token=jimin`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...targets, token: "jimin" }),
    }
  );
  expect(data).toEqual(mockResponse);
});

it("playCardWithTargets: maneja error", async () => {
  mockFetch.mockResolvedValueOnce({
    ok: false,
    status: 401,
    text: async () => "Token inválido",
  });

  const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

  const res = await CardService.playCardWithTargets(42, "bad", {
    target_players: [],
    target_secrets: [],
    target_cards: [72],
    target_sets: [],
  });

  expect(warnSpy).toHaveBeenCalledWith("Error al jugar evento:", 401, "Token inválido");
  expect(res).toBeNull();

  warnSpy.mockRestore();
});

it("playCardWithTargets:json() falla", async () => {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => {
      throw new Error("invalid json");
    },
  });

  const res = await CardService.playCardWithTargets(50, "jimin", {
    target_players: [],
    target_secrets: [],
    target_cards: [],
    target_sets: [],
  });

  expect(res).toEqual({});
});

});