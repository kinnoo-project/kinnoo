"use client";

import { useEffect, useState } from "react";

import RegistryNav from "../../../components/blocks/RegistryNav";
import AgentManifestModal from "../../../components/blocks/AgentManifestModal";
import RegistryTabs from "../../../components/blocks/RegistryTabs";
import { fetchMyAgents, searchAgents, type AgentSummary } from "../../../lib/registry-client";

type RegistryDataState = {
  isLoading: boolean;
  error: string | null;
  agents: AgentSummary[];
};

export default function RegistryPage() {
  const [activeView, setActiveView] = useState<"my-agents" | "search">("my-agents");
  const [searchQuery, setSearchQuery] = useState("");
  const [showOnlyMyAgents, setShowOnlyMyAgents] = useState(false);
  const [myAgentsState, setMyAgentsState] = useState<RegistryDataState>({
    isLoading: true,
    error: null,
    agents: [],
  });
  const [searchState, setSearchState] = useState<RegistryDataState>({
    isLoading: false,
    error: null,
    agents: [],
  });
  const [selectedAgent, setSelectedAgent] = useState<AgentSummary | null>(null);
  const [selectedSource, setSelectedSource] = useState<"my-agents" | "search" | null>(null);

  useEffect(() => {
    let cancelled = false;

    const loadMyAgents = async () => {
      setMyAgentsState({ isLoading: true, error: null, agents: [] });
      try {
        const agents = await fetchMyAgents();
        if (!cancelled) {
          setMyAgentsState({ isLoading: false, error: null, agents });
        }
      } catch {
        if (!cancelled) {
          setMyAgentsState({
            isLoading: false,
            error: "Unable to load your agents right now.",
            agents: [],
          });
        }
      }
    };

    void loadMyAgents();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (activeView !== "search") {
      return;
    }

    if (!searchQuery.trim()) {
      setSearchState({ isLoading: false, error: null, agents: [] });
      return;
    }

    let cancelled = false;

    const loadSearchResults = async () => {
      setSearchState((current) => ({ ...current, isLoading: true, error: null }));
      try {
        const agents = await searchAgents({ query: searchQuery, showOnlyMine: showOnlyMyAgents });
        if (!cancelled) {
          setSearchState({ isLoading: false, error: null, agents });
        }
      } catch {
        if (!cancelled) {
          setSearchState({
            isLoading: false,
            error: "Unable to search agents right now.",
            agents: [],
          });
        }
      }
    };

    void loadSearchResults();

    return () => {
      cancelled = true;
    };
  }, [activeView, searchQuery, showOnlyMyAgents]);

  return (
    <div className="space-y-6">
      <RegistryNav activeView={activeView} onSelectView={setActiveView} />
      <RegistryTabs
        activeView={activeView}
        searchQuery={searchQuery}
        showOnlyMyAgents={showOnlyMyAgents}
        onSearchQueryChange={setSearchQuery}
        onShowOnlyMyAgentsChange={setShowOnlyMyAgents}
        myAgentsState={myAgentsState}
        searchState={searchState}
        onAgentNameClick={(agent, source) => {
          setSelectedAgent(agent);
          setSelectedSource(source);
        }}
      />

      <AgentManifestModal
        selectedAgent={selectedAgent}
        selectedSource={selectedSource}
        onClose={() => {
          setSelectedAgent(null);
          setSelectedSource(null);
        }}
      />
    </div>
  );
}
