import { useState, type ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { routes } from '../config/routeConfig';

export function Layout({ children }: { children: ReactNode }) {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const currentRoute = routes.find(r => r.path === location.pathname);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-amber-700 text-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center space-x-2">
              <span className="text-xl font-bold tracking-tight">Gold Sentiment Index</span>
            </Link>

            {/* Desktop nav */}
            <nav className="hidden md:flex space-x-1">
              {routes.map(route => (
                <Link
                  key={route.path}
                  to={route.path}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    location.pathname === route.path
                      ? 'bg-amber-800 text-white'
                      : 'text-amber-100 hover:bg-amber-600 hover:text-white'
                  }`}
                >
                  {route.label}
                </Link>
              ))}
            </nav>

            {/* Mobile menu button */}
            <button
              className="md:hidden p-2 rounded-md text-amber-100 hover:bg-amber-600"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-amber-600">
            <div className="px-2 pt-2 pb-3 space-y-1">
              {routes.map(route => (
                <Link
                  key={route.path}
                  to={route.path}
                  className={`block px-3 py-2 rounded-md text-base font-medium ${
                    location.pathname === route.path
                      ? 'bg-amber-800 text-white'
                      : 'text-amber-100 hover:bg-amber-600'
                  }`}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {route.label}
                </Link>
              ))}
            </div>
          </div>
        )}
      </header>

      {/* Page title bar */}
      {currentRoute && (
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <h1 className="text-lg font-semibold text-gray-800">{currentRoute.label}</h1>
          </div>
        </div>
      )}

      {/* Content */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-gray-400 text-center py-4 text-sm">
        Gold Sentiment Index &mdash; Daily composite scoring across 7 drivers
      </footer>
    </div>
  );
}
