import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

interface HealthStatus {
  status: string
  queue?: {
    pending: number
    in_progress: number
    completed?: number
    failed?: number
  }
  llm?: {
    active_model: string | null
    active_backend: string | null
    active_preset: string | null
    primary_backend: string | null
    configured_preset: string | null
    fallback_model: string | null
  }
  last_run?: {
    total_cost: number
    total_tokens: number
  } | null
}

export default function StatusBar() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const fetchHealth = async () => {
    try {
      const response = await fetch('/api/system/health')
      if (!response.ok) throw new Error('API unavailable')
      const data = await response.json()
      setHealth(data)
      setError(null)
      setLastUpdated(new Date())
    } catch {
      setError('API offline')
      setHealth(null)
    }
  }

  useEffect(() => {
    fetchHealth()
    const interval = setInterval(fetchHealth, 10000) // Poll every 10s
    return () => clearInterval(interval)
  }, [])

  const formatCost = (cost: number) => `$${cost.toFixed(4)}`
  const formatTokens = (tokens: number) => tokens.toLocaleString()

  return (
    <div className="bg-gray-950 border-b border-gray-800 px-4 py-2">
      <div className="max-w-7xl mx-auto flex items-center justify-between text-xs">
        {/* Left: System Status */}
        <div className="flex items-center space-x-4">
          <Link
            to="/system"
            className="flex items-center space-x-2 hover:bg-gray-800 px-2 py-1 rounded transition-colors"
            title="View system status and diagnostics"
          >
            <div
              className={`w-2 h-2 rounded-full ${
                error ? 'bg-red-500 animate-pulse' : 'bg-green-500'
              }`}
            />
            <span className={error ? 'text-red-400' : 'text-gray-300'}>
              {error ? 'Offline' : 'Connected'}
            </span>
            {error && (
              <span className="text-gray-400 text-[10px]">→</span>
            )}
          </Link>

          {/* Queue Stats */}
          {health?.queue && (
            <div className="flex items-center space-x-3 text-gray-300">
              <span>
                <span className="text-yellow-400">
                  {health.queue.pending}
                </span>{' '}
                pending
              </span>
              <span>
                <span className="text-blue-400">
                  {health.queue.in_progress}
                </span>{' '}
                processing
              </span>
            </div>
          )}
        </div>

        {/* Center: Model Configuration */}
        {health?.llm && (
          <div className="flex items-center space-x-2">
            <span className="text-gray-300">Backend:</span>
            <span className="text-cyan-400 font-mono">
              {health.llm.active_backend || health.llm.primary_backend || 'none'}
            </span>
            <span className="text-gray-400">|</span>
            {health.llm.configured_preset ? (
              <>
                <span className="text-gray-300">Preset:</span>
                <span className="text-purple-400 font-mono">
                  {health.llm.configured_preset}
                </span>
              </>
            ) : (
              <>
                <span className="text-gray-300">Model:</span>
                <span className="text-gray-300 font-mono">
                  {health.llm.fallback_model || 'none'}
                </span>
              </>
            )}
            {health.llm.active_model && (
              <>
                <span className="text-gray-400">|</span>
                <span className="text-gray-300">Active:</span>
                <span className="text-emerald-400 font-mono">
                  {health.llm.active_model}
                </span>
              </>
            )}
          </div>
        )}

        {/* Right: Last Run Cost */}
        <div className="flex items-center space-x-4">
          {health?.last_run && (
            <div className="flex items-center space-x-3 text-gray-300">
              <span>
                Last run:{' '}
                <span className="text-green-400">
                  {formatCost(health.last_run.total_cost)}
                </span>
              </span>
              <span>
                <span className="text-gray-300">
                  {formatTokens(health.last_run.total_tokens)}
                </span>{' '}
                tokens
              </span>
            </div>
          )}
          {lastUpdated && (
            <span className="text-gray-400">
              {lastUpdated.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
