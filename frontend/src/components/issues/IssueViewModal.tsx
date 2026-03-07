import React from 'react'
import { Button } from '../ui/button'
import type { Issue } from '../../types/api'

type IssueViewModalProps = {
  issue: Issue
  onClose: () => void
  onEdit?: (issue: Issue) => void
}

export function IssueViewModal({ issue, onClose, onEdit }: IssueViewModalProps) {
  const assigneeLabel = issue.assignee_name || issue.assignee_id || 'Unassigned'
  const reporterLabel = issue.reporter_name || issue.reporter_id || 'Unknown'
  const updatedLabel = new Date(issue.updated_at).toLocaleString()

  return (
    <div className="modal-overlay">
      <div className="modal-card view-issue-modal">
        <h2 className="modal-title view-issue-heading">Issue Details</h2>
        <div className="view-issue-header">
          <div>
            <div className="view-issue-label">Overview</div>
            <div className="view-issue-title">{issue.title}</div>
          </div>
          <span className="issue-pill">{issue.key}</span>
        </div>

        <div className="view-issue-section">
          <div className="view-issue-row">
            <div className="view-issue-label">Description</div>
            <div className="view-issue-value">{issue.description || 'No description'}</div>
          </div>
        </div>

        <div className="view-issue-grid">
          <div className="view-issue-row">
            <div className="view-issue-label">Type</div>
            <div className="view-issue-value capitalize">{issue.issue_type}</div>
          </div>
          <div className="view-issue-row">
            <div className="view-issue-label">Priority</div>
            <div className="view-issue-value capitalize">{issue.priority}</div>
          </div>
          <div className="view-issue-row">
            <div className="view-issue-label">Status</div>
            <div className="view-issue-value capitalize">
              {issue.status.replace('_', ' ')}
            </div>
          </div>
          <div className="view-issue-row">
            <div className="view-issue-label">Updated</div>
            <div className="view-issue-value">{updatedLabel}</div>
          </div>
          <div className="view-issue-row">
            <div className="view-issue-label">Assignee</div>
            <div className="view-issue-value">{assigneeLabel}</div>
          </div>
          <div className="view-issue-row">
            <div className="view-issue-label">Reporter</div>
            <div className="view-issue-value">{reporterLabel}</div>
          </div>
        </div>

        <div className="modal-actions">
          <Button variant="outline" type="button" onClick={onClose}>
            Close
          </Button>
          {onEdit ? (
            <Button type="button" onClick={() => onEdit(issue)}>
              Edit
            </Button>
          ) : null}
        </div>
      </div>
    </div>
  )
}
