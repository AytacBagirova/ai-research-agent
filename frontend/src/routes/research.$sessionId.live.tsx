import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { Navbar } from "@/components/Navbar";
import { StatusBadge } from "@/components/StatusBadge";
import { StepCard, AgentStep } from "@/components/StepCard";
import { SourceCard, Source } from "@/components/SourceCard";
import { api } from "@/lib/api";
import { toast } from "sonner";

export const Route = createFileRoute("/research/$sessionId/live")({
  component: LivePage,
});

const STAGES = [
  { id: "searching", label: "Searching", emoji: "◌" },
  { id: "reading",   label: "Reading",   emoji: "◌" },
  { id: "analyzing", label: "Analyzing", emoji: "◌" },
  { id: "writing",   label: "Writing",   emoji: "◌" },
  { id: "done",      label: "Done",      emoji: "✿" },
];

const stageFromEvent = (type: string): string | null => {
  switch (type) {
    case "tool_use":   return "searching";
    case "tool_result": return "reading";
    case "thought":
    case "critique":   return "analyzing";
    case "final_report": return "writing";
    case "done":       return "done";
    default:           return null;
  }
};

function LivePage() {
  const { sessionId } = Route.useParams();
  const navigate = useNavigate();
  const [topic, setTopic] = useState<string>("");
  const [status, setStatus] = useState<string>("running");
  const [stage, setStage] = useState<string>("searching");
  const [steps, setSteps] = useState<AgentStep[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const thoughtsRef = useRef<HTMLDivElement>(null);
  const sourcesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Session mövzusunu tap
    api.getSessions().then((list) => {
      const s = list.find((x) => x.id === sessionId);
      if (s) { setTopic(s.topic); setStatus(s.status); }
    }).catch(() => {});

    const es = new EventSource(api.streamUrl(sessionId));

    const onMessage = (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data);
        const type: string = data.type || ev.type;
        const newStage = stageFromEvent(type);
        if (newStage) setStage(newStage);

        // Done
        if (type === "done") {
          setStatus("done");
          setStage("done");
          es.close();
          return;
        }

        // Xəta
        if (type === "error") {
          setStatus("failed");
          toast.error(data.content || data.message || "Something went wrong ✗");
          es.close();
          return;
        }

        // Sources-ı tool_result-dən çıxar
        if (type === "tool_result") {
          const content: string = data.content || "";
          const collected: Source[] = [];

          // data.sources array-i varsa əlavə et
          if (Array.isArray(data.sources)) {
            collected.push(...data.sources);
          }

          // Content-dən URL-ləri çıxar
          if (content) {
            // source_url: "..." formatı
            const urlRe = /source_url["'\s:=]+["']?(https?:\/\/[^\s"'<>)\n]+)/gi;
            let m: RegExpExecArray | null;
            while ((m = urlRe.exec(content)) !== null) {
              collected.push({ url: m[1], title: m[1] });
            }

            // URL: https://... formatı
            const urlLine = /URL:\s*(https?:\/\/[^\s\n]+)/gi;
            while ((m = urlLine.exec(content)) !== null) {
              collected.push({ url: m[1], title: m[1] });
            }

            // Əgər hələ heç nə tapılmadısa — bare URL-ləri götür
            if (collected.length === 0) {
              const bare = content.match(/https?:\/\/[^\s"'<>)\n]+/g);
              bare?.forEach((u) => collected.push({ url: u, title: u }));
            }
          }

          if (collected.length > 0) {
            setSources((prev) => {
              const seen = new Set(prev.map((s) => s.url));
              const merged = [...prev];
              for (const s of collected) {
                if (s.url && !seen.has(s.url)) {
                  seen.add(s.url);
                  merged.push(s);
                }
              }
              return merged;
            });
          }
        }

        // source event
        if (type === "source" && data.source) {
          setSources((prev) => {
            const seen = new Set(prev.map((s) => s.url));
            if (!seen.has(data.source.url)) return [...prev, data.source];
            return prev;
          });
        }

        // Final report — thought kimi göstərmə
        if (type === "final_report") return;

        // Uzun hesabat kimi görünən thought-ları skip et
        const content: string = data.content || data.text || data.message || "";
        const looksLikeReport =
          (content.startsWith("---") || content.startsWith("# ") || content.includes("## Executive Summary")) &&
          content.length > 500;
        if (looksLikeReport) return;

        // Step əlavə et
        setSteps((prev) => [...prev, {
          type,
          content,
          tool: data.tool || data.tool_name,
          timestamp: data.timestamp || Date.now(),
        }]);

      } catch {
        // ignore malformed
      }
    };

    es.onmessage = onMessage;
    ["thought", "tool_use", "tool_result", "critique", "final_report", "done", "error", "source"].forEach((t) => {
      es.addEventListener(t, onMessage as EventListener);
    });

    es.onerror = () => {
      setStatus((cur) => cur === "done" ? cur : "failed");
    };

    return () => es.close();
  }, [sessionId]);

  useEffect(() => {
    thoughtsRef.current?.scrollTo({ top: thoughtsRef.current.scrollHeight, behavior: "smooth" });
  }, [steps.length]);

  useEffect(() => {
    sourcesRef.current?.scrollTo({ top: sourcesRef.current.scrollHeight, behavior: "smooth" });
  }, [sources.length]);

  const activeIdx = STAGES.findIndex((s) => s.id === stage);

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-6xl px-6 pb-24 pt-6">
        <div className="flex flex-wrap items-center gap-3">
          <Link to="/" className="rounded-full border border-border bg-card px-3 py-1.5 text-sm hover:bg-secondary">
            ← Home
          </Link>
          <h1 className="flex-1 font-display text-2xl sm:text-3xl line-clamp-2">{topic || "Researching…"}</h1>
          <StatusBadge status={status} />
        </div>

        {/* Stage progress */}
        <div className="mt-8 rounded-3xl border border-border bg-card p-6 shadow-soft">
          <div className="flex items-center justify-between">
            {STAGES.map((s, i) => {
              const completed = i < activeIdx || status === "done";
              const active = i === activeIdx && status !== "done";
              return (
                <div key={s.id} className="flex flex-1 items-center">
                  <div className="flex flex-col items-center">
                    <div
                      className={`grid h-10 w-10 place-items-center rounded-full text-base transition-all duration-500 ${
                        active
                          ? "bg-gradient-primary text-white shadow-glow animate-soft-pulse"
                          : completed
                          ? "bg-[color:var(--color-berry)] text-white"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {completed ? "✿" : active ? "◌" : s.emoji}
                    </div>
                    <span className="mt-2 font-accent text-xs italic">{s.label}</span>
                  </div>
                  {i < STAGES.length - 1 && (
                    <div className="mx-2 h-[2px] flex-1 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full bg-gradient-primary transition-all duration-700"
                        style={{ width: completed ? "100%" : active ? "50%" : "0%" }}
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <div className="mt-8 grid gap-6 lg:grid-cols-5">
          {/* Thoughts */}
          <section className="lg:col-span-3">
            <h2 className="mb-3 font-display text-xl">
              Agent Thoughts <span className="text-[color:var(--color-dusty)]">♡</span>
            </h2>
            <div
              ref={thoughtsRef}
              className="max-h-[70vh] space-y-3 overflow-y-auto rounded-3xl border border-border bg-card/60 p-4"
            >
              {steps.length === 0 ? (
                <div className="py-16 text-center">
                  <p className="animate-soft-pulse text-3xl">◌</p>
                  <p className="mt-2 font-accent italic text-muted-foreground">Listening to the agent's thoughts…</p>
                </div>
              ) : (
                steps.map((s, i) => <StepCard key={i} step={s} />)
              )}
            </div>
          </section>

          {/* Sources */}
          <section className="lg:col-span-2">
            <h2 className="mb-3 font-display text-xl">
              Sources <span className="text-[color:var(--color-dusty)]">✦</span>
            </h2>
            <div
              ref={sourcesRef}
              className="max-h-[70vh] space-y-3 overflow-y-auto rounded-3xl border border-border bg-card/60 p-4"
            >
              {sources.length === 0 ? (
                <div className="py-16 text-center">
                  <p className="text-3xl">✾</p>
                  <p className="mt-2 font-accent italic text-muted-foreground">Sources will bloom here…</p>
                </div>
              ) : (
                sources.map((s, i) => <SourceCard key={i} source={s} />)
              )}
            </div>
          </section>
        </div>

        {/* Done banner */}
        {status === "done" && (
          <div className="mt-10 animate-fade-up rounded-3xl border border-border bg-card p-6 shadow-soft sm:p-8">
            <div className="flex flex-col items-center gap-4 text-center sm:flex-row sm:justify-between sm:text-left">
              <div>
                <p className="font-display text-2xl text-[color:var(--color-burgundy)]">
                  ✿ Research complete!
                </p>
                <p className="mt-1 font-accent italic text-[color:var(--color-berry)]/80">
                  Your report is ready. View it below.
                </p>
              </div>
              <button
                onClick={() => navigate({ to: "/research/$sessionId/report", params: { sessionId } })}
                className="rounded-full bg-gradient-primary px-8 py-3 font-display text-lg font-semibold text-white shadow-glow transition hover:scale-[1.03]"
              >
                View Report →
              </button>
            </div>
          </div>
        )}

        {/* Failed banner */}
        {status === "failed" && (
          <div className="mt-10 rounded-3xl border border-border bg-card p-6 text-center">
            <p className="font-display text-xl text-[color:var(--color-dusty)]">✗ Something went wrong</p>
            <p className="mt-1 font-accent italic text-muted-foreground">Please try again with a different topic.</p>
            <Link to="/" className="mt-4 inline-block rounded-full bg-gradient-primary px-6 py-2.5 text-white shadow-glow">
              ✿ Try again
            </Link>
          </div>
        )}
      </main>
    </div>
  );
}