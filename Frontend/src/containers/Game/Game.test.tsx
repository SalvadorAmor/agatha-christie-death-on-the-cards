/* eslint-disable @typescript-eslint/no-explicit-any */
import { render, screen, waitFor, fireEvent, renderHook } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import Game from "./Game";
import { act } from '@testing-library/react';
import { GameStatus } from "./Game";
import { useState } from "react";
import WebSocketManager from "../../components/WebSocketManager";
import EventTableService from "../../services/EventTableService";

const mockGame = {
  id: 1,
  name: "Partida Test",
  status: "WAITING",
  current_turn: 0,
  min_players: 2,
  max_players: 6,
  owner: 1,
};

const mockMe = {
  id: 1,
  name: "Yo",
  avatar: "detective1",
  position: 0,
  board_position: 0,
};

vi.mock("../../components/WebSocketManager", () => ({
  default: vi.fn(() => ({
    registerOnUpdate: vi.fn(),
    registerOnCreate: vi.fn(),
    registerOnAction: vi.fn(),
    close: vi.fn(),
  })),
}));

const mockPlayers = [
  { id: 1, name: "Yo", avatar: "detective1", position: 0, board_position: 0 },
  {
    id: 101,
    name: "Jugador 1",
    avatar: "detective2",
    position: 1,
    board_position: 1,
  },
  {
    id: 102,
    name: "Jugador 2",
    avatar: "detective3",
    position: 2,
    board_position: 2,
  },
  {
    id: 103,
    name: "Jugador 3",
    avatar: "detective4",
    position: 3,
    board_position: 3,
  },
];

const mockCards = [
  { id: 10, owner: 1, name: "not-so-fast", card_type: "detective" },
  { id: 11, owner: 1, name: "tommy-beresford", card_type: "detective" },
  { id: 12, owner: 1, name: "tommy-beresford", card_type: "detective" },
  { id: 13, owner: 1, name: "card-trade", card_type: "event" },
];

const mockSecrets = [
  { id: 201, owner: 101, name: "pista-1", revealed: false, type: "varios" },
  { id: 202, owner: 102, name: "pista-2", revealed: true, type: "murderer" },
  { id: 203, owner: 1, name: "mi-pista", revealed: false, type: "varios" },
];

const mockSetSearch = vi.fn();
const mockSetAction = vi.fn();

vi.mock("../../services/SetService.ts", () => ({
  default: {
    search: (...args: any[]) => mockSetSearch(...args),
    set_action: (...args: any[]) => mockSetAction(...args),
  },
}));

mockSetSearch.mockResolvedValue([]);

const mockGameRead = vi.fn();
vi.mock("../../services/GameService.ts", () => ({
  default: {
    read: (...args: any[]) => mockGameRead(...args),
  },
}));

const mockPlayerRead = vi.fn();
const mockPlayerSearch = vi.fn();
vi.mock("../../services/PlayerService", () => ({
  default: {
    read: (...args: any[]) => mockPlayerRead(...args),
    search: (...args: any[]) => mockPlayerSearch(...args),
  },
}));

const mockCardSearch = vi.fn();

const mockCardUpdate = vi.fn();
const mockCardBulkUpdate = vi.fn();

const mockCardPlayAction = vi.fn()

const renderGame = () => {
  return render(
    <MemoryRouter initialEntries={['/game/1']}>
      <Routes>
        <Route path="/game/:gid" element={<Game />} />
      </Routes>
    </MemoryRouter>
  );
};
vi.mock("../../services/CardService.ts", () => ({
  default: {
    search: (...args: any[]) => mockCardSearch(...args),
    update: (...args: any[]) => mockCardUpdate(...args),
    bulkUpdate: (...args: any[]) => mockCardBulkUpdate(...args),
    playCardWithTargets: (...args: any[]) => mockCardPlayAction(...args)
  },
}));

const mockSecretSearch = vi.fn();
vi.mock("../../services/SecretService.ts", () => ({
  default: {
    search: (...args: any[]) => mockSecretSearch(...args),
  },
}));

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<any>();
  return { ...actual, useNavigate: () => mockNavigate };
});

const mockGameUpdate = vi.fn();
vi.mock("../../services/GameService.ts", () => ({
  default: {
    read: (...args: any[]) => mockGameRead(...args),
    update: (...args: any[]) => mockGameUpdate(...args),
  },
}));

const mockEventTableSearch = vi.fn();

vi.mock("../../services/EventTableService.ts", () => ({
  default: {
    searchInTable: (...args: any[]) => mockEventTableSearch(...args),
  },
}));

describe("Game component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();

    localStorage.setItem(
      "player",
      JSON.stringify({ id: 1, position: 0, game_id: 1, token: "XYZ" })
    );

    mockGameRead.mockResolvedValue(mockGame);
    mockPlayerRead.mockResolvedValue(mockMe);
    mockPlayerSearch.mockResolvedValue(mockPlayers);
    mockCardSearch.mockResolvedValue(mockCards);
    mockSecretSearch.mockResolvedValue(mockSecrets);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("muestra 'Cargando…' inicialmente", () => {
    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByText(/cargando/i)).toBeInTheDocument();
  });

  it("renderiza jugadores y avatares", async () => {
    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByText("Jugador 1")).toBeInTheDocument();
    expect(screen.getByText("Jugador 2")).toBeInTheDocument();
    expect(screen.getByText("Jugador 3")).toBeInTheDocument();

    const avatars = screen.getAllByRole("img", { name: "avatar" });
    expect(avatars.length).toBeGreaterThan(0);
  });

  it("redirecciona a '/' si no hay player en localStorage", async () => {
    localStorage.clear();

    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/");
    });
  });

  it("redirecciona a '/' si el player pertenece a otro game_id", async () => {
    localStorage.setItem(
      "player",
      JSON.stringify({ id: 1, position: 0, game_id: 999, token: "XYZ" })
    );

    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/");
    });
  });

  it("preserva el token del player en localStorage tras PlayerService.read", async () => {
    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      const stored = JSON.parse(localStorage.getItem("player") || "{}");
      expect(stored.token).toBe("XYZ");
      expect(stored.id).toBe(1);
    });
  });

  it("llama a los servicios con los filtros correctos", async () => {
    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(mockGameRead).toHaveBeenCalledWith(1);
      expect(mockPlayerRead).toHaveBeenCalledWith(1);
      expect(mockPlayerSearch).toHaveBeenCalledWith({ game_id__eq: 1 });
      expect(mockCardSearch).toHaveBeenCalledWith({
        owner__eq: 1,
        set_id__is_null: true,
      });
      expect(mockSecretSearch).toHaveBeenCalledWith({ game_id__eq: 1 });
    });
  });

  it("si GameService.read falla, permanece en 'Cargando…'", async () => {
    mockGameRead.mockResolvedValue(null);

    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/cargando/i)).toBeInTheDocument();
    });
  });

  it("Boton de pasar turno habilitado", async () => {
    mockGameRead.mockResolvedValueOnce({
      ...mockGame,
      status: "finalize_turn",
    });

    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(async () => {
      const button = await screen.findByRole("button", {
        name: /pasar turno/i,
      });
      expect(button).not.toBeDisabled();
    });
  });

  it("Boton de pasar turno deshabilitado si no es finalize_turn", async () => {
    mockGameRead.mockResolvedValueOnce({
      ...mockGame,
      status: "turn_start",
    });

    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );

    const button = await screen.findByRole("button", { name: /pasar turno/i });
    expect(button).toBeDisabled();
  });
});

describe("handlePassTurn", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();

    localStorage.setItem(
      "player",
      JSON.stringify({ id: 1, position: 0, game_id: 1, token: "XYZ" })
    );

    mockGameRead.mockResolvedValue({ ...mockGame, status: "finalize_turn" });
    mockPlayerRead.mockResolvedValue(mockMe);
    mockPlayerSearch.mockResolvedValue(mockPlayers);
    mockCardSearch
      .mockResolvedValueOnce(mockCards) 
      .mockResolvedValueOnce([]) 
      .mockResolvedValueOnce([]) 
      .mockResolvedValueOnce([{ id: 999, turn_discarded: 0 }]); 

    mockSecretSearch.mockResolvedValue(mockSecrets);
  });

  it("llama GameService.update al hacer click en 'Pasar turno'", async () => {
    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );

    const button = await screen.findByRole("button", { name: /pasar turno/i });

    //  hay descartes entonces el boton de pasar el turno tiene q estar habilitado
    expect(button).not.toBeDisabled();

    fireEvent.click(button);

    await waitFor(() => {
      expect(mockGameUpdate).toHaveBeenCalledTimes(1);
      expect(mockGameUpdate).toHaveBeenCalledWith(1, {
        current_turn: 1, 
        token: "XYZ",
      });
    });
  });
});

describe("selectores de jugador y secreto", () => {
  const renderGame = () => {
    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );
  };

  const basePlayers = [
    { id: 1, name: "Yo", avatar: "detective1", position: 0, board_position: 0 },
    {
      id: 2,
      name: "Jugador 2",
      avatar: "detective2",
      position: 1,
      board_position: 1,
    },
  ];

  const baseSecrets = [
    {
      id: 201,
      owner: 2,
      name: "secreto-oponente",
      revealed: false,
      type: "varios",
    },
    { id: 202, owner: 1, name: "mi-secreto", revealed: false, type: "varios" },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    mockSetSearch.mockReset();
    mockSetAction.mockReset();
    mockEventTableSearch.mockReset();
    localStorage.clear();
    localStorage.setItem(
      "player",
      JSON.stringify({ id: 1, position: 0, game_id: 1, token: "XYZ" })
    );

    mockPlayerRead.mockResolvedValue({
      id: 1,
      name: "Yo",
      avatar: "detective1",
      position: 0,
      board_position: 0,
      token: "XYZ",
    });
    mockPlayerSearch.mockResolvedValue(basePlayers);
    mockCardSearch.mockImplementation(() => Promise.resolve([]));
    mockSetSearch.mockResolvedValue([]);
     mockEventTableSearch.mockResolvedValue([]);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("selecciona y deselecciona un jugador objetivo", async () => {
    mockGameRead.mockResolvedValue({
      ...mockGame,
      status: "waiting_for_choose_player",
      player_in_action: 1,
      current_turn: 0,
    });
    mockSecretSearch.mockResolvedValue([]);

    renderGame();

    await screen.findByText(/jugador objetivo/i);

    const actionButton = await screen.findByRole("button", {
      name: /realizar acción/i,
    });
    expect(actionButton).toBeDisabled();

    const avatars = await screen.findAllByRole("img", { name: "avatar" });
    const targetAvatar =
      avatars.find((img) => img.className.includes("border-gray-300")) ??
      avatars[avatars.length - 1];

    fireEvent.click(targetAvatar);

    await waitFor(() => {
      expect(targetAvatar.parentElement.classList.contains("shadow-xl")).toBe(true);
    });
    await waitFor(() => {
      expect(actionButton).not.toBeDisabled();
    });

    fireEvent.click(targetAvatar);

    await waitFor(() => {
      expect(targetAvatar.classList.contains("shadow-xl")).toBe(false);
    });
    await waitFor(() => {
      expect(actionButton).toBeDisabled();
    });
  });

  it("permite seleccionar secretos propios", async () => {
    mockGameRead.mockResolvedValue({
      ...mockGame,
      status: "waiting_for_choose_secret",
      player_in_action: 1,
      current_turn: 1,
    });
    mockSecretSearch.mockResolvedValue([
      {
        id: 301,
        owner: 2,
        name: "secreto-revelado",
        revealed: true,
        type: "varios",
      },
      {
        id: 302,
        owner: 1,
        name: "mi-secreto",
        revealed: false,
        type: "varios",
      },
    ]);
    mockSetSearch.mockResolvedValue([
      {
        id: 500,
        detectives: [{ id: 1, name: "hercule-poirot" }],
      },
    ]);

    renderGame();

    await screen.findByText(/secreto propio objetivo/i);

    const actionButton = await screen.findByRole("button", {
      name: /realizar acción/i,
    });
    expect(actionButton).toBeDisabled();

    const revealedSecret = await screen.findByAltText("mi-secreto");

    fireEvent.click(revealedSecret);

    await waitFor(() => {
      expect(revealedSecret.parentElement?.className).toContain("md:w-22");
    });
    await waitFor(() => {
      expect(actionButton).not.toBeDisabled();
    });

    fireEvent.click(revealedSecret);

    await waitFor(() => {
      expect(revealedSecret.parentElement?.className).toContain("md:w-20");
    });
    await waitFor(() => {
      expect(actionButton).toBeDisabled();
    });
  });

  it("permite seleccionar secretos ajenos", async () => {
    mockGameRead.mockResolvedValue({
      ...mockGame,
      status: "waiting_for_choose_secret",
      player_in_action: 1,
      current_turn: 0,
    });
    mockSecretSearch.mockResolvedValue([
      {
        id: 301,
        owner: 2,
        name: "secreto-oculto",
        revealed: false,
        type: "varios",
      },
      { id: 302, owner: 1, name: "mi-secreto", revealed: true, type: "varios" },
    ]);
    mockSetSearch.mockResolvedValue([
      {
        id: 500,
        detectives: [{ id: 1, name: "hercule-poirot" }],
      },
    ]);

    renderGame();

    await screen.findByText(/secreto ajeno objetivo/i);

    const actionButton = await screen.findByRole("button", {
      name: /realizar acción/i,
    });
    expect(actionButton).toBeDisabled();

    const revealedSecret = await screen.findByAltText("secret");

    fireEvent.click(revealedSecret);

    await waitFor(() => {
      expect(revealedSecret.parentElement?.className).toContain("md:w-12");
    });
    await waitFor(() => {
      expect(actionButton).not.toBeDisabled();
    });

    fireEvent.click(revealedSecret);

    await waitFor(() => {
      expect(revealedSecret.parentElement?.className).toContain("md:w-10");
    });
    await waitFor(() => {
      expect(actionButton).toBeDisabled();
    });
  });

  it("permite seleccionar secretos revelados cuando aplica Parker Pyne", async () => {
    mockGameRead.mockResolvedValue({
      ...mockGame,
      status: "waiting_for_choose_secret",
      player_in_action: 1,
      current_turn: 0,
    });
    mockSecretSearch.mockResolvedValue([
      {
        id: 301,
        owner: 2,
        name: "secreto-revelado",
        revealed: true,
        type: "varios",
      },
      {
        id: 302,
        owner: 1,
        name: "mi-secreto",
        revealed: false,
        type: "varios",
      },
    ]);
    mockSetSearch.mockResolvedValue([
      {
        id: 500,
        detectives: [{ id: 1, name: "parker-pyne" }],
      },
    ]);

    renderGame();

    await screen.findByText(/secreto revelado objetivo/i);

    const actionButton = await screen.findByRole("button", {
      name: /realizar acción/i,
    });
    expect(actionButton).toBeDisabled();

    const revealedSecret = await screen.findByAltText("secreto-revelado");
    fireEvent.click(revealedSecret);

    await waitFor(() => {
      expect(revealedSecret.parentElement?.className).toContain("md:w-12");
    });
    await waitFor(() => {
      expect(actionButton).not.toBeDisabled();
    });

    fireEvent.click(revealedSecret);

    await waitFor(() => {
      expect(revealedSecret.parentElement?.className).toContain("md:w-10");
    });
    await waitFor(() => {
      expect(actionButton).toBeDisabled();
    });
  });
    it("permite seleccionar secreto propio cuando hay carta jugada en el turno actual", async () => {
    mockGameRead.mockResolvedValue({
      ...mockGame,
      status: "waiting_for_choose_secret",
      player_in_action: 1,
      current_turn: 0,
    });
    
    mockSecretSearch.mockResolvedValue([
      {
        id: 301,
        owner: 2,
        name: "secreto-oponente",
        revealed: false,
        type: "varios",
      },
      {
        id: 302,
        owner: 1,
        name: "mi-secreto",
        revealed: false,
        type: "varios",
      },
    ]);

    mockCardSearch.mockImplementation((params) => {
      if (params.game_id__eq && params.turn_played__eq !== undefined) {
        return Promise.resolve([
          { id: 999, name: "carta-evento", turn_played: 0, owner: 1 }
        ]);
      }
      return Promise.resolve([]); 
    });//mock para q devuelva la carta

    mockSetSearch.mockResolvedValue([]);

    renderGame();

    await screen.findByText(/secreto propio objetivo/i);

    const actionButton = await screen.findByRole("button", {
      name: /realizar acción/i,
    });
    expect(actionButton).toBeDisabled();

    const ownSecret = await screen.findByAltText("mi-secreto");
    fireEvent.click(ownSecret);

    await waitFor(() => {
      expect(ownSecret.parentElement?.className).toContain("md:w-22");
    });
    await waitFor(() => {
      expect(actionButton).not.toBeDisabled();
    });
  });
  it("muestra carta a tradear cuando el estado es SELECT CARD TO TRADE", async () => {
  mockGameRead.mockResolvedValue({
    ...mockGame,
    status: "select_card_to_trade",
    player_in_action: 1,
    current_turn: 0,
  });
  mockSecretSearch.mockResolvedValue(baseSecrets);

  renderGame();

  await screen.findByText(/carta a tradear/i);
});
it("activa selectedtotrade", async () => {
  mockGameRead.mockResolvedValue({
    ...mockGame,
    status: "select_card_to_trade",
    player_in_action: 1,
    current_turn: 0,
  });
  
  mockSecretSearch.mockResolvedValue(baseSecrets);


  const mockHandCards = [
    { id: 10, owner: 1, name: "carta-1", card_type: "detective", set_id: null },
    { id: 11, owner: 1, name: "carta-2", card_type: "detective", set_id: null },
  ];

  mockCardSearch.mockImplementation((params) => {
    if (params.game_id__eq && params.turn_played__eq !== undefined) {
      return Promise.resolve([
        { id: 999, name: "dead-card-folly", turn_played: 0, owner: 1 }
      ]);
    }
    if (params.owner__eq === 1 && params.set_id__is_null === true) {
      return Promise.resolve(mockHandCards);
    }
    if (params.turn_discarded__is_null === true && params.owner__is_null === true) {
      return Promise.resolve([]);
    }
    if (params.turn_discarded__is_null === false) {
      return Promise.resolve([]);
    }
    return Promise.resolve([]);
  });

  mockEventTableSearch.mockResolvedValue([]);

  renderGame();

  await screen.findByText(/carta a tradear/i);

  
  await waitFor(() => {
    expect(screen.getAllByTestId("hand-card").length).toBe(2);
  });

  // Seleccionar una carta pq sino no se habilita. Si o si tienen q cumplirse las dos condiciones
  const handCards = screen.getAllByTestId("hand-card");
  fireEvent.click(handCards[0]);

  const actionButton = screen.getByRole("button", {
    name: /realizar acción/i,
  });
  
  await waitFor(() => {
    expect(actionButton).not.toBeDisabled();
  });
});

it("setea alreadyvoted=true cuando el jugador ya votó en deadcardfolly", async () => {
  mockGameRead.mockResolvedValue({
    ...mockGame,
    status: "select_card_to_trade",
    player_in_action: 1,
    current_turn: 0,
  });
  mockSecretSearch.mockResolvedValue(baseSecrets);

  mockCardSearch.mockImplementation((params) => {
    if (params.game_id__eq && params.turn_played__eq !== undefined) {
      return Promise.resolve([
        { id: 999, name: "dead-card-folly", turn_played: 0, owner: 1 }
      ]);
    }
    return Promise.resolve([]);
  });

  mockEventTableSearch.mockResolvedValue([
    { player_id: 1, action: "dead_card_folly_trade", turn_played: 0 }
  ]);

  renderGame();

  await screen.findByText(/carta a tradear/i);

  await waitFor(() => {
    expect(mockEventTableSearch).toHaveBeenCalledWith({
      game_id__eq: 1,
      action__eq: "dead_card_folly_trade",
      turn_played__eq: 0,
    });
  });

   const actionButton = screen.getByRole("button", {
    name: /realizar acción/i,
  });
  
  await waitFor(() => {
    expect(actionButton).toBeDisabled();
  });
});

it("setea alreadyvoted=false cuando todos los jugadores ya votaron en deadcardfolly", async () => {
  mockGameRead.mockResolvedValue({
    ...mockGame,
    status: "select_card_to_trade",
    player_in_action: 1,
    current_turn: 0,
  });
  mockSecretSearch.mockResolvedValue(baseSecrets);

  mockCardSearch.mockImplementation((params) => {
    if (params.game_id__eq && params.turn_played__eq !== undefined) {
      return Promise.resolve([
        { id: 999, name: "dead-card-folly", turn_played: 0, owner: 1 }
      ]);
    }
    return Promise.resolve([]);
  });

  mockEventTableSearch.mockResolvedValue([
    { player_id: 1, action: "dead_card_folly_trade", turn_played: 0 },
    { player_id: 2, action: "dead_card_folly_trade", turn_played: 0 }
  ]);

  renderGame();

  await screen.findByText(/carta a tradear/i);

  await waitFor(() => {
    expect(mockEventTableSearch).toHaveBeenCalledWith({
      game_id__eq: 1,
      action__eq: "dead_card_folly_trade",
      turn_played__eq: 0,
    });
  });

  await waitFor(() => {
    expect(screen.getByText(/carta a tradear/i)).toBeInTheDocument();
  });
});

});

describe("cardtrade", () => {
  const renderGame = () => {
    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );
  };

  const basePlayers = [
    { id: 1, name: "Yo", avatar: "detective1", position: 0, board_position: 0 },
    { id: 2, name: "Jugador 2", avatar: "detective2", position: 1, board_position: 1 },
    { id: 3, name: "Jugador 3", avatar: "detective3", position: 2, board_position: 2 },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    mockEventTableSearch.mockReset();
    localStorage.clear();
    localStorage.setItem(
      "player",
      JSON.stringify({ id: 1, position: 0, game_id: 1, token: "XYZ" })
    );

    mockPlayerRead.mockResolvedValue({
      id: 1,
      name: "Yo",
      avatar: "detective1",
      position: 0,
      board_position: 0,
      token: "XYZ",
    });
    mockPlayerSearch.mockResolvedValue(basePlayers);
    mockSecretSearch.mockResolvedValue([]);
    mockSetSearch.mockResolvedValue([]);
    mockGameRead.mockResolvedValue({
      ...mockGame,
      status: "in_progress",
      current_turn: 5,
    });
  });

  it("alreadyVoted true cuando < 3 votos, length != 1", async () => {
    mockCardSearch.mockImplementation((params) => {
      if (params.turn_played__eq !== undefined) {
        return Promise.resolve([{ id: 100, name: "card-trade", turn_played: 5 }]);
      }
      return Promise.resolve([]);
    });

    mockEventTableSearch.mockResolvedValue([
      { id: 1, player_id: 1, action: "card_trade", turn_played: 5 },
      { id: 2, player_id: 2, action: "card_trade", turn_played: 5 },
    ]);

    renderGame();

    await waitFor(() => {
      expect(mockEventTableSearch).toHaveBeenCalledWith({
        game_id__eq: 1,
        action__eq: "card_trade",
        turn_played__eq: 5,
      });
    });
  });

  it("marca alreadyVoted false >= 3 votos", async () => {
    mockCardSearch.mockImplementation((params) => {
      if (params.turn_played__eq !== undefined) {
        return Promise.resolve([{ id: 100, name: "card-trade", turn_played: 5 }]);
      }
      return Promise.resolve([]);
    });

    mockEventTableSearch.mockResolvedValue([
      { id: 1, player_id: 1, action: "card_trade", turn_played: 5 },
      { id: 2, player_id: 2, action: "card_trade", turn_played: 5 },
      { id: 3, player_id: 3, action: "card_trade", turn_played: 5 },
    ]);

    renderGame();

    await waitFor(() => {
      expect(mockEventTableSearch).toHaveBeenCalled();
    });
  });

  it("selectedToTrade cuando el jugador es que cambia no selecciono la carta", async () => {
    mockCardSearch.mockImplementation((params) => {
      if (params.turn_played__eq !== undefined) {
        return Promise.resolve([{ id: 100, name: "card-trade", turn_played: 5 }]);
      }
      return Promise.resolve([]);
    });

    mockEventTableSearch.mockResolvedValue([
      { id: 1, player_id: 1, action: "card_trade", turn_played: 5, target_card: null },
    ]);

    renderGame();

    await waitFor(() => {
      expect(mockEventTableSearch).toHaveBeenCalledTimes(2); // Se llama dos veces en el useffect
    });
  });
});

describe("handlePlayAction", () => {
  const basePlayers = [
    { id: 1, name: "Yo", avatar: "detective1", position: 0, board_position: 0 },
    {
      id: 2,
      name: "Jugador 2",
      avatar: "detective2",
      position: 1,
      board_position: 1,
    },
  ];

  const baseSecrets = [
    {
      id: 201,
      owner: 2,
      name: "secreto-oponente",
      revealed: false,
      type: "varios",
    },
    { id: 202, owner: 1, name: "mi-secreto", revealed: false, type: "varios" },
  ];

  const renderGame = () => {
    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );
  };

  beforeEach(() => {
    vi.resetAllMocks();
    localStorage.clear();
    localStorage.setItem(
      "player",
      JSON.stringify({ id: 1, position: 0, game_id: 1, token: "XYZ" })
    );

    mockPlayerRead.mockResolvedValue({
      id: 1,
      name: "Yo",
      avatar: "detective1",
      position: 0,
      board_position: 0,
      token: "XYZ",
    });
    mockPlayerSearch.mockResolvedValue(basePlayers);
    mockCardSearch.mockImplementation(() => Promise.resolve([]));
    mockSecretSearch.mockResolvedValue(baseSecrets);
    mockSetSearch.mockResolvedValue([]);
    mockSetAction.mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("ejecuta set_action con target_secret y reinicia selección", async () => {
    mockGameRead.mockResolvedValue({
      ...mockGame,
      status: "waiting_for_choose_secret",
      player_in_action: 1,
      current_turn: 2,
    });
    mockSetSearch.mockImplementation((params) => {
      if ("turn_played__eq" in params) {
        return Promise.resolve([
          {
            id: 88,
            detectives: [{ id: 1, name: "hercule-poirot" }],
            turn_played: 2,
          },
        ]);
      }
      return Promise.resolve([]); 
    });

    mockSecretSearch.mockResolvedValue([
      {
        id: 301,
        owner: 2,
        name: "secreto-oculto",
        revealed: false,
        type: "varios",
      },
      { id: 302, owner: 1, name: "mi-secreto", revealed: true, type: "varios" },
    ]);

    renderGame();

    await screen.findByText(/secreto ajeno objetivo/i);

    const actionButton = await screen.findByRole("button", {
      name: /realizar acción/i,
    });
    expect(actionButton).toBeDisabled();

    const opponentSecret = await screen.findByRole("img", { name: "secret" });

    fireEvent.click(opponentSecret);

    await waitFor(() => {
      const enlarged = screen
        .getAllByAltText("secret")
        .find((secret) => secret.parentElement?.classList.contains("md:w-12"));
      expect(enlarged).toBeDefined();
    });
    await waitFor(() => {
      expect(actionButton).not.toBeDisabled();
    });

    fireEvent.click(actionButton);

    await waitFor(() => {
      expect(mockSetSearch).toHaveBeenLastCalledWith({
        turn_played__eq: 2,
        game_id__eq: 1,
      });
      expect(mockSetAction).toHaveBeenCalledWith(88, {
        target_secret: 301,
        token: "XYZ",
      });
    });

    await waitFor(() => {
      const deselected = screen.getByAltText("secret");
      expect(deselected.parentElement?.classList.contains("md:w-10")).toBe(
        true
      );
      expect(actionButton).toBeDisabled();
    });
  });

  it("ejecuta set_action con target_player y reinicia selección", async () => {
    mockGameRead.mockResolvedValue({
      ...mockGame,
      status: "waiting_for_choose_player",
      player_in_action: 1,
      current_turn: 0,
    });
    mockSecretSearch.mockResolvedValue([]);
    mockSetSearch.mockResolvedValue([
      { id: 77, detectives: [{ name: "hercule-poirot" }], turn_played: 0 },
    ]);

    renderGame();

    await screen.findByText(/jugador objetivo/i);

    const actionButton = await screen.findByRole("button", {
      name: /realizar acción/i,
    });
    expect(actionButton).toBeDisabled();

    const avatars = await screen.findAllByRole("img", { name: "avatar" });
    const targetAvatar =
      avatars.find((img) => img.className.includes("border-gray-300")) ??
      avatars[avatars.length - 1];

    fireEvent.click(targetAvatar);

    await waitFor(() => {
      expect(targetAvatar.parentElement.classList.contains("shadow-xl")).toBe(true);
    });
    await waitFor(() => {
      expect(actionButton).not.toBeDisabled();
    });

    fireEvent.click(actionButton);

    await waitFor(() => {
      expect(mockSetSearch).toHaveBeenCalledWith({
        turn_played__eq: 0,
        game_id__eq: 1,
      });
      expect(mockSetAction).toHaveBeenCalledWith(77, {
        target_player: 2,
        token: "XYZ",
      });
    });

    await waitFor(() => {
      const refreshedAvatars = screen.getAllByRole("img", { name: "avatar" });
      const refreshedTarget =
        refreshedAvatars.find((img) =>
          img.classList.contains("border-gray-300")
        ) ?? refreshedAvatars[refreshedAvatars.length - 1];
      expect(refreshedTarget.classList.contains("shadow-xl")).toBe(false);
      expect(actionButton).toBeDisabled();
    });
  });
  it("ejecuta playActionCard con target_player y reinicia selección", async () => {
    mockGameRead.mockResolvedValue({
      ...mockGame,
      status: "waiting_for_choose_player",
      player_in_action: 1,
      current_turn: 0,
    });
    mockSecretSearch.mockResolvedValue([]);
    mockCardSearch.mockResolvedValue([{ id: 77, name: "cards-off-the-table", turn_played: 0, owner: 1 }, 
      {id: 78, name: "not-so-fast", owner: 2}]);
    mockCardPlayAction.mockResolvedValue(undefined)

    renderGame();

    await screen.findByText(/jugador objetivo/i);

    const actionButton = await screen.findByRole("button", { name: /realizar acción/i });
    expect(actionButton).toBeDisabled();

    const avatars = await screen.findAllByRole("img", { name: "avatar" });
    const targetAvatar =
      avatars.find((img) => img.className.includes("border-gray-300")) ?? avatars[avatars.length - 1];

    fireEvent.click(targetAvatar);

    await waitFor(() => {
      expect(targetAvatar.parentElement.classList.contains("shadow-xl")).toBe(true);
    });
    await waitFor(() => {
      expect(actionButton).not.toBeDisabled();
    });

    fireEvent.click(actionButton);

    await waitFor(() => {
      expect(mockCardPlayAction).toHaveBeenCalledWith(77, "XYZ",{
        target_players: [2],
      });
    });

    await waitFor(() => {
      const refreshedAvatars = screen.getAllByRole("img", { name: "avatar" });
      const refreshedTarget =
        refreshedAvatars.find((img) => img.classList.contains("border-gray-300")) ??
        refreshedAvatars[refreshedAvatars.length - 1];
      expect(refreshedTarget.classList.contains("shadow-xl")).toBe(false);
      expect(actionButton).toBeDisabled();
    });
  });

  it("ejecuta playActionCard con target_player y target_secret y reinicia selección", async () => {
    mockGameRead.mockResolvedValue({
      ...mockGame,
      status: "waiting_for_choose_player_and_secret",
      player_in_action: 1,
      current_turn: 0,
    });
    mockSecretSearch.mockResolvedValue([{
        id: 301,
        owner: 2,
        name: "secreto-oculto",
        revealed: false,
        type: "varios",
      },
      { id: 302, owner: 1, name: "mi-secreto", revealed: true, type: "varios" }]);
    mockCardSearch.mockResolvedValue([{ id: 77, name: "and-then-there-was-one-more", turn_played: 0, owner: 1 }]);
    mockCardPlayAction.mockResolvedValue(undefined)

    renderGame();

    await screen.findByText(/secreto revelado y jugador objetivo/i);

    const actionButton = await screen.findByRole("button", { name: /realizar acción/i });
    expect(actionButton).toBeDisabled();

    const avatars = await screen.findAllByRole("img", { name: "avatar" });
    const targetAvatar =
      avatars.find((img) => img.className.includes("border-gray-300")) ?? avatars[avatars.length - 1];

    fireEvent.click(targetAvatar);

    await waitFor(() => {
      expect(targetAvatar.parentElement.classList.contains("shadow-xl")).toBe(true);
    });

    const revealedSecret = await screen.findByAltText("mi-secreto");

    
    fireEvent.click(revealedSecret);

    await waitFor(() => {
      expect(revealedSecret.parentElement?.className).toContain("md:w-22");
    });
    await waitFor(() => {
      expect(actionButton).not.toBeDisabled();
    });

    fireEvent.click(actionButton);

    await waitFor(() => {
      expect(mockCardPlayAction).toHaveBeenCalledWith(77, "XYZ",{
        target_players: [2],
        target_secrets: [302]
      });
    });

    await waitFor(() => {
      const refreshedAvatars = screen.getAllByRole("img", { name: "avatar" });
      const refreshedTarget =
        refreshedAvatars.find((img) => img.classList.contains("border-gray-300")) ??
        refreshedAvatars[refreshedAvatars.length - 1];
      expect(refreshedTarget.classList.contains("shadow-xl")).toBe(false);
      expect(actionButton).toBeDisabled();
    });
  });
  it("ejecuta playActionCard con target_set y reinicia selección", async () => {
    mockGameRead.mockResolvedValue({
      ...mockGame,
      status: "waiting_for_choose_set",
      player_in_action: 1,
      current_turn: 2,
    });
    mockCardSearch.mockResolvedValue([{ id: 77, name: "another-victim", turn_played: 2, owner: 1 }]);
    mockSetSearch.mockImplementation((params) => {
      if (params.owner__eq === 2) {
        return Promise.resolve([{ id: 101, owner: 2, turn_played: 1, detectives: [{ name: "poirot" }] }]);
      }
      if (params.owner__eq === 1) {
        return Promise.resolve([]);
      }
      return Promise.resolve([]);
    });
    mockCardPlayAction.mockResolvedValue(undefined)

    renderGame();

    await screen.findByText(/set objetivo a robar/i);

    const actionButton = await screen.findByRole("button", { name: /realizar acción/i });
    expect(actionButton).toBeDisabled();

    const detectives = await screen.findAllByAltText("poirot");
    const detective = detectives[0];

    fireEvent.click(detective);

    await waitFor(() => {
      expect(detective.parentElement.classList.contains("shadow-lg")).toBe(true);
    });
    await waitFor(() => {
      expect(actionButton).not.toBeDisabled();
    });

    fireEvent.click(actionButton);

    await waitFor(() => {
      expect(mockCardPlayAction).toHaveBeenCalledWith(77, "XYZ",{
        target_sets: [101]
      });
    });
  });
 
  it("ejecuta pointyoursuspicions' y setea alreadyVoted", async () => {
  mockGameRead.mockResolvedValue({
    ...mockGame,
    status: "waiting_for_choose_player",
    player_in_action: 1,
    current_turn: 0,
  });
  mockSecretSearch.mockResolvedValue([]);
  mockCardSearch.mockResolvedValue([
    { id: 77, name: "point-your-suspicions", turn_played: 0, owner: 1 }
  ]);
  mockCardPlayAction.mockResolvedValue(undefined);
  
   mockEventTableSearch.mockResolvedValue([]);

  renderGame();

  await screen.findByText(/jugador objetivo/i);

  const actionButton = await screen.findByRole("button", { 
    name: /realizar acción/i 
  });
  expect(actionButton).toBeDisabled();

  const avatars = await screen.findAllByRole("img", { name: "avatar" });
  const targetAvatar =
    avatars.find((img) => img.className.includes("border-gray-300")) ?? 
    avatars[avatars.length - 1];

  fireEvent.click(targetAvatar);

  await waitFor(() => {
    expect(targetAvatar.parentElement.classList.contains("shadow-xl")).toBe(true);
  });
  
  await waitFor(() => {
    expect(actionButton).not.toBeDisabled();
  });

  expect(screen.queryByText(/demas jugadores/i)).not.toBeInTheDocument();

  fireEvent.click(actionButton);

  await waitFor(() => {
    expect(mockCardPlayAction).toHaveBeenCalledWith(77, "XYZ", {
      target_players: [2],
    });
  });

  //se llamo a eventable
  await waitFor(() => {
    expect(mockEventTableSearch).toHaveBeenCalledWith({
      game_id__eq: 1,
      action__eq: "point_your_suspicions",
      turn_played__eq: 0
    });
  });

  await waitFor(() => {
    const refreshedAvatars = screen.getAllByRole("img", { name: "avatar" });
    const refreshedTarget =
      refreshedAvatars.find((img) => 
        img.classList.contains("border-gray-300")
      ) ?? refreshedAvatars[refreshedAvatars.length - 1];
    expect(refreshedTarget.classList.contains("shadow-xl")).toBe(false);
  });
  
});
it("ejecuta playactioncard con target secret", async () => {
  
  mockGameRead.mockResolvedValue({
    ...mockGame,
    status: "waiting_for_choose_secret",
    player_in_action: 1,
    current_turn: 2,
  });
  mockSecretSearch.mockResolvedValue([
    { id: 301, owner: 1, name: "mi-secreto", revealed: false, type: "varios" },
  ]);
  mockCardSearch.mockImplementation((params) => {
    if (params.game_id__eq && params.turn_played__eq !== undefined) {
      return Promise.resolve([
        { id: 88, name: "super-sleuth", turn_played: 2, owner: 1 }
      ]);
    }
    if (params.owner__eq === 1 && params.set_id__is_null === true) {
      return Promise.resolve([]);
    }
    return Promise.resolve([]);
  });
  mockCardPlayAction.mockResolvedValue(undefined);
  mockSetSearch.mockResolvedValue([]);
  
  renderGame();

  await screen.findByText(/secreto propio objetivo/i);

  const mySecret = await screen.findByAltText("mi-secreto");
  fireEvent.click(mySecret);

  await waitFor(() => {
    const actionButton = screen.getByRole("button", { name: /realizar acción/i });
    expect(actionButton).not.toBeDisabled();
  });

  const actionButton = screen.getByRole("button", { name: /realizar acción/i });
  fireEvent.click(actionButton);

  await waitFor(() => {
    expect(mockCardPlayAction).toHaveBeenCalledWith(88, "XYZ", {
      target_secrets: [301],
    });
  });
});
it("ejecuta playcardwithtargets con target cards y actualiza estados en SELECT CARD TOTRADE", async () => {
  mockGameRead.mockResolvedValue({
    ...mockGame,
    status: "select_card_to_trade",
    player_in_action: 1,
    current_turn: 3,
  });
  
  mockCardSearch.mockImplementation((params) => {
    if (params.turn_played__eq !== undefined) {
      return Promise.resolve([
        { id: 88, name: "card-trade", turn_played: 3, owner: 1 }
      ]);
    }
    if (params.owner__eq === 1) {
      return Promise.resolve([
        { id: 100, name: "carta-1", owner: 1 },
        { id: 101, name: "carta-2", owner: 1 }
      ]);
    }
    return Promise.resolve([]);
  });
  
  mockSecretSearch.mockResolvedValue([]);
  mockEventTableSearch.mockResolvedValue([]);
  mockCardPlayAction.mockResolvedValue(undefined);

  renderGame();

   await waitFor(() => {
    expect(mockGameRead).toHaveBeenCalled();
  });

  const cards = await screen.findAllByAltText(/carta-/);
  fireEvent.click(cards[0]);

  const actionButton = await screen.findByRole("button", { 
    name: /realizar acción/i 
  });
  
  await waitFor(() => {
    expect(actionButton).not.toBeDisabled();
  });

  fireEvent.click(actionButton);

  await waitFor(() => {
    expect(mockCardPlayAction).toHaveBeenCalledWith(88, "XYZ", {
      target_cards: [100]
    });
  });
});
  // it("ejecuta PCWT con playerorder left al seleccionar izq", async () => {
  //   mockGameRead.mockResolvedValue({
  //     ...mockGame,
  //     status: "waiting_to_choose_direction",
  //     player_in_action: 1,
  //     current_turn: 0,
  //   });
  //
  //   mockSecretSearch.mockResolvedValue([]);
  //   mockCardSearch.mockResolvedValue([
  //     { id: 77, name: "carta-con-direccion", turn_played: 0, owner: 1 }
  //   ]);
  //   mockCardPlayAction.mockResolvedValue(undefined);
  //
  //   renderGame();
  //
  //  await waitFor(() => {
  //     expect(screen.getByText(/Elegí la dirección/i)).toBeInTheDocument();
  //   });
  //
  //  const leftButton = screen.getByAltText(/izquierda/i);
  //   fireEvent.click(leftButton);
  //
  //   const confirmButton = screen.getByRole("button", { name: /confirmar/i });
  //   fireEvent.click(confirmButton);
  //
  //   await waitFor(() => {
  //     expect(mockCardPlayAction).toHaveBeenCalledWith(77, "XYZ", {
  //       player_order: "counter-clockwise",
  //     });
  //   });
  // });

  it("ejecuta PCWT con playerorder right al seleccionar derecha", async () => {
    mockGameRead.mockResolvedValue({
      ...mockGame,
      status: "waiting_to_choose_direction",
      player_in_action: 1,
      current_turn: 0,
    });

    mockSecretSearch.mockResolvedValue([]);
    mockCardSearch.mockResolvedValue([
      { id: 77, name: "carta-con-direccion", turn_played: 0, owner: 1 }
    ]);
    mockCardPlayAction.mockResolvedValue(undefined);

    renderGame();

    await waitFor(() => {
      expect(screen.getByText(/Elegí la dirección/i)).toBeInTheDocument();
    });

    // Hacer clic en la flecha derecha
    const rightButton = screen.getByAltText(/derecha/i);
    fireEvent.click(rightButton);

    // Hacer clic en el botón Confirmar
    const confirmButton = screen.getByRole("button", { name: /confirmar/i });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockCardPlayAction).toHaveBeenCalledWith(77, "XYZ", {
        player_order: "clockwise",
      });
    });
  });
});

describe("cardSelect (selección de cartas de la mano)", () => {
  const mockTableCards = [
    { id: 30, owner: null, name: "mesa1", discarded_order: 0 },
    { id: 31, owner: null, name: "mesa2", discarded_order: 0 },
    { id: 32, owner: null, name: "mesa3", discarded_order: 0 },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
 vi.spyOn(EventTableService, 'searchInTable').mockResolvedValue([]);
  
    localStorage.setItem(
      "player",
      JSON.stringify({ id: 1, position: 0, game_id: 1, token: "XYZ" })
    );

    mockGameRead.mockResolvedValue({
      ...mockGame,
      status: "turn_start",
      current_turn: 0,
    });

    mockPlayerRead.mockResolvedValue(mockMe);
    mockPlayerSearch.mockResolvedValue([mockPlayers[0], mockPlayers[1]]);
    mockSecretSearch.mockResolvedValue([]);

    mockCardSearch.mockImplementation((params) => {
      if (params.owner__eq === 1 && params.set_id__is_null === true)
        return Promise.resolve(mockCards);
      if (
        params.turn_discarded__is_null === true &&
        params.owner__is_null === true
      )
        return Promise.resolve(mockTableCards);
      if (params.turn_discarded__is_null === false) return Promise.resolve([]);
      if (params.game_id__eq === 1 && params.turn_discarded__eq === 0)
        return Promise.resolve([]);
      return Promise.resolve([]);
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  const renderAndWaitCards = async () => {
    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );
    await new Promise((resolve) => setTimeout(resolve, 100));
    return await screen.findAllByTestId("hand-card");
  };

  it("selecciona una carta", async () => {
    await renderAndWaitCards();
    let handCards = screen.getAllByTestId("hand-card");

    fireEvent.click(handCards[0]);

    await waitFor(() => {
      const updated = screen.getAllByTestId("hand-card")[0];
      expect(updated.className).toContain("scale-110");
      expect(updated.className).toContain("-translate-y-4");
      expect(updated.className).toContain("border-4");
      expect(updated.className).toContain("border-red-900");
    });
  });

  it("deselecciona una carta manteniendo otras", async () => {
    await renderAndWaitCards();
    let handCards = screen.getAllByTestId("hand-card");

    
    fireEvent.click(handCards[0]);
    fireEvent.click(handCards[1]);
    fireEvent.click(handCards[2]);

    await waitFor(() => {
      const updated = screen.getAllByTestId("hand-card");
      expect(updated[0].className).toContain("scale-110");
      expect(updated[1].className).toContain("scale-110");
      expect(updated[2].className).toContain("scale-110");
    });

    fireEvent.click(screen.getAllByTestId("hand-card")[0]);

    await waitFor(() => {
      const updated = screen.getAllByTestId("hand-card");
      expect(updated[0].className).not.toContain("scale-110");
      expect(updated[1].className).toContain("scale-110");
      expect(updated[2].className).toContain("scale-110");
    });
  });
  it("seleccionar not so fast en waiting for cancel action", async () => {
  mockGameRead.mockResolvedValue({
    ...mockGame,
    status: "waiting_for_cancel_action",
    current_turn: 0,
  });

  const mockCardsWithNotSoFast = [
    { id: 10, owner: 1, name: "not-so-fast", card_type: "detective" },
    { id: 11, owner: 1, name: "tommy-beresford", card_type: "detective" },
    { id: 12, owner: 1, name: "card-trade", card_type: "event" },
  ];

  mockCardSearch.mockImplementation((params) => {
    if (params.owner__eq === 1 && params.set_id__is_null === true)
      return Promise.resolve(mockCardsWithNotSoFast);
    if (
      params.turn_discarded__is_null === true &&
      params.owner__is_null === true
    )
      return Promise.resolve(mockTableCards);
    if (params.turn_discarded__is_null === false) return Promise.resolve([]);
    if (params.game_id__eq === 1 && params.turn_discarded__eq === 0)
      return Promise.resolve([]);
    return Promise.resolve([]);
  });

  await renderAndWaitCards();
  let handCards = screen.getAllByTestId("hand-card");

  fireEvent.click(handCards[0]);

  await waitFor(() => {
    const updated = screen.getAllByTestId("hand-card")[0];
    expect(updated.className).toContain("scale-110");
    expect(updated.className).toContain("border-red-900");
  });

  fireEvent.click(handCards[1]);

  await waitFor(() => {
    const updated = screen.getAllByTestId("hand-card");
    expect(updated[0].className).toContain("scale-110");
    expect(updated[1].className).not.toContain("scale-110");
  });
});

it("deseleccionar en waiting for cancel action", async () => {
  mockGameRead.mockResolvedValue({
    ...mockGame,
    status: "waiting_for_cancel_action",
    current_turn: 0,
  });

  const mockCardsWithNotSoFast = [
    { id: 10, owner: 1, name: "not-so-fast", card_type: "detective" },
    { id: 11, owner: 1, name: "tommy-beresford", card_type: "detective" },
  ];

  mockCardSearch.mockImplementation((params) => {
    if (params.owner__eq === 1 && params.set_id__is_null === true)
      return Promise.resolve(mockCardsWithNotSoFast);
    if (
      params.turn_discarded__is_null === true &&
      params.owner__is_null === true
    )
      return Promise.resolve(mockTableCards);
    if (params.turn_discarded__is_null === false) return Promise.resolve([]);
    if (params.game_id__eq === 1 && params.turn_discarded__eq === 0)
      return Promise.resolve([]);
    return Promise.resolve([]);
  });

  await renderAndWaitCards();
  let handCards = screen.getAllByTestId("hand-card");

  fireEvent.click(handCards[0]);

  await waitFor(() => {
    const updated = screen.getAllByTestId("hand-card")[0];
    expect(updated.className).toContain("scale-110");
  });

  fireEvent.click(handCards[0]);

  await waitFor(() => {
    const updated = screen.getAllByTestId("hand-card")[0];
    expect(updated.className).not.toContain("scale-110");
  });
});
it("no permite seleccionar la carta Dead card folly jugada en select card to trade", async () => {
  mockGameRead.mockResolvedValue({
    ...mockGame,
    status: "select_card_to_trade",
    current_turn: 0,
  });

  const mockCardsWithCardTrade = [
    { id: 10, owner: 1, name: "dead-card-folly", card_type: "event", turn_played: 0 },
    { id: 11, owner: 1, name: "tommy-beresford", card_type: "detective" },
  ];

  mockCardSearch.mockImplementation((params) => {
    if (params.owner__eq === 1 && params.set_id__is_null === true)
      return Promise.resolve(mockCardsWithCardTrade);
    if (params.turn_discarded__is_null === true && params.owner__is_null === true)
      return Promise.resolve(mockTableCards);
    if (params.turn_discarded__is_null === false) return Promise.resolve([]);
    if (params.game_id__eq === 1 && params.turn_played__eq === 0)
      return Promise.resolve([mockCardsWithCardTrade[0]]);
    return Promise.resolve([]);
  });

 
  const mockEventTableSearch = vi.spyOn(EventTableService, 'searchInTable')
    .mockResolvedValue([]);

  await renderAndWaitCards();
  let handCards = screen.getAllByTestId("hand-card");

  fireEvent.click(handCards[0]); // Intentar seleccionar card-trade jugada

  await waitFor(() => {
    expect(handCards[0].className).not.toContain("scale-110");
  });

  fireEvent.click(handCards[1]); // Seleccionar otra carta

  await waitFor(() => {
    expect(handCards[1].className).toContain("scale-110");
  });

  mockEventTableSearch.mockRestore();
});
it("no permite seleccionar la carta card trade jugada en select card to trade", async () => {
  mockGameRead.mockResolvedValue({
    ...mockGame,
    status: "select_card_to_trade",
    current_turn: 0,
  });

  const mockCardsWithCardTrade = [
    { id: 10, owner: 1, name: "card-trade", card_type: "event", turn_played: 0 },
    { id: 11, owner: 1, name: "tommy-beresford", card_type: "detective" },
  ];

  mockCardSearch.mockImplementation((params) => {
    if (params.owner__eq === 1 && params.set_id__is_null === true)
      return Promise.resolve(mockCardsWithCardTrade);
    if (params.turn_discarded__is_null === true && params.owner__is_null === true)
      return Promise.resolve(mockTableCards);
    if (params.turn_discarded__is_null === false) return Promise.resolve([]);
    if (params.game_id__eq === 1 && params.turn_played__eq === 0)
      return Promise.resolve([mockCardsWithCardTrade[0]]);
    return Promise.resolve([]);
  });

 
  const mockEventTableSearch = vi.spyOn(EventTableService, 'searchInTable')
    .mockResolvedValue([]);

  await renderAndWaitCards();
  let handCards = screen.getAllByTestId("hand-card");

  fireEvent.click(handCards[0]); // Intentar seleccionar card-trade jugada

  await waitFor(() => {
    expect(handCards[0].className).not.toContain("scale-110");
  });

  fireEvent.click(handCards[1]); // Seleccionar otra carta

  await waitFor(() => {
    expect(handCards[1].className).toContain("scale-110");
  });

  mockEventTableSearch.mockRestore();
});
});

describe("cardPicker (selección de cartas de la mesa)", () => {
  const mockTableCards = [
    { id: 30, owner: null, name: "mesa1", discarded_order: 0 },
    { id: 31, owner: null, name: "mesa2", discarded_order: 0 },
    { id: 32, owner: null, name: "mesa3", discarded_order: 0 },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();

    localStorage.setItem(
      "player",
      JSON.stringify({ id: 1, position: 0, game_id: 1, token: "XYZ" })
    );

    mockGameRead.mockResolvedValue({
      ...mockGame,
      status: "turn_start",
      current_turn: 0,
    });

    mockPlayerRead.mockResolvedValue(mockMe);
    mockPlayerSearch.mockResolvedValue([mockPlayers[0], mockPlayers[1]]);
    mockSecretSearch.mockResolvedValue([]);

    mockCardSearch.mockImplementation((params) => {
      if (params.owner__eq === 1 && params.set_id__is_null === true)
        return Promise.resolve(mockCards);
      if (
        params.turn_discarded__is_null === true &&
        params.owner__is_null === true
      )
        return Promise.resolve(mockTableCards);
      if (params.turn_discarded__is_null === false) return Promise.resolve([]);
      if (params.game_id__eq === 1 && params.turn_discarded__eq === 0)
        return Promise.resolve([]);
      return Promise.resolve([]);
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  const renderAndReady = async () => {
    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );
    await new Promise((resolve) => setTimeout(resolve, 100));
    return await screen.findAllByTestId("table-card");
  };

  it("no se puede seleccionar si no es mi turno", async () => {
    mockGameRead.mockResolvedValueOnce({
      ...mockGame,
      status: "turn_start",
      current_turn: 99,
    });

    const tableCards = await renderAndReady();
    fireEvent.click(tableCards[0]);

    await waitFor(() => {
      expect(tableCards[0].className).not.toContain("border-red-900");
    });
  });

  it("selecciona y deselecciona una carta del tablecards", async () => {
    await renderAndReady();

    let tableCards = screen.getAllByTestId("table-card");
    fireEvent.click(tableCards[0]);

    await waitFor(() => {
      tableCards = screen.getAllByTestId("table-card");
      expect(tableCards[0].className).toContain("border-red-900");
      expect(tableCards[0].className).toContain("scale-110");
    });

    fireEvent.click(tableCards[0]);

    await waitFor(() => {
      tableCards = screen.getAllByTestId("table-card");
      expect(tableCards[0].className).not.toContain("border-red-900");
      expect(tableCards[0].className).not.toContain("scale-110");
    });
  });

  it("no permite seleccionar más cartas que missing", async () => {
    await renderAndReady();

    let tableCards = screen.getAllByTestId("table-card");

    fireEvent.click(tableCards[0]);
    fireEvent.click(tableCards[1]);
    fireEvent.click(tableCards[2]);

    await waitFor(() => {
      tableCards = screen.getAllByTestId("table-card");
      const selected = tableCards.filter((el) =>
        el.className.includes("border-red-900")
      );
      expect(selected.length).toBe(2);
    });
  });
});

describe("handlePick3 (juntar cartas de la mesa)", () => {
  const mockTableCards = [
    { id: 30, owner: null, name: "mesa1", discarded_order: 0 },
    { id: 31, owner: null, name: "mesa2", discarded_order: 0 },
    { id: 32, owner: null, name: "mesa3", discarded_order: 0 },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();

    localStorage.setItem(
      "player",
      JSON.stringify({ id: 1, position: 0, game_id: 1, token: "XYZ" })
    );

    mockGameRead.mockResolvedValue({
      ...mockGame,
      status: "turn_start",
      current_turn: 0,
    });

    mockPlayerRead.mockResolvedValue(mockMe);
    mockPlayerSearch.mockResolvedValue(mockPlayers);
    mockSecretSearch.mockResolvedValue(mockSecrets);

    mockCardSearch.mockImplementation((params) => {
      if (params.owner__eq === 1 && params.set_id__is_null === true)
        return Promise.resolve(mockCards);
      if (
        params.turn_discarded__is_null === true &&
        params.owner__is_null === true
      )
        return Promise.resolve(mockTableCards);
      if (params.turn_discarded__is_null === false) return Promise.resolve([]);
      if (params.game_id__eq === 1 && params.turn_discarded__eq === 0)
        return Promise.resolve([]);
      return Promise.resolve([]);
    });

    mockCardUpdate.mockResolvedValue({ ok: true });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  const renderAndWaitForUI = async () => {
    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );
    await new Promise((resolve) => setTimeout(resolve, 100));
    return await screen.findAllByTestId("table-card");
  };

  it("actualiza una carta con CardService.update", async () => {
    await renderAndWaitForUI();

    let tableCards = screen.getAllByTestId("table-card");
    fireEvent.click(tableCards[0]);

    const button = await screen.findByRole("button", { name: /juntar carta/i });
    expect(button).toBeInTheDocument();

    fireEvent.click(button);

    await waitFor(() => {
      expect(mockCardUpdate).toHaveBeenCalledTimes(1);
      expect(mockCardUpdate).toHaveBeenCalledWith(30, {
        owner: 1,
        token: "XYZ",
      });
    });
  });
});

describe("WinDialog rendering", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();

    localStorage.setItem(
      "player",
      JSON.stringify({ id: 1, position: 0, game_id: 1, token: "XYZ" })
    );

    mockGameRead.mockResolvedValue({
      ...mockGame,
      status: "finalized",
    });

    mockPlayerRead.mockResolvedValue(mockMe);
    mockPlayerSearch.mockResolvedValue(mockPlayers);
    mockSecretSearch.mockResolvedValue(mockSecrets);

   mockCardSearch.mockImplementation((params) => {
      if (params.owner__eq === 1 && params.set_id__is_null === true)
        return Promise.resolve(mockCards);
      if (
        params.turn_discarded__is_null === true &&
        params.owner__is_null === true
      )
        return Promise.resolve([
          { id: 30, owner: null, name: "mesa1", discarded_order: 0 },
          { id: 31, owner: null, name: "mesa2", discarded_order: 0 },
          { id: 32, owner: null, name: "mesa3", discarded_order: 0 },
          { id: 33, owner: null, name: "mesa4", discarded_order: 0 },
        ]);
      if (params.turn_discarded__is_null === false) return Promise.resolve([]);
      if (params.game_id__eq === 1 && params.turn_discarded__eq === 0)
        return Promise.resolve([]);
      return Promise.resolve([]);
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  const renderGame = async () => {
    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );
    await new Promise((resolve) => setTimeout(resolve, 100));
  };

  it("muestra WinDialog cuando el game status es FINALIZED", async () => {
    await renderGame();

    await waitFor(() => {
      expect(
        screen.getByText("¡El asesino fue capturado!")
      ).toBeInTheDocument();
    });
  });

  it("muestra título correcto cuando regularDeckEmpty = true", async () => {
    mockGameRead.mockResolvedValueOnce({
      ...mockGame,
      status: "finalized",
    });

    mockCardSearch.mockImplementation((params) => {
      if (params.owner__eq === 1 && params.set_id__is_null === true)
        return Promise.resolve(mockCards);
      if (
        params.turn_discarded__is_null === true &&
        params.owner__is_null === true
      )
        return Promise.resolve([
          { id: 30, owner: null, name: "mesa1", discarded_order: 0 },
          { id: 31, owner: null, name: "mesa2", discarded_order: 0 },
          { id: 32, owner: null, name: "mesa3", discarded_order: 0 },
        ]);
      if (params.turn_discarded__is_null === false) return Promise.resolve([]);
      if (params.game_id__eq === 1 && params.turn_discarded__eq === 0)
        return Promise.resolve([]);
      return Promise.resolve([]);
    });

    await renderGame();

    await waitFor(() => {
      expect(screen.getByText("¡El asesino se escapó!")).toBeInTheDocument();
    });
  });

  it("muestra título correcto cuando regularDeckEmpty = false", async () => {
   
    mockCardSearch.mockImplementation((params) => {
      if (params.owner__eq === 1 && params.set_id__is_null === true)
        return Promise.resolve(mockCards);
      if (
        params.turn_discarded__is_null === true &&
        params.owner__is_null === true
      )
        return Promise.resolve([
          { id: 30, owner: null, name: "mesa1", discarded_order: 0 },
          { id: 31, owner: null, name: "mesa2", discarded_order: 0 },
          { id: 32, owner: null, name: "mesa3", discarded_order: 0 },
          { id: 33, owner: null, name: "mesa4", discarded_order: 0 },
          { id: 34, owner: null, name: "mesa5", discarded_order: 0 },
        ]);
      if (params.turn_discarded__is_null === false) return Promise.resolve([]);
      if (params.game_id__eq === 1 && params.turn_discarded__eq === 0)
        return Promise.resolve([]);
      return Promise.resolve([]);
    });

    await renderGame();

    await waitFor(() => {
      expect(
        screen.getByText("¡El asesino fue capturado!")
      ).toBeInTheDocument();
    });
  });

  it("muestra el botón 'Volver al inicio' y navega correctamente", async () => {
    await renderGame();

    const button = screen.getByRole("button", { name: /volver al inicio/i });
    expect(button).toBeInTheDocument();

    fireEvent.click(button);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/game_list");
    });
  });
});
describe("mostrar cómplice", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();

    localStorage.setItem(
      "player",
      JSON.stringify({ id: 1, position: 0, game_id: 1, token: "XYZ" })
    );

    mockGameRead.mockResolvedValue({
      ...mockGame,
      status: "turn_start",
      current_turn: 0,
    });

    mockPlayerRead.mockResolvedValue({
      id: 1,
      name: "Yo",
      avatar: "detective1",
      position: 0,
      board_position: 0,
    });

    mockPlayerSearch.mockResolvedValue([
      {
        id: 1,
        name: "Yo",
        avatar: "detective1",
        position: 0,
        board_position: 0,
      },
      {
        id: 2,
        name: "Jugador 2",
        avatar: "detective2",
        position: 1,
        board_position: 1,
      },
    ]);

    mockCardSearch.mockResolvedValue([]);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("muestra 'Asesino' cuando el jugador tiene un secreto de tipo murderer", async () => {
    mockSecretSearch.mockResolvedValue([
      {
        id: 301,
        owner: 1,
        name: "soy-asesino",
        revealed: false,
        type: "murderer",
      },
      {
        id: 302,
        owner: 2,
        name: "secreto-otro",
        revealed: false,
        type: "varios",
      },
    ]);

    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Asesino")).toBeInTheDocument();
    });
  });

  it("muestra 'Cómplice' cuando el jugador tiene un secreto de tipo accomplice", async () => {
    mockSecretSearch.mockResolvedValue([
      {
        id: 301,
        owner: 1,
        name: "soy-complice",
        revealed: false,
        type: "accomplice",
      },
      {
        id: 302,
        owner: 2,
        name: "secreto-otro",
        revealed: false,
        type: "varios",
      },
    ]);

    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Cómplice")).toBeInTheDocument();
    });
  });
});
describe("avatar fallback", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();

    localStorage.setItem(
      "player",
      JSON.stringify({ id: 1, position: 0, game_id: 1, token: "XYZ" })
    );

    mockGameRead.mockResolvedValue({
      ...mockGame,
      status: "turn_start",
      current_turn: 0,
    });

    mockPlayerRead.mockResolvedValue({
      id: 1,
      name: "Yo",
      avatar: "avatar-invalido",
      position: 0,
      board_position: 0,
    });

    mockCardSearch.mockResolvedValue([]);
    mockSecretSearch.mockResolvedValue([]);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("usa AVATARS[0] cuando el avatar del jugador no se encuentra", async () => {
    const playersWithInvalidAvatar = [
      { id: 1, name: "Yo", avatar: "avatar-invalido", position: 0, board_position: 0 },
      { id: 2, name: "Jugador 2", avatar: "detective2", position: 1, board_position: 1 },
    ];

    mockPlayerSearch.mockResolvedValue(playersWithInvalidAvatar);

    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Jugador 2")).toBeInTheDocument();
    });

    const allImages = screen.getAllByRole("img", { name: "avatar" });
    const avatarWithInvalidId = allImages[0];

    expect(avatarWithInvalidId).toBeDefined();
    expect(avatarWithInvalidId.src).toContain("pfp-hercule-poirot.jpg");
  });
});


describe("desgracia social", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    localStorage.setItem("player", JSON.stringify({ id: 1, position: 0, game_id: 1, token: "XYZ" }));

    const mockMeWithDisgrace = { ...mockMe, social_disgrace: true };
    const mockPlayersWithDisgrace = mockPlayers.map(p => ({ ...p, social_disgrace: p.id === 1 ? true : false })); 

    mockGameRead.mockResolvedValue({ ...mockGame, status: "turn_start", current_turn: 0 });
    mockPlayerRead.mockResolvedValue(mockMeWithDisgrace);
    mockPlayerSearch.mockResolvedValue(mockPlayersWithDisgrace);
    mockCardSearch.mockResolvedValue(mockCards);
  });

  it("muestra indicador visual para jugador en desgracia social", async () => {
    render(<MemoryRouter initialEntries={["/game/1"]}><Routes><Route path="/game/:gid" element={<Game />} /></Routes></MemoryRouter>);
    await waitFor(() => screen.getByText("Yo"));
    const avatars = screen.getAllByAltText("avatar");
    const myAvatarContainer = avatars[0]?.parentElement; 
    const myAvatarImg = avatars[0]; 
    expect(myAvatarContainer?.className).toContain("border-blue-800");  
    expect(myAvatarImg?.className).toContain("grayscale"); 
  });

  it("muestra texto privado encima de las cartas en desgracia social", async () => {
    render(<MemoryRouter initialEntries={["/game/1"]}><Routes><Route path="/game/:gid" element={<Game />} /></Routes></MemoryRouter>);
    await waitFor(() => screen.getByText("Estás en desgracia social, seleccioná solo una carta para descartar."));
  });

  it("restringe selección a 1 carta en desgracia social", async () => {
    render(<MemoryRouter initialEntries={["/game/1"]}><Routes><Route path="/game/:gid" element={<Game />} /></Routes></MemoryRouter>);
    await waitFor(() => screen.getByText("Estás en desgracia social, seleccioná solo una carta para descartar."));
    await waitFor(() => screen.getByText("Yo")); 
    await waitFor(() => screen.getAllByTestId("hand-card")); 
    const handCards = screen.getAllByTestId("hand-card");

    await act(async () => {
      fireEvent.click(handCards[0]);
    });
    await waitFor(() => {
      const updatedHandCards = screen.getAllByTestId("hand-card");
      expect(updatedHandCards[0].className).toContain("scale-110");
    }, { timeout: 3000 });

    await act(async () => {
      fireEvent.click(handCards[1]);
    });
    await waitFor(() => {
      const updatedHandCards = screen.getAllByTestId("hand-card");
      expect(updatedHandCards[0].className).toContain("scale-110"); 
      expect(updatedHandCards[1].className).not.toContain("scale-110"); 
    }, { timeout: 3000 });
  });

  it("barra de acciones se muestra con selección y botón habilitado con 1 carta en desgracia social", async () => {
    render(<MemoryRouter initialEntries={["/game/1"]}><Routes><Route path="/game/:gid" element={<Game />} /></Routes></MemoryRouter>);
    await waitFor(() => screen.getByText("Yo"));
    await waitFor(() => screen.getAllByTestId("hand-card"));
    const handCards = screen.getAllByTestId("hand-card");
    
    expect(screen.queryByText("Descartar cartas")).not.toBeInTheDocument();
    
    await act(async () => {
      fireEvent.click(handCards[0]);
    });
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /descartar cartas/i })).toBeInTheDocument();
    }, { timeout: 3000 });
    const discardButton = screen.getByRole("button", { name: /descartar cartas/i });
    expect(discardButton).not.toBeDisabled(); 
    
    await act(async () => {
      fireEvent.click(handCards[0]);
    });
    await waitFor(() => {
      expect(screen.queryByText("Descartar cartas")).not.toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it("deshabilita botón 'Jugar set' en desgracia social", async () => {
    render(<MemoryRouter initialEntries={["/game/1"]}><Routes><Route path="/game/:gid" element={<Game />} /></Routes></MemoryRouter>);
    await waitFor(() => screen.getByText("Yo"));
    await waitFor(() => screen.getAllByTestId("hand-card"));
    const handCards = screen.getAllByTestId("hand-card");

    await act(async () => {
      fireEvent.click(handCards[0]);  
      fireEvent.click(handCards[1]);  
    });

    await waitFor(() => {
      const playSetButton = screen.getByRole("button", { name: /jugar set/i });
      expect(playSetButton).toBeDisabled();
    }, { timeout: 3000 });
  });

  it("deshabilita botón 'Jugar evento' en desgracia social", async () => {
    render(<MemoryRouter initialEntries={["/game/1"]}><Routes><Route path="/game/:gid" element={<Game />} /></Routes></MemoryRouter>);
    await waitFor(() => screen.getByText("Yo"));
    await waitFor(() => screen.getAllByTestId("hand-card"));
    const handCards = screen.getAllByTestId("hand-card");

    await act(async () => {
      fireEvent.click(handCards[3]);
    });

    await waitFor(() => {
      const playEventButton = screen.getByRole("button", { name: /jugar evento/i });
      expect(playEventButton).toBeDisabled();
    }, { timeout: 3000 });
  });

  it("muestra borde azul en avatar durante turno incluso en desgracia social", async () => {
    render(<MemoryRouter initialEntries={["/game/1"]}><Routes><Route path="/game/:gid" element={<Game />} /></Routes></MemoryRouter>);
    await waitFor(() => screen.getByText("Yo"));
    const avatars = screen.getAllByAltText("avatar");
    const myAvatarContainer = avatars[0]?.parentElement;  
    expect(myAvatarContainer?.className).toContain("border-blue-800");
  });


  it("no muestra indicador ni texto si no está en desgracia social", async () => {
    const mockMeWithoutDisgrace = { ...mockMe, social_disgrace: false };
    const mockPlayersWithoutDisgrace = mockPlayers.map(p => ({ ...p, social_disgrace: false }));
    mockPlayerRead.mockResolvedValue(mockMeWithoutDisgrace);
    mockPlayerSearch.mockResolvedValue(mockPlayersWithoutDisgrace);

    render(<MemoryRouter initialEntries={["/game/1"]}><Routes><Route path="/game/:gid" element={<Game />} /></Routes></MemoryRouter>);
    await waitFor(() => screen.getByText("Yo"));
    const avatars = screen.getAllByAltText("avatar");
    const myAvatarContainer = avatars[0]?.parentElement;  
    const myAvatarImg = avatars[0];  
    expect(myAvatarContainer?.className).toContain("border-blue-800");  
    expect(myAvatarImg?.className).not.toContain("grayscale");  
    expect(screen.queryByText("Estás en desgracia social")).not.toBeInTheDocument();
  });
});


describe("WinDialog rendering con nueva lógica murdererEscaped", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();

    localStorage.setItem(
      "player",
      JSON.stringify({ id: 1, position: 0, game_id: 1, token: "XYZ" })
    );

    mockGameRead.mockResolvedValue({
      ...mockGame,

      status: "finalized",
    });

    mockPlayerRead.mockResolvedValue(mockMe);
    mockPlayerSearch.mockResolvedValue(mockPlayers);
    mockSecretSearch.mockResolvedValue(mockSecrets); 
    mockCardSearch.mockImplementation((params) => {
      if (params.owner__eq === 1 && params.set_id__is_null === true)
        return Promise.resolve(mockCards);
      if (
        params.turn_discarded__is_null === true &&
        params.owner__is_null === true
      )
        return Promise.resolve([
          { id: 30, owner: null, name: "mesa1", discarded_order: 0 },
          { id: 31, owner: null, name: "mesa2", discarded_order: 0 },
          { id: 32, owner: null, name: "mesa3", discarded_order: 0 },
          { id: 33, owner: null, name: "mesa4", discarded_order: 0 }, 
        ]);
      if (params.turn_discarded__is_null === false) return Promise.resolve([]);
      if (params.game_id__eq === 1 && params.turn_discarded__eq === 0)
        return Promise.resolve([]);
      return Promise.resolve([]);
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  const renderGame = async () => {
    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );

    await new Promise((resolve) => setTimeout(resolve, 100));
  };

  it("muestra WinDialog cuando el game status es FINALIZED", async () => {
    await renderGame();

    await waitFor(() => {
      expect(
        screen.getByText("¡El asesino fue capturado!") 
      ).toBeInTheDocument();
    });
  });

  it("muestra '¡El asesino se escapó!' cuando el mazo está agotado", async () => {
    //mazo agotado: length === 3
    mockCardSearch.mockImplementation((params) => {
      if (params.owner__eq === 1 && params.set_id__is_null === true)
        return Promise.resolve(mockCards);
      if (
        params.turn_discarded__is_null === true &&
        params.owner__is_null === true
      )
        return Promise.resolve([
          { id: 30, owner: null, name: "mesa1", discarded_order: 0 },
          { id: 31, owner: null, name: "mesa2", discarded_order: 0 },
          { id: 32, owner: null, name: "mesa3", discarded_order: 0 },
        ]);
      if (params.turn_discarded__is_null === false) return Promise.resolve([]);
      if (params.game_id__eq === 1 && params.turn_discarded__eq === 0)
        return Promise.resolve([]);
      return Promise.resolve([]);
    });

    await renderGame();

    await waitFor(() => {
      expect(screen.getByText("¡El asesino se escapó!")).toBeInTheDocument();
    });
  });

  it("muestra '¡El asesino se escapó!' cuando todos los demás están en desgracia social", async () => {
    const playersWithDisgrace = mockPlayers.map(p => ({
      ...p,
      social_disgrace: p.id !== 102 ? true : false,
    }));
    mockPlayerSearch.mockResolvedValue(playersWithDisgrace);

    await renderGame();

    await waitFor(() => {
      expect(screen.getByText("¡El asesino se escapó!")).toBeInTheDocument();
    }); 
  });

  it("muestra '¡El asesino fue capturado!'", async () => {
    const playersMixedDisgrace = mockPlayers.map(p => ({
      ...p,
      social_disgrace: p.id === 101 ? true : false, 
    }));
    mockPlayerSearch.mockResolvedValue(playersMixedDisgrace);

    await renderGame();

    await waitFor(() => {
      expect(
        screen.getByText("¡El asesino fue capturado!")
      ).toBeInTheDocument();
    });
  });

  it("muestra '¡El asesino se escapó!' por mazo agotado y por desgracia social", async () => {
    //mazo agotado
    mockCardSearch.mockImplementation((params) => {
      if (params.owner__eq === 1 && params.set_id__is_null === true)
        return Promise.resolve(mockCards);
      if (
        params.turn_discarded__is_null === true &&
        params.owner__is_null === true
      )
        return Promise.resolve([
          { id: 30, owner: null, name: "mesa1", discarded_order: 0 },
          { id: 31, owner: null, name: "mesa2", discarded_order: 0 },
          { id: 32, owner: null, name: "mesa3", discarded_order: 0 },
        ]);
      if (params.turn_discarded__is_null === false) return Promise.resolve([]);
      if (params.game_id__eq === 1 && params.turn_discarded__eq === 0)
        return Promise.resolve([]);
      return Promise.resolve([]);
    });

    //todos en desgracia 
    const playersWithDisgrace = mockPlayers.map(p => ({
      ...p,
      social_disgrace: p.id !== 102 ? true : false,
    }));
    mockPlayerSearch.mockResolvedValue(playersWithDisgrace);

    await renderGame();

    await waitFor(() => {
      expect(screen.getByText("¡El asesino se escapó!")).toBeInTheDocument();
    });
  });

  it("muestra el botón 'Volver al inicio' y navega correctamente", async () => {
    await renderGame();

    const button = screen.getByRole("button", { name: /volver al inicio/i });
    expect(button).toBeInTheDocument();

    fireEvent.click(button);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/game_list");
    });
  });
});
describe("pointyoursuspicions votacion", () => {
 
  const basePlayers = [
    { id: 1, name: "Yo", avatar: "detective1", position: 0, board_position: 0 },
    { id: 2, name: "Jugador 2", avatar: "detective2", position: 1, board_position: 1 },
    { id: 3, name: "Jugador 3", avatar: "detective3", position: 2, board_position: 2 },
  ];

  const renderGame = () => {
    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    localStorage.setItem(
      "player",
      JSON.stringify({ id: 1, position: 0, game_id: 1, token: "XYZ" })
    );

    mockPlayerRead.mockResolvedValue({
      id: 1,
      name: "Yo",
      avatar: "detective1",
      position: 0,
      board_position: 0,
      token: "XYZ",
    });
    mockPlayerSearch.mockResolvedValue(basePlayers);
    mockSecretSearch.mockResolvedValue([]);
    mockSetSearch.mockResolvedValue([]);
    
    mockEventTableSearch.mockReset();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("setea alreadyvoted a true cuando el jugador ya votó pero no todos votaron", async () => {
    mockGameRead.mockResolvedValue({
      ...mockGame,
      status: "waiting_for_choose_player",
      player_in_action: 1,
      current_turn: 0,
    });

    mockCardSearch.mockImplementation((params) => {
      if (params.game_id__eq && params.turn_played__eq !== undefined) {
        return Promise.resolve([
          { id: 999, name: "point-your-suspicions", turn_played: 0, owner: 1 }
        ]);
      }
      return Promise.resolve([]);
    });

    mockEventTableSearch.mockResolvedValue([
      { id: 1, player_id: 1, action: "point_your_suspicions" },
      { id: 2, player_id: 2, action: "point_your_suspicions" },
    ]);

    renderGame();

    await waitFor(() => {
      expect(mockEventTableSearch).toHaveBeenCalledWith({
        game_id__eq: 1,
        action__eq: "point_your_suspicions",
        turn_played__eq: 0,
      });
    });
  });

  it("setea alreadyvoted a false cuando todos los jugadores votaron", async () => {
    mockGameRead.mockResolvedValue({
      ...mockGame,
      status: "waiting_for_choose_player",
      player_in_action: 1,
      current_turn: 0,
    });

    mockCardSearch.mockImplementation((params) => {
      if (params.game_id__eq && params.turn_played__eq !== undefined) {
        return Promise.resolve([
          { id: 999, name: "point-your-suspicions", turn_played: 0, owner: 1 }
        ]);
      }
      return Promise.resolve([]);
    });

    mockEventTableSearch.mockResolvedValue([
      { id: 1, player_id: 1, action: "point_your_suspicions" },
      { id: 2, player_id: 2, action: "point_your_suspicions" },
      { id: 3, player_id: 3, action: "point_your_suspicions" },
    ]);

    renderGame();

    await waitFor(() => {
      expect(mockEventTableSearch).toHaveBeenCalledWith({
        game_id__eq: 1,
        action__eq: "point_your_suspicions",
        turn_played__eq: 0,
      });
    });

    await waitFor(() => {
      expect(screen.queryByText(/jugador objetivo/i)).toBeInTheDocument();
    });
  });
});

describe("Modal de secreto privado", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    localStorage.setItem(
      "player",
      JSON.stringify({ id: 1, position: 0, game_id: 1, token: "XYZ" })
    );

    mockGameRead.mockResolvedValue({
      ...mockGame,
      status: "turn_start",
    });
    mockPlayerRead.mockResolvedValue(mockMe);
    mockPlayerSearch.mockResolvedValue(mockPlayers);
    mockCardSearch.mockResolvedValue(mockCards);
    mockSecretSearch.mockResolvedValue(mockSecrets);
  });

  it("abre el modal cuando llega mensaje WebSocket de secreto privado para el usuario correcto", async () => {
    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => screen.getByText("Yo"));

    const mockWsManager = vi.mocked(WebSocketManager);
    const wsInstance = mockWsManager.mock.results[0].value;
    const registerActionCalls = wsInstance.registerOnAction.mock.calls.filter(
      (call) => call[1] === "devious" && call[2] === "show-secret"  
    );
    const callback = registerActionCalls[0][0];  

    callback({ dest_user: 1, secret_id: mockSecrets[0].id });

    await waitFor(() => {
      expect(screen.getByText("¡Shh! Descubriste un secreto")).toBeInTheDocument();
    });
  });

});

describe("Chat integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    localStorage.setItem(
      "player",
      JSON.stringify({ id: 1, position: 0, game_id: 1, token: "XYZ" })
    );

    mockGameRead.mockResolvedValue({
      ...mockGame,
      status: "turn_start", 
    });
    mockPlayerRead.mockResolvedValue(mockMe);
    mockPlayerSearch.mockResolvedValue(mockPlayers);
    mockCardSearch.mockResolvedValue(mockCards);
    mockSecretSearch.mockResolvedValue(mockSecrets);
    Element.prototype.scrollIntoView = vi.fn();
  });

  it("renderiza el botón de chat", async () => {
    renderGame();

    await waitFor(() => {
      expect(screen.getByText("Chat")).toBeInTheDocument();
    });
  });

  it("abre el panel de chat al hacer click en el botón", async () => {
    renderGame();

    const chatButton = await screen.findByText("Chat");
    fireEvent.click(chatButton);
    expect(screen.getByText("Cerrar ✕")).toBeInTheDocument();
  });


  it("muestra indicador de mensajes no leídos cuando hay unreadCount", async () => {
  const { container } = renderGame();

  // Esperar a que se instancie el WebSocketManager mock
  const WS = (await import("../../components/WebSocketManager")).default as unknown as vi.Mock;
  await waitFor(() => {
    // Se crea al montar Game; si no hay instancias aún, waitFor reintenta
    expect(WS.mock.results.length).toBeGreaterThan(0);
  });

  // Se toma la primera instancia mockeada y capturamos el callback registrado
  const wsInstance = WS.mock.results[0].value;
  const onCreateCall = wsInstance.registerOnCreate.mock.calls.find(
    (c: any[]) => c[1] === "chat"
  );
  expect(onCreateCall).toBeTruthy();
  const onCreateCb = onCreateCall[0];

  // Nuevo msj con el chat cerrado
  onCreateCb({
    id: 999,
    game_id: 1,
    owner_name: "Otro",
    content: "hola",
    timestamp: "2023-01-01T00:05:00Z",
  });

  // Ahora el botón debe mostrar el puntito dentro
  const chatButton = await screen.findByText("Chat");
  const buttonEl = chatButton.closest("button");
  expect(buttonEl).toBeInTheDocument();

  // Busco el punto
  const dot = buttonEl?.querySelector("span");
  expect(dot).toBeInTheDocument();
  expect(dot?.className).toMatch(/bg-\[\#bb8512\]/);
});

  it("muestra popup de evento cuando llega mensaje WebSocket de chat sin owner_name", async () => {
    render(
      <MemoryRouter initialEntries={["/game/1"]}>
        <Routes>
          <Route path="/game/:gid" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => screen.getByText("Yo"));

    const WS = (await import("../../components/WebSocketManager")).default as unknown as vi.Mock;
    await waitFor(() => {
      expect(WS.mock.results.length).toBeGreaterThan(0);
    });

    const mockWsManager = vi.mocked(WebSocketManager);
    const wsInstance = mockWsManager.mock.results[0].value;
    const registerCreateCalls = wsInstance.registerOnCreate.mock.calls.filter(
      (call) => call[1] === "chat"
    );
    expect(registerCreateCalls.length).toBeGreaterThan(0); 

    const callback = registerCreateCalls[0][0];

    callback({ id: 1, game_id: 1, content: "Evento!", timestamp: "2023-01-01T00:00:00Z" });

    await waitFor(() => {
      expect(screen.getByText("Evento!")).toBeInTheDocument();
    });
  });

  it("activa chooseTheirSecret cuando playedCard es blackmailed", async () => {
    mockGameRead.mockResolvedValueOnce({
      ...mockGame,
      status: "waiting_for_choose_secret",
      player_in_action: 1,
      current_turn: 0,
    });
    mockCardSearch.mockImplementation((params) => {
      if (params.game_id__eq === 1 && params.turn_played__eq === 0) {
        return Promise.resolve([{ id: 100, name: "blackmailed", turn_played: 0, owner: 1 }]);
      }
      if (params.owner__eq === 1 && params.set_id__is_null === true) {
        return Promise.resolve(mockCards);
      }
      return Promise.resolve([]);
    });
    renderGame();
    await waitFor(() => screen.getByText("Yo"));
    expect(await screen.findByText("Esperando selección de secreto ajeno objetivo")).toBeInTheDocument();
  });
});