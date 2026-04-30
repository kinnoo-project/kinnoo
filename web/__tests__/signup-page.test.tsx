import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import MainLayout from "../components/blocks/MainLayout";
import LoginPage from "../app/(public)/login/page";
import SignupPage from "../app/(public)/signup/page";

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

describe("Sign up entry points and signup page", () => {
  it("renders Sign Up CTAs in layout and login page routing to /signup", () => {
    render(
      <MainLayout>
        <div>content</div>
      </MainLayout>,
    );

    const navSignupLink = screen.getByRole("link", { name: "Sign Up" });
    expect(navSignupLink).toBeTruthy();
    expect(navSignupLink.getAttribute("href")).toBe("/signup");

    cleanup();
    render(<LoginPage />);

    const loginSignupLink = screen.getByRole("link", { name: "Sign Up" });
    expect(loginSignupLink).toBeTruthy();
    expect(loginSignupLink.getAttribute("href")).toBe("/signup");
  });

  it("renders hosted sign-up call to action to /api/signup", () => {
    render(<SignupPage />);

    expect(screen.getByText("Sign up today to get access to the agent registry")).toBeTruthy();

    const signupLink = screen.getByRole("link", { name: "Create an Account" });
    expect(signupLink).toBeTruthy();
    expect(signupLink.getAttribute("href")).toBe("/api/signup");
  });

  it("keeps fallback login link for existing users", () => {
    render(<SignupPage />);

    const loginLink = screen.getByRole("link", { name: "Login" });
    expect(loginLink).toBeTruthy();
    expect(loginLink.getAttribute("href")).toBe("/login");
  });

  it("does not render legacy signup form elements", () => {
    render(<SignupPage />);

    expect(screen.queryByLabelText("Email address")).toBeNull();
    expect(screen.queryByRole("button", { name: "Send Verification Link" })).toBeNull();
    expect(screen.queryByText("Check your email for a verification link.")).toBeNull();
  });
});
