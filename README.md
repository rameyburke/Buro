# Buro - Agile Project Management Application

**Sprint 3 Status:** ✅ Notifications & Reports - Complete!

A Jira-like agile project management application built with FastAPI backend and React frontend.

## Completed Sprints:
- ✅ **Sprint 1:** Database Models & Foundation (Backend architecture, Kanban schema)
- ✅ **Sprint 2:** Kanban & Relationships (Full issue CRUD, drag-and-drop board)
- ✅ **Sprint 3:** Notifications & Reports (Email notifications, analytics dashboard)

## Sprint 3 Features:
- **Email Notifications:** SMTP-based notifications for issue assignments and updates
- **Analytics Dashboard:** Team velocity, burndown charts, workload distribution
- **Issue Aging Reports:** Identify issues that may be stuck or need attention
- **Comprehensive Reporting:** Project overviews, completion rates, velocity tracking

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- Git

## Backend Setup

1. **Navigate to the project directory**
   ```bash
   cd /mnt/c/Users/ramey/source/repos/Buro
   ```

2. **Install Python dependencies**
   ```bash
   poetry install
   ```

3. **Set up the database**
   ```bash
   # Create tables
   poetry run python scripts/create_tables.py

   # Optionally seed with sample data
   poetry run python scripts/init_db.py
   ```

4. **Start the FastAPI backend**
   ```bash
   # Development server with hot reload
   poetry run python buro/main.py

   # Or using uvicorn directly
   poetry run uvicorn buro.main:app --reload --host 127.0.0.1 --port 8000
   ```

   The API will be available at http://localhost:8000

## Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies**
   ```bash
   npm install
   ```

3. **Start the React development server**
   ```bash
   npm start
   ```

   The React app will be available at http://localhost:3000

## 🎯 Usage

### Sample Login Credentials (if you seeded the database)
- **Admin**: admin@buro.dev / admin123
- **Manager**: manager@buro.dev / manager123
- **Developer 1**: developer1@buro.dev / dev123
- **Developer 2**: developer2@buro.dev / dev123

### Features
- **Kanban Board**: Drag-and-drop issue management
- **Issue Management**: Create, update, and track issues (Epics, Stories, Tasks, Bugs)
- **Project Organization**: Group issues by projects with unique keys (PROJ-123)
- **Role-based Access**: Different permissions for Admin, Manager, Developer roles

## 📁 Project Structure

```
buro/
├── buro/               # FastAPI backend
│   ├── api/           # API routers (auth, issues, projects, users)
│   ├── core/          # Database, config
│   ├── models/        # SQLAlchemy models
│   ├── services/      # Business logic
│   └── main.py        # FastAPI application entry point
├── frontend/          # React frontend
│   ├── src/
│   │   ├── components/# React components
│   │   ├── stores/    # Zustand state management
│   │   ├── types/     # TypeScript type definitions
│   │   └── lib/       # Utilities and API client
│   └── package.json
├── scripts/           # Database setup scripts
└── pyproject.toml     # Python dependencies
```

## 🛠 Development

### Backend
- **FastAPI**: Modern async Python web framework
- **SQLAlchemy**: Database ORM with async support
- **PostgreSQL/SQLite**: Database (configurable)
- **JWT**: Authentication tokens

### Frontend
- **React 18**: UI framework with hooks
- **TypeScript**: Type safety for JavaScript
- **Zustand**: Lightweight state management
- **@dnd-kit**: Drag-and-drop functionality
- **Tailwind CSS**: Utility-first styling

### Key Design Decisions
- **Service Layer**: Business logic separated from API routes
- **JWT Authentication**: Stateless authentication
- **UUID Primary Keys**: Security and distributed system compatibility
- **Role-based Access Control**: Flexible permission system
- **Kanban Workflow**: Simple, flexible status transitions

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
SECRET_KEY=your-secret-key-here-change-this-in-production
DATABASE_URL=sqlite+aiosqlite:///./buro.db  # or postgresql://...
```

### API Endpoints
- `POST /api/auth/login` - User authentication
- `GET /api/issues` - List issues with filtering
- `POST /api/issues` - Create new issue
- `GET /api/issues/board/{projectId}` - Kanban board data
- `GET /api/projects` - List user projects
- `GET /api/auth/me` - Get current user

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

## 🧪 Testing

### Backend Tests
```bash
poetry run pytest
```

### Frontend Tests
```bash
cd frontend && npm test
```

## 🚀 Production Deployment

### Backend
```bash
# Using Gunicorn
poetry run gunicorn buro.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend
```bash
cd frontend
npm run build
# Serve built files from dist/ directory
```

## 🤝 Contributing

This application is designed as a learning tool with comprehensive comments explaining:
- Why architectural decisions were made
- What tradeoffs exist in the implementation
- How different patterns and technologies work together