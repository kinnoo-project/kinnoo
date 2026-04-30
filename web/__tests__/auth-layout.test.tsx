import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const { redirectMock, cookiesMock } = vi.hoisted(() => ({
  redirectMock: vi.fn(),
  cookiesMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  redirect: redirectMock,
}));

vi.mock("next/headers", () => ({
  cookies: cookiesMock,
}));

import AuthLayout from "../app/(auth)/layout";
import AuthLoading from "../app/(auth)/loading";
import AuthError from "../app/(auth)/error";

afterEach(() => {
  cleanup();
});

describe("Auth layout", () => {
  it("redirects to /login when /api/auth/me returns 401", async () => {
    redirectMock.mockReset();
    redirectMock.mockImplementation(() => {
      throw new Error("REDIRECT_LOGIN");
    });
    cookiesMock.mockResolvedValue({ toString: () => "kinnoo_session=bad" });
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 401 }));

    await expect(AuthLayout({ children: <div>content</div> })).rejects.toThrow("REDIRECT_LOGIN");

    expect(redirectMock).toHaveBeenCalledWith("/login");
  });

  it("renders children when /api/auth/me succeeds", async () => {
    redirectMock.mockReset();
    cookiesMock.mockResolvedValue({ toString: () => "kinnoo_session=good" });
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(JSON.stringify({ user_id: "u1" }), { status: 200 }));

    const view = await AuthLayout({ children: <div>ok</div> });

    expect(redirectMock).not.toHaveBeenCalled();
    expect(view).toBeTruthy();
    expect(fetchSpy).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/auth/me",
      expect.objectContaining({
        method: "GET",
        cache: "no-store",
      }),
    );
  });

  it("throws rate-limited auth error for 429 responses", async () => {
    cookiesMock.mockResolvedValue({ toString: () => "kinnoo_session=limited" });
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 429 }));

    await expect(AuthLayout({ children: <div>content</div> })).rejects.toThrow(
      "AUTH_RATE_LIMITED_429",
    );
  });
});

describe("Auth loading and error routes", () => {
  it("renders loading guidance for protected routes", () => {
    render(<AuthLoading />);
    expect(screen.getByText("Loading your registry...")).toBeTruthy();
    expect(screen.getByText(/checking your session/i)).toBeTruthy();
  });

  it("renders user-friendly 429 error guidance and supports retry", () => {
    const reset = vi.fn();
    render(<AuthError error={new Error("AUTH_RATE_LIMITED_429")} reset={reset} />);

    expect(screen.getByText("Too many requests")).toBeTruthy();
    expect(screen.getByText(/rate limited/i)).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(reset).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("link", { name: "Go to Login" })).toBeTruthy();
  });

  it("renders user-friendly generic downtime guidance", () => {
    const reset = vi.fn();
    render(<AuthError error={new Error("AUTH_API_UNAVAILABLE")} reset={reset} />);

    expect(screen.getByText("Registry temporarily unavailable")).toBeTruthy();
    expect(screen.getByText(/check backend availability/i)).toBeTruthy();
  });
});
