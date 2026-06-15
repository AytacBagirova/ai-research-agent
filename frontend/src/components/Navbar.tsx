import { Link } from "@tanstack/react-router";
import { ThemeToggle } from "./ThemeToggle";

export function Navbar() {
  return (
    <header className="sticky top-0 z-40 backdrop-blur-md" style={{ background: "color-mix(in oklab, var(--color-background) 75%, transparent)" }}>
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link to="/" className="group flex items-center gap-2">
          <span className="text-2xl text-gradient-primary transition-transform duration-300 group-hover:rotate-12">✿</span>
          <span className="font-display text-xl font-semibold tracking-tight">Cute Researcher</span>
        </Link>
        <ThemeToggle />
      </div>
    </header>
  );
}
