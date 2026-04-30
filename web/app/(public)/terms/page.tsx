import type { Metadata } from "next";
import Link from "next/link";

import LegalPage, {
  LegalSection,
  LegalSubsection,
} from "../../../components/blocks/LegalPage";

export const metadata: Metadata = {
  title: "Terms of Service · kinnoo",
  description:
    "The Terms of Service that govern access to and use of the Kinnoo AI agent registry, website, and command-line interface.",
};

const LAST_UPDATED = "April 29, 2026";

export default function TermsOfServicePage() {
  return (
    <LegalPage
      title="Terms of Service"
      lastUpdated={LAST_UPDATED}
      intro={
        <p>
          These Terms of Service (the &ldquo;Terms&rdquo;) form a binding agreement between you
          (&ldquo;you&rdquo; or &ldquo;User&rdquo;) and the maintainers of Kinnoo (&ldquo;Kinnoo,&rdquo;
          &ldquo;we,&rdquo; &ldquo;us,&rdquo; or &ldquo;our&rdquo;) and govern your access to and use
          of the Kinnoo website, the Kinnoo AI agent registry, the Kinnoo command-line interface
          (the &ldquo;CLI&rdquo;), associated APIs, documentation, and any related services
          (collectively, the &ldquo;Service&rdquo;). By accessing or using the Service, by creating
          a Kinnoo account, by publishing or installing an agent, or by clicking a button or
          control indicating acceptance, you agree to be bound by these Terms. If you do not agree
          to these Terms, you may not access or use the Service.
        </p>
      }
    >
      <LegalSection id="about" heading="1. About Kinnoo">
        <p>
          Kinnoo is an open platform that hosts archived packages of artificial intelligence
          agents (&ldquo;Agents&rdquo;) submitted by Users, together with the metadata, version
          history, and documentation that Users choose to publish. The Service allows Users to
          publish, search for, inspect, download, and run Agents through the website or the CLI.
          Kinnoo is operated as a hosting and discovery platform; it is analogous to a code
          hosting service such as GitHub in that the Service primarily distributes content
          authored and uploaded by Users rather than content authored by Kinnoo itself.
        </p>
        <p>
          Kinnoo may use third-party providers, including but not limited to identity provider
          Kinde Auth (&ldquo;Kinde&rdquo;) and one or more cloud infrastructure providers, to
          deliver the Service. Use of these providers is described in our{" "}
          <Link href="/privacy" className="text-[#FF7F00] underline hover:no-underline">
            Privacy Policy
          </Link>
          .
        </p>
      </LegalSection>

      <LegalSection id="eligibility" heading="2. Eligibility and Account Registration">
        <LegalSubsection heading="2.1 Age requirements">
          <p>
            You must be at least 18 years old to create a Kinnoo account and use the Service. If
            you are between 13 and 17 years old, you may use the Service only with the verifiable
            consent and active supervision of a parent or legal guardian who agrees to be bound by
            these Terms on your behalf. The Service is not directed to, and we do not knowingly
            collect personal information from, children under the age of 13 in compliance with
            the United States Children&rsquo;s Online Privacy Protection Act (&ldquo;COPPA&rdquo;)
            and the California Online Privacy Protection Act (&ldquo;CalOPPA&rdquo;).
          </p>
        </LegalSubsection>
        <LegalSubsection heading="2.2 Account information and authentication tokens">
          <p>
            When you register for an account, you must provide accurate, current, and complete
            information and keep it up to date. You are responsible for maintaining the
            confidentiality of any credentials issued to you by Kinde Auth and of any CLI access
            tokens, publish tokens, or API tokens that you generate or that the Service issues to
            you (collectively, &ldquo;Access Tokens&rdquo;), and you are responsible for all
            activity that occurs under your account or with your Access Tokens, whether or not
            authorized by you. You agree to keep Access Tokens secret, to scope them to the
            minimum permissions required, to rotate or revoke them promptly when they may have
            been exposed (including when accidentally committed to a published Agent archive or to
            any public location), and to notify us promptly of any actual or suspected
            unauthorized use of your account, of any Access Token, or of any other breach of
            security.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="2.3 One human per account">
          <p>
            Accounts are issued to individual humans. You may not share your account credentials
            with any other person, and you may not register an account on behalf of any person
            other than yourself unless that person is a minor for whom you are legally responsible.
            Automated agents, bots, or scripts may interact with the Service only through the
            documented public APIs of an account that you control and only in compliance with
            these Terms.
          </p>
        </LegalSubsection>
      </LegalSection>

      <LegalSection id="user-content" heading="3. User Content and License Grant to Kinnoo">
        <LegalSubsection heading="3.1 Definition of User Content">
          <p>
            &ldquo;User Content&rdquo; means any content that you submit, upload, publish, or
            otherwise transmit through the Service, including but not limited to Agent archives
            (source code, compiled artifacts, model weights, configuration files, and assets),
            Agent metadata (names, descriptions, tags, version numbers, dependency declarations,
            permission declarations, and documentation), comments, profile information, and any
            other materials you make available through the Service.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="3.2 Ownership of User Content">
          <p>
            You retain all right, title, and interest in and to your User Content, including any
            copyrights and other intellectual property rights you hold in that content. Nothing in
            these Terms transfers ownership of your User Content to Kinnoo.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="3.3 License to operate the Service">
          <p>
            You grant Kinnoo a worldwide, non-exclusive, royalty-free license to host, store,
            cache, reproduce, transmit, parse, index, display, perform, distribute, and otherwise
            use your User Content solely as reasonably necessary to operate, provide, secure, and
            improve the Service. This includes, without limitation, the right to: (a) store Agent
            archives so they may be downloaded and installed by other Users; (b) display Agent
            metadata, documentation, and version history in the registry user interface and
            through the API; (c) generate derivative artifacts (such as search indices, integrity
            checksums, security scan results, and previews) for the operation of the Service; and
            (d) make backup and disaster-recovery copies.
          </p>
          <p>
            You also grant each other User of the Service the rights granted to that User by the
            license you have applied to your User Content (for example, an open-source license
            file included in your Agent archive). You represent and warrant that you have all
            rights necessary to grant the licenses described in this section.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="3.4 Public-by-default registry">
          <p>
            Unless an Agent or piece of metadata is explicitly marked as private and the Service
            supports such marking, you should assume that User Content you publish to the registry
            is publicly accessible to any visitor or User of the Service, including indexable by
            third-party search engines and downloadable by other Users. Once an Agent archive or
            piece of metadata has been published, it may have been downloaded, mirrored, cached,
            or indexed by other Users or third parties, and Kinnoo cannot recall those copies on
            your behalf.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="3.5 No secrets, credentials, or personal data in published archives">
          <p>
            You are responsible for the contents of every Agent archive and every piece of
            metadata you publish. You agree not to publish, and you represent and warrant that
            your published User Content does not contain, any of the following: API keys, OAuth
            tokens, personal access tokens, cryptographic private keys, database connection
            strings or credentials, cloud-provider access keys, customer data, personally
            identifiable information about any third party, protected health information, payment-
            card data, or any other secret or sensitive information that you do not intend to
            disclose publicly. You acknowledge that any such information you publish must be
            considered compromised, that you are responsible for promptly rotating or revoking it,
            and that Kinnoo&rsquo;s removal of the published copy does not remediate copies that
            other Users or third parties may have downloaded.
          </p>
        </LegalSubsection>
      </LegalSection>

      <LegalSection
        id="non-endorsement"
        heading="4. Non-Endorsement and Third-Party Content Disclaimer"
      >
        <p>
          Kinnoo is a platform for hosting Agent archives and associated metadata that are created
          and uploaded by Users. Kinnoo does not author, control, audit, or curate the substance
          of User Content. Except where Kinnoo expressly identifies itself as the author of
          specific content, all Agents and other materials available through the Service are
          provided by third parties and represent the views, code, instructions, and conduct of
          those third parties and not of Kinnoo.
        </p>
        <p>
          Kinnoo does not endorse, sponsor, certify, vet, audit, verify, or guarantee the
          accuracy, performance, safety, security, legality, fitness for any particular purpose,
          or non-infringement of any Agent, model, dependency, prompt, evaluation result,
          benchmark claim, or other User Content available through the Service. Any reliance you
          place on User Content is strictly at your own risk. Automated metadata such as
          checksums, signature verification results, dependency listings, or static security
          scan output is provided for informational purposes only and does not constitute an
          endorsement or warranty of safety or correctness.
        </p>
        <p>
          The presence of an Agent in the registry, the availability of an install command, or
          the absence of a warning indicator does not imply that Kinnoo has reviewed the Agent or
          that the Agent is safe to install or run. You are solely responsible for evaluating the
          fitness, safety, and legality of any Agent before you install, run, deploy, or rely on
          it.
        </p>
      </LegalSection>

      <LegalSection
        id="user-responsibility"
        heading="5. User Responsibility and Human-in-the-Loop Oversight"
      >
        <LegalSubsection heading="5.1 You are responsible for the Agents you deploy">
          <p>
            You are solely responsible for any Agent that you publish, install, configure,
            execute, or deploy through or as a result of the Service, and for the actions, outputs,
            decisions, omissions, side effects, network calls, file-system modifications, financial
            transactions, communications, and any other consequences of those Agents in your
            environment, in any environment you control, or in any environment on whose behalf you
            act. This responsibility applies whether the Agent was authored by you or by another
            User and whether you obtained the Agent through the registry, the CLI, the API, a
            mirror, or any other distribution channel.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="5.2 Human-in-the-Loop requirement">
          <p>
            Agents are autonomous or semi-autonomous software systems that may produce non-
            deterministic outputs, take actions on external systems, invoke paid APIs, send
            communications, modify data, or otherwise act with real-world consequences. You agree
            to maintain meaningful, qualified, and timely human oversight (&ldquo;Human-in-the-
            Loop&rdquo;) over any Agent you deploy by, at a minimum: (a) reviewing the Agent&rsquo;s
            declared permissions, dependencies, and behavior before installation; (b) running the
            Agent in an isolated or sandboxed environment that limits its access to only the
            resources it requires; (c) configuring approval gates, dry-run modes, spending caps,
            and rate limits where consequential actions are possible; (d) monitoring the Agent in
            production and being able to intervene, pause, or terminate the Agent in a timely
            manner; and (e) verifying outputs before relying on them for any decision that has
            material legal, financial, safety, medical, or reputational consequences.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="5.3 No reliance for high-risk uses">
          <p>
            The Service, the CLI, and Agents distributed through the Service are general-purpose
            tools and are not designed, intended, or authorized for use in high-risk applications
            where failure could lead to death, personal injury, environmental damage, or other
            catastrophic harm, including but not limited to safety-critical medical devices,
            life-support systems, autonomous vehicles, weapons systems, nuclear facilities, or
            critical infrastructure control systems. You agree not to use the Service for any such
            purpose.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="5.4 Compliance with law">
          <p>
            You are solely responsible for ensuring that your use of the Service and any Agent you
            publish, install, or run complies with all laws, regulations, contracts, and policies
            applicable to you, including but not limited to laws regarding privacy, data
            protection, export controls, sanctions, intellectual property, consumer protection,
            financial services, healthcare, and the use of artificial intelligence.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="5.5 The CLI, local execution, and third-party services invoked by Agents">
          <p>
            The Kinnoo command-line interface (the &ldquo;CLI&rdquo;) is a client application that
            you download to and run on a computer that you control. When you use the CLI to
            install, fetch, or run an Agent, the Agent&rsquo;s code is executed on your local
            machine (or on whatever environment in which you choose to run the CLI), with the
            permissions of the operating-system user that invoked the CLI. The CLI is not a
            sandbox, and Kinnoo does not control, monitor, or limit what the Agent can do once it
            is running on your machine. You are solely responsible for the environment in which
            you run the CLI and for any read, write, network, billing, or side-effect actions that
            an Agent performs once executed.
          </p>
          <p>
            Agents may, when executed, invoke third-party services, including but not limited to
            large-language-model providers, search APIs, payment APIs, communication platforms,
            cloud-storage providers, vector databases, browser-automation services, and other
            online services (collectively, &ldquo;Third-Party Services&rdquo;). Kinnoo is not a
            party to your relationship with any Third-Party Service. Your use of any Third-Party
            Service is governed solely by that service&rsquo;s own terms, acceptable-use policy,
            and privacy notice, and you are solely responsible for: (a) reviewing and complying
            with those terms; (b) any data, prompts, content, or instructions that an Agent
            transmits to a Third-Party Service while running on your machine; (c) any fees,
            charges, or quota consumption incurred by an Agent against a Third-Party Service
            using your credentials; and (d) any consequences of a Third-Party Service&rsquo;s
            response being acted upon by the Agent. Kinnoo does not receive, store, or process
            the inputs or outputs that an Agent exchanges with a Third-Party Service when the
            Agent is executed locally through the CLI.
          </p>
          <p>
            If you provide an Agent with credentials or Access Tokens to a Third-Party Service,
            you do so at your own risk and are responsible for the secure storage, scoping, and
            rotation of those credentials. Kinnoo recommends configuring the most restrictive
            permissions and spending limits available, running Agents in an isolated environment
            (for example, a dedicated user account, container, or virtual machine), and reviewing
            the Agent&rsquo;s declared permissions and dependencies before execution.
          </p>
        </LegalSubsection>
      </LegalSection>

      <LegalSection id="acceptable-use" heading="6. Acceptable Use Policy">
        <p>
          As a condition of your access to and use of the Service, you agree that you will not,
          and will not authorize or assist any third party to, do any of the following:
        </p>
        <ul className="list-disc space-y-2 pl-6">
          <li>
            Use the Service for any unlawful purpose, or in furtherance of any illegal act,
            including but not limited to fraud, harassment, stalking, theft of trade secrets,
            unauthorized access to computer systems, or trafficking in illegal goods or services.
          </li>
          <li>
            Publish, distribute, or run any Agent that is designed, marketed, or reasonably
            foreseeable to be used to: (a) generate non-consensual sexual content, child sexual
            abuse material, or any content that sexualizes minors; (b) generate deepfakes,
            synthetic media, or impersonations of real persons without their explicit, informed,
            and revocable consent; (c) facilitate self-harm, suicide, eating disorders, or other
            harm to the user or to others; (d) generate or amplify content intended to defame,
            harass, threaten, or incite violence against any person or group; (e) plan, promote,
            or enable acts of terrorism or mass violence; or (f) circumvent safety, content,
            authentication, or security controls of any system.
          </li>
          <li>
            Publish or distribute any Agent that contains malware, ransomware, spyware, keyloggers,
            credential stealers, cryptominers installed without consent, network worms, remote
            access tools intended for unauthorized use, or any other code intended to damage,
            disable, or gain unauthorized access to any system, account, or data.
          </li>
          <li>
            Publish or distribute User Content that infringes any third party&rsquo;s
            intellectual-property rights, violates any contractual or fiduciary obligation, or
            misappropriates trade secrets.
          </li>
          <li>
            Scrape, harvest, mirror, or bulk-download the Service or any portion of it (including
            the registry, user profiles, or metadata) by means other than the documented public
            APIs, or in a manner that exceeds the published rate limits, or in violation of the
            Service&rsquo;s <code>robots.txt</code> or other machine-readable usage controls.
          </li>
          <li>
            Probe, scan, or test the vulnerability of the Service, breach or attempt to breach any
            security or authentication mechanism, interfere with or disrupt the integrity or
            performance of the Service, or take any action that imposes an unreasonable or
            disproportionately large load on the infrastructure of the Service. Coordinated
            security research is welcome through our published disclosure channel.
          </li>
          <li>
            Use the Service to train, evaluate, or fine-tune any third-party model on User Content
            in violation of the licenses applicable to that User Content, or to circumvent the
            access controls of any private or restricted resource.
          </li>
          <li>
            Use the Service to send unsolicited communications, spam, phishing messages, or chain
            letters, or to impersonate any person or entity or misrepresent your affiliation with
            any person or entity.
          </li>
          <li>
            Attempt to reverse engineer, decompile, or derive the source code of any non-public
            component of the Service, except to the extent that such restriction is expressly
            prohibited by applicable law.
          </li>
          <li>
            Embed, hard-code, or otherwise include in any published Agent archive, metadata
            field, or other User Content any API keys, OAuth tokens, personal access tokens,
            cryptographic private keys, database credentials, cloud-provider access keys, or
            other secrets, whether your own or those of a third party.
          </li>
          <li>
            Register, claim, or use a tenant slug, Agent name, namespace, display name, or other
            identifier in a manner that infringes the trademark, service mark, or other
            identifying right of any third party; that impersonates any person, organization, or
            project; or that is intended to mislead Users into believing that an Agent is
            authored, sponsored, endorsed, or maintained by a person or organization that has not
            authorized such use (including &ldquo;namespace squatting&rdquo; or
            &ldquo;typosquatting&rdquo; on well-known names).
          </li>
          <li>
            Access, use, publish, install, fetch, or run any portion of the Service or any Agent
            from, to, or on behalf of any country, region, entity, or individual that is the
            subject of comprehensive economic sanctions or trade embargoes administered by the
            United States, the European Union, the United Kingdom, the United Nations, or any
            other applicable jurisdiction, or that is otherwise prohibited from receiving United
            States exports or services. You represent and warrant that you are not such a person
            and are not acting on behalf of one.
          </li>
        </ul>
        <p>
          Kinnoo may, at its sole discretion and without prior notice, investigate suspected
          violations of this Acceptable Use Policy, remove or disable access to User Content,
          suspend or terminate accounts, and cooperate with law-enforcement authorities, all as
          further described in Section 8 (Termination).
        </p>
      </LegalSection>

      <LegalSection id="ip" heading="7. Intellectual Property">
        <LegalSubsection heading="7.1 Kinnoo intellectual property">
          <p>
            Excluding User Content, the Service and all materials provided by or on behalf of
            Kinnoo, including but not limited to the Kinnoo name, the Kinnoo logo, the Kinnoo
            website, the CLI, the registry user interface, documentation, designs, graphics, and
            software, are owned by Kinnoo or its licensors and are protected by copyright,
            trademark, and other intellectual-property laws. Subject to your compliance with these
            Terms, Kinnoo grants you a limited, non-exclusive, non-transferable, non-sublicensable,
            revocable license to access and use the Service for its intended purpose. No other
            rights are granted to you by implication, estoppel, or otherwise.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="7.2 Open-source components">
          <p>
            Portions of the Service and the CLI may be made available under one or more open-
            source licenses. Where an open-source license applies to a particular component, that
            license governs your use of that component to the extent of any conflict with these
            Terms.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="7.3 Feedback">
          <p>
            If you provide Kinnoo with any suggestions, ideas, enhancement requests, or other
            feedback regarding the Service (&ldquo;Feedback&rdquo;), you grant Kinnoo a perpetual,
            irrevocable, worldwide, royalty-free, fully paid-up, sublicensable, transferable
            license to use, reproduce, modify, distribute, and otherwise exploit the Feedback for
            any purpose, without any obligation or compensation to you.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="7.4 Copyright complaints and DMCA designated agent">
          <p>
            Kinnoo respects the intellectual-property rights of others. If you believe that
            content available through the Service infringes your copyright, you may submit a
            notice of infringement that complies with the United States Digital Millennium
            Copyright Act (&ldquo;DMCA&rdquo;) using the contact information in Section 13. We
            will respond to properly submitted notices in accordance with the DMCA and our
            internal procedures, including by removing or disabling access to allegedly infringing
            content and, in appropriate circumstances, terminating the accounts of repeat
            infringers.
          </p>
          <p>
            For purposes of 17 U.S.C. § 512(c)(2), Kinnoo has designated an agent to receive
            notifications of claimed infringement. The current contact information for the
            designated agent is published on the Kinnoo website and may also be obtained by
            contacting Kinnoo support through the channels described in Section 13. Notices must
            include all of the elements required by 17 U.S.C. § 512(c)(3),
            including a physical or electronic signature, identification of the copyrighted work
            claimed to have been infringed, identification of the allegedly infringing material
            sufficient to permit us to locate it, your contact information, a good-faith
            statement, and a statement under penalty of perjury that the information is accurate
            and that you are authorized to act on behalf of the rights holder. Misrepresentations
            in a DMCA notice may subject you to liability under 17 U.S.C. § 512(f).
          </p>
        </LegalSubsection>
      </LegalSection>

      <LegalSection id="termination" heading="8. Suspension, Termination, and Agent Removal">
        <LegalSubsection heading="8.1 Termination by you">
          <p>
            You may stop using the Service at any time. You may also request deletion of your
            account by following the procedures described in our Privacy Policy. Termination of
            your account does not automatically remove from the Service any User Content that has
            already been published, mirrored, or downloaded by other Users; please see Section 8.3
            for our retention practices.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="8.2 Suspension and termination by Kinnoo">
          <p>
            Kinnoo reserves the right, at its sole discretion and at any time, with or without
            prior notice and with or without cause, to: (a) suspend or terminate your account;
            (b) remove, disable, deprecate, hide, mark as deprecated, or restrict access to any
            Agent, Agent version, or other User Content; (c) refuse to publish or accept future
            uploads from you; (d) revoke API keys or credentials; (e) impose or modify rate limits,
            quotas, or other usage restrictions; and (f) modify, suspend, or discontinue all or any
            part of the Service. Kinnoo may take any of these actions including, without
            limitation, in response to suspected violations of these Terms, in response to legal
            process or government request, to protect the security or integrity of the Service or
            its Users, to address operational, technical, or commercial concerns, or for any other
            reason it deems appropriate.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="8.3 Retention of Agent archives for compliance and security">
          <p>
            For security, audit, incident-response, dispute-resolution, and legal-compliance
            purposes, Kinnoo may, in its sole discretion, retain copies of Agent archives,
            metadata, and logs that have been published to the Service, including after the
            corresponding Agent or account has been removed from the user-facing registry. Such
            retained copies will not be made publicly accessible through the registry but may be
            preserved internally, disclosed to law-enforcement or regulatory authorities where
            permitted or required by law, or used to enforce these Terms. The fact that an Agent
            has been removed from the user-facing registry does not guarantee that all copies of
            the Agent have been or will be deleted from internal systems, backups, or third-party
            mirrors.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="8.4 Effect of termination">
          <p>
            Upon termination of your account or of these Terms for any reason, your right to
            access and use the Service will immediately cease. Sections of these Terms that by
            their nature should survive termination, including without limitation Sections 3
            (license to operate the Service, with respect to retained content), 4 (non-
            endorsement), 5 (user responsibility), 7 (intellectual property), 8.3 (retention), 9
            (disclaimers), 10 (limitation of liability), 11 (indemnification), 12 (governing law
            and dispute resolution), and 13 (general provisions), will survive.
          </p>
        </LegalSubsection>
      </LegalSection>

      <LegalSection id="disclaimers" heading="9. Disclaimers; AS-IS, AS-AVAILABLE">
        <p className="font-semibold uppercase tracking-wide text-white/90">
          The Service, including without limitation all Agents and User Content available through
          the Service, is provided to you on an &ldquo;AS IS&rdquo; and &ldquo;AS AVAILABLE&rdquo;
          basis, with all faults and without warranty of any kind.
        </p>
        <p>
          To the maximum extent permitted by applicable law, Kinnoo, on its own behalf and on
          behalf of its affiliates, licensors, and service providers, expressly disclaims all
          warranties, whether express, implied, statutory, or otherwise, with respect to the
          Service, including without limitation all implied warranties of merchantability, fitness
          for a particular purpose, title, non-infringement, accuracy, quiet enjoyment, system
          integration, and any warranties arising from course of dealing, course of performance,
          or usage of trade.
        </p>
        <p>
          Without limiting the foregoing, Kinnoo does not warrant that the Service will meet your
          requirements; that the Service will be uninterrupted, timely, secure, or error-free;
          that any defects will be corrected; that the Service or the servers that make it
          available are free of viruses, malicious code, or other harmful components; that any
          Agent or piece of User Content is accurate, reliable, complete, safe, secure, lawful, or
          fit for any particular purpose; or that any output produced by an Agent will be free of
          errors, hallucinations, biased content, harmful content, or unintended actions.
        </p>
        <p>
          You acknowledge that artificial intelligence systems, including the Agents distributed
          through the Service, may produce outputs that are inaccurate, offensive, biased,
          misleading, or otherwise inappropriate, and that Kinnoo has no control over and no
          ability to predict or prevent such outputs. You assume all risk associated with using
          any Agent or output produced by an Agent.
        </p>
      </LegalSection>

      <LegalSection id="liability" heading="10. Limitation of Liability">
        <p className="font-semibold uppercase tracking-wide text-white/90">
          To the maximum extent permitted by applicable law, in no event will Kinnoo, its
          affiliates, licensors, service providers, officers, directors, employees, agents, or
          contributors be liable to you or to any third party for any indirect, incidental,
          special, consequential, exemplary, or punitive damages, or for any loss of profits,
          revenue, goodwill, business opportunity, data, use, or substitute goods or services,
          arising out of or in connection with the Service, these Terms, or any Agent or User
          Content available through the Service, whether based on contract, tort (including
          negligence), strict liability, or any other legal theory, and whether or not Kinnoo has
          been advised of the possibility of such damages.
        </p>
        <p>
          Without limiting the foregoing, Kinnoo will not be liable for any harm, loss, or damage
          of any kind arising from or relating to: (a) the actions, outputs, errors,
          hallucinations, omissions, or autonomous behavior of any Agent, including but not
          limited to financial loss, lost or corrupted data, unauthorized communications,
          unintended API calls or transactions, infringement of third-party rights, or
          reputational harm; (b) your reliance on any information, recommendation, output, or
          other content produced by an Agent or otherwise made available through the Service;
          (c) the conduct of any other User of the Service, including any User who publishes or
          maintains an Agent that you install or run; (d) unauthorized access to or alteration of
          your transmissions or data; or (e) the temporary or permanent unavailability of the
          Service.
        </p>
        <p className="font-semibold uppercase tracking-wide text-white/90">
          To the maximum extent permitted by applicable law, the aggregate liability of Kinnoo
          and its affiliates, licensors, service providers, officers, directors, employees,
          agents, and contributors arising out of or relating to the Service or these Terms will
          not exceed the greater of (i) the total amounts, if any, that you have paid to Kinnoo
          for use of the Service in the twelve (12) months immediately preceding the event giving
          rise to the claim, or (ii) one hundred United States dollars (US$100.00).
        </p>
        <p>
          The limitations and exclusions in this Section 10 apply to the maximum extent permitted
          by applicable law, even if any limited remedy fails of its essential purpose. Some
          jurisdictions do not allow the exclusion or limitation of certain warranties or
          damages, so some of the above exclusions or limitations may not apply to you; in such
          jurisdictions, Kinnoo&rsquo;s liability is limited to the smallest amount permitted by
          law.
        </p>
      </LegalSection>

      <LegalSection id="indemnification" heading="11. Indemnification">
        <p>
          To the maximum extent permitted by applicable law, you agree to defend, indemnify, and
          hold harmless Kinnoo, its affiliates, licensors, service providers, officers, directors,
          employees, agents, and contributors from and against any and all claims, demands,
          actions, liabilities, damages, losses, costs, and expenses (including reasonable
          attorneys&rsquo; fees) arising out of or relating to: (a) your access to or use of the
          Service; (b) any User Content you submit, publish, or transmit through the Service;
          (c) any Agent you publish, install, deploy, or run; (d) your violation of these Terms,
          including the Acceptable Use Policy; (e) your violation of any law or any right of any
          third party, including any intellectual-property right or privacy right; or (f) any
          dispute between you and another User. Kinnoo reserves the right, at your expense, to
          assume the exclusive defense and control of any matter otherwise subject to
          indemnification by you, in which case you agree to cooperate with Kinnoo&rsquo;s defense
          of such matter.
        </p>
      </LegalSection>

      <LegalSection id="governing-law" heading="12. Governing Law and Dispute Resolution">
        <p>
          These Terms and any dispute arising out of or relating to these Terms or the Service
          will be governed by the laws of the State of California, United States of America,
          without regard to its conflict-of-laws principles. Subject to the following paragraph,
          the state and federal courts located in San Francisco County, California will have
          exclusive jurisdiction over any dispute arising out of or relating to these Terms or
          the Service, and you irrevocably consent to the personal jurisdiction and venue of
          those courts.
        </p>
        <p>
          Nothing in these Terms prevents either party from seeking injunctive or other equitable
          relief in any court of competent jurisdiction to protect its intellectual-property
          rights or confidential information. If any provision of these Terms is found to be
          invalid or unenforceable, that provision will be enforced to the maximum extent
          permitted by law, and the remaining provisions will remain in full force and effect.
        </p>
      </LegalSection>

      <LegalSection id="general" heading="13. General Provisions">
        <LegalSubsection heading="13.1 Changes to these Terms">
          <p>
            Kinnoo may modify these Terms from time to time. If we make material changes, we will
            update the &ldquo;Last updated&rdquo; date at the top of this page and, where
            appropriate, provide additional notice (such as a banner in the Service or an email
            to the address associated with your account). Your continued access to or use of the
            Service after the effective date of the updated Terms constitutes your acceptance of
            those updated Terms. If you do not agree to the updated Terms, you must stop using
            the Service.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="13.2 Entire agreement">
          <p>
            These Terms, together with the Privacy Policy and any other agreements that are
            expressly incorporated into these Terms by reference, constitute the entire agreement
            between you and Kinnoo regarding the Service and supersede any prior or contemporaneous
            agreements, communications, or understandings, whether written or oral, regarding the
            same subject matter.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="13.3 No waiver">
          <p>
            The failure of Kinnoo to enforce any right or provision of these Terms will not be
            deemed a waiver of that right or provision. Any waiver must be in writing and signed
            by an authorized representative of Kinnoo.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="13.4 Assignment">
          <p>
            You may not assign or transfer these Terms or any rights or obligations under these
            Terms, by operation of law or otherwise, without Kinnoo&rsquo;s prior written consent.
            Any attempted assignment in violation of this section is void. Kinnoo may freely
            assign or transfer these Terms in whole or in part, including in connection with a
            merger, acquisition, reorganization, or sale of assets.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="13.5 Independent contractors">
          <p>
            You and Kinnoo are independent contractors. Nothing in these Terms creates a
            partnership, joint venture, agency, employment, or fiduciary relationship between
            you and Kinnoo.
          </p>
        </LegalSubsection>
        <LegalSubsection heading="13.6 Contact">
          <p>
            If you have questions about these Terms, you may contact Kinnoo support through the
            channels published on the Kinnoo website, including by opening an issue at{" "}
            <a
              href="https://github.com/kinnoo-project/kinnoo/issues"
              className="text-[#FF7F00] underline hover:no-underline"
              target="_blank"
              rel="noreferrer"
            >
              https://github.com/kinnoo-project/kinnoo/issues
            </a>
            .
          </p>
        </LegalSubsection>
      </LegalSection>
    </LegalPage>
  );
}
