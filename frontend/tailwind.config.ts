import type { Config } from "tailwindcss";

// Visual language carried over from the earlier GuruSetu UI: maroon primary, gold accents,
// light grey canvas, rounded white cards, black-weight uppercase section labels (ux-flows §1.1).
const config: Config = {
  content: ["./src/components/**/*.{js,ts,jsx,tsx,mdx}", "./src/app/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#8C1515", // primary: headers, buttons, titles (8.7:1 on white)
          hover: "#7A1212",
          active: "#6B1010",
          soft: "#FFF0F0", // tinted backgrounds, selected rows
          tint: "#FFF5F5",
          line: "#FFE0E0",
        },
        gold: {
          DEFAULT: "#D4AF37", // fills and badges only; never as text on white (contrast)
          soft: "#FFF9E6",
          line: "#FFE082",
          ink: "#6B1010", // text on gold fills (6.5:1)
        },
        canvas: "#F2F2F2",
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      borderRadius: {
        card: "1.5rem",
      },
    },
  },
  plugins: [],
};
export default config;
