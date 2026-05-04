import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}", "./prompts/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        agri: {
          olive: "#6f7d3a",
          tomato: "#c84630",
          wheat: "#f0c987",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
