type Status = "done" | "running" | "failed" | "pending";

const map: Record<Status, { emoji: string; label: string; cls: string }> = {
  done:    { emoji: "✿", label: "Done",    cls: "bg-[color:var(--color-rose)]/30 text-[color:var(--color-burgundy)] dark:text-[color:var(--color-peach)]" },
  running: { emoji: "◌", label: "Running", cls: "bg-gradient-primary text-white animate-soft-pulse" },
  failed:  { emoji: "✗", label: "Failed",  cls: "bg-[color:var(--color-berry)]/20 text-[color:var(--color-berry)]" },
  pending: { emoji: "⊹", label: "Pending", cls: "bg-muted text-muted-foreground" },
};

export function StatusBadge({ status }: { status: string }) {
  const key = (["done", "running", "failed", "pending"].includes(status) ? status : "pending") as Status;
  const s = map[key];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${s.cls}`}>
      <span>{s.emoji}</span>
      <span className="font-accent text-sm tracking-wide">{s.label}</span>
    </span>
  );
}
