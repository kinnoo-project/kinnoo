import type { Metadata } from "next";
import { cookies } from "next/headers";
import MainLayout from "../components/blocks/MainLayout";
import { fetchAuthMeServer } from "../lib/auth-client";
import "./globals.css";

export const metadata: Metadata = {
  title: "kinnoo",
  description: "Package and share your AI agents",
  icons: {
    icon: "/icon",
    shortcut: "/icon",
    apple: "/icon",
  },
};

function normalizeAppBaseUrl(raw: string | undefined): string {
  const trimmed = raw?.trim();
  if (!trimmed) {
    return "";
  }
  return trimmed.endsWith("/") ? trimmed.slice(0, -1) : trimmed;
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const cookieStore = await cookies();
  const auth = await fetchAuthMeServer(cookieStore.toString());
  const initialTenantSlug = auth.ok ? auth.tenantSlug : null;
  const appBaseUrl = normalizeAppBaseUrl(process.env.NEXT_PUBLIC_APP_BASE_URL);

  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full">
        <MainLayout initialTenantSlug={initialTenantSlug} appBaseUrl={appBaseUrl}>
          {children}
        </MainLayout>
      </body>
    </html>
  );
}
