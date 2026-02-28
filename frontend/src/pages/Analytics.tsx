// frontend/src/pages/Analytics.tsx
//
// Analytics dashboard page with charts and reports.
//
// Educational Notes for Junior Developers:
// - Dashboard organization: Separate data fetching from visualization.
// - Chart integration: Choose appropriate libraries (Chart.js for simplicity).
// - Loading states: Handle async data and error conditions.
// - Responsive design: Charts should work on mobile devices.

import React from 'react'
import useAppStore from '../stores/appStore'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card'
import { useQuery } from '../hooks/useQuery'

export function AnalyticsPage() {
  const { currentProject } = useAppStore()

  // Fetch analytics data using custom query hook
  // Why custom hook: Reusable data fetching with loading/error states
  const { data: overview, loading: overviewLoading } =
    useQuery(getProjectOverview)

  const { data: burndown, loading: burndownLoading } =
    useQuery(getBurndownData)

  const { data: workload, loading: workloadLoading } =
    useQuery(getWorkloadData)

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Select a Project
          </h2>
          <p className="text-gray-600">
            Choose a project to view analytics and reports.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">
          Analytics Dashboard
        </h1>
        <div className="text-sm text-gray-500">
          Project: {currentProject.key} - {currentProject.name}
        </div>
      </div>

      {/* Overview Cards */}
      {overviewLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Loading skeleton */}
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="pt-6">
                <div className="h-16 bg-gray-200 rounded mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : overview ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Total Issues
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">
                {overview.overview.total_issues}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Completed
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {overview.issues.done || 0}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                In Progress
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">
                {overview.issues.in_progress || 0}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Completion Rate
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {overview.overview.completion_rate.toFixed(1)}%
              </div>
            </CardContent>
          </Card>
        </div>
      ) : null}

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Burndown Chart Placeholder */}
        <Card>
          <CardHeader>
            <CardTitle>Burndown Chart</CardTitle>
          </CardHeader>
          <CardContent>
            <BurndownChart
              data={burndown}
              loading={burndownLoading}
            />
          </CardContent>
        </Card>

        {/* Velocity Chart Placeholder */}
        <Card>
          <CardHeader>
            <CardTitle>Team Velocity</CardTitle>
          </CardHeader>
          <CardContent>
            <VelocityChart
              data={overview}
              loading={overviewLoading}
            />
          </CardContent>
        </Card>
      </div>

      {/* Issues Aging Table */}
      <Card>
        <CardHeader>
          <CardTitle>Issues by Age</CardTitle>
          <p className="text-sm text-gray-600">
            Identifies issues that may be stuck or need attention
          </p>
        </CardHeader>
        <CardContent>
          <AgingIssuesTable
            projectId={currentProject.id}
          />
        </CardContent>
      </Card>

      {/* Workload Distribution */}
      {workload && (
        <Card>
          <CardHeader>
            <CardTitle>Team Workload Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <WorkloadChart
              data={workload}
              loading={workloadLoading}
            />
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// Placeholder components - would be implemented with Chart.js or similar
function BurndownChart({ data, loading }: { data: any, loading: boolean }) {
  return (
    <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
      {loading ? (
        <div className="text-gray-500">Loading burndown chart...</div>
      ) : (
        <div className="text-center text-gray-500">
          <div className="text-lg mb-2">📊</div>
          <div>Burndown Chart</div>
          <div className="text-sm mt-1">Implementation planned for full release</div>
        </div>
      )}
    </div>
  )
}

function VelocityChart({ data, loading }: { data: any, loading: boolean }) {
  if (loading || !data) {
    return (
      <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
        <div className="text-gray-500">Loading velocity data...</div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <span className="text-sm font-medium">Completed Issues (30 days)</span>
        <span className="text-lg font-bold">{data.overview.total_issues}</span>
      </div>
      <div className="flex justify-between items-center">
        <span className="text-sm font-medium">Daily Average</span>
        <span className="text-lg font-bold">{data.velocity?.daily_average || 0}</span>
      </div>
    </div>
  )
}

function WorkloadChart({ data, loading }: { data: any, loading: boolean }) {
  if (loading || !data?.workload_distribution) {
    return <div className="text-gray-500">Loading workload data...</div>
  }

  return (
    <div className="space-y-3">
      {data.workload_distribution.slice(0, 5).map((user: any) => (
        <div key={user.user_id} className="flex justify-between items-center">
          <div>
            <div className="font-medium">{user.user_name}</div>
            <div className="text-sm text-gray-500">
              {user.total_issues} issues, Score: {user.workload_score}
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-600">Active Issues</div>
            <div className="font-bold">{user.total_issues}</div>
          </div>
        </div>
      ))}
    </div>
  )
}

function AgingIssuesTable({ projectId }: { projectId: string }) {
  // Placeholder - would fetch and display aging issues
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-4 font-medium text-sm text-gray-600 border-b pb-2">
        <div>Status</div>
        <div>Issue Count</div>
        <div>Average Days</div>
        <div>Max Days</div>
      </div>

      {/* Placeholder data */}
      <div className="grid grid-cols-4 gap-4 py-2 border-b text-sm">
        <div className="flex items-center">
          <div className="w-2 h-2 bg-yellow-400 rounded-full mr-2"></div>
          In Progress
        </div>
        <div>3</div>
        <div>5.2 days</div>
        <div>8 days</div>
      </div>

      <div className="grid grid-cols-4 gap-4 py-2 border-b text-sm">
        <div className="flex items-center">
          <div className="w-2 h-2 bg-blue-400 rounded-full mr-2"></div>
          To Do
        </div>
        <div>5</div>
        <div>12.8 days</div>
        <div>25 days</div>
      </div>
    </div>
  )
}

// API functions
async function getProjectOverview() {
  const { currentProject } = useAppStore.getState()
  if (!currentProject) return null

  const response = await fetch(`/api/analytics/projects/${currentProject.id}/overview`)
  if (!response.ok) throw new Error('Failed to fetch overview')
  return response.json()
}

async function getBurndownData() {
  const { currentProject } = useAppStore.getState()
  if (!currentProject) return null

  const response = await fetch(`/api/analytics/projects/${currentProject.id}/burndown`)
  if (!response.ok) throw new Error('Failed to fetch burndown')
  return response.json()
}

async function getWorkloadData() {
  const response = await fetch('/api/analytics/issues/workload')
  if (!response.ok) throw new Error('Failed to fetch workload')
  return response.json()
}
