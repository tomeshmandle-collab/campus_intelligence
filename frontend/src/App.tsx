import React, { useState, useEffect } from 'react';
import { checkHealth, HealthResponse } from './services/api';
import { PublicLayout } from './components/layout';
import { NoticeFeed } from './components/notices';
import { NoticeDetailPage } from './pages/public';
import { NoticeDetail } from './types/notice';

export const App: React.FC = () => {
  const [currentPath, setCurrentPath] = useState<string>(() => window.location.pathname);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(false);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [reportedNotice, setReportedNotice] = useState<NoticeDetail | null>(null);

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

  // Listen to browser navigation popstate (Back/Forward buttons)
  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname);
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigate = (path: string) => {
    window.history.pushState({}, '', path);
    setCurrentPath(path);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Determine current route: Notice Detail vs Notice Feed
  const noticeDetailMatch = currentPath.match(/^\/notices\/([a-zA-Z0-9_-]+)/);
  const activeNoticeId = noticeDetailMatch ? noticeDetailMatch[1] : null;

  return (
    <PublicLayout currentPath={currentPath}>
      <div className="space-y-8 pb-10">
        {/* Conditional Page Content */}
        {activeNoticeId ? (
          <NoticeDetailPage
            noticeId={activeNoticeId}
            onBack={() => navigate('/notices')}
            onNavigateNotice={(targetId) => navigate(`/notices/${targetId}`)}
            onReportIssue={(targetNotice) => setReportedNotice(targetNotice)}
          />
        ) : (
          <>
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
            <NoticeFeed
              onNoticeSelect={(notice) => navigate(`/notices/${notice.id}`)}
            />
          </>
        )}

        {/* Temporary Feedback Dialog for Issue Reporting (previews Issue P3-4) */}
        {reportedNotice && (
          <div
            role="dialog"
            aria-modal="true"
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs"
          >
            <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="font-bold text-slate-900 text-base">Report an Issue with Notice</h3>
                <button
                  type="button"
                  onClick={() => setReportedNotice(null)}
                  className="text-slate-400 hover:text-slate-600 text-lg leading-none"
                >
                  &times;
                </button>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                You are reporting an issue for: <br />
                <strong className="text-slate-800">{reportedNotice.title}</strong> (ID: {reportedNotice.id})
              </p>
              <div className="rounded-lg bg-indigo-50/70 p-3 text-xs text-indigo-900 border border-indigo-100">
                The full Issue Reporting Modal will be integrated in <strong>Issue P3-4</strong> per the project roadmap.
              </div>
              <div className="flex justify-end pt-2">
                <button
                  type="button"
                  onClick={() => setReportedNotice(null)}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold hover:bg-indigo-700 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </PublicLayout>
  );
};

export default App;
