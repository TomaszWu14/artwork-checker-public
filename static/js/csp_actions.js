/*
 * US-023 (ADR-0004, etap 3): zamiennik atrybutów on*= zgodny ze ścisłą CSP.
 *
 * Zamiast  onclick="saveField(5,'label',this.value)"  szablony piszą
 *          data-on-click="saveField(5,'label',this.value)".
 * Działa też dla elementów dodanych później przez innerHTML (nasłuch podpinany przy pierwszym zdarzeniu).
 *
 * Bez eval: wyrażenie jest parsowane ścisłą gramatyką — sekwencja wywołań  nazwa(arg, …)
 * rozdzielonych ';' oraz event.stopPropagation() / event.preventDefault() / return false.
 * Argumenty: literały JS (liczby, napisy, true/false/null/undefined, obiekty, tablice),
 * this, event, this.value|checked|src|files|parentElement|dataset.X, event.target|key.
 * Wywołać można wyłącznie funkcje z białej listy (CspActions.allow) — wstrzyknięty atrybut
 * nie uruchomi np. setTimeout('…') ani dowolnej funkcji globalnej.
 */
(function () {
  'use strict';
  var allowed = Object.create(null);
  var builtins = Object.create(null);

  function allow() {
    for (var i = 0; i < arguments.length; i++) allowed[arguments[i]] = true;
  }

  // ── Parser ────────────────────────────────────────────────────────────────
  var cache = Object.create(null);

  function parse(src) {
    if (cache[src]) return cache[src];
    var i = 0, n = src.length;
    function err(msg) { throw new Error('CspActions: ' + msg + ' w "' + src + '" (poz. ' + i + ')'); }
    function ws() { while (i < n && /\s/.test(src[i])) i++; }
    function peek(s) { ws(); return src.substr(i, s.length) === s; }
    function eat(s) { if (!peek(s)) err('oczekiwano ' + s); i += s.length; }
    function ident() {
      ws();
      var m = /^[A-Za-z_$][\w$]*/.exec(src.slice(i));
      if (!m) err('oczekiwano nazwy');
      i += m[0].length;
      return m[0];
    }
    function str() {
      var q = src[i++], out = '';
      while (i < n && src[i] !== q) {
        var c = src[i++];
        if (c === '\\') {
          var e = src[i++];
          if (e === 'n') out += '\n';
          else if (e === 't') out += '\t';
          else if (e === 'r') out += '\r';
          else if (e === 'u') { out += String.fromCharCode(parseInt(src.substr(i, 4), 16)); i += 4; }
          else if (e === 'x') { out += String.fromCharCode(parseInt(src.substr(i, 2), 16)); i += 2; }
          else out += e;
        } else out += c;
      }
      if (src[i] !== q) err('niezamknięty napis');
      i++;
      return { k: 'lit', v: out };
    }
    function value() {
      ws();
      var c = src[i];
      if (c === '"' || c === "'") return str();
      if (c === '{') {
        i++;
        var props = [];
        if (!peek('}')) {
          do {
            ws();
            var key = (src[i] === '"' || src[i] === "'") ? str().v : ident();
            eat(':');
            props.push([key, value()]);
          } while (peek(',') && (eat(','), true));
        }
        eat('}');
        return { k: 'obj', v: props };
      }
      if (c === '[') {
        i++;
        var items = [];
        if (!peek(']')) {
          do { items.push(value()); } while (peek(',') && (eat(','), true));
        }
        eat(']');
        return { k: 'arr', v: items };
      }
      var num = /^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?/.exec(src.slice(i));
      if (num) { i += num[0].length; return { k: 'lit', v: parseFloat(num[0]) }; }
      var id = ident();
      if (id === 'true') return { k: 'lit', v: true };
      if (id === 'false') return { k: 'lit', v: false };
      if (id === 'null') return { k: 'lit', v: null };
      if (id === 'undefined') return { k: 'lit', v: undefined };
      if (id === 'this' || id === 'event') {
        var path = [];
        while (src[i] === '.') { i++; path.push(ident()); }
        var allowedPaths = id === 'this'
          ? /^(|value|checked|src|files|parentElement|dataset\.[\w$]+)$/
          : /^(|target|key)$/;
        if (!allowedPaths.test(path.join('.'))) err('niedozwolone ' + id + '.' + path.join('.'));
        return { k: id, v: path };
      }
      err('niedozwolona wartość ' + id);
    }
    var stmts = [];
    while (true) {
      ws();
      if (i >= n) break;
      if (peek('return')) { eat('return'); eat('false'); stmts.push({ k: 'retfalse' }); }
      else {
        var name = ident();
        if (name === 'event') {
          eat('.');
          var m = ident();
          if (m !== 'stopPropagation' && m !== 'preventDefault') err('niedozwolone event.' + m);
          eat('('); eat(')');
          stmts.push({ k: 'ev', v: m });
        } else {
          eat('(');
          var args = [];
          if (!peek(')')) {
            do { args.push(value()); } while (peek(',') && (eat(','), true));
          }
          eat(')');
          stmts.push({ k: 'call', name: name, args: args });
        }
      }
      ws();
      if (i < n) eat(';');
    }
    cache[src] = stmts;
    return stmts;
  }

  // ── Wykonanie ─────────────────────────────────────────────────────────────
  function resolve(node, el, ev) {
    switch (node.k) {
      case 'lit': return node.v;
      case 'arr': return node.v.map(function (x) { return resolve(x, el, ev); });
      case 'obj':
        var o = {};
        node.v.forEach(function (p) { o[p[0]] = resolve(p[1], el, ev); });
        return o;
      default:
        var cur = node.k === 'this' ? el : ev;
        node.v.forEach(function (p) {
          if (cur == null) return;
          if (p.indexOf('dataset.') === 0) cur = cur.dataset[p.slice(8)];
          else cur = cur[p];
        });
        return cur;
    }
  }

  function lookup(name) {
    if (builtins[name]) return builtins[name];
    if (allowed[name] && typeof window[name] === 'function') return window[name];
    return null;
  }

  function run(el, ev, src) {
    var stmts;
    try { stmts = parse(src); } catch (e) { console.error(e.message); return; }
    for (var s = 0; s < stmts.length; s++) {
      var st = stmts[s];
      if (st.k === 'ev') ev[st.v]();
      else if (st.k === 'retfalse') ev.preventDefault();
      else {
        var fn = lookup(st.name);
        if (!fn) { console.error('CspActions: funkcja spoza białej listy: ' + st.name); return; }
        var args = st.args.map(function (a) { return resolve(a, el, ev); });
        if (fn.apply(el, args) === false) ev.preventDefault();
      }
    }
  }

  // Nasłuch jest podpinany NA SAM ELEMENT (jak atrybut on*=), a nie obsługiwany zbiorczo na document —
  // dzięki temu kolejność względem innych nasłuchów i event.stopPropagation() działają tak jak dawniej
  // (np. startMove() w polu edytora zatrzymuje mousedown, zanim dotrze do kontenera rysowania).
  // Podpięcie leniwe: nasłuch w fazie capture na document widzi każde zdarzenie, zanim dotrze ono do
  // elementów, i podpina brakujące nasłuchy na ścieżce — działa też dla elementów dodanych przez innerHTML
  // i dla zdarzeń bez bąbelkowania (blur, load, error, scroll, mouseenter/leave).
  var TYPES = ['click', 'dblclick', 'change', 'input', 'submit', 'keydown', 'keyup', 'mousedown', 'mouseup',
    'mousemove', 'mouseover', 'mouseout', 'dragstart', 'dragend', 'dragover', 'dragleave', 'drop',
    'blur', 'focus', 'load', 'error', 'scroll', 'mouseenter', 'mouseleave'];
  var bound = new WeakMap();

  function listener(ev) {
    var src = ev.currentTarget.getAttribute('data-on-' + ev.type);
    if (src != null) run(ev.currentTarget, ev, src);
  }

  function bindPath(ev) {
    var attr = 'data-on-' + ev.type;
    for (var el = ev.target; el && el.nodeType === 1; el = el.parentElement) {
      if (!el.hasAttribute(attr)) continue;
      var types = bound.get(el);
      if (!types) { types = Object.create(null); bound.set(el, types); }
      if (!types[ev.type]) { types[ev.type] = true; el.addEventListener(ev.type, listener); }
    }
  }
  TYPES.forEach(function (t) { document.addEventListener(t, bindPath, true); });

  // ── Wbudowane akcje (zamienniki typowych handlerów inline) ───────────────
  function byId(id) { return document.getElementById(id); }
  builtins.clickById = function (id) { var e = byId(id); if (e) e.click(); };
  builtins.focusById = function (id) { var e = byId(id); if (e) e.focus(); };
  builtins.hideById = function (id) { var e = byId(id); if (e) e.style.display = 'none'; };
  builtins.removeClassById = function (id, cls) { var e = byId(id); if (e) e.classList.remove(cls); };
  builtins.hideSelf = function () { this.style.display = 'none'; };
  builtins.blurSelf = function () { this.blur(); };
  builtins.upperCaseValue = function () { this.value = this.value.toUpperCase(); };
  builtins.setBackground = function (color) { this.style.background = color; };
  // Pokaż/ukryj hasło (login, reset hasła); this = przycisk.
  builtins.togglePassword = function (id) {
    var i = byId(id); if (!i) return;
    var show = i.type === 'password';
    i.type = show ? 'text' : 'password';
    this.textContent = show ? '🙈' : '👁';
  };
  builtins.goBack = function () { history.back(); };
  builtins.printPage = function () { window.print(); return false; };
  // Tylko adresy względne tej samej aplikacji — bez javascript:, bez innych domen.
  builtins.openWindow = function (url, name) {
    if (typeof url === 'string' && url.charAt(0) === '/' && url.charAt(1) !== '/') window.open(url, name || '_blank');
    return false;
  };
  // Klawisz Enter/Spacja → akcja (dostępność elementów role="button").
  builtins.onKeys = function (keys, name) {
    var ev = arguments[arguments.length - 1];
    if (!(ev instanceof Event) || keys.indexOf(ev.key) < 0) return;
    ev.preventDefault();
    var fn = lookup(name);
    if (fn) fn.apply(this, Array.prototype.slice.call(arguments, 2, arguments.length - 1));
  };
  // Kliknięcie w tło (nie w zawartość) okna modalnego.
  builtins.onSelf = function (name, ev) {
    if (ev && ev.target === this) { var fn = lookup(name); if (fn) fn.call(this); }
  };

  // Diagnostyka (testy e2e): nazwy z wyrażenia, których nie da się wywołać.
  function unresolved(src) {
    var missing = [];
    parse(src).forEach(function (st) {
      if (st.k !== 'call') return;
      if (!lookup(st.name)) missing.push(st.name);
      if ((st.name === 'onKeys' || st.name === 'onSelf') && st.args.length > 1) {
        var ref = st.name === 'onKeys' ? st.args[1] : st.args[0];
        if (ref.k === 'lit' && !lookup(ref.v)) missing.push(ref.v);
      }
    });
    return missing;
  }

  window.CspActions = { allow: allow, parse: parse, unresolved: unresolved };
})();
