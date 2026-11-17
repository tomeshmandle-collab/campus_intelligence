import React from 'react';
import { Navbar } from './Navbar';
import { Footer } from './Footer';

export interface PublicLayoutProps {
  children?: React.ReactNode;
  currentPath?: string;
  onNavigate?: (path: string) => void;
}

export const PublicLayout: React.FC<PublicLayoutProps> = ({
  children,
  currentPath,
  onNavigate,
}) => {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans antialiased selection:bg-indigo-100 selection:text-indigo-900">
      {/* Institutional Top Navbar */}
      <Navbar currentPath={currentPath} onNavigate={onNavigate} />

      {/* Main Page Content */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
        {children}
      </main>

      {/* Institutional Disclaimer & Footer */}
      <Footer />
    </div>
  );
};

export default PublicLayout;
