import { describe, expect, it } from "vitest";

import { buildSecurityHeaders } from "../next.config";

describe("Security headers middleware", () => {
  it("includes required baseline security headers", () => {
    const headers = buildSecurityHeaders("development");

    expect(headers["X-Frame-Options"]).toBe("DENY");
    expect(headers["X-Content-Type-Options"]).toBe("nosniff");
    expect(headers["Referrer-Policy"]).toBe("strict-origin-when-cross-origin");
    expect(headers["Content-Security-Policy"]).toContain("default-src 'self'");
    expect(headers["Content-Security-Policy"]).toContain(
      "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://static.cloudflareinsights.com",
    );
    expect(headers["Content-Security-Policy"]).toContain("connect-src 'self' https: http: ws: wss:");
    expect(headers["Content-Security-Policy"]).toContain("frame-ancestors 'none'");
  });

  it("sets HSTS only in production", () => {
    const devHeaders = buildSecurityHeaders("development");
    const prodHeaders = buildSecurityHeaders("production");

    expect(devHeaders["Strict-Transport-Security"]).toBeUndefined();
    expect(prodHeaders["Content-Security-Policy"]).toContain(
      "script-src 'self' 'unsafe-inline' https://static.cloudflareinsights.com",
    );
    expect(prodHeaders["Content-Security-Policy"]).toContain("connect-src 'self' https: wss:");
    expect(prodHeaders["Strict-Transport-Security"]).toBe(
      "max-age=31536000; includeSubDomains",
    );
  });
});
