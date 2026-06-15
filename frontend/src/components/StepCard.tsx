import { useState } from "react";

export interface AgentStep {
  type: string; // thought | tool_use | tool_result | critique | final_report
  content?: string;
  tool?: string;
  timestamp?: string | number;
}

const stepMeta = (type: string) => {
  switch (type) {
    case "thought":      return { emoji: "♡", label: "Thought" };
    case "tool_use":     return { emoji: "✦", label: "Tool Use" };
    case "tool_result":  return { emoji: "✿", label: "Result" };
    case "critique":     return { emoji: "◈", label: "Critique" };
    case "final_report": return { emoji: "❋", label: "Final Report" };
    default:             return { emoji: "⊹", label: type };
  }
};

export function StepCard({ step }: { step: AgentStep }) {
  const [open, setOpen] = useState(false);
  const meta = stepMeta(step.type);
  const content = step.content ?? "";
  const long = content.length > 220;
  const shown = !open && long ? content.slice(0, 220) + "…" : content;

  const ts = step.timestamp
    ? new Date(typeof step.timestamp === "number" ? step.timestamp : step.timestamp).toLocaleTimeString()
    : "";

  return (
    <div className="rounded-2xl border border-border bg-card p-4 animate-fade-up hover-lift">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className="text-lg text-[color:var(--color-dusty)]">{meta.emoji}</span>
        <span className="font-display text-sm font-semibold">{meta.label}</span>
        {step.tool && (
          <span className="rounded-full bg-[color:var(--color-rose)]/40 px-2.5 py-0.5 font-accent text-xs text-[color:var(--color-burgundy)] dark:text-[color:var(--color-peach)]">
            {step.tool}
          </span>
        )}
        {ts && <span className="ml-auto font-accent text-xs italic text-muted-foreground">{ts}</span>}
      </div>
      {content && (
        <button
          onClick={() => long && setOpen((o) => !o)}
          className={`w-full text-left text-sm leading-relaxed text-foreground/90 ${long ? "cursor-pointer" : "cursor-default"}`}
        >
          <p className="whitespace-pre-wrap">{shown}</p>
          {long && (
            <span className="mt-1 inline-block font-accent text-xs text-[color:var(--color-dusty)]">
              {open ? "show less ⊹" : "show more ⊹"}
            </span>
          )}
        </button>
      )}
    </div>
  );
}
