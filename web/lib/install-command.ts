import type { AgentSummary } from "./registry-client";

export function buildInstallCommand(agent: Pick<AgentSummary, "tenant_slug" | "agent_slug" | "version">): string {
  return `kinnoo install ${agent.tenant_slug}/${agent.agent_slug}==${agent.version}`;
}
