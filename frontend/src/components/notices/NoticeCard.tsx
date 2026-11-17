import React from 'react';
import { Notice, AudienceType } from '../../types/notice';

export interface NoticeCardProps {
  notice: Notice;
  onClick?: (notice: Notice) => void;
  className?: string;
}

/**
 * Maps audience enum to human-friendly display label per docs/API_CONTRACTS.md §5.1
 */
const AUDIENCE_LABELS: Record<AudienceType, string> = {
  student: 'Students',
  faculty: 'Faculty',
  staff: 'Staff',
  all: 'Everyone',
  unspecified: 'Not specified',
};

/**
 * Formats ISO date string into human readable 'Nov 12, 2026' format
 */
const formatPublicationDate = (dateStr: string): string => {
  if (!dateStr) return '';
  try {
    // If string is YYYY-MM-DD, parse year, month, day to avoid timezone shift
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

/**
 * Returns Tailwind badge styling based on notice category:
 * - Blue for Admissions
 * - Amber for Exams
 * - Emerald for General
 */
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
  // Default to Emerald for General / other
  return 'bg-emerald-50 text-emerald-700 border-emerald-200 ring-1 ring-emerald-600/10';
};

/**
 * Component: NoticeCard
 * Public notice presentation card with prominent typography,
 * category & audience pills, formatted dates, deadline badges, and clamped summary.
 */
export const NoticeCard: React.FC<NoticeCardProps> = ({
  notice,
  onClick,
  className = '',
}) => {
  const formattedPubDate = formatPublicationDate(notice.publication_date);
  const normalizedAudience = (notice.audience || 'unspecified').toLowerCase() as AudienceType;
  const audienceLabel = AUDIENCE_LABELS[normalizedAudience] || notice.audience;
  const categoryStyle = getCategoryBadgeStyle(notice.category);

  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    if (onClick) {
      e.preventDefault();
      onClick(notice);
    }
  };

  return (
    <article
      className={`group relative bg-white rounded-xl border border-slate-200/90 shadow-sm hover:shadow-md hover:border-indigo-300 transition-all duration-200 flex flex-col justify-between overflow-hidden ${className}`}
    >
      <a
        href={`/notices/${notice.id}`}
        onClick={handleClick}
        className="p-5 sm:p-6 flex flex-col h-full focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 rounded-xl"
        aria-label={`Notice: ${notice.title}`}
      >
        {/* Top Meta Bar: Category, Audience Pill, and Deadlines */}
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <div className="flex flex-wrap items-center gap-2">
            {/* Category Badge */}
            <span
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider border ${categoryStyle}`}
            >
              {notice.category}
            </span>

            {/* Audience Pill */}
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
              <svg
                className="w-3 h-3 mr-1 text-slate-500"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="2"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"
                />
              </svg>
              {audienceLabel}
            </span>
          </div>

          {/* Urgent / Deadline Badge */}
          {notice.deadline_date && (
            <span
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
                notice.is_urgent
                  ? 'bg-rose-50 text-rose-700 border-rose-200 ring-1 ring-rose-600/10 animate-pulse'
                  : 'bg-amber-50 text-amber-800 border-amber-200 ring-1 ring-amber-600/10'
              }`}
            >
              <svg
                className={`w-3.5 h-3.5 mr-1 ${notice.is_urgent ? 'text-rose-600' : 'text-amber-600'}`}
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="2"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5"
                />
              </svg>
              Deadline: {notice.deadline_date}
            </span>
          )}
        </div>

        {/* Notice Title */}
        <h2 className="text-lg sm:text-xl font-bold text-slate-900 group-hover:text-indigo-600 transition-colors leading-snug tracking-tight mb-2.5">
          {notice.title}
        </h2>

        {/* Summary Snippet - Clamped to 2 lines */}
        <p className="text-sm text-slate-600 line-clamp-2 leading-relaxed mb-4 flex-1">
          {notice.summary_snippet}
        </p>

        {/* Card Footer: Publication Date & Page Count Meta */}
        <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 font-medium">
          <div className="flex items-center space-x-1.5">
            <svg
              className="w-3.5 h-3.5 text-slate-400"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth="2"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>Published on {formattedPubDate}</span>
          </div>

          <div className="flex items-center space-x-3">
            {notice.source_page_count > 0 && (
              <span className="text-slate-400">
                {notice.source_page_count} {notice.source_page_count === 1 ? 'page' : 'pages'}
              </span>
            )}
            <span className="inline-flex items-center text-indigo-600 font-semibold group-hover:translate-x-0.5 transition-transform">
              View Notice
              <svg
                className="w-3.5 h-3.5 ml-1"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="2.5"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
              </svg>
            </span>
          </div>
        </div>
      </a>
    </article>
  );
};

export default NoticeCard;
