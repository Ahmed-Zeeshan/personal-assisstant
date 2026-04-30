const websiteConfig = require('../website/tailwind.config.cjs');

/** @type {import('tailwindcss').Config} */
module.exports = {
  ...websiteConfig,
  content: ['./index.html', './src/**/*.{ts,tsx,js,jsx,html}'],
};
