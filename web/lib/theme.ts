export type ThemeConfig = {
  colors: {
    bg: "#000000";
    text: "#F9FAFB";
    accent: "#FF7F00";
    surface: "#111111";
    cardBorder: "rgba(255,255,255,0.1)";
  };
  radii: {
    card: "8px";
    button: "4px";
  };
  typography: {
    h1: "48px";
    h2: "32px";
    h3: "24px";
    body: "16px";
  };
  spacing: {
    unit: 4;
    scale: readonly [8, 12, 16, 24, 32, 48];
  };
  fonts: {
    primary: '"Avenir Next", "Segoe UI", sans-serif';
  };
};

const rawThemeConfig: ThemeConfig = {
  colors: {
    bg: "#000000",
    text: "#F9FAFB",
    accent: "#FF7F00",
    surface: "#111111",
    cardBorder: "rgba(255,255,255,0.1)",
  },
  radii: {
    card: "8px",
    button: "4px",
  },
  typography: {
    h1: "48px",
    h2: "32px",
    h3: "24px",
    body: "16px",
  },
  spacing: {
    unit: 4,
    scale: [8, 12, 16, 24, 32, 48] as const,
  },
  fonts: {
    primary: '"Avenir Next", "Segoe UI", sans-serif',
  },
};

export const themeConfig = Object.freeze(rawThemeConfig);
