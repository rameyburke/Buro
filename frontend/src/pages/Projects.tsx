// frontend/src/pages/Projects.tsx
//
// Project management page - list, create, and manage projects.
//
// Educational Notes for Junior Developers:
// - Page-level component organization: Each feature area gets its own page
//   vs. monolithic components. Benefits: Maintainability, testability, load splitting.
// - State management patterns: Local component state for forms vs global store
//   for shared data. Local state for transient data, global for persistent/app-wide.
// - Form handling: Controlled components with React state vs uncontrolled.
//   Controlled: Predictable, immediate validation; Tradeoff: More code for simple forms.
// - API integration: Component lifecycle vs custom hooks for data fetching.
//   Hooks: Reusable, testable; Components: Simple for one-time use.

import React, { useState } from 'react'
import useAppStore from '../stores/appStore'
import type { Project } from '../types/api'
import { Button } from '../components/ui/button'

// Types for API responses (already defined in types/api.ts)
// Using local imports for clarity and single responsibility

export function ProjectsPage() {
  const {
    projects,
    currentProject,
    loadProjects,
    setCurrentProject,
    isLoading
  } = useAppStore()

  const [showCreateForm, setShowCreateForm] = useState(false)
  const [projectToEdit, setProjectToEdit] = useState<Project | null>(null)
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null)

  // Why local state for form visibility:
  // - Transient UI state that doesn't need global persistence
  // - Easy to reset on navigation/modal close
  // - Doesn't clutter global store with page-specific state

  React.useEffect(() => {
    // Load projects on page mount
    // Why in useEffect: React's lifecycle pattern for data fetching
    // Alternative: Load projects in store initialization (more eager loading)
    loadProjects()
  }, [loadProjects])

  const handleProjectSelect = (project: Project) => {
    setCurrentProject(project)
  }

  const handleRefresh = async () => {
    await loadProjects()
  }

  return (
    <div className="projects-page">
      <div className="projects-header">
        <div>
          <h1>Projects</h1>
          <p>Manage your agile workspaces and configure project metadata.</p>
        </div>
        <Button onClick={() => setShowCreateForm(true)} className="bg-blue-600 hover:bg-blue-700">
          + New Project
        </Button>
      </div>

      <div className="projects-table-wrapper">
        <table className="projects-table">
          <thead>
            <tr>
              <th>Project</th>
              <th>Description</th>
              <th>Owner</th>
              <th>Created</th>
              <th className="actions-col">Actions</th>
            </tr>
          </thead>
          <tbody>
            {projects.map((project) => {
              const active = currentProject?.id === project.id
              return (
                <tr key={project.id} className={active ? 'active-row' : undefined}>
                  <td>
                    <div className="project-main">
                      <span className="project-pill">{project.key}</span>
                      <div>
                        <p className="project-name">{project.name}</p>
                        {active && <span className="active-badge">Active</span>}
                      </div>
                    </div>
                  </td>
                  <td className="project-description">
                    {project.description || <span className="muted">No description</span>}
                  </td>
                  <td>{project.owner_name || <span className="muted">{project.owner_id || '—'}</span>}</td>
                  <td>{new Date(project.created_at).toLocaleDateString()}</td>
                  <td>
                    <div className="table-actions">
                      <button
                        className="table-action"
                        onClick={() => handleProjectSelect(project)}
                        disabled={active}
                      >
                        {active ? 'Selected' : 'Set Active'}
                      </button>
                      <button
                        className="table-action"
                        onClick={() => setProjectToEdit(project)}
                      >
                        Edit
                      </button>
                      <button
                        className="table-action danger"
                        onClick={() => setProjectToDelete(project)}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}

            {!isLoading && projects.length === 0 && (
              <tr>
                <td colSpan={5}>
                  <div className="empty-state">
                    <div className="icon">📂</div>
                    <h3>No projects yet</h3>
                    <p>Create your first project to get started.</p>
                    <Button onClick={() => setShowCreateForm(true)}>
                      Create Project
                    </Button>
                  </div>
                </td>
              </tr>
            )}

            {isLoading && (
              <tr>
                <td colSpan={5}>
                  <div className="loading-row">Loading projects…</div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {showCreateForm && (
        <ProjectFormModal
          mode="create"
          onClose={() => setShowCreateForm(false)}
          onSuccess={() => {
            setShowCreateForm(false)
            handleRefresh()
          }}
        />
      )}

      {projectToEdit && (
        <ProjectFormModal
          mode="edit"
          project={projectToEdit}
          onClose={() => setProjectToEdit(null)}
          onSuccess={() => {
            setProjectToEdit(null)
            handleRefresh()
          }}
        />
      )}

      {projectToDelete && (
        <DeleteProjectModal
          project={projectToDelete}
          onClose={() => setProjectToDelete(null)}
          onDeleted={() => {
            setProjectToDelete(null)
            handleRefresh()
          }}
        />
      )}
    </div>
  )
}

interface ProjectFormModalProps {
  mode: 'create' | 'edit'
  project?: Project | null
  onClose: () => void
  onSuccess: () => void
}

function ProjectFormModal({ mode, project, onClose, onSuccess }: ProjectFormModalProps) {
  const [formData, setFormData] = useState({
    name: project?.name ?? '',
    key: project?.key ?? '',
    description: project?.description ?? ''
  })
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setErrors({})

    try {
      // Validate form data
      const validationErrors: Record<string, string> = {}

      if (!formData.name.trim()) validationErrors.name = 'Project name is required'
      if (!formData.key.trim()) validationErrors.key = 'Project key is required'

      // Key validation (simple uppercase alphanumeric check)
      if (formData.key && !/^[A-Z0-9]+$/.test(formData.key.toUpperCase())) {
        validationErrors.key = 'Project key must be uppercase letters and numbers only'
      }

      if (Object.keys(validationErrors).length > 0) {
        setErrors(validationErrors)
        setLoading(false)
        return
      }

      // Submit project creation
      // Using global store since project creation affects global state
      let success = false

      if (mode === 'create') {
        success = await useAppStore.getState().createProject({
          ...formData,
          key: formData.key.toUpperCase()
        })
      } else if (project) {
        success = await useAppStore.getState().updateProject(project.id, {
          name: formData.name,
          key: formData.key.toUpperCase(),
          description: formData.description
        })
      }

      if (success) {
        onSuccess()
      } else {
        setErrors({ general: 'Failed to create project. Please try again.' })
      }
    } catch (error: any) {
      setErrors({ general: error.message || 'An error occurred' })
    } finally {
      setLoading(false)
    }
  }

  return (
    // Simple modal overlay - could use a proper modal library like Radix or Headless UI
    <div className="modal-overlay">
      <div className="modal-card">
        <h2 className="modal-title">{mode === 'create' ? 'Create Project' : 'Edit Project'}</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          {errors.general && (
            <div className="text-red-600 text-sm bg-red-50 p-2 rounded">
              {errors.general}
            </div>
          )}

          <div>
            <label className="form-label">Project Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="form-input"
              placeholder="My Agile Project"
              required
            />
            {errors.name && <p className="text-red-600 text-sm mt-1">{errors.name}</p>}
          </div>

          <div>
            <label className="form-label">Project Key *</label>
            <input
              type="text"
              value={formData.key}
              onChange={(e) => setFormData({ ...formData, key: e.target.value.toUpperCase() })}
              className="form-input font-mono"
              placeholder="PROJ"
              maxLength={10}
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              Short code used as issue prefix (e.g., PROJ-123). Must be uppercase letters/numbers only.
            </p>
            {errors.key && <p className="text-red-600 text-sm mt-1">{errors.key}</p>}
          </div>

          <div>
            <label className="form-label">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="form-textarea"
              placeholder="Optional description of the project and its goals..."
            />
          </div>

          <div className="modal-actions">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={loading || !formData.name.trim() || !formData.key.trim()}
            >
              {loading ? 'Saving…' : mode === 'create' ? 'Create Project' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

function DeleteProjectModal({ project, onClose, onDeleted }: { project: Project, onClose: () => void, onDeleted: () => void }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleDelete = async () => {
    setLoading(true)
    setError(null)

    try {
      const success = await useAppStore.getState().deleteProject(project.id)
      if (success) {
        onDeleted()
      } else {
        setError('Unable to delete project. Please try again.')
      }
    } catch (err: any) {
      setError(err.message || 'Unable to delete project. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-card">
        <h2 className="modal-title">Delete Project</h2>
        <p className="text-sm text-gray-600">
          This action cannot be undone. Issues under <strong>{project.key}</strong> will remain but the
          project container will be removed.
        </p>
        {error && <div className="text-red-600 text-sm bg-red-50 p-2 rounded mt-3">{error}</div>}

        <div className="modal-actions">
          <Button variant="outline" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button className="bg-red-600 hover:bg-red-700" onClick={handleDelete} disabled={loading}>
            {loading ? 'Deleting…' : 'Delete Project'}
          </Button>
        </div>
      </div>
    </div>
  )
}
