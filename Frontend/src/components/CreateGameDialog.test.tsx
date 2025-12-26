import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import CreateGameDialog from "./CreateGameDialog";

vi.mock("../services/GameService", () => ({
  default: {
    create: vi.fn(),
  },
}));
import GameService from "../services/GameService";

const playerData = {
  name: "Juan",
  birthdate: "2004-01-28T00:00:00.000Z",
  avatar: "detective2",
};

describe("CreateGameDialog", () => {
  let setItemSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    vi.clearAllMocks();

    setItemSpy = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {});
    vi.spyOn(Storage.prototype, "getItem").mockImplementation((key: string) => {
      if (key === "user.name") return "Sarita";
      if (key === "user.avatar") return "detective2";
      if (key === "user.birthdate") return "2004-01-28T00:00:00.000Z";
      return null;
    });
  });

  afterEach(() => {
    cleanup();
    setItemSpy.mockRestore();
  });

  it("renderiza ok", () => {
    render(
      <MemoryRouter>
        <CreateGameDialog prePlayerData={playerData} onClose={() => {}} />
      </MemoryRouter>
    );

    expect(screen.getByText("Crear Partida")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Confirmar" })).toBeInTheDocument();
  });

  it("caso nombre vacío", async () => {
    render(
      <MemoryRouter>
        <CreateGameDialog prePlayerData={playerData} onClose={() => {}} />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));

    expect(await screen.findByText(/el nombre no puede estar vacío/i)).toBeInTheDocument();
  });

  it("caso min ok, max demasiado alto", async () => {
    render(
      <MemoryRouter>
        <CreateGameDialog prePlayerData={playerData} onClose={() => {}} />
      </MemoryRouter>
    );

    const maxInput = screen.getByRole("maximo");
    const minInput = screen.getByRole("minimo");
    fireEvent.change(maxInput, { target: { value: "10" } });
    fireEvent.change(minInput, { target: { value: "2" } });

    const nameInput = screen.getByRole("textbox");
    fireEvent.change(nameInput, { target: { value: "Mi Partida" } });

    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));

    expect(await screen.findByText(/debe tener entre 2 y 6 jugadores/i)).toBeInTheDocument();
  });

  it("caso min muy bajo, max demasiado alto", async () => {
    render(
      <MemoryRouter>
        <CreateGameDialog prePlayerData={playerData} onClose={() => {}} />
      </MemoryRouter>
    );

    const maxInput = screen.getByRole("maximo");
    const minInput = screen.getByRole("minimo");
    fireEvent.change(maxInput, { target: { value: "10" } });
    fireEvent.change(minInput, { target: { value: "1" } });

    const nameInput = screen.getByRole("textbox");
    fireEvent.change(nameInput, { target: { value: "Mi Partida" } });

    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));

    expect(await screen.findByText(/debe tener entre 2 y 6 jugadores/i)).toBeInTheDocument();
  });

  it("caso max ok, min demasiado bajo", async () => {
    render(
      <MemoryRouter>
        <CreateGameDialog prePlayerData={playerData} onClose={() => {}} />
      </MemoryRouter>
    );

    const maxInput = screen.getByRole("maximo");
    const minInput = screen.getByRole("minimo");
    fireEvent.change(maxInput, { target: { value: "4" } });
    fireEvent.change(minInput, { target: { value: "1" } });

    const nameInput = screen.getByRole("textbox");
    fireEvent.change(nameInput, { target: { value: "Mi Partida" } });

    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));

    expect(await screen.findByText(/debe tener entre 2 y 6 jugadores/i)).toBeInTheDocument();
  });

  it("caso min mas alto que max", async () => {
    render(
      <MemoryRouter>
        <CreateGameDialog prePlayerData={playerData} onClose={() => {}} />
      </MemoryRouter>
    );

    const maxInput = screen.getByRole("maximo");
    const minInput = screen.getByRole("minimo");
    fireEvent.change(maxInput, { target: { value: "4" } });
    fireEvent.change(minInput, { target: { value: "6" } });

    const nameInput = screen.getByRole("textbox");
    fireEvent.change(nameInput, { target: { value: "Mi Partida" } });

    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));

    expect(await screen.findByText(/La cantidad máxima de jugadores no puede ser menor que la mínima./i)).toBeInTheDocument();
  });

it("muestra error si el create devuelve null", async () => {
  (GameService.create as any).mockResolvedValue(null);

  render(
    <MemoryRouter>
      <CreateGameDialog
        prePlayerData={playerData}
        onClose={() => {}}
      />
    </MemoryRouter>
  );

  fireEvent.change(screen.getByRole("textbox"), { target: { value: "Mi Partida" } });
  fireEvent.change(screen.getByRole("maximo"), { target: { value: "4" } });

  fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));

  await waitFor(() => {
    expect(screen.getByText(/error al navegar al lobby/i)).toBeInTheDocument();
  });
});

it("muestra 'Error creando la partida.'", async () => {
  (GameService.create as any).mockRejectedValue({});

  render(
    <MemoryRouter>
      <CreateGameDialog prePlayerData={playerData} onClose={() => {}} />
    </MemoryRouter>
  );

  fireEvent.change(screen.getByRole("textbox"), { target: { value: "Mi Partida" } });
  fireEvent.change(screen.getByRole("maximo"), { target: { value: "4" } });
  fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));

  await waitFor(() => {
    expect(screen.getByText(/Error creando la partida/i)).toBeInTheDocument();
  });
});

  
  it("caso submit ok, localStorage", async () => {
    const backendResponse = {
      player: { id: 1, name: "Sarita", avatar: "detective2", game_id: 123, token: "abc123" },
    };
    (GameService.create as any).mockResolvedValue(backendResponse);

    render(
      <MemoryRouter>
        <CreateGameDialog prePlayerData={{name: backendResponse.player.name, birthdate: Date.now().toString(), avatar: backendResponse.player.avatar}} onClose={() => {}} />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByRole("textbox"), { target: { value: "Mi Partida" } });
    fireEvent.change(screen.getByRole("maximo"), { target: { value: "4" } });
    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));

    await waitFor(() => {
      expect(GameService.create).toHaveBeenCalledTimes(1);
      expect(setItemSpy).toHaveBeenCalledWith("player",JSON.stringify(backendResponse.player)
      );
    });
  });
});