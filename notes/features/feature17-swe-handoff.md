# Feature 110 — SWE Handoff: Landing Page Update for Beta

## Context
Update the Next.js web frontend for invite-only beta. Remove open registration, add beta messaging, add obfuscated email link.

## Files to Modify
- `web/` directory — Next.js frontend files:
  - Landing/home page: add "Invite-Only Beta" messaging
  - Registration page: add invite token field, remove open-access language
  - Login page: add "Forgot Password?" link (other feature (unreferenced))
  - Navigation: ensure consistent beta branding

## Key Changes
1. **Landing page hero**: "kinnoo — Beta" tagline, brief description, "Interested? Email us" CTA
2. **Email obfuscation**: Render email via JavaScript (not plain HTML)
   ```js
   // Example: build mailto link dynamically
   const user = 'contact';
   const domain = 'kinnoo.ai';
   document.getElementById('email-link').href = `mailto:${user}@${domain}`;
   ```
3. **Registration page**: Add invite token field pre-filled from `?token=` query param
4. **Static export**: Ensure `output: 'export'` in `next.config.ts` for Cloudflare Pages

## Implementation Notes
- `web/next.config.ts` (~40 lines) already has rewrite config — may need updates for API URL
- Static export means no server-side rendering — all pages must be client-rendered
- Keep the design minimal — no new design system or major redesign
- Email obfuscation: simple JS concatenation defeats most email scrapers

## Testing
- Landing page renders "Invite-Only Beta" messaging
- Email link works but is not in plain HTML source
- Registration page shows invite token field
- `next build && next export` succeeds
- All pages render correctly in browser

## Dependencies
- None (can be done independently)

## Acceptance Criteria Summary
1. "Invite-Only Beta" messaging on landing page
2. No open registration form
3. Email obfuscated via JavaScript
4. Static export works
