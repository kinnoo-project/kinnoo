import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import PrivacyPolicyPage from "../app/(public)/privacy/page";
import TermsOfServicePage from "../app/(public)/terms/page";

afterEach(() => {
  cleanup();
});

describe("Terms of Service page", () => {
  it("renders the document header with title and last-updated date", () => {
    render(<TermsOfServicePage />);

    expect(
      screen.getByRole("heading", { level: 1, name: "Terms of Service" }),
    ).toBeTruthy();
    expect(screen.getByText(/Last updated: April 29, 2026/i)).toBeTruthy();
  });

  it("renders all required top-level sections in order", () => {
    render(<TermsOfServicePage />);

    const expectedHeadings = [
      "1. About Kinnoo",
      "2. Eligibility and Account Registration",
      "3. User Content and License Grant to Kinnoo",
      "4. Non-Endorsement and Third-Party Content Disclaimer",
      "5. User Responsibility and Human-in-the-Loop Oversight",
      "6. Acceptable Use Policy",
      "7. Intellectual Property",
      "8. Suspension, Termination, and Agent Removal",
      "9. Disclaimers; AS-IS, AS-AVAILABLE",
      "10. Limitation of Liability",
      "11. Indemnification",
      "12. Governing Law and Dispute Resolution",
      "13. General Provisions",
    ];

    const renderedHeadings = screen
      .getAllByRole("heading", { level: 2 })
      .map((node) => node.textContent ?? "");

    expect(renderedHeadings).toEqual(expectedHeadings);
  });

  it("includes the production-ready protections required by issue #379", () => {
    render(<TermsOfServicePage />);
    const article = screen.getByTestId("legal-page");

    // Non-endorsement clause
    expect(
      within(article).getByText(/does not endorse, sponsor, certify, vet, audit/i),
    ).toBeTruthy();

    // Human-in-the-loop / user responsibility
    expect(within(article).getAllByText(/Human-in-the-Loop/).length).toBeGreaterThan(0);
    expect(
      within(article).getByText(/solely responsible for any Agent that you publish/i),
    ).toBeTruthy();

    // AS IS / AS AVAILABLE limitation of liability
    expect(within(article).getByText(/AS IS/)).toBeTruthy();
    expect(within(article).getByText(/AS AVAILABLE/)).toBeTruthy();
    expect(
      within(article).getByText(/hallucinations, omissions, or autonomous behavior/i),
    ).toBeTruthy();

    // Acceptable use policy items
    expect(within(article).getByText(/deepfakes/i)).toBeTruthy();
    expect(within(article).getByText(/self-harm/i)).toBeTruthy();
    expect(within(article).getByText(/Scrape, harvest, mirror/)).toBeTruthy();

    // IP retention by user
    expect(
      within(article).getByText(/You retain all right, title, and interest/i),
    ).toBeTruthy();

    // Termination / archival retention discretion
    expect(
      within(article).getByText(/in its sole discretion, retain copies of Agent archives/i),
    ).toBeTruthy();

    // Age requirement (COPPA / CalOPPA)
    expect(within(article).getByText(/at least 18 years old/i)).toBeTruthy();
    expect(within(article).getByText(/COPPA/)).toBeTruthy();
    expect(within(article).getByText(/CalOPPA/)).toBeTruthy();

    // Kinnoo-specific: CLI / local execution / third-party services invoked by Agents
    expect(
      within(article).getByText(/CLI is not a sandbox/i),
    ).toBeTruthy();
    expect(
      within(article).getAllByText(/Third-Party Service/).length,
    ).toBeGreaterThan(0);

    // Kinnoo-specific: no secrets in published archives + namespace squatting + sanctions
    expect(
      within(article).getByText(/no secrets, credentials, or personal data/i),
    ).toBeTruthy();
    expect(within(article).getByText(/namespace squatting/i)).toBeTruthy();
    expect(within(article).getByText(/economic sanctions or trade embargoes/i))
      .toBeTruthy();

    // DMCA designated agent contact
    expect(within(article).getByText(/512\(c\)\(2\)/)).toBeTruthy();
    expect(
      within(article).getByText(/Kinnoo has designated an agent to receive/i),
    ).toBeTruthy();

    // Access Tokens covered in account section
    expect(within(article).getAllByText(/Access Tokens/).length).toBeGreaterThan(0);
  });

  it("links to the Privacy Policy", () => {
    render(<TermsOfServicePage />);

    const privacyLinks = screen
      .getAllByRole("link", { name: /Privacy Policy/i })
      .filter((node) => node.getAttribute("href") === "/privacy");

    expect(privacyLinks.length).toBeGreaterThanOrEqual(1);
  });
});

describe("Privacy Policy page", () => {
  it("renders the document header with title and last-updated date", () => {
    render(<PrivacyPolicyPage />);

    expect(
      screen.getByRole("heading", { level: 1, name: "Privacy Policy" }),
    ).toBeTruthy();
    expect(screen.getByText(/Last updated: April 29, 2026/i)).toBeTruthy();
  });

  it("renders all required top-level sections in order", () => {
    render(<PrivacyPolicyPage />);

    const expectedHeadings = [
      "1. Scope of this Policy",
      "2. Information We Collect",
      "3. How We Use Personal Information",
      "4. Legal Bases for Processing (EEA / UK Users)",
      "5. How We Share Personal Information",
      "6. International Data Transfers",
      "7. Data Retention",
      "8. Security",
      "9. Your Rights and Choices",
      "10. Children Under 13",
      "11. Do Not Track and Third-Party Sites",
      "12. Changes to This Privacy Policy",
      "13. How to Contact Us",
    ];

    const renderedHeadings = screen
      .getAllByRole("heading", { level: 2 })
      .map((node) => node.textContent ?? "");

    expect(renderedHeadings).toEqual(expectedHeadings);
  });

  it("addresses GDPR, CCPA, and CalOPPA compliance topics from issue #379", () => {
    render(<PrivacyPolicyPage />);
    const article = screen.getByTestId("legal-page");

    // GDPR / CCPA / CalOPPA references
    expect(within(article).getAllByText(/GDPR/).length).toBeGreaterThan(0);
    expect(within(article).getAllByText(/CCPA/).length).toBeGreaterThan(0);
    expect(within(article).getAllByText(/CalOPPA/).length).toBeGreaterThan(0);

    // Kinde Auth as data processor, including social sign-in (Google / GitHub)
    expect(within(article).getAllByText(/Kinde Auth/).length).toBeGreaterThan(0);
    expect(
      within(article).getByText(/Kinde processes your authentication credentials/i),
    ).toBeTruthy();
    expect(within(article).getByText(/Google and GitHub/)).toBeTruthy();

    // Collects names and emails, but does not sell data or handle payments
    expect(within(article).getByText(/your name \(or display name\), email address/i))
      .toBeTruthy();
    expect(
      within(article).getByText(/We do not sell your personal information/i),
    ).toBeTruthy();
    expect(
      within(article).getByText(/Kinnoo does not currently process payments/i),
    ).toBeTruthy();

    // No children under 13 clause
    expect(
      within(article).getByText(/we do not knowingly\s+collect personal information from children under the age of 13/i),
    ).toBeTruthy();

    // Kinnoo-specific: CLI data collection + local execution privacy
    expect(
      within(article).getByText(/Information collected by the Kinnoo CLI/i),
    ).toBeTruthy();
    expect(
      within(article).getByText(/does not transmit telemetry to Kinnoo other than/i),
    ).toBeTruthy();
    expect(
      within(article).getByText(/Information when you run an Agent locally/i),
    ).toBeTruthy();
    expect(
      within(article).getByText(/Kinnoo does not receive, store, or process the prompts/i),
    ).toBeTruthy();

    // Authentication and access tokens are listed as a category
    expect(
      within(article).getByText(/Authentication and access tokens:/),
    ).toBeTruthy();
  });

  it("links to the Terms of Service", () => {
    render(<PrivacyPolicyPage />);

    const termsLinks = screen
      .getAllByRole("link", { name: /Terms of Service/i })
      .filter((node) => node.getAttribute("href") === "/terms");

    expect(termsLinks.length).toBeGreaterThanOrEqual(1);
  });
});
