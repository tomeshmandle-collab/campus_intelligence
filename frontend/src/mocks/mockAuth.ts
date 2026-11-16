/**
 * CAI Campus Intelligence — Mock Authentication Fixtures
 * Reference: docs/API_CONTRACTS.md §11 (Mock data and parallel development)
 * 
 * Provides mock institutional staff credentials for parallel frontend development
 * while backend M03 Supabase Auth integration is in progress.
 */

import { User } from '../types/auth';

export interface MockAccount {
  email: string;
  password: string;
  user: User;
  token: string;
}

/**
 * Standard test accounts for Kirori Mal College staff and administration.
 */
export const MOCK_STAFF_ACCOUNTS: MockAccount[] = [
  {
    email: 'uploader@kmc.du.ac.in',
    password: 'password123',
    user: {
      id: 'd3b07384-d113-49a0-9759-4b475143e101',
      email: 'uploader@kmc.du.ac.in',
      full_name: 'Dr. Ramesh Sharma (Staff Uploader)',
      role: 'uploader',
      department: 'Administration',
      created_at: '2026-01-15T09:00:00Z',
    },
    token: 'mock-session-token-uploader-kmc-101',
  },
  {
    email: 'admin@kmc.du.ac.in',
    password: 'password123',
    user: {
      id: 'e4c18495-e224-4ab1-a860-5c586254f202',
      email: 'admin@kmc.du.ac.in',
      full_name: 'Prof. Anita Verma (Principal / Admin)',
      role: 'admin',
      department: 'Principal Office',
      created_at: '2026-01-10T08:30:00Z',
    },
    token: 'mock-session-token-admin-kmc-202',
  },
  {
    email: 'staff@kmc.du.ac.in',
    password: 'password123',
    user: {
      id: 'f5d29506-f335-4bc2-b971-6d697365a303',
      email: 'staff@kmc.du.ac.in',
      full_name: 'KMC Academic Staff',
      role: 'uploader',
      department: 'Academic Branch',
      created_at: '2026-02-01T10:15:00Z',
    },
    token: 'mock-session-token-staff-kmc-303',
  },
];

/**
 * Validates provided credentials against mock staff accounts.
 */
export function authenticateMock(
  email: string,
  password: string
): { user: User; token: string } | null {
  const normalizedEmail = email.trim().toLowerCase();
  const matched = MOCK_STAFF_ACCOUNTS.find(
    (account) =>
      account.email.toLowerCase() === normalizedEmail &&
      account.password === password
  );

  if (matched) {
    return {
      user: matched.user,
      token: matched.token,
    };
  }

  return null;
}
