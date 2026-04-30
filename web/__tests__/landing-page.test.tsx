// [agent - deprecated - do not execute]
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import LandingPage from "../app/(public)/page";

afterEach(() => {
  cleanup();
});

describe.skip("Landing page", () => {
  beforeEach(() => {
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });
  });

  it("renders exact hero title and sub-headline", () => {
    render(<LandingPage />);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "kinnoo",
      }),
    ).toBeTruthy();

    expect(screen.getByText("The package manager for AI agents")).toBeTruthy();

    expect(
      screen.getByText(
        "The open, secure platform to package, publish, test, and run AI agents",
      ),
    ).toBeTruthy();

    expect(
      screen.getByText(
        "Kinnoo brings DevOps rigor to the AI agent ecosystem. Initialize, package, distribute, and deploy agents from multiple frameworks into a single, secure, verifiable workflow.",
      ),
    ).toBeTruthy();
  });

  it("renders terminal command and supports copy feedback", async () => {
    render(<LandingPage />);

    expect(screen.getByText("pip install kinnoo")).toBeTruthy();
    const copyButton = screen.getByRole("button", { name: "Copy install command" });
    expect(copyButton).toBeTruthy();

    fireEvent.click(copyButton);
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith("pip install kinnoo");
    expect(await screen.findByText("Copied!")).toBeTruthy();
  });

  it("renders all six feature cards with exact copy", () => {
    render(<LandingPage />);

    const expectedCards: Array<{ title: string; description: string }> = [
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
          "Signed archives, permission declarations, static security sweeps, dependency audits, preflight checks, runtime monitoring, and a kill switch help you trust what you run.",
      },
      {
        title: "Inspect before you run",
        description:
          "Review agent manifests, dependencies, environment variables, permissions, service calls and cryptographic integrity of agent files before installation — no surprises.",
      },
    ];

    for (const card of expectedCards) {
      expect(screen.getByRole("heading", { level: 3, name: card.title })).toBeTruthy();
      expect(screen.getByText(card.description)).toBeTruthy();
    }
  });

  it("exposes hover/focus hooks and avoids horizontal overflow classes", () => {
    const { container } = render(<LandingPage />);

    const grid = screen.getByTestId("feature-grid");
    expect(grid.className).toContain("grid-cols-1");
    expect(grid.className).toContain("sm:grid-cols-2");

    const cards = container.querySelectorAll("article");
    expect(cards.length).toBe(6);

    cards.forEach((card) => {
      expect(card.className).toContain("hover:border-[#FF7F00]");
      expect(card.className).toContain("focus-within:ring-1");
      expect(card.className).toContain("overflow-hidden");
    });
  });

  it("covers hero, terminal preview, and features in one render pass", () => {
    render(<LandingPage />);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "kinnoo",
      }),
    ).toBeTruthy();
    expect(screen.getByText("The package manager for AI agents")).toBeTruthy();
    expect(screen.getByText("pip install kinnoo")).toBeTruthy();
    expect(screen.getByTestId("feature-grid")).toBeTruthy();
  });
});
