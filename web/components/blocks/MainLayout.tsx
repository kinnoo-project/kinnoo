"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { Menu, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import { themeConfig } from "../../lib/theme";

type HeaderButtonProps = {
  href: string;
  children: ReactNode;
};

function HeaderButton({ href, children }: HeaderButtonProps) {
  return (
    <Link
      href={href}
      className="inline-flex h-9 items-center justify-center rounded-button border border-white/20 px-3 text-sm font-medium text-kinnoo-text transition hover:border-[#FF7F00] hover:text-[#FF7F00] max-[399px]:px-2 max-[399px]:text-xs"
      style={{ borderRadius: themeConfig.radii.button }}
    >
      {children}
    </Link>
  );
}

type MainLayoutProps = {
  children: ReactNode;
  initialTenantSlug?: string | null;
  appBaseUrl?: string;
};

function readCookieValue(name: string): string {
  const cookiePrefix = `${name}=`;
  const entry = document.cookie
    .split(";")
    .map((item) => item.trim())
    .find((item) => item.startsWith(cookiePrefix));
  if (!entry) {
    return "";
  }
  return decodeURIComponent(entry.slice(cookiePrefix.length));
}

function submitLogoutForm(csrfToken: string): void {
  const form = document.createElement("form");
  form.method = "POST";
  form.action = "/api/logout";

  const csrfInput = document.createElement("input");
  csrfInput.type = "hidden";
  csrfInput.name = "csrf_token";
  csrfInput.value = csrfToken;
  form.appendChild(csrfInput);

  document.body.appendChild(form);
  form.submit();
}

export default function MainLayout({ children, initialTenantSlug = null, appBaseUrl = "" }: MainLayoutProps) {
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const profileMenuContainerRef = useRef<HTMLDivElement | null>(null);

  const resolvedBaseUrl = useMemo(() => {
    const trimmed = appBaseUrl.trim();
    if (!trimmed) {
      return "";
    }
    return trimmed.endsWith("/") ? trimmed.slice(0, -1) : trimmed;
  }, [appBaseUrl]);

  const appHref = (path: string): string => {
    if (!resolvedBaseUrl) {
      return path;
    }
    return `${resolvedBaseUrl}${path}`;
  };

  const isAuthenticated = Boolean(initialTenantSlug);
  const tenantInitial = initialTenantSlug?.trim().charAt(0).toUpperCase() || "U";

  useEffect(() => {
    if (!isProfileMenuOpen) {
      return;
    }

    const handleDocumentPointerDown = (event: MouseEvent) => {
      const container = profileMenuContainerRef.current;
      if (!container) {
        return;
      }
      if (container.contains(event.target as Node)) {
        return;
      }
      setIsProfileMenuOpen(false);
    };

    document.addEventListener("mousedown", handleDocumentPointerDown);
    return () => {
      document.removeEventListener("mousedown", handleDocumentPointerDown);
    };
  }, [isProfileMenuOpen]);

  return (
    <div className="min-h-screen bg-kinnoo-bg text-kinnoo-text">
      <header
        className="sticky top-0 z-50 border-b border-white/10 glass-surface"
        style={{
          borderColor: themeConfig.colors.cardBorder,
          color: themeConfig.colors.text,
        }}
      >
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-2 px-4 py-3">
          <div className="flex items-center gap-3">
            <Dialog.Root>
              <Dialog.Trigger asChild>
                <button
                  type="button"
                  aria-label="Open menu"
                  className="inline-flex h-10 w-10 items-center justify-center rounded-button border border-white/20 text-kinnoo-text transition hover:border-white/30"
                  style={{ borderRadius: themeConfig.radii.button }}
                >
                  <Menu size={18} />
                </button>
              </Dialog.Trigger>

              <Dialog.Portal>
                <Dialog.Overlay className="fixed inset-0 bg-black/60" />
                <Dialog.Content
                  className="fixed top-16 rounded-card border border-white/10 bg-[#222222] p-4 shadow-xl"
                  style={{
                    borderColor: themeConfig.colors.cardBorder,
                    left: "max(1rem, calc((100vw - 72rem) / 2 + 1rem))",
                    width: "min(20rem, calc(100vw - 2rem))",
                  }}
                >
                  <div className="mb-4 flex items-center justify-between">
                    <Dialog.Title className="text-base font-semibold">Menu</Dialog.Title>
                    <Dialog.Description className="sr-only">
                      Quick navigation links for project resources.
                    </Dialog.Description>
                    <Dialog.Close asChild>
                      <button
                        type="button"
                        aria-label="Close menu"
                        className="inline-flex h-8 w-8 items-center justify-center rounded-button border border-white/20"
                      >
                        <X size={16} />
                      </button>
                    </Dialog.Close>
                  </div>
                  <nav className="flex flex-col gap-3 text-sm">
                    <a
                      href="https://github.com/kinnoo-project/kinnoo"
                      target="_blank"
                      rel="noreferrer"
                      className="text-kinnoo-text transition hover:text-[#FF7F00]"
                    >
                      GitHub
                    </a>
                    <a
                      href="https://github.com/kinnoo-project/kinnoo/tree/main/docs"
                      target="_blank"
                      rel="noreferrer"
                      className="text-kinnoo-text transition hover:text-[#FF7F00]"
                    >
                      Docs
                    </a>
                    <a
                      href="https://github.com/kinnoo-project/kinnoo/issues"
                      target="_blank"
                      rel="noreferrer"
                      className="text-kinnoo-text transition hover:text-[#FF7F00]"
                    >
                      Report an Issue
                    </a>
                  </nav>
                </Dialog.Content>
              </Dialog.Portal>
            </Dialog.Root>

            <Link
              href="/"
              className="text-lg font-medium tracking-wide text-kinnoo-text transition hover:text-[#FF7F00] sm:text-xl"
            >
              kinnoo
            </Link>
          </div>

          <div className="flex shrink-0 items-center gap-1 sm:gap-2">
            {isAuthenticated ? (
              <>
                <HeaderButton href={appHref("/registry")}>{initialTenantSlug}</HeaderButton>
                <div ref={profileMenuContainerRef} className="relative">
                  <button
                    type="button"
                    aria-label="Open profile menu"
                    onClick={() => {
                      setIsProfileMenuOpen((current) => !current);
                    }}
                    className="inline-flex h-9 w-9 cursor-pointer items-center justify-center rounded-full border border-white/20 text-sm font-semibold text-kinnoo-text transition hover:border-[#FF7F00] hover:text-[#FF7F00]"
                  >
                    <span aria-hidden="true">{tenantInitial}</span>
                  </button>
                  {isProfileMenuOpen ? (
                    <div className="absolute right-0 top-full z-50 mt-2 min-w-[9rem] rounded-card border border-white/15 bg-[#222222] py-1 shadow-xl">
                      <Link
                        href={appHref("/settings")}
                        onClick={() => {
                          setIsProfileMenuOpen(false);
                        }}
                        className="block px-4 py-2 text-sm text-kinnoo-text transition hover:text-[#FF7F00]"
                      >
                        Settings
                      </Link>
                      <button
                        type="button"
                        onClick={() => {
                          setIsProfileMenuOpen(false);
                          submitLogoutForm(readCookieValue("kinnoo_csrf"));
                        }}
                        className="block w-full cursor-pointer px-4 py-2 text-left text-sm text-kinnoo-text transition hover:text-[#FF7F00]"
                      >
                        Logout
                      </button>
                    </div>
                  ) : null}
                </div>
              </>
            ) : (
              <>
                <HeaderButton href="/login">Login</HeaderButton>
                <HeaderButton href="/signup">Sign Up</HeaderButton>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl px-4 py-6">{children}</main>

      <footer
        className="mt-12 border-t border-white/10 text-sm text-white/60"
        style={{ borderColor: themeConfig.colors.cardBorder }}
      >
        <div className="mx-auto flex w-full max-w-6xl flex-col items-start justify-between gap-3 px-4 py-6 sm:flex-row sm:items-center">
          <p>© {new Date().getFullYear()} Kinnoo</p>
          <nav aria-label="Legal" className="flex flex-wrap items-center gap-x-6 gap-y-2">
            <Link
              href="/terms"
              className="text-white/70 transition hover:text-[#FF7F00]"
            >
              Terms of Service
            </Link>
            <Link
              href="/privacy"
              className="text-white/70 transition hover:text-[#FF7F00]"
            >
              Privacy Policy
            </Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
