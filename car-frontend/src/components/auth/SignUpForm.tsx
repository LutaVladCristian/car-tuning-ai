import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { AxiosError } from 'axios';

export default function SignUpForm() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await register({ username, email, password });
      navigate('/login');
    } catch (err) {
      const axiosErr = err as AxiosError<{ detail: string | { msg: string }[] }>;
      const detail = axiosErr.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((d) => d.msg).join(', '));
      } else {
        setError(detail ?? 'Registration failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface-900 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold tracking-tight mb-1">
            <span className="text-accent-blue">Car</span>
            <span className="text-accent-orange">Tune</span>
            <span className="text-zinc-100">AI</span>
          </h1>
          <p className="text-zinc-400 text-sm">Create your account</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-surface-800 border border-surface-600 rounded-xl p-6 space-y-4"
        >
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-lg px-4 py-2">
              {error}
            </div>
          )}

          <div className="space-y-1">
            <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              minLength={3}
              maxLength={50}
              autoFocus
              className="w-full bg-surface-700 border border-surface-600 rounded-lg px-4 py-2.5 text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-accent-blue transition-colors text-sm"
              placeholder="your_username"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full bg-surface-700 border border-surface-600 rounded-lg px-4 py-2.5 text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-accent-blue transition-colors text-sm"
              placeholder="you@example.com"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className="w-full bg-surface-700 border border-surface-600 rounded-lg px-4 py-2.5 text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-accent-blue transition-colors text-sm"
              placeholder="Min. 8 characters"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-accent-orange hover:bg-orange-400 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2.5 rounded-lg transition-colors text-sm shadow-glow-orange"
          >
            {isLoading ? 'Creating account...' : 'Create account'}
          </button>
        </form>

        <p className="text-center text-zinc-500 text-sm mt-4">
          Already have an account?{' '}
          <Link to="/login" className="text-accent-blue hover:text-accent-glow transition-colors">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
