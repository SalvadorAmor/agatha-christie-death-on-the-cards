import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import Game_List from "./game_list";
import Game_Item from "./game_item";
import GameService from "../../services/Game";
import PlayerService from "../../services/Player";
import PlayerServiceOK from "../../services/PlayerService";

//MOCKS
vi.mock("../../services/Game", () => ({
  default: {
    getGames: vi.fn(),
  },
}));

vi.mock("../../services/Player", () => ({
  default: {
    getPlayers: vi.fn(),
  },
}));

vi.mock("../../services/PlayerService", () => ({
  default: {
    create: vi.fn(),
  },
}));

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual =
    (await vi.importActual) <
    typeof import("react-router-dom") >
    "react-router-dom";
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const mockRegisterOnCreate = vi.fn();
const mockRegisterOnDelete = vi.fn();
const mockClose = vi.fn();

vi.mock("../../services/Game", () => ({
  default: {
    getGames: vi.fn(),
  },
}));

vi.mock("../WebSocketManager.js", () => {
  return {
    default: vi.fn().mockImplementation(() => ({
      registerOnCreate: mockRegisterOnCreate,
      registerOnDelete: mockRegisterOnDelete,
      close: mockClose,
    })),
  };
});

//----------------------------------------------TESTS DE RENDER DE GAME LIST------------------------------------------------------

describe("Game_List", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
  });

  it("caso renderizar sin partidas", async () => {
    GameService.getGames.mockResolvedValueOnce([]);

    render(<Game_List />);

    expect(
      await screen.findByText(/No hay partidas disponibles/i)
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: /Crear Partida/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Unirse a Partida/i })
    ).toBeInTheDocument();
    
    // expect(screen.getByRole("button", { name: /Salir/i })).toBeInTheDocument();
    // expect(screen.getByRole("button", { name: /Salir/i })).toBeEnabled();
    // const buttonS = await screen.findByRole("button", { name: /Salir/i });
    // fireEvent.click(buttonS);
    // expect(sessionStorage.length).toBe(0);

    const buttonU = await screen.findByRole("button", {
      name: /Unirse a Partida/i,
    });

    expect(buttonU).toBeDisabled();

    const buttonC = await screen.findByRole("button", {
      name: /Crear Partida/i,
    });
    expect(buttonC).toBeEnabled();

    const buttonD = await screen.findByRole("button", {
      name: />/i,
    });
    expect(buttonD).toBeDisabled();

    const buttonI = await screen.findByRole("button", {
      name: /</i,
    });
    expect(buttonI).toBeDisabled();

    const img = screen.getByAltText(/Death on the Cards/i);
    expect(img).toBeInTheDocument();
  });
});

it("caso renderizar con partidas", async () => {
  GameService.getGames.mockResolvedValueOnce([
    {
      id: 1,
      name: "Partida de prueba",
      max_players: 4,
    },
  ]);

  render(<Game_List />);

  const partida = await screen.findByText(/Partida de prueba/i);
  expect(partida).toBeInTheDocument();

  expect(
    screen.queryByText(/No hay partidas disponibles/i)
  ).not.toBeInTheDocument();

  // expect(screen.getByRole("button", { name: /Salir/i })).toBeInTheDocument();
  // expect(screen.getByRole("button", { name: /Salir/i })).toBeEnabled();

  const buttonU = await screen.findByRole("button", {
    name: /Unirse a Partida/i,
  });

  expect(buttonU).toBeDisabled();

  const buttonC = await screen.findByRole("button", {
    name: /Crear Partida/i,
  });
  expect(buttonC).toBeEnabled();

  const buttonD = await screen.findByRole("button", {
    name: />/i,
  });
  expect(buttonD).toBeDisabled();

  const buttonI = await screen.findByRole("button", {
    name: /</i,
  });
  expect(buttonI).toBeDisabled();

  const img = screen.getByAltText(/Death on the Cards/i);
  expect(img).toBeInTheDocument();
});

//PARTIDAS "EXISTENTES" PARA PROBAR ACCIONES
const mockGames = [
  { id: 1, name: "Partida 1", max_players: 4 },
  { id: 2, name: "Partida 2", max_players: 4 },
  { id: 3, name: "Partida 3", max_players: 4 },
  { id: 4, name: "Partida 4", max_players: 4 },
  { id: 5, name: "Partida 5", max_players: 4 },
];

const mockPlayers = [
    { id: 1, game_id: 1, name: "Jugador 1" },
    { id: 2, game_id: 1, name: "Jugador 2" },
    { id: 3, game_id: 2, name: "Jugador 3" },
];

beforeEach(() => {
  GameService.getGames.mockResolvedValue(mockGames);
  PlayerService.getPlayers.mockResolvedValue(mockPlayers);
  mockNavigate.mockClear();
});

it("navegación del carrusel", async () => {
  render(<Game_List />);

  const partida1 = await screen.findByText((content) =>
    content.includes("Partida 1")
  );
  expect(partida1).toBeInTheDocument();

  const prevButton = await screen.findByText("<");
  const nextButton = await screen.findByText(">");

  expect(prevButton).toBeDisabled();
  expect(nextButton).not.toBeDisabled();

  fireEvent.click(nextButton);

  expect(prevButton).not.toBeDisabled();

  fireEvent.click(nextButton);
  fireEvent.click(nextButton);

  expect(nextButton).toBeDisabled();

  fireEvent.click(prevButton);
  expect(screen.getByText(/Partida 1/i)).toBeVisible();
  expect(screen.getByText(/Partida 2/i)).toBeVisible();
  expect(screen.getByText(/Partida 3/i)).toBeVisible();

  expect(
    screen.queryByText(/No hay partidas disponibles/i)
  ).not.toBeInTheDocument();
});

const mockPlayer = {
  id: 1,
  game_id: 2,
  name: "Salvi",
  date_of_birth: "2004-01-28T00:00:00.000Z",
  avatar: "detective1",
  token: "test",
  position: null,
};

beforeEach(() => {
  GameService.getGames.mockResolvedValue(mockGames);
  PlayerService.getPlayers.mockResolvedValue([]);
  PlayerServiceOK.create.mockResolvedValue(mockPlayer);
  mockNavigate.mockClear();
});

it("Seleccion de partidas", async () => {
  render(<Game_List />);

  const partida2 = await screen.findByText((content) =>
    content.includes("Partida 2")
  );
  fireEvent.click(partida2);

  const joinButton = screen.getByRole("button", { name: /Unirse a Partida/i });
  expect(joinButton).toBeEnabled();
});

it("carga las partidas ", async () => {
  const mockGames = [
    { id: 1, name: "Partida 1", max_players: 4 },
    { id: 2, name: "Partida 2", max_players: 4 },
  ];

  GameService.getGames.mockResolvedValueOnce(mockGames);

  render(<Game_List />);

  await waitFor(() => {
    expect(screen.getByText(/Partida 1/i)).toBeInTheDocument();
    expect(screen.getByText(/Partida 2/i)).toBeInTheDocument();
  });

  expect(GameService.getGames).toHaveBeenCalledWith({ status__eq: "waiting" });
});

it("abre y cierra el diálogo de crear partida", async () => {
  GameService.getGames.mockResolvedValueOnce(mockGames);
  
  render(<Game_List />);

  await screen.findByText(/Partida 1/i);

  const createButton = screen.getByRole("button", { name: /Crear Partida/i });
  fireEvent.click(createButton);

  const cancelButton = screen.getByRole("button", { name: /Cancelar/i });
  fireEvent.click(cancelButton);

  await waitFor(() => {
    expect(screen.queryByRole("button", { name: /Cancelar/i })).not.toBeInTheDocument();
  });
});

it("Crear y Unirse a Partida cambia estado de join", async () => {
  render(
    <Game_List
      prePlayerData={{
        name: "test",
        birthdate: Date.now().toString(),
        avatar: "detective2",
      }}
    />
  );

  const createButton = screen.getByRole("button", { name: /Crear Partida/i });
  fireEvent.click(createButton);

  const gameItem = await screen.findByText(/Partida 1/i);
  fireEvent.click(gameItem);

  const joinButton = screen.getByRole("button", { name: /Unirse a Partida/i });
  expect(joinButton).toBeEnabled();
  fireEvent.click(joinButton);
});

it("Unirse a partida e ir al lobby", async () => {
  sessionStorage.clear();
  localStorage.clear();
  PlayerServiceOK.create.mockResolvedValue(mockPlayer);

  render(
    <Game_List
      prePlayerData={{
        name: "test",
        birthdate: Date.now().toString(),
        avatar: "detective2",
      }}
    />
  );

  const gameItem = await screen.findByText(/Partida 2/i);
  fireEvent.click(gameItem);

  const joinButton = screen.getByRole("button", { name: /Unirse a Partida/i });
  expect(joinButton).toBeEnabled();
  fireEvent.click(joinButton);

  await waitFor(() => {
    const saved = localStorage.getItem("player");
    expect(saved).not.toBeNull();
    expect(localStorage.getItem("player")).toContain('"game_id":2');
    expect(mockNavigate).toHaveBeenCalledWith("/lobby/2");
  });
});

it("Unirse erroneamente a partida", async () => {
  sessionStorage.clear();
  localStorage.clear();
  sessionStorage.setItem("user.name", "Salvi");
  sessionStorage.setItem("user.birthdate", "2004-01-28T00:00:00.000Z");
  sessionStorage.setItem("user.avatar", "detective1");
  PlayerServiceOK.create.mockResolvedValue(null);
  render(
    <Game_List
      prePlayerData={{
        name: "test",
        birthdate: Date.now().toString(),
        avatar: "detective2",
      }}
    />
  );

  const gameItem = await screen.findByText(/Partida 2/i);
  fireEvent.click(gameItem);

  const joinButton = screen.getByRole("button", { name: /Unirse a Partida/i });
  expect(joinButton).toBeEnabled();
  fireEvent.click(joinButton);

  await waitFor(() => {
    const saved = localStorage.getItem("player");
    expect(saved).toBeNull();
  });
});

//------------------------------------------ TESTS DE WEBSOCKETS CON LAS PARTIDAS----------------------------------------------

describe("Game_List - WebSocketManager", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("recibe evento 'create'", async () => {
    let onCreateCallback;
    mockRegisterOnCreate.mockImplementationOnce((cb) => (onCreateCallback = cb));
    mockRegisterOnCreate.mockImplementationOnce(() => {});
    GameService.getGames.mockResolvedValueOnce([]);

    render(<Game_List />);

    const newGame = { id: 1, name: "Nueva partida", max_players: 5 };
    await waitFor(() => {
      expect(GameService.getGames).toHaveBeenCalled();
    });

    onCreateCallback(newGame);

    await waitFor(() => {
      expect(screen.getByText(/Nueva partida/i)).toBeInTheDocument();
    });
  });

it("recibe evento 'delete'", async () => {
  let onDeleteCallback;
  mockRegisterOnDelete.mockImplementation((cb) => (onDeleteCallback = cb));

  const mockGames = [
    { id: 1, name: "Partida 1", max_players: 4 },
    { id: 2, name: "Partida 2", max_players: 4 },
  ];

  GameService.getGames.mockResolvedValueOnce(mockGames);
  render(<Game_List />);

  await screen.findByText(/Partida 1/i);
  
  const partida1 = screen.getByText(/Partida 1/i);
  fireEvent.click(partida1);

  const joinButton = screen.getByRole("button", { name: /Unirse a Partida/i });
  await waitFor(() => {
    expect(joinButton).toBeEnabled();
  });

  onDeleteCallback({ id: 1 });

  await waitFor(() => {
    expect(screen.queryByText(/Partida 1/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Partida 2/i)).toBeInTheDocument();
    expect(screen.queryByText(/No hay partidas disponibles/i)).not.toBeInTheDocument();
    expect(joinButton).toBeDisabled();
  });

  onDeleteCallback({ id: 2 });

  await waitFor(() => {
    expect(screen.queryByText(/Partida 1/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Partida 2/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/No hay partidas disponibles/i)).toBeInTheDocument();
    expect(joinButton).toBeDisabled();
  });
});

it("elimina partida NO seleccionada sin afectar la selección de otra partida", async () => {
  let onDeleteCallback;
  mockRegisterOnDelete.mockImplementation((cb) => (onDeleteCallback = cb));

  const mockGames = [
    { id: 1, name: "Partida 1", max_players: 4 },
    { id: 2, name: "Partida 2", max_players: 4 },
    { id: 3, name: "Partida 3", max_players: 4 },
  ];

  GameService.getGames.mockResolvedValueOnce(mockGames);
  render(<Game_List />);

  await screen.findByText(/Partida 1/i);
  
  
  const partida1 = screen.getByText(/Partida 1/i);
  fireEvent.click(partida1);

  const joinButton = screen.getByRole("button", { name: /Unirse a Partida/i });
  await waitFor(() => {
    expect(joinButton).toBeEnabled();
  });

  onDeleteCallback({ id: 2 });

  await waitFor(() => {
    expect(screen.queryByText(/Partida 2/i)).not.toBeInTheDocument();
    expect(screen.getByText(/Partida 1/i)).toBeInTheDocument();
    expect(joinButton).toBeEnabled();
  });
});
});

