import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import MainLayout from "../components/blocks/MainLayout";

afterEach(() => {
  cleanup();
});

describe("MainLayout", () => {
  it("renders hamburger menu and public auth buttons when unauthenticated", () => {
    render(
      <MainLayout>
        <div>content</div>
      </MainLayout>,
    );

    expect(screen.getByRole("button", { name: /open menu/i })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Login" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Sign Up" })).toBeTruthy();
  });

  it("renders tenant button and profile menu when authenticated", () => {
    render(
      <MainLayout initialTenantSlug="jerryschen">
        <div>content</div>
      </MainLayout>,
    );

    expect(screen.getByRole("link", { name: "jerryschen" })).toBeTruthy();
    expect(screen.queryByRole("link", { name: "Login" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Sign Up" })).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: /open profile menu/i }));
    expect(screen.getByRole("link", { name: "Settings" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Logout" })).toBeTruthy();
  });

  it("submits logout as navigation-style POST from profile menu", () => {
    document.cookie = "kinnoo_csrf=test-csrf-token";
    const submitSpy = vi
      .spyOn(HTMLFormElement.prototype, "submit")
      .mockImplementation(() => undefined);

    render(
      <MainLayout initialTenantSlug="jerryschen">
        <div>content</div>
      </MainLayout>,
    );

    fireEvent.click(screen.getByRole("button", { name: /open profile menu/i }));
    fireEvent.click(screen.getByRole("button", { name: "Logout" }));

    expect(submitSpy).toHaveBeenCalledTimes(1);
    const logoutForm = document.querySelector(
      'form[action="/api/logout"][method="POST"]',
    ) as HTMLFormElement | null;
    expect(logoutForm).toBeTruthy();
    const csrfInput = logoutForm?.querySelector('input[name="csrf_token"]') as HTMLInputElement | null;
    expect(csrfInput?.value).toBe("test-csrf-token");
  });

  it("opens menu sheet with expected navigation links", () => {
    render(
      <MainLayout>
        <div>content</div>
      </MainLayout>,
    );

    fireEvent.click(screen.getByRole("button", { name: /open menu/i }));

    expect(screen.getByRole("link", { name: "GitHub" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Docs" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Report an Issue" })).toBeTruthy();
  });

  it("includes responsive classes for mobile-safe header behavior", () => {
    const { container } = render(
      <MainLayout>
        <div>content</div>
      </MainLayout>,
    );

    const headerRow = container.querySelector("header > div");
    expect(headerRow?.className).toContain("gap-2");
    expect(headerRow?.className).toContain("px-4");

    const authButtons = screen.getAllByRole("link", { name: /login|sign up/i });
    for (const button of authButtons) {
      expect(button.className).toContain("max-[399px]:text-xs");
      expect(button.className).toContain("max-[399px]:px-2");
    }

    fireEvent.click(screen.getByRole("button", { name: /open menu/i }));
    const dialog = container.ownerDocument.querySelector("[role='dialog']");
    expect(dialog?.className).toContain("rounded-card");
    expect(dialog?.className).toContain("bg-[#222222]");
  });
});
