import type { ReactNode } from "react";

type LegalPageProps = {
  title: string;
  lastUpdated: string;
  intro: ReactNode;
  children: ReactNode;
};

/**
 * Shared layout for legal/policy pages (Terms of Service, Privacy Policy, etc.).
 * Renders a long-form, document-style page with consistent typography that
 * matches the rest of the Kinnoo site.
 */
export default function LegalPage({ title, lastUpdated, intro, children }: LegalPageProps) {
  return (
    <article
      className="mx-auto flex max-w-4xl flex-col gap-8 pb-16 pt-4 text-white/85 sm:pt-8"
      data-testid="legal-page"
    >
      <header className="space-y-3">
        <h1 className="text-4xl font-semibold leading-tight tracking-tight text-[#FF7F00] sm:text-5xl">
          {title}
        </h1>
        <p className="text-sm text-white/60">Last updated: {lastUpdated}</p>
        <div className="text-base leading-relaxed text-white/80 sm:text-lg">{intro}</div>
      </header>
      <div className="space-y-10 text-base leading-relaxed sm:text-[1.0625rem]">{children}</div>
    </article>
  );
}

type LegalSectionProps = {
  id: string;
  heading: string;
  children: ReactNode;
};

export function LegalSection({ id, heading, children }: LegalSectionProps) {
  return (
    <section id={id} aria-labelledby={`${id}-title`} className="space-y-4">
      <h2
        id={`${id}-title`}
        className="text-2xl font-semibold tracking-tight text-[#F9FAFB] sm:text-3xl"
      >
        {heading}
      </h2>
      <div className="space-y-4 text-white/80">{children}</div>
    </section>
  );
}

type LegalSubsectionProps = {
  heading: string;
  children: ReactNode;
};

export function LegalSubsection({ heading, children }: LegalSubsectionProps) {
  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold text-[#F9FAFB] sm:text-xl">{heading}</h3>
      <div className="space-y-3 text-white/80">{children}</div>
    </div>
  );
}
