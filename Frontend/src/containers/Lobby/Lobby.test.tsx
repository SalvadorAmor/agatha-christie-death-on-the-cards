import {
  render,
  screen,
  cleanup,
  waitFor,
  fireEvent,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import Lobby from "./Lobby";

const mockRegisterOnUpdate = vi.fn();
const mockRegisterOnCreate = vi.fn();
const mockRegisterOnDelete = vi.fn();
const mockClose = vi.fn();
const mockNavigate = vi.fn();

vi.mock("../../components/WebSocketManager.tsx", () => {
  return {
    default: vi.fn().mockImplementation(() => ({
      registerOnUpdate: mockRegisterOnUpdate,
      registerOnCreate: mockRegisterOnCreate,
      registerOnDelete: mockRegisterOnDelete,
      close: mockClose,
    })),
  };
});

vi.mock("../../services/GameService.ts", () => ({
  default: {
    read: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock("../../services/PlayerService.ts", () => ({
  default: {
    search: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock("react-router", async () => {
  const actual = await vi.importActual("react-router");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ gameId: "123" }),
  };
});

global.alert = vi.fn();

import GameService from "../../services/GameService.ts";
import PlayerService from "../../services/PlayerService.ts";

const mockPlayer = {
  id: 1,
  name: "Linus",
  token: "abc123",
  avatar: "detective1",
};

const mockGame = {
  id: 123,
  name: "Partida de prueba",
  owner: 1,
  max_players: 4,
  min_players: 2, 
  status: "waiting",
};

const mockPlayers = [
  {
    id: 1,
    name: "Linus",
    avatar: "detective1",
  },
  {
    id: 2,
    name: "Ada",
    avatar: "detective2",
  },
];

describe("Lobby", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.stubGlobal("localStorage", {
      getItem: vi.fn(() => JSON.stringify(mockPlayer)),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    });

    GameService.read.mockResolvedValue(mockGame);
    PlayerService.search.mockResolvedValue(mockPlayers);
  });

  afterEach(() => {
    cleanup();
  });

  it("Renderiza el lobby con jugadores y título", async () => {
    render(
      <MemoryRouter initialEntries={["/lobby/123"]}>
        <Lobby />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Partida de prueba #123")).toBeInTheDocument();
    });

    expect(screen.getByText("Linus")).toBeInTheDocument();
    expect(screen.getByText("Ada")).toBeInTheDocument();
    expect(screen.getByText("2/4 Jugadores")).toBeInTheDocument();
  });

  it("Renderiza botón Comenzar si el jugador es dueño", async () => {
    render(
      <MemoryRouter initialEntries={["/lobby/123"]}>
        <Lobby />
      </MemoryRouter>
    );

    const btn = await screen.findByRole("button", { name: "Comenzar" });
    expect(btn).toHaveClass("bg-white");
  });

  it("No muestra botón blanco si jugador no es dueño", async () => {
    const notOwnerPlayer = { ...mockPlayer, id: 999 };
    (localStorage.getItem as any).mockReturnValue(
      JSON.stringify(notOwnerPlayer)
    );

    render(
      <MemoryRouter initialEntries={["/lobby/123"]}>
        <Lobby />
      </MemoryRouter>
    );

    const btn = await screen.findByRole("button", { name: "Comenzar" });
    expect(btn).not.toHaveClass("bg-white");
  });

  it("Llama a GameService.update al hacer click en 'Comenzar'", async () => {
    GameService.update.mockResolvedValue({ ...mockGame, status: "started" });

    render(
      <MemoryRouter initialEntries={["/lobby/123"]}>
        <Lobby />
      </MemoryRouter>
    );

    const btn = await screen.findByRole("button", { name: "Comenzar" });
    fireEvent.click(btn);

    await waitFor(() => {
      expect(GameService.update).toHaveBeenCalledWith(123, {
        token: "abc123",
        status: "started",
      });
    });
  });

  it("muestra 'Error cargando la partida.'", async () => {
    (GameService.read as any).mockRejectedValue(
      new Error("error al cargar partidas")
    );
    const consoleErrorSpy = vi
      .spyOn(console, "error")
      .mockImplementation(() => {});

    render(
      <MemoryRouter>
        <Lobby />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Error cargando partida.",
        expect.any(Error)
      );

      consoleErrorSpy.mockRestore();
    });
  });

  it("muestra 'Error cargando jugadores.'", async () => {
    (PlayerService.search as any).mockRejectedValue(
      new Error("error al cargar jugadores")
    );
    const consoleErrorSpy = vi
      .spyOn(console, "error")
      .mockImplementation(() => {});

    render(
      <MemoryRouter>
        <Lobby />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Error cargando jugadores.",
        expect.any(Error)
      );

      consoleErrorSpy.mockRestore();
    });
  });

  //NO LO DESCOMENTO PORQUE NO ESTÁ IMPLEMENTADO
  it("elimina al jugador no owner que abandonó la partida", async () => {
    const notOwnerPlayer = { ...mockPlayer, id: 999 };
    (localStorage.getItem as any).mockReturnValue(
      JSON.stringify(notOwnerPlayer)
    );

    PlayerService.delete.mockResolvedValueOnce({});

    render(
      <MemoryRouter initialEntries={["/lobby/123"]}>
        <Lobby />
      </MemoryRouter>
    );

    const leaveBtn = await screen.findByRole("button", { name: /Abandonar/i });
    fireEvent.click(leaveBtn);

    await waitFor(() => {
      expect(PlayerService.delete).toHaveBeenCalledWith(999, {
        token: "abc123",
      });
      expect(mockNavigate).toHaveBeenCalledWith(`/`);
    });
  });

  it("muestra un alerta cuando un jugador no owner no puede abandonar la partida", async () => {
    const notOwnerPlayer = { ...mockPlayer, id: 999 };
    (localStorage.getItem as any).mockReturnValue(
      JSON.stringify(notOwnerPlayer)
    );
    PlayerService.delete.mockResolvedValueOnce(null);

    render(
      <MemoryRouter initialEntries={["/lobby/123"]}>
        <Lobby />
      </MemoryRouter>
    );

    const leaveBtn = await screen.findByRole("button", { name: /Abandonar/i });
    fireEvent.click(leaveBtn);

    await waitFor(() => {
      expect(PlayerService.delete).toHaveBeenCalledWith(999, {
        token: "abc123",
      });
      expect(global.alert).toHaveBeenCalledWith(
        "Ha ocurrido un error al salir de la partida"
      );
    });
  });

  it("el dueño elimina la partida y navega al inicio", async () => {
    GameService.delete.mockResolvedValueOnce({});

    render(
      <MemoryRouter initialEntries={["/lobby/123"]}>
        <Lobby />
      </MemoryRouter>
    );

    const leaveBtn = await screen.findByRole("button", { name: /Abandonar/i });
    fireEvent.click(leaveBtn);

    await waitFor(() => {
      expect(GameService.delete).toHaveBeenCalledWith(123, {
        token: "abc123",
      });
      expect(mockNavigate).toHaveBeenCalledWith(`/`);
    });
    expect(PlayerService.delete).not.toHaveBeenCalled();
  });

  it("muestra un alerta cuando GameService.delete devuelve null", async () => {
    GameService.delete.mockResolvedValueOnce(null);

    render(
      <MemoryRouter initialEntries={["/lobby/123"]}>
        <Lobby />
      </MemoryRouter>
    );

    const leaveBtn = await screen.findByRole("button", { name: /Abandonar/i });
    fireEvent.click(leaveBtn);

    await waitFor(() => {
      expect(GameService.delete).toHaveBeenCalledWith(123, {
        token: "abc123",
      });
      expect(global.alert).toHaveBeenCalledWith(
        "Ha ocurrido un error al salir de la partida"
      );
    });
  });

  it("Muestra 'Cargando...' mientras no se tiene el game o player", () => {
    (localStorage.getItem as any).mockReturnValue(null);

    render(
      <MemoryRouter initialEntries={["/lobby/123"]}>
        <Lobby />
      </MemoryRouter>
    );

    expect(screen.getByText("Cargando...")).toBeInTheDocument();
  });

  it("Muestra una alerta si gameservice update devuelve null ", async () => {
    GameService.update.mockResolvedValue(null);

    render(
      <MemoryRouter initialEntries={["/lobby/123"]}>
        <Lobby />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Partida de prueba #123")).toBeInTheDocument();
    });
    const btn = await screen.findByRole("button", { name: "Comenzar" });
    fireEvent.click(btn);
    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        "Ha ocurrido un error al iniciar la partida"
      );
    });
  });
});

it("usa AVATARS[0] cuando el avatar del jugador no se encuentra", async () => {
  const playersWithInvalidAvatar = [
    {
      id: 1,
      name: "Linus",
      avatar: "avatar-invalido",
    },
  ];

  PlayerService.search.mockResolvedValue(playersWithInvalidAvatar);

  render(
    <MemoryRouter initialEntries={["/lobby/123"]}>
      <Lobby />
    </MemoryRouter>
  );

  await waitFor(() => {
    expect(screen.getByText("Partida de prueba #123")).toBeInTheDocument();
    expect(screen.getByText("Linus")).toBeInTheDocument();
  });
});
