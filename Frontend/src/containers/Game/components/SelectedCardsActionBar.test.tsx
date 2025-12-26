import { vi, describe, it, expect, beforeEach } from "vitest";

vi.mock("../../../services/EventTableService.ts", () => ({
  default: {
    searchInTable: vi.fn(),
    cancelAction: vi.fn(),
  },
}));

import EventTableService from "../../../services/EventTableService.ts";


vi.mock("../../../services/SetService.ts", () => ({
  default: {
    search: vi.fn().mockResolvedValue([]),
    create: vi.fn().mockResolvedValue(true),
    update: vi.fn().mockResolvedValue({
      id: 202,
      name: "otro-detective",
      card_type: "detective",
    }),
  },
}));

vi.mock("../../../services/CardService.ts", () => ({
  default: {
    playEvent: vi.fn(() => Promise.resolve("ok")),
    bulkUpdate: vi.fn(() => Promise.resolve("ok")),
  },
}));

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import SelectedCardsActionBar, { Modal } from "./SelectedCardsActionBar";
import CardService from "../../../services/CardService.ts";
import SetService from "../../../services/SetService.ts";

describe("SelectedCardsActionBar full coverage", () => {
  const mockPlayer = { id: 1, token: "abc", name: "Player1", avatar: "avatar.png" };
  const mockGame = { id: 1, name: "Game1", current_turn: 5 };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders nothing when no selected cards", () => {
    const setCards = vi.fn();
    const setSelectedCards = vi.fn();
    const setHasDiscarded = vi.fn();
    const cards = [
      { id: "10", card_type: "event", name: "EventCard" },
      { id: "11", card_type: "detective", name: "DetectiveCard" },
    ];

    const { container } = render(
      <SelectedCardsActionBar
        selectedCards={[]}
        cards={cards}
        myPlayer={mockPlayer}
        game={mockGame}
        setCards={setCards}
        setSelectedCards={setSelectedCards}
        setHasDiscarded={setHasDiscarded}
      />
    );

    expect(container.innerHTML).toBe("");
    expect(screen.queryByText("Descartar cartas")).toBeNull();
  });

  it("playEvent is called when one event card selected and player+game exist", async () => {
    const setCards = vi.fn();
    const setSelectedCards = vi.fn();
    const setHasDiscarded = vi.fn();
    const cards = [{ id: "10", card_type: "event", name: "EventCard" }];

    render(
      <SelectedCardsActionBar
        selectedCards={["10"]}
        cards={cards}
        myPlayer={mockPlayer}
        game={mockGame}
        setCards={setCards}
        setSelectedCards={setSelectedCards}
        setHasDiscarded={setHasDiscarded}
      />
    );

    const playBtn = screen.getByText("Jugar evento");
    await fireEvent.click(playBtn);

    expect(CardService.playEvent).toHaveBeenCalledTimes(1);
    expect(CardService.playEvent).toHaveBeenCalledWith("10", mockPlayer.token);
  });

  it("playEvent does nothing if missing player or wrong selection length", async () => {
    const setCards = vi.fn();
    const setSelectedCards = vi.fn();
    const setHasDiscarded = vi.fn();

    // no player
    render(
      <SelectedCardsActionBar
        selectedCards={["10"]}
        cards={[{ id: "10", card_type: "detective", name: "EventCard" }]}
        myPlayer={null}
        game={mockGame}
        setCards={setCards}
        setSelectedCards={setSelectedCards}
        setHasDiscarded={setHasDiscarded}
      />
    );
    expect(screen.queryByText("Jugar evento")).toBeNull();

    // wrong selection count (2)
    render(
      <SelectedCardsActionBar
        selectedCards={["10", "20"]}
        cards={[
          { id: "10", card_type: "event", name: "EventCard" },
          { id: "20", card_type: "event", name: "EventCard2" },
        ]}
        myPlayer={mockPlayer}
        game={mockGame}
        setCards={setCards}
        setSelectedCards={setSelectedCards}
        setHasDiscarded={setHasDiscarded}
      />
    );
    expect(screen.queryByText("Jugar evento")).toBeNull();
    expect(CardService.playEvent).not.toHaveBeenCalled();
  });

  it("discard calls CardService.bulkUpdate, clears selection and sets hasDiscarded on success", async () => {
    const setCards = vi.fn();
    const setSelectedCards = vi.fn();
    const setHasDiscarded = vi.fn();
    const cards = [{ id: "11", card_type: "detective", name: "DetectiveCard" }];

    render(
      <SelectedCardsActionBar
        selectedCards={["11"]}
        cards={cards}
        myPlayer={mockPlayer}
        game={mockGame}
        setCards={setCards}
        setSelectedCards={setSelectedCards}
        setHasDiscarded={setHasDiscarded}
      />
    );

    const discardBtn = screen.getByText("Descartar cartas");
    await fireEvent.click(discardBtn);

    expect(CardService.bulkUpdate).toHaveBeenCalledTimes(1);
    expect(CardService.bulkUpdate).toHaveBeenCalledWith(["11"], {
      turn_discarded: mockGame.current_turn,
      token: mockPlayer.token,
    });

    expect(setSelectedCards).toHaveBeenCalledWith([]);
    expect(setHasDiscarded).toHaveBeenCalledWith(true);
  });

  it("discard logs error when bulkUpdate rejects and does not clear selection", async () => {
    const setCards = vi.fn();
    const setSelectedCards = vi.fn();
    const setHasDiscarded = vi.fn();
    const cards = [{ id: "11", card_type: "detective", name: "DetectiveCard" }];

    (CardService.bulkUpdate as any).mockImplementationOnce(() => Promise.reject(new Error("fail")));
    const consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <SelectedCardsActionBar
        selectedCards={["11"]}
        cards={cards}
        myPlayer={mockPlayer}
        game={mockGame}
        setCards={setCards}
        setSelectedCards={setSelectedCards}
        setHasDiscarded={setHasDiscarded}
      />
    );

    const discardBtn = screen.getByText("Descartar cartas");
    await fireEvent.click(discardBtn);

    expect(CardService.bulkUpdate).toHaveBeenCalled();
    expect(consoleErrorSpy).toHaveBeenCalled();
    expect(setSelectedCards).not.toHaveBeenCalledWith([]);
    consoleErrorSpy.mockRestore();
  });

  it("invalid detective set abre modal y se puede cerrar", async () => {
    const setCards = vi.fn();
    const setSelectedCards = vi.fn();
    const setHasDiscarded = vi.fn();

    const cards = [{ id: "d1", card_type: "detective", name: "hercule-poirot" }];
    render(
      <SelectedCardsActionBar
        selectedCards={["d1"]}
        cards={cards}
        myPlayer={mockPlayer}
        game={mockGame}
        setCards={setCards}
        setSelectedCards={setSelectedCards}
        setHasDiscarded={setHasDiscarded}
      />
    );

    const jugarSetBtn = screen.getByText("Jugar set");
    await fireEvent.click(jugarSetBtn);

    expect(screen.getByText("Set Inválido")).toBeInTheDocument();
    expect(screen.getByText(/no forman un set de detective valido/i)).toBeInTheDocument();

    await fireEvent.click(screen.getByText("Entendido"));
    expect(screen.queryByText("Set Inválido")).toBeNull();
  });

  it("valid detective set -> SetService.create true => filtra cartas y limpia selección", async () => {
    const setCards = vi.fn();
    const setSelectedCards = vi.fn();
    const setHasDiscarded = vi.fn();

    const cards = [
      { id: "a", card_type: "detective", name: "hercule-poirot" },
      { id: "b", card_type: "detective", name: "harley-quin-wildcard" },
      { id: "c", card_type: "detective", name: "hercule-poirot" },
      { id: "z", card_type: "detective", name: "other" },
    ];

    (SetService.create as any).mockImplementationOnce(() => Promise.resolve(true));

    render(
      <SelectedCardsActionBar
        selectedCards={["a", "b", "c"]}
        cards={cards}
        myPlayer={mockPlayer}
        game={mockGame}
        setCards={setCards}
        setSelectedCards={setSelectedCards}
        setHasDiscarded={setHasDiscarded}
      />
    );

    await fireEvent.click(screen.getByText("Jugar set"));

    expect(SetService.create).toHaveBeenCalledWith({ detectives: ["a", "b", "c"] });
    const fn = setCards.mock.calls[0][0];
    expect(fn(cards)).toEqual([{ id: "z", card_type: "detective", name: "other" }]);
    expect(setSelectedCards).toHaveBeenCalledWith([]);
  });

describe("Agregar al set beresford", () => {
  const myPlayer: any = { id: 1, token: "jim", name: "Jim", avatar: "avatardejim.png" };
  const game: any = { id: 10, name: "jim", current_turn: 7 };

  const mkProps = () => ({
    selectedCards: [] as number[],
    cards: [] as any[],
    myPlayer,
    game,
    setCards: vi.fn(),
    setSelectedCards: vi.fn(),
    setHasDiscarded: vi.fn(),
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("isCompatibleAdd retorna true cuando se agrega tuppence a un set con tommy", async () => {
   (SetService as any).search.mockResolvedValueOnce([
      { 
        id: 99, 
        owner: myPlayer.id, 
        detectives: [
          { id: 1, name: "tommy-beresford" },
          { id: 2, name: "tommy-beresford" }
        ] 
      },
    ]);
    (SetService as any).update.mockResolvedValueOnce({ ok: true });

    const props = mkProps();
     props.cards = [
      { id: 101, name: "tuppence-beresford", card_type: "detective" },
      { id: 202, name: "otro-detective", card_type: "detective" },
    ];
    props.selectedCards = [101];

    render(<SelectedCardsActionBar {...props} />);

    const button = await screen.findByText("Agregar al set");
    expect(button).toBeInTheDocument();

    await fireEvent.click(button);

    expect(SetService.update).toHaveBeenCalledWith(99, {
      add_card: 101,
      token: "jim",
    });
  });

  it("isCompatibleAdd retorna true cuando se agrega tommy a un set con tuppence", async () => {
    // Set existente tiene tuppence-beresford
    (SetService as any).search.mockResolvedValueOnce([
      { 
        id: 99, 
        owner: myPlayer.id, 
        detectives: [
          { id: 1, name: "tuppence-beresford" },
          { id: 2, name: "tuppence-beresford" }
        ] 
      },
    ]);
    (SetService as any).update.mockResolvedValueOnce({ ok: true });

    const props = mkProps();
    // Carta a agregar es tommy-beresford
    props.cards = [
      { id: 101, name: "tommy-beresford", card_type: "detective" },
      { id: 202, name: "otro-detective", card_type: "detective" },
    ];
    props.selectedCards = [101];

    render(<SelectedCardsActionBar {...props} />);

    const button = await screen.findByText("Agregar al set");
    expect(button).toBeInTheDocument();

    await fireEvent.click(button);

    expect(SetService.update).toHaveBeenCalledWith(99, {
      add_card: 101,
      token: "jim",
    });
  });

  it("isCompatibleAdd retorna false cuando se agrega otro detective a un set con tommy", async () => {
    (SetService as any).search.mockResolvedValueOnce([
      { 
        id: 99, 
        owner: myPlayer.id, 
        detectives: [{ id: 1, name: "tommy-beresford" }] 
      },
    ]);

    const props = mkProps();
    props.cards = [{ id: 101, name: "hercule-poirot", card_type: "detective" }];
    props.selectedCards = [101];

    render(<SelectedCardsActionBar {...props} />);
    
      expect(screen.queryByText("Agregar al set")).toBeNull();
  });
});
  
  it("valid detective set pero SetService.create falsy -> no filtra, igual limpia selección", async () => {
    const setCards = vi.fn();
    const setSelectedCards = vi.fn();
    const setHasDiscarded = vi.fn();

    const cards = [
      { id: "a", card_type: "detective", name: "hercule-poirot" },
      { id: "b", card_type: "detective", name: "harley-quin-wildcard" },
      { id: "c", card_type: "detective", name: "hercule-poirot" },
    ];

    (SetService.create as any).mockImplementationOnce(() => Promise.resolve(false));

    render(
      <SelectedCardsActionBar
        selectedCards={["a", "b", "c"]}
        cards={cards}
        myPlayer={mockPlayer}
        game={mockGame}
        setCards={setCards}
        setSelectedCards={setSelectedCards}
        setHasDiscarded={setHasDiscarded}
      />
    );

    await fireEvent.click(screen.getByText("Jugar set"));
    expect(SetService.create).toHaveBeenCalled();
    expect(setCards).not.toHaveBeenCalled();
    expect(setSelectedCards).toHaveBeenCalledWith([]);
  });

  it("caso especial tommy+tuppence válido", async () => {
    const setCards = vi.fn();
    const setSelectedCards = vi.fn();
    const setHasDiscarded = vi.fn();

    const cards = [
      { id: "t1", card_type: "detective", name: "tommy-beresford" },
      { id: "t2", card_type: "detective", name: "tuppence-beresford" },
      { id: "x", card_type: "detective", name: "other" },
    ];

    (SetService.create as any).mockImplementationOnce(() => Promise.resolve(true));

    render(
      <SelectedCardsActionBar
        selectedCards={["t1", "t2"]}
        cards={cards}
        myPlayer={mockPlayer}
        game={mockGame}
        setCards={setCards}
        setSelectedCards={setSelectedCards}
        setHasDiscarded={setHasDiscarded}
      />
    );

    await fireEvent.click(screen.getByText("Jugar set"));

    expect(SetService.create).toHaveBeenCalledWith({ detectives: ["t1", "t2"] });
    const fn = setCards.mock.calls[0][0];
    expect(fn(cards)).toEqual([{ id: "x", card_type: "detective", name: "other" }]);
    expect(setSelectedCards).toHaveBeenCalledWith([]);
  });

  it("Modal renderiza estados y callbacks", async () => {
    const onClose = vi.fn();
    const { rerender } = render(<Modal message="hello" isSuccess={false} onClose={onClose} />);
    expect(screen.getByText("Set Inválido")).toBeInTheDocument();
    await fireEvent.click(screen.getByText("Entendido"));
    expect(onClose).toHaveBeenCalledTimes(1);

    rerender(<Modal message="ok" isSuccess={true} onClose={onClose} />);
    expect(screen.getByText("Set Válido")).toBeInTheDocument();
  });
});

describe("Agregar al set", () => {
  const myPlayer: any = { id: 1, token: "jiminteamo", name: "Jimin", avatar: "avatardejimin.png" };
  const game: any = { id: 10, name: "jimingame", current_turn: 7 };

  const mkProps = () => ({
    selectedCards: [] as number[],
    cards: [] as any[],
    myPlayer,
    game,
    setCards: vi.fn(),
    setSelectedCards: vi.fn(),
    setHasDiscarded: vi.fn(),
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("muestra el boton y ejecuta el update", async () => {
  (SetService as any).search.mockResolvedValueOnce([
    { id: 99, owner: myPlayer.id, detectives: [{ id: 1, name: "lady-eileen-bundle-brent" }] },
  ]);
  (SetService as any).update.mockResolvedValueOnce({ ok: true });

  const props = mkProps();
  props.cards = [
    { id: 101, name: "lady-eileen-bundle-brent", card_type: "detective" },
    { id: 202, name: "otro-detective", card_type: "detective" },
  ];
  props.selectedCards = [101];

  render(<SelectedCardsActionBar {...props} />);

  // esperamos a que aparezca el botón
  const button = await screen.findByText("Agregar al set");
  expect(button).toBeInTheDocument();

  // clic para ejecutar la acción
  await fireEvent.click(button);

  // verificamos que se haya hecho la llamada al update
  expect(SetService.update).toHaveBeenCalledWith(99, {
    add_card: 101,
    token: "jiminteamo",
  });

  // esperamos que se actualicen las cartas y se limpie la selección
  await waitFor(() => {
    expect(props.setCards).toHaveBeenCalled();
    expect(props.setSelectedCards).toHaveBeenCalledWith([]);
  });

  // comprobamos que se filtraron las cartas correctamente
  const setArg = props.setCards.mock.calls[0][0];

  if (typeof setArg === "function") {
    const newCards = setArg(props.cards);
    expect(newCards).toEqual([{ id: 202, name: "otro-detective", card_type: "detective" }]);
  } else {
    // si el componente llama setCards directamente con un array
    expect(setArg).toEqual([{ id: 202, name: "otro-detective", card_type: "detective" }]);
  }
});

  it("no muestra boton si la carta es un comodín", async () => {
    (SetService as any).search.mockResolvedValueOnce([
      { id: 99, owner: myPlayer.id, detectives: [{ id: 1, name: "lady-eileen-bundle-brent" }] },
    ]);

    const props = mkProps();
    props.cards = [{ id: 101, name: "harley-quin-wildcard", card_type: "detective" }];
    props.selectedCards = [101];

    render(<SelectedCardsActionBar {...props} />);
    expect(screen.queryByText("Agregar al set")).toBeNull();
  });

  it("no muestra boton si no hay sets compatibles", async () => {
    (SetService as any).search.mockResolvedValueOnce([
      { id: 99, owner: myPlayer.id, detectives: [{ id: 1, name: "hercule-poirot" }] },
    ]);

    const props = mkProps();
    props.cards = [{ id: 101, name: "lady-eileen-bundle-brent", card_type: "detective" }];
    props.selectedCards = [101];

    render(<SelectedCardsActionBar {...props} />);
    expect(screen.queryByText("Agregar al set")).toBeNull();
  });
});
const mockPlayer = { id: 1, token: "tok123", name: "Player1", avatar: "a.png" };
const mockGame = { id: 10, current_turn: 3, player_in_action: 1, status: "waiting_for_cancel_action" };

describe("handleCancelAction dentro de SelectedCardsActionBar", () => {
  const mkProps = () => ({
    selectedCards: [99],
    cards: [
  {
    id: 99,
    name: "not-so-fast",
    card_type: "event",
    owner: 1,
    discarded_order: null,
    turn_played: null,
  },
],
    myPlayer: mockPlayer,
    game: mockGame,
    setCards: vi.fn(),
    setSelectedCards: vi.fn(),
    setHasDiscarded: vi.fn(),
    isInSocialDisgrace: false,
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("no hace nada si no hay game", async () => {
    const props = mkProps();
    props.game = null as any;

    render(<SelectedCardsActionBar {...props} />);

    expect(screen.queryByText("Cancelar acción")).toBeNull();
  });

  it("ejecuta handle cancel action", async () => {
    const props = mkProps();

    (EventTableService as any).searchInTable.mockResolvedValueOnce([
      { id: 555, action: "to_cancel", completed_action: false },
    ]);
    (EventTableService as any).cancelAction.mockResolvedValueOnce({ ok: true });

    render(<SelectedCardsActionBar {...props} />);

    const button = screen.getByText("Cancelar acción");
    expect(button).toBeInTheDocument();

    await fireEvent.click(button);

    await waitFor(() => {
      expect(EventTableService.searchInTable).toHaveBeenCalledWith({
        game_id__eq: mockGame.id,
        turn_played__eq: mockGame.current_turn,
        action__eq: "to_cancel",
        completed_action__eq: false,
      });

      expect(EventTableService.cancelAction).toHaveBeenCalledWith(
        555,
        99,
        mockPlayer.token
      );

      expect(props.setSelectedCards).toHaveBeenCalledWith([]);
    });
  });

  it("si la func search in table devuelve vacio no intenta cancelar nada", async () => {
    const props = mkProps();
    (EventTableService as any).searchInTable.mockResolvedValueOnce([]);
    (EventTableService as any).cancelAction.mockResolvedValueOnce({ ok: true });

    render(<SelectedCardsActionBar {...props} />);
    await fireEvent.click(screen.getByText("Cancelar acción"));

    await waitFor(() => {
      expect(EventTableService.searchInTable).toHaveBeenCalled();
      expect(EventTableService.cancelAction).not.toHaveBeenCalled();
      expect(props.setSelectedCards).toHaveBeenCalledWith([]);
    });
  });
});

describe("Ariadne Oliver", () => {
  const myPlayer: any = { id: 42, token: "jimin", name: "sara", avatar: "a.png" };
  const game: any = { id: 100, name: "g", current_turn: 1, player_in_action: 42, status: "turn_start" };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("no muestra 'Jugar set' si la selección incluye ariadne-oliver", () => {
    const props = {
      selectedCards: [1, 2],
      cards: [
        { id: 1, card_type: "detective", name: "ariadne-oliver" },
        { id: 2, card_type: "detective", name: "hercule-poirot" },
      ],
      myPlayer,
      game,
      setCards: vi.fn(),
      setSelectedCards: vi.fn(),
      setHasDiscarded: vi.fn(),
      isInSocialDisgrace: false,
    };

    render(<SelectedCardsActionBar {...props} />);

    expect(screen.queryByText("Jugar set")).toBeNull();
  });

  it("no muestra 'Agregar al set' cuando la carta seleccionada es ariadne-oliver", async () => {
    (SetService as any).search
      .mockResolvedValueOnce([
        { id: 9, owner: myPlayer.id, detectives: [{ id: 77, name: "hercule-poirot" }] },
      ])
      .mockResolvedValueOnce([]);

    const props = {
      selectedCards: [3],
      cards: [{ id: 3, card_type: "detective", name: "ariadne-oliver" }],
      myPlayer,
      game,
      setCards: vi.fn(),
      setSelectedCards: vi.fn(),
      setHasDiscarded: vi.fn(),
      isInSocialDisgrace: false,
    };

    render(<SelectedCardsActionBar {...props} />);
    expect(screen.queryByText("Agregar al set")).toBeNull();
  });

  it("muestra 'Jugar carta' para Ariadne y llama a playEvent al click", async () => {
    const props = {
      selectedCards: [5],
      cards: [{ id: 5, card_type: "detective", name: "ariadne-oliver" }],
      myPlayer,
      game,
      setCards: vi.fn(),
      setSelectedCards: vi.fn(),
      setHasDiscarded: vi.fn(),
      isInSocialDisgrace: false,
    };

    render(<SelectedCardsActionBar {...props} />);

    const btn = screen.getByText("Jugar carta");
    expect(btn).toBeInTheDocument();

    await fireEvent.click(btn);

    expect(CardService.playEvent).toHaveBeenCalledTimes(1);
    expect(CardService.playEvent).toHaveBeenCalledWith(5, myPlayer.token);
  });
});