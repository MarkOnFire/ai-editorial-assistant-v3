import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { SkeletonDashboard } from '../components/ui/Skeleton'

interface QueueStats {
  pending: number
  in_progress: number
  completed: number
  failed: number
}

interface RecentJob {
  id: number
  project_name: string
  transcript_file: string
  status: string
  queued_at: string
  priority: number
}

export default function Home() {
  const [stats, setStats] = useState<QueueStats | null>(null)
  const [recentJobs, setRecentJobs] = useState<RecentJob[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, jobsRes] = await Promise.all([
          fetch('/api/queue/stats'),
          fetch('/api/queue/?page=1&page_size=5&sort=newest'),
        ])

        if (statsRes.ok) {
          setStats(await statsRes.json())
        }
        if (jobsRes.ok) {
          const data = await jobsRes.json()
          // API returns paginated response with jobs array
          setRecentJobs(data.jobs || [])
        }
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const statusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'text-yellow-400'
      case 'in_progress':
        return 'text-blue-400'
      case 'completed':
        return 'text-green-400'
      case 'failed':
        return 'text-red-400'
      case 'investigating':
        return 'text-orange-400'
      default:
        return 'text-gray-400'
    }
  }

  if (loading) {
    return <SkeletonDashboard />
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Dashboard</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          label="Pending"
          value={stats?.pending ?? 0}
          color="text-yellow-400"
        />
        <StatCard
          label="Processing"
          value={stats?.in_progress ?? 0}
          color="text-blue-400"
        />
        <StatCard
          label="Completed"
          value={stats?.completed ?? 0}
          color="text-green-400"
        />
        <StatCard
          label="Failed"
          value={stats?.failed ?? 0}
          color="text-red-400"
        />
      </div>

      {/* Recent Jobs */}
      <div className="bg-gray-800 rounded-lg border border-gray-700">
        <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
          <h2 className="text-lg font-medium text-white">Recent Jobs</h2>
          <Link
            to="/queue"
            className="text-sm text-blue-400 hover:text-blue-300"
          >
            View all
          </Link>
        </div>
        <div className="divide-y divide-gray-700">
          {recentJobs.length === 0 ? (
            <div className="px-4 py-8 text-center text-gray-300">
              No jobs in queue
            </div>
          ) : (
            recentJobs.map((job) => (
              <Link
                key={job.id}
                to={`/jobs/${job.id}`}
                className="block px-4 py-3 hover:bg-gray-750 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-white font-medium">
                      {job.project_name}
                    </div>
                    <div className="text-sm text-gray-400">
                      {new Date(job.queued_at + 'Z').toLocaleString()}
                    </div>
                  </div>
                  <span className={`text-sm font-medium ${statusColor(job.status)}`}>
                    {job.status}
                  </span>
                </div>
              </Link>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string
  value: number
  color: string
}) {
  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
      <div className="text-sm text-gray-300">{label}</div>
      <div className={`text-3xl font-bold ${color}`}>{value}</div>
    </div>
  )
}
