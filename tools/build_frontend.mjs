// tools/build_frontend.mjs — build frontendu bez CDN (US-022, ADR-0004 etap 2).
//
//   npm ci && npm run build
//
// 1. Kopiuje przypięte wersje bibliotek (package.json) do static/vendor/ —
//    przeglądarka nie pobiera już kodu z unpkg.com / cdn.tailwindcss.com.
// 2. Kompiluje JSX raportu (frontend/src/artwork_report_pf.jsx) do zwykłego JS —
//    bez Babel w przeglądarce (który wymagał 'unsafe-eval').
// 3. Buduje CSS Tailwinda z klas użytych w repo (static/css/tailwind.css).
//
// Wyniki są w repo; CI uruchamia ten skrypt i sprawdza `git diff --exit-code`,
// więc źródło i zbudowane pliki nie mogą się rozjechać.
import { build, transform } from "esbuild";
import { execFileSync } from "node:child_process";
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const nm = (p) => join(root, "node_modules", p);
const out = (p) => join(root, "static", p);

const vendor = [
  ["react/umd/react.production.min.js", "vendor/react/react.production.min.js"],
  ["react/LICENSE", "vendor/react/LICENSE"],
  ["react-dom/umd/react-dom.production.min.js", "vendor/react/react-dom.production.min.js"],
  ["react-dom/LICENSE", "vendor/react/LICENSE.react-dom"],
  // US-024: build CSP Alpine — wyrażenia bez eval (wymaga Alpine.data dla komponentów).
  ["@alpinejs/csp/dist/cdn.min.js", "vendor/alpinejs/alpine-csp.min.js"],
  ["@alpinejs/collapse/dist/cdn.min.js", "vendor/alpinejs/collapse.min.js"],
  ["lucide/dist/umd/lucide.min.js", "vendor/lucide/lucide.min.js"],
  ["lucide/LICENSE", "vendor/lucide/LICENSE"],
];
for (const [src, dst] of vendor) {
  mkdirSync(dirname(out(dst)), { recursive: true });
  copyFileSync(nm(src), out(dst));
}
// Pakiety Alpine nie zawierają pliku LICENSE — zapisujemy informację o licencji z package.json.
const alpineNotice = ["@alpinejs/csp", "@alpinejs/collapse"].map((name) => {
  const pkg = JSON.parse(readFileSync(nm(`${name}/package.json`), "utf8"));
  return `${pkg.name}@${pkg.version} — licencja ${pkg.license} (https://github.com/alpinejs/alpine/blob/main/LICENSE.md)`;
}).join("\n");
writeFileSync(out("vendor/alpinejs/LICENSE.txt"), alpineNotice + "\n");

await build({
  entryPoints: [join(root, "frontend/src/artwork_report_pf.jsx")],
  outfile: out("js/artwork_report_pf.js"),
  bundle: false,
  format: "iife",
  target: ["es2018"],
  jsx: "transform",          // React.createElement — jak Babel standalone (classic runtime)
  loader: { ".jsx": "jsx" },
  minify: false,
  legalComments: "none",
  banner: { js: "// Zbudowane z frontend/src/artwork_report_pf.jsx przez `npm run build` — nie edytuj ręcznie." },
  logLevel: "warning",
});

// US-027: podgląd projektów raportu (/artwork/design-preview) — wcześniej React i Babel z unpkg
// kompilowały JSX w przeglądarce (blokowane przez ścisłą CSP). Każdy plik kompilujemy do osobnego
// IIFE (jak osobne <script> — wymiana tylko przez Object.assign(window, …)) i sklejamy w kolejności
// ładowania. app-print.jsx nie jest ładowany przez index.html — pomijamy.
const designOrder = ["design-canvas", "shared", "artwork-svg", "variant-a", "variant-b", "variant-c",
  "variant-d", "variant-e", "app"];
const designParts = [];
for (const name of designOrder) {
  const src = readFileSync(join(root, "frontend/src/design_preview", `${name}.jsx`), "utf8");
  const { code } = await transform(src, {
    loader: "jsx", jsx: "transform", format: "iife", target: ["es2020"], legalComments: "none",
  });
  designParts.push(`// ── ${name}.jsx ──\n${code}`);
}
writeFileSync(out("design/design_preview.js"),
  "// Zbudowane z frontend/src/design_preview/*.jsx przez `npm run build` — nie edytuj ręcznie.\n"
  + designParts.join("\n"));

execFileSync(
  process.execPath,
  [nm("tailwindcss/lib/cli.js"), "-c", join(root, "tailwind.config.js"),
   "-i", join(root, "frontend/tailwind.css"), "-o", out("css/tailwind.css"), "--minify"],
  { stdio: ["ignore", "inherit", "inherit"], cwd: root },
);
console.log("frontend build OK");
