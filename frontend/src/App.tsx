import React, { useState, useEffect } from 'react';
import { checkHealth, HealthResponse, API_BASE_URL } from '@/services/api';
import { AuthProvider, useAuth } from '@/context';
import { LoginPage } from '@/pages/admin';
import { ProtectedRoute } from '@/components/auth';

/**
 * Health check view from Phase 1 scaffold.
 */
const HealthCheckView: React.FC = () => {
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
  );
};

/**
 * Preview dashboard rendered inside ProtectedRoute.
 */
const AdminDashboardPreview: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <div className="max-w-xl w-full bg-white rounded-2xl shadow-xl border border-slate-200/80 p-8 space-y-6">
      <div className="flex items-center space-x-3 border-b border-slate-100 pb-4">
        <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center font-bold">
          ✓
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-900">
            Staff Portal Dashboard
          </h2>
          <p className="text-xs text-slate-500">
            Protected Route Verified &bull; Active Session
          </p>
        </div>
      </div>

      <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 space-y-3 text-sm">
        <div className="flex justify-between items-center">
          <span className="text-slate-500 font-medium">Full Name:</span>
          <span className="font-semibold text-slate-800">{user?.full_name || 'N/A'}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-500 font-medium">Email:</span>
          <span className="font-mono text-xs text-slate-700">{user?.email}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-500 font-medium">Application Role:</span>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800 uppercase">
            {user?.role}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-500 font-medium">Department:</span>
          <span className="text-slate-700">{user?.department || 'Unspecified'}</span>
        </div>
      </div>

      <div className="pt-2">
        <button
          onClick={logout}
          className="w-full py-2.5 px-4 border border-rose-200 rounded-lg text-sm font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 transition"
        >
          Sign Out of Staff Session
        </button>
      </div>
    </div>
  );
};

/**
 * Main application content with view switcher to test P4 Auth flows and Phase 1 Health.
 */
const AppContent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'health' | 'admin'>('admin');
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col">
      {/* Top Bar Navigation for Local Testing */}
      <nav className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="font-bold text-slate-800 text-sm tracking-tight">
            CAI Campus Intelligence
          </span>
          <span className="text-slate-300">|</span>
          <span className="text-xs font-medium text-slate-500">P4 Workbench</span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveTab('admin')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              activeTab === 'admin'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            Staff Portal (Login / Protected)
          </button>
          <button
            onClick={() => setActiveTab('health')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              activeTab === 'health'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            Backend Health
          </button>
        </div>
      </nav>

      {/* Main View Area */}
      <main className="flex-1 flex items-center justify-center p-6">
        {activeTab === 'health' ? (
          <HealthCheckView />
        ) : !isAuthenticated ? (
          <LoginPage onSuccess={() => setActiveTab('admin')} />
        ) : (
          <ProtectedRoute onRedirect={() => setActiveTab('admin')}>
            <AdminDashboardPreview />
          </ProtectedRoute>
        )}
      </main>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;
