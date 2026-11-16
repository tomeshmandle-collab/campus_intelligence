import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from 'react';
import { apiClient } from '../services/api';
import { User, UserRole, AuthContextType } from '../types/auth';
import { authenticateMock } from '../mocks/mockAuth';

export type { User, UserRole, AuthContextType };

const STORAGE_KEYS = {
  TOKEN: 'cai_session_token',
  USER: 'cai_auth_user',
} as const;

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

/**
 * CAI Campus Intelligence — Authentication Context Provider (M03 / P4)
 *
 * Manages staff authentication state, token persistence, and HTTP client authorization header.
 * Provides mock authentication for parallel frontend development with fallback to
 * backend endpoint POST /api/v1/auth/login.
 */
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Synchronize Axios default Authorization header with token
  const updateAuthHeader = useCallback((token: string | null) => {
    if (token) {
      apiClient.defaults.headers.common = apiClient.defaults.headers.common || {};
      (apiClient.defaults.headers.common as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    } else if (apiClient.defaults.headers.common) {
      delete (apiClient.defaults.headers.common as Record<string, string>)['Authorization'];
    }
  }, []);

  // Restore stored session on mount
  useEffect(() => {
    try {
      const storedToken = localStorage.getItem(STORAGE_KEYS.TOKEN);
      const storedUser = localStorage.getItem(STORAGE_KEYS.USER);

      if (storedToken && storedUser) {
        const parsedUser = JSON.parse(storedUser) as User;
        setSessionToken(storedToken);
        setUser(parsedUser);
        updateAuthHeader(storedToken);
      }
    } catch (err) {
      console.error('[AuthContext] Failed to parse stored session:', err);
      localStorage.removeItem(STORAGE_KEYS.TOKEN);
      localStorage.removeItem(STORAGE_KEYS.USER);
    } finally {
      setIsLoading(false);
    }
  }, [updateAuthHeader]);

  /**
   * Log in user with email and password.
   * Priority:
   * 1. Evaluates contract-aligned mock staff accounts.
   * 2. If not matched in mock fixtures, falls back to backend API: POST /api/v1/auth/login.
   * 3. If backend is unavailable or credentials are invalid, throws descriptive Error.
   */
  const login = useCallback(
    async (email: string, password: string): Promise<void> => {
      const trimmedEmail = email.trim();
      if (!trimmedEmail || !password) {
        throw new Error('Email and password are required.');
      }

      // Step 1: Mock implementation check
      const mockResult = authenticateMock(trimmedEmail, password);
      if (mockResult) {
        setSessionToken(mockResult.token);
        setUser(mockResult.user);
        updateAuthHeader(mockResult.token);
        localStorage.setItem(STORAGE_KEYS.TOKEN, mockResult.token);
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(mockResult.user));
        return;
      }

      // Step 2: Fallback to backend API POST /api/v1/auth/login
      try {
        const response = await apiClient.post('/auth/login', {
          email: trimmedEmail,
          password,
        });

        const data = response.data;
        const token =
          data.access_token || data.sessionToken || data.token || null;

        const resolvedUser: User = data.user || {
          id: data.id || 'backend-user',
          email: data.email || trimmedEmail,
          full_name: data.full_name || null,
          role: (data.role as UserRole) || 'uploader',
        };

        if (!token) {
          throw new Error('Server response did not include an authentication token.');
        }

        setSessionToken(token);
        setUser(resolvedUser);
        updateAuthHeader(token);
        localStorage.setItem(STORAGE_KEYS.TOKEN, token);
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(resolvedUser));
      } catch (err: unknown) {
        // Handle backend error responses and offline states
        const errorObj = err as {
          response?: {
            status?: number;
            data?: {
              error?: { message?: string };
              detail?: string | Array<{ msg?: string }>;
            };
          };
          message?: string;
          code?: string;
        };

        const backendMessage =
          errorObj.response?.data?.error?.message ||
          (typeof errorObj.response?.data?.detail === 'string'
            ? errorObj.response.data.detail
            : Array.isArray(errorObj.response?.data?.detail)
            ? errorObj.response?.data?.detail[0]?.msg
            : undefined) ||
          errorObj.message;

        if (
          errorObj.code === 'ERR_NETWORK' ||
          errorObj.response?.status === 404 ||
          errorObj.message?.includes('Network Error')
        ) {
          throw new Error(
            'Invalid credentials. (For local development, use uploader@kmc.du.ac.in or admin@kmc.du.ac.in with password: password123)'
          );
        }

        if (backendMessage) {
          throw new Error(backendMessage);
        }

        throw new Error('Authentication failed. Please check your credentials.');
      }
    },
    [updateAuthHeader]
  );

  /**
   * Clears active session, storage, and Authorization header.
   */
  const logout = useCallback(() => {
    setUser(null);
    setSessionToken(null);
    updateAuthHeader(null);
    localStorage.removeItem(STORAGE_KEYS.TOKEN);
    localStorage.removeItem(STORAGE_KEYS.USER);
  }, [updateAuthHeader]);

  const value: AuthContextType = {
    user,
    sessionToken,
    token: sessionToken,
    isAuthenticated: Boolean(user && sessionToken),
    isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * Hook to consume CAI Campus Intelligence Authentication Context.
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
