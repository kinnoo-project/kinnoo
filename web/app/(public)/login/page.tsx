"use client";

import { useState } from "react";
import Link from "next/link";

import { startLoginRedirect } from "../../../lib/auth-client";

export default function LoginPage() {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleStartLogin() {
    setSubmitError(null);
    setIsSubmitting(true);

    try {
      const response = await startLoginRedirect();

      if (response.ok) {
        window.location.assign("/api/login");
      } else {
        setSubmitError("Unable to start sign in. Please try again.");
      }
    } catch {
      setSubmitError("Unable to sign in right now. Please try again shortly.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="flex min-h-[calc(100vh-14rem)] items-center justify-center px-4 py-8">
      <div className="w-full max-w-md rounded-card border border-white/10 bg-kinnoo-surface/70 p-6 shadow-xl sm:p-8">
        <h1 className="mb-2 text-3xl font-semibold tracking-tight text-kinnoo-text">Registry Login</h1>
        <p className="mb-6 text-sm text-white/70">Welcome back to Kinnoo!</p>

        <div className="space-y-4">
          <button
            type="button"
            onClick={() => {
              void handleStartLogin();
            }}
            disabled={isSubmitting}
            className="mt-2 inline-flex w-full cursor-pointer items-center justify-center rounded-button border border-kinnoo-accent/70 bg-kinnoo-accent/10 px-4 py-2 text-sm font-semibold text-kinnoo-text transition hover:border-[#FF7F00] hover:bg-kinnoo-accent/20 hover:text-[#FF7F00] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent"
          >
            {isSubmitting ? "Redirecting..." : "Continue to Login"}
          </button>

          {submitError ? (
            <p role="alert" className="text-sm text-red-300">
              {submitError}
            </p>
          ) : null}

          <p className="text-sm text-white/70">
            Need an account?{" "}
            <Link
              href="/signup"
              className="underline decoration-white/40 underline-offset-4 transition hover:text-[#FF7F00] hover:decoration-[#FF7F00]"
            >
              Sign Up
            </Link>
          </p>
        </div>
      </div>
    </section>
  );
}
