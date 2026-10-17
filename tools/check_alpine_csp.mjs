// US-024 (ADR-0004, etap 2b): sprawdzenie wyrażeń Alpine pod build CSP (@alpinejs/csp, bez eval).
//
//  • każde wyrażenie dyrektywy (x-text, x-show, :attr, @event, x-model, x-for…) musi się sparsować
//    parserem z builda CSP — ten sam kod, który wykona je w przeglądarce,
//  • wyrażenia nie mogą sięgać do globali (Math, window, encodeURIComponent…) — build CSP ich nie widzi;
//    potrzebne funkcje dodaj jako metody komponentu,
//  • każdy komponent z x-data="nazwa()" musi być zarejestrowany: Alpine.data('nazwa', nazwa).
//
// Uruchomienie: node tools/check_alpine_csp.mjs   (po npm ci; job CI „frontend”)
import { readFileSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const { Tokenizer, Parser } = await import(join(root, "node_modules/@alpinejs/csp/src/parser.js"));

const DIRECTIVE = /\s(x-(?:text|html|show|if|model(?:\.[\w-]+)*|for|init|effect|bind:[\w.-]+|on:[\w.:-]+|data)|@[\w.:-]+|:[\w-]+)\s*=\s*(["'])([\s\S]*?)\2/g;
const MAGICS = new Set(["$event", "$refs", "$el", "$nextTick", "$watch", "$dispatch", "$store", "$data",
  "$root", "$id", "true", "false", "null", "undefined"]);
const shellJs = readFileSync(join(root, "static/js/shell.js"), "utf8");

// Nazwy dostępne w wyrażeniu = pola i metody komponentów (strony i dcShell z base.html), zmienne x-for
// i magie Alpine. Wszystko inne (Math, window, funkcje globalne strony) build CSP odrzuci w przeglądarce.
function componentKeys(name, sources) {
  for (const src of sources) {
    const m = new RegExp(`function\\s+${name}\\s*\\([^)]*\\)\\s*\\{`).exec(src);
    if (!m) continue;
    const body = src.slice(m.index + m[0].length).split(/\n(?:async\s+)?function\s/)[0];
    const keys = new Set();
    for (const k of body.matchAll(/(?:^|[{,\s])(?:async\s+)?(?:get\s+)?([A-Za-z_$][\w$]*)\s*(?::(?!:)|\([^)]*\)\s*\{)/g)) keys.add(k[1]);
    return keys;
  }
  return null;
}
const shellKeys = componentKeys("dcShell", [shellJs]);

function rootIdentifiers(node, out) {
  if (!node || typeof node !== "object") return;
  if (node.type === "Identifier") { out.add(node.name); return; }
  if (node.type === "MemberExpression") {
    rootIdentifiers(node.object, out);
    if (node.computed) rootIdentifiers(node.property, out);
    return;
  }
  for (const [k, v] of Object.entries(node)) {
    if (k === "type" || k === "key") continue;
    Array.isArray(v) ? v.forEach((x) => rootIdentifiers(x, out)) : rootIdentifiers(v, out);
  }
}

const errors = [];
let count = 0;
const tdir = join(root, "templates");
for (const f of readdirSync(tdir).filter((n) => n.endsWith(".html")).sort()) {
  const text = readFileSync(join(tdir, f), "utf8");
  if (!/\sx-data=/.test(text)) continue;
  const scope = new Set([...MAGICS, ...shellKeys]);
  for (const d of text.matchAll(/\sx-data="(\w+)\(\)"/g)) for (const k of componentKeys(d[1], [text]) || []) scope.add(k);
  for (const v of text.matchAll(/x-for="\s*\(?([^)]*?)\)?\s+(?:in|of)\s/g)) v[1].split(",").forEach((s) => scope.add(s.trim()));
  for (const m of text.matchAll(DIRECTIVE)) {
    let [, name, , expr] = m;
    const line = text.slice(0, m.index).split("\n").length;
    expr = expr.replace(/\{\{[\s\S]*?\}\}/g, "0").replace(/\{%[\s\S]*?%\}/g, "").trim();
    if (!expr) continue;
    if (name === "x-data") {
      const comp = /^(\w+)\s*\(\s*\)$/.exec(expr);
      if (!comp) { errors.push(`${f}:${line} x-data="${expr}" — oczekiwano wywołania zarejestrowanego komponentu`); continue; }
      const reg = new RegExp(`Alpine\\.data\\(\\s*['"]${comp[1]}['"]`);
      if (!reg.test(text) && !reg.test(shellJs)) errors.push(`${f}:${line} komponent ${comp[1]} bez Alpine.data('${comp[1]}', …)`);
      continue;
    }
    if (name === "x-for") {
      const mm = /^\s*(?:\(([^)]*)\)|(\w+))\s+(?:in|of)\s+([\s\S]+)$/.exec(expr);
      if (!mm) { errors.push(`${f}:${line} x-for="${expr}" — niepoprawna składnia`); continue; }
      expr = mm[3];
    }
    count++;
    let ast;
    try {
      ast = new Parser(new Tokenizer(expr).tokenize()).parse();
    } catch (e) {
      errors.push(`${f}:${line} ${name}="${expr}" — ${e.message}`);
      continue;
    }
    const ids = new Set();
    rootIdentifiers(ast, ids);
    for (const id of ids) if (!scope.has(id)) errors.push(`${f}:${line} ${name}="${expr}" — „${id}” nie jest polem komponentu (globalne nazwy są niedostępne w buildzie CSP)`);
  }
}

if (errors.length) {
  console.error(errors.join("\n"));
  console.error(`\n${errors.length} problem(ów) w ${count} wyrażeniach Alpine (build CSP).`);
  process.exit(1);
}
console.log(`Alpine CSP: ${count} wyrażeń OK`);
