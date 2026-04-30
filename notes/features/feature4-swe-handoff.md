# Feature 50 — SWE Agent Handoff: MainLayout, Design System & Global Theme

## Overview

Build the visual skeleton of the kinnoo web frontend: the global layout header with hamburger menu and auth buttons, plus the design token module that all future components will reference. This feature depends on feature3 being complete (the Next.js project must already be scaffolded).

## Reference Documents

- Planning doc: `notes/phases/phase5-planning.md` — Sub-phase 1
- Feature definition: `FEATURES.txt` → feature4
- Tasks: `TASKS.txt` → task108, task109, task110, task111
- Tests: `TESTS.txt` → test427–test431
- Design tokens reference: See feature3 AC or the planning doc's "Design Tokens" section

## Design Tokens (quick reference)

| Token | Value |
|-------|-------|
| bg | `#000000` |
| text | `#F9FAFB` |
| accent | `#3B82F6` |
| surface | `#111111` |
| cardBorder | `rgba(255,255,255,0.1)` |
| radii.card | `8px` |
| radii.button | `4px` |
| typography.h1 | `48px` |
| typography.h2 | `32px` |
| typography.h3 | `24px` |
| typography.body | `16px` |
| spacing.unit | `4` (px) |
| fonts.primary | `"Avenir Next", "Segoe UI", sans-serif` |

## Tasks (implement in order)

### Task 286 — Create ThemeConfig design token module

**Goal:** Single source of truth for all design tokens, exported as a frozen TypeScript object.

**Steps:**
1. Create `web/lib/theme.ts`:
   ```ts
   export const themeConfig = {
     colors: {
       bg: '#000000',
       text: '#F9FAFB',
       accent: '#3B82F6',
       surface: '#111111',
       cardBorder: 'rgba(255,255,255,0.1)',
     },
     radii: {
       card: '8px',
       button: '4px',
     },
     typography: {
       h1: '48px',
       h2: '32px',
       h3: '24px',
       body: '16px',
     },
     spacing: {
       unit: 4,
       scale: [8, 12, 16, 24, 32, 48],
     },
     fonts: {
       primary: '"Avenir Next", "Segoe UI", sans-serif',
     },
   } as const;

   export type ThemeConfig = typeof themeConfig;
   ```
2. Verify `npm run build` passes with this module.

**Files created:**
- `web/lib/theme.ts`

---

### Task 287 — Build MainLayout header with hamburger menu and auth buttons

**Goal:** Create the persistent header visible on every page.

**Steps:**
1. Create `web/components/blocks/MainLayout.tsx`:
   ```
   Header structure:
   ┌──────────────────────────────────────────────┐
   │ [☰ Menu]               [Login]  [Sign Up]    │
   └──────────────────────────────────────────────┘
   ```
2. **Top-left:** A button with the Lucide `Menu` icon. On click, it opens a Radix UI Dialog (configured as a slide-out sheet/drawer from the left). The sheet contains three links:
   - **GitHub** → external link to the kinnoo GitHub repo (use `#` as placeholder URL for now)
   - **Docs** → external link (`#` placeholder)
   - **Report an Issue** → external link (`#` placeholder)
3. **Top-right:** Two buttons styled as ghost variants (transparent background, text color `#F9FAFB`, hover: slight background opacity shift):
   - **Login** — wraps a `next/link` to `/login`
   - **Sign Up** — wraps a `next/link` to `/signup`
   Use Radix UI `Slot` for button composability if helpful.
4. **Header styling:**
   - `position: sticky; top: 0; z-index: 50;`
   - Background: `bg-black/50` with `backdrop-blur-md` (glassmorphism)
   - Bottom border: `border-b border-white/10`
   - Flex layout: `flex items-center justify-between px-4 h-14`
5. Wire MainLayout into `web/app/layout.tsx`:
   ```tsx
   import { MainLayout } from '@/components/blocks/MainLayout';

   export default function RootLayout({ children }: { children: React.ReactNode }) {
     return (
       <html lang="en">
         <body>
           <MainLayout>
             <main>{children}</main>
           </MainLayout>
         </body>
       </html>
     );
   }
   ```

**Files created/modified:**
- `web/components/blocks/MainLayout.tsx` (new)
- `web/app/layout.tsx` (modified)

---

### Task 288 — Make layout responsive for mobile viewports

**Goal:** Ensure header works on mobile without overflow or overlap.

**Steps:**
1. Review the header at these widths: 375px, 640px, 768px, 1024px.
2. Add Tailwind responsive utilities:
   - Sheet drawer: `w-full sm:w-80` (full width on mobile, fixed width on larger)
   - Button text: Consider `text-sm` on mobile; if very narrow (< 400px), Sign Up could use shorter text or smaller font.
   - Use `gap-2` between buttons, `px-3 sm:px-4` for header padding.
3. Ensure the hamburger icon and buttons fit on a single row at 375px.

**Files modified:**
- `web/components/blocks/MainLayout.tsx`

---

### Task 289 — Write smoke tests for layout and design tokens

**Goal:** Automated tests that verify the layout renders correctly and design tokens are accurate.

**Steps:**
1. Install test dependencies (if not already present):
   ```bash
   npm install -D vitest @testing-library/react @testing-library/jest-dom @vitejs/plugin-react jsdom
   ```
2. Create `web/vitest.config.ts`:
   ```ts
   import { defineConfig } from 'vitest/config';
   import react from '@vitejs/plugin-react';
   import path from 'path';

   export default defineConfig({
     plugins: [react()],
     test: {
       environment: 'jsdom',
       globals: true,
       setupFiles: [],
     },
     resolve: {
       alias: {
         '@': path.resolve(__dirname, '.'),
       },
     },
   });
   ```
3. Create `web/__tests__/theme.test.ts`:
   - Import `themeConfig` from `@/lib/theme`
   - Assert all color values match spec
   - Assert radii, typography, spacing, and font values match
4. Create `web/__tests__/layout.test.tsx`:
   - Render `MainLayout` with a child element
   - Assert hamburger menu button is in the DOM (find by aria-label or role)
   - Assert "Login" link/button is present
   - Assert "Sign Up" link/button is present
   - Click hamburger → assert "GitHub", "Docs", "Report an Issue" links appear
5. Add a `"test"` script to `web/package.json`: `"test": "vitest run"`
6. Run `npm test` and verify all tests pass.

**Files created/modified:**
- `web/vitest.config.ts` (new)
- `web/__tests__/theme.test.ts` (new)
- `web/__tests__/layout.test.tsx` (new)
- `web/package.json` (add test script + dev dependencies)

---

## Acceptance Criteria Checklist

| AC  | Description | Verified by |
|-----|-------------|-------------|
| AC1 | ThemeConfig exports all design tokens | test427, test428 |
| AC2 | Header renders hamburger + Login + Sign Up | test429 |
| AC3 | Hamburger opens sheet with 3 links | test430 |
| AC4 | Login → /login, Sign Up → /signup | test429 (link href) |
| AC5 | Dark theme, 1px borders, glassmorphism | Visual inspection |
| AC6 | Responsive on mobile viewports | test431 |
| AC7 | Smoke tests pass | test427–test430 |

## Constraints

- Use **Radix UI Dialog** as the sheet/drawer primitive — do not install a separate sheet library.
- Use **Lucide React** for the Menu icon — do not use other icon libraries.
- Reference `themeConfig` tokens where possible instead of hardcoding hex values in JSX.
- All components must be TypeScript with proper type annotations.
- The hamburger sheet links can use `#` as placeholder URLs for now (they'll be updated in later features).
- All tests must pass `npm test` before marking tasks as needs-review.
