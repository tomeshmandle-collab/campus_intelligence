import React, { useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';

export interface ProtectedRouteProps {
  children: React.ReactNode;
  fallbackUrl?: string;
  onRedirect?: () => void;
}

/**
 * Route protection wrapper for staff/uploader administration pages (M03 / P4).
 * Prevents UI flashing during session restoration and redirects unauthenticated
 * users to the login portal.
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  fallbackUrl = '/admin/login',
  onRedirect,
}) => {
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      if (onRedirect) {
        onRedirect();
      } else {
        window.location.href = fallbackUrl;
      }
    }
  }, [isLoading, isAuthenticated, fallbackUrl, onRedirect]);

  // Prevent UI flash during session check
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Verifying Staff Session...
          </span>
        </div>
      </div>
    );
  }

  // Block rendering protected UI if unauthenticated
  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
