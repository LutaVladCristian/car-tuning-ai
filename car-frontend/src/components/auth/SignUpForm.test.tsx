import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import SignUpForm from './SignUpForm';

const mockNavigate = vi.fn();
const mockRegister = vi.fn();

vi.mock('react-router-dom', async (importOriginal) => {
  const mod = await importOriginal<typeof import('react-router-dom')>();
  return { ...mod, useNavigate: () => mockNavigate };
});

vi.mock('../../context/useAuth', () => ({
  useAuth: () => ({ register: mockRegister }),
}));

function renderForm() {
  return render(
    <MemoryRouter>
      <SignUpForm />
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('SignUpForm', () => {
  it('renders username, email, and password inputs', () => {
    renderForm();
    expect(screen.getByPlaceholderText('your_username')).toBeDefined();
    expect(screen.getByPlaceholderText('you@example.com')).toBeDefined();
    expect(screen.getByPlaceholderText('Min. 8 characters')).toBeDefined();
  });

  it('calls register with the correct payload on submit', async () => {
    mockRegister.mockResolvedValueOnce(undefined);
    renderForm();

    fireEvent.change(screen.getByPlaceholderText('your_username'), { target: { value: 'bob' } });
    fireEvent.change(screen.getByPlaceholderText('you@example.com'), { target: { value: 'bob@test.com' } });
    fireEvent.change(screen.getByPlaceholderText('Min. 8 characters'), { target: { value: 'password1' } });
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() =>
      expect(mockRegister).toHaveBeenCalledWith({
        username: 'bob',
        email: 'bob@test.com',
        password: 'password1',
      })
    );
  });

  it('navigates to "/login" after successful registration', async () => {
    mockRegister.mockResolvedValueOnce(undefined);
    renderForm();

    fireEvent.change(screen.getByPlaceholderText('your_username'), { target: { value: 'u' } });
    fireEvent.change(screen.getByPlaceholderText('you@example.com'), { target: { value: 'u@u.com' } });
    fireEvent.change(screen.getByPlaceholderText('Min. 8 characters'), { target: { value: 'pass1234' } });
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/login'));
  });

  it('shows a string error from the API detail field', async () => {
    mockRegister.mockRejectedValueOnce({
      response: { data: { detail: 'Username already taken' } },
    });
    renderForm();

    fireEvent.change(screen.getByPlaceholderText('your_username'), { target: { value: 'u' } });
    fireEvent.change(screen.getByPlaceholderText('you@example.com'), { target: { value: 'u@u.com' } });
    fireEvent.change(screen.getByPlaceholderText('Min. 8 characters'), { target: { value: 'pass1234' } });
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => expect(screen.getByText('Username already taken')).toBeDefined());
  });

  it('joins multiple validation error messages when detail is an array', async () => {
    mockRegister.mockRejectedValueOnce({
      response: {
        data: {
          detail: [
            { msg: 'Username too short' },
            { msg: 'Password too weak' },
          ],
        },
      },
    });
    renderForm();

    fireEvent.change(screen.getByPlaceholderText('your_username'), { target: { value: 'u' } });
    fireEvent.change(screen.getByPlaceholderText('you@example.com'), { target: { value: 'u@u.com' } });
    fireEvent.change(screen.getByPlaceholderText('Min. 8 characters'), { target: { value: 'pass1234' } });
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() =>
      expect(screen.getByText('Username too short, Password too weak')).toBeDefined()
    );
  });

  it('shows the fallback error when no detail field is present', async () => {
    mockRegister.mockRejectedValueOnce(new Error('Network error'));
    renderForm();

    fireEvent.change(screen.getByPlaceholderText('your_username'), { target: { value: 'u' } });
    fireEvent.change(screen.getByPlaceholderText('you@example.com'), { target: { value: 'u@u.com' } });
    fireEvent.change(screen.getByPlaceholderText('Min. 8 characters'), { target: { value: 'pass1234' } });
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() =>
      expect(screen.getByText('Registration failed. Please try again.')).toBeDefined()
    );
  });

  it('disables the button and shows "Creating account..." while the request is in flight', async () => {
    let resolve!: () => void;
    mockRegister.mockReturnValueOnce(new Promise<void>((res) => { resolve = res; }));
    renderForm();

    fireEvent.change(screen.getByPlaceholderText('your_username'), { target: { value: 'u' } });
    fireEvent.change(screen.getByPlaceholderText('you@example.com'), { target: { value: 'u@u.com' } });
    fireEvent.change(screen.getByPlaceholderText('Min. 8 characters'), { target: { value: 'pass1234' } });
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      const btn = screen.getByRole('button', { name: /creating account/i });
      expect(btn).toBeDefined();
      expect((btn as HTMLButtonElement).disabled).toBe(true);
    });

    resolve();
  });
});
