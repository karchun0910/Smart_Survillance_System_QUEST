import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Camera,
  CircleAlert,
  Database,
  Plus,
  RefreshCw,
  ShieldCheck,
} from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api/v1'
const DISPLAY_TIME_ZONE = 'Asia/Kuala_Lumpur'

function formatEventTime(utcTimestamp: string) {
  const timestamp = /(?:Z|[+-]\d{2}:\d{2})$/.test(utcTimestamp)
    ? utcTimestamp
    : `${utcTimestamp}Z`
  const date = new Date(timestamp)

  if (Number.isNaN(date.getTime())) return utcTimestamp

  return new Intl.DateTimeFormat('en-MY', {
    dateStyle: 'medium',
    timeStyle: 'medium',
    hour12: false,
    timeZone: DISPLAY_TIME_ZONE,
  }).format(date)
}

function humanize(value: string) {
  const label = value.replaceAll('_', ' ')
  return label.charAt(0).toUpperCase() + label.slice(1)
}

type Health = {
  status: string
  application: string
  environment: string
}

type CameraStatus = {
  source: number
  available: boolean
}

type Rule = {
  id: number
  name: string
  observation_type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  is_enabled: boolean
  cooldown_seconds: number
  confidence_threshold: number
  min_duration_seconds: number
  created_at: string
}

type Event = {
  id: number
  camera_id: string
  track_id: string
  violation_type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  occurred_at: string
  review_status: 'pending' | 'confirmed' | 'false_alarm'
  message: string
}

type RuleDraft = Pick<
  Rule,
  | 'name'
  | 'observation_type'
  | 'severity'
  | 'cooldown_seconds'
  | 'confidence_threshold'
  | 'min_duration_seconds'
>

const emptyRule: RuleDraft = {
  name: '',
  observation_type: '',
  severity: 'medium',
  cooldown_seconds: 30,
  confidence_threshold: 0.5,
  min_duration_seconds: 0,
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(error?.detail ?? `Request failed (${response.status})`)
  }

  return response.json() as Promise<T>
}

function StatusCard({
  icon,
  label,
  value,
  available,
}: {
  icon: React.ReactNode
  label: string
  value: string
  available: boolean
}) {
  return (
    <article className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
      <div className="mb-5 flex items-center justify-between">
        <span className="rounded-lg bg-white/10 p-2 text-slate-200">
          {icon}
        </span>
        <span
          className={`size-2.5 rounded-full ${available ? 'bg-emerald-400' : 'bg-rose-400'}`}
          aria-label={available ? 'Connected' : 'Unavailable'}
        />
      </div>
      <p className="text-sm text-slate-400">{label}</p>
      <p className="mt-1 text-lg font-semibold text-white">{value}</p>
    </article>
  )
}

function App() {
  const queryClient = useQueryClient()
  const [draft, setDraft] = useState<RuleDraft>(emptyRule)

  const health = useQuery({
    queryKey: ['health'],
    queryFn: () => request<Health>('/health'),
    refetchInterval: 2000,
  })
  const camera = useQuery({
    queryKey: ['camera'],
    queryFn: () => request<CameraStatus>('/cameras/status'),
    refetchInterval: 2000,
  })
  const rules = useQuery({
    queryKey: ['rules'],
    queryFn: () => request<Rule[]>('/rules'),
    refetchInterval: 2000,
  })
  const events = useQuery({
    queryKey: ['events'],
    queryFn: () => request<Event[]>('/events?limit=20'),
    refetchInterval: 2000,
  })

  const createRule = useMutation({
    mutationFn: (payload: RuleDraft) =>
      request<Rule>('/rules', {
        method: 'POST',
        body: JSON.stringify({ ...payload, is_enabled: true }),
      }),
    onSuccess: () => {
      setDraft(emptyRule)
      void queryClient.invalidateQueries({ queryKey: ['rules'] })
    },
  })

  const toggleRule = useMutation({
    mutationFn: (rule: Rule) =>
      request<Rule>(`/rules/${rule.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ is_enabled: !rule.is_enabled }),
      }),
    onSuccess: () =>
      void queryClient.invalidateQueries({ queryKey: ['rules'] }),
  })

  const reviewEvent = useMutation({
    mutationFn: ({ id, review_status }: Pick<Event, 'id' | 'review_status'>) =>
      request<Event>(`/events/${id}/review`, {
        method: 'PATCH',
        body: JSON.stringify({ review_status }),
      }),
    onSuccess: () =>
      void queryClient.invalidateQueries({ queryKey: ['events'] }),
  })

  function submitRule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    createRule.mutate(draft)
  }

  function refreshAll() {
    void queryClient.invalidateQueries()
  }

  const apiConnected = health.isSuccess
  const databaseConnected = rules.isSuccess

  return (
    <div className="min-h-[100dvh] bg-[#0f172a] text-slate-100">
      <header className="border-b border-white/10">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <span className="grid size-10 place-items-center rounded-xl bg-emerald-400 text-slate-950">
              <ShieldCheck aria-hidden="true" size={22} strokeWidth={2} />
            </span>
            <div>
              <p className="font-semibold text-white">Smart Surveillance</p>
              <p className="text-xs text-slate-400">Laboratory control panel</p>
            </div>
          </div>
          <button
            type="button"
            onClick={refreshAll}
            aria-label="Refresh system status and policy rules"
            className="ml-3 flex size-11 shrink-0 cursor-pointer items-center justify-center rounded-lg border border-white/15 text-sm font-medium text-slate-200 transition-colors hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400 sm:h-11 sm:w-auto sm:gap-2 sm:px-4"
          >
            <RefreshCw aria-hidden="true" size={17} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8">
          <p className="text-sm font-medium text-emerald-400">
            System overview
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            Surveillance dashboard
          </h1>
          <p className="mt-3 max-w-2xl text-slate-400">
            Monitor the local system and manage the rules stored in MySQL.
          </p>
        </div>

        <section
          aria-label="System status"
          className="grid gap-4 md:grid-cols-3"
        >
          <StatusCard
            icon={<ShieldCheck aria-hidden="true" size={20} />}
            label="Backend API"
            value={
              health.isPending
                ? 'Checking…'
                : apiConnected
                  ? 'Online'
                  : 'Offline'
            }
            available={apiConnected}
          />
          <StatusCard
            icon={<Database aria-hidden="true" size={20} />}
            label="MySQL database"
            value={
              rules.isPending
                ? 'Checking…'
                : databaseConnected
                  ? 'Connected'
                  : 'Unavailable'
            }
            available={databaseConnected}
          />
          <StatusCard
            icon={<Camera aria-hidden="true" size={20} />}
            label="Camera source"
            value={
              camera.isPending
                ? 'Checking…'
                : camera.data?.available
                  ? `Camera ${camera.data.source} ready`
                  : 'Not available'
            }
            available={camera.data?.available ?? false}
          />
        </section>

        {(health.isError ||
          rules.isError ||
          camera.isError ||
          events.isError) && (
          <div
            role="alert"
            className="mt-6 flex items-start gap-3 rounded-xl border border-amber-400/30 bg-amber-400/10 p-4 text-sm text-amber-100"
          >
            <CircleAlert
              className="mt-0.5 shrink-0"
              aria-hidden="true"
              size={18}
            />
            <p>
              Some services are unavailable. Start FastAPI on port 8000 and
              confirm the MySQL settings in <code>Backend/.env</code>, then
              select Refresh.
            </p>
          </div>
        )}

        <div className="mt-8 grid min-w-0 gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
          <section className="min-w-0 overflow-hidden rounded-2xl bg-white text-slate-900">
            <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4 sm:px-6">
              <div>
                <h2 className="text-lg font-semibold">Policy rules</h2>
                <p className="mt-1 text-sm text-slate-500">
                  {rules.data?.length ?? 0} rules stored in the database
                </p>
              </div>
            </div>

            {rules.isPending && (
              <p className="px-6 py-10 text-center text-sm text-slate-500">
                Loading rules…
              </p>
            )}

            {rules.isError && (
              <div className="px-6 py-10 text-center" role="alert">
                <p className="text-sm text-rose-700">{rules.error.message}</p>
                <button
                  type="button"
                  onClick={() => void rules.refetch()}
                  className="mt-3 min-h-11 cursor-pointer rounded-lg border border-slate-300 px-4 text-sm font-medium hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-800"
                >
                  Try again
                </button>
              </div>
            )}

            {rules.isSuccess && rules.data.length === 0 && (
              <p className="px-6 py-10 text-center text-sm text-slate-500">
                No rules yet. Add your first rule using the form.
              </p>
            )}

            {rules.data && rules.data.length > 0 && (
              <div className="divide-y divide-slate-200">
                {rules.data.map((rule) => (
                  <div
                    key={rule.id}
                    className="flex flex-col gap-4 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="font-medium break-words text-slate-900">
                          {rule.name}
                        </h3>
                        <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600 capitalize">
                          {rule.severity}
                        </span>
                      </div>
                      <p className="mt-1 font-mono text-xs break-all text-slate-500">
                        {rule.observation_type} ·{' '}
                        {Math.round(rule.confidence_threshold * 100)}%
                        confidence · {rule.cooldown_seconds}s cooldown
                      </p>
                    </div>
                    <button
                      type="button"
                      disabled={toggleRule.isPending}
                      onClick={() => toggleRule.mutate(rule)}
                      className={`min-h-11 shrink-0 cursor-pointer rounded-lg px-4 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-800 disabled:cursor-not-allowed disabled:opacity-50 ${
                        rule.is_enabled
                          ? 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                    >
                      {rule.is_enabled ? 'Enabled' : 'Disabled'}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="overflow-hidden rounded-2xl bg-white text-slate-900 xl:col-span-2">
            <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4 sm:px-6">
              <div>
                <h2 className="text-lg font-semibold">Recent events</h2>
                <p className="mt-1 text-sm text-slate-500">
                  Confirmed violations and lecturer review status
                </p>
              </div>
              <span className="rounded-full bg-rose-100 px-3 py-1 text-xs font-medium text-rose-700">
                {events.data?.filter(
                  (event) => event.review_status === 'confirmed',
                ).length ?? 0}{' '}
                confirmed
              </span>
            </div>
            {events.isPending && (
              <p className="px-6 py-10 text-center text-sm text-slate-500">
                Loading events…
              </p>
            )}
            {events.isError && (
              <div className="px-6 py-10 text-center" role="alert">
                <p className="text-sm text-rose-700">{events.error.message}</p>
                <button
                  type="button"
                  onClick={() => void events.refetch()}
                  className="mt-3 min-h-11 cursor-pointer rounded-lg border border-slate-300 px-4 text-sm font-medium hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-800"
                >
                  Try again
                </button>
              </div>
            )}
            {reviewEvent.isError && (
              <p
                role="alert"
                className="border-b border-rose-200 bg-rose-50 px-6 py-3 text-sm text-rose-700"
              >
                Review was not saved: {reviewEvent.error.message}
              </p>
            )}
            {events.isSuccess && events.data.length === 0 && (
              <p className="px-6 py-10 text-center text-sm text-slate-500">
                No events recorded yet. Post an observation from the detector
                worker.
              </p>
            )}
            {events.data && events.data.length > 0 && (
              <div className="divide-y divide-slate-200">
                {events.data.map((event) => {
                  const confirmed = event.review_status === 'confirmed'
                  const falseAlarm = event.review_status === 'false_alarm'
                  return (
                    <div
                      key={event.id}
                      className={`flex flex-col gap-3 border-l-4 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6 ${confirmed ? 'border-rose-500 bg-rose-50' : falseAlarm ? 'border-emerald-500 bg-emerald-50/40' : 'border-amber-500 bg-amber-50'}`}
                    >
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="font-medium text-slate-900">
                            {humanize(event.violation_type)}
                          </h3>
                          <span className="rounded-full bg-slate-200 px-2 py-1 text-xs text-slate-700 capitalize">
                            {event.severity}
                          </span>
                          <span className="rounded-full bg-white px-2 py-1 text-xs font-medium text-slate-700 capitalize ring-1 ring-slate-200">
                            {event.review_status.replace('_', ' ')}
                          </span>
                        </div>
                        <p className="mt-1 text-sm text-slate-600">
                          {event.message} · camera {event.camera_id} · track{' '}
                          {event.track_id}
                        </p>
                        <p className="mt-1 text-xs text-slate-500">
                          {formatEventTime(event.occurred_at)}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="button"
                          disabled={reviewEvent.isPending || confirmed}
                          onClick={() =>
                            reviewEvent.mutate({
                              id: event.id,
                              review_status: 'confirmed',
                            })
                          }
                          className="min-h-11 cursor-pointer rounded-lg bg-rose-600 px-4 text-sm font-medium text-white hover:bg-rose-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rose-700 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          Confirm
                        </button>
                        <button
                          type="button"
                          disabled={reviewEvent.isPending || falseAlarm}
                          onClick={() =>
                            reviewEvent.mutate({
                              id: event.id,
                              review_status: 'false_alarm',
                            })
                          }
                          className="min-h-11 cursor-pointer rounded-lg border border-slate-300 bg-white px-4 text-sm font-medium text-slate-700 hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          False alarm
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </section>

          <aside className="w-full min-w-0 rounded-2xl border border-white/10 bg-white/[0.04] p-5 sm:p-6">
            <div className="mb-6 flex items-center gap-3">
              <span className="grid size-9 place-items-center rounded-lg bg-emerald-400/15 text-emerald-300">
                <Plus aria-hidden="true" size={19} />
              </span>
              <div>
                <h2 className="font-semibold text-white">Add policy rule</h2>
                <p className="text-sm text-slate-400">
                  Saved directly through FastAPI
                </p>
              </div>
            </div>

            <form onSubmit={submitRule} className="min-w-0 space-y-4">
              <label className="block text-sm font-medium text-slate-200">
                Rule name
                <input
                  required
                  maxLength={100}
                  value={draft.name}
                  onChange={(event) =>
                    setDraft({ ...draft, name: event.target.value })
                  }
                  className="mt-2 min-h-11 w-full rounded-lg border border-white/15 bg-slate-950 px-3 text-white outline-none placeholder:text-slate-600 focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/20"
                  placeholder="No laboratory coat"
                />
              </label>

              <label className="block text-sm font-medium text-slate-200">
                Observation type
                <input
                  required
                  maxLength={100}
                  pattern="[a-z][a-z0-9_]*"
                  value={draft.observation_type}
                  onChange={(event) =>
                    setDraft({ ...draft, observation_type: event.target.value })
                  }
                  className="mt-2 min-h-11 w-full rounded-lg border border-white/15 bg-slate-950 px-3 font-mono text-sm text-white outline-none placeholder:text-slate-600 focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/20"
                  placeholder="missing_lab_coat"
                />
              </label>

              <div className="grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2">
                <label className="block min-w-0 text-sm font-medium text-slate-200">
                  Severity
                  <select
                    value={draft.severity}
                    onChange={(event) =>
                      setDraft({
                        ...draft,
                        severity: event.target.value as RuleDraft['severity'],
                      })
                    }
                    className="mt-2 min-h-11 w-full rounded-lg border border-white/15 bg-slate-950 px-3 text-white outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/20"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </label>

                <label className="block min-w-0 text-sm font-medium text-slate-200">
                  Cooldown
                  <input
                    required
                    type="number"
                    min="0"
                    value={draft.cooldown_seconds}
                    onChange={(event) =>
                      setDraft({
                        ...draft,
                        cooldown_seconds: Number(event.target.value),
                      })
                    }
                    className="mt-2 min-h-11 w-full rounded-lg border border-white/15 bg-slate-950 px-3 text-white outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/20"
                    aria-describedby="cooldown-help"
                  />
                </label>
              </div>
              <p id="cooldown-help" className="text-xs text-slate-500">
                Seconds before the same alert can trigger again.
              </p>

              <div className="grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2">
                <label className="block min-w-0 text-sm font-medium text-slate-200">
                  Confidence
                  <input
                    required
                    type="number"
                    min="0"
                    max="1"
                    step="0.05"
                    value={draft.confidence_threshold}
                    onChange={(event) =>
                      setDraft({
                        ...draft,
                        confidence_threshold: Number(event.target.value),
                      })
                    }
                    className="mt-2 min-h-11 w-full rounded-lg border border-white/15 bg-slate-950 px-3 text-white outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/20"
                  />
                </label>
                <label className="block min-w-0 text-sm font-medium text-slate-200">
                  Visible seconds
                  <input
                    required
                    type="number"
                    min="0"
                    step="0.5"
                    value={draft.min_duration_seconds}
                    onChange={(event) =>
                      setDraft({
                        ...draft,
                        min_duration_seconds: Number(event.target.value),
                      })
                    }
                    className="mt-2 min-h-11 w-full rounded-lg border border-white/15 bg-slate-950 px-3 text-white outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/20"
                  />
                </label>
              </div>

              {createRule.isError && (
                <p role="alert" className="text-sm break-words text-rose-300">
                  {createRule.error.message}
                </p>
              )}

              <button
                type="submit"
                disabled={createRule.isPending}
                className="min-h-11 w-full min-w-0 cursor-pointer rounded-lg bg-emerald-400 px-4 font-semibold text-slate-950 transition-colors hover:bg-emerald-300 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-300 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {createRule.isPending ? 'Saving…' : 'Save rule'}
              </button>
            </form>
          </aside>
        </div>
      </main>
    </div>
  )
}

export default App
