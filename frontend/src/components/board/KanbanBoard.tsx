// frontend/src/components/board/KanbanBoard.tsx
//
// Main Kanban board component with drag-and-drop functionality.
//
// Educational Notes for Junior Developers:
// - DndContext: Manages drag and drop state across components hierarchically.
// - Drag handlers: Different handlers for different drag scenarios.
// - Visual feedback: Real-time updates maintain user understanding.
// - Collision detection: Prevent moves that violate business rules.

import React from 'react'
import {
  DndContext,
  DragEndEvent,
  DragOverEvent,
  DragStartEvent,
  DragOverlay,
  pointerWithin,
  closestCenter
} from '@dnd-kit/core'
import { arrayMove } from '@dnd-kit/sortable'
import { KanbanColumn } from './KanbanColumn'
import { IssueCard } from '../issues/IssueCard'
import useAppStore from '../../stores/appStore'
import type { Issue } from '../../types/api'

const COLUMN_TITLES = {
  backlog: 'Backlog',
  to_do: 'To Do',
  in_progress: 'In Progress',
  done: 'Done'
} as const

export function KanbanBoard() {
  const {
    kanbanBoard,
    currentProject,
    isLoading,
    moveIssue,
    refreshKanbanBoard
  } = useAppStore()

  const [dragOverlay, setDragOverlay] = React.useState<Issue | null>(null)
  const [dragColumnId, setDragColumnId] = React.useState<string | null>(null)

  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event
    const data = active.data.current as { type: string; issue: Issue }

    if (data?.type === 'issue') {
      setDragOverlay(data.issue)
      console.log('Started dragging issue:', data.issue.key)
    }
  }

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event

    if (!active || !over) return

    const activeData = active.data.current as { type: string; issue: Issue }
    const overData = over.data.current as { type: string; status: string; issue: Issue }

    // Track which column we're dragging over
    if (overData?.type === 'column') {
      setDragColumnId(overData.status)
    }
  }

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event

    setDragOverlay(null)
    setDragColumnId(null)

    if (!active || !over) return

    const activeData = active.data.current as { type: string; issue: Issue }
    const overData = over.data.current as { type: string; status: string; issue: Issue }

    if (activeData?.type !== 'issue') return

    const draggedIssue = activeData.issue
    const targetColumn = overData?.status

    if (!targetColumn) return

    const currentStatus = draggedIssue.status
    if (currentStatus === targetColumn) return // No change

    // Validate move (could add business rule validation here)
    console.log(`Moving ${draggedIssue.key} from ${currentStatus} to ${targetColumn}`)

    // Perform the move via API
    const success = await moveIssue(draggedIssue.id, targetColumn)

    if (success) {
      // Refresh board to show updated state
      await refreshKanbanBoard()
      console.log('Issue moved successfully')
    } else {
      console.error('Failed to move issue')
      // Could show toast notification here
    }
  }

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Select a project to view the board</div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading board...</div>
      </div>
    )
  }

  return (
    <div className="h-full">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{currentProject.name} Board</h1>
        <p className="text-gray-600">Track and manage your team's work</p>
      </div>

      <DndContext
        collisionDetection={pointerWithin} // Accurate pointer-based collision detection
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 h-full">
          {Object.entries(kanbanBoard).map(([status, issues]) => {
            const columnTitle = COLUMN_TITLES[status as keyof typeof COLUMN_TITLES] || status
            const columnStatus = status as keyof typeof COLUMN_TITLES

            return (
              <KanbanColumn
                key={status}
                title={columnTitle}
                status={columnStatus}
                issues={issues}
                isLoading={false}
              />
            )
          })}
        </div>

        {/* Drag overlay for visual feedback */}
        <DragOverlay>
          {dragOverlay ? (
            <IssueCard
              issue={dragOverlay}
              isDragging
            />
          ) : null}
        </DragOverlay>
      </DndContext>
    </div>
  )
}