import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { useFocusTrap } from '../hooks/useFocusTrap'
import Breadcrumb from '../components/ui/Breadcrumb'
import { useToast } from '../components/ui/Toast'
import { Skeleton, SkeletonCard } from '../components/ui/Skeleton'

interface JobPhase {
  name: string
  status: string
  cost?: number
  tokens?: number
  started_at?: string
  completed_at?: string
  model?: string
  tier?: number
  tier_label?: string
  tier_reason?: string
  attempts?: number
}

interface JobOutputs {
  analysis?: string
  formatted_transcript?: string
  seo_metadata?: string
  copy_edited?: string
}

interface JobDetail {
  id: number
  project_name: string
  transcript_file?: string
  status: string
  priority: number
  queued_at: string
  started_at?: string
  completed_at?: string
  current_phase?: string
  last_heartbeat?: string
  retry_count: number
  max_retries: number
  phases?: JobPhase[]
  actual_cost?: number
  total_tokens?: number
  error_message?: string
  outputs?: JobOutputs
  airtable_record_id?: string
  airtable_url?: string
  media_id?: string
}

// Map output keys to their display names and filenames
const OUTPUT_FILES: Record<string, { label: string; filename: string }> = {
  analysis: { label: 'Analysis', filename: 'analyst_output.md' },
  formatted_transcript: { label: 'Formatted Transcript', filename: 'formatter_output.md' },
  seo_metadata: { label: 'SEO Metadata', filename: 'seo_output.md' },
  qa_review: { label: 'QA Review', filename: 'manager_output.md' },
  copy_edited: { label: 'Copy Edited', filename: 'copy_editor_output.md' },
  recovery_analysis: { label: 'Recovery Analysis', filename: 'recovery_analysis.md' },
}

export default function JobDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [job, setJob] = useState<JobDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [viewingOutput, setViewingOutput] = useState<{
    label: string
    content: string
    isJson: boolean
  } | null>(null)
  const [loadingOutput, setLoadingOutput] = useState(false)
  const triggerRef = useRef<HTMLButtonElement | null>(null)
  const modalRef = useFocusTrap(!!viewingOutput)
  const { toast } = useToast()

  useEffect(() => {
    const fetchJob = async () => {
      try {
        const response = await fetch(`/api/jobs/${id}`)
        if (!response.ok) {
          throw new Error('Job not found')
        }
        setJob(await response.json())
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load job')
      } finally {
        setLoading(false)
      }
    }

    fetchJob()

    // Auto-refresh while job is in progress
    const interval = setInterval(() => {
      if (job?.status === 'in_progress' || job?.status === 'pending') {
        fetchJob()
      }
    }, 3000)

    return () => clearInterval(interval)
  }, [id, job?.status])

  const handleAction = async (action: string) => {
    const actionLabels: Record<string, { success: string; error: string }> = {
      pause: { success: 'Job paused successfully', error: 'Failed to pause job' },
      resume: { success: 'Job resumed successfully', error: 'Failed to resume job' },
      retry: { success: 'Job retry initiated', error: 'Failed to retry job' },
      cancel: { success: 'Job cancelled successfully', error: 'Failed to cancel job' },
    }

    try {
      const response = await fetch(`/api/jobs/${id}/${action}`, {
        method: 'POST',
      })
      if (response.ok) {
        toast(actionLabels[action]?.success || `Job ${action}ed successfully`, 'success')
        // Refresh job data
        const updated = await fetch(`/api/jobs/${id}`)
        if (updated.ok) {
          setJob(await updated.json())
        }
      } else {
        toast(actionLabels[action]?.error || `Failed to ${action} job`, 'error')
      }
    } catch (err) {
      console.error(`Failed to ${action} job:`, err)
      toast(actionLabels[action]?.error || `Failed to ${action} job`, 'error')
    }
  }

  const handleViewOutput = async (key: string, filename: string, event: React.MouseEvent<HTMLButtonElement>) => {
    // Save reference to trigger button
    triggerRef.current = event.currentTarget

    setLoadingOutput(true)
    try {
      const response = await fetch(`/api/jobs/${id}/outputs/${filename}`)
      if (!response.ok) {
        throw new Error('Failed to load output')
      }
      const content = await response.text()
      const fileInfo = OUTPUT_FILES[key]
      setViewingOutput({
        label: fileInfo?.label || filename,
        content,
        isJson: filename.endsWith('.json'),
      })
    } catch (err) {
      console.error('Failed to load output:', err)
    } finally {
      setLoadingOutput(false)
    }
  }

  const closeModal = () => {
    setViewingOutput(null)
    // Return focus to trigger button
    setTimeout(() => {
      triggerRef.current?.focus()
    }, 0)
  }

  // Handle Escape key to close modal
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && viewingOutput) {
        closeModal()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [viewingOutput])

  const phaseStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <span className="text-green-400">&#10003;</span>
      case 'in_progress':
        return <span className="text-blue-400 animate-pulse">&#9679;</span>
      case 'failed':
        return <span className="text-red-400">&#10007;</span>
      case 'skipped':
        return <span className="text-gray-400">&#8212;</span>
      default:
        return <span className="text-gray-400">&#9675;</span>
    }
  }

  if (loading) {
    return (
      <div className="space-y-6" aria-label="Loading job details" role="status">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
          <Skeleton className="h-6 w-48 mb-4" />
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i}>
                <Skeleton className="h-5 w-full" />
              </div>
            ))}
          </div>
        </div>
        <span className="sr-only">Loading job details...</span>
      </div>
    )
  }

  if (error || !job) {
    return (
      <div className="text-center py-12">
        <div role="alert" aria-live="assertive" className="text-red-400 mb-4">{error || 'Job not found'}</div>
        <button
          onClick={() => navigate(-1)}
          className="text-blue-400 hover:text-blue-300"
        >
          Go back
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <Breadcrumb
        items={[
          { label: 'Home', href: '/' },
          { label: 'Queue', href: '/queue' },
          { label: `Job #${job.id}` },
        ]}
      />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => navigate(-1)}
            className="text-sm text-gray-400 hover:text-white mb-2 inline-block transition-colors"
            aria-label="Go back to previous page"
          >
            &#8592; Back
          </button>
          <h1 className="text-2xl font-bold text-white">
            {job.project_name}
          </h1>
          <p className="text-gray-400">
            Job #{job.id}
            {job.current_phase && job.status === 'in_progress' && (
              <span className="ml-2 text-blue-400 animate-pulse">
                • Processing {job.current_phase}...
              </span>
            )}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2">
          {job.status === 'in_progress' && (
            <button
              onClick={() => handleAction('pause')}
              className="px-3 py-1.5 bg-orange-600 hover:bg-orange-500 text-white rounded-md text-sm"
            >
              Pause
            </button>
          )}
          {job.status === 'paused' && (
            <button
              onClick={() => handleAction('resume')}
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-md text-sm"
            >
              Resume
            </button>
          )}
          {job.status === 'failed' && (
            <button
              onClick={() => handleAction('retry')}
              className="px-3 py-1.5 bg-green-600 hover:bg-green-500 text-white rounded-md text-sm"
            >
              Retry
            </button>
          )}
          {['pending', 'paused'].includes(job.status) && (
            <button
              onClick={() => handleAction('cancel')}
              className="px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white rounded-md text-sm"
            >
              Cancel
            </button>
          )}
        </div>
      </div>

      {/* SST Record & Media ID */}
      {(job.airtable_url || job.media_id) && (
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {job.airtable_url && (
              <div>
                <div className="text-xs text-gray-400 uppercase tracking-wide mb-2">
                  SST Record
                </div>
                <a
                  href={job.airtable_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-blue-400 hover:text-blue-300 transition-colors"
                >
                  <span>View in Airtable</span>
                  <svg
                    className="ml-1.5 w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                    />
                  </svg>
                </a>
                {job.airtable_record_id && (
                  <div className="text-xs text-gray-500 mt-1 font-mono">
                    {job.airtable_record_id}
                  </div>
                )}
              </div>
            )}
            {job.media_id && (
              <div>
                <div className="text-xs text-gray-400 uppercase tracking-wide mb-2">
                  Media ID
                </div>
                <div className="text-white font-mono">{job.media_id}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Progress Bar for in_progress jobs */}
      {job.status === 'in_progress' && job.phases && (
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">Processing Progress</span>
            <span className="text-sm text-white">
              {job.phases.filter(p => p.status === 'completed').length} / {job.phases.length} phases
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2.5">
            <div
              className="bg-blue-500 h-2.5 rounded-full transition-all duration-500"
              style={{
                width: `${(job.phases.filter(p => p.status === 'completed').length / job.phases.length) * 100}%`
              }}
            />
          </div>
        </div>
      )}

      {/* Info Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <InfoCard label="Status" value={job.status} />
        <InfoCard label="Priority" value={String(job.priority)} />
        <InfoCard
          label="Cost"
          value={job.actual_cost ? `$${job.actual_cost.toFixed(4)}` : '-'}
        />
        <InfoCard
          label="Tokens"
          value={job.phases?.reduce((sum, p) => sum + (p.tokens || 0), 0).toLocaleString() ?? '-'}
        />
      </div>

      {/* Phases */}
      {job.phases && job.phases.length > 0 && (
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
          <h2 className="text-lg font-medium text-white mb-4">
            Processing Phases
          </h2>
          <div className="space-y-3">
            {job.phases.map((phase, idx) => (
              <div
                key={idx}
                className="py-3 border-b border-gray-700 last:border-0"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {phaseStatusIcon(phase.status)}
                    <span className="text-white">{phase.name}</span>
                    {phase.tier_label && (
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        phase.tier === 2 ? 'bg-purple-900/50 text-purple-300' :
                        phase.tier === 1 ? 'bg-blue-900/50 text-blue-300' :
                        'bg-green-900/50 text-green-300'
                      }`}>
                        {phase.tier_label}
                      </span>
                    )}
                    {phase.attempts && phase.attempts > 1 && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-orange-900/50 text-orange-300">
                        {phase.attempts} attempts
                      </span>
                    )}
                  </div>
                  <div className="flex items-center space-x-4 text-sm text-gray-400">
                    {phase.cost !== undefined && (
                      <span>${phase.cost.toFixed(4)}</span>
                    )}
                    {phase.tokens !== undefined && (
                      <span>{phase.tokens.toLocaleString()} tokens</span>
                    )}
                  </div>
                </div>
                {(phase.model || phase.tier_reason) && (
                  <div className="mt-1 ml-8 text-xs text-gray-500 space-y-0.5">
                    {phase.model && (
                      <div>
                        Model: <span className="text-gray-400 font-mono">{phase.model}</span>
                      </div>
                    )}
                    {phase.tier_reason && (
                      <div>
                        Reason: <span className="text-gray-400">{phase.tier_reason}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Outputs */}
      {job.outputs && Object.keys(job.outputs).length > 0 && (
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
          <h2 className="text-lg font-medium text-white mb-4">
            Output Files
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Object.entries(job.outputs).map(([key, filename]) => {
              const fileInfo = OUTPUT_FILES[key]
              if (!fileInfo || !filename) return null
              return (
                <button
                  key={key}
                  onClick={(e) => handleViewOutput(key, fileInfo.filename, e)}
                  disabled={loadingOutput}
                  className="flex items-center justify-center px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-md text-sm text-white transition-colors disabled:opacity-50"
                  aria-label={`View ${fileInfo.label}`}
                >
                  <span className="mr-2">&#128196;</span>
                  {fileInfo.label}
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Copy Editor Handoff - shown for completed jobs */}
      {job.status === 'completed' && (
        <CopyEditorHandoff projectName={job.project_name} />
      )}

      {/* Error Message */}
      {job.error_message && (
        <div role="alert" aria-live="assertive" className="bg-red-900/20 border border-red-500/30 rounded-lg p-4">
          <h3 className="text-red-400 font-medium mb-2">Error</h3>
          <pre className="text-sm text-red-300 whitespace-pre-wrap">
            {job.error_message}
          </pre>
        </div>
      )}

      {/* Timestamps */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
        <h2 className="text-lg font-medium text-white mb-4">Timeline</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-400">Queued:</span>
            <span className="ml-2 text-white">
              {new Date(job.queued_at).toLocaleString()}
            </span>
          </div>
          {job.started_at && (
            <div>
              <span className="text-gray-400">Started:</span>
              <span className="ml-2 text-white">
                {new Date(job.started_at).toLocaleString()}
              </span>
            </div>
          )}
          {job.completed_at && (
            <div>
              <span className="text-gray-400">Completed:</span>
              <span className="ml-2 text-white">
                {new Date(job.completed_at).toLocaleString()}
              </span>
            </div>
          )}
          {job.last_heartbeat && job.status === 'in_progress' && (
            <div>
              <span className="text-gray-400">Last heartbeat:</span>
              <span className="ml-2 text-white">
                {new Date(job.last_heartbeat).toLocaleString()}
              </span>
            </div>
          )}
          <div>
            <span className="text-gray-400">Retries:</span>
            <span className="ml-2 text-white">
              {job.retry_count} / {job.max_retries}
            </span>
          </div>
        </div>
      </div>

      {/* Output Viewer Modal */}
      {viewingOutput && (
        <div
          className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
          onClick={closeModal}
        >
          <div
            ref={modalRef}
            className="bg-gray-900 rounded-lg border border-gray-700 w-full max-w-4xl max-h-[90vh] flex flex-col"
            role="dialog"
            aria-modal="true"
            aria-labelledby="output-modal-title"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
              <h3 id="output-modal-title" className="text-lg font-medium text-white">
                {viewingOutput.label}
              </h3>
              <button
                onClick={closeModal}
                className="text-gray-400 hover:text-white text-2xl leading-none"
                aria-label="Close output viewer"
              >
                &times;
              </button>
            </div>
            {/* Modal Content */}
            <div className="flex-1 overflow-auto p-4">
              {viewingOutput.isJson ? (
                <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono">
                  {viewingOutput.content}
                </pre>
              ) : (
                <div className="prose prose-invert prose-sm max-w-none">
                  <ReactMarkdown>{viewingOutput.content}</ReactMarkdown>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function InfoCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-3">
      <div className="text-xs text-gray-400 uppercase tracking-wide">
        {label}
      </div>
      <div className="text-lg font-medium text-white mt-1">{value}</div>
    </div>
  )
}

function CopyEditorHandoff({ projectName }: { projectName: string }) {
  const [copied, setCopied] = useState(false)
  const promptText = `I'd like to edit ${projectName}`

  const handleCopyPrompt = async () => {
    try {
      await navigator.clipboard.writeText(promptText)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <div className="bg-gradient-to-r from-emerald-900/30 to-teal-900/30 rounded-lg border border-emerald-500/30 p-6">
      <div className="flex items-start space-x-4">
        {/* Icon */}
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-emerald-500/20 rounded-full flex items-center justify-center">
            <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-emerald-300 mb-2">
            Ready for Copy Editing
          </h3>
          <p className="text-gray-300 text-sm mb-4">
            This project is ready for interactive editing. Open Claude Desktop and start a conversation:
          </p>

          {/* Prompt Example */}
          <div className="bg-gray-900/50 rounded-lg p-4 mb-4">
            <div className="flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <span className="text-gray-400 text-sm">Say:</span>
                <p className="text-white font-medium mt-1 truncate">
                  "{promptText}"
                </p>
              </div>
              <button
                onClick={handleCopyPrompt}
                className="ml-4 flex-shrink-0 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-md text-sm font-medium transition-colors flex items-center space-x-1.5"
                aria-label="Copy prompt to clipboard"
              >
                {copied ? (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    <span>Copy</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Help Link */}
          <p className="text-gray-400 text-xs">
            First time?{' '}
            <a
              href="https://github.com/your-org/ai-editorial-assistant-v3/blob/main/docs/CLAUDE_DESKTOP_SETUP.md"
              target="_blank"
              rel="noopener noreferrer"
              className="text-emerald-400 hover:text-emerald-300 underline"
            >
              See the setup guide
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}
