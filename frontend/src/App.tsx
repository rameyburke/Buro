import React, { useEffect } from 'react';
import { Routes, Route, Navigate, Link, NavLink } from 'react-router-dom';
import useAppStore from './stores/appStore';
import './App.css';

// Import pages
import { KanbanBoard } from './components/board/KanbanBoard';
import { AnalyticsPage } from './pages/Analytics';
import { ProjectsPage } from './pages/Projects';
import { IssuesPage } from './pages/Issues';
import { LoginPage } from './pages/Login';
import { ProjectSelector } from './components/navigation/ProjectSelector';
import { BuroLogo } from './components/branding/BuroLogo';

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

  const navLinks = [
    { to: '/board', label: 'Kanban Board' },
    { to: '/projects', label: 'Projects' },
    { to: '/issues', label: 'Issues' },
    { to: '/analytics', label: 'Analytics' }
  ];

  return (
    <div className="app-root">
      {/* Navigation Header */}
      <header className="buro-header">
        <div className="header-inner">
          <div className="brand">
            <Link to="/" className="brand-link" aria-label="Buro home">
              <BuroLogo variant="mark" />
            </Link>
          </div>

          {isAuthenticated && (
            <nav className="view-tabs" aria-label="Main views">
              {navLinks.map(({ to, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) => `view-tab${isActive ? ' active' : ''}`}
                >
                  {label}
                </NavLink>
              ))}
            </nav>
          )}

          <div className="header-actions">
            {isAuthenticated && <ProjectSelector />}
            {isAuthenticated ? (
              <button
                onClick={() => useAppStore.getState().logout()}
                className="ghost-button"
              >
                Logout
              </button>
            ) : (
              <button
                onClick={() => alert('Login/Register coming in next sprint!')}
                className="primary-button"
              >
                Login
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="content-shell">
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
