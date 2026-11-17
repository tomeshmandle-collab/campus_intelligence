import { Notice, NoticeDetail } from '../types/notice';

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

/**
 * Detailed Notice records matching docs/API_CONTRACTS.md §5.4
 * Used for offline mock mode in NoticeDetailPage.
 */
export const mockNoticeDetails: Record<string, NoticeDetail> = {
  'notif-adm-2026-001': {
    id: 'notif-adm-2026-001',
    title: 'Postgraduate Admissions 2026-27: Round 2 Seat Allocation & Physical Document Verification',
    reference_number: 'KMC/ADM/2026/PG-02',
    category: 'Admissions',
    summary:
      'The Central Admission Committee announces the publication of the Round 2 provisional seat allotment list for all Postgraduate (MA, M.Sc, M.Com) courses for the academic session 2026-27. All candidates offered admission in this round are required to attend physical document verification in Room 102 (Administrative Wing) between 10:00 AM and 4:00 PM on working days. Please present original certificates, migration certificates, CUET-PG scorecard, and paid fee receipts. Failure to appear for physical verification or submit complete documents within the stipulated timeline will lead to automatic cancellation of provisional admission without further notice.',
    issuing_authority: 'Office of the Dean, Admissions — Kirori Mal College',
    issue_date: '2026-11-10',
    audiences: ['student'],
    audience_targets: [
      {
        role: 'student',
        department: 'Postgraduate Studies',
        year: '1st Year (2026-27)',
        detail: 'Candidates provisionally shortlisted in PG Round 2 allotment',
      },
    ],
    important_dates: [
      {
        kind: 'event',
        label: 'Verification Desk Opens',
        starts_on: '2026-11-12',
        starts_time: '10:00 AM',
        source_page: 1,
      },
      {
        kind: 'deadline',
        label: 'Final Document Verification & Fee Confirmation Deadline',
        starts_on: '2026-11-20',
        starts_time: '4:00 PM',
        source_page: 2,
      },
    ],
    action_items: [
      'Download and print provisional admission slip from admission portal.',
      'Produce original Class 10th, 12th, and Undergraduate degree mark sheets along with two self-attested photocopies.',
      'Report in person to Room 102, Administrative Block before November 20, 2026, 4:00 PM.',
      'Collect official stamped acknowledgement from the admission convenor desk.',
    ],
    relationship_status: 'current',
    related_notices: [],
    field_labels: {
      title: 'human_corrected',
      summary: 'ai_extracted',
      important_dates: 'human_corrected',
    },
    source_file: {
      available: true,
      download_url: 'https://example.kmc.du.ac.in/downloads/notices/2026/PG_Round2_Verification.pdf',
      filename: 'PG_Round2_Verification_Schedule.pdf',
      page_count: 2,
    },
    published_at: '2026-11-10T09:30:00Z',
    updated_at: '2026-11-10T11:15:00Z',
  },

  'notif-exam-2026-002': {
    id: 'notif-exam-2026-002',
    title: 'Urgent: Submission of Examination Fees & Portal Clearance for Semesters III and V',
    reference_number: 'KMC/EXAM/2026/ODD-FEE-14',
    category: 'Exams',
    summary:
      'Notice is hereby issued to all regular, ex-students, and essential repeaters of Semester III and Semester V regarding mandatory clearance of examination fees for November-December 2026 university examinations. Students must complete payment exclusively through the college ERP student portal. Offline or cash payments will not be entertained. Admit cards and roll numbers will be withheld for students whose fees remain unconfirmed on the DU examination portal past the cut-off date. This schedule has been amended to provide an extended grace window per university circular.',
    issuing_authority: 'Convenor, College Examination Branch',
    issue_date: '2026-11-05',
    audiences: ['student'],
    audience_targets: [
      {
        role: 'student',
        department: 'All Undergraduate Departments',
        year: 'Semesters III and V',
        detail: 'Regular and ex-students eligible for Odd Semester Exams',
      },
    ],
    important_dates: [
      {
        kind: 'deadline',
        label: 'Online Fee Submission Portal Closes',
        starts_on: '2026-11-18',
        starts_time: '11:59 PM',
        source_page: 1,
      },
      {
        kind: 'event',
        label: 'Issuance of Digital Hall Tickets',
        starts_on: '2026-11-22',
        source_page: 2,
      },
    ],
    action_items: [
      'Log into the college ERP student dashboard with registered institutional credentials.',
      'Review pre-filled course examination codes against opted semester papers.',
      'Complete online transaction and save transaction receipt PDF for hall ticket verification.',
    ],
    relationship_status: 'amended',
    related_notices: [
      {
        notice_id: 'notif-adm-2026-001',
        relationship_type: 'amends',
        title: 'Postgraduate Admissions 2026-27: Round 2 Seat Allocation',
        publication_date: '2026-11-10',
      },
    ],
    field_labels: {
      title: 'human_corrected',
      summary: 'ai_extracted',
    },
    source_file: {
      available: true,
      download_url: 'https://example.kmc.du.ac.in/downloads/notices/2026/Exam_Fee_Sem3_5.pdf',
      filename: 'Exam_Fee_Circular_Sem3_5.pdf',
      page_count: 2,
    },
    published_at: '2026-11-05T08:00:00Z',
    updated_at: '2026-11-07T14:20:00Z',
  },

  'notif-gen-2026-003': {
    id: 'notif-gen-2026-003',
    title: 'Annual Inter-College Sports & Athletics Meet 2026: Team Trials and Registration',
    reference_number: 'KMC/SPT/2026/TRIALS-01',
    category: 'General',
    summary:
      'The Department of Physical Education and Sports invites student athletes across all faculties to take part in selection trials for the upcoming University of Delhi Inter-College Tournaments. Selection trials will be conducted for Football (Men), Athletics (Men & Women), Badminton, Basketball, and Table Tennis at the college grounds and sports complex. Candidates must appear in proper sports kit with valid college identity cards. Medical fitness certificates signed by a registered practitioner are mandatory for track and contact sports.',
    issuing_authority: 'Director of Physical Education, Kirori Mal College',
    issue_date: '2026-11-08',
    audiences: ['all'],
    audience_targets: [
      {
        role: 'all',
        department: 'All Courses',
        year: null,
        detail: 'Undergraduate and Postgraduate bonafide students',
      },
    ],
    important_dates: [
      {
        kind: 'event',
        label: 'Athletics & Track Trials',
        starts_on: '2026-11-19',
        starts_time: '08:30 AM',
        source_page: 1,
      },
      {
        kind: 'event',
        label: 'Team Sports Trials (Football & Basketball)',
        starts_on: '2026-11-21',
        starts_time: '09:00 AM',
        source_page: 1,
      },
    ],
    action_items: [
      'Register name and sporting discipline at the Physical Education Office (Gymnasium wing).',
      'Submit self-attested copy of college ID card and medical fitness certificate.',
      'Assemble at Main Ground 15 minutes prior to scheduled trial timings.',
    ],
    relationship_status: 'current',
    related_notices: [],
    field_labels: {
      title: 'ai_extracted',
      summary: 'ai_extracted',
    },
    source_file: {
      available: true,
      download_url: 'https://example.kmc.du.ac.in/downloads/notices/2026/Sports_Trials_Notice.pdf',
      filename: 'Sports_Trials_Notice_2026.pdf',
      page_count: 1,
    },
    published_at: '2026-11-08T11:00:00Z',
  },

  'notif-sch-2026-004': {
    id: 'notif-sch-2026-004',
    title: 'Merit-Cum-Means Scholarship 2026: Application Guidelines & Family Income Certificate Verification',
    reference_number: 'KMC/SCH/2026/MCM-04',
    category: 'Scholarships',
    summary:
      'Applications in the prescribed proforma are invited from meritorious and economically deserving undergraduate students for the Kirori Mal College Merit-Cum-Means Scholarship for the current academic year. Eligible applicants must have secured at least 65% aggregate marks (or equivalent CGPA) in the previous academic examination and family gross income must not exceed INR 2,50,000 per annum. Shortlisted applicants will be invited for an interaction with the Staff Council Scholarship Advisory Committee. Incomplete applications or certificates issued by non-competent revenue authorities will be rejected summarily.',
    issuing_authority: 'Scholarship Advisory Committee, Staff Council',
    issue_date: '2026-11-01',
    audiences: ['student'],
    audience_targets: [
      {
        role: 'student',
        department: 'Arts, Science, Commerce',
        year: 'All UG Years',
        detail: 'Students with annual family income under 2.5 Lakhs and >65% marks',
      },
    ],
    important_dates: [
      {
        kind: 'event',
        label: 'Application Forms Available at Counter 4',
        starts_on: '2026-11-03',
        source_page: 1,
      },
      {
        kind: 'deadline',
        label: 'Last Date for Submission of Hard Copies',
        starts_on: '2026-11-25',
        starts_time: '03:00 PM',
        source_page: 2,
      },
    ],
    action_items: [
      'Collect Form MCM-A from Accounts Section Counter 4 or download official annexure.',
      'Obtain Revenue Authority (Tehsildar / Sub-Divisional Magistrate) Income Certificate valid for FY 2025-26.',
      'Attach bank passbook front page photocopy displaying active account number and IFSC code.',
      'Submit completed dossier with tutor recommendation to Counter 4 before November 25, 2026.',
    ],
    relationship_status: 'current',
    related_notices: [],
    field_labels: {
      title: 'human_corrected',
      summary: 'human_corrected',
    },
    source_file: {
      available: true,
      download_url: 'https://example.kmc.du.ac.in/downloads/notices/2026/MCM_Scholarship_Notice.pdf',
      filename: 'MCM_Scholarship_Guidelines_2026.pdf',
      page_count: 3,
    },
    published_at: '2026-11-01T10:00:00Z',
  },

  'notif-fac-2026-005': {
    id: 'notif-fac-2026-005',
    title: 'One-Week Faculty Development Programme (FDP) on Artificial Intelligence and Digital Pedagogy',
    reference_number: 'CAI/KMC/2026/FDP-AI-01',
    category: 'General',
    summary:
      'The Centre for Artificial Intelligence (CAI) at Kirori Mal College, in collaboration with UGC-HRDC, cordially invites faculty members across all teaching departments to enroll in a one-week national Faculty Development Programme titled "Artificial Intelligence and Digital Pedagogy in Higher Education". Topics include hands-on training on large language models, citation provenance checking, responsible AI governance in curriculum design, and automated laboratory evaluation. Participation certificates will be awarded upon meeting minimum 90% attendance and successful capstone project presentation.',
    issuing_authority: 'Centre for Artificial Intelligence, Kirori Mal College',
    issue_date: '2026-11-12',
    audiences: ['faculty'],
    audience_targets: [
      {
        role: 'faculty',
        department: 'All Academic Faculties',
        year: null,
        detail: 'Permanent, Ad-hoc, and Guest Faculty members',
      },
    ],
    important_dates: [
      {
        kind: 'deadline',
        label: 'Faculty Online Nomination Deadline',
        starts_on: '2026-11-30',
        starts_time: '05:00 PM',
        source_page: 1,
      },
      {
        kind: 'event',
        label: 'Inaugural Session & Keynote Address',
        starts_on: '2026-12-05',
        starts_time: '10:00 AM',
        source_page: 1,
      },
    ],
    action_items: [
      'Fill Google registration form circulated via official departmental faculty email.',
      'Obtain Head of Department approval / endorsement signature.',
      'Submit nomination slip to CAI secretariat, Room 204.',
    ],
    relationship_status: 'current',
    related_notices: [],
    field_labels: {
      title: 'human_corrected',
      summary: 'ai_extracted',
    },
    source_file: {
      available: true,
      download_url: 'https://example.kmc.du.ac.in/downloads/notices/2026/CAI_FDP_Flyer.pdf',
      filename: 'CAI_Faculty_Development_Programme_2026.pdf',
      page_count: 1,
    },
    published_at: '2026-11-12T14:30:00Z',
  },

  'notif-stf-2026-006': {
    id: 'notif-stf-2026-006',
    title: 'Campus Electrical Substation Maintenance and Scheduled Power Interruption Circular',
    reference_number: 'KMC/EST/2026/ELEC-88',
    category: 'General',
    summary:
      'Notice is hereby given that the Engineering & Estate Maintenance Division will undertake essential preventive maintenance and transformer servicing at Substation No. 2. A scheduled shutdown will occur on Saturday from 10:00 AM to 02:00 PM. Power supply to Administrative Block, Science Block Labs, and Main Library will remain temporarily suspended during this window. Emergency backup diesel generators will power essential IT servers, network rack rooms, and refrigeration facilities. All staff members are requested to properly shut down desktop computers and sensitive equipment by Friday evening.',
    issuing_authority: 'Estate Officer & Caretaker, Kirori Mal College',
    issue_date: '2026-11-14',
    audiences: ['staff'],
    audience_targets: [
      {
        role: 'staff',
        department: 'Administration, Library, Laboratory Staff',
        year: null,
        detail: 'Administrative and Technical staff operating on campus',
      },
    ],
    important_dates: [
      {
        kind: 'event',
        label: 'Scheduled Power Outage Maintenance Window',
        starts_on: '2026-11-21',
        starts_time: '10:00 AM to 02:00 PM',
        source_page: 1,
      },
    ],
    action_items: [
      'Back up work and shut down all lab workstations prior to Friday closing.',
      'Notify estate maintenance supervisor in case of high-priority uninterrupted experiment requirements.',
    ],
    relationship_status: 'current',
    related_notices: [],
    field_labels: {
      title: 'ai_extracted',
      summary: 'ai_extracted',
    },
    source_file: {
      available: true,
      download_url: 'https://example.kmc.du.ac.in/downloads/notices/2026/Estate_Maintenance_Circular.pdf',
      filename: 'Substation_Power_Maintenance_Schedule.pdf',
      page_count: 1,
    },
    published_at: '2026-11-14T16:00:00Z',
  },
};

/**
 * Helper to retrieve mock detail by notice ID or synthesize from mock list item
 */
export function getMockNoticeDetail(id: string): NoticeDetail | undefined {
  if (mockNoticeDetails[id]) {
    return mockNoticeDetails[id];
  }
  // If not explicitly defined, synthesize from base list item if available
  const base = mockNotices.find((n) => n.id === id);
  if (!base) return undefined;

  return {
    id: base.id,
    title: base.title,
    reference_number: `KMC/NOT/${base.id.toUpperCase()}`,
    category: base.category,
    summary: `${base.summary_snippet} (Full official text extracted from university records).`,
    issuing_authority: 'Kirori Mal College Administration',
    issue_date: base.publication_date,
    audiences: [base.audience],
    audience_targets: [
      {
        role: base.audience,
        department: null,
        year: null,
        detail: `Targeted to ${base.audience}`,
      },
    ],
    important_dates: base.deadline_date
      ? [
          {
            kind: 'deadline',
            label: 'Submission Deadline',
            starts_on: base.deadline_date,
            source_page: 1,
          },
        ]
      : [],
    action_items: ['Refer to the official signed notice document for full compliance instructions.'],
    relationship_status: 'current',
    related_notices: [],
    field_labels: {
      title: 'ai_extracted',
      summary: 'ai_extracted',
    },
    source_file: {
      available: true,
      download_url: `https://example.kmc.du.ac.in/downloads/${base.id}.pdf`,
      filename: `${base.id}.pdf`,
      page_count: base.source_page_count,
    },
    published_at: `${base.publication_date}T10:00:00Z`,
  };
}
