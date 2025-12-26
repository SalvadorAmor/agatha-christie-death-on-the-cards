import '@testing-library/jest-dom/vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import MyPlayerSets from './MyPlayerSets';
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

describe('MyPlayerSets', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

it('renderiza el botón con la primera carta del set', async () => {
  mockSearch.mockResolvedValueOnce([
    {
      id: 77,
      detectives: [
        { id: 1, name: 'tommy-beresford' },
        { id: 2, name: 'miss-marple' },
      ],
    },
  ]);

  render(<MyPlayerSets playerId={55} game={mockGame} />);

  await waitFor(() => {
    expect(mockSearch).toHaveBeenCalledWith({ owner__eq: 55 });
  });

  const button = await screen.findByRole('button');
  expect(button).toBeInTheDocument();

  const imgs = screen.getAllByRole('img', { name: /tommy-beresford/i });
  expect(imgs.length).toBeGreaterThan(0);
});

  it('muestra las imágenes del popup al renderizar', async () => {
    mockSearch.mockResolvedValueOnce([
      {
        id: 10,
        detectives: [
          { id: 1, name: 'parker-pyne' },
          { id: 2, name: 'miss-marple' },
        ],
      },
    ]);

    render(<MyPlayerSets playerId={1} game={mockGame} />);

    await waitFor(() => {
      expect(mockSearch).toHaveBeenCalledWith({ owner__eq: 1 });
    });

    // debe renderizar ambas imágenes de detectives
    const imgs = await screen.findAllByRole('img');
    const names = imgs.map((i) => i.getAttribute('alt'));
    expect(names).toContain('parker-pyne');
    expect(names).toContain('miss-marple');
  });
});