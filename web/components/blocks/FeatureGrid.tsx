type FeatureCard = {
  title: string;
  description: string;
};

const FEATURES: readonly FeatureCard[] = [
  {
    title: "Supports common AI agent frameworks",
    description:
      "Initialize, import, install and test AI agents developed with LangChain, LangGraph, PydanticAI, OpenAI Agents SDK, OpenClaw, and more.",
  },
  {
    title: "Hosted agent registry",
    description:
      "Publish agents to a hosted registry where others can search, inspect, and install them — like npm, but for agents.",
  },
  {
    title: "From Zero to Running in Seconds",
    description:
      "kinnoo install and kinnoo run — no README hunting, no venv setup, no env var guessing. Dependencies, runtime, and configuration are handled by kinnoo.",
  },
  {
    title: "Built for production workflows",
    description:
      "From simple one-shot agents to complex multi-agent handoffs, Kinnoo provides the standardized environment agents need to interact reliably. Package agents into portable units that run consistently from local dev to production.",
  },
  {
    title: "Security-first by design",
    description:
      "Signed archives, permission declarations, static security sweeps, dependency audits, preflight checks, runtime monitoring, and a kill switch - trust what you run.",
  },
  {
    title: "Inspect before you run",
    description:
      "Review agent manifests, dependencies, environment variables, permissions, service calls and cryptographic integrity of agent files before installation — no surprises.",
  },
] as const;

export default function FeatureGrid() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3" data-testid="feature-grid">
      {FEATURES.map((feature) => (
        <article
          key={feature.title}
          className="group min-h-40 overflow-hidden rounded-card border-2 border-white/25 bg-[#222222] p-5 transition hover:-translate-y-0.5 hover:border-[#FF7F00] focus-within:border-[#FF7F00] focus-within:ring-1 focus-within:ring-[#FF7F00]"
        >
          <h3 className="mb-3 text-xl font-semibold leading-snug text-[#F9FAFB]">{feature.title}</h3>
          <p className="text-sm leading-relaxed text-[#F9FAFB] sm:text-base">{feature.description}</p>
        </article>
      ))}
    </div>
  );
}
