// src/components/LookIntoTheAshesModal.test.tsx
import "@testing-library/jest-dom";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import LookIntoTheAshesModal from "./LookIntoTheAshesModal";

const cards = [
  { id: 70, name: "adriane-oliver" },
  { id: 71, name: "look-into-the-ashes" },
  { id: 72, name: "parker-pyne" },
];

describe("LookIntoTheAshesModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("open=false", () => {
    const onConfirm = vi.fn();
    render(<LookIntoTheAshesModal open={false} cards={cards} onConfirm={onConfirm} />);

    // No hay título ni botón
    expect(
      screen.queryByText(/elegí la carta que quieras incorporar a tu mano/i)
    ).toBeNull();
    expect(screen.queryByRole("button", { name: /confirmar/i })).toBeNull();
  });

  it("renderiza cartas pero botón deshabilitado", () => {
    const onConfirm = vi.fn();
    render(<LookIntoTheAshesModal open={true} cards={cards} onConfirm={onConfirm} />);

    expect(
      screen.getByText(/elegí la carta que quieras incorporar a tu mano/i)
    ).toBeInTheDocument();

    expect(screen.getByAltText("adriane-oliver")).toBeInTheDocument();
    expect(screen.getByAltText("look-into-the-ashes")).toBeInTheDocument();
    expect(screen.getByAltText("parker-pyne")).toBeInTheDocument();

    const confirmBtn = screen.getByRole("button", { name: /confirmar/i });
    expect(confirmBtn).toBeDisabled();
  });

  it("seleccionar una carta", async () => {
    const onConfirm = vi.fn();
    render(<LookIntoTheAshesModal open={true} cards={cards} onConfirm={onConfirm} />);

    fireEvent.click(screen.getByAltText("parker-pyne"));

    const confirmBtn = screen.getByRole("button", { name: /confirmar/i });
    expect(confirmBtn).not.toBeDisabled();

    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(onConfirm).toHaveBeenCalledTimes(1);
      expect(onConfirm).toHaveBeenCalledWith(72);
    });
  });
});
