// frontend/src/stores/appStore.ts
//
// Zustand store for application-wide state management.
//
// Educational Notes for Junior Developers:
// - Zustand vs Redux: Simpler API, less boilerplate, built-in TypeScript.
//   Tradeoff: Less middleware ecosystem vs. learning curve reduction.
// - Store structure: One store for global state, split by domains.
// - Actions: Colocate actions with state for cleaner organization.
// - Persistence: Use Zustand middleware for localStorage sync.

import { create } from 'zustand'
import * as api from '../lib/api'
import type {
  AppState,
  User,
  Issue,
  Project,
  AuthResponse,
  KanbanBoard,
  IssueCreate,
  IssueUpdate
} from '../types/api'

// Define the store interface with actions
interface AppStore extends AppState {
  // Auth actions
  login: (email: string, password: string) => Promise<boolean>
  register: (email: string, password: string, fullName: string) => Promise<boolean>
  logout: () => void
  loadAuthFromStorage: () => void

  // Project actions
  loadProjects: () => Promise<boolean>
  setCurrentProject: (project: Project | null) => void

  // Issue actions
  loadIssues: (projectId?: string) => Promise<boolean>
  createIssue: (issue: IssueCreate) => Promise<boolean>
  updateIssue: (issueId: string, updates: IssueUpdate) => Promise<boolean>
  moveIssue: (issueId: string, newStatus: string) => Promise<boolean>
  setSelectedIssue: (issue: Issue | null) => void
  refreshKanbanBoard: () => Promise<boolean>
}

// Why create the store with an interface: TypeScript ensures action signatures
// are implemented correctly and state is properly typed.
const useAppStore = create<AppStore>((set, get) => ({
  // Initial state - everything has a default value
  // Why explicit nulls: Makes it clear what state exists vs doesn't exist
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: false,

  projects: [],
  currentProject: null,

  issues: [],
  kanbanBoard: {
    backlog: [],
    to_do: [],
    in_progress: [],
    done: []
  },
  selectedIssue: null,
  filters: {},

  // Auth actions
  login: async (email: string, password: string): Promise<boolean> => {
    set({ isLoading: true })

    try {
      const response: AuthResponse = await api.login(email, password)

      // Store token in localStorage for persistence
      // Why localStorage: Persists across browser refreshes vs sessionStorage
      localStorage.setItem('token', response.access_token)

      set({
        user: response.user,
        token: response.access_token,
        isAuthenticated: true,
        isLoading: false
      })

      return true
    } catch (error) {
      set({ isLoading: false })
      console.error('Login failed:', error)
      return false
    }
  },

  register: async (email: string, password: string, fullName: string): Promise<boolean> => {
    set({ isLoading: true })

    try {
      const response: AuthResponse = await api.register(email, password, fullName)

      localStorage.setItem('token', response.access_token)

      set({
        user: response.user,
        token: response.access_token,
        isAuthenticated: true,
        isLoading: false
      })

      return true
    } catch (error) {
      set({ isLoading: false })
      console.error('Registration failed:', error)
      return false
    }
  },

  logout: (): void => {
    // Clear authentication state
    localStorage.removeItem('token')

    set({
      user: null,
      token: null,
      isAuthenticated: false,
      // Clear project/issue state on logout for security
      projects: [],
      currentProject: null,
      issues: [],
      selectedIssue: null
    })
  },

  loadAuthFromStorage: (): void => {
    const token = localStorage.getItem('token')
    if (token) {
      // Could decode JWT and validate expiration here
      // For now, assume valid and load user info
      set({
        token,
        isAuthenticated: true
      })
    }
  },

  // Project actions
  loadProjects: async (): Promise<boolean> => {
    set({ isLoading: true })

    try {
      const projects = await api.getProjects()

      set({
        projects,
        isLoading: false,
        // Auto-select first project if none selected
        currentProject: get().currentProject || projects[0] || null
      })

      return true
    } catch (error) {
      set({ isLoading: false })
      console.error('Failed to load projects:', error)
      return false
    }
  },

  setCurrentProject: (project: Project | null): void => {
    set({ currentProject: project })

    // When project changes, refresh issues for new project
    if (project) {
      get().loadIssues(project.id)
    } else {
      set({ issues: [], kanbanBoard: { backlog: [], to_do: [], in_progress: [], done: [] } })
    }
  },

  // Issue actions
  loadIssues: async (projectId?: string): Promise<boolean> => {
    const currentProject = projectId || get().currentProject?.id
    if (!currentProject) {
      console.warn('No project selected for loading issues')
      return false
    }

    set({ isLoading: true })

    try {
      const issues = await api.getIssues({ project_id: currentProject })
      const kanbanBoard = await api.getKanbanBoard(currentProject)

      set({
        issues,
        kanbanBoard,
        isLoading: false
      })

      return true
    } catch (error) {
      set({ isLoading: false })
      console.error('Failed to load issues:', error)
      return false
    }
  },

  createIssue: async (issueData: IssueCreate): Promise<boolean> => {
    try {
      const newIssue = await api.createIssue(issueData)

      // Refresh the board to show the new issue
      await get().refreshKanbanBoard()

      return true
    } catch (error) {
      console.error('Failed to create issue:', error)
      return false
    }
  },

  updateIssue: async (issueId: string, updates: IssueUpdate): Promise<boolean> => {
    try {
      await api.updateIssue(issueId, updates)

      // Refresh issues and board
      await get().refreshKanbanBoard()

      return true
    } catch (error) {
      console.error('Failed to update issue:', error)
      return false
    }
  },

  moveIssue: async (issueId: string, newStatus: string): Promise<boolean> => {
    try {
      await api.moveIssue(issueId, newStatus)

      // Refresh board to reflect the move
      await get().refreshKanbanBoard()

      return true
    } catch (error) {
      console.error('Failed to move issue:', error)
      return false
    }
  },

  setSelectedIssue: (issue: Issue | null): void => {
    set({ selectedIssue: issue })
  },

  refreshKanbanBoard: async (): Promise<boolean> => {
    const currentProject = get().currentProject
    if (!currentProject) {
      return false
    }

    try {
      const kanbanBoard = await api.getKanbanBoard(currentProject.id)
      const issues = await api.getIssues({ project_id: currentProject.id })

      set({
        kanbanBoard,
        issues,
        isLoading: false
      })

      return true
    } catch (error) {
      console.error('Failed to refresh board:', error)
      return false
    }
  },
}))

// Export the store hook
export default useAppStore