import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const assignMock = vi.fn();

beforeEach(() => {
  assignMock.mockReset();
  Object.defineProperty(window, "location", {
    configurable: true,
    value: { assign: assignMock },
  });
});

import LoginPage from "../app/(public)/login/page";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("Login page", () => {
  it("renders hosted-login CTA and no password form inputs", () => {
    render(<LoginPage />);

    expect(screen.getByText("Registry Login")).toBeTruthy();
    expect(screen.getByText("Welcome back to Kinnoo!")).toBeTruthy();
    expect(screen.queryByLabelText("Password")).toBeNull();
    expect(screen.queryByLabelText("Username (E-mail)")).toBeNull();
    expect(screen.getByRole("button", { name: "Continue to Login" })).toBeTruthy();
  });

  it("starts redirect-based login flow from /api/login", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 307 }));

    render(<LoginPage />);
    fireEvent.click(screen.getByRole("button", { name: "Continue to Login" }));

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledWith(
        "/api/login",
        expect.objectContaining({
          method: "GET",
          credentials: "include",
          redirect: "manual",
        }),
      );
    });
    expect(assignMock).toHaveBeenCalledWith("/api/login");
  });
});
