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
  DragStartEvent,
  DragOverlay,
  closestCenter
} from '@dnd-kit/core'
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

  // Load board data when component mounts or project changes
  // Why useEffect: Load data after component mounts
  // Alternative: Load in store initialization (could cause premature API calls)
  React.useEffect(() => {
    if (currentProject) {
      refreshKanbanBoard()
    }
  }, [currentProject, refreshKanbanBoard])

  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event
    const data = active.data.current as { type: string; issue: Issue }

    if (data?.type === 'issue') {
      setDragOverlay(data.issue)
      console.log('Started dragging issue:', data.issue.key)
    }
  }

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event

    setDragOverlay(null)

    if (!active || !over) return

    const activeData = active.data.current as { type: string; issue: Issue }
    const overData = over.data.current as { type: string; status: string; issue: Issue }

    if (activeData?.type !== 'issue') return

    // Only allow drops on column containers, not on individual issues
    if (overData?.type !== 'column') return

    const draggedIssue = activeData.issue
    const targetColumn = overData?.status

    if (!targetColumn) return

    const currentStatus = draggedIssue.status
    if (currentStatus === targetColumn) return // No change

    console.log(`Moving ${draggedIssue.key} from ${currentStatus} to ${targetColumn}`)

      console.log(`✅ Executing move: ${draggedIssue.key} from ${currentStatus} → ${targetColumn}`)

      // Perform the move via API
      const success = await moveIssue(draggedIssue.id, targetColumn)

      if (success) {
        // Refresh board to reflect the move
        await refreshKanbanBoard()
        console.log('✅ Issue moved successfully')
      } else {
        console.error('❌ Failed to move issue')
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

      <div className="border border-gray-300 rounded-lg p-4 bg-gray-50">
        <DndContext
          collisionDetection={closestCenter}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
        <div         style={{
          display: 'flex',
          flexDirection: 'row',
          gap: '12px',
          overflowX: 'auto',
          paddingBottom: '16px',
          width: 'max-content',
          minWidth: '100%'
        }}>
          {Object.entries(kanbanBoard).map(([status, issues], index) => {
            const columnTitle = COLUMN_TITLES[status as keyof typeof COLUMN_TITLES] || status
            const columnStatus = status as keyof typeof COLUMN_TITLES

            return (
              <React.Fragment key={status}>
                <div style={{ flexShrink: 0, width: '280px' }}>
                  <KanbanColumn
                    title={columnTitle}
                    status={columnStatus}
                    issues={issues}
                    isLoading={false}
                  />
                </div>
                {index < Object.keys(kanbanBoard).length - 1 && (
                  <div className="flex-shrink-0 w-1 bg-gray-300 rounded-full"></div>
                )}
              </React.Fragment>
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
    </div>
  )
}
