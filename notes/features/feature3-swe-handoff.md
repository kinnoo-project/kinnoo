# Feature 49 — SWE Agent Handoff: Next.js Project Initialization & Directory Structure

## Overview

Initialize the Next.js 15+ (App Router) project that will become the kinnoo web frontend. This is the foundational setup work — scaffolding, tooling, directory structure, and dependency installation. No UI components are built here; that's feature4.

## Reference Documents

- Planning doc: `notes/phases/phase5-planning.md` — Sub-phase 1
- Feature definition: `FEATURES.txt` → feature3
- Tasks: `TASKS.txt` → task104, task105, task106, task107
- Tests: `TESTS.txt` → test421–test426

## Tasks (implement in order)

### Task 282 — Initialize Next.js project in web/

**Goal:** Scaffold a brand-new Next.js 15+ project in the top-level `<redacted-path> directory.

**Steps:**
1. From the repo root, run:
   ```bash
   npx create-next-app@latest web --typescript --tailwind --app --eslint --src-dir=false --use-npm
   ```
   If Next.js 15 prompts for Turbopack, accept the default. If prompted about import alias, use `@/*`.
2. Verify `<redacted-path>` contains `next` ≥ 15, `react` ≥ 19, `typescript`, and `tailwindcss`.
3. Create `<redacted-path>` with a single line: `20`
4. Append to the root `.gitignore`:
   ```
   # Next.js web frontend
   <redacted-path>
   <redacted-path>
   ```
5. Verify: `cd web && npm run dev` starts, `npm run build` succeeds. Then kill the dev server.

**Files created/modified:**
- `<redacted-path> (entire scaffold)
- `<redacted-path>` (new)
- `.gitignore` (append)

---

### Task 283 — Configure Tailwind with dark-mode design tokens

**Goal:** Extend the Tailwind config to include all project design tokens.

**Steps:**
1. Open `<redacted-path>` and extend the `theme` section:
   ```ts
   theme: {
     extend: {
       colors: {
         kinnoo: {
           bg: '#000000',
           text: '#F9FAFB',
           accent: '#3B82F6',
           surface: '#111111',
         },
         'card-border': 'rgba(255,255,255,0.1)',
       },
       fontFamily: {
         sans: ['"Avenir Next"', '"Segoe UI"', 'sans-serif'],
       },
       borderRadius: {
         card: '8px',
         button: '4px',
       },
     },
   }
   ```
2. Update `<redacted-path>` — ensure the base layer sets:
   ```css
   body {
     background-color: #000000;
     color: #F9FAFB;
   }
   ```
   Remove or override any default light-mode styles that create-next-app may have added.
3. Run `npm run build` to verify Tailwind compiles correctly.

**Files modified:**
- `<redacted-path>`
- `<redacted-path>`

---

### Task 284 — Create directory structure and placeholder route pages

**Goal:** Set up route groups and component directories so the routing skeleton is navigable.

**Steps:**
1. Create these directories and files inside `<redacted-path>
   ```
   app/(public)/page.tsx            → export default function LandingPage() { return <h1>Landing Page</h1> }
   app/(public)/login/page.tsx      → export default function LoginPage() { return <h1>Login</h1> }
   app/(public)/signup/page.tsx     → export default function SignupPage() { return <h1>Sign Up</h1> }
   app/(auth)/layout.tsx            → export default function AuthLayout({ children }: { children: React.ReactNode }) { return <>{children}</> }
   app/(auth)/registry/page.tsx     → export default function RegistryPage() { return <h1>Registry</h1> }
   components/ui/.gitkeep
   components/blocks/.gitkeep
   lib/.gitkeep
   __tests__/.gitkeep
   ```
2. Move or delete the default `app/page.tsx` that create-next-app generates — the `(public)/page.tsx` now serves as `/`.
3. Verify all four routes are accessible in the dev server: `/`, `/login`, `/signup`, `/registry`.

**Important:** Next.js route groups use parenthesized folder names `(public)` and `(auth)` — these do NOT appear in the URL path.

**Files created:**
- All files listed above
- Remove: `<redacted-path>` (replaced by `(public)/page.tsx`)

---

### Task 285 — Install Radix UI, Lucide, and framer-motion

**Goal:** Install the core UI library dependencies needed by feature4.

**Steps:**
1. From `<redacted-path>, run:
   ```bash
   npm install @radix-ui/react-dialog @radix-ui/react-navigation-menu @radix-ui/react-slot lucide-react framer-motion
   ```
2. Verify all five appear in `<redacted-path>` under `dependencies`.
3. Run `npm run build` — confirm no dependency conflicts or type errors.

**Files modified:**
- `<redacted-path>`
- `<redacted-path>`

---

## Acceptance Criteria Checklist

| AC  | Description | Verified by |
|-----|-------------|-------------|
| AC1 | web/ contains working Next.js 15+ with TypeScript | test421 |
| AC2 | Tailwind configured with dark-mode tokens | test423 |
| AC3 | Directory structure matches spec | test424 |
| AC4 | Radix UI + Lucide + framer-motion in package.json | test426 |
| AC5 | Dev server starts, all routes accessible | test422, test425 |
| AC6 | npm run build succeeds | test422 |
| AC7 | Font family set correctly | test423 |

## Constraints

- Use **npm** as the package manager (not yarn or pnpm).
- Require **Node.js 20+** (enforced via .nvmrc).
- The `<redacted-path> directory is at the repo root, alongside `<redacted-path> and `<redacted-path>
- Do not modify anything in `<redacted-path> or `<redacted-path> for this feature.
- Remove any default light-mode boilerplate from create-next-app (e.g., the white background page, Vercel logo, etc.).
