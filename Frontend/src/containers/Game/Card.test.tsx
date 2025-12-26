import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Card, DiscardedCard, DrawCard } from "./components/Card";

describe("Card components", () => {
  it("renderiza Card con la imagen correcta", () => {
    render(<Card source="CARTA" />);
    const img = screen.getByAltText("CARTA");

    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("src", "/images/cards/CARTA.png");
    expect(img).toHaveClass("rounded-xl");
  });

  it("renderiza DiscardedCard con la imagen correcta", () => {
    render(<DiscardedCard source="DESCARTADA" />);
    const img = screen.getByAltText("carta_descartada");

    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("src", "/images/cards/DESCARTADA.png");
    expect(img).toHaveClass("rounded-xl");
  });
});
