import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Login from './Login';

describe('Login component', () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it('caso renderizar ok', () => {
    render(<Login />);

    expect(screen.getByPlaceholderText(/nombre de usuario/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/dd\/mm\/yyyy/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /ingresar/i })).toBeInTheDocument();
  });
  
  it('caso nombre vacío', () => {
    render(<Login />);
    fireEvent.click(screen.getByRole('button', { name: /ingresar/i }));
    expect(screen.getByText(/nombre inválido/i)).toBeInTheDocument();
  });
  
  it('caso nombre largo', () => {
    render(<Login />);
    fireEvent.change(screen.getByPlaceholderText(/nombre de usuario/i), {
      target: { value: 'Agathaaaaaaaaaaaaaaa' },
    });
    fireEvent.click(screen.getByRole('button', { name: /ingresar/i }));
    expect(screen.getByText(/nombre inválido/i)).toBeInTheDocument();
  });

  it('caso fecha vacia', () => {
    render(<Login />);
    fireEvent.change(screen.getByPlaceholderText(/nombre de usuario/i), {
      target: { value: 'Agatha' },
    });
    fireEvent.click(screen.getByRole('button', { name: /ingresar/i }));

    expect(screen.getByText(/fecha inválida/i)).toBeInTheDocument();
  });
  
  it('caso fecha futura', () => {
    render(<Login />);
    fireEvent.change(screen.getByPlaceholderText(/nombre de usuario/i), {
      target: { value: 'Poirot' },
    });
    fireEvent.change(screen.getByPlaceholderText(/dd\/mm\/yyyy/i), {
      target: { value: '2099-01-28' },
    });
    fireEvent.click(screen.getByRole('button', { name: /ingresar/i }));

    expect(screen.getByText(/fecha inválida/i)).toBeInTheDocument();
  });

  it('caso ok', () => {
    const mockSetPlayerData = vi.fn();

    render(<Login setPrePlayerData={mockSetPlayerData} />);

    fireEvent.change(screen.getByPlaceholderText(/nombre de usuario/i), {
      target: { value: 'Agatha' },
    });
    fireEvent.change(screen.getByPlaceholderText(/dd\/mm\/yyyy/i), {
      target: { value: '2004-01-28' },
    });
    fireEvent.click(screen.getByRole('button', { name: /ingresar/i }));

    expect(mockSetPlayerData).toHaveBeenCalledWith({
      name: 'Agatha',
      birthdate: '2004-01-28T00:00:00.000Z',
      avatar: 'detective1',
    });
  });

it('caso botón derecho', () => {
  render(<Login />);

  expect(screen.getByText(/hercule poirot/i)).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: '›' }));
  expect(screen.getByText(/miss marple/i)).toBeInTheDocument();
  expect(screen.queryByText(/hercule poirot/i)).not.toBeInTheDocument();
});

it('caso botón izquierdo', () => {
  render(<Login />);

  expect(screen.getByText(/hercule poirot/i)).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: '‹' }));
  expect(screen.getByText(/ariadne oliver/i)).toBeInTheDocument();
  expect(screen.queryByText(/hercule poirot/i)).not.toBeInTheDocument();
});
});
