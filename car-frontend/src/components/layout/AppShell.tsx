import { Outlet, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function AppShell() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-surface-900 flex flex-col">
      <nav className="bg-surface-800 border-b border-surface-600 px-6 py-3 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <span className="text-2xl font-bold tracking-tight">
            <span className="text-accent-blue">Car</span>
            <span className="text-accent-orange">Tune</span>
            <span className="text-zinc-100">AI</span>
          </span>
        </Link>
        <div className="flex items-center gap-4">
          <span className="text-zinc-400 text-sm">
            {user?.username}
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
