// frontend/src/lib/api.ts
//
// HTTP client for communicating with the FastAPI backend.
//
// Educational Notes for Junior Developers:
// - API client layer: Separate network logic from UI components.
// - Fetch vs Axios: Native fetch is modern, built-in, no extra dependencies.
// - Error handling: Centralized error responses for consistent UX.
// - Authentication: Automatic JWT token inclusion for protected routes.

import type {
  User,
  Project,
  Issue,
  KanbanBoard,
  AuthResponse,
  IssueCreate,
  IssueUpdate,
  IssueListResponse,
  UserListResponse
} from '../types/api'

// API configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api'

// Utility function for authenticated fetch requests
// Why this function: DRYs up JWT header inclusion logic and handles FastAPI redirects
async function authenticatedFetch(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = localStorage.getItem('token')

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>)
  }

  // Include JWT token if available
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  // Ensure trailing slash for REST endpoints without query strings to avoid FastAPI redirects
  const hasQuery = endpoint.includes('?') || endpoint.includes('#')
  const normalizedEndpoint = hasQuery
    ? endpoint
    : endpoint.endsWith('/')
      ? endpoint
      : `${endpoint}/`

  const response = await fetch(`${API_BASE_URL}${normalizedEndpoint}`, {
    ...options,
    headers,
    redirect: 'follow' // Handle FastAPI 307 redirects automatically
  })

  // Handle common HTTP errors
  if (!response.ok) {
    let errorMessage = 'Unknown error'

    if (response.status === 401) {
      errorMessage = 'Not authenticated - please log in'
      // Clear invalid token on 401
      localStorage.removeItem('token')
    } else if (response.status === 403) {
      errorMessage = 'Access forbidden'
    } else {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error', fullResponse: response }))
      errorMessage = errorData.detail || `HTTP ${response.status}: ${response.statusText}`
      if (errorData.detail === 'Unknown error') {
        console.error('API Error details:', response.status, response.statusText, errorData)
      }
    }

    throw new Error(errorMessage)
  }

  return response
}

// Why async functions: All network requests return promises
// Why type annotations: TypeScript ensures response types match expectations

// Authentication endpoints
export async function login(email: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  })

  if (!response.ok) {
    throw new Error('Invalid credentials')
  }

  return response.json()
}

export async function register(
  email: string,
  password: string,
  full_name: string
): Promise<AuthResponse> {
  const response = await authenticatedFetch('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, full_name })
  })

  return response.json()
}

export async function getCurrentUser(): Promise<User> {
  const response = await authenticatedFetch('/auth/me')
  return response.json()
}

// Project endpoints
export async function getProjects(): Promise<Project[]> {
  const response = await authenticatedFetch('/projects')
  const data = await response.json()
  return data.projects
}

export async function getUsers(): Promise<User[]> {
  const response = await authenticatedFetch('/users')
  const data: UserListResponse = await response.json()
  return data.users
}

export async function createProject(
  name: string,
  key: string,
  description?: string
): Promise<Project> {
  const response = await authenticatedFetch('/projects', {
    method: 'POST',
    body: JSON.stringify({ name, key, description })
  })

  return response.json()
}

export async function updateProject(
  projectId: string,
  updates: Partial<Pick<Project, 'name' | 'key' | 'description'>>
): Promise<Project> {
  const response = await authenticatedFetch(`/projects/${projectId}`, {
    method: 'PUT',
    body: JSON.stringify(updates)
  })

  return response.json()
}

export async function deleteProject(projectId: string): Promise<void> {
  await authenticatedFetch(`/projects/${projectId}`, {
    method: 'DELETE'
  })
}

// Issue endpoints
export async function getIssues(filters: {
  project_id?: string,
  assignee_id?: string,
  status?: string,
  issue_type?: string
} = {}): Promise<Issue[]> {
  const params = new URLSearchParams()

  // Convert filters to query parameters
  Object.entries(filters).forEach(([key, value]) => {
    if (value && value !== 'undefined' && value !== 'null') {
      params.append(key, value)
    }
  })

  const response = await authenticatedFetch(`/issues?${params}`)
  const data: IssueListResponse = await response.json()

  return data.issues
}

export async function createIssue(issue: IssueCreate): Promise<Issue> {
  const response = await authenticatedFetch('/issues', {
    method: 'POST',
    body: JSON.stringify(issue)
  })

  return response.json()
}

export async function updateIssue(
  issueId: string,
  updates: IssueUpdate
): Promise<Issue> {
  const response = await authenticatedFetch(`/issues/${issueId}`, {
    method: 'PUT',
    body: JSON.stringify(updates)
  })

  return response.json()
}

export async function moveIssue(issueId: string, newStatus: string): Promise<Issue> {
  const formData = new URLSearchParams()
  formData.append('new_status', newStatus)

  const response = await authenticatedFetch(`/issues/${issueId}/status`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: formData.toString()
  })

  const contentType = response.headers.get('content-type')
  if (contentType && contentType.includes('application/json')) {
    return response.json()
  } else {
    // Handle non-JSON responses (though should be JSON)
    throw new Error('Invalid response from server')
  }
}

export async function getKanbanBoard(projectId: string): Promise<KanbanBoard> {
  const response = await authenticatedFetch(`/issues/projects/${projectId}/kanban`)
  return response.json()
}

export async function deleteIssue(issueId: string): Promise<void> {
  await authenticatedFetch(`/issues/${issueId}`, {
    method: 'DELETE'
  })
}

// Utility function for parsing issue keys
export function parseIssueKey(key: string): { projectKey: string, issueNumber: number } {
  const parts = key.split('-')
  return {
    projectKey: parts[0],
    issueNumber: parseInt(parts[1], 10)
  }
}

// Export API base URL for testing/configuration
export { API_BASE_URL }
