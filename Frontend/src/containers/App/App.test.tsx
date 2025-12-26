import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { describe, it, expect, afterEach, vi } from "vitest";
import App from "./App";
import Game from "../Game/Game";

vi.mock("../../components/Home/game_list.jsx", () => ({
  default: ({ prePlayerData }: any) => {
    return (
      <div data-testid="game-list">
        {prePlayerData?.name} - {prePlayerData?.birthdate} - {prePlayerData?.avatar}
      </div>
    );
  },
}));

vi.mock("../../components/Login", () => ({
  default: ({ setPrePlayerData }: any) => {
    return (
      <button
        onClick={() =>
          setPrePlayerData({ name: "Jaz", birthdate: "2002-04-21", avatar: "avatar.png" })
        }
      >
        Ingresar
      </button>
    );
  },
}));

afterEach(() => {
  cleanup();
  vi.resetModules(); // Esto limpia los módulos importados y mocks
});


describe("App routing", () => {
  it("muestra Login en /", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/" element={<App />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByRole("button", { name: /ingresar/i })).toBeInTheDocument();
    expect(screen.queryByTestId("game-list")).toBeNull();
  });

  it("muestra Game en /game/:gameId", () => {
    render(
      <MemoryRouter initialEntries={["/game/123"]}>
        <Routes>
          <Route path="/game/:gameId" element={<Game />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText(/cargando/i)).toBeInTheDocument();
 expect(screen.queryByTestId("game-list")).toBeNull();
  });

   it("Sale del login y renderiza Game_List al setear prePlayerData", () => {
    render(<App />);

  
    expect(screen.getByRole("button", { name: /ingresar/i })).toBeInTheDocument();
    expect(screen.queryByTestId("game-list")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: /ingresar/i }));


    expect(screen.queryByRole("button", { name: /ingresar/i })).toBeNull();
    const gameList = screen.getByTestId("game-list");
    expect(gameList).toBeInTheDocument();

    expect(gameList).toHaveTextContent("Jaz");
    expect(gameList).toHaveTextContent("2002-04-21");
    expect(gameList).toHaveTextContent("avatar.png");
  });
});


 