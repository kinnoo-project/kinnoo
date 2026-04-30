"use client";

type AuthErrorBoundaryProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function AuthError({ error, reset }: AuthErrorBoundaryProps) {
  const message = error.message || "AUTH_API_UNAVAILABLE";

  let title = "Registry temporarily unavailable";
  let body = "Please retry in a moment. If this continues, check backend availability.";

  if (message.includes("401")) {
    title = "Authentication required";
    body = "Your session is not valid. Please sign in again to continue.";
  } else if (message.includes("429") || message.includes("RATE_LIMITED")) {
    title = "Too many requests";
    body = "You are being rate limited. Please wait briefly, then retry.";
  }

  return (
    <section className="rounded-card border border-red-400/30 bg-[#111111] p-6" role="alert">
      <h2 className="text-xl font-semibold text-kinnoo-text">{title}</h2>
      <p className="mt-2 text-sm text-white/70">{body}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={reset}
          className="rounded-button border border-kinnoo-accent/60 px-4 py-2 text-sm font-semibold text-kinnoo-text hover:border-kinnoo-accent"
        >
          Retry
        </button>
        <a
          href="/login"
          className="inline-flex items-center rounded-button border border-white/20 px-4 py-2 text-sm text-white/80 hover:border-kinnoo-accent"
        >
          Go to Login
        </a>
      </div>
    </section>
  );
}
