import { Outlet, Link } from 'react-router-dom';
import { useAuth } from '../../context/useAuth';

export default function AppShell() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-surface-900 flex flex-col">
      <nav className="bg-surface-800 border-b border-surface-600 px-4 py-3 sm:px-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <Link to="/" className="flex items-center gap-2">
          <span className="text-xl sm:text-2xl font-bold tracking-tight">
            <span className="text-accent-blue">Slick</span>
            <span className="text-accent-orange">Tunes</span>
            <span className="text-zinc-100">AI</span>
          </span>
        </Link>
        <div className="flex w-full flex-wrap items-center justify-between gap-3 sm:w-auto sm:justify-end sm:gap-4">
          <span className="min-w-0 truncate text-zinc-400 text-sm">
            {user?.displayName ?? user?.email}
          </span>
          <button
            onClick={logout}
            className="text-sm text-zinc-400 hover:text-zinc-100 border border-surface-600 hover:border-zinc-500 px-3 py-1.5 rounded-md transition-colors"
          >
            Sign out
          </button>
        </div>
      </nav>
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}
