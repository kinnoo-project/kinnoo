import type { NextConfig } from "next";

export function buildSecurityHeaders(nodeEnv: string | undefined): Record<string, string> {
	const isProduction = (nodeEnv ?? "").toLowerCase() === "production";
	const contentSecurityPolicy = isProduction
		? [
				"default-src 'self'",
				"script-src 'self' 'unsafe-inline' https://static.cloudflareinsights.com",
				"style-src 'self' 'unsafe-inline'",
				"img-src 'self' data: blob:",
				"font-src 'self' data:",
				"connect-src 'self' https: wss:",
				"frame-ancestors 'none'",
			].join("; ")
		: [
				"default-src 'self'",
				"script-src 'self' 'unsafe-inline' 'unsafe-eval' https://static.cloudflareinsights.com",
				"style-src 'self' 'unsafe-inline'",
				"img-src 'self' data: blob:",
				"font-src 'self' data:",
				"connect-src 'self' https: http: ws: wss:",
				"frame-ancestors 'none'",
			].join("; ");

	const headers: Record<string, string> = {
		"X-Frame-Options": "DENY",
		"X-Content-Type-Options": "nosniff",
		"Referrer-Policy": "strict-origin-when-cross-origin",
		"Content-Security-Policy": contentSecurityPolicy,
	};

	if (isProduction) {
		headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains";
	}

	return headers;
}

const nextConfig: NextConfig = {
	async headers() {
		const securityHeaders = buildSecurityHeaders(process.env.NODE_ENV);
		return [
			{
				source: "/:path*",
				headers: Object.entries(securityHeaders).map(([key, value]) => ({
					key,
					value,
				})),
			},
		];
	},
};

export default nextConfig;
