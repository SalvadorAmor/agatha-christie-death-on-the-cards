import "@testing-library/jest-dom";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import FollyModal from "./FollyModal";

describe("FollyModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("open=false", () => {
    const onConfirm = vi.fn();
    render(<FollyModal open={false} onConfirm={onConfirm} />);

   expect(
      screen.queryByText(/elegí la dirección en la que querés enviar las cartas/i)
    ).toBeNull();
    expect(screen.queryByRole("button", { name: /confirmar/i })).toBeNull();
  });

  it("renderiza flechas pero botón confirmar deshabilitado", () => {
    const onConfirm = vi.fn();
    render(<FollyModal open={true} onConfirm={onConfirm} />);

    expect(
      screen.getByText(/elegí la dirección en la que querés enviar las cartas/i)
    ).toBeInTheDocument();
    expect(screen.getByAltText("izquierda")).toBeInTheDocument();
    expect(screen.getByAltText("derecha")).toBeInTheDocument();

    const confirmBtn = screen.getByRole("button", { name: /confirmar/i });
    expect(confirmBtn).toBeDisabled();
  });

  it("seleccionar izq", async () => {
    const onConfirm = vi.fn();
    render(<FollyModal open={true} onConfirm={onConfirm} />);

    fireEvent.click(screen.getByAltText("izquierda"));

    const confirmBtn = screen.getByRole("button", { name: /confirmar/i });
    expect(confirmBtn).not.toBeDisabled();

    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(onConfirm).toHaveBeenCalledTimes(1);
      expect(onConfirm).toHaveBeenCalledWith("counter-clockwise");
    });
  });

  it("seleccionar der", async () => {
    const onConfirm = vi.fn();
    render(<FollyModal open={true} onConfirm={onConfirm} />);

    fireEvent.click(screen.getByAltText("derecha"));

    const confirmBtn = screen.getByRole("button", { name: /confirmar/i });
    expect(confirmBtn).not.toBeDisabled();

    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(onConfirm).toHaveBeenCalledTimes(1);
      expect(onConfirm).toHaveBeenCalledWith("clockwise");
    });
  }); 
});