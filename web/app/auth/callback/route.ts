import { proxyToBackend } from "../../../lib/backend-proxy";

export const dynamic = "force-dynamic";

export async function GET(request: Request): Promise<Response> {
  return proxyToBackend(request, "/auth/callback");
}