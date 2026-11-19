import { Notice } from '../types/notice';

/**
 * 6 Realistic mock notices for Kirori Mal College (CAI Campus Intelligence)
 * Covering Admissions, Exams, General, Scholarships, and urgent deadlines.
 */
export const mockNotices: Notice[] = [
  {
    id: 'notif-adm-2026-001',
    title: 'Postgraduate Admissions 2026-27: Round 2 Seat Allocation & Physical Document Verification',
    category: 'Admissions',
    publication_date: '2026-11-10',
    deadline_date: '2026-11-20',
    audience: 'student',
    summary_snippet:
      'Shortlisted candidates for PG courses must report to Room 102 with original mark sheets and fee receipts before the closing hour. Failure to verify will forfeit the provisional seat.',
    is_urgent: true,
    source_page_count: 2,
  },
  {
    id: 'notif-exam-2026-002',
    title: 'Urgent: Submission of Examination Fees & Portal Clearance for Semesters III and V',
    category: 'Exams',
    publication_date: '2026-11-05',
    deadline_date: '2026-11-18',
    audience: 'student',
    summary_snippet:
      'All regular students appearing for odd semester examinations must clear outstanding fee dues via the college online payment gateway to generate their hall tickets.',
    is_urgent: true,
    source_page_count: 2,
  },
  {
    id: 'notif-gen-2026-003',
    title: 'Annual Inter-College Sports & Athletics Meet 2026: Team Trials and Registration',
    category: 'General',
    publication_date: '2026-11-08',
    deadline_date: null,
    audience: 'all',
    summary_snippet:
      'The Department of Physical Education invites interested students to participate in selection trials for athletics, football, and badminton at the college sports ground.',
    is_urgent: false,
    source_page_count: 1,
  },
  {
    id: 'notif-sch-2026-004',
    title: 'Merit-Cum-Means Scholarship 2026: Application Guidelines & Family Income Certificate Verification',
    category: 'Scholarships',
    publication_date: '2026-11-01',
    deadline_date: '2026-11-25',
    audience: 'student',
    summary_snippet:
      'Eligible undergraduate students with annual family income below INR 2.5 Lakhs can submit the prescribed application form along with self-attested supporting documents at Counter 4.',
    is_urgent: false,
    source_page_count: 3,
  },
  {
    id: 'notif-fac-2026-005',
    title: 'One-Week Faculty Development Programme (FDP) on Artificial Intelligence and Digital Pedagogy',
    category: 'General',
    publication_date: '2026-11-12',
    deadline_date: '2026-11-30',
    audience: 'faculty',
    summary_snippet:
      'Organised by the Centre for Artificial Intelligence, this workshop equips faculty members with generative AI research workflows and modern syllabus design methods.',
    is_urgent: false,
    source_page_count: 1,
  },
  {
    id: 'notif-stf-2026-006',
    title: 'Campus Electrical Substation Maintenance and Scheduled Power Interruption Circular',
    category: 'General',
    publication_date: '2026-11-14',
    deadline_date: null,
    audience: 'staff',
    summary_snippet:
      'Essential electrical servicing will take place on Saturday between 10:00 AM and 2:00 PM affecting the administrative block and laboratory wings. Backup generators will support core servers.',
    is_urgent: false,
    source_page_count: 1,
  },
];
