/**
 * Notice types for CAI Campus Intelligence
 * Strictly adhering to docs/API_CONTRACTS.md (Section 5.1, 5.2, 5.4, 7.4, 7.5)
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

export type RelationshipStatus = 'current' | 'superseded' | 'amended' | 'extended' | 'cancelled';

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

export interface ImportantDate {
  kind: 'deadline' | 'event' | 'publication' | string;
  label: string;
  starts_on: string;
  ends_on?: string | null;
  starts_time?: string | null;
  source_page?: number | null;
}

export interface AudienceTarget {
  role: AudienceType;
  department?: string | null;
  year?: string | null;
  detail?: string | null;
}

export interface SourceFile {
  available: boolean;
  download_url: string | null;
  filename?: string | null;
  page_count?: number;
}

export interface RelatedNotice {
  notice_id: string;
  relationship_type: 'amends' | 'replaces' | 'extends' | 'cancels' | string;
  title?: string;
  publication_date?: string;
}

export interface NoticeDetail {
  id: string;
  title: string;
  reference_number: string | null;
  category: NoticeCategory;
  summary: string;
  issuing_authority: string | null;
  issue_date: string | null;
  audiences: AudienceType[];
  audience_targets: AudienceTarget[];
  important_dates: ImportantDate[];
  action_items: string[];
  relationship_status: RelationshipStatus;
  related_notices: RelatedNotice[];
  field_labels?: Record<string, 'ai_extracted' | 'human_corrected'>;
  source_file: SourceFile;
  published_at: string;
  updated_at?: string;
}

export interface NoticeDetailResponse {
  notice: NoticeDetail;
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

/**
 * Error report types per docs/API_CONTRACTS.md §7.8 and Issue P3-4
 */
export type ErrorReportReason =
  | 'Incorrect Date'
  | 'Wrong Audience'
  | 'Typo in Summary'
  | 'Document Unreadable'
  | 'Other';

export type ErrorReportIssueType =
  | 'incorrect_information'
  | 'broken_link_or_file'
  | 'missing_dates_or_details'
  | 'duplicate_notice'
  | 'other';

export const ERROR_REPORT_REASONS: readonly ErrorReportReason[] = [
  'Incorrect Date',
  'Wrong Audience',
  'Typo in Summary',
  'Document Unreadable',
  'Other',
] as const;

export const REASON_TO_ISSUE_TYPE: Record<ErrorReportReason, ErrorReportIssueType> = {
  'Incorrect Date': 'incorrect_information',
  'Wrong Audience': 'incorrect_information',
  'Typo in Summary': 'incorrect_information',
  'Document Unreadable': 'broken_link_or_file',
  'Other': 'other',
};

export interface ErrorReportRequest {
  issue_type: ErrorReportIssueType | string;
  description: string;
}

export interface ErrorReportResponse {
  report_id: string;
  status: 'received' | string;
}

