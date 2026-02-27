import React, { useEffect, useRef, useState } from 'react'
import useAppStore from '../../stores/appStore'
import type { Project } from '../../types/api'

export function ProjectSelector() {
  const { projects, currentProject, setCurrentProject, isLoading } = useAppStore()
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (!dropdownRef.current) {
        return
      }
      if (!dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
    }

    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen])

  const handleSelectProject = (project: Project) => {
    setCurrentProject(project)
    setIsOpen(false)
  }

  const hasProjects = projects.length > 0
  const label = currentProject ? `${currentProject.key} · ${currentProject.name}` : 'Select Project'

  return (
    <div className="project-selector" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => (hasProjects ? setIsOpen((prev) => !prev) : undefined)}
        className={`project-trigger${!hasProjects ? ' disabled' : ''}`}
        disabled={!hasProjects}
      >
        <span className="project-icon" aria-hidden>
          <svg viewBox="0 0 24 24" stroke="currentColor" fill="none">
            <path
              d="M3 8h18M5 5h6l2 2h8v12H3z"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>
        <span className="project-label">{label}</span>
        <span className={`project-caret${isOpen ? ' open' : ''}`} aria-hidden>
          <svg viewBox="0 0 20 20" fill="currentColor">
            <path d="M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 011.08 1.04l-4.25 4.25a.75.75 0 01-1.08 0L5.21 8.27a.75.75 0 01.02-1.06z" />
          </svg>
        </span>
      </button>

      {isOpen && hasProjects && (
        <div className="project-menu" role="listbox">
          {projects.map((project) => {
            const active = currentProject?.id === project.id
            return (
              <button
                key={project.id}
                type="button"
                role="option"
                aria-selected={active}
                className={`project-option${active ? ' active' : ''}`}
                onClick={() => handleSelectProject(project)}
              >
                <span className="project-key">{project.key}</span>
                <span className="project-name">{project.name}</span>
                {active && (
                  <span className="project-check" aria-hidden>
                    <svg viewBox="0 0 20 20" fill="currentColor">
                      <path
                        fillRule="evenodd"
                        d="M16.704 5.288a1 1 0 010 1.415l-7.11 7.11a1 1 0 01-1.415 0L3.295 9.92a1 1 0 011.414-1.415l3.057 3.057 6.403-6.403a1 1 0 011.534.129z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </span>
                )}
              </button>
            )
          })}
        </div>
      )}

      {!hasProjects && !isLoading && isOpen && (
        <div className="project-menu empty" aria-live="polite">
          <p>No projects yet</p>
        </div>
      )}
    </div>
  )
}
