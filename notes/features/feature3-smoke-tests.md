# Feature 49 — Smoke Tests: Next.js Project Initialization & Directory Structure

Manual verification steps to confirm feature3 is complete and correct. Run these after the SWE agent marks all tasks as needs-review.

---

## 1. Project Scaffold Exists

```bash
# From repo root:
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"
ls web/package.json web/tsconfig.json web/tailwind.config.ts web/next.config.ts web/.nvmrc
```
**Expected:** All five files exist. No "No such file" errors.

## 2. Node Version Pinned

```bash
cat web/.nvmrc
```
**Expected:** Output is `20`

## 3. Dependencies Correct

```bash
(cd web && node -e "
const pkg = require('./package.json');
const deps = pkg.dependencies;
console.log('next:', deps.next);
console.log('react:', deps.react);
console.log('typescript:', deps.typescript || pkg.devDependencies?.typescript);
console.log('tailwindcss:', deps.tailwindcss || pkg.devDependencies?.tailwindcss);
console.log('@radix-ui/react-dialog:', deps['@radix-ui/react-dialog']);
console.log('@radix-ui/react-navigation-menu:', deps['@radix-ui/react-navigation-menu']);
console.log('@radix-ui/react-slot:', deps['@radix-ui/react-slot']);
console.log('lucide-react:', deps['lucide-react']);
console.log('framer-motion:', deps['framer-motion']);
")
```
**Expected:** All nine packages print a version (not `undefined`). `next` ≥ 15, `react` ≥ 19.

## 4. Design Tokens in Tailwind Config

```bash
grep -E "kinnoo|Avenir|card-border" web/tailwind.config.ts
```
**Expected:** Matches for custom color names (`kinnoo`, `card-border`) and font family (`Avenir`).

## 5. Global CSS Dark Mode

```bash
grep -E "background|color.*F9FAFB|000000" web/app/globals.css
```
**Expected:** Body background is `#000000`, text color is `#F9FAFB`.

## 6. Font Family Set

```bash
grep -i "avenir" web/tailwind.config.ts
```
**Expected:** `"Avenir Next"` appears in the fontFamily config.

## 7. Directory Structure Complete

```bash
ls web/app/\(public\)/page.tsx \
   web/app/\(public\)/login/page.tsx \
   web/app/\(public\)/signup/page.tsx \
   web/app/\(auth\)/layout.tsx \
   web/app/\(auth\)/registry/page.tsx
ls -d web/components/ui web/components/blocks web/lib web/__tests__
```
**Expected:** All files and directories exist.

## 8. Build Succeeds

```bash
(cd web && npm run build)
```
**Expected:** Exit code 0, no TypeScript or compilation errors in output.

## 9. Dev Server Starts and Routes Work

```bash
(cd web && npm run dev > /tmp/kinnoo-feature3-dev.log 2>&1) &
DEV_PID=$!

# Wait for dev server to become reachable (max ~60s)
for i in {1..30}; do
   if curl -fsS --connect-timeout 2 --max-time 5 http://localhost:3000/ >/dev/null; then
      break
   fi
   sleep 2
done

for route in / /login /signup /registry; do
   code=$(curl -sS --connect-timeout 5 --max-time 15 -o /dev/null -w "%{http_code}" "http://localhost:3000${route}")
   echo "${route} -> ${code}"
done

kill "$DEV_PID" || true
wait "$DEV_PID" 2>/dev/null || true
```
**Expected:** All four curl commands return `200`.
For `/registry`, `307` redirect to login is also acceptable when unauthenticated.

## 10. Root .gitignore Updated

```bash
grep "web/node_modules" .gitignore && grep "web/.next" .gitignore
```
**Expected:** Both patterns found in `.gitignore`.

---

## Summary Checklist

| # | Check | Pass? |
|---|-------|-------|
| 1 | Scaffold files exist | |
| 2 | .nvmrc = 20 | |
| 3 | All 9 deps have versions | |
| 4 | Tailwind tokens present | |
| 5 | Dark mode globals.css | |
| 6 | Avenir Next font | |
| 7 | Directory structure complete | |
| 8 | npm run build succeeds | |
| 9 | All 4 routes return 200 | |
| 10 | .gitignore updated | |
