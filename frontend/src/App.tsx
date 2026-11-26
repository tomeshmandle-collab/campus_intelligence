import React, { useState, useEffect } from 'react';
import { checkHealth, HealthResponse } from './services/api';
import { PublicLayout } from './components/layout';
import { NoticeFeed, ErrorReportModal } from './components/notices';
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

        {/* Public Error Report Form Modal (Issue P3-4) */}
        <ErrorReportModal
          isOpen={!!reportedNotice}
          notice={reportedNotice}
          onClose={() => setReportedNotice(null)}
          isMockMode={!health}
        />
      </div>
    </PublicLayout>
  );
};

export default App;
