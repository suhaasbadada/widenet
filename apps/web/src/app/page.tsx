import { getApiHealth } from "@/lib/api";

export default async function Home() {
  const health = await getApiHealth();

  return (
    <main className="page-shell">
      <section className="hero-flow px-6 pt-10 pb-16 md:px-12 md:pt-16 md:pb-24">
        <div className="mx-auto w-full max-w-6xl animate-rise">
          <div className="mb-10 flex flex-wrap items-center justify-between gap-4">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-600">Widenet Platform</p>
            <span className={`status-chip ${health.ok ? "status-ok" : "status-down"}`}>
              API {health.ok ? "connected" : "unreachable"}
            </span>
          </div>

          <h1 className="font-display max-w-5xl text-5xl leading-[1.05] text-slate-900 md:text-7xl">
            One workspace for resumes, applications, and outreach.
          </h1>

          <p
            className="mt-8 max-w-3xl text-lg leading-8 text-slate-700 animate-rise"
            style={{ animationDelay: "90ms" }}
          >
            Widenet helps candidates turn one structured profile into tailored resumes,
            job-specific answers, and personalized recruiter messages. It keeps every step
            organized by application so execution stays consistent.
          </p>

          <div className="mt-10 flex flex-wrap gap-3 animate-rise" style={{ animationDelay: "160ms" }}>
            <button className="cta-main" type="button">Join Waitlist</button>
            <button className="cta-ghost" type="button">See Product Preview</button>
          </div>

          <div className="mt-16 grid gap-8 border-t border-slate-300/70 pt-8 md:grid-cols-4 animate-rise" style={{ animationDelay: "230ms" }}>
            <article>
              <p className="metric-label">Status</p>
              <p className="metric-value">Alpha</p>
              <p className="metric-copy">Core platform workflow is active</p>
            </article>
            <article>
              <p className="metric-label">Module</p>
              <p className="metric-value">Auth</p>
              <p className="metric-copy">Role-aware access and session flow</p>
            </article>
            <article>
              <p className="metric-label">Module</p>
              <p className="metric-value">Resumes</p>
              <p className="metric-copy">Generate and export DOCX/PDF variants</p>
            </article>
            <article>
              <p className="metric-label">Module</p>
              <p className="metric-value">Pipeline</p>
              <p className="metric-copy">Jobs, applications, and outreach tracking</p>
            </article>
          </div>
        </div>
      </section>

      <section className="px-6 pb-20 md:px-12 md:pb-24">
        <div className="mx-auto grid w-full max-w-6xl gap-10 border-t border-slate-300/60 pt-12 md:grid-cols-3">
          <article className="animate-rise" style={{ animationDelay: "260ms" }}>
            <p className="feature-kicker">01 Candidate Core</p>
            <h2 className="font-display text-3xl text-slate-900">Structured profile</h2>
              <p className="feature-copy mt-3 text-sm leading-7 text-slate-700">
              Resume upload, parsing, and profile refresh keep source data reliable before
              generating any application content.
            </p>
          </article>

          <article className="animate-rise" style={{ animationDelay: "320ms" }}>
            <p className="feature-kicker">02 Application Engine</p>
            <h2 className="font-display text-3xl text-slate-900">Tailored output</h2>
              <p className="feature-copy mt-3 text-sm leading-7 text-slate-700">
              Job descriptions and profile context are mapped into focused answers and resume
              variants aligned to each role.
            </p>
          </article>

          <article className="animate-rise" style={{ animationDelay: "380ms" }}>
            <p className="feature-kicker">03 Outreach Studio</p>
            <h2 className="font-display text-3xl text-slate-900">Communication layer</h2>
              <p className="feature-copy mt-3 text-sm leading-7 text-slate-700">
              Generate recruiter outreach and cover letters with consistent tone and role-specific
              relevance across opportunities.
            </p>
          </article>
        </div>
      </section>
    </main>
  );
}
