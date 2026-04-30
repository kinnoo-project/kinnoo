"use client";

import { useCallback, useState } from "react";

const COMMAND_TEXT = "pip install kinnoo";

export default function TerminalPreview() {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(COMMAND_TEXT);
    setCopied(true);
    window.setTimeout(() => {
      setCopied(false);
    }, 1200);
  }, []);

  return (
    <div className="rounded-card border-2 border-white/25 bg-[#222222] p-4 transition hover:border-[#FF7F00] card-border-1">
      <div className="mb-3 text-xs uppercase tracking-[0.18em] text-white/50">Terminal</div>
      <div className="flex items-center justify-between gap-3">
        <code className="text-sm text-kinnoo-text sm:text-base">{COMMAND_TEXT}</code>
        <button
          type="button"
          onClick={handleCopy}
          className="rounded-button cursor-pointer border border-white/20 px-3 py-1 text-sm font-medium text-kinnoo-text transition hover:border-[#FF7F00] hover:text-[#FF7F00] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent"
          aria-label="Copy install command"
        >
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
    </div>
  );
}
