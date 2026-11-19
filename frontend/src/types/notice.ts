/**
 * Notice types for CAI Campus Intelligence
 * Strictly adhering to docs/API_CONTRACTS.md (Section 5.1, 5.2, 7.4)
 */

export type AudienceType = 'student' | 'faculty' | 'staff' | 'all' | 'unspecified';

export type NoticeCategory =
  | 'Admissions'
  | 'Exams'
  | 'General'
  | 'Scholarships'
  | 'Academic'
  | 'Events'
  | string;

export interface Notice {
  id: string;
  title: string;
  category: NoticeCategory;
  publication_date: string;
  deadline_date: string | null;
  audience: AudienceType;
  summary_snippet: string;
  is_urgent: boolean;
  source_page_count: number;
}

export interface NoticeListPagination {
  limit: number;
  offset: number;
  total: number;
  has_more: boolean;
}

export interface NoticeListResponse {
  items: Notice[];
  pagination: NoticeListPagination;
}

export interface NoticeFilterParams {
  audience?: AudienceType;
  category?: string;
  from_date?: string;
  to_date?: string;
  q?: string;
  sort?: string;
  limit?: number;
  offset?: number;
}
