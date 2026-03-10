import React, { useEffect, useState } from 'react';
import { Routes, Route, Navigate, Link, NavLink } from 'react-router-dom';
import useAppStore from './stores/appStore';
import * as api from './lib/api';
import './App.css';

// Import pages
import { KanbanBoard } from './components/board/KanbanBoard';
import { AnalyticsPage } from './pages/Analytics';
import { ProjectsPage } from './pages/Projects';
import { IssuesPage } from './pages/Issues';
import { UsersPage } from './pages/Users';
import { LoginPage } from './pages/Login';
import { ProjectSelector } from './components/navigation/ProjectSelector';
import { BuroLogo } from './components/branding/BuroLogo';

// Main App Component
function App() {
  const [themeSaving, setThemeSaving] = useState(false);
  const {
    loadAuthFromStorage,
    loadCurrentUser,
    loadProjects,
    projects,
    isAuthenticated,
    user,
  } = useAppStore();

  const currentTheme = user?.theme === 'dark' ? 'dark' : 'light';

  // Initialize app state on mount
  // Why useEffect: Run once when app starts, after component mounts
  useEffect(() => {
    // Load stored authentication state
    loadAuthFromStorage();
  }, [loadAuthFromStorage]);

  // Load projects only when user is authenticated
  // Why separate useEffect: Avoid loading projects until auth is confirmed
  useEffect(() => {
    if (isAuthenticated && !user) {
      void loadCurrentUser();
    }
  }, [isAuthenticated, user, loadCurrentUser]);

  useEffect(() => {
    if (isAuthenticated && !projects.length) {
      loadProjects();
    }
  }, [isAuthenticated, loadProjects, projects.length]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (currentTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [currentTheme]);

  const toggleTheme = async () => {
    if (!user || themeSaving) return;

    const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setThemeSaving(true);

    try {
      await api.updateUser(user.id, { theme: nextTheme });
      await loadCurrentUser();
    } catch (error) {
      console.error('Failed to update theme preference:', error);
    } finally {
      setThemeSaving(false);
    }
  };

  const navLinks = [
    { to: '/board', label: 'Kanban Board' },
    { to: '/projects', label: 'Projects' },
    { to: '/issues', label: 'Issues' },
    { to: '/analytics', label: 'Analytics' },
    ...(user?.role === 'admin' ? [{ to: '/users', label: 'Users' }] : []),
  ];

  // When restoring a persisted session, wait for /auth/me before applying
  // role-based route guards. This avoids redirecting valid admin deep-links
  // (like /users) to /board during initial hydration.
  if (isAuthenticated && !user) {
    return (
      <div className="app-root">
        <main className="content-shell">
          <div className="flex items-center justify-center h-64 text-gray-500">
            Loading your workspace...
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className={`app-root ${currentTheme === 'dark' ? 'dark' : ''}`}>
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
              <>
                <button
                  type="button"
                  onClick={toggleTheme}
                  disabled={themeSaving}
                  className="theme-toggle-button rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-600 dark:text-slate-100 dark:hover:bg-slate-700"
                  data-testid="theme-toggle"
                  aria-label={`Switch to ${currentTheme === 'dark' ? 'light' : 'dark'} theme`}
                >
                  {currentTheme === 'dark' ? 'Light' : 'Dark'}
                </button>
                <button
                  onClick={() => useAppStore.getState().logout()}
                  className="ghost-button"
                >
                  Logout
                </button>
              </>
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
              <Route path="/users" element={user?.role === 'admin' ? <UsersPage /> : <Navigate to="/board" replace />} />
            </>
          )}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
