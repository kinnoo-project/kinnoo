import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams("token=valid-reset-token"),
}));

import ResetPasswordPage from "../app/(public)/forgot-password/reset/page";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("/forgot-password/reset page", () => {
  it("enforces match and minimum length validations", () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(JSON.stringify({ message: "ok" }), { status: 200 }));

    render(<ResetPasswordPage />);

    fireEvent.change(screen.getByLabelText("New Password"), {
      target: { value: "long-enough-passphrase" },
    });
    fireEvent.change(screen.getByLabelText("Confirm Password"), {
      target: { value: "different-passphrase" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Reset Password" }));

    expect(screen.getByText("Passwords do not match.")).toBeTruthy();
    expect(fetchSpy).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText("New Password"), {
      target: { value: "short" },
    });
    fireEvent.change(screen.getByLabelText("Confirm Password"), {
      target: { value: "short" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Reset Password" }));

    expect(screen.getByText("Password must be at least 10 characters.")).toBeTruthy();
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("submits valid payload and shows completion message", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(JSON.stringify({ message: "ok" }), { status: 200 }));

    render(<ResetPasswordPage />);

    fireEvent.change(screen.getByLabelText("New Password"), {
      target: { value: "long-enough-passphrase" },
    });
    fireEvent.change(screen.getByLabelText("Confirm Password"), {
      target: { value: "long-enough-passphrase" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Reset Password" }));

    await waitFor(() => {
      expect(screen.getByText("Password reset complete.")).toBeTruthy();
    });

    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });
});
