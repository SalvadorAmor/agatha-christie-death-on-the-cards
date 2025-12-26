import "@testing-library/jest-dom";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import ShowPrivateSecretModal from "./ShowPrivateSecretModal";
import type { Secret } from "./ShowPrivateSecretModal";

const mockSecret: Secret = {
  id: 1,
  owner: 1,
  name: "Secreto de prueba",
  revealed: false,
  type: "varios",
};
const mockSecretMurderer: Secret = {
  id: 1,
  owner: 1,
  name: "Secreto de prueba",
  revealed: false,
  type: "murderer",
};
const mockSecretAccomplice: Secret = {
  id: 1,
  owner: 1,
  name: "Secreto de prueba",
  revealed: false,
  type: "accomplice",
};

const mockSecrets = [mockSecret];

describe("ShowPrivateSecretModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("no muestra nada si open=false", () => {
    render(
      <ShowPrivateSecretModal open={false} secret={mockSecret} onClose={vi.fn()} />
    );

    expect(screen.queryByText(/secreto mostrado/i)).toBeNull();
    expect(screen.queryByText(mockSecret.name)).toBeNull();
    expect(screen.queryByRole("button", { name: /cerrar/i })).toBeNull();
  });

  it("no muestra nada si secret=null", () => {
    render(
      <ShowPrivateSecretModal open={true} secret={null} onClose={vi.fn()} />
    );

    expect(screen.queryByText(/secreto mostrado/i)).toBeNull();
    expect(screen.queryByRole("button", { name: /cerrar/i })).toBeNull();
  });

    test.each([mockSecret, mockSecretAccomplice, mockSecretMurderer])("muestra el modal con la imagen del secreto y botón cerrar", (mockedSecret) => {
    render(
      <ShowPrivateSecretModal 
        open={true} 
        secret={mockedSecret.id}  // Pasa el ID como número
        secrets={[mockedSecret]}   // Pasa el array de secrets
        onClose={vi.fn()} 
      />
    );

    expect(screen.getByText("¡Shh! Descubriste un secreto")).toBeInTheDocument();
    expect(screen.getByAltText(`Secreto: ${mockedSecret.name}`)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /cerrar/i })).toBeInTheDocument();
    });
  it("no muestra nada si secret=null", () => {
    render(
      <ShowPrivateSecretModal open={true} secret={null} onClose={vi.fn()} />
    );

    expect(screen.queryByText(/secreto mostrado/i)).toBeNull();
    expect(screen.queryByRole("button", { name: /cerrar/i })).toBeNull();
  });

  it("No encuentra el secreto", () => {
    render(
      <ShowPrivateSecretModal
        open={true}
        secret={mockSecret.id}  // Pasa el ID como número
        secrets={[]}   // Pasa el array de secrets
        onClose={vi.fn()}
      />
    );

    expect(screen.queryByText("¡Shh! Descubriste un secreto")).toBeNull();
    expect(screen.queryByAltText(`Secreto: ${mockSecret.name}`)).toBeNull();
    expect(screen.queryByRole("button", { name: /cerrar/i })).toBeNull();
  });


  it("llama a onClose cuando se hace click en el botón cerrar", () => {
    const mockOnClose = vi.fn();
    render(
      <ShowPrivateSecretModal 
        open={true} 
        secret={mockSecret.id}  // Pasa el ID
        secrets={mockSecrets}   // Pasa el array
        onClose={mockOnClose} 
      />
    );

    const closeButton = screen.getByRole("button", { name: /cerrar/i });
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });
});
