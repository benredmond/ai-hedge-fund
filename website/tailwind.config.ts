import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['var(--font-commit-mono)', 'monospace'],
        sans: ['var(--font-satoshi)', 'sans-serif'],
        serif: ['var(--font-sentient)', 'serif'],
      },
      colors: {
        background: '#fafaf9',
        foreground: '#1a1a1a',
        muted: '#6b6b6b',
        border: '#e5e5e5',
        vermillion: '#ff3a2d',
        negative: '#9b2c2c',
        benchmark: '#a3a3a3',
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
};

export default config;
