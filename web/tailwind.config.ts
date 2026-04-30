import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        kinnoo: {
          bg: "#000000",
          text: "#F9FAFB",
          accent: "#FF7F00",
          surface: "#111111",
        },
        "card-border": "rgba(255,255,255,0.1)",
      },
      fontFamily: {
        sans: ['"Avenir Next"', '"Segoe UI"', "sans-serif"],
      },
      borderRadius: {
        card: "8px",
        button: "4px",
      },
      spacing: {
        2: "8px",
        3: "12px",
        4: "16px",
        6: "24px",
        8: "32px",
        12: "48px",
      },
    },
  },
  plugins: [],
};

export default config;
