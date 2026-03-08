import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Button } from '../components/ui/button'
import { Card, CardContent } from '../components/ui/card'
import useAppStore from '../stores/appStore'
import * as api from '../lib/api'
import type { User, UserRole } from '../types/api'

type UserFormState = {
  full_name: string
  email: string
  role: UserRole
}

const DEFAULT_USER_FORM: UserFormState = {
  full_name: '',
  email: '',
  role: 'developer',
}

export function UsersPage() {
  const currentUser = useAppStore((state) => state.user)
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [showInactive, setShowInactive] = useState(false)
  const [search, setSearch] = useState('')
  const [error, setError] = useState<string | null>(null)

  const [showAddModal, setShowAddModal] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [deletingUser, setDeletingUser] = useState<User | null>(null)
  const [tempPassword, setTempPassword] = useState<string | null>(null)

  const loadUsers = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await api.getUsers({
        includeInactive: showInactive,
        search: search.trim() || undefined,
        limit: 200,
      })
      setUsers(result)
    } catch (loadError: any) {
      setError(loadError?.message || 'Failed to load users')
    } finally {
      setLoading(false)
    }
  }, [search, showInactive])

  useEffect(() => {
    if (currentUser?.role === 'admin') {
      void loadUsers()
    }
    // Learning note: includeInactive + search in dependencies keeps the page
    // source of truth in URL-like local state. Tradeoff: more frequent requests,
    // but UI remains predictable and easy to reason about.
  }, [currentUser?.role, loadUsers])

  const sortedUsers = useMemo(
    () => [...users].sort((a, b) => a.full_name.localeCompare(b.full_name)),
    [users],
  )

  if (currentUser?.role !== 'admin') {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Only administrators can manage users.</div>
      </div>
    )
  }

  return (
    <div className="users-page">
      <div className="users-header">
        <div>
          <h1>User Maintenance</h1>
          <p>Manage team accounts, roles, and active status.</p>
        </div>
        <Button onClick={() => setShowAddModal(true)}>+ Add User</Button>
      </div>

      {tempPassword ? (
        <div className="users-temp-password" role="status">
          Temporary password: <strong>{tempPassword}</strong>
        </div>
      ) : null}

      <Card>
        <CardContent className="pt-6">
          <div className="users-filters">
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              className="form-input users-search"
              placeholder="Search by name or email"
            />
            <label className="users-inactive-toggle">
              <input
                type="checkbox"
                checked={showInactive}
                onChange={(event) => setShowInactive(event.target.checked)}
              />
              Show inactive users
            </label>
            <Button variant="outline" onClick={() => void loadUsers()} disabled={loading}>
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      {error ? <div className="users-error">{error}</div> : null}

      <div className="users-table-wrapper">
        <table className="users-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th className="actions-col">Actions</th>
            </tr>
          </thead>
          <tbody>
            {!loading && sortedUsers.length === 0 ? (
              <tr>
                <td colSpan={5}>
                  <div className="empty-state">
                    <h3>No users found</h3>
                    <p>Try changing your search or inactive filter.</p>
                  </div>
                </td>
              </tr>
            ) : null}

            {sortedUsers.map((user) => (
              <tr key={user.id}>
                <td>{user.full_name}</td>
                <td>{user.email}</td>
                <td>
                  <span className={`role-badge role-${user.role}`}>{user.role}</span>
                </td>
                <td>
                  <span className={user.is_active ? 'status-active' : 'status-inactive'}>
                    {user.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>
                  <div className="table-actions">
                    <button className="table-action" onClick={() => setEditingUser(user)}>
                      Edit
                    </button>
                    <button
                      className="table-action danger"
                      onClick={() => setDeletingUser(user)}
                      disabled={!user.is_active || user.id === currentUser.id}
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showAddModal ? (
        <UserCreateModal
          onClose={() => setShowAddModal(false)}
          onCreated={async (password) => {
            setShowAddModal(false)
            setTempPassword(password)
            await loadUsers()
          }}
        />
      ) : null}

      {editingUser ? (
        <UserEditModal
          user={editingUser}
          onClose={() => setEditingUser(null)}
          onSaved={async () => {
            setEditingUser(null)
            await loadUsers()
          }}
        />
      ) : null}

      {deletingUser ? (
        <UserDeleteModal
          user={deletingUser}
          onClose={() => setDeletingUser(null)}
          onDeleted={async () => {
            setDeletingUser(null)
            await loadUsers()
          }}
        />
      ) : null}
    </div>
  )
}

function UserCreateModal({
  onClose,
  onCreated,
}: {
  onClose: () => void
  onCreated: (temporaryPassword: string) => Promise<void>
}) {
  const [form, setForm] = useState<UserFormState>(DEFAULT_USER_FORM)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const result = await api.createUser(form)
      await onCreated(result.temporary_password)
    } catch (submitError: any) {
      setError(submitError?.message || 'Failed to create user')
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-card">
        <h2 className="modal-title">Add User</h2>
        <p className="text-sm text-gray-600 mb-4">
          We generate a temporary password so administrators can onboard users
          without waiting for an email flow.
        </p>
        <form onSubmit={submit} className="space-y-4">
          {error ? <div className="users-error">{error}</div> : null}
          <div>
            <label className="form-label" htmlFor="create-user-full-name">Full name</label>
            <input
              id="create-user-full-name"
              className="form-input"
              value={form.full_name}
              onChange={(event) => setForm({ ...form, full_name: event.target.value })}
              required
            />
          </div>
          <div>
            <label className="form-label" htmlFor="create-user-email">Email</label>
            <input
              id="create-user-email"
              type="email"
              className="form-input"
              value={form.email}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
              required
            />
          </div>
          <div>
            <label className="form-label" htmlFor="create-user-role">Role</label>
            <select
              id="create-user-role"
              className="form-input"
              value={form.role}
              onChange={(event) => setForm({ ...form, role: event.target.value as UserRole })}
            >
              <option value="admin">Admin</option>
              <option value="manager">Manager</option>
              <option value="developer">Developer</option>
            </select>
          </div>
          <div className="modal-actions">
            <Button type="button" variant="outline" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Creating...' : 'Create user'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

function UserEditModal({
  user,
  onClose,
  onSaved,
}: {
  user: User
  onClose: () => void
  onSaved: () => Promise<void>
}) {
  const [form, setForm] = useState<UserFormState>({
    full_name: user.full_name,
    email: user.email,
    role: user.role,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError(null)
    try {
      // Tradeoff: we keep edit payload narrow (name + role) to avoid coupling
      // account identity changes to this first admin workflow.
      await api.updateUser(user.id, {
        full_name: form.full_name,
        role: form.role,
      })
      await onSaved()
    } catch (submitError: any) {
      setError(submitError?.message || 'Failed to update user')
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-card">
        <h2 className="modal-title">Edit User</h2>
        <form onSubmit={submit} className="space-y-4">
          {error ? <div className="users-error">{error}</div> : null}
          <div>
            <label className="form-label" htmlFor="edit-user-full-name">Full name</label>
            <input
              id="edit-user-full-name"
              className="form-input"
              value={form.full_name}
              onChange={(event) => setForm({ ...form, full_name: event.target.value })}
              required
            />
          </div>
          <div>
            <label className="form-label" htmlFor="edit-user-email">Email</label>
            <input id="edit-user-email" className="form-input" value={form.email} disabled />
          </div>
          <div>
            <label className="form-label" htmlFor="edit-user-role">Role</label>
            <select
              id="edit-user-role"
              className="form-input"
              value={form.role}
              onChange={(event) => setForm({ ...form, role: event.target.value as UserRole })}
            >
              <option value="admin">Admin</option>
              <option value="manager">Manager</option>
              <option value="developer">Developer</option>
            </select>
          </div>
          <div className="modal-actions">
            <Button type="button" variant="outline" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Saving...' : 'Save changes'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

function UserDeleteModal({
  user,
  onClose,
  onDeleted,
}: {
  user: User
  onClose: () => void
  onDeleted: () => Promise<void>
}) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const confirmDelete = async () => {
    setLoading(true)
    setError(null)
    try {
      await api.deleteUser(user.id)
      await onDeleted()
    } catch (deleteError: any) {
      setError(deleteError?.message || 'Failed to deactivate user')
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-card">
        <h2 className="modal-title">Deactivate User</h2>
        <p className="text-sm text-gray-600 mb-4">
          This keeps historical references intact while removing the user from active
          workflows.
        </p>
        <p className="text-sm text-gray-700 mb-4">
          Deactivate <strong>{user.full_name}</strong>?
        </p>
        {error ? <div className="users-error">{error}</div> : null}
        <div className="modal-actions">
          <Button type="button" variant="outline" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button type="button" className="bg-red-600 hover:bg-red-700" onClick={confirmDelete} disabled={loading}>
            {loading ? 'Deactivating...' : 'Deactivate'}
          </Button>
        </div>
      </div>
    </div>
  )
}
