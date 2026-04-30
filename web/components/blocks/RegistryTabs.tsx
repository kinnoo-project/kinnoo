"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";

import { fetchAgentSecurityReport, type AgentSummary } from "../../lib/registry-client";

type RegistryView = "my-agents" | "search";

type RegistryTabsProps = {
  activeView: RegistryView;
  searchQuery: string;
  showOnlyMyAgents: boolean;
  onSearchQueryChange: (value: string) => void;
  onShowOnlyMyAgentsChange: (checked: boolean) => void;
  myAgentsState: {
    isLoading: boolean;
    error: string | null;
    agents: AgentSummary[];
  };
  searchState: {
    isLoading: boolean;
    error: string | null;
    agents: AgentSummary[];
  };
  onAgentNameClick: (agent: AgentSummary, source: "my-agents" | "search") => void;
};

type AgentSecurityIcon = "🔏" | "❌" | "";

const panelMotion = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -6 },
  transition: { duration: 0.16, ease: "easeOut" as const },
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

function AgentTable({
  agents,
  source,
  securityIcons,
  onAgentNameClick,
}: {
  agents: AgentSummary[];
  source: "my-agents" | "search";
  securityIcons: Record<string, AgentSecurityIcon>;
  onAgentNameClick: (agent: AgentSummary, source: "my-agents" | "search") => void;
}) {
  const iconTooltip = (icon: AgentSecurityIcon): string => {
    if (icon === "🔏") {
      return "Agent archive signed with publisher private key.";
    }
    if (icon === "❌") {
      return "Agent archive failed integrity verification (corrupted or tampered).";
    }
    return "";
  };

  return (
    <div className="mt-3 overflow-x-auto rounded-card border border-white/15">
      <table className="min-w-full border-collapse text-left text-sm text-kinnoo-text">
        <thead className="bg-black/35 text-xs uppercase tracking-[0.08em] text-white/70">
          <tr>
            <th className="px-3 py-2">Tenant</th>
            <th className="px-3 py-2">Name</th>
            <th className="px-3 py-2">Version</th>
            <th className="px-3 py-2">Author</th>
            <th className="px-3 py-2">Framework</th>
            <th className="px-3 py-2">Size</th>
            <th className="px-3 py-2">Description</th>
          </tr>
        </thead>
        <tbody>
          {agents.map((agent) => (
            <tr
              key={`${agent.tenant_slug}/${agent.agent_slug}/${agent.version}`}
              className="border-t border-white/10 align-top"
            >
              <td className="px-3 py-2">{agent.tenant_slug}</td>
              <td className="px-3 py-2">
                <button
                  type="button"
                  onClick={() => onAgentNameClick(agent, source)}
                  className="text-left text-kinnoo-accent transition hover:text-[#60A5FA] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent"
                >
                  <span className="underline decoration-kinnoo-accent/50 underline-offset-2">
                    {agent.agent_slug}
                  </span>
                  {securityIcons[`${agent.tenant_slug}/${agent.agent_slug}/${agent.version}`] ? (
                    <span
                      aria-label={iconTooltip(
                        securityIcons[`${agent.tenant_slug}/${agent.agent_slug}/${agent.version}`],
                      )}
                      title={iconTooltip(
                        securityIcons[`${agent.tenant_slug}/${agent.agent_slug}/${agent.version}`],
                      )}
                      className="text-base"
                    >
                      {"\u00A0\u00A0"}
                      {securityIcons[`${agent.tenant_slug}/${agent.agent_slug}/${agent.version}`]}
                    </span>
                  ) : null}
                </button>
              </td>
              <td className="px-3 py-2">{agent.version}</td>
              <td className="px-3 py-2">{agent.author ?? "Unknown"}</td>
              <td className="px-3 py-2">{agent.framework ?? "Unknown"}</td>
              <td className="px-3 py-2">{formatSize(agent.size)}</td>
              <td className="px-3 py-2">{agent.description ?? "No description provided."}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function RegistryTabs({
  activeView,
  searchQuery,
  showOnlyMyAgents,
  onSearchQueryChange,
  onShowOnlyMyAgentsChange,
  myAgentsState,
  searchState,
  onAgentNameClick,
}: RegistryTabsProps) {
  const [securityIcons, setSecurityIcons] = useState<Record<string, AgentSecurityIcon>>({});

  const candidateAgents = useMemo(() => {
    const merged = [...myAgentsState.agents, ...searchState.agents];
    const deduped = new Map<string, AgentSummary>();
    for (const agent of merged) {
      const key = `${agent.tenant_slug}/${agent.agent_slug}/${agent.version}`;
      if (!deduped.has(key)) {
        deduped.set(key, agent);
      }
    }
    return Array.from(deduped.values());
  }, [myAgentsState.agents, searchState.agents]);

  useEffect(() => {
    let cancelled = false;

    const pendingAgents = candidateAgents.filter((agent) => {
      const key = `${agent.tenant_slug}/${agent.agent_slug}/${agent.version}`;
      return !(key in securityIcons) && Boolean(agent.version);
    });

    if (pendingAgents.length === 0) {
      return;
    }

    const loadSecurityIcons = async () => {
      const updates: Record<string, AgentSecurityIcon> = {};

      await Promise.all(
        pendingAgents.map(async (agent) => {
          const key = `${agent.tenant_slug}/${agent.agent_slug}/${agent.version}`;
          try {
            const report = await fetchAgentSecurityReport(
              agent.tenant_slug,
              agent.agent_slug,
              agent.version,
            );

            const checks = Array.isArray(report.checks) ? report.checks : [];
            const signaturePass = checks.some(
              (check) => check.check_name === "signature" && check.status.toLowerCase() === "pass",
            );
            const archiveIntegrityFail = checks.some(
              (check) =>
                (check.check_name === "archive_integrity" || check.check_name === "archive") &&
                check.status.toLowerCase() === "fail",
            );
            const perFileIntegrityFail = checks.some(
              (check) =>
                (check.check_name === "per_file_integrity" || check.check_name === "per_file") &&
                check.status.toLowerCase() === "fail",
            );

            if (archiveIntegrityFail || perFileIntegrityFail) {
              updates[key] = "❌";
              return;
            }

            if (signaturePass) {
              updates[key] = "🔏";
              return;
            }

            updates[key] = "";
          } catch {
            updates[key] = "";
          }
        }),
      );

      if (!cancelled && Object.keys(updates).length > 0) {
        setSecurityIcons((current) => ({ ...current, ...updates }));
      }
    };

    void loadSecurityIcons();

    return () => {
      cancelled = true;
    };
  }, [candidateAgents, securityIcons]);

  return (
    <AnimatePresence mode="wait" initial={false}>
      {activeView === "my-agents" ? (
        <motion.section
          key="my-agents"
          {...panelMotion}
          aria-live="polite"
          className="rounded-card border border-white/15 bg-[#222222] p-5"
          data-testid="registry-my-agents-view"
        >
          <h1 className="text-2xl font-semibold text-kinnoo-text">My Agents</h1>
          {myAgentsState.isLoading ? (
            <p className="mt-2 text-sm text-white/70">Loading agents...</p>
          ) : myAgentsState.error ? (
            <p role="alert" className="mt-2 text-sm text-red-300">
              {myAgentsState.error}
            </p>
          ) : myAgentsState.agents.length === 0 ? (
            <p className="mt-2 text-sm text-white/70">No agents published yet.</p>
          ) : (
            <AgentTable
              agents={myAgentsState.agents}
              source="my-agents"
              securityIcons={securityIcons}
              onAgentNameClick={onAgentNameClick}
            />
          )}
        </motion.section>
      ) : (
        <motion.section
          key="search"
          {...panelMotion}
          aria-live="polite"
          className="space-y-4 rounded-card border border-white/15 bg-[#222222] p-5"
          data-testid="registry-search-view"
        >
          <h1 className="text-2xl font-semibold text-kinnoo-text">Search</h1>
          <div className="space-y-3">
            <label htmlFor="registry-search-query" className="block text-sm font-medium text-white/85">
              Search public agents
            </label>
            <input
              id="registry-search-query"
              name="searchQuery"
              type="text"
              value={searchQuery}
              onChange={(event) => onSearchQueryChange(event.target.value)}
              placeholder="Search by tenant, name, framework..."
              className="w-full rounded-button border border-white/20 bg-black/35 px-3 py-2 text-sm text-kinnoo-text placeholder:text-white/45 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent"
            />
            <label className="inline-flex items-center gap-2 text-sm text-white/80">
              <input
                type="checkbox"
                checked={showOnlyMyAgents}
                onChange={(event) => onShowOnlyMyAgentsChange(event.target.checked)}
                className="h-4 w-4 rounded border-white/30 bg-black/35 text-kinnoo-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent"
              />
              Show only my agents
            </label>

            {searchState.isLoading ? (
              <p className="text-sm text-white/70">Loading search results...</p>
            ) : searchState.error ? (
              <p role="alert" className="text-sm text-red-300">
                {searchState.error}
              </p>
            ) : searchState.agents.length === 0 ? (
              <p className="text-sm text-white/70">No matching agents found.</p>
            ) : (
              <AgentTable
                agents={searchState.agents}
                source="search"
                securityIcons={securityIcons}
                onAgentNameClick={onAgentNameClick}
              />
            )}
          </div>
        </motion.section>
      )}
    </AnimatePresence>
  );
}
