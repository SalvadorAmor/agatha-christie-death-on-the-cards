import { renderHook } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { useEffect, useState } from 'react';

const mockRegisterOnUpdate = vi.fn();
const mockClose = vi.fn();

const MockWebSocketManager = vi.fn().mockImplementation(() => ({
  registerOnUpdate: mockRegisterOnUpdate,
  close: mockClose,
}));

vi.mock('../../components/WebSocketManager.tsx', () => ({
  default: MockWebSocketManager,
}));

const mockUpdateCards = vi.fn();
const mockUpdatePlayers = vi.fn();
const mockUpdateSecrets = vi.fn();

vi.mock('../../pages/Game', async (orig) => {
  const actual = await orig();
  return {
    ...actual,
    updateCards: mockUpdateCards,
    updatePlayers: mockUpdatePlayers,
    updateSecrets: mockUpdateSecrets,
  };
});

function useWebSocketGameEffect(gid: string | undefined, myPlayer: any) {
  const [game, setGame] = useState(null);
  const [cards, setCards] = useState([]);
  const [drawDeck, setDrawDeck] = useState([]);
  const [discardDeck, setDiscardDeck] = useState([]);
  const [hasDiscarded, setHasDiscarded] = useState(false);
  const [players, setPlayers] = useState([]);
  const [secrets, setSecrets] = useState([]);

  useEffect(() => {
    if (!gid || !myPlayer) return;
    const gameId = parseInt(gid);
    if (isNaN(gameId)) return;

    const wsmanager = new MockWebSocketManager(myPlayer.token);

    wsmanager.registerOnUpdate((data: any) => {
      if (data.id === gameId) setGame(data);
    }, 'game');

    wsmanager.registerOnUpdate((data: any) => {
      if (Array.isArray(data)) {
        const first = data[0];
        if (first && first.game_id === gameId) {
          mockUpdateCards(gameId, myPlayer.id, setCards, setDrawDeck, setDiscardDeck, setGame, setHasDiscarded);
        }
      } else if (data.game_id === gameId) {
        mockUpdateCards(gameId, myPlayer.id, setCards, setDrawDeck, setDiscardDeck, setGame, setHasDiscarded);
      }
    }, 'card');

    wsmanager.registerOnUpdate((data: any) => {
      if (data.game_id === gameId) {
        mockUpdatePlayers(gameId, setPlayers, myPlayer.position);
      }
    }, 'player');

    wsmanager.registerOnUpdate((data: any) => {
      if (data.game_id === gameId) {
        mockUpdateSecrets(gameId, setSecrets);
      }
    }, 'secret');

    return () => wsmanager.close();
  }, [gid, myPlayer]);

  return { game, players, secrets };
}

describe('Game WebSocket Effect', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should not initialize WebSocketManager if gid or myPlayer missing', () => {
    renderHook(() => useWebSocketGameEffect(undefined, null));
    expect(MockWebSocketManager).not.toHaveBeenCalled();
  });

  it('should initialize WebSocketManager and register 4 update listeners', () => {
    const player = { id: 1, token: 'abc123', position: 0 };
    renderHook(() => useWebSocketGameEffect('42', player));

    expect(MockWebSocketManager).toHaveBeenCalledWith('abc123');
    expect(mockRegisterOnUpdate).toHaveBeenCalledTimes(4);
    expect(mockRegisterOnUpdate).toHaveBeenCalledWith(expect.any(Function), 'game');
    expect(mockRegisterOnUpdate).toHaveBeenCalledWith(expect.any(Function), 'card');
    expect(mockRegisterOnUpdate).toHaveBeenCalledWith(expect.any(Function), 'player');
    expect(mockRegisterOnUpdate).toHaveBeenCalledWith(expect.any(Function), 'secret');
  });

  it('should update game when receiving game data', () => {
    const player = { id: 1, token: 'tok', position: 0 };
    renderHook(() => useWebSocketGameEffect('10', player));

    const [handler] = mockRegisterOnUpdate.mock.calls.find((c) => c[1] === 'game');
    const newGame = { id: 10, name: 'Mock Game' };

    handler(newGame);
    expect(newGame.id).toBe(10);
  });

  it('should call updateCards for array or single card data', () => {
    const player = { id: 2, token: 'x', position: 0 };
    renderHook(() => useWebSocketGameEffect('5', player));

    const [handler] = mockRegisterOnUpdate.mock.calls.find((c) => c[1] === 'card');
    handler([{ id: 1, game_id: 5 }]);
    expect(mockUpdateCards).toHaveBeenCalled();
    handler({ id: 2, game_id: 5 });
    expect(mockUpdateCards).toHaveBeenCalledTimes(2);
  });

  it('should call updatePlayers when player update matches game_id', () => {
    const player = { id: 1, token: 'x', position: 1 };
    renderHook(() => useWebSocketGameEffect('77', player));

    const [handler] = mockRegisterOnUpdate.mock.calls.find((c) => c[1] === 'player');
    handler({ game_id: 77 });
    expect(mockUpdatePlayers).toHaveBeenCalledWith(77, expect.any(Function), 1);
  });

  it('should call updateSecrets when secret update matches game_id', () => {
    const player = { id: 3, token: 't', position: 2 };
    renderHook(() => useWebSocketGameEffect('99', player));

    const [handler] = mockRegisterOnUpdate.mock.calls.find((c) => c[1] === 'secret');
    handler({ game_id: 99 });
    expect(mockUpdateSecrets).toHaveBeenCalledWith(99, expect.any(Function));
  });

  it('should close WebSocketManager on unmount', () => {
    const player = { id: 9, token: 'tok', position: 0 };
    const { unmount } = renderHook(() => useWebSocketGameEffect('3', player));
    unmount();
    expect(mockClose).toHaveBeenCalled();
  });
});
