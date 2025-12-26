import React, { useEffect } from "react";
import { render, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import useLookIntoTheAshes from "./useLookIntoTheAshes";

// mocks
const mockCardSearch = vi.fn();
const mockPlayWithTargets = vi.fn();
vi.mock("../services/CardService", () => ({
  default: {
    search: (...args: any[]) => mockCardSearch(...args),
    playCardWithTargets: (...args: any[]) => mockPlayWithTargets(...args),
  },
}));

type Params = { game: any | null;
             myPlayer: any | null;
             discardDeck: any[]
            };
type HookAPI = ReturnType<typeof useLookIntoTheAshes>;

function HookHost({ params, onReady }: { params: Params; onReady: (api: HookAPI) => void }) {
    
  const api = useLookIntoTheAshes(params);
  useEffect(() => { onReady(api); }, [api, onReady]);
  return null;
}

const baseGame = {
  id: 1,
  status: "waiting_for_choose_discarded",
  player_in_action: 10,
  current_turn: 5,
};
const me = { id: 10, token: "jiminteamo" };

describe("useLookIntoTheAshes hook", () => {
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

  it("abre y arma el top 5", async () => {
    let api!: HookAPI;
    const discardDeck = [
      { id: 10, name: "a" },
      { id: 11, name: "b" },
      { id: 12, name: "c" },
      { id: 13, name: "d" },
      { id: 14, name: "e" },
      { id: 15, name: "f" },
      { id: 16, name: "g" },
    ];

    render(
      <HookHost
        params={{ game: baseGame, myPlayer: me, discardDeck }}
        onReady={(x) => (api = x)}
      />
    );

    await waitFor(() => {
      expect(api.open).toBe(true);
      expect(api.cards.map((c) => c.id)).toEqual([12, 13, 14, 15, 16]);
    });
    expect(mockCardSearch).not.toHaveBeenCalled();
  });

  it("confirm(): busca la carta jugada", async () => {
    let api!: HookAPI;
    mockCardSearch.mockResolvedValueOnce([
      { id: 999, name: "look-into-the-ashes", type: "event" },
    ]);

    render(
      <HookHost
        params={{
          game: baseGame,
          myPlayer: me,
          discardDeck: [
            { id: 70, name: "x" },
            { id: 71, name: "y" },
            { id: 72, name: "z" },
            { id: 73, name: "w" },
            { id: 74, name: "v" },
            { id: 75, name: "u" },
          ],
        }}
        onReady={(x) => (api = x)}
      />
    );

    await waitFor(() => expect(api.open).toBe(true));

    await api.confirm(73);

    expect(mockCardSearch).toHaveBeenCalledWith({
      game_id__eq: 1,
      turn_played__eq: 5,
    });
    expect(mockPlayWithTargets).toHaveBeenCalledWith(999, "jiminteamo", {
      target_players: [],
      target_secrets: [],
      target_cards: [73],
      target_sets: [],
    });

    await waitFor(() => {
      expect(api.open).toBe(false);
      expect(api.cards).toEqual([]);
    });
  });

  it("confirm(): si no hay carta jugada", async () => {
    let api!: HookAPI;
    mockCardSearch.mockResolvedValueOnce([]);

    render(
      <HookHost
        params={{ game: baseGame, myPlayer: me, discardDeck: [{ id: 1, name: "x" }] }}
        onReady={(x) => (api = x)}
      />
    );

    await api.confirm(1);
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

it("if !eventCard", async () => {
  let api!: HookAPI;
  mockCardSearch.mockResolvedValueOnce([]);

  render(
    <HookHost
      params={{ game: baseGame, myPlayer: me, discardDeck: [{ id: 1, name: "x" }] }}
      onReady={(x) => (api = x)}
    />
  );

  await api.confirm(1);
  expect(mockPlayWithTargets).not.toHaveBeenCalled();
});

it("early return", async () => {
  let api!: HookAPI;
  render(
    <HookHost params={{ game: null, myPlayer: null, discardDeck: [] }} onReady={(x) => (api = x)} />
  );
  await api.confirm(999);
  expect(mockCardSearch).not.toHaveBeenCalled();
});

});
