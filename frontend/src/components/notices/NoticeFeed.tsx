import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Notice, AudienceType } from '../../types/notice';
import { mockNotices } from '../../mocks/mockNotices';
import { fetchNotices } from '../../services/api';
import { NoticeCard } from './NoticeCard';

export type AudienceFilter = 'All' | 'Student' | 'Faculty' | 'Staff';

const AUDIENCE_OPTIONS: AudienceFilter[] = ['All', 'Student', 'Faculty', 'Staff'];

const CATEGORY_OPTIONS = [
  'All Categories',
  'Admissions',
  'Exams',
  'General',
  'Scholarships',
];

/**
 * Animated Loading Skeleton Card mimicking NoticeCard layout
 */
export const NoticeSkeletonCard: React.FC = () => {
  return (
    <div
      className="bg-white rounded-xl border border-slate-200/90 shadow-sm p-5 sm:p-6 flex flex-col justify-between animate-pulse"
      aria-hidden="true"
    >
      <div>
        {/* Badges line */}
        <div className="flex items-center justify-between gap-2 mb-4">
          <div className="flex items-center gap-2">
            <div className="h-5 w-20 bg-slate-200 rounded-full"></div>
            <div className="h-5 w-16 bg-slate-100 rounded-full"></div>
          </div>
          <div className="h-5 w-28 bg-slate-200 rounded-full"></div>
        </div>

        {/* Title skeleton */}
        <div className="space-y-2 mb-4">
          <div className="h-5 bg-slate-200 rounded w-5/6"></div>
          <div className="h-5 bg-slate-200 rounded w-2/3"></div>
        </div>

        {/* Summary snippet skeleton */}
        <div className="space-y-2 mb-6">
          <div className="h-4 bg-slate-100 rounded w-full"></div>
          <div className="h-4 bg-slate-100 rounded w-4/5"></div>
        </div>
      </div>

      {/* Footer skeleton */}
      <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
        <div className="h-3.5 bg-slate-200 rounded w-32"></div>
        <div className="h-3.5 bg-slate-200 rounded w-20"></div>
      </div>
    </div>
  );
};

export interface NoticeFeedProps {
  className?: string;
  onNoticeSelect?: (notice: Notice) => void;
}

/**
 * NoticeFeed Component
 * Renders the public notice feed with interactive audience chips,
 * category dropdown, 4 animated loading skeletons, empty state,
 * and automatic API fetch with offline mock fallback.
 */
export const NoticeFeed: React.FC<NoticeFeedProps> = ({
  className = '',
  onNoticeSelect,
}) => {
  const [selectedAudience, setSelectedAudience] = useState<AudienceFilter>('All');
  const [selectedCategory, setSelectedCategory] = useState<string>('All Categories');
  const [notices, setNotices] = useState<Notice[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isUsingMock, setIsUsingMock] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Map AudienceFilter to backend API param format
  const getAudienceParam = (filter: AudienceFilter): AudienceType | undefined => {
    switch (filter) {
      case 'Student':
        return 'student';
      case 'Faculty':
        return 'faculty';
      case 'Staff':
        return 'staff';
      case 'All':
      default:
        return undefined; // Omitted or 'all' represents unfiltered view in API_CONTRACTS §5.1
    }
  };

  const loadNotices = useCallback(async () => {
    setIsLoading(true);
    setErrorMsg(null);

    const audienceParam = getAudienceParam(selectedAudience);
    const categoryParam =
      selectedCategory === 'All Categories' ? undefined : selectedCategory.toLowerCase();

    try {
      const response = await fetchNotices({
        audience: audienceParam,
        category: categoryParam,
      });

      if (response && Array.isArray(response.items) && response.items.length > 0) {
        setNotices(response.items);
        setIsUsingMock(false);
      } else {
        // If API succeeded but returned empty list from DB, verify or fall back if testing locally
        setNotices(response.items || []);
        setIsUsingMock(false);
      }
    } catch {
      // Backend is offline or endpoint not yet deployed -> fallback to mockNotices
      setIsUsingMock(true);
      setNotices(mockNotices);
    } finally {
      // Add slight delay to avoid jarring layout shifts when loading
      setIsLoading(false);
    }
  }, [selectedAudience, selectedCategory]);

  useEffect(() => {
    loadNotices();
  }, [loadNotices]);

  // Client-side filtering (applied when using mockNotices fallback)
  const filteredNotices = useMemo(() => {
    if (!isUsingMock) {
      // When live API is connected, the server already applies filter parameters
      return notices;
    }

    return notices.filter((notice) => {
      // 1. Audience Filter
      // Per API_CONTRACTS §5.1:
      // - 'All': includes all notices
      // - Role filter ('Student', 'Faculty', 'Staff'): includes targeted notices + notices targeting 'all'
      let matchesAudience = true;
      if (selectedAudience === 'Student') {
        matchesAudience = notice.audience === 'student' || notice.audience === 'all';
      } else if (selectedAudience === 'Faculty') {
        matchesAudience = notice.audience === 'faculty' || notice.audience === 'all';
      } else if (selectedAudience === 'Staff') {
        matchesAudience = notice.audience === 'staff' || notice.audience === 'all';
      }

      // 2. Category Filter
      let matchesCategory = true;
      if (selectedCategory !== 'All Categories') {
        const catNotice = notice.category.toLowerCase();
        const catFilter = selectedCategory.toLowerCase();
        matchesCategory =
          catNotice === catFilter ||
          (catFilter === 'exams' && (catNotice === 'examination' || catNotice === 'exam')) ||
          (catFilter === 'admissions' && catNotice === 'admission');
      }

      return matchesAudience && matchesCategory;
    });
  }, [notices, isUsingMock, selectedAudience, selectedCategory]);

  const handleResetFilters = () => {
    setSelectedAudience('All');
    setSelectedCategory('All Categories');
  };

  const hasActiveFilters =
    selectedAudience !== 'All' || selectedCategory !== 'All Categories';

  return (
    <section className={`w-full space-y-6 ${className}`}>
      {/* Feed Control Bar: Audience Chips & Category Select */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 sm:p-5 shadow-sm space-y-4 sm:space-y-0 sm:flex sm:items-center sm:justify-between sm:gap-4">
        {/* Audience Chips */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider mr-1">
            Audience:
          </span>
          {AUDIENCE_OPTIONS.map((audience) => {
            const isActive = selectedAudience === audience;
            return (
              <button
                key={audience}
                type="button"
                onClick={() => setSelectedAudience(audience)}
                className={`inline-flex items-center px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-sm ring-2 ring-indigo-600/20'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200/80 hover:text-slate-900'
                }`}
                aria-pressed={isActive}
              >
                {audience}
              </button>
            );
          })}
        </div>

        {/* Category Select Dropdown */}
        <div className="flex items-center space-x-2">
          <label
            htmlFor="category-select"
            className="text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap"
          >
            Category:
          </label>
          <div className="relative min-w-[170px]">
            <select
              id="category-select"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full appearance-none rounded-lg border border-slate-300 bg-white px-3.5 py-1.5 pr-8 text-sm font-medium text-slate-800 shadow-sm hover:border-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-colors"
            >
              {CATEGORY_OPTIONS.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-500">
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="2"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Fallback / Status Banner if using mock data */}
      {isUsingMock && (
        <div className="flex items-center justify-between bg-amber-50 border border-amber-200/80 rounded-lg px-4 py-2.5 text-xs text-amber-800">
          <div className="flex items-center space-x-2">
            <svg
              className="w-4 h-4 text-amber-600 shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth="2"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
              />
            </svg>
            <span>
              Backend notice endpoint offline. Displaying verified local mock notices.
            </span>
          </div>
          <button
            onClick={loadNotices}
            className="text-amber-900 underline font-semibold hover:text-amber-950 ml-2"
          >
            Retry Connection
          </button>
        </div>
      )}

      {errorMsg && (
        <div className="bg-rose-50 border border-rose-200 rounded-lg p-4 text-sm text-rose-700">
          {errorMsg}
        </div>
      )}

      {/* Main Notice Feed Content */}
      {isLoading ? (
        /* 4 Animated Skeleton Placeholders */
        <div
          className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6"
          aria-label="Loading notice feed"
        >
          {Array.from({ length: 4 }).map((_, idx) => (
            <NoticeSkeletonCard key={idx} />
          ))}
        </div>
      ) : filteredNotices.length > 0 ? (
        /* Grid of Notice Cards */
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium px-1">
            <span>
              Showing {filteredNotices.length}{' '}
              {filteredNotices.length === 1 ? 'notice' : 'notices'}
            </span>
            {hasActiveFilters && (
              <button
                onClick={handleResetFilters}
                className="text-indigo-600 hover:text-indigo-800 font-semibold"
              >
                Clear all filters
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
            {filteredNotices.map((notice) => (
              <NoticeCard
                key={notice.id}
                notice={notice}
                onClick={onNoticeSelect}
              />
            ))}
          </div>
        </div>
      ) : (
        /* Empty State */
        <div className="bg-white rounded-xl border border-dashed border-slate-300 p-12 text-center flex flex-col items-center justify-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
            <svg
              className="w-6 h-6"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth="1.5"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
              />
            </svg>
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-slate-900">
              No notices found for the selected filter.
            </h3>
            <p className="text-sm text-slate-500 max-w-sm">
              Try selecting a different audience chip or changing the category dropdown.
            </p>
          </div>
          {hasActiveFilters && (
            <button
              type="button"
              onClick={handleResetFilters}
              className="inline-flex items-center px-4 py-2 border border-slate-300 rounded-lg text-sm font-medium text-slate-700 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors shadow-sm"
            >
              Reset Filters
            </button>
          )}
        </div>
      )}
    </section>
  );
};

export default NoticeFeed;
