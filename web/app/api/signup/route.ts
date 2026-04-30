import { proxyToBackend } from "../../../lib/backend-proxy";

export const dynamic = "force-dynamic";

async function proxySignupOrFallback(request: Request): Promise<Response> {
  const signupResponse = await proxyToBackend(request, "/signup");
  if (signupResponse.status !== 404) {
    return signupResponse;
  }

  // Compatibility fallback for environments where backend /signup is not deployed yet.
  return proxyToBackend(request, "/login");
}

export async function GET(request: Request): Promise<Response> {
  return proxySignupOrFallback(request);
}

export async function POST(request: Request): Promise<Response> {
  return proxySignupOrFallback(request);
}
