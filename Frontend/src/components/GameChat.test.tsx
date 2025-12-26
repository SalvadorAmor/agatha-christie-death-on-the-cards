import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import GameChat from "./GameChat";
import ChatService from "../services/ChatService";

vi.mock("../services/ChatService", () => ({
  default: {
    create: vi.fn(),
  },
}));

const mockMessages = [
  {
    id: 1,
    game_id: 1,
    owner_name: "Player1",
    content: "Hola a todos",
    timestamp: "2023-01-01T00:00:00Z",
  },
  {
    id: 2,
    game_id: 1,
    owner_name: null,
    content: "Evento: Carta jugada",
    timestamp: "2023-01-01T00:01:00Z",
  },
];

describe("GameChat", () => {
  const mockOnClose = vi.fn();
  const mockCreate = vi.mocked(ChatService.create);

  beforeEach(() => {
    vi.clearAllMocks();
    Element.prototype.scrollIntoView = vi.fn();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renderiza el panel del chat con mensajes e input", () => {
    render(
      <GameChat
        messages={mockMessages}
        onClose={mockOnClose}
        myPlayerId={123}
        gameId={1}
      />
    );

    expect(screen.getByText("Chat & Eventos")).toBeInTheDocument();
    expect(screen.getByText("Cerrar ✕")).toBeInTheDocument();

    expect(screen.getByText("Hola a todos")).toBeInTheDocument();
    expect(screen.getByText("Evento: Carta jugada")).toBeInTheDocument();

    expect(screen.getByPlaceholderText("Escribí un mensaje...")).toBeInTheDocument();
    expect(screen.getByText("Enviar")).toBeInTheDocument();
  });

  it("diferencia visualmente mensajes de jugador y eventos", () => {
    render(
      <GameChat
        messages={mockMessages}
        onClose={mockOnClose}
        myPlayerId={123}
        gameId={1}
      />
    );

    const playerMsg = screen.getByText("Hola a todos").closest("div");
    const eventMsg = screen.getByText("Evento: Carta jugada").closest("div");

    expect(playerMsg?.className).toMatch(/text-white/);
    expect(eventMsg?.className).toMatch(/text-\[#bb8512\]/);
  });

  it("llama a onClose al hacer click en ✕", () => {
    render(
      <GameChat
        messages={mockMessages}
        onClose={mockOnClose}
        myPlayerId={123}
        gameId={1}
      />
    );

    fireEvent.click(screen.getByText("Cerrar ✕"));
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("envía mensaje al hacer click en Enviar", async () => {
    mockCreate.mockResolvedValueOnce({
      id: 3,
      game_id: 1,
      owner_name: "Player123",
      content: "Nuevo mensaje",
      timestamp: "2023-01-01T00:02:00Z",
    });

    render(
      <GameChat
        messages={mockMessages}
        onClose={mockOnClose}
        myPlayerId={123}
        gameId={1}
      />
    );

    const input = screen.getByPlaceholderText("Escribí un mensaje...");
    const sendButton = screen.getByText("Enviar");

    fireEvent.change(input, { target: { value: "Nuevo mensaje" } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalledWith({
        game_id: 1,
        owner_id: 123,
        content: "Nuevo mensaje",
      });
    });

    expect(input).toHaveValue("");
  });

  it("envía mensaje al presionar Enter", async () => {
    mockCreate.mockResolvedValueOnce({
      id: 4,
      game_id: 1,
      owner_name: "Player123",
      content: "Mensaje con Enter",
      timestamp: "2023-01-01T00:03:00Z",
    });

    render(
      <GameChat
        messages={mockMessages}
        onClose={mockOnClose}
        myPlayerId={123}
        gameId={1}
      />
    );

    const input = screen.getByPlaceholderText("Escribí un mensaje...");
    fireEvent.change(input, { target: { value: "Mensaje con Enter" } });
    fireEvent.keyDown(input, { key: "Enter" });

    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalledWith({
        game_id: 1,
        owner_id: 123,
        content: "Mensaje con Enter",
      });
    });
  });

  it("no envía mensaje vacío", async () => {
    render(
      <GameChat
        messages={mockMessages}
        onClose={mockOnClose}
        myPlayerId={123}
        gameId={1}
      />
    );

    const sendButton = screen.getByText("Enviar");
    fireEvent.click(sendButton);

    expect(mockCreate).not.toHaveBeenCalled();
  });

  it("maneja error al enviar mensaje", async () => {
    mockCreate.mockRejectedValueOnce(new Error("Network error"));
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <GameChat
        messages={mockMessages}
        onClose={mockOnClose}
        myPlayerId={123}
        gameId={1}
      />
    );

    const input = screen.getByPlaceholderText("Escribí un mensaje...");
    const sendButton = screen.getByText("Enviar");

    fireEvent.change(input, { target: { value: "Mensaje fallido" } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(errorSpy).toHaveBeenCalledWith("Error enviando mensaje:", expect.any(Error));
    });

    errorSpy.mockRestore();
  });
});
