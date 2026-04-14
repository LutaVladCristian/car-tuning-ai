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
  useAuth: () => ({ login: mockLogin }),
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
  it('renders username and password inputs', () => {
    renderForm();
    expect(screen.getByPlaceholderText('your_username')).toBeDefined();
    expect(screen.getByPlaceholderText('••••••••')).toBeDefined();
  });

  it('calls login with the entered credentials on submit', async () => {
    mockLogin.mockResolvedValueOnce(undefined);
    renderForm();

    fireEvent.change(screen.getByPlaceholderText('your_username'), {
      target: { value: 'alice' },
    });
    fireEvent.change(screen.getByPlaceholderText('••••••••'), {
      target: { value: 'secret123' },
    });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => expect(mockLogin).toHaveBeenCalledWith({
      username: 'alice',
      password: 'secret123',
    }));
  });

  it('navigates to "/" after a successful login', async () => {
    mockLogin.mockResolvedValueOnce(undefined);
    renderForm();

    fireEvent.change(screen.getByPlaceholderText('your_username'), { target: { value: 'u' } });
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'p' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/'));
  });

  it('shows the API error message when login fails with a detail field', async () => {
    mockLogin.mockRejectedValueOnce({
      response: { data: { detail: 'Invalid credentials' } },
    });
    renderForm();

    fireEvent.change(screen.getByPlaceholderText('your_username'), { target: { value: 'u' } });
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'p' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => expect(screen.getByText('Invalid credentials')).toBeDefined());
  });

  it('shows the fallback error message when the error has no detail field', async () => {
    mockLogin.mockRejectedValueOnce(new Error('Network error'));
    renderForm();

    fireEvent.change(screen.getByPlaceholderText('your_username'), { target: { value: 'u' } });
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'p' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() =>
      expect(screen.getByText('Invalid username or password.')).toBeDefined()
    );
  });

  it('disables the button and shows "Signing in..." while the request is in flight', async () => {
    let resolve!: () => void;
    mockLogin.mockReturnValueOnce(new Promise<void>((res) => { resolve = res; }));
    renderForm();

    fireEvent.change(screen.getByPlaceholderText('your_username'), { target: { value: 'u' } });
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'p' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      const btn = screen.getByRole('button', { name: /signing in/i });
      expect(btn).toBeDefined();
      expect((btn as HTMLButtonElement).disabled).toBe(true);
    });

    resolve();
  });
});
