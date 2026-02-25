// frontend/src/pages/Issues.tsx
//
// Issues management page - list, create, and manage issues.
//
// Educational Notes for Junior Developers:
// - Table vs Card Layout: Table for density/list view, cards for Kanban board.
//   Tables: Better for scanning/filtered lists; Cards: Better for status visualization.
// - Inline editing vs Modal forms: Inline for quick edits (status), modal for complex changes.
//   Tradeoff: UX convenience vs visual clutter and complexity.
// - Bulk operations: Multi-select checkboxes for batch updates.
//   Benefits: Productivity; Drawbacks: Complex state management.
// - Search/filter combinations: Server-side vs client-side filtering.
//   Server-side: Scalable, reduces data transfer; Client-side: Faster for small datasets.

import React, { useState, useEffect } from 'react'
import useAppStore from '../stores/appStore'
import { Button } from '../components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card'
import { IssueCard } from '../components/issues/IssueCard'

// Why separate page: Issues have complex CRUD needs that deserve dedicated focus
// Alternative: Inline creation in Kanban board (adds clutter, complex state management)
export function IssuesPage() {
  const {
    issues,
    currentProject,
    isAuthenticated,
    loadIssues
  } = useAppStore()

  const [showCreateForm, setShowCreateForm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({
    status: '',
    type: '',
    assignee: ''
  })

  // Load issues when page mounts or project changes
  useEffect(() => {
    if (currentProject) {
      loadIssues(currentProject.id)
    }
  }, [currentProject, loadIssues])

  const filteredIssues = issues.filter(issue => {
    // Simple client-side filtering - acceptable for moderate data volumes
    // Why client-side: No need for additional API calls for simple filters
    // Alternative: Server-side for large datasets to reduce transfer/reduce client load
    if (filters.status && issue.status !== filters.status) return false
    if (filters.type && issue.issue_type !== filters.type) return false
    if (filters.assignee && issue.assignee_id !== filters.assignee) return false
    return true
  })

  const handleCreateSuccess = () => {
    setShowCreateForm(false)
    if (currentProject) {
      loadIssues(currentProject.id)
    }
  }

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Select a Project First
          </h2>
          <p className="text-gray-600">
            Go to <a href="/projects" className="text-blue-600">Projects</a> to select or create a project.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Issues</h1>
          <p className="text-gray-600">
            Manage issues for {currentProject.key} - {currentProject.name}
          </p>
        </div>

        <Button
          onClick={() => setShowCreateForm(true)}
          className="bg-green-600 hover:bg-green-700"
        >
          + New Issue
        </Button>
      </div>

      {/* Issue Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {['backlog', 'to_do', 'in_progress', 'done'].map(status => {
          const count = issues.filter(issue => issue.status === status).length
          const statusLabel = {
            backlog: 'Backlog',
            to_do: 'To Do',
            in_progress: 'In Progress',
            done: 'Done'
          }[status]

          return (
            <Card key={status}>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">{count}</div>
                <p className="text-xs text-gray-600 uppercase">{statusLabel}</p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex space-x-4">
            <select
              value={filters.status}
              onChange={(e) => setFilters({...filters, status: e.target.value})}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="">All Statuses</option>
              <option value="backlog">Backlog</option>
              <option value="to_do">To Do</option>
              <option value="in_progress">In Progress</option>
              <option value="done">Done</option>
            </select>

            <select
              value={filters.type}
              onChange={(e) => setFilters({...filters, type: e.target.value})}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="">All Types</option>
              <option value="epic">Epic</option>
              <option value="story">Story</option>
              <option value="task">Task</option>
              <option value="bug">Bug</option>
            </select>

            <Button
              onClick={() => setFilters({ status: '', type: '', assignee: '' })}
              variant="outline"
              size="sm"
            >
              Clear Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Issues List */}
      <div className="space-y-2">
        {filteredIssues.length === 0 ? (
          <Card>
            <CardContent className="pt-12 pb-12">
              <div className="text-center">
                <div className="text-4xl mb-4">📋</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No issues found</h3>
                <p className="text-gray-600 mb-4">
                  {issues.length === 0
                    ? "Create your first issue to get started."
                    : "Try adjusting your filters."
                  }
                </p>
                <Button onClick={() => setShowCreateForm(true)}>
                  Create Issue
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {filteredIssues.map((issue) => (
              <div key={issue.id} className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm text-gray-500">{issue.key}</span>
                      <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                        issue.issue_type === 'bug' ? 'bg-red-100 text-red-700' :
                        issue.issue_type === 'epic' ? 'bg-purple-100 text-purple-700' :
                        issue.issue_type === 'story' ? 'bg-blue-100 text-blue-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {issue.issue_type}
                      </span>
                      <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                        issue.priority === 'highest' ? 'bg-red-200 text-red-800' :
                        issue.priority === 'high' ? 'bg-orange-200 text-orange-800' :
                        issue.priority === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                        'bg-gray-200 text-gray-700'
                      }`}>
                        {issue.priority}
                      </span>
                    </div>

                    <h3 className="font-medium text-gray-900 mb-2">
                      {issue.title}
                    </h3>

                    {issue.description && (
                      <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                        {issue.description}
                      </p>
                    )}

                    <div className="flex items-center text-xs text-gray-500 gap-4">
                      <span>Status: <strong>{issue.status.replace('_', ' ').toUpperCase()}</strong></span>
                      {issue.assignee_id && <span>Assigned to: Developer</span>}
                      <span>Reporter: User</span>
                    </div>
                  </div>

                  <div className="flex space-x-1">
                    <Button size="sm" variant="outline">
                      Edit
                    </Button>
                    <Button size="sm" variant="destructive">
                      Delete
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Issue Modal */}
      {showCreateForm && (
        <IssueCreateModal
          onClose={() => setShowCreateForm(false)}
          onSuccess={handleCreateSuccess}
        />
      )}
    </div>
  )
}

// Issue Creation Modal
function IssueCreateModal({ onClose, onSuccess }: { onClose: () => void, onSuccess: () => void }) {
  const { currentProject, createIssue } = useAppStore()

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    issue_type: 'task' as const,
    priority: 'medium' as const,
    assignee_id: ''
  })

  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setErrors({})

    try {
      const validationErrors: Record<string, string> = {}

      if (!formData.title.trim()) validationErrors.title = 'Issue title is required'
      if (!currentProject) validationErrors.project = 'No project selected'

      if (Object.keys(validationErrors).length > 0) {
        setErrors(validationErrors)
        setLoading(false)
        return
      }

      const success = await createIssue({
        ...formData,
        project_id: currentProject!.id,
        assignee_id: formData.assignee_id || undefined
      })

      if (success) {
        onSuccess()
      } else {
        setErrors({ general: 'Failed to create issue. Please try again.' })
      }
    } catch (error: any) {
      setErrors({ general: error.message || 'An error occurred' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-lg mx-4 max-h-[80vh] overflow-y-auto">
        <h2 className="text-xl font-bold mb-4">Create New Issue</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          {errors.general && (
            <div className="text-red-600 text-sm bg-red-50 p-3 rounded">
              {errors.general}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Issue Title *
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Brief description of the issue..."
              required
            />
            {errors.title && <p className="text-red-600 text-sm mt-1">{errors.title}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 h-24"
              placeholder="Detailed issue description..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Type
              </label>
              <select
                value={formData.issue_type}
                onChange={(e) => setFormData({ ...formData, issue_type: e.target.value as any })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="task">Task</option>
                <option value="bug">Bug</option>
                <option value="story">Story</option>
                <option value="epic">Epic</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Priority
              </label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value as any })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="lowest">Lowest</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="highest">Highest</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Assignee (Optional)
            </label>
            <select
              value={formData.assignee_id}
              onChange={(e) => setFormData({ ...formData, assignee_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Unassigned</option>
              {/* Would load actual users from API */}
              <option value="dev1">Developer 1</option>
              <option value="dev2">Developer 2</option>
            </select>
          </div>

          {currentProject && (
            <div className="bg-blue-50 p-3 rounded">
              <p className="text-sm text-blue-700">
                Issue will be created in project: <strong>{currentProject.key}</strong>
              </p>
            </div>
          )}

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
              disabled={loading || !formData.title.trim()}
            >
              {loading ? 'Creating...' : 'Create Issue'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}