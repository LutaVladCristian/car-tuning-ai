import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import LoginForm from './LoginForm';

const mockNavigate = vi.fn();
const mockLogin = vi.fn();

vi.mock('react-router-dom', async (importOriginal) => {
  const mod = await importOriginal<typeof import('react-router-dom')>();
  return { ...mod, useNavigate: () => mockNavigate };
});

vi.mock('../../context/useAuth', () => ({
  useAuth: () => ({ login: mockLogin, loginWithEmail: vi.fn() }),
}));

function renderForm() {
  return render(
    <MemoryRouter>
      <LoginForm />
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('LoginForm', () => {
  it('renders the SlickTunesAI brand', () => {
    renderForm();
    expect(screen.getByText('Slick')).toBeDefined();
    expect(screen.getByText('Tunes')).toBeDefined();
    expect(screen.getByText('AI')).toBeDefined();
  });

  it('renders the Google Sign-In button', () => {
    renderForm();
    expect(screen.getByRole('button', { name: /sign in with google/i })).toBeDefined();
  });

  it('calls login() when the button is clicked', async () => {
    mockLogin.mockResolvedValueOnce(undefined);
    renderForm();
    fireEvent.click(screen.getByRole('button', { name: /sign in with google/i }));
    await waitFor(() => expect(mockLogin).toHaveBeenCalledTimes(1));
  });

  it('navigates to "/" after a successful login', async () => {
    mockLogin.mockResolvedValueOnce(undefined);
    renderForm();
    fireEvent.click(screen.getByRole('button', { name: /sign in with google/i }));
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/'));
  });

  it('shows error message when login fails', async () => {
    mockLogin.mockRejectedValueOnce(new Error('popup closed'));
    renderForm();
    fireEvent.click(screen.getByRole('button', { name: /sign in with google/i }));
    await waitFor(() =>
      expect(screen.getByText('Google sign in failed. Please try again.')).toBeDefined()
    );
  });

  it('disables the button and shows "Signing in..." while in flight', async () => {
    let resolve!: () => void;
    mockLogin.mockReturnValueOnce(new Promise<void>((res) => { resolve = res; }));
    renderForm();
    fireEvent.click(screen.getByRole('button', { name: /sign in with google/i }));
    await waitFor(() => {
      const buttons = screen.getAllByRole('button', { name: /signing in/i });
      expect(buttons.length).toBeGreaterThan(0);
      expect(buttons.every((btn) => (btn as HTMLButtonElement).disabled)).toBe(true);
    });
    resolve();
  });
});
