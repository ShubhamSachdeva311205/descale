/** @type {import('tailwindcss').Config} */
const channel = (name) => `oklch(var(${name}) / <alpha-value>)`

export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: channel("--bg"),
        surface: channel("--surface"),
        "surface-2": channel("--surface-2"),
        "border-strong": channel("--border-strong"),
        ink: channel("--ink"),
        "ink-muted": channel("--ink-muted"),
        "ink-faint": channel("--ink-faint"),
        signal: channel("--signal"),
        "signal-ink": channel("--signal-ink"),

        // shadcn-compatible aliases
        background: channel("--background"),
        foreground: channel("--foreground"),
        card: channel("--card"),
        "card-foreground": channel("--card-foreground"),
        popover: channel("--popover"),
        "popover-foreground": channel("--popover-foreground"),
        primary: channel("--primary"),
        "primary-foreground": channel("--primary-foreground"),
        secondary: channel("--secondary"),
        "secondary-foreground": channel("--secondary-foreground"),
        muted: channel("--muted"),
        "muted-foreground": channel("--muted-foreground"),
        accent: channel("--accent"),
        "accent-foreground": channel("--accent-foreground"),
        destructive: channel("--destructive"),
        "destructive-foreground": channel("--destructive-foreground"),
        border: channel("--border"),
        input: channel("--input"),
        ring: channel("--ring"),
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "fade-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(220%)" },
        },
        "pulse-soft": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.55" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.24s cubic-bezier(0.22, 1, 0.36, 1) both",
        scan: "scan 1.6s cubic-bezier(0.4, 0, 0.2, 1) infinite",
        "pulse-soft": "pulse-soft 1.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
}
