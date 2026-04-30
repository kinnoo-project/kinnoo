"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { buildInstallCommand } from "../../lib/install-command";
import {
  fetchAgentDetail,
  fetchAgentSecurityReport,
  type AgentDetail,
  type AgentSecurityReport,
  type AgentSummary,
} from "../../lib/registry-client";

type AgentManifestModalProps = {
  selectedAgent: AgentSummary | null;
  selectedSource: "my-agents" | "search" | null;
  onClose: () => void;
};

export default function AgentManifestModal({
  selectedAgent,
  selectedSource,
  onClose,
}: AgentManifestModalProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<AgentDetail | null>(null);
  const [securityReport, setSecurityReport] = useState<AgentSecurityReport | null>(null);
  const [copied, setCopied] = useState(false);
  const [activeManifestTab, setActiveManifestTab] = useState<"registry" | "agent" | "versions" | "security">("registry");

  useEffect(() => {
    if (!selectedAgent) {
      setIsLoading(false);
      setError(null);
      setDetail(null);
      setSecurityReport(null);
      setCopied(false);
      setActiveManifestTab("registry");
      return;
    }

    let cancelled = false;

    const loadDetail = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const nextDetail = await fetchAgentDetail(selectedAgent.tenant_slug, selectedAgent.agent_slug);
        const version = selectedAgent.version;
        let nextSecurityReport: AgentSecurityReport | null = null;
        if (version) {
          try {
            nextSecurityReport = await fetchAgentSecurityReport(
              selectedAgent.tenant_slug,
              selectedAgent.agent_slug,
              version,
            );
          } catch {
            nextSecurityReport = {
              tenant_slug: selectedAgent.tenant_slug,
              agent_slug: selectedAgent.agent_slug,
              version,
              checks: [],
            };
          }
        }
        if (!cancelled) {
          setDetail(nextDetail);
          setSecurityReport(nextSecurityReport);
        }
      } catch {
        if (!cancelled) {
          setError("Unable to load agent manifest details right now.");
          setDetail(null);
          setSecurityReport(null);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void loadDetail();

    return () => {
      cancelled = true;
    };
  }, [selectedAgent]);

  const prettyRegistryManifest = useMemo(() => {
    if (!detail) {
      return "";
    }

    // Keep Registry Manifest focused on registry metadata only.
    const { agent_manifest: _agentManifest, manifest: _manifest, ...registryManifestOnly } = detail;
    return JSON.stringify(registryManifestOnly, null, 2);
  }, [detail]);

  const resolvedAgentManifest = useMemo(() => {
    if (!detail || typeof detail !== "object") {
      return null;
    }

    if (
      "agent_manifest" in detail &&
      detail.agent_manifest &&
      typeof detail.agent_manifest === "object" &&
      !Array.isArray(detail.agent_manifest)
    ) {
      return detail.agent_manifest;
    }

    if (
      "manifest" in detail &&
      detail.manifest &&
      typeof detail.manifest === "object" &&
      !Array.isArray(detail.manifest)
    ) {
      return detail.manifest;
    }

    return null;
  }, [detail]);

  const prettyAgentManifest = useMemo(() => {
    if (!resolvedAgentManifest) {
      return "";
    }
    return JSON.stringify(resolvedAgentManifest, null, 2);
  }, [resolvedAgentManifest]);

  const versions = useMemo(() => {
    const raw = detail?.versions;
    if (!Array.isArray(raw)) {
      return [] as Array<{ version: string; created_at: string; updated_at: string }>;
    }
    return raw
      .map((row) => {
        if (!row || typeof row !== "object") {
          return null;
        }
        const item = row as Record<string, unknown>;
        const version = typeof item.version === "string" ? item.version : "";
        if (!version) {
          return null;
        }
        return {
          version,
          created_at: typeof item.created_at === "string" ? item.created_at : "",
          updated_at: typeof item.updated_at === "string" ? item.updated_at : "",
        };
      })
      .filter((row): row is { version: string; created_at: string; updated_at: string } => row !== null);
  }, [detail]);

  const securityChecks = useMemo(() => {
    const checks = securityReport?.checks;
    if (!Array.isArray(checks)) {
      return [] as Array<{ check_name: string; status: string; detail: string }>;
    }
    return checks
      .map((row) => {
        if (!row || typeof row !== "object") {
          return null;
        }
        const item = row as Record<string, unknown>;
        return {
          check_name: typeof item.check_name === "string" ? item.check_name : "",
          status: typeof item.status === "string" ? item.status.toLowerCase() : "",
          detail: typeof item.detail === "string" ? item.detail : "",
        };
      })
      .filter((row): row is { check_name: string; status: string; detail: string } => Boolean(row && row.check_name));
  }, [securityReport]);

  const installCommand = useMemo(() => {
    if (!selectedAgent) {
      return null;
    }
    return buildInstallCommand(selectedAgent);
  }, [selectedAgent]);

  const handleCopyInstallCommand = async () => {
    if (!installCommand) {
      return;
    }

    await navigator.clipboard.writeText(installCommand);
    setCopied(true);
    window.setTimeout(() => {
      setCopied(false);
    }, 1200);
  };

  return (
    <Dialog.Root open={Boolean(selectedAgent)} onOpenChange={(open) => (!open ? onClose() : undefined)}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/70" />
        <Dialog.Content className="fixed left-1/2 top-1/2 w-[min(52rem,calc(100vw-2rem))] -translate-x-1/2 -translate-y-1/2 rounded-card border border-white/15 bg-[#222222] p-5 shadow-xl">
          <div className="mb-4 flex items-start justify-between gap-3">
            <div>
              <Dialog.Title className="text-lg font-semibold text-kinnoo-text">Agent Manifest</Dialog.Title>
              <Dialog.Description className="text-sm text-white/70">
                {selectedAgent
                  ? `${selectedAgent.tenant_slug}/${selectedAgent.agent_slug}`
                  : "No agent selected"}
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button
                type="button"
                aria-label="Close manifest modal"
                onClick={onClose}
                className="inline-flex h-8 w-8 items-center justify-center rounded-button border border-white/20 text-white/80 transition hover:border-kinnoo-accent hover:text-kinnoo-accent"
              >
                <X size={16} />
              </button>
            </Dialog.Close>
          </div>

          {isLoading ? <p className="text-sm text-white/70">Loading manifest details...</p> : null}
          {error ? (
            <p role="alert" className="text-sm text-red-300">
              {error}
            </p>
          ) : null}
          {!isLoading && !error && detail ? (
            <div>
              <div className="mb-2 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setActiveManifestTab("registry")}
                  className={`rounded-button border px-3 py-1 text-xs font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent ${
                    activeManifestTab === "registry"
                      ? "border-kinnoo-accent bg-kinnoo-accent/15 text-kinnoo-accent"
                      : "border-white/20 text-white/75 hover:border-white/35 hover:text-white"
                  }`}
                >
                  Registry Manifest
                </button>
                <button
                  type="button"
                  onClick={() => setActiveManifestTab("agent")}
                  className={`rounded-button border px-3 py-1 text-xs font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent ${
                    activeManifestTab === "agent"
                      ? "border-kinnoo-accent bg-kinnoo-accent/15 text-kinnoo-accent"
                      : "border-white/20 text-white/75 hover:border-white/35 hover:text-white"
                  }`}
                >
                  Agent Manifest
                </button>
                <button
                  type="button"
                  onClick={() => setActiveManifestTab("versions")}
                  className={`rounded-button border px-3 py-1 text-xs font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent ${
                    activeManifestTab === "versions"
                      ? "border-kinnoo-accent bg-kinnoo-accent/15 text-kinnoo-accent"
                      : "border-white/20 text-white/75 hover:border-white/35 hover:text-white"
                  }`}
                >
                  Agent Versions
                </button>
                <button
                  type="button"
                  onClick={() => setActiveManifestTab("security")}
                  className={`rounded-button border px-3 py-1 text-xs font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent ${
                    activeManifestTab === "security"
                      ? "border-kinnoo-accent bg-kinnoo-accent/15 text-kinnoo-accent"
                      : "border-white/20 text-white/75 hover:border-white/35 hover:text-white"
                  }`}
                >
                  Security
                </button>
              </div>

              {activeManifestTab === "registry" ? (
                <pre className="max-h-[55vh] overflow-auto rounded-card border border-white/10 bg-black/35 p-3 text-xs text-white/85">
                  {prettyRegistryManifest}
                </pre>
              ) : activeManifestTab === "agent" && resolvedAgentManifest ? (
                <pre className="max-h-[55vh] overflow-auto rounded-card border border-white/10 bg-black/35 p-3 text-xs text-white/85">
                  {prettyAgentManifest}
                </pre>
              ) : activeManifestTab === "agent" ? (
                <div className="rounded-card border border-white/10 bg-black/35 p-3 text-xs text-white/70">
                  Agent manifest (kinnoo.yaml) is not available for this record.
                </div>
              ) : activeManifestTab === "versions" ? (
                versions.length > 0 ? (
                  <div className="max-h-[55vh] overflow-auto rounded-card border border-white/10 bg-black/35 p-3 text-xs text-white/85">
                    <table className="min-w-full border-collapse text-left text-xs text-kinnoo-text">
                      <thead className="bg-black/35 text-[11px] uppercase tracking-[0.08em] text-white/70">
                        <tr>
                          <th className="px-2 py-1">Version</th>
                          <th className="px-2 py-1">Created</th>
                          <th className="px-2 py-1">Updated</th>
                        </tr>
                      </thead>
                      <tbody>
                        {versions.map((row) => (
                          <tr key={row.version} className="border-t border-white/10 align-top">
                            <td className="px-2 py-1">{row.version}</td>
                            <td className="px-2 py-1">{row.created_at || "N/A"}</td>
                            <td className="px-2 py-1">{row.updated_at || "N/A"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="rounded-card border border-white/10 bg-black/35 p-3 text-xs text-white/70">
                    Version history is not available for this agent.
                  </div>
                )
              ) : securityChecks.length > 0 ? (
                <div className="max-h-[55vh] overflow-auto rounded-card border border-white/10 bg-black/35 p-3 text-xs text-white/85">
                  <table className="min-w-full border-collapse text-left text-xs text-kinnoo-text">
                    <thead className="bg-black/35 text-[11px] uppercase tracking-[0.08em] text-white/70">
                      <tr>
                        <th className="px-2 py-1">Check</th>
                        <th className="px-2 py-1">Result</th>
                        <th className="px-2 py-1">Detail</th>
                      </tr>
                    </thead>
                    <tbody>
                      {securityChecks.map((row) => (
                        <tr key={row.check_name} className="border-t border-white/10 align-top">
                          <td className="px-2 py-1">{row.check_name}</td>
                          <td className="px-2 py-1">
                            {row.status === "pass"
                              ? "[PASS]"
                              : row.status === "unsigned"
                                ? "[UNSIGNED]"
                                : row.status === "fail"
                                  ? "[FAIL]"
                                  : "[UNKNOWN]"}
                          </td>
                          <td className="px-2 py-1">{row.detail || ""}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="rounded-card border border-white/10 bg-black/35 p-3 text-xs text-white/70">
                  Security report is not available for this version.
                </div>
              )}
            </div>
          ) : null}

          {installCommand ? (
            <div className="mt-4 rounded-card border-2 border-white/25 bg-[#222222] p-4 transition hover:border-[#FF7F00] card-border-1">
              <p className="mb-2 text-xs uppercase tracking-[0.18em] text-white/50">Terminal</p>
              <div className="flex items-center justify-between gap-3">
                <code className="text-sm text-kinnoo-text sm:text-base">{installCommand}</code>
                <button
                  type="button"
                  onClick={handleCopyInstallCommand}
                  className="rounded-button border border-white/20 px-3 py-1 text-sm font-medium text-kinnoo-text transition hover:border-kinnoo-accent hover:text-kinnoo-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent"
                >
                  {copied ? "Copied!" : "Copy"}
                </button>
              </div>
            </div>
          ) : null}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
