import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/useAuth';

export default function LoginForm() {
  const { login, loginWithEmail } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGoogleSignIn = async () => {
    setError(null);
    setIsLoading(true);
    try {
      await login();
      navigate('/');
    } catch {
      setError('Google sign in failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEmailSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await loginWithEmail(email, password);
      navigate('/');
    } catch (err: unknown) {
      const code = (err as { code?: string }).code;
      if (code === 'auth/invalid-credential' || code === 'auth/wrong-password' || code === 'auth/user-not-found') {
        setError('Invalid email or password.');
      } else if (code === 'auth/too-many-requests') {
        setError('Too many attempts. Please try again later.');
      } else {
        setError('Sign in failed. Please try again.');
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
          <p className="text-zinc-400 text-sm">Sign in to get started</p>
        </div>

        <div className="bg-surface-800 border border-surface-600 rounded-xl p-6 space-y-4">
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-lg px-4 py-2">
              {error}
            </div>
          )}

          <button
            onClick={handleGoogleSignIn}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-3 bg-white hover:bg-zinc-100 disabled:opacity-50 disabled:cursor-not-allowed text-zinc-900 font-medium py-2.5 rounded-lg transition-colors text-sm"
          >
            {!isLoading && (
              <svg viewBox="0 0 24 24" className="w-5 h-5" xmlns="http://www.w3.org/2000/svg">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
            )}
            {isLoading ? 'Signing in...' : 'Sign in with Google'}
          </button>

          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-surface-600" />
            <span className="text-zinc-500 text-xs">or</span>
            <div className="flex-1 h-px bg-surface-600" />
          </div>

          <form onSubmit={handleEmailSignIn} className="space-y-3">
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              disabled={isLoading}
              className="w-full bg-surface-900 border border-surface-600 text-zinc-100 placeholder-zinc-500 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-accent-blue disabled:opacity-50"
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              disabled={isLoading}
              className="w-full bg-surface-900 border border-surface-600 text-zinc-100 placeholder-zinc-500 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-accent-blue disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-accent-blue hover:bg-accent-blue/90 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2.5 rounded-lg transition-colors text-sm"
            >
              {isLoading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <p className="text-center text-zinc-500 text-xs">
            Don't have an account?{' '}
            <Link to="/signup" className="text-accent-blue hover:underline">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
