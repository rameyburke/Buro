import React from 'react';
import { Routes, Route } from 'react-router-dom';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>🚀 Buro - Agile Project Management</h1>
        <nav>
          <button onClick={() => alert('Kanban Board coming soon!')}>
            🏗️ Kanban Board (In Development)
          </button>
        </nav>
      </header>
      <main>
        <div className="hero-section">
          <h2>Welcome to Buro!</h2>
          <p>A comprehensive Jira-like agile project management platform</p>
          <div className="status-cards">
            <div className="status-card">
              <strong>🔧 Backend:</strong> Running at http://localhost:8000
            </div>
            <div className="status-card">
              <strong>🎨 Frontend:</strong> Starting up...
            </div>
            <div className="status-card">
              <strong>🗄️ Database:</strong> SQLite with sample schema
            </div>
          </div>
          <div className="instructions">
            <h3>🔄 Next Steps:</h3>
            <ul>
              <li>Complete Kanban board implementation</li>
              <li>Add drag-and-drop functionality</li>
              <li>Implement authentication UI</li>
              <li>Create issue management forms</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;