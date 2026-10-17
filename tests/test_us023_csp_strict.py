"""US-023 (ADR-0004, etapy 3–4): ścisła CSP dla skryptów.

- szablony nie mają atrybutów on*= ani skryptów inline bez nonce,
- akcje data-on-* wywołują wyłącznie funkcje z białej listy (CspActions.allow w tym samym szablonie,
  w base.html albo wbudowane w static/js/csp_actions.js),
- egzekwowana polityka: script-src bez 'unsafe-inline', z nonce zgodnym z tym w znacznikach <script>.
"""
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES = sorted((ROOT / "templates").glob("*.html"))
ACTIONS_JS = (ROOT / "static/js/csp_actions.js").read_text(encoding="utf-8")

HANDLER_RE = re.compile(
    r"(?<=[\s\"'])on(click|dblclick|change|input|submit|keydown|keyup|keypress|mousedown|mouseup|mousemove|"
    r"mouseover|mouseout|mouseenter|mouseleave|dragstart|dragend|dragover|dragleave|drop|blur|focus|load|"
    r"error|scroll|paste|contextmenu|wheel|toggle|reset|select|resize)\s*=\s*\\?[\"']",
    re.I,
)
SCRIPT_TAG_RE = re.compile(r"<script\b([^>]*)>", re.I)
ACTION_RE = re.compile(r"data-on-[a-z]+\s*=\s*(\\?[\"'])(.*?)\1", re.S)
ALLOW_RE = re.compile(r"CspActions\.allow\(([^)]*)\)")
BUILTINS = set(re.findall(r"builtins\.(\w+)\s*=", ACTIONS_JS))


def _names_used(body: str) -> set:
    """Funkcje wywoływane przez akcję: nazwa( na początku instrukcji oraz nazwy podane jako napis
    do onKeys/onSelf (te też przechodzą przez białą listę)."""
    body = body.replace("\\'", "'").replace('\\"', '"')
    names = set(re.findall(r"(?:^|;)\s*([A-Za-z_$][\w$]*)\s*\(", body))
    names.discard("event")
    for m in re.finditer(r"\b(?:onKeys\(\[[^\]]*\]\s*,|onSelf\()\s*['\"](\w+)['\"]", body):
        names.add(m.group(1))
    return names


def _allowed_in(text: str) -> set:
    out = set()
    for m in ALLOW_RE.finditer(text):
        out |= set(re.findall(r"['\"](\w+)['\"]", m.group(1)))
    return out


BASE_ALLOWED = _allowed_in((ROOT / "templates/base.html").read_text(encoding="utf-8"))


@pytest.mark.parametrize("tpl", TEMPLATES, ids=lambda p: p.name)
def test_no_inline_event_handlers(tpl):
    text = tpl.read_text(encoding="utf-8")
    found = [text.count("\n", 0, m.start()) + 1 for m in HANDLER_RE.finditer(text)]
    assert found == [], f"atrybuty on*= w liniach {found} — użyj data-on-* (static/js/csp_actions.js)"


@pytest.mark.parametrize("tpl", TEMPLATES, ids=lambda p: p.name)
def test_inline_scripts_carry_nonce(tpl):
    text = tpl.read_text(encoding="utf-8")
    missing = [
        text.count("\n", 0, m.start()) + 1
        for m in SCRIPT_TAG_RE.finditer(text)
        if "src=" not in m.group(1) and "csp_nonce()" not in m.group(1)
    ]
    assert missing == [], f"<script> bez nonce w liniach {missing}"


@pytest.mark.parametrize("tpl", TEMPLATES, ids=lambda p: p.name)
def test_actions_call_only_allowlisted_functions(tpl):
    text = tpl.read_text(encoding="utf-8")
    used = set()
    for m in ACTION_RE.finditer(text):
        used |= _names_used(m.group(2))
    allowed = _allowed_in(text) | BASE_ALLOWED | BUILTINS
    assert used - allowed == set(), f"brak w CspActions.allow: {sorted(used - allowed)}"


@pytest.mark.parametrize("tpl", TEMPLATES, ids=lambda p: p.name)
def test_allowlisted_functions_exist(tpl):
    """Literówka w białej liście = martwy przycisk; nazwa musi być zdefiniowana w szablonie."""
    text = tpl.read_text(encoding="utf-8")
    for name in _allowed_in(text):
        assert re.search(
            rf"(function\s+{name}\s*\(|\b(?:window\.)?{name}\s*=\s*(?:async\s*)?(?:function|\())", text
        ), f"{tpl.name}: {name} nie jest zdefiniowana"


def test_pages_with_actions_load_the_dispatcher():
    for tpl in TEMPLATES:
        text = tpl.read_text(encoding="utf-8")
        if "data-on-" in text and "{% extends" not in text:
            assert "csp_actions" in text, f"{tpl.name}: brak static/js/csp_actions.js"
    assert "js/csp_actions.js" in (ROOT / "templates/base.html").read_text(encoding="utf-8")


def test_dispatcher_has_no_eval():
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", ACTIONS_JS, flags=re.S)
    assert not re.search(r"\beval\s*\(|new\s+Function\s*\(|setTimeout\s*\(\s*['\"]", code)
    assert "window[name]" in code and "allowed[name]" in code   # wywołanie tylko z białej listy


def test_enforced_policy_is_strict_and_matches_nonce(admin_client):
    resp = admin_client.get("/history")
    assert resp.status_code == 200
    csp = resp.headers["Content-Security-Policy"]
    script_src = re.search(r"script-src ([^;]+);", csp).group(1).split()
    assert "'unsafe-inline'" not in script_src
    nonce = [s for s in script_src if s.startswith("'nonce-")]
    assert len(nonce) == 1
    value = nonce[0][len("'nonce-"):-1]
    inline = [t for t in SCRIPT_TAG_RE.findall(resp.get_data(as_text=True)) if "src=" not in t]
    assert inline and all(f'nonce="{value}"' in t for t in inline)
    # nowy nonce przy każdej odpowiedzi; Report-Only (cel US-024) bez 'unsafe-eval'
    assert admin_client.get("/history").headers["Content-Security-Policy"] != csp
    assert "'unsafe-eval'" not in resp.headers["Content-Security-Policy-Report-Only"]


def test_report_html_renders_without_request_context():
    pytest.importorskip("jinja2")
    from artwork_report_engine import build_demo_report, render_report_html

    html = render_report_html(build_demo_report())
    assert "data-on-click" in html and not re.search(r"<[a-z][^<>]*\son[a-z]+=", html)


# ── Składnia akcji (lustro parsera z csp_actions.js) ──────────────────────────
class _P:
    def __init__(self, s):
        self.s, self.i = s, 0

    def ws(self):
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1

    def eat(self, tok):
        self.ws()
        assert self.s.startswith(tok, self.i), f"oczekiwano {tok!r} w {self.s!r} (poz. {self.i})"
        self.i += len(tok)

    def peek(self, tok):
        self.ws()
        return self.s.startswith(tok, self.i)

    def ident(self):
        self.ws()
        m = re.compile(r"[A-Za-z_$][\w$]*").match(self.s, self.i)
        assert m, f"oczekiwano nazwy w {self.s!r} (poz. {self.i})"
        self.i = m.end()
        return m.group(0)

    def string(self):
        q = self.s[self.i]
        self.i += 1
        while self.i < len(self.s) and self.s[self.i] != q:
            self.i += 2 if self.s[self.i] == "\\" else 1
        assert self.i < len(self.s), f"niezamknięty napis w {self.s!r}"
        self.i += 1

    def seq(self, close):
        if not self.peek(close):
            self.value()
            while self.peek(","):
                self.eat(",")
                self.value()
        self.eat(close)

    def value(self):
        self.ws()
        c = self.s[self.i:self.i + 1]
        if c in ("'", '"'):
            return self.string()
        if c == "[":
            self.i += 1
            return self.seq("]")
        if c == "{":
            self.i += 1
            if not self.peek("}"):
                while True:
                    self.ws()
                    self.string() if self.s[self.i] in "'\"" else self.ident()
                    self.eat(":")
                    self.value()
                    if not self.peek(","):
                        break
                    self.eat(",")
            return self.eat("}")
        m = re.compile(r"[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?").match(self.s, self.i)
        if m:
            self.i = m.end()
            return
        name = self.ident()
        if name in ("true", "false", "null", "undefined"):
            return
        assert name in ("this", "event"), f"niedozwolona wartość {name!r} w {self.s!r}"
        path = []
        while self.s[self.i:self.i + 1] == ".":
            self.i += 1
            path.append(self.ident())
        ok = r"(|value|checked|src|files|parentElement|dataset\.[\w$]+)" if name == "this" else r"(|target|key)"
        assert re.fullmatch(ok, ".".join(path)), f"niedozwolone {name}.{'.'.join(path)} w {self.s!r}"

    def program(self):
        while True:
            self.ws()
            if self.i >= len(self.s):
                return
            if self.peek("return"):
                self.eat("return")
                self.eat("false")
            else:
                name = self.ident()
                if name == "event":
                    self.eat(".")
                    assert self.ident() in ("stopPropagation", "preventDefault")
                    self.eat("(")
                    self.eat(")")
                else:
                    self.eat("(")
                    self.seq(")")
            self.ws()
            if self.i < len(self.s):
                self.eat(";")


def _concrete(body: str) -> str:
    """Wstawki szablonu/JS zastępujemy przykładowymi wartościami (liczba lub napis)."""
    body = re.sub(r"\{\{.*?\}\}", "0", body)
    body = re.sub(r"\$\{(?:[^{}]|\{[^{}]*\})*\}", "0", body)
    body = re.sub(r"'\s*\+[^']*\+\s*'", "0", body)          # '+expr+' w napisach JS
    body = re.sub(r'"\s*\+[^"]*\+\s*"', "0", body)
    return body.replace("\\'", "'").replace('\\"', '"')


@pytest.mark.parametrize("tpl", TEMPLATES, ids=lambda p: p.name)
def test_action_bodies_match_dispatcher_grammar(tpl):
    text = tpl.read_text(encoding="utf-8")
    for m in ACTION_RE.finditer(text):
        _P(_concrete(m.group(2))).program()


@pytest.mark.parametrize("tpl", TEMPLATES, ids=lambda p: p.name)
def test_tojson_in_double_quoted_action_is_escaped(tpl):
    """|tojson nie escapuje '"' (zwraca Markup, więc |e nic nie robi) — w atrybucie "…" ucina
    wyrażenie i przycisk nie działa. Wymagane |tojson|forceescape."""
    text = tpl.read_text(encoding="utf-8")
    bad = [
        m.group(0)[:80]
        for m in re.finditer(r'data-on-[a-z]+="[^"]*"', text)
        if re.search(r"\|\s*tojson(?!\s*\|\s*forceescape)", m.group(0))
    ]
    assert bad == []
