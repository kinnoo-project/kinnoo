# Feature 51 Smoke Tests - Landing Page

Run these checks after SWE implementation for feature5.

## 1) Hero content exactness
1. Start app: cd web && npm run dev
2. Open <redacted-url>
3. Verify h1 text exactly:
   Package, publish, share your AI agents with the world
4. Verify sub-headline exactly matches planning copy.

Pass if:
- Both strings match exactly, including punctuation.

## 2) Terminal Preview component
1. Verify terminal block contains: pip install kinnoo
2. Click copy button.
3. Confirm visible success feedback appears (example: Copied!).

Pass if:
- Command text is visible and copy feedback appears.

## 3) Six feature cards and exact copy
1. Scroll to Features section.
2. Confirm six cards render.
3. Validate each card header and subtext against planning doc.

Pass if:
- All six headers and subtexts match exactly.

## 4) Hover and focus affordances
1. Hover each feature card on desktop.
2. Keyboard-tab to copy button and interactive items.
3. Check visible focus styles.

Pass if:
- Hover state appears and focus ring is visible.

## 5) Responsive layout
1. Test at 375px, 768px, 1280px widths.
2. Confirm no clipping/overlap in hero, terminal block, or cards.

Pass if:
- Content remains readable with no horizontal overflow.

## 6) Automated tests
1. Run: cd web && npm test -- landing-page

Pass if:
- Landing-page suite passes and covers hero, terminal preview, and features.

## Sign-off checklist
- [ ] Hero title exact
- [ ] Sub-headline exact
- [ ] Terminal Preview + copy works
- [ ] Six cards exact
- [ ] Responsive at 3 breakpoints
- [ ] Landing tests passing
