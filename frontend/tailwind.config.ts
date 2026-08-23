import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      borderRadius: {
        "32px": "32px",
        "24px": "24px",
        "20px": "20px",
      },
      colors: {
        obsidian: {
          950: "#0b0f17",
          900: "#101726",
          850: "#151e33",
          800: "#1c2842",
          700: "#2a3b61",
        },
        accent: {
          cyan: "#22d3ee",
          indigo: "#6366f1",
          emerald: "#10b981",
          amber: "#f59e0b",
          rose: "#f43f5e",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
