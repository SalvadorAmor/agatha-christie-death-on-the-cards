import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import WebSocketManager from "./WebSocketManager";

// MOCKS
const mockWebSocketSend = vi.fn();
const mockWebSocketClose = vi.fn();
const mockWebSocketAddEventListener = vi.fn();

class MockWebSocket {
  url: string;
  readyState: number = 1; // ws ya està abierto
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  listeners: Map<string, Function[]> = new Map();

  constructor(url: string) {
    this.url = url;
    setTimeout(() => this.onopen?.(new Event("open")), 0);
  }

  send = mockWebSocketSend;
  close = mockWebSocketClose;

  addEventListener = (event: string, callback: Function) => {
    mockWebSocketAddEventListener(event, callback);
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)?.push(callback);
  };

  removeEventListener = vi.fn();
  dispatchEvent = vi.fn();
}

vi.stubGlobal("WebSocket", MockWebSocket);

describe("WebSocketManager", () => {
  let wsManager: WebSocketManager;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    wsManager?.close();
  });

  describe("Conexion Websocket", () => {
    it("debería conectar con token", async () => {
      const consoleSpy = vi.spyOn(console, "log").mockImplementation(() => {});

      wsManager = new WebSocketManager("test-token-123");

      await vi.waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith("WebSocket connected");
      });
      expect(wsManager["socket"]).toBeDefined();
      expect(wsManager["socket"]?.url).toContain("token=test-token-123");

      consoleSpy.mockRestore();
    });

    it("debería conectar sin token", async () => {
      const consoleSpy = vi.spyOn(console, "log").mockImplementation(() => {});

      wsManager = new WebSocketManager(null);

      await vi.waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith("WebSocket connected");
      });
      expect(wsManager["socket"]).toBeDefined();
      expect(wsManager["socket"]?.url).not.toContain("token=");

      consoleSpy.mockRestore();
    });

    it("recibir y parsear mensaje de ws", async () => {
      const consoleSpy = vi.spyOn(console, "log").mockImplementation(() => {});

      wsManager = new WebSocketManager("test-token");

      await vi.waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith("WebSocket connected");
      });

      const mockData = {
        action: "create",
        model: "game",
        data: { id: 1, name: "Nueva Partida" },
      };

      const messageEvent = new MessageEvent("message", {
        data: JSON.stringify(mockData),
      });

       wsManager["socket"]?.onmessage?.(messageEvent);

      await vi.waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          "WebSocket message received:",
          mockData
        );
      });

      consoleSpy.mockRestore();
    });

    it("cerrar la conexión", () => {
      wsManager = new WebSocketManager("test-token");

      wsManager.close();

      expect(mockWebSocketClose).toHaveBeenCalled();
    });
  });
  describe("eventos", () => {
    beforeEach(() => {
      wsManager = new WebSocketManager("test-token");
    });
    it("callback para evento 'create'", () => {
      const mockCallback = vi.fn();
      const mockData = { id: 1, name: "Nueva Partida", max_players: 4 };
      wsManager.registerOnCreate(mockCallback, "game");
      expect(mockWebSocketAddEventListener).toHaveBeenCalledWith(
        "message",
        expect.any(Function)
      );
      // evento de websocket
      const listeners = (wsManager["socket"] as any).listeners.get("message");
      const messageEvent = new MessageEvent("message", {
        data: JSON.stringify({
          action: "create",
          model: "game",
          data: mockData,
        }),
      });
      listeners?.[0](messageEvent);
      expect(mockCallback).toHaveBeenCalledWith(mockData);
    });
    it("debería registrar callback para evento 'update'", () => {
      const mockCallback = vi.fn();
      const mockData = { id: 1, name: "Partida Actualizada", max_players: 5 };
      wsManager.registerOnUpdate(mockCallback, "game");
      expect(mockWebSocketAddEventListener).toHaveBeenCalledWith(
        "message",
        expect.any(Function)
      );
      const listeners = (wsManager["socket"] as any).listeners.get("message");
      const messageEvent = new MessageEvent("message", {
        data: JSON.stringify({
          action: "update",
          model: "game",
          data: mockData,
        }),
      });
      listeners?.[0](messageEvent);
      expect(mockCallback).toHaveBeenCalledWith(mockData);
    });
    it("debería registrar callback para evento 'delete'", () => {
      const mockCallback = vi.fn();
      const mockData = { id: 1 };
      wsManager.registerOnDelete(mockCallback, "game");
      expect(mockWebSocketAddEventListener).toHaveBeenCalledWith(
        "message",
        expect.any(Function)
      );
      const listeners = (wsManager["socket"] as any).listeners.get("message");
      const messageEvent = new MessageEvent("message", {
        data: JSON.stringify({
          action: "delete",
          model: "game",
          data: mockData,
        }),
      });
      listeners?.[0](messageEvent);
      expect(mockCallback).toHaveBeenCalledWith(mockData);
    });
    it("debería registrar callback para un action específico", () => {
      const mockCallback = vi.fn();
      const mockData = { remaining_seconds: 15 };
      wsManager.registerOnAction(mockCallback, "timer", "update_seconds");
      expect(mockWebSocketAddEventListener).toHaveBeenCalledWith(
        "message",
        expect.any(Function)
      );
      const listeners = (wsManager["socket"] as any).listeners.get("message");
      const messageEvent = new MessageEvent("message", {
        data: JSON.stringify({
          action: "update_seconds",
          model: "timer",
          data: mockData,
        }),
      });
      listeners?.[0](messageEvent);
      expect(mockCallback).toHaveBeenCalledWith(mockData);
    });
    it("no invoca el callback si el action no coincide", () => {
      const mockCallback = vi.fn();
      wsManager.registerOnAction(mockCallback, "timer", "update_seconds");
      const listeners = (wsManager["socket"] as any).listeners.get("message");
      const messageEvent = new MessageEvent("message", {
        data: JSON.stringify({
          action: "other_action",
          model: "timer",
          data: { remaining_seconds: 10 },
        }),
      });
      listeners?.[0](messageEvent);
      expect(mockCallback).not.toHaveBeenCalled();
    });
  });
});
