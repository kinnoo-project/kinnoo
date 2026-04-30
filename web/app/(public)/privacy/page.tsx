import type { Metadata } from "next";
import Link from "next/link";

import LegalPage, {
  LegalSection,
  LegalSubsection,
} from "../../../components/blocks/LegalPage";

export const metadata: Metadata = {
  title: "Privacy Policy · kinnoo",
  description:
    "How Kinnoo collects, uses, shares, and protects personal information for the Kinnoo AI agent registry, website, and command-line interface.",
};

const LAST_UPDATED = "April 29, 2026";

export default function PrivacyPolicyPage() {
  return (
    <LegalPage
      title="Privacy Policy"
      lastUpdated={LAST_UPDATED}
      intro={
        <p>
          This Privacy Policy explains how the maintainers of Kinnoo (&ldquo;Kinnoo,&rdquo;
          &ldquo;we,&rdquo; &ldquo;us,&rdquo; or &ldquo;our&rdquo;) collect, use, share, retain,
          and protect personal information in connection with the Kinnoo website, the Kinnoo AI
          agent registry, the Kinnoo command-line interface (the &ldquo;CLI&rdquo;), associated
          APIs, and any related services (collectively, the &ldquo;Service&rdquo;). It also
          describes the rights that you may have over your personal information under applicable
          data-protection laws, including the European Union&rsquo;s General Data Protection
          Regulation (&ldquo;GDPR&rdquo;), the United Kingdom GDPR, the California Consumer Privacy
          Act as amended by the California Privacy Rights Act (collectively, the
          &ldquo;CCPA&rdquo;), and the California Online Privacy Protection Act
          (&ldquo;CalOPPA&rdquo;). By using the Service you acknowledge that you have read this
          Privacy Policy. Your use of the Service is also governed by our{" "}
          <Link href="/terms" className="text-[#FF7F00] underline hover:no-underline">
            Terms of Service
          </Link>
          .
        </p>
      }
    >
      <LegalSection id="scope" heading="1. Scope of this Policy">
        <p>
          This Privacy Policy applies to personal information that Kinnoo processes as a
          controller (or, where applicable, as a business) in connection with the Service. It does
          not apply to personal information that is processed by third parties whose products or
          services you may interact with separately, including the operators of any external
          website, registry mirror, or AI model provider that an Agent (as defined in our Terms of
          Service) may invoke. Where the Service includes links or integrations with third-party
          services, you should review the privacy notices of those third parties to understand how
          they handle your personal information.
        </p>
        <p>
          For users in the European Economic Area, the United Kingdom, and Switzerland, the
          &ldquo;controller&rdquo; of personal information processed under this Privacy Policy is
          the Kinnoo project. You may contact us using the details in Section 13.
        </p>
      </LegalSection>

      <LegalSection id="information-we-collect" heading="2. Information We Collect">
        <LegalSubsection heading="2.1 Information you provide directly">
          <p>
            When you create a Kinnoo account, publish or install Agents, configure your profile,
            or contact us, we collect the information you choose to provide. This typically
            includes:
          </p>
          <ul className="list-disc space-y-2 pl-6">
            <li>
              <span className="font-semibold text-white/90">Account identifiers:</span> your name
              (or display name), email address, chosen username or tenant slug, and a hashed or
              federated representation of your authentication credentials.
            </li>
            <li>
              <span className="font-semibold text-white/90">Authentication and access tokens:
              </span>{" "}
              session tokens issued by Kinde Auth and any CLI access tokens, publish tokens, or
              API tokens that you generate or that the Service issues to you. We store these in a
              hashed or otherwise non-reversible form where technically feasible and use them only
              to authenticate your requests to the Service.
            </li>
            <li>
              <span className="font-semibold text-white/90">Profile information:</span> any
              optional profile fields you choose to fill in, such as a biography, links, or an
              avatar image.
            </li>
            <li>
              <span className="font-semibold text-white/90">Content you publish:</span> Agent
              archives (source code, compiled artifacts, configuration, and other files), Agent
              metadata (names, descriptions, tags, version numbers, dependency declarations,
              permission declarations, and documentation), and any other content you submit
              through the Service. User Content you publish is generally public, is fetched and
              served to other Users on request, and may be downloaded, mirrored, cached, or
              indexed by third parties. Do not include personal information about yourself or
              others, and do not include API keys, tokens, credentials, or other secrets, in
              published User Content unless you intend for that information to be permanently
              public; if you do, you must consider the secret compromised and rotate it.
            </li>
            <li>
              <span className="font-semibold text-white/90">Communications:</span> the contents of
              messages you send to us, including support requests, bug reports, abuse reports, and
              copyright complaints.
            </li>
          </ul>
        </LegalSubsection>
        <LegalSubsection heading="2.2 Information from social sign-in">
          <p>
            We use Kinde Auth (operated by Kinde, Inc.) to handle account registration,
            authentication, and session management. Kinde Auth offers the option to sign up or
            sign in using a social identity provider, currently including Google and GitHub. If
            you choose to use a social sign-in option, the relevant identity provider will share
            with Kinde, and Kinde will share with us, a limited profile typically consisting of
            your name, email address, and a stable provider-specific user identifier. We do not
            receive your social-account password. Information shared with us by a social provider
            is treated as account information under this Privacy Policy.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="2.3 Information collected automatically">
          <p>
            When you access or use the Service, we and our service providers may automatically
            collect:
          </p>
          <ul className="list-disc space-y-2 pl-6">
            <li>
              <span className="font-semibold text-white/90">Log and device data:</span> Internet
              Protocol (IP) address, user-agent string, device and operating-system information,
              CLI version (where applicable), preferred language, time zone, referring URL, and
              the date, time, and duration of requests.
            </li>
            <li>
              <span className="font-semibold text-white/90">Usage data:</span> the pages or API
              endpoints you access, the Agents you publish, install, fetch, or search for, the
              actions you take in the registry user interface, and similar interactions with the
              Service.
            </li>
            <li>
              <span className="font-semibold text-white/90">Security and integrity data:</span>
              {" "}records related to authentication attempts, rate limiting, abuse detection,
              webhook deliveries, and audit logs.
            </li>
            <li>
              <span className="font-semibold text-white/90">Cookies and similar technologies:
              </span>{" "}
              strictly necessary cookies (such as our session cookie and a CSRF token) that are
              required for the Service to function and to keep you signed in. We do not use
              third-party advertising cookies or cross-site tracking cookies. Your browser&rsquo;s
              settings allow you to block or delete cookies, but doing so may prevent you from
              signing in or using parts of the Service.
            </li>
          </ul>
        </LegalSubsection>
        <LegalSubsection heading="2.4 Information we do not collect">
          <p>
            We do not knowingly collect government-issued identification numbers, payment-card
            numbers, bank-account information, precise geolocation, biometric identifiers,
            information about your physical or mental health, or special categories of personal
            data under the GDPR. Kinnoo does not currently process payments; if and when we
            introduce paid features in the future, we will update this Privacy Policy and the
            payment information will be handled by a regulated payment processor under that
            processor&rsquo;s own terms.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="2.5 Information collected by the Kinnoo CLI">
          <p>
            The Kinnoo command-line interface (the &ldquo;CLI&rdquo;) communicates with the
            Service when you authenticate, search the registry, publish or unpublish an Agent,
            install or fetch an Agent, or otherwise invoke a CLI command that maps to a registry
            API. When the CLI makes such a request, the same categories of log data described in
            Section 2.3 are recorded for that request, including IP address, user-agent string,
            CLI version, the API endpoint invoked, and the Agent selector or query that you
            provided. Where the request is authenticated, we associate it with your account or
            Access Token.
          </p>
          <p>
            The CLI does not transmit telemetry to Kinnoo other than what is required to fulfill
            the registry API request you have invoked. It does not report on which Agents you run
            locally, the inputs or outputs of those Agents, your file system contents, your
            environment variables, or other information about your local machine. Some CLI
            commands may write configuration, cached archives, or log files to a directory under
            your home directory; that local data is stored on your machine and is not transmitted
            to Kinnoo.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="2.6 Information when you run an Agent locally">
          <p>
            When you use the CLI to run an Agent on your machine, the Agent executes locally with
            the permissions of the operating-system user that invoked the CLI. Kinnoo does not
            receive, store, or process the prompts, inputs, outputs, files, network traffic, or
            other data that the Agent generates or exchanges with any third-party service while
            it is running. If the Agent invokes a third-party service (for example, a large-
            language-model provider, search API, payment provider, or cloud-storage provider),
            the data sent to and received from that service is governed by the privacy notice and
            terms of that third-party service and not by this Privacy Policy. You are responsible
            for understanding the data-handling practices of any third-party service that an
            Agent you run is configured to use.
          </p>
        </LegalSubsection>
      </LegalSection>

      <LegalSection id="how-we-use" heading="3. How We Use Personal Information">
        <p>We use personal information for the following purposes:</p>
        <ul className="list-disc space-y-2 pl-6">
          <li>
            <span className="font-semibold text-white/90">To provide the Service:</span> to create
            and maintain your account, authenticate you, accept and serve Agent uploads and
            downloads, render the registry user interface, respond to API requests, and otherwise
            deliver the features of the Service.
          </li>
          <li>
            <span className="font-semibold text-white/90">To secure the Service:</span> to detect,
            investigate, and prevent fraud, abuse, security incidents, malware uploads, and
            violations of our Terms of Service or Acceptable Use Policy; to apply rate limits and
            quotas; and to comply with audit and incident-response obligations.
          </li>
          <li>
            <span className="font-semibold text-white/90">To communicate with you:</span> to send
            transactional messages such as email-verification messages, password-reset messages,
            security alerts, and important changes to the Service or this Privacy Policy. We do
            not currently send marketing emails; if we do in the future, we will provide a clear
            opt-out mechanism.
          </li>
          <li>
            <span className="font-semibold text-white/90">To improve the Service:</span> to
            understand how the Service is used in aggregate, to debug errors, and to plan and test
            new features. We aim to use aggregated or de-identified data wherever possible for
            these purposes.
          </li>
          <li>
            <span className="font-semibold text-white/90">To comply with the law:</span> to comply
            with our legal and regulatory obligations, respond to lawful requests from public
            authorities, enforce our agreements, and protect the rights, property, or safety of
            Kinnoo, our Users, or others.
          </li>
        </ul>
      </LegalSection>

      <LegalSection id="legal-bases" heading="4. Legal Bases for Processing (EEA / UK Users)">
        <p>
          If you are located in the European Economic Area, the United Kingdom, or Switzerland,
          we process your personal information on the following legal bases:
        </p>
        <ul className="list-disc space-y-2 pl-6">
          <li>
            <span className="font-semibold text-white/90">Performance of a contract</span> (Art.
            6(1)(b) GDPR): to provide the Service to you under our Terms of Service, including
            creating your account, accepting and serving Agent archives, and responding to your
            requests.
          </li>
          <li>
            <span className="font-semibold text-white/90">Legitimate interests</span> (Art. 6(1)(f)
            GDPR): to secure the Service, prevent fraud and abuse, maintain audit logs, debug
            errors, and improve the Service. We balance these interests against your rights and
            freedoms and apply safeguards to minimize the personal information involved.
          </li>
          <li>
            <span className="font-semibold text-white/90">Compliance with legal obligations</span>
            {" "}(Art. 6(1)(c) GDPR): to comply with applicable laws, respond to lawful requests
            from public authorities, and retain records required by law.
          </li>
          <li>
            <span className="font-semibold text-white/90">Consent</span> (Art. 6(1)(a) GDPR):
            where we ask for your specific consent (for example, for any future optional analytics
            or marketing communication). You may withdraw your consent at any time without
            affecting the lawfulness of processing carried out before withdrawal.
          </li>
        </ul>
      </LegalSection>

      <LegalSection id="sharing" heading="5. How We Share Personal Information">
        <p>We share personal information only as described in this Section 5:</p>
        <LegalSubsection heading="5.1 Service providers and processors">
          <p>
            We share personal information with carefully selected service providers that process
            it on our behalf and under written contractual obligations consistent with this
            Privacy Policy and applicable law. These currently include, without limitation:
          </p>
          <ul className="list-disc space-y-2 pl-6">
            <li>
              <span className="font-semibold text-white/90">Kinde, Inc. (Kinde Auth):</span> our
              identity and authentication provider. Kinde processes your authentication
              credentials, social-sign-in information, session tokens, and related security
              metadata as our processor for the purpose of providing identity services to the
              Service. Kinde&rsquo;s processing is subject to its own privacy notice and
              data-processing agreement, and Kinde acts strictly on our documented instructions
              for purposes of operating the Service.
            </li>
            <li>
              <span className="font-semibold text-white/90">Cloud infrastructure providers:</span>
              {" "}we host the Service on commercial cloud infrastructure providers that supply
              compute, storage, content-delivery, edge, and database services. These providers
              process personal information only to host and deliver the Service.
            </li>
            <li>
              <span className="font-semibold text-white/90">Email delivery and support tooling:
              </span>{" "}
              we use service providers to send transactional email (for example, email-
              verification and password-reset messages) and to manage support requests.
            </li>
            <li>
              <span className="font-semibold text-white/90">Security and observability tooling:
              </span>{" "}
              we may use providers for error monitoring, log aggregation, denial-of-service
              protection, and similar operational purposes.
            </li>
          </ul>
          <p>
            We require each of these providers to protect personal information consistent with
            applicable law and to use it only for the purposes for which we share it.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="5.2 Other Users and the public">
          <p>
            By design, the registry exposes certain account-level information to other Users and
            to the public, including your username or tenant slug, your published Agents and
            their metadata, and any profile information you choose to make public. We do not
            disclose your email address or other contact information to other Users without your
            consent except as required by law.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="5.3 Legal, safety, and enforcement disclosures">
          <p>
            We may disclose personal information when we have a good-faith belief that disclosure
            is necessary to: (a) comply with applicable law, regulation, legal process, or
            governmental request; (b) enforce the Terms of Service, including investigation of
            potential violations; (c) detect, prevent, or otherwise address fraud, security, or
            technical issues; or (d) protect against harm to the rights, property, or safety of
            Kinnoo, our Users, or the public as required or permitted by law.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="5.4 Business transfers">
          <p>
            If Kinnoo is involved in a merger, acquisition, reorganization, financing, or sale of
            assets, personal information may be transferred as part of that transaction, subject
            to standard confidentiality obligations and to the protections of this Privacy
            Policy. We will notify you of any material change in the controller of your personal
            information.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="5.5 No sale or sharing of personal information">
          <p>
            We do not sell your personal information for monetary or other valuable consideration,
            and we do not &ldquo;share&rdquo; your personal information for cross-context
            behavioral advertising as those terms are defined under the CCPA. We have not engaged
            in such sales or sharing in the preceding twelve months.
          </p>
        </LegalSubsection>
      </LegalSection>

      <LegalSection id="international-transfers" heading="6. International Data Transfers">
        <p>
          Kinnoo is operated from, and our service providers may process personal information in,
          the United States and other countries that may have data-protection laws different from
          those in your country of residence. Where personal information of users in the European
          Economic Area, the United Kingdom, or Switzerland is transferred to a country that has
          not received an adequacy decision from the relevant authority, we rely on appropriate
          safeguards such as the European Commission&rsquo;s Standard Contractual Clauses, the
          United Kingdom International Data Transfer Addendum, or other lawful transfer
          mechanisms with our service providers. You may contact us to request more information
          about the safeguards we use.
        </p>
      </LegalSection>

      <LegalSection id="retention" heading="7. Data Retention">
        <p>
          We retain personal information for as long as is reasonably necessary to provide the
          Service, to comply with our legal and regulatory obligations, to resolve disputes, and
          to enforce our agreements. Specific retention practices include:
        </p>
        <ul className="list-disc space-y-2 pl-6">
          <li>
            <span className="font-semibold text-white/90">Account information</span> is retained
            for the lifetime of your account and for a reasonable period thereafter to allow for
            account recovery, dispute resolution, and audit trail integrity.
          </li>
          <li>
            <span className="font-semibold text-white/90">Published User Content</span>, including
            Agent archives and metadata, may remain publicly available so long as it is published
            and may be retained internally after removal as described in Section 8.3 of our Terms
            of Service for security, audit, and legal-compliance purposes.
          </li>
          <li>
            <span className="font-semibold text-white/90">Security and audit logs</span> are
            retained for a limited period appropriate to their purpose, typically not longer than
            twenty-four (24) months unless a longer retention period is required by law or to
            investigate an ongoing incident.
          </li>
          <li>
            <span className="font-semibold text-white/90">Backups</span> follow a separate
            retention cycle. Personal information that has been deleted from active systems may
            persist in encrypted backups for a limited period until those backups are rotated and
            overwritten.
          </li>
        </ul>
      </LegalSection>

      <LegalSection id="security" heading="8. Security">
        <p>
          We implement administrative, technical, and organizational measures designed to protect
          personal information against unauthorized access, accidental loss, alteration, or
          disclosure. These measures include encryption of data in transit using industry-standard
          TLS, encryption of sensitive data at rest where supported by our infrastructure
          providers, the use of a managed identity provider to store and verify authentication
          credentials, role-based access control for administrative interfaces, audit logging,
          rate limiting, and security monitoring. No method of transmission over the Internet or
          method of electronic storage is one hundred percent secure, and we cannot guarantee
          absolute security. You are responsible for keeping your account credentials confidential
          and for using strong, unique passwords with your social-sign-in providers.
        </p>
      </LegalSection>

      <LegalSection id="your-rights" heading="9. Your Rights and Choices">
        <LegalSubsection heading="9.1 Rights for users in the EEA, UK, and Switzerland (GDPR)">
          <p>
            Subject to applicable law and certain exemptions, you have the right to:
          </p>
          <ul className="list-disc space-y-2 pl-6">
            <li>
              <span className="font-semibold text-white/90">Access</span> the personal information
              we hold about you.
            </li>
            <li>
              <span className="font-semibold text-white/90">Rectify</span> personal information
              that is inaccurate or incomplete.
            </li>
            <li>
              <span className="font-semibold text-white/90">Erase</span> your personal information
              in certain circumstances (for example, where it is no longer necessary for the
              purposes for which it was collected).
            </li>
            <li>
              <span className="font-semibold text-white/90">Restrict or object</span> to certain
              processing, including processing based on legitimate interests.
            </li>
            <li>
              <span className="font-semibold text-white/90">Data portability:</span> receive a
              copy of personal information you provided to us in a structured, commonly used,
              machine-readable format.
            </li>
            <li>
              <span className="font-semibold text-white/90">Withdraw consent</span> where we are
              processing your personal information based on your consent.
            </li>
            <li>
              <span className="font-semibold text-white/90">Lodge a complaint</span> with your
              local supervisory authority. We would, however, appreciate the opportunity to
              address your concerns first.
            </li>
          </ul>
        </LegalSubsection>
        <LegalSubsection heading="9.2 Rights for California residents (CCPA)">
          <p>
            Subject to applicable law and certain exemptions, California residents have the right
            to:
          </p>
          <ul className="list-disc space-y-2 pl-6">
            <li>
              Know the categories and specific pieces of personal information we have collected
              about them, the categories of sources, the business or commercial purposes for
              collecting it, and the categories of third parties with whom we share it.
            </li>
            <li>Request deletion of personal information that we have collected from them.</li>
            <li>
              Request correction of inaccurate personal information that we maintain about them.
            </li>
            <li>
              Opt out of the sale or sharing of personal information. As described above, we do
              not sell or share personal information for cross-context behavioral advertising.
            </li>
            <li>
              Limit the use and disclosure of sensitive personal information. We do not use
              sensitive personal information to infer characteristics about you and we limit our
              use of any such information to providing the Service and the other purposes
              permitted by the CCPA.
            </li>
            <li>
              Be free from unlawful discrimination for exercising your CCPA rights.
            </li>
          </ul>
        </LegalSubsection>
        <LegalSubsection heading="9.3 How to exercise your rights">
          <p>
            You may exercise these rights by contacting us using the details in Section 13. We
            may need to verify your identity before responding to a request, and we may be unable
            to fulfill a request where an exemption under applicable law applies. We will respond
            within the timeframes required by applicable law. You may use an authorized agent to
            submit a request on your behalf, subject to verification.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="9.4 Account self-service">
          <p>
            Many account changes can be made directly within the Service. You can update profile
            information, change your password through your social or Kinde-managed credentials,
            unpublish or deprecate Agents you have published, and request account deletion using
            the in-product controls or by contacting us.
          </p>
        </LegalSubsection>
      </LegalSection>

      <LegalSection id="children" heading="10. Children Under 13">
        <p>
          The Service is not directed to children under the age of 13, and we do not knowingly
          collect personal information from children under the age of 13. If you are a parent or
          legal guardian and believe that a child under 13 has provided personal information to
          the Service, please contact us using the details in Section 13 and we will take
          reasonable steps to delete that information from our systems. Users between the ages of
          13 and 17 may use the Service only in accordance with the age requirements set out in
          our Terms of Service. This Privacy Policy is also intended to satisfy the requirements
          of the California Online Privacy Protection Act (CalOPPA) regarding the protection of
          minors.
        </p>
      </LegalSection>

      <LegalSection id="dnt-and-third-parties" heading="11. Do Not Track and Third-Party Sites">
        <p>
          Some browsers offer a &ldquo;Do Not Track&rdquo; setting. Because there is no industry-
          standard interpretation of this signal, we do not currently respond to it. We do not,
          however, allow third-party advertising networks to collect personal information about
          your activity on the Service for cross-site behavioral advertising. The Service may
          contain links to third-party websites and resources, including, for example, links from
          published Agent metadata to third-party documentation. We are not responsible for the
          privacy practices of those third parties, and we encourage you to review their privacy
          notices before providing them with personal information.
        </p>
      </LegalSection>

      <LegalSection id="changes" heading="12. Changes to This Privacy Policy">
        <p>
          We may update this Privacy Policy from time to time. If we make material changes, we
          will update the &ldquo;Last updated&rdquo; date at the top of this page and, where
          appropriate, provide additional notice (such as a banner in the Service or an email to
          the address associated with your account). Your continued use of the Service after the
          effective date of the updated Privacy Policy constitutes your acknowledgement of the
          updated terms to the extent permitted by applicable law.
        </p>
      </LegalSection>

      <LegalSection id="contact" heading="13. How to Contact Us">
        <p>
          If you have questions about this Privacy Policy or wish to exercise any of your rights,
          you may contact Kinnoo support through the channels published on the Kinnoo website,
          including by opening an issue at{" "}
          <a
            href="https://github.com/kinnoo-project/kinnoo/issues"
            className="text-[#FF7F00] underline hover:no-underline"
            target="_blank"
            rel="noreferrer"
          >
            https://github.com/kinnoo-project/kinnoo/issues
          </a>
          . Please do not include sensitive personal information in a public issue. If you are
          located in the European Economic Area, the United Kingdom, or Switzerland and your
          concern is not resolved by contacting us, you have the right to lodge a complaint with
          your local supervisory authority.
        </p>
      </LegalSection>
    </LegalPage>
  );
}
