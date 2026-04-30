export type AgentSummary = {
  tenant_slug: string;
  agent_slug: string;
  version: string;
  author?: string;
  framework?: string;
  size?: number;
  description?: string;
};

export type AgentDetail = {
  tenant_slug: string;
  agent_slug: string;
  versions?: unknown;
  metadata?: unknown;
  manifest?: unknown;
  agent_manifest?: unknown;
  [key: string]: unknown;
};

export type SecurityCheckRow = {
  check_name: string;
  status: string;
  detail?: string;
  timestamp?: string;
};

export type AgentSecurityReport = {
  tenant_slug: string;
  agent_slug: string;
  version: string;
  security_status?: unknown;
  checks: SecurityCheckRow[];
};

type SearchAgentsParams = {
  query: string;
  showOnlyMine: boolean;
};

type AgentsEnvelope = {
  items?: unknown;
};

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path, {
    method: "GET",
    credentials: "include",
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

function toAgentSummary(item: unknown): AgentSummary | null {
  if (!item || typeof item !== "object") {
    return null;
  }

  const row = item as Record<string, unknown>;
  const tenantSlug = typeof row.tenant_slug === "string" ? row.tenant_slug : "";
  const agentSlug =
    typeof row.agent_slug === "string"
      ? row.agent_slug
      : typeof row.name === "string"
        ? row.name
        : "";
  const version =
    typeof row.version === "string"
      ? row.version
      : typeof row.latest_version === "string"
        ? row.latest_version
        : "";

  if (!tenantSlug || !agentSlug) {
    return null;
  }

  const author = typeof row.author === "string" && row.author ? row.author : undefined;
  const framework = typeof row.framework === "string" && row.framework ? row.framework : undefined;
  const description =
    typeof row.description === "string" && row.description ? row.description : undefined;

  let size: number | undefined;
  if (typeof row.size === "number") {
    size = row.size;
  } else if (typeof row.archive_size_bytes === "number") {
    size = row.archive_size_bytes;
  }

  return {
    tenant_slug: tenantSlug,
    agent_slug: agentSlug,
    version,
    author,
    framework,
    size,
    description,
  };
}

function normalizeAgentSummaryList(payload: unknown): AgentSummary[] {
  const source = Array.isArray(payload)
    ? payload
    : payload && typeof payload === "object" && Array.isArray((payload as AgentsEnvelope).items)
      ? ((payload as AgentsEnvelope).items as unknown[])
      : [];

  return source.map(toAgentSummary).filter((item): item is AgentSummary => item !== null);
}

export async function fetchMyAgents(): Promise<AgentSummary[]> {
  const payload = await getJson<unknown>("/api/agents?show_only_mine=true");
  return normalizeAgentSummaryList(payload);
}

export async function searchAgents(params: SearchAgentsParams): Promise<AgentSummary[]> {
  const searchParams = new URLSearchParams();
  searchParams.set("q", params.query);
  if (params.showOnlyMine) {
    searchParams.set("show_only_mine", "true");
  }

  const queryString = searchParams.toString();
  const url = queryString.length > 0 ? `/api/search?${queryString}` : "/api/search";

  const payload = await getJson<unknown>(url);
  return normalizeAgentSummaryList(payload);
}

export async function fetchAgentDetail(
  tenantSlug: string,
  agentSlug: string,
): Promise<AgentDetail> {
  return getJson<AgentDetail>(`/api/agents/${tenantSlug}/${agentSlug}`);
}

export async function fetchAgentSecurityReport(
  tenantSlug: string,
  agentSlug: string,
  version: string,
): Promise<AgentSecurityReport> {
  return getJson<AgentSecurityReport>(
    `/api/agents/${tenantSlug}/${agentSlug}/${version}/security-report`,
  );
}
