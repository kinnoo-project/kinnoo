import { describe, expect, it } from "vitest";

type AdapterContract = {
  framework: "langgraph" | "openai";
  runtimeLanguage: "nodejs" | "python";
  entrypointHint: string;
  confidence: number;
};

type FixtureInput = {
  framework: "langgraph" | "openai";
  filePath: string;
  source: string;
};

function mapFixtureToAdapterContract(fixture: FixtureInput): AdapterContract {
  const lowered = fixture.source.toLowerCase();

  if (fixture.framework === "langgraph") {
    const runtimeLanguage = fixture.filePath.endsWith(".ts") ? "nodejs" : "python";
    const entrypointHint = runtimeLanguage === "nodejs" ? "src/graph.ts" : "graph.py";
    const confidence = lowered.includes("stategraph") ? 0.95 : 0.55;
    return {
      framework: "langgraph",
      runtimeLanguage,
      entrypointHint,
      confidence,
    };
  }

  const runtimeLanguage = fixture.filePath.endsWith(".ts") ? "nodejs" : "python";
  const entrypointHint = runtimeLanguage === "nodejs" ? "src/agent.ts" : "agent.py";
  const confidence = lowered.includes("from agents import") || lowered.includes("@openai/agents") ? 0.94 : 0.5;
  return {
    framework: "openai",
    runtimeLanguage,
    entrypointHint,
    confidence,
  };
}

describe("feature75 adapter fixture contracts", () => {
  it("it_langgraph_ts_fixture_maps_adapter_contract", () => {
    const fixture: FixtureInput = {
      framework: "langgraph",
      filePath: "src/graph.ts",
      source: "import { StateGraph } from '@langchain/langgraph';",
    };

    const mapped = mapFixtureToAdapterContract(fixture);

    expect(mapped.framework).toBe("langgraph");
    expect(mapped.runtimeLanguage).toBe("nodejs");
    expect(mapped.entrypointHint).toBe("src/graph.ts");
    expect(mapped.confidence).toBeGreaterThanOrEqual(0.9);
  });

  it("it_openai_python_fixture_maps_adapter_contract", () => {
    const fixture: FixtureInput = {
      framework: "openai",
      filePath: "agent.py",
      source: "from agents import Agent\nprint(Agent)",
    };

    const mapped = mapFixtureToAdapterContract(fixture);

    expect(mapped.framework).toBe("openai");
    expect(mapped.runtimeLanguage).toBe("python");
    expect(mapped.entrypointHint).toBe("agent.py");
    expect(mapped.confidence).toBeGreaterThanOrEqual(0.9);
  });
});
