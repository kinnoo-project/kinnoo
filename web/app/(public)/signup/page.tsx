"use client";

import Link from "next/link";

export default function SignupPage() {
  return (
    <section className="flex min-h-[calc(100vh-14rem)] items-center justify-center px-4 py-8">
      <div className="w-full max-w-md rounded-card border border-white/10 bg-kinnoo-surface/70 p-6 shadow-xl sm:p-8">
        <h1 className="mb-2 text-3xl font-semibold tracking-tight text-kinnoo-text">Sign Up</h1>
        <p className="mb-6 text-sm text-white/70">
          Sign up today to get access to the agent registry
        </p>

        <Link
          href="/api/signup"
          className="inline-flex w-full cursor-pointer items-center justify-center rounded-button border border-kinnoo-accent/70 bg-kinnoo-accent/10 px-4 py-2 text-sm font-semibold text-kinnoo-text transition hover:border-[#FF7F00] hover:bg-kinnoo-accent/20 hover:text-[#FF7F00] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent"
        >
          Create an Account
        </Link>

        <p className="pt-5 text-sm text-white/70">
          Already have an account?{" "}
          <Link
            href="/login"
            className="underline decoration-white/40 underline-offset-4 transition hover:text-[#FF7F00] hover:decoration-[#FF7F00]"
          >
            Login
          </Link>
        </p>
      </div>
    </section>
  );
}
