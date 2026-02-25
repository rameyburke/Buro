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
import { Button } from '../components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card'

// Types for API responses (already defined in types/api.ts)
// Using local imports for clarity and single responsibility

export function ProjectsPage() {
  const {
    projects,
    currentProject,
    isAuthenticated,
    loadProjects,
    setCurrentProject
  } = useAppStore()

  const [showCreateForm, setShowCreateForm] = useState(false)
  const [loading, setLoading] = useState(false)

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

  const handleProjectSelect = (project: any) => {
    setCurrentProject(project)
  }

  const handleCreateProjectSuccess = () => {
    setShowCreateForm(false)
    loadProjects() // Refresh the list
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
          <p className="text-gray-600">Manage your agile project workspaces</p>
        </div>

        <Button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 hover:bg-blue-700"
        >
          + New Project
        </Button>
      </div>

      {/* Current Project Display */}
      {currentProject && (
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center">
                🎯 Current Project: {currentProject.key} - {currentProject.name}
              </CardTitle>
              <span className="text-sm text-blue-600 font-medium">Active</span>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600">{currentProject.description}</p>
            <p className="text-sm text-gray-500 mt-2">
              Created: {new Date(currentProject.created_at).toLocaleDateString()}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Projects List */}
      <div className="grid gap-4">
        {projects.map((project) => (
          <Card
            key={project.id}
            className={`cursor-pointer transition-all ${
              currentProject?.id === project.id
                ? 'border-blue-500 ring-1 ring-blue-500'
                : 'hover:shadow-md'
            }`}
            onClick={() => handleProjectSelect(project)}
          >
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-3">
                  <div className="px-2 py-1 bg-gray-100 text-gray-800 text-sm font-mono rounded">
                    {project.key}
                  </div>
                  {project.name}
                </CardTitle>
                {currentProject?.id === project.id && (
                  <span className="text-sm text-blue-600 font-medium">✓ Selected</span>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {project.description && (
                <p className="text-gray-600 mb-3">{project.description}</p>
              )}
              <div className="flex items-center justify-between text-sm text-gray-500">
                <span>Owner: {project.owner_id}</span>
                <span>Created: {new Date(project.created_at).toLocaleDateString()}</span>
              </div>
            </CardContent>
          </Card>
        ))}

        {projects.length === 0 && (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">📂</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No projects yet</h3>
            <p className="text-gray-600 mb-4">Create your first project to get started with agile management.</p>
            <Button onClick={() => setShowCreateForm(true)}>
              Create Your First Project
            </Button>
          </div>
        )}
      </div>

      {/* Create Project Modal */}
      {showCreateForm && (
        <ProjectCreateModal
          onClose={() => setShowCreateForm(false)}
          onSuccess={handleCreateProjectSuccess}
        />
      )}
    </div>
  )
}

// Modal Component for creating projects
function ProjectCreateModal({ onClose, onSuccess }: { onClose: () => void, onSuccess: () => void }) {
  const [formData, setFormData] = useState({
    name: '',
    key: '',
    description: ''
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
      const success = await useAppStore.getState().createProject({
        ...formData,
        key: formData.key.toUpperCase()
      })

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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <h2 className="text-xl font-bold mb-4">Create New Project</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          {errors.general && (
            <div className="text-red-600 text-sm bg-red-50 p-2 rounded">
              {errors.general}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Project Name *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="My Agile Project"
              required
            />
            {errors.name && <p className="text-red-600 text-sm mt-1">{errors.name}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Project Key *
            </label>
            <input
              type="text"
              value={formData.key}
              onChange={(e) => setFormData({ ...formData, key: e.target.value.toUpperCase() })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
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
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 h-20"
              placeholder="Optional description of the project and its goals..."
            />
          </div>

          <div className="flex justify-end space-x-3 pt-4">
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
              {loading ? 'Creating...' : 'Create Project'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}