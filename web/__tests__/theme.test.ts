import { describe, expect, it } from "vitest";

import { themeConfig } from "../lib/theme";

describe("themeConfig", () => {
  it("exports correct color tokens", () => {
    expect(themeConfig.colors.bg).toBe("#000000");
    expect(themeConfig.colors.text).toBe("#F9FAFB");
    expect(themeConfig.colors.accent).toBe("#FF7F00");
    expect(themeConfig.colors.surface).toBe("#111111");
    expect(themeConfig.colors.cardBorder).toBe("rgba(255,255,255,0.1)");
  });

  it("exports correct radii, typography, spacing, and font tokens", () => {
    expect(themeConfig.radii.card).toBe("8px");
    expect(themeConfig.radii.button).toBe("4px");

    expect(themeConfig.typography.h1).toBe("48px");
    expect(themeConfig.typography.h2).toBe("32px");
    expect(themeConfig.typography.h3).toBe("24px");
    expect(themeConfig.typography.body).toBe("16px");

    expect(themeConfig.spacing.unit).toBe(4);
    expect(themeConfig.spacing.scale).toEqual([8, 12, 16, 24, 32, 48]);
    expect(themeConfig.fonts.primary).toContain("Avenir Next");
  });
});
