"use client";

import type { FormEvent } from "react";
import { useState } from "react";

import FormField from "../../../components/ui/form-field";
import { validateForgotPasswordEmail } from "../../../lib/auth-validation";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState<string | undefined>(undefined);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [confirmationMessage, setConfirmationMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError(null);

    const validation = validateForgotPasswordEmail(email);
    setEmailError(validation.email);
    if (validation.email) {
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch("/api/auth/password-reset-request", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ email: email.trim() }),
      });

      if (!response.ok) {
        setSubmitError("Unable to send reset link right now. Please try again.");
        return;
      }

      setConfirmationMessage("If an account exists with that email, you'll receive a reset link.");
    } catch {
      setSubmitError("Unable to send reset link right now. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="flex min-h-[calc(100vh-14rem)] items-center justify-center px-4 py-8">
      <div className="w-full max-w-md rounded-card border border-white/10 bg-kinnoo-surface/70 p-6 shadow-xl sm:p-8">
        <h1 className="mb-2 text-3xl font-semibold tracking-tight text-kinnoo-text">Forgot Password</h1>
        <p className="mb-6 text-sm text-white/70">Enter your email and we will send a reset link.</p>

        <form className="space-y-4" noValidate onSubmit={handleSubmit}>
          <FormField
            id="forgot-email"
            name="email"
            label="Email address"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            error={emailError}
          />

          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex w-full items-center justify-center rounded-button border border-kinnoo-accent/70 bg-kinnoo-accent/10 px-4 py-2 text-sm font-semibold text-kinnoo-text transition hover:bg-kinnoo-accent/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent"
          >
            {isSubmitting ? "Sending..." : "Send Reset Link"}
          </button>

          {confirmationMessage ? (
            <p role="status" className="text-sm text-emerald-300">
              {confirmationMessage}
            </p>
          ) : null}

          {submitError ? (
            <p role="alert" className="text-sm text-red-300">
              {submitError}
            </p>
          ) : null}
        </form>
      </div>
    </section>
  );
}
