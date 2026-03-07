// frontend/src/components/issues/IssueCard.tsx
//
// Issue card component for displaying issues in Kanban board and lists.
//
// Educational Notes for Junior Developers:
// - React component composition: Build complex UIs from smaller, reusable pieces.
// - Props validation: TypeScript interfaces ensure correct data flow.
// - Styling patterns: Tailwind CSS with conditional classes for dynamic styling.

import React from 'react'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import type { Issue } from '../../types/api'

interface IssueCardProps {
  issue: Issue
  isDragging?: boolean
  onTitleClick?: (issue: Issue) => void
}

// Priority color mapping for visual indicator
const PRIORITY_COLORS = {
  highest: 'text-red-600 bg-red-100',
  high: 'text-orange-600 bg-orange-100',
  medium: 'text-yellow-600 bg-yellow-100',
  low: 'text-blue-600 bg-blue-100',
  lowest: 'text-gray-600 bg-gray-100'
}

// Issue type icons (simple text for now)
const ISSUE_TYPE_ICONS = {
  epic: '📋',
  story: '📝',
  task: '✅',
  bug: '🐛'
}

export function IssueCard({ issue, isDragging = false, onTitleClick }: IssueCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging: dndDragging
  } = useSortable({
    id: issue.id,
    data: { type: 'issue', issue }
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  const isActualDragging = dndDragging || isDragging

  return (
      <div
        ref={setNodeRef}
        style={style}
        {...attributes}
        draggable={false}
        className={`
        kanban-issue-card bg-white border-2 border-slate-300 rounded-lg p-5 mb-6 shadow-sm hover:shadow-md hover:border-slate-400 transition-all text-xs min-h-[80px] w-full
        ${isActualDragging ? 'opacity-60 shadow-lg scale-[1.01]' : ''}
        cursor-grab hover:cursor-grabbing
      `}
        {...listeners}
        onClick={(e) => {
          // Prevent click when dragging
          if (!isActualDragging) {
            console.log('Open issue detail:', issue.id)
          }
        }}
      >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm">{ISSUE_TYPE_ICONS[issue.issue_type]}</span>
            <span className="issue-pill text-[11px] uppercase tracking-[0.08em]">
              {issue.key}
            </span>
          </div>

          <button
            type="button"
            className="issue-card-title text-base text-slate-700 mb-1 leading-snug text-left hover:text-slate-900 focus:outline-none rounded line-clamp-2 border-0 bg-transparent p-0"
            style={{ background: 'transparent', border: 'none', padding: 0, fontWeight: 800 }}
            data-testid="issue-card-title"
            draggable={false}
            onPointerDown={(event) => {
              event.preventDefault()
              event.stopPropagation()
            }}
            onMouseDown={(event) => event.stopPropagation()}
            onDragStart={(event) => event.preventDefault()}
            onClick={(event) => {
              event.stopPropagation()
              if (!isActualDragging) {
                onTitleClick?.(issue)
              }
            }}
          >
            {issue.title}
          </button>

          {issue.description && (
            <p className="text-xs text-slate-500 mb-2 line-clamp-1">
              {issue.description.length > 50
                ? `${issue.description.substring(0, 50)}...`
                : issue.description
              }
            </p>
          )}

          <div className="flex items-center justify-between">
            <span className={`px-2 py-0.5 text-[10px] rounded-full font-semibold ${PRIORITY_COLORS[issue.priority]}`}>
              {issue.priority.toUpperCase()}
            </span>
            <br />
            <span className="text-xs font-medium text-slate-600">
              {issue.assignee_name || 'Unassigned'}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

// Also export a non-draggable version for lists
export function IssueCardStatic({ issue }: { issue: Issue }) {
  return <IssueCard issue={issue} />
}
