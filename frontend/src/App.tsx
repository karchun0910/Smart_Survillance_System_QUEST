const installedTools = [
  'React + TypeScript',
  'Vite',
  'Tailwind CSS',
  'React Router',
  'TanStack Query',
  'HLS.js',
]

function App() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#090d12] px-6 py-16 text-slate-100">
      <section className="w-full max-w-3xl rounded-2xl border border-slate-800 bg-slate-950 p-8 md:p-12">
        <div className="mb-8 flex items-center gap-3">
          <span className="size-2.5 rounded-full bg-emerald-400 shadow-[0_0_18px_rgba(52,211,153,0.75)]" />
          <span className="text-sm font-medium tracking-wide text-emerald-300">
            Frontend environment ready
          </span>
        </div>

        <p className="mb-3 text-sm font-semibold tracking-[0.2em] text-slate-500 uppercase">
          Smart Surveillance System
        </p>
        <h1 className="max-w-2xl text-4xl font-semibold tracking-tight text-white md:text-6xl">
          React development workspace
        </h1>
        <p className="mt-5 max-w-2xl text-base leading-7 text-slate-400 md:text-lg">
          The project is configured for the live-monitoring dashboard, event
          review, rule management, and camera playback modules.
        </p>

        <div className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {installedTools.map((tool) => (
            <div
              key={tool}
              className="rounded-xl border border-slate-800 bg-slate-900/70 px-4 py-3 text-sm text-slate-300"
            >
              {tool}
            </div>
          ))}
        </div>

        <p className="mt-10 text-sm text-slate-500">
          Start editing{' '}
          <code className="rounded bg-slate-900 px-2 py-1 text-slate-300">
            src/App.tsx
          </code>
        </p>
      </section>
    </main>
  )
}

export default App
