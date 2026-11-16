/**
 * CAI Campus Intelligence — Authentication & User Types
 * Implements roles and profile shapes according to:
 * - docs/MODULES.md (M03: Authentication & Authorization)
 * - docs/DATABASE_SCHEMA.md (profiles table)
 * - docs/API_CONTRACTS.md (§4: Authentication and authorization)
 */

export type UserRole = 'uploader' | 'admin';

export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  role: UserRole | string;
  department?: string | null;
  created_at?: string;
}

export interface AuthContextType {
  user: User | null;
  sessionToken: string | null;
  token: string | null; // Convenient alias for sessionToken
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}
