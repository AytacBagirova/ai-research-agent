import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Navbar } from "@/components/Navbar";
import { StatusBadge } from "@/components/StatusBadge";
import { api, Session } from "@/lib/api";

export const Route = createFileRoute("/")({
  component: HomePage,
});

const depths = [
  { id: "basic", label: "Basic", emoji: "◌" },
  { id: "medium", label: "Medium", emoji: "✦" },
  { id: "deep", label: "Deep", emoji: "❋" },
] as const;

const languages = [
  { id: "English", label: "English" },
  { id: "Azərbaycan", label: "Azərbaycan" },
  { id: "Русский", label: "Русский" },
];

function HomePage() {
  const navigate = useNavigate();
  const [topic, setTopic] = useState("");
  const [depth, setDepth] = useState<"basic" | "medium" | "deep">("medium");
  const [language, setLanguage] = useState("English");
  const [notes, setNotes] = useState("");
  const [notesOpen, setNotesOpen] = useState(false);
  const [sessions, setSessions] = useState<Session[] | null>(null);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let alive = true;
    api.getSessions()
      .then((s) => alive && setSessions(s))
      .catch(() => alive && setSessions([]))
      .finally(() => alive && setLoadingSessions(false));
    return () => { alive = false; };
  }, []);

  const begin = async () => {
    if (!topic.trim()) {
      toast.error("Please enter a topic ⊹");
      return;
    }
    setSubmitting(true);
    try {
      const { id } = await api.startResearch({
        topic: topic.trim(),
        additional_instructions: notes.trim() || undefined,
        depth,
        language,
      });
      toast.success("Research begun ✿");
      navigate({ to: "/research/$sessionId/live", params: { sessionId: id } });
    } catch (e) {
      toast.error("Couldn't reach the research garden ✗");
      setSubmitting(false);
    }
  };

  const removeSession = async (id: string) => {
    try {
      await api.deleteSession(id);
      setSessions((s) => (s ?? []).filter((x) => x.id !== id));
      toast.success("Removed ⊹");
    } catch {
      toast.error("Couldn't delete ✗");
    }
  };

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-5xl px-6 pb-24 pt-10 sm:pt-16">
        {/* Hero */}
        <section className="text-center animate-fade-up">
          <p className="font-accent text-lg italic text-[color:var(--color-dusty)]">⊹ ✦ ⊹</p>
          <h1 className="mt-3 font-display text-5xl font-semibold leading-tight sm:text-6xl md:text-7xl">
            Research anything,{" "}
            <span className="text-gradient-primary">beautifully.</span>
          </h1>
          <p className="mt-5 font-accent text-xl italic text-muted-foreground">
            Your aesthetic AI research companion ✦
          </p>
        </section>

        {/* Search */}
        <section className="mt-12 animate-fade-up" style={{ animationDelay: "80ms" }}>
          <div className="gradient-border mx-auto max-w-3xl rounded-full p-[2px] shadow-soft">
            <input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && begin()}
              placeholder="What shall we explore today? ✿"
              className="w-full rounded-full bg-background px-7 py-5 font-sans text-lg text-foreground placeholder:text-muted-foreground/70 focus:outline-none"
            />
          </div>

          {/* Options */}
          <div className="mx-auto mt-6 flex max-w-3xl flex-wrap items-center justify-center gap-3">
            <div className="flex rounded-full border border-border bg-card p-1">
              {depths.map((d) => (
                <button
                  key={d.id}
                  onClick={() => setDepth(d.id)}
                  className={`rounded-full px-4 py-2 text-sm font-medium transition-all duration-300 ${
                    depth === d.id ? "bg-gradient-primary text-white shadow-glow" : "text-foreground/80 hover:text-foreground"
                  }`}
                >
                  {d.emoji} {d.label}
                </button>
              ))}
            </div>

            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="rounded-full border border-border bg-card px-4 py-2.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {languages.map((l) => (
                <option key={l.id} value={l.id}>{l.label}</option>
              ))}
            </select>

            <button
              onClick={() => setNotesOpen((o) => !o)}
              className="rounded-full border border-border bg-card px-4 py-2.5 text-sm font-medium hover:bg-secondary transition"
            >
              Additional notes ⊹ {notesOpen ? "▴" : "▾"}
            </button>
          </div>

          {notesOpen && (
            <div className="mx-auto mt-4 max-w-3xl animate-fade-up">
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                placeholder="Any special focus, perspective, or sources to prioritize…"
                className="w-full rounded-2xl border border-border bg-card px-5 py-4 text-sm text-foreground placeholder:text-muted-foreground/70 focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
          )}

          <div className="mt-8 flex justify-center">
            <button
              onClick={begin}
              disabled={submitting}
              className="rounded-full bg-gradient-primary px-10 py-4 font-display text-lg font-semibold text-white shadow-glow transition-all duration-300 hover:scale-[1.03] disabled:opacity-60 disabled:hover:scale-100"
            >
              {submitting ? "Beginning… ◌" : "Begin Research ✿"}
            </button>
          </div>
        </section>

        {/* Past explorations */}
        <section className="mt-20">
          <div className="mb-6 flex items-end justify-between">
            <h2 className="font-display text-3xl">
              Past Explorations <span className="text-[color:var(--color-dusty)]">✦</span>
            </h2>
          </div>

          {loadingSessions ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {[0, 1, 2, 3].map((i) => (
                <div key={i} className="h-28 animate-soft-pulse rounded-2xl bg-card" />
              ))}
            </div>
          ) : !sessions || sessions.length === 0 ? (
            <div className="rounded-3xl border border-border bg-card p-12 text-center">
              <p className="text-3xl">✿</p>
              <p className="mt-3 font-display text-xl">No explorations yet</p>
              <p className="mt-1 font-accent text-base italic text-muted-foreground">
                Begin your first research above ⊹
              </p>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {sessions.map((s) => (
                <div key={s.id} className="group relative rounded-2xl border border-border bg-card p-5 hover-lift">
                  <Link
                    to={s.status === "done" ? "/research/$sessionId/report" : "/research/$sessionId/live"}
                    params={{ sessionId: s.id }}
                    className="block"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <h3 className="font-display text-lg leading-tight line-clamp-2">{s.topic}</h3>
                      <StatusBadge status={s.status} />
                    </div>
                    <p className="mt-3 font-accent text-sm italic text-muted-foreground">
                      {s.created_at ? new Date(s.created_at).toLocaleString() : ""}
                      {s.depth ? ` · ${s.depth}` : ""}
                    </p>
                  </Link>
                  <button
                    onClick={() => removeSession(s.id)}
                    className="absolute right-3 top-3 rounded-full px-2 py-1 text-xs text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100 hover:text-[color:var(--color-berry)]"
                    aria-label="Delete"
                  >
                    ✗
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>

        <p className="mt-20 text-center font-accent text-sm italic text-muted-foreground">
          ⊹ ✧ ˚ · made with care · ˚ ✧ ⊹
        </p>
      </main>
    </div>
  );
}
