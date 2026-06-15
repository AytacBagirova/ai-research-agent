export interface Source {
  title: string;
  url: string;
  type?: string;
  credibility?: number; // 0..1
  snippet?: string;
}

const typeEmoji = (t?: string) => {
  switch ((t || "").toLowerCase()) {
    case "arxiv": return "❋";
    case "pdf": return "✾";
    case "wikipedia": case "wiki": return "◈";
    default: return "✦";
  }
};

export function SourceCard({ source }: { source: Source }) {
  const cred = Math.max(0, Math.min(1, source.credibility ?? 0.7));
  return (
    <a
      href={source.url}
      target="_blank"
      rel="noreferrer"
      className="block rounded-2xl border border-border bg-card p-4 hover-lift animate-fade-up"
    >
      <div className="flex items-start gap-3">
        <span className="text-xl text-[color:var(--color-dusty)]">{typeEmoji(source.type)}</span>
        <div className="min-w-0 flex-1">
          <h4 className="font-display text-base leading-snug line-clamp-2">{source.title || source.url}</h4>
          <p className="mt-1 truncate font-accent text-sm text-muted-foreground">{source.url}</p>
          {source.snippet && (
            <p className="mt-2 text-sm text-foreground/80 line-clamp-2">{source.snippet}</p>
          )}
          <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-gradient-soft"
              style={{ width: `${cred * 100}%` }}
            />
          </div>
        </div>
      </div>
    </a>
  );
}
