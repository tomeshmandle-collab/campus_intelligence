import React, { useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { UserRole } from '../../types/auth';

export interface ProtectedRouteProps {
  children: React.ReactNode;
  fallbackUrl?: string;
  onRedirect?: () => void;
  allowedRoles?: UserRole[];
}

/**
 * Route protection wrapper for staff/uploader administration pages (M03 / P4).
 * Prevents UI flashing during session restoration, checks role permissions,
 * and redirects unauthenticated users to the login portal.
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  fallbackUrl = '/admin/login',
  onRedirect,
  allowedRoles,
}) => {
  const { user, isAuthenticated, isLoading } = useAuth();

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
  if (!isAuthenticated || !user) {
    return null;
  }

  // Role authorization check (if allowedRoles is specified)
  if (allowedRoles && !allowedRoles.includes(user.role as UserRole)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
        <div className="max-w-md w-full bg-white rounded-xl shadow-md border border-slate-200 p-6 text-center space-y-3">
          <div className="w-12 h-12 bg-rose-100 text-rose-600 rounded-full flex items-center justify-center mx-auto text-xl font-bold">
            !
          </div>
          <h2 className="text-lg font-bold text-slate-800">Access Restricted</h2>
          <p className="text-sm text-slate-600">
            Your institutional role (<strong className="font-semibold text-indigo-600">{user.role}</strong>) does not have permission to view this section.
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

export default ProtectedRoute;
