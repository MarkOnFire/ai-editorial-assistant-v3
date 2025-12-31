import { useEffect, useState, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import ConfirmDialog from '../components/ui/ConfirmDialog'
import { useToast } from '../components/ui/Toast'
import { SkeletonQueue } from '../components/ui/Skeleton'
import { useDebounce } from '../hooks/useDebounce'

interface Job {
  id: number
  project_name: string
  transcript_file: string
  status: string
  priority: number
  queued_at: string
  current_phase: string | null
}

interface PaginatedResponse {
  jobs: Job[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

interface QueueStats {
  pending: number
  in_progress: number
  completed: number
  failed: number
  cancelled: number
  paused: number
  total: number
}

export default function Queue() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [jobs, setJobs] = useState<Job[]>([])
  const [filter, setFilter] = useState<string>('all')
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<QueueStats | null>(null)

  // Pagination and search state
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [total, setTotal] = useState(0)
  const [searchInput, setSearchInput] = useState(searchParams.get('search') || '')
  const debouncedSearch = useDebounce(searchInput, 300)
  const PAGE_SIZE = 50

  // Dialog state
  const [confirmDialog, setConfirmDialog] = useState<{
    isOpen: boolean
    title: string
    message: string
    onConfirm: () => void
    variant?: 'danger' | 'warning' | 'info'
  }>({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: () => {},
  })

  const { toast } = useToast()

  const handlePrioritize = async (jobId: number) => {
    try {
      // Find max priority and set this job higher
      const maxPriority = Math.max(...jobs.map(j => j.priority), 0)
      await fetch(`/api/jobs/${jobId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ priority: maxPriority + 10 })
      })
      fetchJobs() // Refresh
    } catch (err) {
      console.error('Failed to prioritize job:', err)
    }
  }

  const handleCancel = (jobId: number) => {
    setConfirmDialog({
      isOpen: true,
      title: 'Cancel Job',
      message: 'Are you sure you want to cancel this job? This action cannot be undone.',
      variant: 'danger',
      onConfirm: async () => {
        try {
          const response = await fetch(`/api/jobs/${jobId}/cancel`, { method: 'POST' })
          if (response.ok) {
            toast('Job cancelled successfully', 'success')
            fetchJobs()
          } else {
            toast('Failed to cancel job', 'error')
          }
        } catch (err) {
          console.error('Failed to cancel job:', err)
          toast('Failed to cancel job', 'error')
        }
        setConfirmDialog({ ...confirmDialog, isOpen: false })
      },
    })
  }

  const handleClearJobs = (statuses: string[]) => {
    const statusLabels = statuses.join(' and ')

    setConfirmDialog({
      isOpen: true,
      title: 'Delete Jobs',
      message: `Are you sure you want to delete all ${statusLabels} jobs? This cannot be undone.`,
      variant: 'danger',
      onConfirm: async () => {
        try {
          const params = new URLSearchParams()
          statuses.forEach(s => params.append('statuses', s))

          const response = await fetch(`/api/queue/bulk?${params}`, { method: 'DELETE' })
          if (response.ok) {
            const result = await response.json()
            toast(result.message, 'success')
            fetchJobs()
          } else {
            toast('Failed to delete jobs', 'error')
          }
        } catch (err) {
          console.error('Failed to clear jobs:', err)
          toast('Failed to delete jobs', 'error')
        }
        setConfirmDialog({ ...confirmDialog, isOpen: false })
      },
    })
  }

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch('/api/queue/stats')
      if (response.ok) {
        const data: QueueStats = await response.json()
        setStats(data)
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err)
    }
  }, [])

  const fetchJobs = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: PAGE_SIZE.toString(),
        sort: 'newest',
      })

      // Only add status filter if not 'all'
      if (filter !== 'all') {
        params.set('status', filter)
      }

      if (debouncedSearch) {
        params.set('search', debouncedSearch)
      }

      const response = await fetch(`/api/queue/?${params}`)
      if (response.ok) {
        const data: PaginatedResponse = await response.json()
        setJobs(data.jobs || [])
        setTotal(data.total)
        setTotalPages(data.total_pages)
      }
    } catch (err) {
      console.error('Failed to fetch jobs:', err)
    } finally {
      setLoading(false)
    }
  }, [filter, page, debouncedSearch])

  useEffect(() => {
    fetchJobs()
    fetchStats()
  }, [fetchJobs, fetchStats])

  // Update URL when search changes
  useEffect(() => {
    const params = new URLSearchParams(searchParams)
    if (debouncedSearch) {
      params.set('search', debouncedSearch)
    } else {
      params.delete('search')
    }
    setSearchParams(params, { replace: true })
  }, [debouncedSearch, setSearchParams, searchParams])

  // Reset to first page when search changes
  useEffect(() => {
    if (debouncedSearch !== searchParams.get('search')) {
      setPage(1)
    }
  }, [debouncedSearch, searchParams])

  const clearSearch = () => {
    setSearchInput('')
    setPage(1)
  }

  const handleFilterChange = (newFilter: string) => {
    setFilter(newFilter)
    setPage(1) // Reset to first page when filter changes
  }

  const statusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
      case 'in_progress':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
      case 'completed':
        return 'bg-green-500/20 text-green-400 border-green-500/30'
      case 'failed':
        return 'bg-red-500/20 text-red-400 border-red-500/30'
      case 'investigating':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30'
      case 'paused':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/30'
      case 'cancelled':
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header with Title, Search, and Count */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Job Queue</h1>
          <span className="text-gray-400 text-sm">
            {total} job{total !== 1 ? 's' : ''}
            {filter !== 'all' && ` (${filter.replace('_', ' ')})`}
            {debouncedSearch && ` matching "${debouncedSearch}"`}
          </span>
        </div>

        {/* Clear Button and Search */}
        <div className="flex items-center gap-4">
          {/* Clear Failed/Cancelled Button */}
          <button
            onClick={() => handleClearJobs(['failed', 'cancelled'])}
            className="px-3 py-1.5 text-sm bg-red-900/50 hover:bg-red-800/50 text-red-300 rounded-md transition-colors"
            title="Delete all failed and cancelled jobs"
          >
            Clear Failed/Cancelled
          </button>

          {/* Instant Search */}
          <div className="relative">
            <label htmlFor="queue-search" className="sr-only">Search jobs by filename</label>
            <input
              id="queue-search"
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search by filename..."
              className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 w-64 pr-8"
              aria-describedby="queue-search-desc"
            />
            {searchInput && (
              <button
                type="button"
                onClick={clearSearch}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                aria-label="Clear search"
              >
                ✕
              </button>
            )}
            <span id="queue-search-desc" className="sr-only">
              Search filters automatically as you type. Results appear after you stop typing for 300ms.
            </span>
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center space-x-1 bg-gray-800 rounded-lg p-1 w-fit">
        {['all', 'pending', 'in_progress', 'completed', 'failed', 'cancelled'].map((status) => {
          const count = stats
            ? status === 'all'
              ? stats.total
              : stats[status as keyof QueueStats]
            : null

          return (
            <button
              key={status}
              onClick={() => handleFilterChange(status)}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors flex items-center space-x-1.5 ${
                filter === status
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <span>{status === 'all' ? 'All' : status.replace('_', ' ')}</span>
              {count !== null && (
                <span
                  className={`px-1.5 py-0.5 text-xs rounded-full ${
                    filter === status
                      ? 'bg-gray-600 text-gray-200'
                      : 'bg-gray-700 text-gray-400'
                  }`}
                >
                  {count}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Jobs Table */}
      {loading ? (
        <SkeletonQueue />
      ) : (
        <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
        {jobs.length === 0 ? (
          <div className="px-4 py-8 text-center text-gray-300">
            No jobs found
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-850 border-b border-gray-700">
              <tr className="text-left text-sm text-gray-300">
                <th className="px-4 py-3 font-medium">ID</th>
                <th className="px-4 py-3 font-medium">Transcript</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Phase</th>
                <th className="px-4 py-3 font-medium">Created</th>
                <th className="px-4 py-3 font-medium">Priority</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {jobs.map((job) => (
                <tr
                  key={job.id}
                  className="hover:bg-gray-750 transition-colors"
                >
                  <td className="px-4 py-3">
                    <Link
                      to={`/jobs/${job.id}`}
                      className="text-blue-400 hover:text-blue-300"
                    >
                      #{job.id}
                    </Link>
                  </td>
                  <td className="px-4 py-3 font-medium text-white">
                    {job.project_name}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${statusColor(
                        job.status
                      )}`}
                    >
                      {job.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-300 text-sm">
                    {job.current_phase || '-'}
                  </td>
                  <td className="px-4 py-3 text-gray-300 text-sm">
                    {new Date(job.queued_at + 'Z').toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-gray-300 text-sm">
                    {job.priority}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center space-x-2">
                      {job.status === 'pending' && (
                        <>
                          <button
                            onClick={() => handlePrioritize(job.id)}
                            className="px-2 py-1 text-xs bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors"
                            title="Move to top of queue"
                          >
                            ↑ Prioritize
                          </button>
                          <button
                            onClick={() => handleCancel(job.id)}
                            className="px-2 py-1 text-xs bg-red-600/50 hover:bg-red-600 text-red-100 rounded transition-colors"
                            title="Cancel job"
                          >
                            Cancel
                          </button>
                        </>
                      )}
                      {job.status === 'in_progress' && (
                        <span className="text-xs text-gray-300">Processing...</span>
                      )}
                      {['completed', 'failed', 'cancelled'].includes(job.status) && (
                        <Link
                          to={`/jobs/${job.id}`}
                          className="text-xs text-gray-300 hover:text-white"
                        >
                          View details
                        </Link>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        </div>
      )}

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center space-x-4 py-4">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-700 transition-colors"
          >
            ← Previous
          </button>
          <span className="text-gray-400">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-700 transition-colors"
          >
            Next →
          </button>
        </div>
      )}

      {/* Confirm Dialog */}
      <ConfirmDialog
        isOpen={confirmDialog.isOpen}
        onConfirm={confirmDialog.onConfirm}
        onCancel={() => setConfirmDialog({ ...confirmDialog, isOpen: false })}
        title={confirmDialog.title}
        message={confirmDialog.message}
        variant={confirmDialog.variant}
        confirmText="Confirm"
        cancelText="Cancel"
      />
    </div>
  )
}
