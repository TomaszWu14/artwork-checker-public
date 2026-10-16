// US-022: Tailwind budowany z repo zamiast Play CDN (cdn.tailwindcss.com) — bez skryptu z
// zewnątrz generującego style w przeglądarce. Skanujemy wszystkie miejsca, w których
// mogą wystąpić nazwy klas (szablony, skrypty, HTML generowany w Pythonie).
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js",
    "!./static/js/vendor/**",
    "./frontend/src/**/*.{js,jsx}",
    "./*.py",
    "./blueprints/**/*.py",
  ],
  theme: { extend: {} },
  plugins: [],
};
