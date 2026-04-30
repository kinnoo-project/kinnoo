const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
  "host",
  "content-length",
]);

function normalizeBackendUrl(rawUrl: string | undefined): string {
  const trimmed = rawUrl?.trim();
  if (!trimmed) {
    return "http://localhost:8000";
  }
  return trimmed.endsWith("/") ? trimmed.slice(0, -1) : trimmed;
}

function getBackendUrl(): string {
  return normalizeBackendUrl(process.env.BACKEND_URL ?? process.env.KINNOO_API_BASE_URL);
}

function copyHeaders(source: Headers): Headers {
  const nextHeaders = new Headers();

  // Preserve multiple Set-Cookie headers; using set() would overwrite earlier cookies.
  const maybeSetCookie = source as Headers & { getSetCookie?: () => string[] };
  const setCookies = maybeSetCookie.getSetCookie?.() ?? [];
  if (setCookies.length > 0) {
    for (const cookie of setCookies) {
      nextHeaders.append("set-cookie", cookie);
    }
  }

  source.forEach((value, key) => {
    const normalizedKey = key.toLowerCase();
    if (HOP_BY_HOP_HEADERS.has(normalizedKey) || normalizedKey === "set-cookie") {
      return;
    }
    nextHeaders.append(key, value);
  });
  return nextHeaders;
}

export async function proxyToBackend(request: Request, targetPath: string): Promise<Response> {
  const backendUrl = getBackendUrl();
  const incomingUrl = new URL(request.url);
  const targetUrl = new URL(`${backendUrl}${targetPath}`);
  targetUrl.search = incomingUrl.search;

  const requestHeaders = copyHeaders(request.headers);
  requestHeaders.set("x-forwarded-host", incomingUrl.host);
  requestHeaders.set("x-forwarded-proto", incomingUrl.protocol.replace(":", ""));

  const init: RequestInit = {
    method: request.method,
    headers: requestHeaders,
    redirect: "manual",
    body: request.method === "GET" || request.method === "HEAD" ? undefined : await request.arrayBuffer(),
  };

  const backendResponse = await fetch(targetUrl, init);
  const responseHeaders = copyHeaders(backendResponse.headers);

  return new Response(backendResponse.body, {
    status: backendResponse.status,
    statusText: backendResponse.statusText,
    headers: responseHeaders,
  });
}
