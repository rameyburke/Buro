// frontend/src/components/board/KanbanColumn.tsx
//
// Kanban column component for drag-and-drop issue workflow.
//
// Educational Notes for Junior Developers:
// - State management: Local component state vs global store synchronization.
// - Drag and drop zones: Droppable areas must handle item transfers correctly.
// - Visual feedback: Loading, empty states, hover effects improve UX.

import React from 'react'
import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import type { Issue, IssueStatus } from '../../types/api'
import { IssueCard } from '../issues/IssueCard'

interface KanbanColumnProps {
  title: string
  status: IssueStatus // Maps to API status enum
  issues: Issue[]
  isLoading?: boolean
}

const STATUS_COLORS: Record<IssueStatus, string> = {
  backlog: 'bg-gray-100 border-gray-300',
  to_do: 'bg-blue-50 border-blue-300',
  in_progress: 'bg-yellow-50 border-yellow-300',
  done: 'bg-green-50 border-green-300'
}

const STATUS_COUNT_COLORS: Record<IssueStatus, string> = {
  backlog: 'bg-gray-200 text-gray-700',
  to_do: 'bg-blue-200 text-blue-700',
  in_progress: 'bg-yellow-200 text-yellow-700',
  done: 'bg-green-200 text-green-700'
}

export function KanbanColumn({ title, status, issues, isLoading }: KanbanColumnProps) {
  const {
    setNodeRef,
    isOver
  } = useDroppable({
    id: status,
    data: { type: 'column', status }
  })

  return (
    <div className={`
      flex flex-col h-full min-h-[600px] bg-white border border-gray-200 rounded-lg
      ${isOver ? 'border-blue-400 shadow-lg' : ''}
      ${STATUS_COLORS[status as IssueStatus]}
    `}>
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <h2 className="font-semibold text-gray-900">{title}</h2>
        <div className={`
          px-2 py-1 text-xs font-medium rounded-full
          ${STATUS_COUNT_COLORS[status as IssueStatus]}
        `}>
          {issues.length}
        </div>
      </div>

      <div
        ref={setNodeRef}
        className="flex-1 p-4 space-y-0 min-h-[300px]"
      >
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-gray-500">Loading issues...</div>
          </div>
        ) : issues.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-gray-400 text-sm">No issues</div>
          </div>
        ) : (
          <SortableContext
            items={issues.map(issue => issue.id)}
            strategy={verticalListSortingStrategy}
          >
            {issues.map((issue) => (
              <IssueCard
                key={issue.id}
                issue={issue}
              />
            ))}
          </SortableContext>
        )}
      </div>
    </div>
  )
}