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

import React, { useState, useEffect, useMemo } from 'react'
import useAppStore from '../stores/appStore'
import { Button } from '../components/ui/button'
import { Card, CardContent } from '../components/ui/card'
import type { Issue } from '../types/api'

// Why separate page: Issues have complex CRUD needs that deserve dedicated focus
// Alternative: Inline creation in Kanban board (adds clutter, complex state management)
export function IssuesPage() {
  const {
    issues,
    currentProject,
    isLoading,
    loadIssues
  } = useAppStore()

  const [showCreateForm, setShowCreateForm] = useState(false)
  const [issueToEdit, setIssueToEdit] = useState<Issue | null>(null)
  const [issueToDelete, setIssueToDelete] = useState<Issue | null>(null)
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

  const handleRefresh = () => {
    if (currentProject) {
      loadIssues(currentProject.id)
    }
  }

  const handleCreateSuccess = () => {
    setShowCreateForm(false)
    handleRefresh()
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
    <div className="issues-page">
      <div className="issues-header">
        <div>
          <h1>Issues</h1>
          <p>Track every piece of work inside {currentProject.key} · {currentProject.name}</p>
        </div>
        <Button onClick={() => setShowCreateForm(true)} className="bg-green-600 hover:bg-green-700">
          + New Issue
        </Button>
      </div>

      <div className="issue-stats">
        {['backlog', 'to_do', 'in_progress', 'done'].map((status) => {
          const count = issues.filter((issue) => issue.status === status).length
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

      <Card>
        <CardContent className="pt-6">
          <div className="issues-filters">
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="filter-control"
            >
              <option value="">All Statuses</option>
              <option value="backlog">Backlog</option>
              <option value="to_do">To Do</option>
              <option value="in_progress">In Progress</option>
              <option value="done">Done</option>
            </select>

            <select
              value={filters.type}
              onChange={(e) => setFilters({ ...filters, type: e.target.value })}
              className="filter-control"
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

      <div className="issues-table-wrapper">
        <table className="issues-table">
          <thead>
            <tr>
              <th>Key</th>
              <th>Title</th>
              <th>Status</th>
              <th>Priority</th>
              <th>Assignee</th>
              <th>Updated</th>
              <th className="actions-col">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredIssues.map((issue) => (
              <tr key={issue.id}>
                <td>
                  <div className="issue-key">
                    <span className="issue-pill">{issue.key}</span>
                    <span className={`issue-type ${issue.issue_type}`}>{issue.issue_type}</span>
                  </div>
                </td>
                <td>
                  <div className="issue-title">{issue.title}</div>
                  {issue.description && (
                    <p className="issue-description">{issue.description}</p>
                  )}
                </td>
                <td>
                  <span className={`status-badge status-${issue.status}`}>
                    {issue.status.replace('_', ' ')}
                  </span>
                </td>
                <td>
                  <span className={`priority-badge priority-${issue.priority}`}>
                    {issue.priority}
                  </span>
                </td>
                <td>
                  {issue.assignee_name || issue.assignee_id ? (
                    issue.assignee_name || issue.assignee_id
                  ) : (
                    <span className="muted">Unassigned</span>
                  )}
                </td>
                <td>{new Date(issue.updated_at).toLocaleDateString()}</td>
                <td>
                  <div className="table-actions">
                    <button className="table-action" onClick={() => console.log('view', issue.id)}>
                      View
                    </button>
                    <button className="table-action" onClick={() => setIssueToEdit(issue)}>
                      Edit
                    </button>
                    <button className="table-action danger" onClick={() => setIssueToDelete(issue)}>
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}

            {!isLoading && filteredIssues.length === 0 && (
              <tr>
                <td colSpan={7}>
                  <div className="empty-state">
                    <div className="icon">📋</div>
                    <h3>No issues found</h3>
                    <p>{issues.length === 0 ? 'Create your first issue to get started.' : 'Try adjusting your filters.'}</p>
                    <Button onClick={() => setShowCreateForm(true)}>Create Issue</Button>
                  </div>
                </td>
              </tr>
            )}

            {isLoading && (
              <tr>
                <td colSpan={7}>
                  <div className="loading-row">Loading issues…</div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {showCreateForm && (
        <IssueCreateModal
          onClose={() => setShowCreateForm(false)}
          onSuccess={handleCreateSuccess}
        />
      )}

      {issueToEdit && (
        <IssueEditModal
          issue={issueToEdit}
          onClose={() => setIssueToEdit(null)}
          onSuccess={() => {
            setIssueToEdit(null)
            handleRefresh()
          }}
        />
      )}

      {issueToDelete && (
        <IssueDeleteModal
          issue={issueToDelete}
          onClose={() => setIssueToDelete(null)}
          onDeleted={() => {
            setIssueToDelete(null)
            handleRefresh()
          }}
        />
      )}
    </div>
  )
}

// Issue Creation Modal
function IssueCreateModal({ onClose, onSuccess }: { onClose: () => void, onSuccess: () => void }) {
  const { currentProject, createIssue, users, usersLoading, loadUsers } = useAppStore()

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    issue_type: 'task' as const,
    priority: 'medium' as const,
    assignee_id: ''
  })

  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [assigneeSearch, setAssigneeSearch] = useState('')

  useEffect(() => {
    if (users.length === 0 && !usersLoading) {
      loadUsers()
    }
  }, [users.length, usersLoading, loadUsers])

  const filteredUsers = useMemo(() => {
    const query = assigneeSearch.trim().toLowerCase()
    if (!query) {
      return users
    }
    return users.filter((user) =>
      user.full_name.toLowerCase().includes(query) || user.email.toLowerCase().includes(query)
    )
  }, [users, assigneeSearch])

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
            <input
              type="text"
              value={assigneeSearch}
              onChange={(e) => setAssigneeSearch(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 mb-2"
              placeholder="Search team members"
            />
            <select
              value={formData.assignee_id}
              onChange={(e) => setFormData({ ...formData, assignee_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={usersLoading}
            >
              <option value="">Unassigned</option>
              {filteredUsers.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.full_name} ({user.role})
                </option>
              ))}
            </select>
            {usersLoading && <p className="text-xs text-gray-500 mt-1">Loading users…</p>}
            {!usersLoading && filteredUsers.length === 0 && (
              <p className="text-xs text-gray-500 mt-1">No users match "{assigneeSearch}".</p>
            )}
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

function IssueDeleteModal({ issue, onClose, onDeleted }: { issue: Issue, onClose: () => void, onDeleted: () => void }) {
  const deleteIssue = useAppStore((state) => state.deleteIssue)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleDelete = async () => {
    setLoading(true)
    setError(null)

    const success = await deleteIssue(issue.id)
    setLoading(false)

    if (success) {
      onDeleted()
    } else {
      setError('Failed to delete issue. Please try again.')
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-card">
        <h2 className="modal-title">Delete Issue</h2>
        <p className="text-sm text-gray-600 mb-4">
          This action cannot be undone. Issue <strong>{issue.key}</strong> ({issue.title}) will be permanently removed.
        </p>
        {error && <div className="text-red-600 text-sm bg-red-50 p-2 rounded mb-3">{error}</div>}
        <div className="modal-actions">
          <Button variant="outline" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button className="bg-red-600 hover:bg-red-700" onClick={handleDelete} disabled={loading}>
            {loading ? 'Deleting…' : 'Delete Issue'}
          </Button>
        </div>
      </div>
    </div>
  )
}

function IssueEditModal({ issue, onClose, onSuccess }: { issue: Issue, onClose: () => void, onSuccess: () => void }) {
  const updateIssue = useAppStore((state) => state.updateIssue)
  const users = useAppStore((state) => state.users)
  const usersLoading = useAppStore((state) => state.usersLoading)
  const loadUsers = useAppStore((state) => state.loadUsers)

  const [formData, setFormData] = useState({
    title: issue.title,
    description: issue.description || '',
    priority: issue.priority as Issue['priority'],
    assignee_id: issue.assignee_id || ''
  })
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [assigneeSearch, setAssigneeSearch] = useState('')

  useEffect(() => {
    if (users.length === 0 && !usersLoading) {
      loadUsers()
    }
  }, [users.length, usersLoading, loadUsers])

  const filteredUsers = useMemo(() => {
    const query = assigneeSearch.trim().toLowerCase()
    if (!query) {
      return users
    }
    return users.filter((user) =>
      user.full_name.toLowerCase().includes(query) || user.email.toLowerCase().includes(query)
    )
  }, [users, assigneeSearch])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setErrors({})

    if (!formData.title.trim()) {
      setErrors({ title: 'Title is required' })
      setLoading(false)
      return
    }

    const payload = {
      title: formData.title.trim(),
      description: formData.description || undefined,
      priority: formData.priority,
      assignee_id: formData.assignee_id || undefined
    }

    const success = await updateIssue(issue.id, payload)
    if (success) {
      onSuccess()
    } else {
      setErrors({ general: 'Failed to update issue. Please try again.' })
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-card">
        <h2 className="modal-title">Edit Issue</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          {errors.general && (
            <div className="text-red-600 text-sm bg-red-50 p-2 rounded">{errors.general}</div>
          )}

          <div>
            <label className="form-label">Title *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="form-input"
              required
            />
            {errors.title && <p className="text-red-600 text-sm mt-1">{errors.title}</p>}
          </div>

          <div>
            <label className="form-label">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="form-textarea"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="form-label">Priority</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value as Issue['priority'] })}
                className="form-input"
              >
                {['highest', 'high', 'medium', 'low', 'lowest'].map((priority) => (
                  <option key={priority} value={priority}>{priority}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="form-label">Assignee</label>
              <input
                type="text"
                value={assigneeSearch}
                onChange={(e) => setAssigneeSearch(e.target.value)}
                className="form-input mb-2"
                placeholder="Search team members"
              />
              <select
                value={formData.assignee_id}
                onChange={(e) => setFormData({ ...formData, assignee_id: e.target.value })}
                className="form-input"
                disabled={usersLoading}
              >
                <option value="">Unassigned</option>
                {filteredUsers.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.full_name} ({user.role})
                  </option>
                ))}
              </select>
              {usersLoading && <p className="text-xs text-gray-500 mt-1">Loading users…</p>}
              {!usersLoading && filteredUsers.length === 0 && (
                <p className="text-xs text-gray-500 mt-1">No team members match "{assigneeSearch}".</p>
              )}
            </div>
          </div>

          <div className="modal-actions">
            <Button variant="outline" type="button" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Saving…' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
