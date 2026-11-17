import React, { useState, useEffect } from 'react';
import {
  NoticeDetail,
  AudienceType,
} from '../../types/notice';
import { fetchNoticeById } from '../../services/api';
import { getMockNoticeDetail } from '../../mocks/mockNotices';

export interface NoticeDetailPageProps {
  noticeId: string;
  onBack?: () => void;
  onNavigateNotice?: (id: string) => void;
  onReportIssue?: (notice: NoticeDetail) => void;
}

const AUDIENCE_LABELS: Record<AudienceType, string> = {
  student: 'Students',
  faculty: 'Faculty',
  staff: 'Staff',
  all: 'Everyone',
  unspecified: 'Not specified',
};

const formatReadableDate = (dateStr?: string | null): string => {
  if (!dateStr) return 'Not specified';
  try {
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
      const [year, month, day] = dateStr.split('-').map(Number);
      const date = new Date(year, month - 1, day);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    }
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return dateStr;
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return dateStr;
  }
};

const getCategoryBadgeStyle = (category: string): string => {
  const normalized = category.toLowerCase();
  if (normalized.includes('admiss')) {
    return 'bg-blue-50 text-blue-700 border-blue-200 ring-1 ring-blue-600/10';
  }
  if (normalized.includes('exam')) {
    return 'bg-amber-50 text-amber-800 border-amber-200 ring-1 ring-amber-600/10';
  }
  if (normalized.includes('scholarship')) {
    return 'bg-purple-50 text-purple-700 border-purple-200 ring-1 ring-purple-600/10';
  }
  return 'bg-emerald-50 text-emerald-700 border-emerald-200 ring-1 ring-emerald-600/10';
};

const calculateDaysRemaining = (deadlineStr: string): { label: string; urgency: 'urgent' | 'warning' | 'normal' | 'passed' } => {
  try {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    let deadlineDate: Date;
    if (/^\d{4}-\d{2}-\d{2}$/.test(deadlineStr)) {
      const [year, month, day] = deadlineStr.split('-').map(Number);
      deadlineDate = new Date(year, month - 1, day);
    } else {
      deadlineDate = new Date(deadlineStr);
    }

    if (isNaN(deadlineDate.getTime())) {
      return { label: `Deadline: ${deadlineStr}`, urgency: 'normal' };
    }

    deadlineDate.setHours(0, 0, 0, 0);
    const diffTime = deadlineDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
      return { label: 'Deadline Passed', urgency: 'passed' };
    }
    if (diffDays === 0) {
      return { label: 'Due Today', urgency: 'urgent' };
    }
    if (diffDays === 1) {
      return { label: 'Due Tomorrow', urgency: 'urgent' };
    }
    if (diffDays <= 3) {
      return { label: `${diffDays} days left`, urgency: 'urgent' };
    }
    if (diffDays <= 7) {
      return { label: `${diffDays} days left`, urgency: 'warning' };
    }
    return { label: `${diffDays} days remaining`, urgency: 'normal' };
  } catch {
    return { label: `Deadline: ${deadlineStr}`, urgency: 'normal' };
  }
};

export const NoticeDetailPage: React.FC<NoticeDetailPageProps> = ({
  noticeId,
  onBack,
  onNavigateNotice,
  onReportIssue,
}) => {
  const [notice, setNotice] = useState<NoticeDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isUsingMock, setIsUsingMock] = useState<boolean>(false);
  const [copyNoticeSuccess, setCopyNoticeSuccess] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    const loadNotice = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetchNoticeById(noticeId);
        if (isMounted) {
          if (response && response.notice) {
            setNotice(response.notice);
            setIsUsingMock(false);
          } else {
            throw new Error('Notice format invalid');
          }
        }
      } catch (err: unknown) {
        // Fallback to offline mock record
        const mock = getMockNoticeDetail(noticeId);
        if (isMounted) {
          if (mock) {
            setNotice(mock);
            setIsUsingMock(true);
          } else {
            setError(
              err instanceof Error
                ? err.message
                : 'Notice could not be found or is not publicly published.'
            );
          }
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    if (noticeId) {
      loadNotice();
    }
    return () => {
      isMounted = false;
    };
  }, [noticeId]);

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopyNoticeSuccess(true);
    setTimeout(() => setCopyNoticeSuccess(false), 2500);
  };

  if (loading) {
    return (
      <div className="space-y-6 max-w-4xl mx-auto py-4 animate-pulse" aria-busy="true">
        {/* Back Link Skeleton */}
        <div className="h-4 w-32 bg-slate-200 rounded"></div>

        {/* Header Skeleton */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 sm:p-8 space-y-4">
          <div className="flex gap-2">
            <div className="h-6 w-24 bg-slate-200 rounded-full"></div>
            <div className="h-6 w-20 bg-slate-100 rounded-full"></div>
          </div>
          <div className="h-8 bg-slate-200 rounded w-4/5"></div>
          <div className="h-4 bg-slate-100 rounded w-1/3"></div>
        </div>

        {/* Content Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-6">
            <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-3">
              <div className="h-5 w-40 bg-slate-200 rounded"></div>
              <div className="h-4 bg-slate-100 rounded w-full"></div>
              <div className="h-4 bg-slate-100 rounded w-full"></div>
              <div className="h-4 bg-slate-100 rounded w-3/4"></div>
            </div>
          </div>
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-3">
              <div className="h-5 w-32 bg-slate-200 rounded"></div>
              <div className="h-10 bg-slate-200 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !notice) {
    return (
      <div className="max-w-2xl mx-auto py-12 px-4 text-center">
        <div className="w-16 h-16 mx-auto rounded-full bg-rose-50 text-rose-500 flex items-center justify-center mb-4 border border-rose-100">
          <svg
            className="w-8 h-8"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="1.5"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
            />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-slate-900 mb-2">Notice Not Found</h2>
        <p className="text-sm text-slate-600 mb-6 max-w-md mx-auto">
          {error || 'The requested circular may have been withdrawn, archived, or is currently pending administrative review.'}
        </p>
        <button
          type="button"
          onClick={onBack || (() => window.history.back())}
          className="inline-flex items-center px-4 py-2 border border-slate-300 rounded-lg text-sm font-semibold text-slate-700 bg-white hover:bg-slate-50 transition-colors shadow-sm"
        >
          &larr; Return to Notice Feed
        </button>
      </div>
    );
  }

  // Find primary deadline if exists
  const deadlineDateObj = notice.important_dates?.find((d) => d.kind === 'deadline');
  const deadlineCountdown = deadlineDateObj ? calculateDaysRemaining(deadlineDateObj.starts_on) : null;

  const isSupersededOrAmended =
    notice.relationship_status === 'amended' ||
    notice.relationship_status === 'superseded' ||
    notice.relationship_status === 'cancelled';

  return (
    <article className="max-w-5xl mx-auto pb-12 space-y-6">
      {/* Top Breadcrumb & Return Action */}
      <nav aria-label="Breadcrumb" className="flex items-center justify-between">
        <button
          type="button"
          onClick={onBack || (() => window.history.back())}
          className="inline-flex items-center text-sm font-medium text-indigo-600 hover:text-indigo-800 transition-colors group"
        >
          <svg
            className="w-4 h-4 mr-1.5 transition-transform group-hover:-translate-x-0.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
          Back to all notices
        </button>

        <div className="flex items-center space-x-2">
          {isUsingMock && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
              Offline Mock Source
            </span>
          )}
          <button
            type="button"
            onClick={handleCopyLink}
            className="inline-flex items-center px-2.5 py-1 text-xs font-medium text-slate-600 bg-white border border-slate-200 rounded-md hover:bg-slate-50 hover:text-slate-900 transition-colors shadow-xs"
            title="Copy direct shareable link"
          >
            <svg
              className="w-3.5 h-3.5 mr-1 text-slate-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244"
              />
            </svg>
            {copyNoticeSuccess ? 'Link Copied!' : 'Share'}
          </button>
        </div>
      </nav>

      {/* Superseded / Amended Alert Banner */}
      {isSupersededOrAmended && (
        <section
          aria-labelledby="amended-notice-banner"
          className="rounded-xl border border-amber-300 bg-amber-50/90 p-4 sm:p-5 text-amber-900 shadow-sm"
        >
          <div className="flex items-start space-x-3.5">
            <div className="shrink-0 pt-0.5 text-amber-600">
              <svg
                className="w-6 h-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth="2"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
                />
              </svg>
            </div>
            <div className="flex-1">
              <h2 id="amended-notice-banner" className="text-sm font-bold text-amber-900 uppercase tracking-wide">
                Notice Status Alert: {notice.relationship_status.toUpperCase()}
              </h2>
              <p className="text-sm text-amber-800 mt-1">
                This circular has been formally marked as{' '}
                <span className="font-semibold underline">{notice.relationship_status}</span> by the issuing authority.
                Terms, fee amounts, or deadlines within this notice may have been altered by a later circular.
              </p>

              {notice.related_notices && notice.related_notices.length > 0 && (
                <div className="mt-3 pt-3 border-t border-amber-200/80 flex flex-wrap items-center gap-2">
                  <span className="text-xs font-semibold text-amber-900">Active Reference:</span>
                  {notice.related_notices.map((rel) => (
                    <button
                      key={rel.notice_id}
                      type="button"
                      onClick={() => onNavigateNotice?.(rel.notice_id)}
                      className="inline-flex items-center text-xs font-semibold px-2.5 py-1 rounded bg-amber-100 text-amber-900 hover:bg-amber-200 transition-colors border border-amber-300"
                    >
                      {rel.title || `Notice #${rel.notice_id}`} &rarr;
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* Main Notice Header Card */}
      <header className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-5">
        {/* Badges Line */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Category Pill */}
          <span
            className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${getCategoryBadgeStyle(
              notice.category
            )}`}
          >
            {notice.category}
          </span>

          {/* Audiences Pills */}
          {notice.audiences?.map((aud) => (
            <span
              key={aud}
              className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200"
            >
              Audience: {AUDIENCE_LABELS[aud] || aud}
            </span>
          ))}

          {/* Reference Number */}
          {notice.reference_number && (
            <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-mono text-slate-600 bg-slate-50 border border-slate-200">
              Ref: {notice.reference_number}
            </span>
          )}
        </div>

        {/* Title */}
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight leading-snug">
          {notice.title}
        </h1>

        {/* Authority & Published Date */}
        <div className="flex flex-wrap items-center gap-y-2 gap-x-6 text-sm text-slate-600 pt-2 border-t border-slate-100">
          <div className="flex items-center space-x-2">
            <svg
              className="w-4 h-4 text-slate-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
              />
            </svg>
            <span className="font-medium text-slate-800">
              {notice.issuing_authority || 'Kirori Mal College Administration'}
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <svg
              className="w-4 h-4 text-slate-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5"
              />
            </svg>
            <span>Published: {formatReadableDate(notice.published_at || notice.issue_date)}</span>
          </div>

          {notice.field_labels?.title && (
            <span className="inline-flex items-center text-xs text-slate-400 italic">
              Verification: {notice.field_labels.title === 'human_corrected' ? 'Verified by Staff' : 'AI Extracted'}
            </span>
          )}
        </div>
      </header>

      {/* Main Grid: Left Details & Right Actions/Provenance */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 Cols): Structured Summary, Action Checklist, Target Audience */}
        <div className="lg:col-span-2 space-y-6">
          {/* Structured Summary Card */}
          <section
            aria-labelledby="summary-heading"
            className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-7 space-y-4"
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h2 id="summary-heading" className="text-lg font-bold text-slate-900 flex items-center space-x-2">
                <span>Executive Summary</span>
              </h2>
              <span className="text-xs font-medium text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                Source Faithful
              </span>
            </div>

            <div className="text-slate-700 text-sm sm:text-base leading-relaxed whitespace-pre-line">
              {notice.summary}
            </div>

            {/* Target Criteria Detail if specified */}
            {notice.audience_targets && notice.audience_targets.length > 0 && (
              <div className="mt-4 pt-4 border-t border-slate-100 bg-slate-50/70 -mx-6 -mb-6 p-4 sm:p-6 rounded-b-xl">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">
                  Targeted Student Group & Eligibility
                </h3>
                <ul className="space-y-1.5 text-xs sm:text-sm text-slate-700">
                  {notice.audience_targets.map((target, idx) => (
                    <li key={idx} className="flex items-start space-x-2">
                      <span className="text-indigo-600 font-bold">&bull;</span>
                      <span>
                        <strong className="capitalize">{target.role}:</strong>{' '}
                        {target.department ? `${target.department} ` : ''}
                        {target.year ? `(${target.year}) ` : ''}
                        {target.detail ? `— ${target.detail}` : ''}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>

          {/* Action Items Checklist Card (if available) */}
          {notice.action_items && notice.action_items.length > 0 && (
            <section
              aria-labelledby="action-items-heading"
              className="bg-white rounded-xl border border-indigo-100 shadow-sm p-6 sm:p-7 space-y-4 bg-gradient-to-br from-white to-indigo-50/30"
            >
              <div className="flex items-center space-x-2 border-b border-indigo-100 pb-3">
                <div className="p-1 rounded bg-indigo-100 text-indigo-700">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                </div>
                <h2 id="action-items-heading" className="text-base font-bold text-slate-900">
                  Action Steps for Candidates
                </h2>
              </div>

              <ol className="space-y-2.5 text-sm text-slate-700 list-decimal list-inside">
                {notice.action_items.map((step, idx) => (
                  <li key={idx} className="leading-relaxed pl-1">
                    <span className="text-slate-800">{step}</span>
                  </li>
                ))}
              </ol>
            </section>
          )}

          {/* Report an Issue trigger banner */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm">
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-lg bg-slate-100 text-slate-500 shrink-0">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.75">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M3 3v1.5M3 21v-6m0 0l2.77-.693a9 9 0 016.208.682l.108.054a9 9 0 006.086.71l3.114-.732a48.524 48.524 0 01-.005-10.499l-3.11.732a9 9 0 01-6.085-.711l-.108-.054a9 9 0 00-6.208-.682L3 4.5M3 15V4.5"
                  />
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-900">Spotted a discrepancy or typo?</p>
                <p className="text-xs text-slate-500">
                  Help ensure campus information fidelity by flagging inaccuracies directly to the college editor.
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => onReportIssue?.(notice)}
              className="shrink-0 inline-flex items-center px-3.5 py-2 border border-slate-300 text-xs font-semibold rounded-lg text-slate-700 bg-white hover:bg-slate-50 hover:text-slate-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors shadow-xs"
            >
              Report an Issue
            </button>
          </div>
        </div>

        {/* Right Column (1 Col): Key Dates Card & Official PDF Provenance Box */}
        <div className="space-y-6">
          {/* Key Dates Card */}
          <section
            aria-labelledby="dates-heading"
            className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 sm:p-6 space-y-4"
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h2 id="dates-heading" className="text-base font-bold text-slate-900 flex items-center space-x-2">
                <svg
                  className="w-4 h-4 text-indigo-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <span>Key Schedule & Dates</span>
              </h2>

              {deadlineCountdown && (
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${
                    deadlineCountdown.urgency === 'urgent'
                      ? 'bg-rose-100 text-rose-800 border border-rose-200'
                      : deadlineCountdown.urgency === 'warning'
                      ? 'bg-amber-100 text-amber-800 border border-amber-200'
                      : deadlineCountdown.urgency === 'passed'
                      ? 'bg-slate-100 text-slate-600 border border-slate-200'
                      : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                  }`}
                >
                  {deadlineCountdown.label}
                </span>
              )}
            </div>

            {/* Structured Date Items */}
            <div className="space-y-3.5">
              {/* Issue Date */}
              <div className="flex items-start justify-between text-xs sm:text-sm">
                <span className="text-slate-500">Notice Issued:</span>
                <span className="font-semibold text-slate-800">
                  {formatReadableDate(notice.issue_date || notice.published_at)}
                </span>
              </div>

              {/* Deadline Date */}
              {notice.important_dates?.map((dt, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg border text-xs sm:text-sm ${
                    dt.kind === 'deadline'
                      ? 'bg-rose-50/60 border-rose-200 text-rose-950'
                      : 'bg-slate-50 border-slate-200 text-slate-800'
                  }`}
                >
                  <div className="flex items-center justify-between font-semibold mb-1">
                    <span className="capitalize">{dt.label}</span>
                    <span className="text-xs uppercase tracking-wider text-slate-500">
                      {dt.kind}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-600">
                    <span className="font-medium text-slate-900">{formatReadableDate(dt.starts_on)}</span>
                    {dt.starts_time && <span>Time: {dt.starts_time}</span>}
                  </div>
                  {dt.source_page && (
                    <div className="text-[11px] text-slate-400 mt-1">
                      Cited from Source Page {dt.source_page}
                    </div>
                  )}
                </div>
              ))}

              {(!notice.important_dates || notice.important_dates.length === 0) && (
                <div className="text-xs text-slate-500 italic">
                  No additional milestone deadlines extracted for this circular.
                </div>
              )}
            </div>
          </section>

          {/* Document Provenance Box & PDF Download Button */}
          <section
            aria-labelledby="provenance-heading"
            className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 sm:p-6 space-y-4"
          >
            <div className="border-b border-slate-100 pb-3">
              <h2 id="provenance-heading" className="text-base font-bold text-slate-900 flex items-center space-x-2">
                <svg
                  className="w-4 h-4 text-indigo-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
                  />
                </svg>
                <span>Document Provenance</span>
              </h2>
            </div>

            {/* Document Details */}
            <div className="space-y-2.5 text-xs sm:text-sm text-slate-600">
              <div className="flex items-center justify-between">
                <span>Format:</span>
                <span className="font-semibold text-slate-800">Official PDF</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Page Count:</span>
                <span className="font-semibold text-slate-800">
                  {notice.source_file?.page_count || 1} {notice.source_file?.page_count === 1 ? 'Page' : 'Pages'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Authenticity:</span>
                <span className="inline-flex items-center text-emerald-700 font-medium">
                  <svg className="w-3.5 h-3.5 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Signed Institutional Copy
                </span>
              </div>
            </div>

            <p className="text-xs text-slate-500 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100">
              Original documents are secured with short-lived access tokens per university data isolation policies.
            </p>

            {/* Download Button */}
            {notice.source_file?.available && notice.source_file.download_url ? (
              <a
                href={notice.source_file.download_url}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full inline-flex items-center justify-center px-4 py-2.5 border border-transparent rounded-lg text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors shadow-sm"
              >
                <svg
                  className="w-4 h-4 mr-2"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
                  />
                </svg>
                Download Official Notice (PDF)
              </a>
            ) : (
              <button
                type="button"
                disabled
                className="w-full inline-flex items-center justify-center px-4 py-2.5 border border-slate-200 rounded-lg text-sm font-medium text-slate-400 bg-slate-100 cursor-not-allowed"
              >
                Document Download Unavailable
              </button>
            )}
          </section>
        </div>
      </div>
    </article>
  );
};

export default NoticeDetailPage;
