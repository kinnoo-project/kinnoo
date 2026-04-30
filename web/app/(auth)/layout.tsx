import type { ReactNode } from "react";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { fetchAuthMeServer } from "../../lib/auth-client";

export default async function AuthLayout({ children }: { children: ReactNode }) {
  const cookieStore = await cookies();
  const auth = await fetchAuthMeServer(cookieStore.toString());

  if (!auth.ok && auth.status === 429) {
    throw new Error("AUTH_RATE_LIMITED_429");
  }

  if (!auth.ok) {
    // When auth API is unavailable (for example in local dev/test without backend),
    // treat the user as unauthenticated and send them to login instead of returning 500.
    redirect("/login");
  }

  return <>{children}</>;
}
