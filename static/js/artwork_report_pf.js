// Zbudowane z frontend/src/artwork_report_pf.jsx przez `npm run build` — nie edytuj ręcznie.
(() => {
  function diffWords(a, b) {
    const A = (a || "").split(/(\s+)/), B = (b || "").split(/(\s+)/);
    const aw = A.filter((t) => t.trim()), bw = B.filter((t) => t.trim());
    const n = aw.length, m = bw.length;
    const dp = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
    for (let i2 = n - 1; i2 >= 0; i2--) for (let j2 = m - 1; j2 >= 0; j2--)
      dp[i2][j2] = aw[i2].toLowerCase() === bw[j2].toLowerCase() ? dp[i2 + 1][j2 + 1] + 1 : Math.max(dp[i2 + 1][j2], dp[i2][j2 + 1]);
    const aFlag = new Array(n).fill(true), bFlag = new Array(m).fill(true);
    let i = 0, j = 0;
    while (i < n && j < m) {
      if (aw[i].toLowerCase() === bw[j].toLowerCase()) {
        aFlag[i] = false;
        bFlag[j] = false;
        i++;
        j++;
      } else if (dp[i + 1][j] >= dp[i][j + 1]) i++;
      else j++;
    }
    return { aw, bw, aFlag, bFlag };
  }
  function OcrLine({ words, flags, side }) {
    return /* @__PURE__ */ React.createElement("div", { className: "pf-ocr " + (side === "A" ? "a" : "b") }, /* @__PURE__ */ React.createElement("span", { className: "lab" }, "OCR \u2014 ", side === "A" ? "Master A" : "Dostawca B"), words.map((w, i) => /* @__PURE__ */ React.createElement(React.Fragment, { key: i }, flags[i] ? /* @__PURE__ */ React.createElement("span", { className: "d" }, w) : w, " ")));
  }
  const MIN_CROP_HEIGHT = 90;
  function ImagePane({ side, field, onOpen }) {
    const MAP = {
      a: { tag: "\u2460", title: "MASTER (WZORZEC A)", cls: "a" },
      b: { tag: "\u2461", title: "DOSTAWCA (PLIK B)", cls: "b" },
      c: { tag: "\u2462", title: "DOSTAWCA W SKALI \xB7 SIFT", cls: "c" },
      d: { tag: "\u2463", title: "MAPA R\xD3\u017BNIC \xB7 SSIM", cls: "d" }
    }[side];
    const imgKey = { a: "imgA", b: "imgB", c: "imgC", d: "imgD" }[side];
    const src = field.cutout[imgKey];
    const wrapRef = React.useRef(null);
    function scaleThinCrop(img) {
      if (!img || !wrapRef.current) return;
      const ar = img.naturalHeight / img.naturalWidth;
      if (!ar || ar === 0) return;
      const displayW = img.offsetWidth;
      const displayH = displayW * ar;
      if (displayH > 0 && displayH < MIN_CROP_HEIGHT) {
        const scale = Math.min(MIN_CROP_HEIGHT / displayH, 6);
        img.style.transformOrigin = "top left";
        img.style.transform = `scale(${scale})`;
        img.style.width = `${100 / scale}%`;
        wrapRef.current.style.height = `${Math.round(displayH * scale) + 2}px`;
        wrapRef.current.style.overflow = "hidden";
      }
    }
    return /* @__PURE__ */ React.createElement("div", { className: "pf-pane " + MAP.cls }, /* @__PURE__ */ React.createElement("div", { className: "pf-pane-tab" }, /* @__PURE__ */ React.createElement("span", { className: "ti" }, MAP.tag), MAP.title), /* @__PURE__ */ React.createElement("div", { className: "pf-pane-img", ref: wrapRef, onClick: () => onOpen && src && onOpen() }, /* @__PURE__ */ React.createElement("div", { className: "pf-expand-hint" }, "\u2922 Powi\u0119ksz"), src ? /* @__PURE__ */ React.createElement(
      "img",
      {
        src: "data:image/jpeg;base64," + src,
        alt: "Kadr \u2014 " + MAP.title,
        onLoad: (e) => scaleThinCrop(e.target)
      }
    ) : /* @__PURE__ */ React.createElement("div", { style: { padding: 24, textAlign: "center", color: "#9ca3af", fontSize: 13 } }, "Brak obrazu")));
  }
  function FieldCard({ field, idx, openLb }) {
    const stacked = field.layout === "stacked";
    const { aw, bw, aFlag, bFlag } = diffWords(field.ocrA, field.ocrB);
    const hasD = !!field.cutout.imgD;
    const sides = stacked ? ["a", "b"] : ["a", "b", ...hasD ? ["d"] : []];
    const cols = stacked ? 1 : sides.length;
    const prioLabel = { KR: "KR \xB7 krytyczne", W: "W \xB7 wa\u017Cne", I: "I \xB7 informacyjne" }[field.priority];
    return /* @__PURE__ */ React.createElement("div", { className: "pf-card r-" + field.result, id: "pf-" + field.id }, /* @__PURE__ */ React.createElement("div", { className: "pf-card-head" }, /* @__PURE__ */ React.createElement("span", { className: "idx" }, String(idx + 1).padStart(2, "0")), /* @__PURE__ */ React.createElement("span", { className: "name" }, field.name), /* @__PURE__ */ React.createElement("span", { className: "pf-badge prio-" + field.priority, title: prioLabel }, /* @__PURE__ */ React.createElement("span", { className: "pin" }), field.priority), /* @__PURE__ */ React.createElement("span", { className: "pf-badge res-" + field.result }, field.result === "diff" ? "R\xD3\u017BNICA" : "ZGODNE")), /* @__PURE__ */ React.createElement("div", { className: "pf-card-body" }, /* @__PURE__ */ React.createElement("div", { className: "pf-panes " + (stacked ? "stack" : "side"), style: { "--cols": cols } }, stacked ? /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement(ImagePane, { side: "a", field, onOpen: () => openLb(field, "a") }), /* @__PURE__ */ React.createElement(OcrLine, { words: aw, flags: aFlag, side: "A" })), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement(ImagePane, { side: "b", field, onOpen: () => openLb(field, "b") }), /* @__PURE__ */ React.createElement(OcrLine, { words: bw, flags: bFlag, side: "B" }))) : sides.map((s) => /* @__PURE__ */ React.createElement("div", { key: s }, /* @__PURE__ */ React.createElement(ImagePane, { side: s, field, onOpen: () => openLb(field, s) }), s === "a" && /* @__PURE__ */ React.createElement(OcrLine, { words: aw, flags: aFlag, side: "A" }), s === "b" && /* @__PURE__ */ React.createElement(OcrLine, { words: bw, flags: bFlag, side: "B" })))), field.note && /* @__PURE__ */ React.createElement("div", { className: "pf-card-note" }, /* @__PURE__ */ React.createElement("span", { className: "ic" }, "\u26A0"), /* @__PURE__ */ React.createElement("span", null, field.note))));
  }
  function Lightbox({ field, onClose }) {
    const [zoom, setZoom] = React.useState(1);
    const [off, setOff] = React.useState({ x: 0, y: 0 });
    const [rotA, setRotA] = React.useState(0);
    const [rotB, setRotB] = React.useState(0);
    const drag = React.useRef(null);
    const [grabbing, setGrabbing] = React.useState(false);
    const bump = (d) => setZoom((z) => Math.min(6, Math.max(0.2, +(z + d).toFixed(2))));
    const reset = React.useCallback(() => {
      setZoom(1);
      setOff({ x: 0, y: 0 });
      setRotA(0);
      setRotB(0);
    }, []);
    React.useEffect(() => {
      const h = (e) => {
        if (e.key === "Escape") onClose();
        else if (e.key === "+" || e.key === "=") bump(0.25);
        else if (e.key === "-") bump(-0.25);
        else if (e.key === "0") reset();
      };
      window.addEventListener("keydown", h);
      return () => window.removeEventListener("keydown", h);
    }, [onClose, reset]);
    const onWheel = (e) => {
      e.preventDefault();
      bump(e.deltaY < 0 ? 0.18 : -0.18);
    };
    const onDown = (e) => {
      drag.current = { x: e.clientX, y: e.clientY, ox: off.x, oy: off.y };
      setGrabbing(true);
    };
    const onMove = (e) => {
      if (!drag.current) return;
      setOff({ x: drag.current.ox + (e.clientX - drag.current.x), y: drag.current.oy + (e.clientY - drag.current.y) });
    };
    const onUp = () => {
      drag.current = null;
      setGrabbing(false);
    };
    const holderStyle = (rot) => ({
      position: "absolute",
      top: "50%",
      left: "50%",
      transform: `translate(calc(-50% + ${off.x}px),calc(-50% + ${off.y}px)) scale(${zoom}) rotate(${rot}deg)`,
      transformOrigin: "center"
    });
    const sides = [
      { key: "a", src: field.cutout.imgA, rot: rotA, setRot: setRotA, tag: "\u2460 MASTER A", cls: "a" },
      { key: "b", src: field.cutout.imgB, rot: rotB, setRot: setRotB, tag: "\u2461 DOSTAWCA B", cls: "b" }
    ];
    return /* @__PURE__ */ React.createElement("div", { className: "pf-lb", onMouseUp: onUp }, /* @__PURE__ */ React.createElement("div", { className: "pf-lb-toolbar" }, /* @__PURE__ */ React.createElement("div", { className: "pf-lb-title" }, field.name, /* @__PURE__ */ React.createElement("span", { className: "b" }, field.priority, " \xB7 ", field.result === "diff" ? "R\xD3\u017BNICA" : "ZGODNE")), /* @__PURE__ */ React.createElement("div", { className: "pf-lb-grp" }, /* @__PURE__ */ React.createElement("button", { className: "pf-lb-btn", onClick: () => bump(-0.25) }, "\u2212"), /* @__PURE__ */ React.createElement("span", { className: "pf-lb-zoom" }, Math.round(zoom * 100), "%"), /* @__PURE__ */ React.createElement("button", { className: "pf-lb-btn", onClick: () => bump(0.25) }, "\uFF0B"), /* @__PURE__ */ React.createElement("button", { className: "pf-lb-btn", onClick: reset }, "\u21A9 Reset")), /* @__PURE__ */ React.createElement("button", { className: "pf-lb-btn pf-lb-close", onClick: onClose }, "\u2715 Zamknij")), /* @__PURE__ */ React.createElement("div", { className: "pf-lb-stage" }, sides.map(({ key, src, rot, setRot, tag, cls }) => /* @__PURE__ */ React.createElement("div", { className: "pf-lb-panel", key }, /* @__PURE__ */ React.createElement("div", { className: "pf-lb-panel-head" }, /* @__PURE__ */ React.createElement("span", { className: "pf-lb-tag " + cls }, tag), /* @__PURE__ */ React.createElement("div", { className: "pf-lb-rot" }, /* @__PURE__ */ React.createElement("button", { onClick: () => setRot((r) => r - 90) }, "\u21BA"), /* @__PURE__ */ React.createElement("button", { onClick: () => setRot((r) => r + 90) }, "\u21BB"))), /* @__PURE__ */ React.createElement(
      "div",
      {
        className: "pf-lb-canvas" + (grabbing ? " grabbing" : ""),
        onMouseDown: onDown,
        onMouseMove: onMove,
        onMouseUp: onUp,
        onMouseLeave: onUp,
        onWheel
      },
      src && /* @__PURE__ */ React.createElement("img", { src: "data:image/jpeg;base64," + src, style: holderStyle(rot), alt: tag }),
      !src && /* @__PURE__ */ React.createElement("div", { style: { color: "#9fb0cc", fontSize: 14 } }, "Brak obrazu")
    ), key === "b" && /* @__PURE__ */ React.createElement("div", { className: "pf-lb-hint" }, "Scroll = zoom \xB7 przeci\u0105gnij = przesu\u0144 \xB7 rotacja osobno")))));
  }
  function PfApp() {
    const fields = window.REPORT_FIELDS || [];
    const [resFilter, setResFilter] = React.useState("all");
    const [prioFilter, setPrioFilter] = React.useState("all");
    const [lb, setLb] = React.useState(null);
    const diffCount = fields.filter((f) => f.result === "diff").length;
    const okCount = fields.length - diffCount;
    const pct = fields.length ? Math.round(okCount / fields.length * 100) : 100;
    const shown = fields.filter(
      (f) => (resFilter === "all" || f.result === resFilter) && (prioFilter === "all" || f.priority === prioFilter)
    );
    return /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("div", { className: "pf-summary" }, /* @__PURE__ */ React.createElement("div", { className: "pf-stat diff" }, /* @__PURE__ */ React.createElement("span", { className: "num" }, diffCount), /* @__PURE__ */ React.createElement("span", { className: "lbl" }, "r\xF3\u017Cnic do", /* @__PURE__ */ React.createElement("br", null), "weryfikacji")), /* @__PURE__ */ React.createElement("div", { className: "pf-stat ok" }, /* @__PURE__ */ React.createElement("span", { className: "num" }, okCount), /* @__PURE__ */ React.createElement("span", { className: "lbl" }, "p\xF3l", /* @__PURE__ */ React.createElement("br", null), "zgodnych")), /* @__PURE__ */ React.createElement("div", { className: "pf-compliance" }, /* @__PURE__ */ React.createElement("div", { className: "bar" }, /* @__PURE__ */ React.createElement("i", { style: { width: pct + "%" } })), /* @__PURE__ */ React.createElement("span", { className: "pct" }, pct, "%")), /* @__PURE__ */ React.createElement("div", { className: "pf-filters" }, /* @__PURE__ */ React.createElement(
      "button",
      {
        className: "pf-fbtn" + (resFilter === "all" && prioFilter === "all" ? " active" : ""),
        onClick: () => {
          setResFilter("all");
          setPrioFilter("all");
        }
      },
      "Wszystkie"
    ), /* @__PURE__ */ React.createElement(
      "button",
      {
        className: "pf-fbtn" + (resFilter === "diff" ? " active" : ""),
        onClick: () => setResFilter(resFilter === "diff" ? "all" : "diff")
      },
      /* @__PURE__ */ React.createElement("span", { className: "dot", style: { background: "var(--result-diff)" } }),
      "R\xF3\u017Cnice",
      /* @__PURE__ */ React.createElement("span", { className: "cnt" }, diffCount)
    ), /* @__PURE__ */ React.createElement(
      "button",
      {
        className: "pf-fbtn" + (prioFilter === "KR" ? " active" : ""),
        onClick: () => setPrioFilter(prioFilter === "KR" ? "all" : "KR")
      },
      /* @__PURE__ */ React.createElement("span", { className: "dot", style: { background: "var(--prio-critical)" } }),
      "Krytyczne"
    ))), /* @__PURE__ */ React.createElement("div", { style: { display: "grid", gap: "var(--pf-gap-cards)" } }, shown.map((f, i) => /* @__PURE__ */ React.createElement(
      FieldCard,
      {
        key: f.id,
        field: f,
        idx: fields.indexOf(f),
        openLb: (field) => setLb(field)
      }
    )), shown.length === 0 && /* @__PURE__ */ React.createElement("div", { className: "pf-empty" }, "Brak p\xF3l dla wybranego filtra.")), lb && /* @__PURE__ */ React.createElement(Lightbox, { field: lb, onClose: () => setLb(null) }));
  }
  ReactDOM.createRoot(document.getElementById("pfroot")).render(/* @__PURE__ */ React.createElement(PfApp, null));
})();
