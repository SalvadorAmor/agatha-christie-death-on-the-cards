import { vi, describe, it, expect, beforeEach } from "vitest";

const mockCardSearch = vi.fn();
const mockGameRead = vi.fn();
const mockPlayerSearch = vi.fn();
const mockSecretSearch = vi.fn();

vi.mock("../../../services/CardService.ts", () => ({
  default: { search: (...args: any[]) => mockCardSearch(...args) },
}));
vi.mock("../../../services/GameService.ts", () => ({
  default: { read: (...args: any[]) => mockGameRead(...args) },
}));
vi.mock("../../../services/PlayerService.ts", () => ({
  default: { search: (...args: any[]) => mockPlayerSearch(...args) },
}));
vi.mock("../../../services/SecretService.ts", () => ({
  default: { search: (...args: any[]) => mockSecretSearch(...args) },
}));

import {
  handleUpdateCards,
  updateCards,
  updatePlayers,
  updateSecrets,
  updateGame,
} from "../Game";

describe("updateHandlers", () => {
  const mockSetCards = vi.fn();
  const mockSetDrawDeck = vi.fn();
  const mockSetDiscardDeck = vi.fn();
  const mockSetGame = vi.fn();
  const mockSetHasDiscarded = vi.fn();
  const mockSetPlayers = vi.fn();
  const mockSetSecrets = vi.fn();
  const mockSetPlayedCard = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("handleUpdateCards", () => {
    it("should fetch and update cards, decks and game", async () => {
      const gameId = 1;
      const playerId = 2;

      const myCards = [{ id: 1 }];
      const drawDeck = [{ id: 2 }];
      const discardDeck = [{ id: 3 }];
      const gameData = { id: 1, current_turn: 10 };
      const playedCardData = [{ id: 99, name: "card", turn_played: 10 }];

      mockCardSearch
        .mockResolvedValueOnce(myCards)
        .mockResolvedValueOnce(drawDeck)
        .mockResolvedValueOnce(discardDeck)
        .mockResolvedValueOnce([])
        .mockResolvedValueOnce(playedCardData);

      mockGameRead.mockResolvedValueOnce(gameData);

      await handleUpdateCards(
        gameId,
        playerId,
        mockSetCards,
        mockSetDrawDeck,
        mockSetDiscardDeck,
        mockSetGame,
        mockSetHasDiscarded,
        mockSetPlayedCard
      );

      await Promise.resolve();

      expect(mockSetCards).toHaveBeenCalledWith(myCards);
      expect(mockSetDrawDeck).toHaveBeenCalledWith(drawDeck);
      expect(mockSetDiscardDeck).toHaveBeenCalledWith(discardDeck);
      expect(mockSetGame).toHaveBeenCalledWith(gameData);
      expect(mockSetHasDiscarded).toHaveBeenCalledWith(false);
    });
  });

  describe("updateCards", () => {
    beforeEach(() => {
      mockCardSearch.mockResolvedValue([]);
      mockGameRead.mockResolvedValue({ id: 1, current_turn: 1 });
    });

    it("should call handleUpdateCards when data is array with matching game_id", async () => {
      const data = [{ game_id: 1 }];
      await updateCards(data, 1, 2, mockSetCards, mockSetDrawDeck, mockSetDiscardDeck, mockSetGame, mockSetHasDiscarded, mockSetPlayedCard);
      await Promise.resolve();
      expect(mockCardSearch).toHaveBeenCalled();
      expect(mockGameRead).toHaveBeenCalled();
    });

    it("should call handleUpdateCards when data is object with matching game_id", async () => {
      const data = { game_id: 1 };
      await updateCards(data, 1, 2, mockSetCards, mockSetDrawDeck, mockSetDiscardDeck, mockSetGame, mockSetHasDiscarded, mockSetPlayedCard);
      await Promise.resolve();
      expect(mockCardSearch).toHaveBeenCalled();
      expect(mockGameRead).toHaveBeenCalled();
    });

    it("should NOT call handleUpdateCards when game_id mismatches", async () => {
      const data = { game_id: 2 };
      await updateCards(data, 1, 2, mockSetCards, mockSetDrawDeck, mockSetDiscardDeck, mockSetGame, mockSetHasDiscarded, mockSetPlayedCard);
      expect(mockCardSearch).not.toHaveBeenCalled();
    });
  });

  describe("updatePlayers", () => {
    it("should update players when game_id matches", async () => {
      const data = { game_id: 1 };
      const players = [
        { id: 1, position: 1, avatar: 1 },
        { id: 2, position: 2, avatar: 2 },
      ];
      mockPlayerSearch.mockResolvedValueOnce(players);

      await updatePlayers(data, 1, mockSetPlayers, 1);

      expect(mockPlayerSearch).toHaveBeenCalledWith({ game_id__eq: 1 });
      expect(mockSetPlayers).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({ board_position: expect.any(Number) }),
        ])
      );
    });

    it("should NOT call PlayerService when game_id mismatches", async () => {
      await updatePlayers({ game_id: 2 }, 1, mockSetPlayers, 1);
      expect(mockPlayerSearch).not.toHaveBeenCalled();
    });
  });

  describe("updateSecrets", () => {
    it("should call SecretService.search when game_id matches", async () => {
      const secrets = [{ id: 1 }];
      mockSecretSearch.mockResolvedValueOnce(secrets);

      await updateSecrets({ game_id: 1 }, 1, mockSetSecrets);
      expect(mockSecretSearch).toHaveBeenCalledWith({ game_id__eq: 1 });
      expect(mockSetSecrets).toHaveBeenCalledWith(secrets);
    });

    it("should NOT call SecretService when game_id mismatches", async () => {
      await updateSecrets({ game_id: 2 }, 1, mockSetSecrets);
      expect(mockSecretSearch).not.toHaveBeenCalled();
    });
  });

  describe("updateGame", () => {
    it("should set game if id matches", () => {
      const data = { id: 1 };
      updateGame(data, 1, mockSetGame);
      expect(mockSetGame).toHaveBeenCalledWith(data);
    });

    it("should NOT set game if id mismatches", () => {
      const data = { id: 2 };
      updateGame(data, 1, mockSetGame);
      expect(mockSetGame).not.toHaveBeenCalled();
    });
  });
});
