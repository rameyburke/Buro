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
    <div ref={setNodeRef} className={`
      flex flex-col h-full min-h-[600px] bg-gray-50 border-2 border-gray-300 rounded-lg relative
      ${isOver ? 'border-blue-500 bg-blue-50 shadow-lg' : 'hover:border-gray-400 hover:bg-gray-100'}
      transition-all duration-300
    `}>
      <div className="flex items-center justify-between p-3 border-b-2 border-gray-400 bg-gray-100 rounded-t-lg">
        <h3 className="font-semibold text-gray-900 text-sm">{title}</h3>
        <div className={`
          px-2 py-1 text-xs font-medium rounded-full bg-white
          ${STATUS_COUNT_COLORS[status as IssueStatus]}
        `}>
          {issues.length}
        </div>
      </div>

      <div className="flex-1 p-2 min-h-[300px]">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-gray-500 text-xs">Loading issues...</div>
          </div>
        ) : issues.length === 0 ? (
          <div className={`
            flex items-center justify-center h-full rounded-lg border-2 border-dashed
            ${isOver ? 'border-blue-400 bg-blue-50 text-blue-600' : 'border-gray-300 bg-gray-25 text-gray-400'}
            transition-colors duration-200
          `}>
            <div className="text-center">
              <div className="text-2xl mb-1">⬇️</div>
              <div className="text-xs font-medium">Drop issues here</div>
            </div>
          </div>
        ) : (
          <div className={`space-y-2 ${isOver ? 'ring-2 ring-blue-400 ring-opacity-50 rounded-lg' : ''}`}>
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
          </div>
        )}
      </div>
    </div>
  )
}
