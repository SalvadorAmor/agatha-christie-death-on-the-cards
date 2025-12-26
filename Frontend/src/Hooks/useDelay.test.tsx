import React, { useEffect } from "react";
import { render, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import useDelay from "./useDelay";

// mocks
const mockCardSearch = vi.fn();
const mockPlayWithTargets = vi.fn();

vi.mock("../services/CardService", () => ({
  default: {
    search: (...args: any[]) => mockCardSearch(...args),
    playCardWithTargets: (...args: any[]) => mockPlayWithTargets(...args),
  },
}));

type Params = {
  game: any | null;
  myPlayer: any | null;
  discardDeck: any[];
};
type HookAPI = ReturnType<typeof useDelay>;

function HookHost({
  params,
  onReady,
}: {
  params: Params;
  onReady: (api: HookAPI) => void;
}) {
  const api = useDelay(params);
  useEffect(() => {
    onReady(api);
  }, [api, onReady]);
  return null;
}

const baseGame = {
  id: 1,
  status: "waiting_for_order_discard",
  player_in_action: 10,
  current_turn: 5,
};
const me = { id: 10, token: "jaz" };

describe("useDelay hook", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("no abre si no te toca", async () => {
    let api!: HookAPI;

    render(
      <HookHost
        params={{
          game: { ...baseGame, status: "turn_start" },
          myPlayer: me,
          discardDeck: [{ id: 1, name: "x" }],
        }}
        onReady={(x) => (api = x)}
      />
    );

    await waitFor(() => {
      expect(api.open).toBe(false);
      expect(api.cards).toEqual([]);
    });
  });

  it("abre y muestra las 5 cartas del top del descarte", async () => {
    let api!: HookAPI;
    const discardDeck = [
      { id: 1, name: "a" },
      { id: 2, name: "b" },
      { id: 3, name: "c" },
      { id: 4, name: "d" },
      { id: 5, name: "e" },
      { id: 6, name: "f" },
      { id: 7, name: "g" },
    ];

    render(
      <HookHost
        params={{ game: baseGame, myPlayer: me, discardDeck }}
        onReady={(x) => (api = x)}
      />
    );

    await waitFor(() => {
      expect(api.open).toBe(true);
      expect(api.cards.map((c) => c.id)).toEqual([3, 4, 5, 6, 7]);
    });

    expect(mockCardSearch).not.toHaveBeenCalled();
  });

  it("confirm(): busca la carta jugada y llama a playCardWithTargets", async () => {
    let api!: HookAPI;
    mockCardSearch.mockResolvedValueOnce([
      { id: 999, name: "delay", type: "event" },
    ]);

    render(
      <HookHost
        params={{
          game: baseGame,
          myPlayer: me,
          discardDeck: [
            { id: 10, name: "x" },
            { id: 11, name: "y" },
            { id: 12, name: "z" },
            { id: 13, name: "w" },
            { id: 14, name: "v" },
            { id: 15, name: "u" },
          ],
        }}
        onReady={(x) => (api = x)}
      />
    );

    await waitFor(() => expect(api.open).toBe(true));

    await api.confirm([11, 12, 13, 14, 15]);

    expect(mockCardSearch).toHaveBeenCalledWith({
      game_id__eq: 1,
      turn_played__eq: 5,
    });

    expect(mockPlayWithTargets).toHaveBeenCalledWith(999, "jaz", {
      target_players: [],
      target_secrets: [],
      target_cards: [11, 12, 13, 14, 15],
      target_sets: [],
    });

    await waitFor(() => {
      expect(api.open).toBe(false); //se cerro el modal
      expect(api.cards).toEqual([]);
    });
  });

  it("confirm(): si no hay carta jugada, no hace nada", async () => {
    let api!: HookAPI;
    mockCardSearch.mockResolvedValueOnce([]);

    render(
      <HookHost
        params={{
          game: baseGame,
          myPlayer: me,
          discardDeck: [{ id: 1, name: "x" }],
        }}
        onReady={(x) => (api = x)}
      />
    );

    await api.confirm([1]);
    expect(mockPlayWithTargets).not.toHaveBeenCalled();
  });

  it("early return: si falta game o myPlayer", async () => {
    let api!: HookAPI;

    render(
      <HookHost
        params={{ game: null, myPlayer: null, discardDeck: [] }}
        onReady={(x) => (api = x)}
      />
    );

    await api.confirm([123]);
    expect(mockCardSearch).not.toHaveBeenCalled();
    expect(mockPlayWithTargets).not.toHaveBeenCalled();
  });

  it("close(): cierra el modal", async () => {
    let api!: HookAPI;

    render(
      <HookHost
        params={{
          game: baseGame,
          myPlayer: me,
          discardDeck: [
            { id: 90, name: "a" },
            { id: 91, name: "b" },
            { id: 92, name: "c" },
            { id: 93, name: "d" },
            { id: 94, name: "e" },
          ],
        }}
        onReady={(x) => (api = x)}
      />
    );

    await waitFor(() => expect(api.open).toBe(true));
    api.close();
    await waitFor(() => expect(api.open).toBe(false));
  });
});
