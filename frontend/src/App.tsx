import React, { useState, useEffect } from 'react';
import { checkHealth, HealthResponse } from './services/api';
import { PublicLayout } from './components/layout';
import { NoticeFeed } from './components/notices';

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(false);
  const [healthError, setHealthError] = useState<string | null>(null);

  const fetchHealth = async () => {
    setHealthLoading(true);
    setHealthError(null);
    try {
      const data = await checkHealth();
      setHealth(data);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'message' in err) {
        setHealthError(String((err as { message: string }).message));
      } else {
        setHealthError('Failed to reach backend health endpoint.');
      }
    } finally {
      setHealthLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <PublicLayout currentPath="/notices">
      <div className="space-y-8 pb-10">
        {/* Page Banner Header */}
        <header className="border-b border-slate-200 pb-6 pt-2">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <div className="inline-flex items-center space-x-2 text-indigo-600 font-semibold text-xs tracking-wider uppercase mb-1.5">
                <span>Kirori Mal College</span>
                <span>&bull;</span>
                <span>University of Delhi</span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                Official Campus Notices & Circulars
              </h1>
              <p className="text-sm text-slate-500 mt-1 max-w-2xl">
                Browse latest notices, examination forms, admissions updates, and scholarship guidelines.
                All information is strictly source-faithful and verified from official documents.
              </p>
            </div>

            {/* Quick Status Pill */}
            <div className="shrink-0 flex items-center space-x-2 text-xs">
              <span className="text-slate-500">API Status:</span>
              {healthLoading ? (
                <span className="inline-flex items-center px-2 py-0.5 rounded-full font-medium bg-amber-50 text-amber-700 border border-amber-200">
                  Checking...
                </span>
              ) : health ? (
                <span className="inline-flex items-center px-2 py-0.5 rounded-full font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Online (v{health.version})
                </span>
              ) : (
                <span
                  title={healthError || 'Backend offline'}
                  className="inline-flex items-center px-2 py-0.5 rounded-full font-medium bg-slate-100 text-slate-600 border border-slate-200"
                >
                  Offline (Mock Mode)
                </span>
              )}
            </div>
          </div>
        </header>

        {/* Public Notice Feed with Filter Chips, Skeletons, and Empty State */}
        <NoticeFeed />
      </div>
    </PublicLayout>
  );
};

export default App;
