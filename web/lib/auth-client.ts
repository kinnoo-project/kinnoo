export type LoginResult = {
  ok: boolean;
  status: number;
};

export type AuthMeResult = {
  ok: boolean;
  status: number;
  tenantSlug: string | null;
  username: string | null;
};

function isSuccessfulLoginResponse(response: Response): boolean {
  if (response.ok) {
    return true;
  }

  // With redirect: "manual", successful auth redirects can appear as opaque
  // redirects (status 0) depending on browser/runtime behavior.
  if (response.type === "opaqueredirect") {
    return true;
  }

  // Redirect-based auth flows can surface standard redirect responses
  // depending on browser/runtime behavior.
  return [302, 303, 307, 308].includes(response.status);
}

export async function startLoginRedirect(): Promise<LoginResult> {
  const response = await fetch("/api/login", {
    method: "GET",
    credentials: "include",
    cache: "no-store",
    redirect: "manual",
  });

  return {
    ok: isSuccessfulLoginResponse(response),
    status: response.status,
  };
}

export async function fetchAuthMeServer(cookieHeader: string): Promise<AuthMeResult> {
  const backendBaseUrl = (
    process.env.BACKEND_URL ?? process.env.KINNOO_API_BASE_URL ?? "http://127.0.0.1:8000"
  ).replace(/\/+$/, "");

  try {
    const response = await fetch(`${backendBaseUrl}/api/auth/me`, {
      method: "GET",
      cache: "no-store",
      headers: {
        Accept: "application/json",
        ...(cookieHeader ? { Cookie: cookieHeader } : {}),
      },
    });

    let tenantSlug: string | null = null;
    let username: string | null = null;
    if (response.ok) {
      try {
        const payload = (await response.json()) as { tenant_slug?: unknown; username?: unknown };
        if (typeof payload.tenant_slug === "string" && payload.tenant_slug.trim()) {
          tenantSlug = payload.tenant_slug.trim();
        }
        if (typeof payload.username === "string" && payload.username.trim()) {
          username = payload.username.trim();
        }
      } catch {
        // Keep auth status even if payload parsing fails.
      }
    }

    return {
      ok: response.ok,
      status: response.status,
      tenantSlug,
      username,
    };
  } catch {
    return {
      ok: false,
      status: 503,
      tenantSlug: null,
      username: null,
    };
  }
}
