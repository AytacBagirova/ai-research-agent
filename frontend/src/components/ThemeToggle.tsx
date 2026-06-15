import { useTheme } from "@/lib/theme";

export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  const isDark = theme === "dark";
  return (
    <button
      onClick={toggle}
      aria-label="Toggle theme"
      className="relative inline-flex h-10 w-10 items-center justify-center rounded-full border border-border bg-card backdrop-blur transition-all duration-300 hover:shadow-glow hover:scale-105"
    >
      <span className="text-lg transition-transform duration-500" style={{ transform: isDark ? "rotate(0deg)" : "rotate(-180deg)" }}>
        {isDark ? "☾" : "☀"}
      </span>
    </button>
  );
}
