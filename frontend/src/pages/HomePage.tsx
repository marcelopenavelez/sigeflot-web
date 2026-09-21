const capabilities = ['Administración de flota', 'Mantenimiento vehicular', 'Control operativo']

export function HomePage() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_right,_#1c4569,_transparent_38%),linear-gradient(135deg,_#091321,_#0e2134)] px-6 py-10 text-slate-100">
      <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-5xl flex-col justify-between">
        <header className="flex items-center gap-3 text-sm font-semibold tracking-[0.18em] text-cyan-300">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-cyan-400/15 text-lg">S</span>
          SIGEFLOT WEB
        </header>
        <section className="max-w-3xl py-20">
          <p className="mb-5 text-sm font-semibold uppercase tracking-[0.2em] text-cyan-300">Plataforma en preparación</p>
          <h1 className="text-4xl font-bold tracking-tight text-white sm:text-6xl">Sistema Integral de Gestión de Flota y Mantenimiento Vehicular</h1>
          <p className="mt-7 max-w-2xl text-lg leading-8 text-slate-300">Base tecnológica para centralizar la información, mejorar la trazabilidad y respaldar las decisiones operativas de una flota.</p>
          <div className="mt-10 flex flex-wrap gap-3">
            {capabilities.map((capability) => <span key={capability} className="rounded-full border border-cyan-300/20 bg-white/5 px-4 py-2 text-sm text-slate-200">{capability}</span>)}
          </div>
        </section>
        <footer className="border-t border-white/10 pt-6 text-sm text-slate-400">Proyecto académico · ISAM · Herramientas y Servicios para Desarrolladores en la Web</footer>
      </div>
    </main>
  )
}
