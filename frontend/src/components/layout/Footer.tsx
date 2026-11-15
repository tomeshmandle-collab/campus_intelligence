import React from 'react';

export const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-slate-200 bg-white text-slate-600 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-10 space-y-8">
        {/* Official Institutional Disclaimer Banner - Academic Slate / Indigo Styling */}
        <div className="rounded-xl bg-slate-50 border border-slate-200/80 p-4 sm:p-5 shadow-sm">
          <div className="flex items-start space-x-3.5">
            <div className="shrink-0 p-1.5 rounded-lg bg-indigo-50 text-indigo-600 mt-0.5">
              <svg
                className="w-5 h-5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>
            <div className="space-y-1">
              <span className="text-xs font-semibold uppercase tracking-wider text-indigo-700 block">
                Official Institutional Disclaimer
              </span>
              <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-normal">
                Extracted notice information is derived from official college notices. Always verify with the original document.
              </p>
            </div>
          </div>
        </div>

        {/* Institutional Identity, Navigation, and Action Links */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 pt-2">
          {/* Institution Credits */}
          <div className="space-y-1.5">
            <div className="flex items-center space-x-2">
              <span className="h-2 w-2 rounded-full bg-indigo-600" aria-hidden="true" />
              <h3 className="text-sm sm:text-base font-semibold text-slate-900 tracking-tight">
                Centre for Artificial Intelligence, Kirori Mal College
              </h3>
            </div>
            <p className="text-xs text-slate-500 pl-4">
              University of Delhi &bull; Official Digital Notice Board &amp; Intelligence System
            </p>
          </div>

          {/* Quick Links & Report an Issue */}
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2.5 text-xs sm:text-sm font-medium text-slate-600">
            <a
              href="/notices"
              className="hover:text-indigo-600 transition-colors"
            >
              Notices
            </a>
            <a
              href="/search"
              className="hover:text-indigo-600 transition-colors"
            >
              Search &amp; Ask
            </a>
            <a
              href="/about"
              className="hover:text-indigo-600 transition-colors"
            >
              About CAI
            </a>
            <a
              href="/report-issue"
              className="inline-flex items-center text-indigo-600 hover:text-indigo-800 transition-colors group"
            >
              <svg
                className="w-3.5 h-3.5 mr-1 text-indigo-500 group-hover:text-indigo-700"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
                <line x1="4" y1="22" x2="4" y2="15" />
              </svg>
              Report an Issue
            </a>
            <a
              href="/login"
              className="hover:text-slate-900 text-slate-500 transition-colors"
            >
              Staff Portal
            </a>
          </div>
        </div>

        {/* Copyright & Secondary Attribution */}
        <div className="border-t border-slate-100 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400">
          <p>
            &copy; {currentYear} Centre for Artificial Intelligence, Kirori Mal College. All rights reserved.
          </p>
          <p className="flex items-center space-x-1.5">
            <span>Assistive Intelligence</span>
            <span>&bull;</span>
            <a
              href="/report-issue"
              className="text-slate-500 hover:text-indigo-600 underline underline-offset-2 transition-colors"
            >
              Report notice discrepancy
            </a>
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
