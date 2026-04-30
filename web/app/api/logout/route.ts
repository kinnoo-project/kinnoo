import { proxyToBackend } from "../../../lib/backend-proxy";

export const dynamic = "force-dynamic";

export async function POST(request: Request): Promise<Response> {
  return proxyToBackend(request, "/logout");
}
