import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import SetService from "./SetService";

const API = "http://localhost:8000/api";
const mockFetch = vi.fn();
(global as any).fetch = mockFetch;

describe("SetService", () => {
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

    const data = await SetService.search(filters);

    expect(mockFetch).toHaveBeenCalledWith(
      `${API}/detective_set/search?token=jimin`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(filters),
      }
    );
    expect(data).toEqual(mockSets);
  });

  it("search: sin token", async () => {
    const filters = { owner__eq: 1 };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    });

    await SetService.search(filters);

    expect(mockFetch).toHaveBeenCalledWith(
      `${API}/detective_set/search`,
      expect.any(Object)
    );
  });

  it("search: maneja error", async () => {
    localStorage.setItem("player", JSON.stringify({ token: "jimin" }));
    mockFetch.mockResolvedValueOnce({ ok: false });

    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
    const data = await SetService.search({ owner__eq: 999 });

    expect(warnSpy).toHaveBeenCalledWith("Error al obtener sets");
    expect(data).toEqual([]);
    warnSpy.mockRestore();
  });

  it("read: devuelve un set", async () => {
    localStorage.setItem("player", JSON.stringify({ token: "jimin" }));
    const mockSet = { id: 7 };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSet,
    });

    const data = await SetService.read(7);

    expect(mockFetch).toHaveBeenCalledWith(`${API}/detective_set/7?token=jimin`);
    expect(data).toEqual(mockSet);
  });

  it("read: sin token", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false });

    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
    const data = await SetService.read(5);

    expect(mockFetch).toHaveBeenCalledWith(`${API}/detective_set/5`);
    expect(warnSpy).toHaveBeenCalledWith("Error al obtener set");
    expect(data).toBeNull();
    warnSpy.mockRestore();
  });
  
  it("create: POST devuelve json", async () => {
    localStorage.setItem("player", JSON.stringify({ token: "jimin" }));
    const payload = { detectives: [1, 2, 3] };
    const created = { id: 123, ...payload };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => created,
    });

    const data = await SetService.create(payload);

    expect(mockFetch).toHaveBeenCalledWith(`${API}/detective_set?token=jimin`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    expect(data).toEqual(created);
  });

  it("create: maneja error", async () => {
    localStorage.setItem("player", JSON.stringify({ token: "jimin" }));
    mockFetch.mockResolvedValueOnce({ ok: false });

    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
    const data = await SetService.create({ detectives: [] });

    expect(warnSpy).toHaveBeenCalledWith("Error al crear set");
    expect(data).toBeNull();
    warnSpy.mockRestore();
  });
  it("set_action devuelve datos", async () => {
  const payload = { target_player: 2, token: "abc123" };
  const mockResponse = { success: true };
  
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => mockResponse,
  });

  const data = await SetService.set_action(5, payload);

  expect(mockFetch).toHaveBeenCalledWith(
    `${API}/detective_set/5`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }
  );
  expect(data).toEqual(mockResponse);
});

it("set_action maneja error", async () => {
  mockFetch.mockResolvedValueOnce({ ok: false });

  const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
  const data = await SetService.set_action(999, { target_player: 1 });

  expect(warnSpy).toHaveBeenCalledWith("Error al jugar efecto de set");
  expect(data).toBeNull();
  warnSpy.mockRestore();
});
it("update: realiza POST y devuelve json", async () => {
  const sid = 10;
  const payload = { add_card: 42, token: "abc123" };
  const mockResponse = { id: sid, updated: true };

  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => mockResponse,
  });

  const data = await SetService.update(sid, payload);

  expect(mockFetch).toHaveBeenCalledWith(
    `${API}/detective_set/update/${sid}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }
  );
  expect(data).toEqual(mockResponse);
});

it("update: maneja error", async () => {
  const sid = 99;
  const payload = { add_card: 1, token: "xyz" };
  mockFetch.mockResolvedValueOnce({ ok: false });

  const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
  const data = await SetService.update(sid, payload);

  expect(mockFetch).toHaveBeenCalledWith(
    `${API}/detective_set/update/${sid}`,
    expect.any(Object)
  );
  expect(warnSpy).toHaveBeenCalledWith("Error al actualizar set");
  expect(data).toBeNull();

  warnSpy.mockRestore();
});

});