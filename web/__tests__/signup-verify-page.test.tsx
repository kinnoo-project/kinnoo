import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams("token=valid-token"),
}));

import SignupVerifyPage from "../app/(public)/signup/verify/page";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe.skip("/signup/verify page [deprecated]", () => {
  it("enforces password match and minimum length", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(JSON.stringify({ message: "ok" }), { status: 200 }));

    render(<SignupVerifyPage />);

    fireEvent.change(screen.getByLabelText("Create Password"), {
      target: { value: "long-enough-passphrase" },
    });
    fireEvent.change(screen.getByLabelText("Confirm Password"), {
      target: { value: "different-passphrase" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create Account" }));

    expect(screen.getByText("Passwords do not match.")).toBeTruthy();
    expect(fetchSpy).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText("Create Password"), {
      target: { value: "short" },
    });
    fireEvent.change(screen.getByLabelText("Confirm Password"), {
      target: { value: "short" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create Account" }));

    expect(screen.getByText("Password must be at least 10 characters.")).toBeTruthy();
    expect(fetchSpy).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText("Create Password"), {
      target: { value: "long-enough-passphrase" },
    });
    fireEvent.change(screen.getByLabelText("Confirm Password"), {
      target: { value: "long-enough-passphrase" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create Account" }));

    await waitFor(() => {
      expect(screen.getByText("Account created. Redirecting to your registry...")).toBeTruthy();
    });
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });
});
