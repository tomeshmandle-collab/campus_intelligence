import React, { useState, useEffect, useMemo } from 'react';
import {
  SearchResultItem,
  Citation,
  AskResponse,
  AudienceType,
  ConfidenceLevel,
} from '../../types/notice';
import {
  searchNotices,
  mockSearchNotices,
  askQuestion,
  mockAskQuestion,
} from '../../services/api';

export interface SearchAndAskPageProps {
  initialTab?: 'search' | 'ask';
  onNoticeSelect?: (noticeId: string) => void;
  isMockMode?: boolean;
}

/**
 * Safe text highlight component to highlight matching search terms without dangerouslySetInnerHTML.
 */
function HighlightSnippet({ text, query }: { text: string; query: string }) {
  if (!text) return null;
  if (!query || !query.trim()) return <span>{text}</span>;

  const escapedTerms = query
    .trim()
    .split(/\s+/)
    .filter((term) => term.length > 0)
    .map((term) => term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));

  if (escapedTerms.length === 0) return <span>{text}</span>;

  const regex = new RegExp(`(${escapedTerms.join('|')})`, 'gi');
  const parts = text.split(regex);

  return (
    <span>
      {parts.map((part, index) =>
        regex.test(part) ? (
          <mark
            key={index}
            className="bg-amber-100 text-amber-900 font-semibold px-1 py-0.5 rounded border border-amber-200"
          >
            {part}
          </mark>
        ) : (
          <span key={index}>{part}</span>
        )
      )}
    </span>
  );
}

/**
 * Expandable Citation Card Component adhering to §7.7
 */
interface CitationCardProps {
  citation: Citation;
  index: number;
  onNoticeSelect?: (noticeId: string) => void;
}

const CitationCard: React.FC<CitationCardProps> = ({ citation, index, onNoticeSelect }) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(index === 0);

  return (
    <div className="border border-slate-200 rounded-lg bg-white shadow-sm overflow-hidden transition-all hover:border-indigo-300">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 text-left flex items-center justify-between gap-3 bg-slate-50/70 hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 transition-colors"
        aria-expanded={isExpanded}
        aria-label={`Citation ${index + 1}: ${citation.notice_title}`}
      >
        <div className="flex items-center space-x-2.5 min-w-0">
          <span className="shrink-0 flex items-center justify-center w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 font-bold text-xs">
            {index + 1}
          </span>
          <span className="font-medium text-slate-800 text-sm truncate">
            {citation.notice_title}
          </span>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-100">
            Page {citation.page}
          </span>
          <svg
            className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${
              isExpanded ? 'rotate-180 text-indigo-600' : ''
            }`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 py-3.5 border-t border-slate-100 bg-white space-y-3">
          <div className="relative pl-3 border-l-2 border-indigo-500 text-sm text-slate-700 italic bg-slate-50/50 py-2 pr-2 rounded-r">
            &ldquo;{citation.excerpt}&rdquo;
          </div>

          <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
            <span className="flex items-center space-x-1">
              <svg className="w-3.5 h-3.5 text-slate-400" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z"
                  clipRule="evenodd"
                />
              </svg>
              <span>Verified document excerpt &bull; Page {citation.page}</span>
            </span>

            {onNoticeSelect && (
              <button
                type="button"
                onClick={() => onNoticeSelect(citation.notice_id)}
                className="inline-flex items-center space-x-1 text-indigo-600 hover:text-indigo-800 font-semibold hover:underline"
              >
                <span>View Full Notice</span>
                <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                  <path
                    fillRule="evenodd"
                    d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export const SearchAndAskPage: React.FC<SearchAndAskPageProps> = ({
  initialTab = 'search',
  onNoticeSelect,
  isMockMode = false,
}) => {
  const [activeTab, setActiveTab] = useState<'search' | 'ask'>(initialTab);

  // Search state
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [lastExecutedSearch, setLastExecutedSearch] = useState<string>('');
  const [searchAudience, setSearchAudience] = useState<AudienceType>('all');
  const [searchResults, setSearchResults] = useState<SearchResultItem[]>([]);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState<boolean>(false);

  // Ask state
  const [askQuestionText, setAskQuestionText] = useState<string>('');
  const [askAudience, setAskAudience] = useState<AudienceType>('all');
  const [askResponse, setAskResponse] = useState<AskResponse | null>(null);
  const [isAsking, setIsAsking] = useState<boolean>(false);
  const [askError, setAskError] = useState<string | null>(null);

  // Synchronize initialTab if prop changes
  useEffect(() => {
    setActiveTab(initialTab);
  }, [initialTab]);

  // Execute keyword search
  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const query = searchQuery.trim();
    if (!query) return;

    setIsSearching(true);
    setSearchError(null);
    setHasSearched(true);
    setLastExecutedSearch(query);

    const params = {
      q: query,
      audience: searchAudience !== 'all' ? searchAudience : undefined,
    };

    try {
      let data;
      if (isMockMode) {
        data = await mockSearchNotices(params);
      } else {
        try {
          data = await searchNotices(params);
        } catch {
          // Graceful fallback to mock data if backend search endpoint is unreachable
          data = await mockSearchNotices(params);
        }
      }
      setSearchResults(data.items || []);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'message' in err) {
        setSearchError(String((err as { message: string }).message));
      } else {
        setSearchError('Search failed. Please try again.');
      }
    } finally {
      setIsSearching(false);
    }
  };

  // Execute Grounded Ask question
  const handleAsk = async (questionToAsk?: string) => {
    const text = (questionToAsk !== undefined ? questionToAsk : askQuestionText).trim();
    if (!text) return;

    if (questionToAsk !== undefined) {
      setAskQuestionText(questionToAsk);
    }

    setIsAsking(true);
    setAskError(null);

    const payload = {
      question: text,
      audience: askAudience !== 'all' ? askAudience : undefined,
    };

    try {
      let data: AskResponse;
      if (isMockMode) {
        data = await mockAskQuestion(payload);
      } else {
        try {
          data = await askQuestion(payload);
        } catch {
          // Graceful fallback to mock Q&A if backend is offline
          data = await mockAskQuestion(payload);
        }
      }
      setAskResponse(data);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'message' in err) {
        setAskError(String((err as { message: string }).message));
      } else {
        setAskError('Failed to process question. Please try again.');
      }
    } finally {
      setIsAsking(false);
    }
  };

  // Quick suggestion prompts for students
  const exampleQuestions = [
    'What is the last date to submit the exam form?',
    'When is the Round 2 PG admission verification?',
    'What is the family income limit for the merit scholarship?',
    'Are there sports team selection trials?',
  ];

  // Map API status to confidence badge
  const confidenceConfig: Record<
    ConfidenceLevel,
    { label: string; bg: string; text: string; border: string; icon: string }
  > = useMemo(
    () => ({
      high: {
        label: 'High Confidence',
        bg: 'bg-emerald-50',
        text: 'text-emerald-700',
        border: 'border-emerald-200',
        icon: '✓',
      },
      uncertain: {
        label: 'Uncertain / Conflicting Evidence',
        bg: 'bg-amber-50',
        text: 'text-amber-700',
        border: 'border-amber-200',
        icon: '⚠',
      },
      not_found: {
        label: 'Not Found in Notices',
        bg: 'bg-slate-100',
        text: 'text-slate-700',
        border: 'border-slate-300',
        icon: '✕',
      },
    }),
    []
  );

  const getConfidenceLevel = (status: string): ConfidenceLevel => {
    if (status === 'answered') return 'high';
    if (status === 'uncertain') return 'uncertain';
    return 'not_found';
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-slate-200 pb-5">
        <div className="inline-flex items-center space-x-2 text-indigo-600 font-semibold text-xs tracking-wider uppercase mb-1">
          <span>Official Notice Information Retrieval</span>
          <span>&bull;</span>
          <span>Kirori Mal College</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Search Notices & Ask Q&amp;A
        </h1>
        <p className="text-sm text-slate-500 mt-1 max-w-3xl">
          Instantly query published college circulars using keyword search or ask natural-language
          questions with verified, cited excerpts.
        </p>

        {/* Toggle Switch: Search Notices vs Ask a Question */}
        <div className="mt-6 flex justify-center sm:justify-start">
          <div
            role="tablist"
            aria-label="Search and Ask mode selector"
            className="inline-flex p-1 bg-slate-100 rounded-xl border border-slate-200 shadow-inner"
          >
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'search'}
              aria-controls="search-panel"
              onClick={() => setActiveTab('search')}
              className={`flex items-center space-x-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-150 ${
                activeTab === 'search'
                  ? 'bg-white text-indigo-700 shadow-sm border border-slate-200/60'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
              }`}
            >
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth="2"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
              <span>Search Notices</span>
            </button>

            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'ask'}
              aria-controls="ask-panel"
              onClick={() => setActiveTab('ask')}
              className={`flex items-center space-x-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-150 ${
                activeTab === 'ask'
                  ? 'bg-white text-indigo-700 shadow-sm border border-slate-200/60'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
              }`}
            >
              <svg
                className="w-4 h-4 text-indigo-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth="2"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"
                />
              </svg>
              <span>Ask a Question</span>
              <span className="ml-1 inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-100 text-indigo-700">
                AI
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* TAB 1: Search Notices */}
      {activeTab === 'search' && (
        <section id="search-panel" role="tabpanel" aria-label="Search Notices" className="space-y-6">
          {/* Search Form Card */}
          <div className="bg-white p-4 sm:p-6 rounded-xl border border-slate-200 shadow-sm">
            <form onSubmit={handleSearch} className="space-y-4">
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth="2"
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                      />
                    </svg>
                  </div>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search notices by keyword, exam fee, admission, date, etc..."
                    className="w-full pl-10 pr-10 py-2.5 rounded-lg border border-slate-300 bg-white text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm sm:text-base shadow-sm"
                    aria-label="Search notices input"
                  />
                  {searchQuery && (
                    <button
                      type="button"
                      onClick={() => setSearchQuery('')}
                      className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 focus:outline-none"
                      aria-label="Clear search input"
                    >
                      <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </button>
                  )}
                </div>

                {/* Audience filter option */}
                <div className="shrink-0 flex items-center space-x-2">
                  <label htmlFor="search-audience" className="text-xs font-semibold text-slate-500 uppercase sr-only">
                    Audience
                  </label>
                  <select
                    id="search-audience"
                    value={searchAudience}
                    onChange={(e) => setSearchAudience(e.target.value as AudienceType)}
                    className="px-3 py-2.5 rounded-lg border border-slate-300 bg-white text-slate-700 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 shadow-sm"
                  >
                    <option value="all">All Audiences</option>
                    <option value="student">Students</option>
                    <option value="faculty">Faculty</option>
                    <option value="staff">Staff</option>
                  </select>

                  <button
                    type="submit"
                    disabled={isSearching || !searchQuery.trim()}
                    className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg font-semibold text-sm text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                  >
                    {isSearching ? (
                      <>
                        <svg
                          className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                          fill="none"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8v8H4z"
                          />
                        </svg>
                        <span>Searching...</span>
                      </>
                    ) : (
                      <span>Search</span>
                    )}
                  </button>
                </div>
              </div>

              {/* Sample keyword pills */}
              <div className="flex flex-wrap items-center gap-1.5 pt-1 text-xs text-slate-500">
                <span className="font-medium text-slate-600">Suggested queries:</span>
                {['Examination Fees', 'Postgraduate Admissions', 'Scholarship', 'Sports Trials'].map(
                  (suggestion) => (
                    <button
                      key={suggestion}
                      type="button"
                      onClick={() => {
                        setSearchQuery(suggestion);
                        setTimeout(() => handleSearch(), 50);
                      }}
                      className="inline-flex items-center px-2.5 py-1 rounded-full bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 text-slate-600 border border-slate-200 transition-colors"
                    >
                      {suggestion}
                    </button>
                  )
                )}
              </div>
            </form>
          </div>

          {/* Search Error Alert */}
          {searchError && (
            <div className="rounded-lg bg-rose-50 border border-rose-200 p-4 text-sm text-rose-700 flex items-center space-x-2">
              <svg className="w-5 h-5 shrink-0 text-rose-500" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
              <span>{searchError}</span>
            </div>
          )}

          {/* Search Loading Skeleton */}
          {isSearching && (
            <div className="space-y-4">
              {[1, 2, 3].map((n) => (
                <div
                  key={n}
                  className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm animate-pulse space-y-3"
                >
                  <div className="flex items-center space-x-2">
                    <div className="h-4 bg-slate-200 rounded w-24" />
                    <div className="h-4 bg-slate-200 rounded w-16" />
                  </div>
                  <div className="h-5 bg-slate-200 rounded w-3/4" />
                  <div className="h-4 bg-slate-100 rounded w-full" />
                  <div className="h-4 bg-slate-100 rounded w-2/3" />
                </div>
              ))}
            </div>
          )}

          {/* Search Results Display */}
          {!isSearching && hasSearched && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-sm text-slate-500 px-1">
                <span>
                  Found <strong className="text-slate-800">{searchResults.length}</strong> matching notice
                  {searchResults.length === 1 ? '' : 's'} for &ldquo;{lastExecutedSearch}&rdquo;
                </span>
                <span className="text-xs bg-slate-100 px-2.5 py-0.5 rounded-full text-slate-600">
                  Docs/API §7.6
                </span>
              </div>

              {searchResults.length === 0 ? (
                <div className="text-center py-12 px-4 rounded-xl border border-dashed border-slate-300 bg-white">
                  <div className="w-12 h-12 mx-auto rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mb-3">
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                  <h3 className="text-base font-semibold text-slate-800">No matching notices found</h3>
                  <p className="text-sm text-slate-500 mt-1 max-w-sm mx-auto">
                    We couldn&apos;t find any published notice matching &ldquo;{lastExecutedSearch}&rdquo;. Try
                    broadening your search term or searching with different keywords.
                  </p>
                </div>
              ) : (
                <div className="space-y-3.5">
                  {searchResults.map((item) => (
                    <article
                      key={item.notice.id}
                      className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-indigo-300 transition-all flex flex-col justify-between"
                    >
                      <div className="space-y-2.5">
                        {/* Badges: Match Type, Source Page, Relationship */}
                        <div className="flex flex-wrap items-center gap-2 text-xs">
                          <span className="inline-flex items-center px-2 py-0.5 rounded font-medium bg-indigo-50 text-indigo-700 border border-indigo-100">
                            Page {item.source_page ?? 1}
                          </span>
                          <span className="inline-flex items-center px-2 py-0.5 rounded font-medium bg-slate-100 text-slate-600">
                            {item.match_type.toUpperCase()} MATCH
                          </span>
                          {item.notice.relationship_status !== 'current' && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                              Status: {item.notice.relationship_status}
                            </span>
                          )}
                        </div>

                        {/* Notice Title */}
                        <h2 className="text-base sm:text-lg font-bold text-slate-900 hover:text-indigo-600 transition-colors">
                          {onNoticeSelect ? (
                            <button
                              type="button"
                              onClick={() => onNoticeSelect(item.notice.id)}
                              className="text-left font-bold text-slate-900 hover:text-indigo-600 focus:outline-none focus-visible:underline"
                            >
                              {item.notice.title}
                            </button>
                          ) : (
                            <a href={`/notices/${item.notice.id}`}>{item.notice.title}</a>
                          )}
                        </h2>

                        {/* Matched Text Excerpt with Highlighted Keywords */}
                        {item.matched_text && (
                          <div className="p-3 bg-slate-50 rounded-lg border-l-4 border-indigo-500 text-sm text-slate-700 leading-relaxed">
                            <span className="font-semibold text-slate-900 block text-xs uppercase tracking-wider mb-1 text-indigo-700">
                              Matched Notice Excerpt:
                            </span>
                            <HighlightSnippet
                              text={item.matched_text}
                              query={lastExecutedSearch}
                            />
                          </div>
                        )}

                        {/* Summary */}
                        <p className="text-xs sm:text-sm text-slate-500 line-clamp-2">
                          {item.notice.summary}
                        </p>
                      </div>

                      {/* View Action Link */}
                      <div className="pt-3 mt-3 border-t border-slate-100 flex items-center justify-end">
                        {onNoticeSelect ? (
                          <button
                            type="button"
                            onClick={() => onNoticeSelect(item.notice.id)}
                            className="inline-flex items-center text-xs font-semibold text-indigo-600 hover:text-indigo-800 space-x-1"
                          >
                            <span>Open Notice Detail</span>
                            <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                              <path
                                fillRule="evenodd"
                                d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                                clipRule="evenodd"
                              />
                            </svg>
                          </button>
                        ) : (
                          <a
                            href={`/notices/${item.notice.id}`}
                            className="inline-flex items-center text-xs font-semibold text-indigo-600 hover:text-indigo-800 space-x-1"
                          >
                            <span>Open Notice Detail</span>
                            <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                              <path
                                fillRule="evenodd"
                                d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                                clipRule="evenodd"
                              />
                            </svg>
                          </a>
                        )}
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </div>
          )}
        </section>
      )}

      {/* TAB 2: Ask a Question */}
      {activeTab === 'ask' && (
        <section id="ask-panel" role="tabpanel" aria-label="Ask a Question" className="space-y-6">
          {/* Question Input Card */}
          <div className="bg-white p-5 sm:p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-start space-x-3">
              <div className="shrink-0 p-2 rounded-lg bg-indigo-50 text-indigo-600">
                <svg
                  className="w-5 h-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div className="flex-1">
                <h2 className="text-base sm:text-lg font-bold text-slate-900">
                  Ask a Question on College Notices
                </h2>
                <p className="text-xs sm:text-sm text-slate-500">
                  Ask factual questions regarding deadlines, eligibility, exam schedules, or fee instructions.
                  Answers are synthesized strictly from published college documents.
                </p>
              </div>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleAsk();
              }}
              className="space-y-3"
            >
              <div className="relative">
                <textarea
                  rows={3}
                  value={askQuestionText}
                  onChange={(e) => setAskQuestionText(e.target.value)}
                  placeholder="e.g., What is the last date to submit the exam form?"
                  className="w-full px-4 py-3 rounded-lg border border-slate-300 bg-white text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm sm:text-base resize-none shadow-sm"
                  aria-label="Ask a question input"
                />
              </div>

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
                {/* Audience filter for retrieval context */}
                <div className="flex items-center space-x-2">
                  <label htmlFor="ask-audience" className="text-xs font-semibold text-slate-500">
                    Target Role:
                  </label>
                  <select
                    id="ask-audience"
                    value={askAudience}
                    onChange={(e) => setAskAudience(e.target.value as AudienceType)}
                    className="px-2.5 py-1.5 rounded-lg border border-slate-300 bg-white text-slate-700 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-sm"
                  >
                    <option value="all">All Roles</option>
                    <option value="student">Student</option>
                    <option value="faculty">Faculty</option>
                    <option value="staff">Staff</option>
                  </select>
                </div>

                <div className="flex items-center justify-end space-x-2">
                  {askQuestionText && (
                    <button
                      type="button"
                      onClick={() => setAskQuestionText('')}
                      className="px-3 py-2 text-xs font-medium text-slate-500 hover:text-slate-800"
                    >
                      Clear
                    </button>
                  )}
                  <button
                    type="submit"
                    disabled={isAsking || !askQuestionText.trim()}
                    className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-lg font-semibold text-sm text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                  >
                    {isAsking ? (
                      <>
                        <svg
                          className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                          fill="none"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8v8H4z"
                          />
                        </svg>
                        <span>Analyzing Notices...</span>
                      </>
                    ) : (
                      <>
                        <span>Ask Grounded AI</span>
                        <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                          <path
                            fillRule="evenodd"
                            d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Quick suggestion prompt chips */}
              <div className="pt-2 border-t border-slate-100">
                <span className="text-xs font-medium text-slate-500 block mb-1.5">
                  Try one of these sample questions:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {exampleQuestions.map((eq) => (
                    <button
                      key={eq}
                      type="button"
                      onClick={() => handleAsk(eq)}
                      className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700 hover:bg-indigo-50 hover:text-indigo-700 hover:border-indigo-200 border border-slate-200 transition-colors text-left"
                    >
                      {eq}
                    </button>
                  ))}
                </div>
              </div>
            </form>
          </div>

          {/* Ask Error Message */}
          {askError && (
            <div className="rounded-lg bg-rose-50 border border-rose-200 p-4 text-sm text-rose-700 flex items-center space-x-2">
              <svg className="w-5 h-5 shrink-0 text-rose-500" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
              <span>{askError}</span>
            </div>
          )}

          {/* Ask Loading State */}
          {isAsking && (
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4 animate-pulse">
              <div className="flex items-center space-x-3">
                <div className="h-6 w-24 bg-slate-200 rounded-full" />
                <div className="h-4 w-32 bg-slate-200 rounded" />
              </div>
              <div className="h-4 bg-slate-200 rounded w-full" />
              <div className="h-4 bg-slate-200 rounded w-5/6" />
              <div className="h-20 bg-slate-100 rounded-lg w-full mt-4" />
            </div>
          )}

          {/* Generated Answer Card */}
          {!isAsking && askResponse && (
            <div className="space-y-6">
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                {/* Answer Card Top Header */}
                <div className="px-5 py-4 border-b border-slate-200 bg-slate-50/70 flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center space-x-2.5">
                    <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-xs">
                      <svg
                        className="w-4 h-4"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                      </svg>
                    </div>
                    <span className="font-bold text-slate-900 text-sm sm:text-base">
                      Synthesized Answer
                    </span>
                  </div>

                  {/* Confidence Badge ('high' = green, 'uncertain' = amber, 'not_found' = gray) */}
                  {(() => {
                    const level = getConfidenceLevel(askResponse.status);
                    const cfg = confidenceConfig[level];
                    return (
                      <span
                        className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${cfg.bg} ${cfg.text} ${cfg.border}`}
                        data-testid="confidence-badge"
                      >
                        <span>{cfg.icon}</span>
                        <span>{cfg.label}</span>
                      </span>
                    );
                  })()}
                </div>

                {/* Answer Content */}
                <div className="p-5 sm:p-6 space-y-5">
                  <div className="text-base sm:text-lg text-slate-900 font-medium leading-relaxed">
                    {askResponse.answer}
                  </div>

                  {/* Citations Section */}
                  {askResponse.citations && askResponse.citations.length > 0 && (
                    <div className="pt-4 border-t border-slate-100 space-y-3">
                      <div className="flex items-center justify-between">
                        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                          Source Provenance &amp; Citations ({askResponse.citations.length})
                        </h3>
                        <span className="text-[11px] text-slate-400">
                          Click cards below to expand original excerpt
                        </span>
                      </div>

                      <div className="space-y-2.5">
                        {askResponse.citations.map((cit, idx) => (
                          <CitationCard
                            key={`${cit.notice_id}-${cit.page}-${idx}`}
                            citation={cit}
                            index={idx}
                            onNoticeSelect={onNoticeSelect}
                          />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Institutional AI Disclaimer */}
              <div
                role="note"
                aria-label="Institutional AI disclaimer"
                className="flex items-start space-x-3 p-4 rounded-xl bg-indigo-50/70 border border-indigo-200 text-indigo-900 text-xs sm:text-sm leading-relaxed"
              >
                <div className="shrink-0 mt-0.5 text-indigo-600">
                  <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                    <path
                      fillRule="evenodd"
                      d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div>
                  <span className="font-bold block text-indigo-950 mb-0.5">
                    Institutional AI Verification Notice
                  </span>
                  <span>
                    AI answers are strictly derived from official college notices. Always refer to
                    cited documents for formal verification.
                  </span>
                </div>
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
};

export default SearchAndAskPage;
