import "@testing-library/jest-dom";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import DelayModal from "./DelayModal";

const cards = [
  { id: 1, name: "a" },
  { id: 2, name: "b" },
  { id: 3, name: "c" },
  { id: 4, name: "d" },
  { id: 5, name: "e" },
];

describe("DelayModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("open=false no renderiza nada", () => {
    const onConfirm = vi.fn();
    render(<DelayModal open={false} cards={cards} onConfirm={onConfirm} />);

    expect(screen.queryByText(/elegí las cartas a devolver/i)).toBeNull();
  });

  it("renderiza correctamente con botón deshabilitado", () => {
    const onConfirm = vi.fn();
    render(
      <DelayModal open={true} cards={cards.slice(0, 5)} onConfirm={onConfirm} />
    );

    expect(
      screen.getByText(/elegí las cartas a devolver/i)
    ).toBeInTheDocument();

    // muestra todas las cartas
    expect(screen.getByAltText("a")).toBeInTheDocument();
    expect(screen.getByAltText("b")).toBeInTheDocument();
    expect(screen.getByAltText("c")).toBeInTheDocument();
    expect(screen.getByAltText("d")).toBeInTheDocument();
    expect(screen.getByAltText("e")).toBeInTheDocument();

    const confirmBtn = screen.getByRole("button", { name: /confirmar/i });
    expect(confirmBtn).toBeDisabled();
  });

  it("selecciona cartas y el botón se habilita sólo con todas las cartas seleccionadas", async () => {
    const onConfirm = vi.fn();
    render(<DelayModal open={true} cards={cards} onConfirm={onConfirm} />);

    const confirmBtn = screen.getByRole("button", { name: /confirmar/i });
    expect(confirmBtn).toBeDisabled();

    // seleccionamos 3 
    fireEvent.click(screen.getByAltText("a"));
    fireEvent.click(screen.getByAltText("b"));
    fireEvent.click(screen.getByAltText("c"));
    expect(confirmBtn).toBeDisabled();

    //2 más (total 5)
    fireEvent.click(screen.getByAltText("d"));
    fireEvent.click(screen.getByAltText("e"));
    expect(confirmBtn).not.toBeDisabled();
  });

  it("llama onConfirm con el orden de cartas", async () => {
    const onConfirm = vi.fn();
    render(<DelayModal open={true} cards={cards} onConfirm={onConfirm} />);

    // seleccionamos 5 en orden específico
    fireEvent.click(screen.getByAltText("e")); // 5
    fireEvent.click(screen.getByAltText("c")); // 3
    fireEvent.click(screen.getByAltText("a")); // 1
    fireEvent.click(screen.getByAltText("b")); // 2
    fireEvent.click(screen.getByAltText("d")); // 4

    const confirmBtn = screen.getByRole("button", { name: /confirmar/i });
    expect(confirmBtn).not.toBeDisabled();

    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(onConfirm).toHaveBeenCalledTimes(1);
      // el orden debe coincidir 
      expect(onConfirm).toHaveBeenCalledWith([5, 3, 1, 2, 4]);
    });
  });
  it("Si selecciona una carta se pone el numero del orden, desppues deselecciona una carta", async () => {
  const onConfirm = vi.fn();
  render(<DelayModal open={true} cards={cards} onConfirm={onConfirm} />);

  const carta1 = screen.getByAltText("a");
  const carta2 = screen.getByAltText("b");

   expect(screen.queryByText("1")).not.toBeInTheDocument();
   expect(screen.queryByText("2")).not.toBeInTheDocument();
  fireEvent.click(carta1);
  expect(screen.getByText("1")).toBeInTheDocument();
  fireEvent.click(carta2);
  expect(screen.getByText("1")).toBeInTheDocument();
  expect(screen.getByText("2")).toBeInTheDocument();

  fireEvent.click(carta1);

  await waitFor(() => {
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.queryByText("2")).not.toBeInTheDocument(); //carta a pasa a ser la unica seleccionada por ende pasa a ser 1 y el 2 desaparece
  });
});

});
