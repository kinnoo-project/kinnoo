"use client";

import Link from "next/link";
import type { FormEvent } from "react";
import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";

import FormField from "../../../../components/ui/form-field";
import {
  PASSWORD_MAX_LENGTH,
  PASSWORD_MIN_LENGTH,
  validateResetPasswords,
} from "../../../../lib/auth-validation";

export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <section className="flex min-h-[calc(100vh-14rem)] items-center justify-center px-4 py-8">
          <div className="w-full max-w-md rounded-card border border-white/10 bg-kinnoo-surface/70 p-6 shadow-xl sm:p-8">
            <h1 className="mb-2 text-3xl font-semibold tracking-tight text-kinnoo-text">Reset Password</h1>
            <p className="text-sm text-white/70">Loading reset form...</p>
          </div>
        </section>
      }
    >
      <ResetPasswordForm />
    </Suspense>
  );
}

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<{ newPassword?: string; confirmPassword?: string }>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [confirmationMessage, setConfirmationMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError(null);

    if (!token) {
      setSubmitError("Reset link is missing or invalid.");
      return;
    }

    const nextErrors = validateResetPasswords(newPassword, confirmPassword);
    setFieldErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch("/api/auth/password-reset-confirm", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ token, new_password: newPassword.trim() }),
      });

      if (!response.ok) {
        setSubmitError("Unable to reset password. The link may be invalid or expired.");
        return;
      }

      setConfirmationMessage("Password reset complete.");
      setNewPassword("");
      setConfirmPassword("");
    } catch {
      setSubmitError("Unable to reset password right now. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="flex min-h-[calc(100vh-14rem)] items-center justify-center px-4 py-8">
      <div className="w-full max-w-md rounded-card border border-white/10 bg-kinnoo-surface/70 p-6 shadow-xl sm:p-8">
        <h1 className="mb-2 text-3xl font-semibold tracking-tight text-kinnoo-text">Reset Password</h1>
        <p className="mb-6 text-sm text-white/70">
          Use {PASSWORD_MIN_LENGTH}-{PASSWORD_MAX_LENGTH} characters for your new password.
        </p>

        <form className="space-y-4" noValidate onSubmit={handleSubmit}>
          <FormField
            id="reset-password"
            name="new_password"
            label="New Password"
            type="password"
            autoComplete="new-password"
            placeholder="Create a new passphrase"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
            error={fieldErrors.newPassword}
            helperText="Long passphrases are easier to remember and harder to crack."
          />

          <FormField
            id="reset-confirm-password"
            name="confirm_password"
            label="Confirm Password"
            type="password"
            autoComplete="new-password"
            placeholder="Confirm your passphrase"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            error={fieldErrors.confirmPassword}
          />

          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex w-full items-center justify-center rounded-button border border-kinnoo-accent/70 bg-kinnoo-accent/10 px-4 py-2 text-sm font-semibold text-kinnoo-text transition hover:bg-kinnoo-accent/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent"
          >
            {isSubmitting ? "Resetting..." : "Reset Password"}
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

        <p className="pt-5 text-sm text-white/70">
          Back to{" "}
          <Link href="/login" className="underline decoration-white/40 underline-offset-4 hover:text-kinnoo-accent">
            login
          </Link>
        </p>
      </div>
    </section>
  );
}
