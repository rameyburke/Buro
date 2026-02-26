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

export function IssueCard({ issue, isDragging = false }: IssueCardProps) {
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
       className={`
        bg-white border-2 border-gray-300 rounded-lg p-2 mb-3 shadow-md hover:shadow-lg hover:border-blue-300 transition-all text-xs min-h-[60px] w-full
        ${isActualDragging ? 'opacity-50 shadow-xl rotate-1 scale-105' : ''}
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
          <div className="flex items-center gap-1 mb-1">
            <span className="text-sm">{ISSUE_TYPE_ICONS[issue.issue_type]}</span>
            <span className="text-xs text-gray-500">{issue.key}</span>
          </div>

          <h3 className="font-medium text-xs text-gray-900 mb-1 leading-tight">
            {issue.title}
          </h3>

          {issue.description && (
            <p className="text-xs text-gray-600 mb-1 line-clamp-1">
              {issue.description.length > 50
                ? `${issue.description.substring(0, 50)}...`
                : issue.description
              }
            </p>
          )}

          <div className="flex items-center justify-between">
            <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${PRIORITY_COLORS[issue.priority]}`}>
              {issue.priority.toUpperCase()}
            </span>

            {issue.assignee_id && (
              <div className="flex items-center">
                <div className="w-5 h-5 bg-blue-500 text-white rounded-full text-xs flex items-center justify-center">
                  {/* Placeholder avatar - could show user's initial */}
                  A
                </div>
              </div>
            )}
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