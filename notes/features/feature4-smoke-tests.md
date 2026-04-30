# Feature 50 — Smoke Tests: MainLayout, Design System & Global Theme

Manual verification steps to confirm feature4 is complete and correct. Run these after the SWE agent marks all tasks as needs-review.

---

## 1. ThemeConfig Module Exists and Exports Tokens

```bash
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"
(cd web && node -e "
const { themeConfig } = require('./lib/theme');
console.log('bg:', themeConfig.colors.bg);
console.log('text:', themeConfig.colors.text);
console.log('accent:', themeConfig.colors.accent);
console.log('surface:', themeConfig.colors.surface);
console.log('cardBorder:', themeConfig.colors.cardBorder);
console.log('radii.card:', themeConfig.radii.card);
console.log('radii.button:', themeConfig.radii.button);
console.log('h1:', themeConfig.typography.h1);
console.log('spacing.unit:', themeConfig.spacing.unit);
console.log('fonts:', themeConfig.fonts.primary);
")
```
**Expected:** All values print and match the design spec. No `undefined`.

> Note: If lib/theme.ts uses ESM-only syntax, you may need `npx tsx web/lib/theme.ts` or verify via the automated tests instead.

## 2. MainLayout Component Exists

```bash
ls web/components/blocks/MainLayout.tsx
```
**Expected:** File exists.

## 3. Layout Wired into app/layout.tsx

```bash
grep -E "MainLayout|import.*MainLayout" web/app/layout.tsx
```
**Expected:** MainLayout is imported and used in the root layout.

## 4. Visual Check — Header Renders

```bash
(cd web && npm run dev > /tmp/kinnoo-feature4-dev.log 2>&1) &
DEV_PID=$!
sleep 5
kill "$DEV_PID" || true
wait "$DEV_PID" 2>/dev/null || true
```
Open `http://localhost:3000/` in a browser.

**Expected:**
- Sticky header at the top with dark/translucent background
- Left side: hamburger menu icon (☰ or similar)
- Right side: "Login" and "Sign Up" text buttons
- Background is pure black, text is near-white

## 5. Visual Check — Hamburger Menu Opens

Click the hamburger icon.

**Expected:**
- A slide-out sheet/drawer appears (from the left or as an overlay)
- Contains three links: "GitHub", "Docs", "Report an Issue"
- Clicking outside or pressing Escape closes it

## 6. Visual Check — Button Navigation

Click "Login" → **Expected:** navigates to `/login` page
Click "Sign Up" → **Expected:** navigates to `/signup` page

## 7. Visual Check — Responsive (Mobile)

Open DevTools → toggle device toolbar → set width to 375px.

**Expected:**
- Hamburger icon and Login/Sign Up buttons are visible
- Nothing overflows or overlaps
- Sheet drawer is full-width on mobile

Repeat at 768px — **Expected:** Header still looks correct.

## 8. Glassmorphism Effect

Scroll down on a page with enough content (add some temporary tall content if needed).

**Expected:**
- Header stays fixed at top (sticky)
- Behind the header, content blurs through (backdrop-blur effect visible)
- 1px bottom border visible (subtle white/10 line)

## 9. Automated Tests Pass

```bash
(cd web && npm test)
```
**Expected:** All tests pass:
- `__tests__/theme.test.ts` — ThemeConfig color, radii, typography, spacing assertions
- `__tests__/layout.test.tsx` — Hamburger button, Login link, Sign Up link, sheet content assertions

## 10. No Light-Mode Boilerplate Remaining

```bash
# Check that create-next-app defaults have been cleaned up
grep -r "Vercel" web/app/ || echo "Clean"
grep -r "white" web/app/globals.css || echo "Clean"
```
**Expected:** No references to Vercel logos or white backgrounds in app code.

---

## Summary Checklist

| # | Check | Pass? |
|---|-------|-------|
| 1 | ThemeConfig exports all tokens | |
| 2 | MainLayout.tsx exists | |
| 3 | MainLayout wired into layout.tsx | |
| 4 | Header renders with hamburger + buttons | |
| 5 | Hamburger opens sheet with 3 links | |
| 6 | Login → /login, Sign Up → /signup | |
| 7 | Responsive at 375px and 768px | |
| 8 | Glassmorphism + sticky + border | |
| 9 | npm test passes | |
| 10 | No light-mode boilerplate | |
