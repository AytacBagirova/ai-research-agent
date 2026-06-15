import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { toast } from "sonner";
import { Navbar } from "@/components/Navbar";
import { SourceCard } from "@/components/SourceCard";
import { StepCard, AgentStep } from "@/components/StepCard";
import { api } from "@/lib/api";

export const Route = createFileRoute("/research/$sessionId/report")({
  component: ReportPage,
});

function ReportPage() {
  const { sessionId } = Route.useParams();
  const navigate = useNavigate();
  const [data, setData] = useState<Awaited<ReturnType<typeof api.getReport>> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timelineOpen, setTimelineOpen] = useState(false);

  useEffect(() => {
    let alive = true;
    api.getReport(sessionId)
      .then((d) => alive && setData(d))
      .catch((e) => alive && setError(e.message))
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, [sessionId]);

  const copyReport = async () => {
    if (!data?.report) return;
    await navigator.clipboard.writeText(data.report);
    toast.success("Copied ✿");
  };

  if (loading) {
    return (
      <div className="min-h-screen">
        <Navbar />
        <main className="mx-auto max-w-4xl px-6 pt-10">
          <div className="h-12 w-2/3 animate-soft-pulse rounded-2xl bg-card" />
          <div className="mt-6 space-y-3">
            {[0,1,2,3,4].map((i) => <div key={i} className="h-6 w-full animate-soft-pulse rounded bg-card" />)}
          </div>
        </main>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen">
        <Navbar />
        <main className="mx-auto max-w-2xl px-6 pt-20 text-center">
          <p className="text-4xl">✗</p>
          <h1 className="mt-3 font-display text-2xl">Couldn't load the report</h1>
          <p className="mt-2 font-accent italic text-[color:var(--color-dusty)]">{error}</p>
          <Link to="/" className="mt-6 inline-block rounded-full bg-gradient-primary px-6 py-2.5 text-white shadow-glow">
            ✿ Go home
          </Link>
        </main>
      </div>
    );
  }

  const stats = data.stats ?? {};
  const duration = stats.duration_ms ? `${(stats.duration_ms / 1000).toFixed(1)}s` : "—";

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-4xl px-6 pb-24 pt-6">
        <Link to="/" className="rounded-full border border-border bg-card px-3 py-1.5 text-sm hover:bg-secondary">
          ← Home
        </Link>

        <header className="mt-6 animate-fade-up">
          <p className="font-accent text-lg italic text-[color:var(--color-dusty)]">⊹ research report ⊹</p>
          <h1 className="mt-2 font-display text-4xl leading-tight sm:text-5xl">{data.topic}</h1>

          <div className="mt-6 flex flex-wrap gap-3">
            <Stat emoji="✦" label="tokens" value={stats.tokens ?? "—"} />
            <Stat emoji="✿" label="sources" value={stats.sources ?? data.sources?.length ?? 0} />
            <Stat emoji="◈" label="time" value={duration} />
          </div>
        </header>

        {/* Report markdown */}
        <article className="report-prose mt-10 animate-fade-up">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {data.report || "_No report content._"}
          </ReactMarkdown>
        </article>

        {/* Sources */}
        {data.sources?.length > 0 && (
          <section className="mt-14">
            <h2 className="mb-4 font-display text-2xl">References <span className="text-[color:var(--color-dusty)]">✦</span></h2>
            <div className="grid gap-3 sm:grid-cols-2">
              {data.sources.map((s, i) => <SourceCard key={i} source={s} />)}
            </div>
          </section>
        )}

        {/* Timeline */}
        {data.timeline && data.timeline.length > 0 && (
          <section className="mt-14">
            <button
              onClick={() => setTimelineOpen((o) => !o)}
              className="flex w-full items-center justify-between rounded-2xl border border-border bg-card px-5 py-4"
            >
              <span className="font-display text-xl">Research Journey ◈</span>
              <span className="font-accent italic text-muted-foreground">{timelineOpen ? "hide" : "show"} ⊹</span>
            </button>
            {timelineOpen && (
              <div className="mt-4 space-y-3 animate-fade-up">
                {data.timeline.map((s, i) => <StepCard key={i} step={s as AgentStep} />)}
              </div>
            )}
          </section>
        )}

        {/* Actions */}
        <div className="mt-14 flex flex-wrap justify-center gap-3">
          <button
            onClick={copyReport}
            className="rounded-full border border-border bg-card px-6 py-3 font-medium hover:bg-secondary"
          >
            ✿ Copy Report
          </button>
          <button
            onClick={() => navigate({ to: "/" })}
            className="rounded-full bg-gradient-primary px-6 py-3 font-medium text-white shadow-glow hover:scale-[1.03] transition"
          >
            ✦ New Research
          </button>
        </div>
      </main>

      <style>{`
        .report-prose { color: var(--color-foreground); font-family: var(--font-sans); line-height: 1.7; }
        .report-prose h1, .report-prose h2, .report-prose h3, .report-prose h4 {
          font-family: var(--font-display); color: var(--color-burgundy);
          margin-top: 1.6em; margin-bottom: 0.5em; line-height: 1.25;
        }
        .dark .report-prose h1, .dark .report-prose h2, .dark .report-prose h3, .dark .report-prose h4 { color: var(--color-peach); }
        .report-prose h1 { font-size: 2rem; }
        .report-prose h2 { font-size: 1.6rem; }
        .report-prose h3 { font-size: 1.3rem; }
        .report-prose p { margin: 1em 0; }
        .report-prose a { color: var(--color-dusty); text-decoration: underline; text-underline-offset: 3px; }
        .report-prose a:hover { color: var(--color-berry); }
        .report-prose blockquote {
          border-left: 3px solid var(--color-dusty); padding: 0.4em 1em; margin: 1.2em 0;
          font-family: var(--font-accent); font-style: italic; color: var(--color-muted-foreground);
          background: var(--color-card); border-radius: 0 1rem 1rem 0;
        }
        .report-prose ul, .report-prose ol { padding-left: 1.4em; margin: 1em 0; }
        .report-prose li { margin: 0.3em 0; }
        .report-prose code {
          background: var(--color-muted); padding: 0.15em 0.4em; border-radius: 0.4em;
          font-size: 0.9em; color: var(--color-berry);
        }
        .dark .report-prose code { color: var(--color-peach); }
        .report-prose pre {
          background: var(--color-card); padding: 1em; border-radius: 1rem; overflow-x: auto;
          border: 1px solid var(--color-border);
        }
        .report-prose pre code { background: transparent; padding: 0; }
        .report-prose hr { border: none; border-top: 1px solid var(--color-border); margin: 2em 0; }
        .report-prose table { width: 100%; border-collapse: collapse; margin: 1em 0; }
        .report-prose th, .report-prose td { border: 1px solid var(--color-border); padding: 0.5em 0.8em; text-align: left; }
        .report-prose th { background: var(--color-card); font-family: var(--font-display); }
      `}</style>
    </div>
  );
}

function Stat({ emoji, label, value }: { emoji: string; label: string; value: string | number }) {
  return (
    <div className="rounded-2xl border border-border bg-card px-4 py-3">
      <div className="flex items-baseline gap-2">
        <span className="text-lg text-[color:var(--color-dusty)]">{emoji}</span>
        <span className="font-display text-xl font-semibold">{value}</span>
      </div>
      <p className="font-accent text-xs italic text-muted-foreground">{label}</p>
    </div>
  );
}
