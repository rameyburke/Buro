// frontend/src/pages/Analytics.tsx
//
// Project analytics dashboard (PM-focused).
//

import React, { useCallback, useState } from 'react'
import useAppStore from '../stores/appStore'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card'
import { useQuery } from '../hooks/useQuery'
import {
  getAnalyticsOverview,
  getAnalyticsBurndown,
  getAnalyticsCycleTime,
  getAnalyticsThroughput,
  getAnalyticsAging,
  getAnalyticsOldest,
  getAnalyticsWorkload
} from '../lib/api'

type RangeLabel = '7d' | '14d' | '30d' | '90d'

const RANGE_OPTIONS: RangeLabel[] = ['7d', '14d', '30d', '90d']

export function AnalyticsPage() {
  const { currentProject } = useAppStore()
  const [range, setRange] = useState<RangeLabel>('30d')

  const fetchOverview = useCallback(() => {
    if (!currentProject) return Promise.resolve(null)
    return getAnalyticsOverview(currentProject.id, range)
  }, [currentProject, range])

  const fetchBurndown = useCallback(() => {
    if (!currentProject) return Promise.resolve(null)
    return getAnalyticsBurndown(currentProject.id, range)
  }, [currentProject, range])

  const fetchCycleTime = useCallback(() => {
    if (!currentProject) return Promise.resolve(null)
    return getAnalyticsCycleTime(currentProject.id, range)
  }, [currentProject, range])

  const fetchThroughput = useCallback(() => {
    if (!currentProject) return Promise.resolve(null)
    return getAnalyticsThroughput(currentProject.id, range)
  }, [currentProject, range])

  const fetchAging = useCallback(() => {
    if (!currentProject) return Promise.resolve(null)
    return getAnalyticsAging(currentProject.id)
  }, [currentProject])

  const fetchOldest = useCallback(() => {
    if (!currentProject) return Promise.resolve(null)
    return getAnalyticsOldest(currentProject.id)
  }, [currentProject])

  const fetchWorkload = useCallback(() => {
    if (!currentProject) return Promise.resolve(null)
    return getAnalyticsWorkload(currentProject.id)
  }, [currentProject])

  const { data: overview, loading: overviewLoading } = useQuery(
    fetchOverview,
    currentProject ? `analytics:overview:${currentProject.id}:${range}` : undefined
  )

  const { data: burndown, loading: burndownLoading } = useQuery(
    fetchBurndown,
    currentProject ? `analytics:burndown:${currentProject.id}:${range}` : undefined
  )

  const { data: cycleTime, loading: cycleTimeLoading } = useQuery(
    fetchCycleTime,
    currentProject ? `analytics:cycle:${currentProject.id}:${range}` : undefined
  )

  const { data: throughput, loading: throughputLoading } = useQuery(
    fetchThroughput,
    currentProject ? `analytics:throughput:${currentProject.id}:${range}` : undefined
  )

  const { data: aging, loading: agingLoading } = useQuery(
    fetchAging,
    currentProject ? `analytics:aging:${currentProject.id}` : undefined
  )

  const { data: oldest, loading: oldestLoading } = useQuery(
    fetchOldest,
    currentProject ? `analytics:oldest:${currentProject.id}` : undefined
  )

  const { data: workload, loading: workloadLoading } = useQuery(
    fetchWorkload,
    currentProject ? `analytics:workload:${currentProject.id}` : undefined
  )

  if (!currentProject) {
    return (
      <div className="analytics-empty">
        <div>
          <h2>Select a Project</h2>
          <p>Choose a project to view analytics and reports.</p>
        </div>
      </div>
    )
  }

  const completionRate = overview?.overview?.completion_rate ?? 0
  const completedInRange = overview?.overview?.completed_in_range ?? 0
  const avgCycleTime = overview?.overview?.avg_cycle_time_hours ?? 0
  const wipCount = overview?.overview?.wip_count ?? 0
  const burndownDelta = overview?.overview?.burndown_delta ?? 0

  const burndownSeries = burndown
    ? [
        {
          label: 'Ideal',
          color: '#3b82f6',
          data: burndown.remaining_ideal
        },
        {
          label: 'Actual',
          color: '#ef4444',
          data: burndown.remaining_actual
        }
      ]
    : []

  const cycleSeries = cycleTime
    ? [
        {
          label: 'Cycle Time (hrs)',
          color: '#10b981',
          data: cycleTime.avg_cycle_time_hours
        }
      ]
    : []

  return (
    <div className="analytics-dashboard">
      <div className="analytics-header">
        <div>
          <h1>Analytics Dashboard</h1>
          <p>Project: {currentProject.key} · {currentProject.name}</p>
        </div>
        <RangePicker range={range} onChange={setRange} />
      </div>

      <div className="analytics-kpis">
        <KpiCard
          title="Completion Rate"
          value={`${completionRate.toFixed(1)}%`}
          subtext={`${completedInRange} done in range`}
          accent="kpi-green"
          loading={overviewLoading}
        />
        <KpiCard
          title="Avg Cycle Time"
          value={`${avgCycleTime.toFixed(1)}h`}
          subtext="In Progress → Done"
          accent="kpi-blue"
          loading={overviewLoading}
        />
        <KpiCard
          title="Work In Progress"
          value={`${wipCount}`}
          subtext="In progress + review"
          accent="kpi-amber"
          loading={overviewLoading}
        />
        <KpiCard
          title="Burndown Delta"
          value={`${burndownDelta > 0 ? '+' : ''}${burndownDelta}`}
          subtext="vs ideal" 
          accent={burndownDelta > 0 ? 'kpi-red' : 'kpi-green'}
          loading={overviewLoading}
        />
      </div>

      <div className="analytics-grid">
        <Card className="analytics-card-span">
          <CardHeader>
            <CardTitle>Burndown vs Ideal</CardTitle>
          </CardHeader>
          <CardContent>
            <LineChart
              series={burndownSeries}
              labels={burndown?.dates ?? []}
              loading={burndownLoading}
              height={200}
            />
          </CardContent>
        </Card>

        <Card className="analytics-card-span">
          <CardHeader>
            <CardTitle>Cycle Time Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <LineChart
              series={cycleSeries}
              labels={cycleTime?.dates ?? []}
              loading={cycleTimeLoading}
              height={200}
            />
          </CardContent>
        </Card>
      </div>

      <div className="analytics-grid">
        <Card>
          <CardHeader>
            <CardTitle>Throughput</CardTitle>
          </CardHeader>
          <CardContent>
            <BarChart
              labels={throughput?.dates ?? []}
              values={throughput?.completed_counts ?? []}
              loading={throughputLoading}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Team Workload</CardTitle>
          </CardHeader>
          <CardContent>
            <WorkloadList
              data={workload?.assignees ?? []}
              loading={workloadLoading}
            />
          </CardContent>
        </Card>
      </div>

      <div className="analytics-grid">
        <Card>
          <CardHeader>
            <CardTitle>Issues by Age</CardTitle>
          </CardHeader>
          <CardContent>
            <AgingTable data={aging?.status_breakdown ?? {}} loading={agingLoading} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Oldest Open Issues</CardTitle>
          </CardHeader>
          <CardContent>
            <OldestIssuesTable data={oldest?.issues ?? []} loading={oldestLoading} />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function RangePicker({ range, onChange }: { range: RangeLabel, onChange: (range: RangeLabel) => void }) {
  return (
    <div className="range-picker">
      {RANGE_OPTIONS.map(option => (
        <button
          key={option}
          className={option === range ? 'range-pill active' : 'range-pill'}
          onClick={() => onChange(option)}
          type="button"
        >
          {option}
        </button>
      ))}
    </div>
  )
}

function KpiCard({
  title,
  value,
  subtext,
  accent,
  loading
}: {
  title: string
  value: string
  subtext: string
  accent: string
  loading: boolean
}) {
  return (
    <Card className={`kpi-card ${accent}`}>
      <CardContent>
        {loading ? (
          <div className="kpi-skeleton" />
        ) : (
          <>
            <div className="kpi-title">{title}</div>
            <div className="kpi-value">{value}</div>
            <div className="kpi-subtext">{subtext}</div>
          </>
        )}
      </CardContent>
    </Card>
  )
}

function LineChart({
  series,
  labels,
  loading,
  height
}: {
  series: { label: string; color: string; data: (number | null)[] }[]
  labels: string[]
  loading: boolean
  height: number
}) {
  if (loading) {
    return <div className="chart-loading">Loading chart...</div>
  }

  if (!series.length || !labels.length) {
    return <div className="chart-empty">No data yet.</div>
  }

  const values = series.flatMap(item => item.data.filter((v): v is number => v !== null))
  const maxValue = Math.max(...values, 1)
  const minValue = Math.min(...values, 0)
  const viewHeight = 100
  const viewWidth = 300
  const padding = 10

  const toPoint = (value: number, index: number, length: number) => {
    const x = padding + (index / Math.max(length - 1, 1)) * (viewWidth - padding * 2)
    const y = viewHeight - padding - ((value - minValue) / Math.max(maxValue - minValue, 1)) * (viewHeight - padding * 2)
    return `${x},${y}`
  }

  return (
    <div className="chart-wrapper" style={{ height }}>
      <svg viewBox={`0 0 ${viewWidth} ${viewHeight}`} preserveAspectRatio="none">
        {series.map(item => (
          <polyline
            key={item.label}
            fill="none"
            stroke={item.color}
            strokeWidth="2"
            points={item.data.map((value, index) => {
              if (value === null) return null
              return toPoint(value, index, labels.length)
            }).filter(Boolean).join(' ')}
          />
        ))}
      </svg>
      <div className="chart-legend">
        {series.map(item => (
          <div key={item.label} className="chart-legend-item">
            <span className="chart-legend-dot" style={{ backgroundColor: item.color }} />
            {item.label}
          </div>
        ))}
      </div>
    </div>
  )
}

function BarChart({
  labels,
  values,
  loading
}: {
  labels: string[]
  values: number[]
  loading: boolean
}) {
  if (loading) {
    return <div className="chart-loading">Loading throughput...</div>
  }

  if (!labels.length) {
    return <div className="chart-empty">No data yet.</div>
  }

  const maxValue = Math.max(...values, 1)

  return (
    <div className="bar-chart">
      {values.map((value, index) => (
        <div key={`${labels[index]}-${index}`} className="bar-item">
          <div className="bar-track">
            <div
              className="bar-fill"
              style={{ width: `${(value / maxValue) * 100}%` }}
            />
          </div>
          <div className="bar-label">
            <span>{labels[index]}</span>
            <strong>{value}</strong>
          </div>
        </div>
      ))}
    </div>
  )
}

function WorkloadList({ data, loading }: { data: any[], loading: boolean }) {
  if (loading) {
    return <div className="chart-loading">Loading workload...</div>
  }

  if (!data.length) {
    return <div className="chart-empty">No workload data yet.</div>
  }

  const maxWip = Math.max(...data.map(item => item.wip_total || 0), 1)

  return (
    <div className="workload-list">
      {data.map(item => (
        <div key={item.user_id || item.user_name} className="workload-row">
          <div>
            <div className="workload-name">{item.user_name}</div>
            <div className="workload-meta">Active: {item.total_active}</div>
          </div>
          <div className="workload-bar">
            <div
              className="workload-bar-fill"
              style={{ width: `${(item.wip_total / maxWip) * 100}%` }}
            />
          </div>
          <div className="workload-wip">WIP {item.wip_total}</div>
        </div>
      ))}
    </div>
  )
}

function AgingTable({ data, loading }: { data: Record<string, any>, loading: boolean }) {
  if (loading) {
    return <div className="chart-loading">Loading aging report...</div>
  }

  const entries = Object.entries(data)
  if (!entries.length) {
    return <div className="chart-empty">No aging data yet.</div>
  }

  return (
    <div className="table-grid">
      <div className="table-row table-header">
        <div>Status</div>
        <div>Count</div>
        <div>Avg Days</div>
        <div>Max Days</div>
      </div>
      {entries.map(([status, stats]) => (
        <div key={status} className="table-row">
          <div className="capitalize">{status.replace('_', ' ')}</div>
          <div>{stats.count}</div>
          <div>{stats.avg_age_days}</div>
          <div>{stats.max_age_days}</div>
        </div>
      ))}
    </div>
  )
}

function OldestIssuesTable({ data, loading }: { data: any[], loading: boolean }) {
  if (loading) {
    return <div className="chart-loading">Loading oldest issues...</div>
  }

  if (!data.length) {
    return <div className="chart-empty">No open issues yet.</div>
  }

  return (
    <div className="table-grid">
      <div className="table-row table-header">
        <div>Issue</div>
        <div>Assignee</div>
        <div>Status</div>
        <div>Age</div>
      </div>
      {data.map(issue => (
        <div key={issue.key} className="table-row">
          <div>{issue.key} · {issue.title}</div>
          <div>{issue.assignee}</div>
          <div className="capitalize">{issue.status.replace('_', ' ')}</div>
          <div>{issue.age_days}d</div>
        </div>
      ))}
    </div>
  )
}
