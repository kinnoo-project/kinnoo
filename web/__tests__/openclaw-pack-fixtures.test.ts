import { describe, expect, it } from "vitest";

const REQUIRED_OPENCLAW_ENTRIES = [
  "kinnoo.yaml",
  "AGENTS.md",
  "skills/planner/SKILL.md",
  "memory/session/journal.md",
] as const;

const EXCLUDED_RUNTIME_PREFIXES = [
  ".git/",
  ".openclaw/",
  "node_modules/",
  "skills/.git/",
  "skills/node_modules/",
  "memory/.openclaw/",
] as const;

function validateOpenClawPackFixture(entries: string[]): {
  missingRequired: string[];
  forbiddenPresent: string[];
} {
  const missingRequired = REQUIRED_OPENCLAW_ENTRIES.filter((entry) => !entries.includes(entry));

  const forbiddenPresent = entries.filter((entry) =>
    EXCLUDED_RUNTIME_PREFIXES.some((prefix) => entry === prefix.slice(0, -1) || entry.startsWith(prefix)),
  );

  return { missingRequired, forbiddenPresent };
}

describe.skip("feature79 openclaw pack fixture contract [deprecated]", () => {
  it("it_accepts_fixture_with_required_entries_and_no_runtime_artifacts", () => {
    const fixtureEntries = [
      "kinnoo.yaml",
      "index.js",
      "requirements.txt",
      "package.json",
      "AGENTS.md",
      "skills/planner/SKILL.md",
      "memory/session/journal.md",
      "wheels/missing_wheels.txt",
    ];

    const result = validateOpenClawPackFixture(fixtureEntries);
    expect(result.missingRequired).toEqual([]);
    expect(result.forbiddenPresent).toEqual([]);
  });

  it("it_flags_runtime_artifact_prefixes_when_present", () => {
    const fixtureEntries = [
      "kinnoo.yaml",
      "AGENTS.md",
      "skills/planner/SKILL.md",
      "memory/session/journal.md",
      "skills/node_modules/dep/index.js",
      "memory/.openclaw/cache.json",
    ];

    const result = validateOpenClawPackFixture(fixtureEntries);
    expect(result.missingRequired).toEqual([]);
    expect(result.forbiddenPresent).toEqual([
      "skills/node_modules/dep/index.js",
      "memory/.openclaw/cache.json",
    ]);
  });
});
