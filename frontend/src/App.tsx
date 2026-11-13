import React, { useState, useEffect } from 'react';
import { checkHealth, HealthResponse, API_BASE_URL } from '@/services/api';

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await checkHealth();
      setHealth(data);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'message' in err) {
        setError(String((err as { message: string }).message));
      } else {
        setError('Failed to reach backend health endpoint.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6">
      <div className="max-w-xl w-full bg-white rounded-xl shadow-md border border-slate-200 p-8 space-y-6">
        <header className="border-b border-slate-100 pb-4">
          <div className="flex items-center space-x-2 text-indigo-600 font-semibold text-xs tracking-wider uppercase">
            <span>CAI Campus Intelligence</span>
            <span>&bull;</span>
            <span>Phase 1 Scaffold</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 mt-1">
            Frontend Foundation
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            React 18 + TypeScript + Vite + Tailwind CSS
          </p>
        </header>

        <section className="bg-slate-50 rounded-lg p-4 border border-slate-200/60 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">
              API Base URL
            </span>
            <code className="text-xs font-mono bg-slate-200/80 px-2 py-0.5 rounded text-slate-800">
              {API_BASE_URL}
            </code>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">
              Backend Health
            </span>
            <div>
              {loading && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                  Checking...
                </span>
              )}
              {!loading && health && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                  Healthy (v{health.version})
                </span>
              )}
              {!loading && error && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-100 text-rose-800">
                  Offline / Disconnected
                </span>
              )}
            </div>
          </div>

          {health && (
            <div className="pt-2 border-t border-slate-200/60 text-xs text-slate-600 space-y-1">
              <div>
                <span className="font-semibold text-slate-700">Timestamp: </span>
                {health.timestamp}
              </div>
              <div>
                <span className="font-semibold text-slate-700">Status: </span>
                {health.status}
              </div>
            </div>
          )}

          {error && (
            <div className="pt-2 border-t border-slate-200/60 text-xs text-rose-600">
              {error}
            </div>
          )}
        </section>

        <div className="flex justify-end">
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 transition"
          >
            {loading ? 'Refreshing...' : 'Refresh Health'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default App;

