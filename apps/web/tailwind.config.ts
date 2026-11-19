import type { Config } from 'tailwindcss';
const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#0b0e13', panel: '#12161f', line: '#232a38',
        up: '#26a69a', down: '#ef5350', accent: '#f5b041',
      },
    },
  },
  plugins: [],
};
export default config;
