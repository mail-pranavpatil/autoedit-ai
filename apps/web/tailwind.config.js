/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f1115",
        panel: "#171a21",
        line: "#2a3140",
        muted: "#8b93a7",
        accent: "#6ee7b7",
        foreground: "#e8ecf4",
        // Secondary/category accents — categories, presets, creative
        // highlights only. Never status semantics; StatusBadge's own
        // emerald/red/sky/amber mapping stays separate. Suffixed to avoid
        // silently replacing Tailwind's own lime/teal/yellow scales.
        "lime-accent": "#C6F24C",
        "lavender-accent": "#C4B5F5",
        "coral-accent": "#FF9B85",
        "yellow-accent": "#FFDD75",
        "teal-accent": "#6FD3E8",
      },
      borderRadius: {
        xl: "16px",
        "2xl": "20px",
      },
    },
  },
  plugins: [],
};
