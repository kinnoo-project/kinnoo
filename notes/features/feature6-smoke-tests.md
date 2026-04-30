# Feature 52 Smoke Tests - Secure Login UI

Run these checks after SWE implementation for feature6.

## 1) Login card structure
1. Start app: cd web && npm run dev
2. Open http://localhost:3000/login
3. Verify centered card has:
   - Username (E-mail) field
   - Password field
   - Login button
   - Forgot Password link

Pass if:
- All required elements are present and clearly labeled.

## 2) Forgot Password navigation
1. Click Forgot Password.

Pass if:
- Route changes to /forgot-password.

## 3) Validation behavior
1. Submit empty form.
2. Submit invalid email with password.
3. Submit valid email with empty password.

Pass if:
- Submission blocked and inline validation messages shown.

## 4) Loading-state behavior
1. Submit valid credentials against delayed/mock response.
2. Observe Login button state during request.

Pass if:
- Button disables and shows loading feedback, then returns to normal.

## 5) Secure request settings
1. Inspect network request from /login submit.
2. Confirm request uses /login path and includes credentials.
3. Confirm no token is written to localStorage/sessionStorage.

Pass if:
- Session-cookie model is used and browser storage remains untouched.

## 6) Success redirect path
1. Simulate successful login response.
2. Observe client navigation target.

Pass if:
- User is routed to /registry (not /agents).

## 7) Automated tests
1. Run: cd web && npm test -- login-page

Pass if:
- Login-page suite passes for fields, validation, loading, secure fetch options, redirect.

## Sign-off checklist
- [ ] Card and fields present
- [ ] Forgot Password link works
- [ ] Validation blocks invalid input
- [ ] Loading state works
- [ ] credentials include used
- [ ] No localStorage/sessionStorage token writes
- [ ] Success redirects to /registry
- [ ] Login tests passing
