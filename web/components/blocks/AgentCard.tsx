import type { AgentSummary } from "../../lib/registry-client";

type AgentCardProps = {
  agent: AgentSummary;
  onNameClick: (agent: AgentSummary) => void;
};

function formatSize(size?: number): string {
  if (typeof size !== "number" || Number.isNaN(size)) {
    return "Unknown";
  }

  if (size < 1024) {
    return `${size} B`;
  }

  const kb = size / 1024;
  if (kb < 1024) {
    return `${kb.toFixed(1)} KB`;
  }

  return `${(kb / 1024).toFixed(2)} MB`;
}

export default function AgentCard({ agent, onNameClick }: AgentCardProps) {
  return (
    <article className="rounded-card border border-white/15 bg-[#222222] p-4">
      <dl className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-white/60">Tenant</dt>
          <dd className="text-kinnoo-text">{agent.tenant_slug}</dd>
        </div>
        <div>
          <dt className="text-white/60">Name</dt>
          <dd>
            <button
              type="button"
              onClick={() => onNameClick(agent)}
              className="text-left text-kinnoo-accent underline decoration-kinnoo-accent/50 underline-offset-2 transition hover:text-[#60A5FA] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent"
            >
              {agent.agent_slug}
            </button>
          </dd>
        </div>
        <div>
          <dt className="text-white/60">Version</dt>
          <dd className="text-kinnoo-text">{agent.version}</dd>
        </div>
        <div>
          <dt className="text-white/60">Author</dt>
          <dd className="text-kinnoo-text">{agent.author ?? "Unknown"}</dd>
        </div>
        <div>
          <dt className="text-white/60">Framework</dt>
          <dd className="text-kinnoo-text">{agent.framework ?? "Unknown"}</dd>
        </div>
        <div>
          <dt className="text-white/60">Size</dt>
          <dd className="text-kinnoo-text">{formatSize(agent.size)}</dd>
        </div>
        <div className="sm:col-span-2">
          <dt className="text-white/60">Description</dt>
          <dd className="text-kinnoo-text">{agent.description ?? "No description provided."}</dd>
        </div>
      </dl>
    </article>
  );
}
