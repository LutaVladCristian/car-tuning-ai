import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ProtectedRoute from './ProtectedRoute';

vi.mock('../../context/useAuth', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '../../context/useAuth';
const mockUseAuth = vi.mocked(useAuth);

function renderWithRouter(isAuthenticated: boolean) {
  mockUseAuth.mockReturnValue({
    user: isAuthenticated ? { username: 'alice', token: 'tok' } : null,
    isAuthenticated,
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
  });

  return render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <div>Protected Content</div>
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<div>Login Page</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe('ProtectedRoute', () => {
  it('renders children when the user is authenticated', () => {
    renderWithRouter(true);
    expect(screen.getByText('Protected Content')).toBeDefined();
    expect(screen.queryByText('Login Page')).toBeNull();
  });

  it('redirects to /login when the user is not authenticated', () => {
    renderWithRouter(false);
    expect(screen.getByText('Login Page')).toBeDefined();
    expect(screen.queryByText('Protected Content')).toBeNull();
  });
});
