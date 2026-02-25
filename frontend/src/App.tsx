import React, { useEffect } from 'react';
import { Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import useAppStore from './stores/appStore';
import './App.css';

// Import pages
import { KanbanBoard } from './components/board/KanbanBoard';
import { AnalyticsPage } from './pages/Analytics';
import { ProjectsPage } from './pages/Projects';
import { IssuesPage } from './pages/Issues';
import { LoginPage } from './pages/Login';

// Simple auth wrapper
function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAppStore();
  const location = useLocation();

  if (!isAuthenticated) {
    // Could redirect to login page here
    return <Navigate to="/" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

// Main App Component
function App() {
  const {
    loadAuthFromStorage,
    loadProjects,
    projects,
    isAuthenticated
  } = useAppStore();

  // Initialize app state on mount
  // Why useEffect: Run once when app starts, after component mounts
  useEffect(() => {
    // Load stored authentication state
    loadAuthFromStorage();
  }, [loadAuthFromStorage]);

  // Load projects only when user is authenticated
  // Why separate useEffect: Avoid loading projects until auth is confirmed
  useEffect(() => {
    if (isAuthenticated && !projects.length) {
      loadProjects();
    }
  }, [isAuthenticated, loadProjects, projects.length]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Header */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="text-xl font-bold text-gray-900">
                🚀 Buro
              </Link>

              {isAuthenticated && (
                <div className="ml-10 flex items-baseline space-x-4">
                  <Link
                    to="/board"
                    className="text-gray-900 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Kanban Board
                  </Link>
                  <Link
                    to="/projects"
                    className="text-gray-900 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Projects
                  </Link>
                  <Link
                    to="/issues"
                    className="text-gray-900 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Issues
                  </Link>
                  <Link
                    to="/analytics"
                    className="text-gray-900 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Analytics
                  </Link>
                </div>
              )}
            </div>

            <div className="flex items-center space-x-4">
              {isAuthenticated ? (
                <button
                  onClick={() => useAppStore.getState().logout()}
                  className="bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded-md text-sm font-medium"
                >
                  Logout
                </button>
              ) : (
                <button
                  onClick={() => alert('Login/Register coming in next sprint!')}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                >
                  Login
                </button>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <Routes>
          {/* Landing/Login page */}
          {!isAuthenticated ? (
            <>
              <Route path="/" element={
                <div className="text-center">
                  <h1 className="text-4xl font-bold text-gray-900 mb-4">
                    Welcome to Buro
                  </h1>
                  <p className="text-xl text-gray-600 mb-8">
                    Agile Project Management Platform - Kanban & Analytics
                  </p>

                  <div className="mt-8">
                    <button
                      onClick={() => window.location.href = '/login'}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg text-lg font-medium"
                    >
                      Sign In to Demo
                    </button>
                    <p className="text-sm text-gray-500 mt-2">
                      Use: admin@buro.dev / admin
                    </p>
                  </div>
                </div>
              } />
              <Route path="/login" element={<LoginPage />} />
            </>
          ) : (
            // Authenticated user routes
            <>
              <Route path="/" element={<Navigate to="/board" replace />} />
              <Route path="/board" element={<KanbanBoard />} />
              <Route path="/projects" element={<ProjectsPage />} />
              <Route path="/issues" element={<IssuesPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
            </>
          )}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;