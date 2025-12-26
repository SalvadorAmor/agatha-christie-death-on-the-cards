import '@testing-library/jest-dom/vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import OpponentPlayerSets from './OpponentPlayerSets';
import type { Game } from '../containers/Game/Game';

const mockSearch = vi.fn();

vi.mock('../services/SetService', () => ({
  default: {
    search: (...args: any[]) => mockSearch(...args),
  },
}));

const mockGame: Game = {
  id: 1,
  status: 'turn_start',
  current_turn: 0,
  name: '',
  min_players: 2,
  max_players: 4,
  owner: 1,
  player_in_action: 1,
};

describe('OpponentPlayerSets', () => {
  beforeEach(() => vi.clearAllMocks());

  it('no renderiza nada cuando no hay sets', async () => {
    mockSearch.mockResolvedValueOnce([]);
    const { container } = render(
      <OpponentPlayerSets
        playerId={123}
        game={mockGame}
        canSelect
        setTargetSet={() => {}}
        targetSet={0}
      />
    );
    await waitFor(() => {
      expect(mockSearch).toHaveBeenCalledWith({ owner__eq: 123 });
      expect(container.firstChild).toBeNull();
    });
  });

  it('muestra imagen de la primera carta cuando hay sets', async () => {
    mockSearch.mockResolvedValueOnce([
      {
        id: 77,
        detectives: [
          { id: 1, name: 'tommy-beresford' },
          { id: 2, name: 'miss-marple' },
        ],
      },
    ]);
    render(
      <OpponentPlayerSets
        playerId={55}
        game={mockGame}
        canSelect
        setTargetSet={() => {}}
        targetSet={0}
      />
    );
    await waitFor(() => expect(mockSearch).toHaveBeenCalledWith({ owner__eq: 55 }));
    const imgs = screen.getAllByRole('img', { name: /tommy-beresford/i });
    expect(imgs[0]).toBeInTheDocument();
  });

  it('el tooltip aparece en el DOM', async () => {
    mockSearch.mockResolvedValueOnce([
      {
        id: 10,
        detectives: [
          { id: 1, name: 'parker-pyne' },
          { id: 2, name: 'miss-marple' },
        ],
      },
    ]);
    render(
      <OpponentPlayerSets
        playerId={1}
        game={mockGame}
        canSelect
        setTargetSet={() => {}}
        targetSet={0}
      />
    );
    const parkerImgs = await screen.findAllByRole('img', { name: /parker-pyne/i });
    expect(parkerImgs.length).toBeGreaterThan(0);
  });

  it('propaga el id cuando se selecciona un set distinto', async () => {
    mockSearch.mockResolvedValueOnce([
      { id: 77, detectives: [{ id: 1, name: 'tommy-beresford' }] },
    ]);
    const setTargetSet = vi.fn();
    render(
      <OpponentPlayerSets
        playerId={99}
        game={mockGame}
        canSelect
        setTargetSet={setTargetSet}
        targetSet={null}
      />
    );
    const [thumb] = await screen.findAllByRole('img', { name: /tommy-beresford/i });
    fireEvent.click(thumb.parentElement as HTMLElement);
    expect(setTargetSet).toHaveBeenCalledWith(77);
  });

  it('resetea el target al volver a elegir el mismo set', async () => {
    mockSearch.mockResolvedValueOnce([
      { id: 55, detectives: [{ id: 1, name: 'miss-marple' }] },
    ]);
    const setTargetSet = vi.fn();
    render(
      <OpponentPlayerSets
        playerId={77}
        game={mockGame}
        canSelect
        setTargetSet={setTargetSet}
        targetSet={55}
      />
    );
    const [thumb] = await screen.findAllByRole('img', { name: /miss-marple/i });
    fireEvent.click(thumb.parentElement as HTMLElement);
    expect(setTargetSet).toHaveBeenCalledWith(null);
  });
});