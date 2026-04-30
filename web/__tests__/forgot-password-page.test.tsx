import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import ForgotPasswordPage from "../app/(public)/forgot-password/page";
import LoginPage from "../app/(public)/login/page";

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}));

afterEach(() => {
  cleanup();
  pushMock.mockReset();
  vi.restoreAllMocks();
});

describe.skip("/forgot-password page [deprecated]", () => {
  it("exposes forgot-password navigation from login and renders form controls", () => {
    render(<LoginPage />);

    const forgotLink = screen.getByRole("link", { name: "Forgot your password?" });
    expect(forgotLink).toBeTruthy();
    expect(forgotLink.getAttribute("href")).toBe("/forgot-password");

    cleanup();
    render(<ForgotPasswordPage />);

    expect(screen.getByRole("heading", { name: "Forgot Password" })).toBeTruthy();
    expect(screen.getByLabelText("Email address")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Send Reset Link" })).toBeTruthy();
  });

  it("validates email and shows generic confirmation on success", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(JSON.stringify({ message: "ok" }), { status: 200 }));

    render(<ForgotPasswordPage />);

    fireEvent.click(screen.getByRole("button", { name: "Send Reset Link" }));
    expect(screen.getByText("Email is required.")).toBeTruthy();
    expect(fetchSpy).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText("Email address"), {
      target: { value: "not-an-email" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send Reset Link" }));
    expect(screen.getByText("Enter a valid email address.")).toBeTruthy();
    expect(fetchSpy).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText("Email address"), {
      target: { value: "user@example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send Reset Link" }));

    await waitFor(() => {
      expect(screen.getByText("If an account exists with that email, you'll receive a reset link.")).toBeTruthy();
    });

    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });
});
