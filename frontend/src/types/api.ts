// frontend/src/types/api.ts
//
// TypeScript type definitions for API responses.
//
// Educational Notes for Junior Developers:
// - TypeScript interfaces vs types: Use interfaces for object shapes,
//   types for unions and complex types (interfaces can be extended).
// - API contract types: Mirror backend schemas for type safety.
// - Optional fields: Use ? for nullable fields from API.

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'admin' | 'manager' | 'developer';
  avatar_url?: string;
}

export interface Project {
  id: string;
  name: string;
  key: string;
  description?: string;
  owner_id: string;
  default_assignee_id?: string;
  created_at: string;
  updated_at: string;
}

export type IssueStatus = 'backlog' | 'to_do' | 'in_progress' | 'done';
export type IssuePriority = 'highest' | 'high' | 'medium' | 'low' | 'lowest';
export type IssueType = 'epic' | 'story' | 'task' | 'bug';
export type UserRole = 'admin' | 'manager' | 'developer';

export interface Issue {
  id: string;
  key: string;  // PROJ-123 format
  title: string;
  description?: string;
  issue_type: IssueType;
  status: IssueStatus;
  priority: IssuePriority;
  project_id: string;
  reporter_id: string;
  assignee_id?: string;
  created_at: string;
  updated_at: string;
}

export interface IssueCreate {
  title: string;
  description?: string;
  issue_type?: 'epic' | 'story' | 'task' | 'bug';
  priority?: 'highest' | 'high' | 'medium' | 'low' | 'lowest';
  project_id: string;
  assignee_id?: string;
}

export interface IssueUpdate {
  title?: string;
  description?: string;
  priority?: 'highest' | 'high' | 'medium' | 'low' | 'lowest';
  assignee_id?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface KanbanBoard {
  backlog: Issue[];
  to_do: Issue[];
  in_progress: Issue[];
  done: Issue[];
}

// API request/response schemas
export interface IssueListResponse {
  issues: Issue[];
  total: number;
  skip: number;
  limit: number;
}

// Error response
export interface ApiError {
  detail: string;
  code?: string;
}

// Auth state
export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Project state
export interface ProjectState {
  projects: Project[];
  currentProject: Project | null;
  isLoading: boolean;
}

// Issue state
export interface IssueState {
  issues: Issue[];
  kanbanBoard: KanbanBoard;
  selectedIssue: Issue | null;
  isLoading: boolean;
  filters: IssueFilters;
}

// Combined app state
export interface AppState extends AuthState, ProjectState, IssueState {
  // Actions will be defined in the store
}

// Filter types for issue listing
export interface IssueFilters {
  projectId?: string;
  assigneeId?: string;
  reporterId?: string;
  status?: string;
  issueType?: string;
  search?: string;
}

// Form types
export interface LoginForm {
  email: string;
  password: string;
}

export interface RegisterForm extends LoginForm {
  full_name: string;
}

export interface IssueForm {
  title: string;
  description?: string;
  issue_type: 'epic' | 'story' | 'task' | 'bug';
  priority: 'highest' | 'high' | 'medium' | 'low' | 'lowest';
  assignee_id?: string;
}