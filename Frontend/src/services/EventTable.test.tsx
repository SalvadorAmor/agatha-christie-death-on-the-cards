import { describe, it, expect, vi, beforeEach } from "vitest";
import EventTableService from "./EventTableService";

const API_URL = "http://localhost:8000/api";

describe("EventTableService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn(); // mock global fetch
  });

  describe("searchInTable", () => {
    it("hace post y devuelve bien", async () => {
      const mockResponse = [{ id: 1, action: "action" }];
      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue(mockResponse),
      });

      const filter = { game_id__eq: 10 };
      const result = await EventTableService.searchInTable(filter);

      expect(fetch).toHaveBeenCalledWith(
        `${API_URL}/event_table/search`,
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(filter),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it("maneja el resultado no ok", async () => {
      const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
      (fetch as any).mockResolvedValueOnce({
        ok: false,
        json: vi.fn(),
      });

      const result = await EventTableService.searchInTable({ test: true });

      expect(fetch).toHaveBeenCalledTimes(1);
      expect(warnSpy).toHaveBeenCalledWith(
        "Error al obtener eventos de la event table"
      );
      expect(result).toEqual([]);
      warnSpy.mockRestore();
    });
  });

  describe("cancelAction", () => {
    it("hace post y devuelve todo obien", async () => {
      const mockResponse = { success: true };
      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue(mockResponse),
      });

      const result = await EventTableService.cancelAction(42, 99, "abc123");

      expect(fetch).toHaveBeenCalledWith(
        `${API_URL}/card/cancel_action/42`,
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ not_so_fast: 99, token: "abc123" }),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it("maneja si el result no ok", async () => {
      const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
      (fetch as any).mockResolvedValueOnce({
        ok: false,
        json: vi.fn(),
      });

      const result = await EventTableService.cancelAction(1, 2, "abc");

      expect(fetch).toHaveBeenCalledTimes(1);
      expect(warnSpy).toHaveBeenCalledWith("Error al cancelar acción");
      expect(result).toEqual([]);
      warnSpy.mockRestore();
    });

  });
});