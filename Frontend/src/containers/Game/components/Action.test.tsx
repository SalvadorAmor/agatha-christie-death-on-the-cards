import "@testing-library/jest-dom";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Action } from "./Action";

describe("Action component", () => {
  it("muestra el mensaje y oculta el botón si el jugador no está en acción", () => {
    render(
      <Action
        target="Detective"
        action={vi.fn()}
        isPlayerInAction={false}
        isEnabled={false}
        gameStat="waiting_for_choose_player"
      />
    );

    expect(
      screen.getByText(/Esperando selección de Detective/i)
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /realizar acción/i })).toBeNull();
  });

  it("renderiza el botón habilitado y ejecuta la acción", () => {
    const onAction = vi.fn();

    render(
      <Action
        target="Sospechoso"
        action={onAction}
        isPlayerInAction={true}
        isEnabled={true}
        gameStat="waiting_for_choose_secret"
      />
    );

    const button = screen.getByRole("button", { name: /realizar acción/i });

    expect(button).toHaveClass("bg-red-900");
    expect(button).not.toBeDisabled();

    fireEvent.click(button);
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it("renderiza el botón deshabilitado cuando no está habilitado", () => {
    const onAction = vi.fn();

    render(
      <Action
        target="Sospechoso"
        action={onAction}
        isPlayerInAction={true}
        isEnabled={false}
        gameStat="waiting_for_choose_secret"
      />
    );

    const button = screen.getByRole("button", { name: /realizar acción/i });

    expect(button).toHaveClass("bg-gray-500");
    expect(button).toBeDisabled();

    fireEvent.click(button);
    expect(onAction).not.toHaveBeenCalled();
  });

  it("muestra el temporizador cuando se puede cancelar la acción", () => {
    render(
      <Action
        target="Detective"
        action={vi.fn()}
        isPlayerInAction={true}
        isEnabled={true}
        gameStat="waiting_for_cancel_action"
        remainingSeconds={12}
      />
    );

    expect(
      screen.getByText("¡Rápido! Esta acción se puede detener")
    ).toBeInTheDocument();
    expect(screen.getByText("Tiempo restante: 12s")).toBeInTheDocument();
  });

  it("no muestra el temporizador si no hay segundos restantes", () => {
    render(
      <Action
        target="Detective"
        action={vi.fn()}
        isPlayerInAction={true}
        isEnabled={true}
        gameStat="waiting_for_cancel_action"
        remainingSeconds={null}
      />
    );

    expect(
      screen.getByText("¡Rápido! Esta acción se puede detener")
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/Tiempo restante/i)
    ).not.toBeInTheDocument();
  });
});
