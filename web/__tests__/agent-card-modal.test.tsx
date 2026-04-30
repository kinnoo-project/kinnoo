import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import AgentCard from "../components/blocks/AgentCard";
import RegistryPage from "../app/(auth)/registry/page";

function jsonResponse(payload: unknown, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(() => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse([]));
});

afterEach(() => {
  cleanup();
});

describe("AgentCard", () => {
  it("renders required metadata fields and clickable name", () => {
    const onNameClick = vi.fn();

    render(
      <AgentCard
        agent={{
          tenant_slug: "acme",
          agent_slug: "calendar-helper",
          version: "1.2.3",
          author: "jerry",
          framework: "langgraph",
          size: 4096,
          description: "Helps with calendar workflows.",
        }}
        onNameClick={onNameClick}
      />, 
    );

    expect(screen.getByText("Tenant")).toBeTruthy();
    expect(screen.getByText("Name")).toBeTruthy();
    expect(screen.getByText("Version")).toBeTruthy();
    expect(screen.getByText("Author")).toBeTruthy();
    expect(screen.getByText("Framework")).toBeTruthy();
    expect(screen.getByText("Size")).toBeTruthy();
    expect(screen.getByText("Description")).toBeTruthy();

    const nameButton = screen.getByRole("button", { name: "calendar-helper" });
    fireEvent.click(nameButton);

    expect(onNameClick).toHaveBeenCalledTimes(1);
  });

  it("opens manifest modal from name click and closes using X", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url === "/api/agents?show_only_mine=true") {
        return Promise.resolve(
          jsonResponse([
            {
              tenant_slug: "acme",
              agent_slug: "calendar-helper",
              version: "1.2.3",
              description: "test",
            },
          ]),
        );
      }
      if (url === "/api/agents/acme/calendar-helper") {
        return Promise.resolve(
          jsonResponse({
            tenant_slug: "acme",
            agent_slug: "calendar-helper",
            manifest: { name: "calendar-helper" },
          }),
        );
      }
      if (url === "/api/agents/acme/calendar-helper/1.2.3/security-report") {
        return Promise.resolve(
          jsonResponse({
            tenant_slug: "acme",
            agent_slug: "calendar-helper",
            version: "1.2.3",
            checks: [],
          }),
        );
      }
      return Promise.resolve(jsonResponse([]));
    });

    render(<RegistryPage />);

    const agentNameButton = await screen.findByRole("button", { name: "calendar-helper" });
    fireEvent.click(agentNameButton);

    expect(await screen.findByRole("heading", { name: "Agent Manifest" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Close manifest modal" }));

    await waitFor(() => {
      expect(screen.queryByRole("heading", { name: "Agent Manifest" })).toBeNull();
    });
  });

  it("fetches detail endpoint and renders registry, agent, versions, and security tabs", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url === "/api/agents?show_only_mine=true") {
        return Promise.resolve(
          jsonResponse([
            {
              tenant_slug: "acme",
              agent_slug: "calendar-helper",
              version: "1.2.3",
              description: "test",
            },
          ]),
        );
      }
      if (url === "/api/agents/acme/calendar-helper") {
        return Promise.resolve(
          jsonResponse({
            tenant_slug: "acme",
            agent_slug: "calendar-helper",
            versions: [{ version: "1.2.3", created_at: "2026-01-01T00:00:00Z", updated_at: "2026-01-01T00:00:00Z" }],
            agent_manifest: { framework: "langgraph" },
          }),
        );
      }
      if (url === "/api/agents/acme/calendar-helper/1.2.3/security-report") {
        return Promise.resolve(
          jsonResponse({
            tenant_slug: "acme",
            agent_slug: "calendar-helper",
            version: "1.2.3",
            checks: [
              { check_name: "signature", status: "unsigned", detail: "missing" },
              { check_name: "archive_integrity", status: "pass", detail: "ok" },
            ],
          }),
        );
      }
      return Promise.resolve(jsonResponse([]));
    });

    render(<RegistryPage />);

    fireEvent.click(await screen.findByRole("button", { name: "calendar-helper" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Registry Manifest" })).toBeTruthy();
      expect(screen.getByRole("button", { name: "Agent Manifest" })).toBeTruthy();
      expect(screen.getByRole("button", { name: "Agent Versions" })).toBeTruthy();
      expect(screen.getByRole("button", { name: "Security" })).toBeTruthy();
      expect(screen.getByText(/"agent_slug": "calendar-helper"/)).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: "Agent Manifest" }));

    await waitFor(() => {
      expect(screen.getByText(/"framework": "langgraph"/)).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: "Agent Versions" }));
    await waitFor(() => {
      expect(screen.getAllByText("2026-01-01T00:00:00Z").length).toBeGreaterThan(0);
    });

    fireEvent.click(screen.getByRole("button", { name: "Security" }));
    await waitFor(() => {
      expect(screen.getByText("[UNSIGNED]", { exact: false })).toBeTruthy();
      expect(screen.getByText("[PASS]", { exact: false })).toBeTruthy();
    });

    const urls = fetchSpy.mock.calls.map(([url]) => String(url));
    expect(urls).toContain("/api/agents/acme/calendar-helper");
  });

  it("shows deterministic install command in search modal and copy feedback", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(globalThis.navigator, "clipboard", {
      value: { writeText },
      configurable: true,
    });

    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);

      if (url === "/api/agents?show_only_mine=true") {
        return Promise.resolve(
          jsonResponse([
            {
              tenant_slug: "acme",
              agent_slug: "calendar-helper",
              version: "1.2.3",
              description: "test",
            },
          ]),
        );
      }

      if (url.startsWith("/api/search")) {
        return Promise.resolve(
          jsonResponse([
            {
              tenant_slug: "acme",
              agent_slug: "public-helper",
              version: "2.0.0",
              description: "public",
            },
          ]),
        );
      }

      if (url === "/api/agents/acme/public-helper") {
        return Promise.resolve(
          jsonResponse({
            tenant_slug: "acme",
            agent_slug: "public-helper",
            manifest: { name: "public-helper" },
          }),
        );
      }
      if (url === "/api/agents/acme/public-helper/2.0.0/security-report") {
        return Promise.resolve(
          jsonResponse({
            tenant_slug: "acme",
            agent_slug: "public-helper",
            version: "2.0.0",
            checks: [],
          }),
        );
      }

      return Promise.resolve(jsonResponse([]));
    });

    render(<RegistryPage />);

    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    fireEvent.change(await screen.findByLabelText("Search public agents"), {
      target: { value: "public" },
    });
    fireEvent.click(await screen.findByRole("button", { name: "public-helper" }));

    await waitFor(() => {
      expect(screen.getByText("kinnoo install acme/public-helper==2.0.0")).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: "Copy" }));

    await waitFor(() => {
      expect(writeText).toHaveBeenCalledWith("kinnoo install acme/public-helper==2.0.0");
      expect(screen.getByRole("button", { name: "Copied!" })).toBeTruthy();
    });
  });

  it("covers full agent card and modal interaction flow", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(globalThis.navigator, "clipboard", {
      value: { writeText },
      configurable: true,
    });

    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);

      if (url === "/api/agents?show_only_mine=true") {
        return Promise.resolve(
          jsonResponse([
            {
              tenant_slug: "acme",
              agent_slug: "calendar-helper",
              version: "1.2.3",
              author: "jerry",
              framework: "langgraph",
              size: 4096,
              description: "calendar",
            },
          ]),
        );
      }

      if (url.startsWith("/api/search")) {
        return Promise.resolve(
          jsonResponse([
            {
              tenant_slug: "acme",
              agent_slug: "public-helper",
              version: "2.0.0",
              author: "jerry",
              framework: "langgraph",
              size: 2048,
              description: "public",
            },
          ]),
        );
      }

      if (url === "/api/agents/acme/calendar-helper") {
        return Promise.resolve(
          jsonResponse({
            tenant_slug: "acme",
            agent_slug: "calendar-helper",
            versions: [{ version: "1.2.3" }],
            agent_manifest: { framework: "langgraph" },
          }),
        );
      }
      if (url === "/api/agents/acme/calendar-helper/1.2.3/security-report") {
        return Promise.resolve(
          jsonResponse({
            tenant_slug: "acme",
            agent_slug: "calendar-helper",
            version: "1.2.3",
            checks: [],
          }),
        );
      }

      if (url === "/api/agents/acme/public-helper") {
        return Promise.resolve(
          jsonResponse({
            tenant_slug: "acme",
            agent_slug: "public-helper",
            versions: [{ version: "2.0.0" }],
            agent_manifest: { framework: "langgraph" },
          }),
        );
      }
      if (url === "/api/agents/acme/public-helper/2.0.0/security-report") {
        return Promise.resolve(
          jsonResponse({
            tenant_slug: "acme",
            agent_slug: "public-helper",
            version: "2.0.0",
            checks: [],
          }),
        );
      }

      return Promise.resolve(jsonResponse([]));
    });

    render(<RegistryPage />);

    expect(await screen.findByText("Tenant")).toBeTruthy();
    fireEvent.click(await screen.findByRole("button", { name: "calendar-helper" }));

    fireEvent.click(await screen.findByRole("button", { name: "Agent Manifest" }));

    await waitFor(() => {
      expect(screen.getByText(/"framework": "langgraph"/)).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: "Close manifest modal" }));
    await waitFor(() => {
      expect(screen.queryByRole("heading", { name: "Agent Manifest" })).toBeNull();
    });

    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    fireEvent.change(await screen.findByLabelText("Search public agents"), {
      target: { value: "public" },
    });
    fireEvent.click(await screen.findByRole("button", { name: "public-helper" }));

    await waitFor(() => {
      expect(screen.getByText("kinnoo install acme/public-helper==2.0.0")).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: "Copy" }));
    await waitFor(() => {
      expect(writeText).toHaveBeenCalledWith("kinnoo install acme/public-helper==2.0.0");
      expect(screen.getByRole("button", { name: "Copied!" })).toBeTruthy();
    });
  });
});
