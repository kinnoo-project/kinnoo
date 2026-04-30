type RegistryView = "my-agents" | "search";

type RegistryNavProps = {
  activeView: RegistryView;
  onSelectView: (view: RegistryView) => void;
};

const baseTabClass =
  "cursor-pointer rounded-button border px-4 py-2 text-sm font-medium transition hover:!border-[#FF7F00] hover:!text-[#FF7F00] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent";

export default function RegistryNav({
  activeView,
  onSelectView,
}: RegistryNavProps) {
  return (
    <nav
      aria-label="Registry navigation"
      className="flex flex-wrap items-center gap-2 rounded-card border border-white/15 bg-[#222222] p-3"
    >
      <button
        type="button"
        onClick={() => onSelectView("my-agents")}
        aria-pressed={activeView === "my-agents"}
        className={`${baseTabClass} border-white/20 bg-transparent text-white/80`}
      >
        My Agents
      </button>
      <button
        type="button"
        onClick={() => onSelectView("search")}
        aria-pressed={activeView === "search"}
        className={`${baseTabClass} border-white/20 bg-transparent text-white/80`}
      >
        Search
      </button>
    </nav>
  );
}
