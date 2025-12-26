import "@testing-library/jest-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import WinDialog from "./WinDialog";

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<any>();
  return { ...actual, useNavigate: () => mockNavigate };
});

const baseProps = {
  open: true,
  murdererName: "sara",
  murdererAvatar: "",
};
describe("WinDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("no se muestra si open=false", () => {
    render(
      <MemoryRouter>
        <WinDialog {...baseProps} open={false} murdererEscaped={false} />
      </MemoryRouter>
    );

    expect(screen.queryByText(/el asesino fue capturado/i)).toBeNull();
    expect(screen.queryByText(/el asesino se escapó/i)).toBeNull();
  });

  it("muestra el título capturado", () => {
    render(
      <MemoryRouter>
        <WinDialog {...baseProps} murdererEscaped={false} />
      </MemoryRouter>
    );

    expect(screen.getByText(/el asesino fue capturado/i)).toBeInTheDocument();
    expect(screen.getByText("sara")).toBeInTheDocument();
    expect(screen.getByAltText("asesino")).toBeInTheDocument();
  });

  it("muestra el título escapo", () => {
    render(
      <MemoryRouter>
        <WinDialog {...baseProps} murdererEscaped={true} />
      </MemoryRouter>
    );

    expect(screen.getByText(/el asesino se escapó/i)).toBeInTheDocument();
    expect(screen.getByAltText("asesino")).toBeInTheDocument();
  });

  it("navega", () => {
    render(
      <MemoryRouter>
        <WinDialog {...baseProps} murdererEscaped={false} navigateTo="/game_list" />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole("button", { name: /volver al inicio/i }));
    expect(mockNavigate).toHaveBeenCalledWith("/game_list");
  });
});