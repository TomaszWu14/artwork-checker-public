// Zbudowane z frontend/src/design_preview/*.jsx przez `npm run build` — nie edytuj ręcznie.
// ── design-canvas.jsx ──
(() => {
  const DC = {
    bg: "#08111e",
    grid: "rgba(255,255,255,0.04)",
    label: "rgba(193,202,216,0.7)",
    title: "rgba(234,237,242,0.9)",
    subtitle: "rgba(193,202,216,0.6)",
    postitBg: "#ffba4f",
    postitText: "#3a2a12",
    font: '-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif'
  };
  if (typeof document !== "undefined" && !document.getElementById("dc-styles")) {
    const s = document.createElement("style");
    s.id = "dc-styles";
    s.textContent = [
      ".dc-editable{cursor:text;outline:none;white-space:nowrap;border-radius:3px;padding:0 2px;margin:0 -2px}",
      ".dc-editable:focus{background:#fff;box-shadow:0 0 0 1.5px #c96442}",
      "[data-dc-slot]{transition:transform .18s cubic-bezier(.2,.7,.3,1)}",
      "[data-dc-slot].dc-dragging{transition:none;z-index:10;pointer-events:none}",
      "[data-dc-slot].dc-dragging .dc-card{box-shadow:0 12px 40px rgba(0,0,0,.25),0 0 0 2px #c96442;transform:scale(1.02)}",
      // isolation:isolate contains artboard content's z-indexes so a
      // z-indexed child (sticky navbar etc.) can't paint over .dc-header or
      // the .dc-menu popover that drops into the top of the card.
      ".dc-card{isolation:isolate;transition:box-shadow .15s,transform .15s}",
      ".dc-card *{scrollbar-width:none}",
      ".dc-card *::-webkit-scrollbar{display:none}",
      // Per-artboard header: grip + label on the left, delete/expand on the
      // right. Single flex row; when the artboard's on-screen width is too
      // narrow for both the label yields (ellipsis, then hidden entirely below
      // ~4ch via the container query) and the buttons stay on the row.
      ".dc-header{position:absolute;bottom:100%;left:-4px;margin-bottom:calc(4px * var(--dc-inv-zoom,1));z-index:2;",
      "  display:flex;align-items:center;container-type:inline-size}",
      ".dc-labelrow{display:flex;align-items:center;gap:4px;height:24px;flex:1 1 auto;min-width:0}",
      ".dc-grip{flex:0 0 auto;cursor:grab;display:flex;align-items:center;padding:5px 4px;border-radius:4px;transition:background .12s,opacity .12s}",
      ".dc-grip:hover{background:rgba(0,0,0,.08)}",
      ".dc-grip:active{cursor:grabbing}",
      ".dc-labeltext{flex:1 1 auto;min-width:0;cursor:pointer;border-radius:4px;padding:3px 6px;",
      "  display:flex;align-items:center;transition:background .12s;overflow:hidden}",
      // Below ~4ch of label room: hide the label entirely, and drop the grip to
      // hover-only (same reveal rule as .dc-btns) so a narrow header is clean
      // until the card is moused.
      "@container (max-width: 110px){",
      "  .dc-labeltext{display:none}",
      "  .dc-grip{opacity:0}",
      "  [data-dc-slot]:hover .dc-grip{opacity:1}",
      "}",
      ".dc-labeltext:hover{background:rgba(0,0,0,.05)}",
      ".dc-labeltext .dc-editable{overflow:hidden;text-overflow:ellipsis;max-width:100%}",
      ".dc-labeltext .dc-editable:focus{overflow:visible;text-overflow:clip}",
      ".dc-btns{flex:0 0 auto;margin-left:auto;display:flex;gap:2px;opacity:0;transition:opacity .12s}",
      "[data-dc-slot]:hover .dc-btns,.dc-btns:has(.dc-menu){opacity:1}",
      ".dc-expand,.dc-kebab{width:22px;height:22px;border-radius:5px;border:none;cursor:pointer;padding:0;",
      "  background:transparent;color:rgba(60,50,40,.7);display:flex;align-items:center;justify-content:center;",
      "  font:inherit;transition:background .12s,color .12s}",
      ".dc-expand:hover,.dc-kebab:hover{background:rgba(0,0,0,.06);color:#2a251f}",
      // Slot hosting an open menu floats above later siblings (which otherwise
      // paint on top — same z-index:auto, later DOM order) so the popup isn't
      // clipped by the next card.
      "[data-dc-slot]:has(.dc-menu){z-index:10}",
      ".dc-menu{position:absolute;top:100%;right:0;margin-top:4px;background:#fff;border-radius:8px;",
      "  box-shadow:0 8px 28px rgba(0,0,0,.18),0 0 0 1px rgba(0,0,0,.05);padding:4px;min-width:160px;z-index:10}",
      ".dc-menu button{display:block;width:100%;padding:7px 10px;border:0;background:transparent;",
      "  border-radius:5px;font-family:inherit;font-size:13px;font-weight:500;line-height:1.2;",
      "  color:#29261b;cursor:pointer;text-align:left;transition:background .12s;white-space:nowrap}",
      ".dc-menu button:hover{background:rgba(0,0,0,.05)}",
      ".dc-menu hr{border:0;border-top:1px solid rgba(0,0,0,.08);margin:4px 2px}",
      ".dc-menu .dc-danger{color:#c96442}",
      ".dc-menu .dc-danger:hover{background:rgba(201,100,66,.1)}",
      // Chrome (titles / labels / buttons) counter-scales against the viewport
      // zoom so it stays a constant on-screen size. --dc-inv-zoom is set by
      // DCViewport on every transform update and inherits to all descendants —
      // any overlay inside the world (e.g. a TweaksPanel on an artboard) can use
      // it the same way.
      //
      // The header uses transform:scale (out-of-flow, so layout impact doesn't
      // matter) with its world-space width set to card-width / inv-zoom so that
      // after counter-scaling its on-screen width exactly matches the card's —
      // that's what lets the container query + text-overflow behave against the
      // card's visible edge at every zoom level.
      //
      // The section head uses CSS zoom instead of transform so its layout box
      // grows with the counter-scale, pushing the card row down — otherwise the
      // constant-screen-size title would overflow into the (shrinking) world-
      // space gap and overlap the artboard headers at low zoom.
      ".dc-header{width:calc((100% + 4px) / var(--dc-inv-zoom,1));",
      "  transform:scale(var(--dc-inv-zoom,1));transform-origin:bottom left}",
      ".dc-sectionhead{zoom:var(--dc-inv-zoom,1)}"
    ].join("\n");
    document.head.appendChild(s);
  }
  const DCCtx = React.createContext(null);
  function dcFlatten(children) {
    const out = [];
    React.Children.forEach(children, (c) => {
      if (c && c.type === React.Fragment) out.push(...dcFlatten(c.props.children));
      else out.push(c);
    });
    return out;
  }
  const DC_STATE_FILE = ".design-canvas.state.json";
  function DesignCanvas({ children, minScale, maxScale, style }) {
    const [state, setState] = React.useState({ sections: {}, focus: null });
    const [ready, setReady] = React.useState(false);
    const didRead = React.useRef(false);
    const skipNextWrite = React.useRef(false);
    React.useEffect(() => {
      let off = false;
      fetch("./" + DC_STATE_FILE).then((r) => r.ok ? r.json() : null).then((saved) => {
        if (off || !saved || !saved.sections) return;
        skipNextWrite.current = true;
        setState((s) => ({ ...s, sections: saved.sections }));
      }).catch(() => {
      }).finally(() => {
        didRead.current = true;
        if (!off) setReady(true);
      });
      const t = setTimeout(() => {
        if (!off) setReady(true);
      }, 150);
      return () => {
        off = true;
        clearTimeout(t);
      };
    }, []);
    React.useEffect(() => {
      if (!didRead.current) return;
      if (skipNextWrite.current) {
        skipNextWrite.current = false;
        return;
      }
      const t = setTimeout(() => {
        window.omelette?.writeFile(DC_STATE_FILE, JSON.stringify({ sections: state.sections })).catch(() => {
        });
      }, 250);
      return () => clearTimeout(t);
    }, [state.sections]);
    const registry = {};
    const sectionMeta = {};
    const sectionOrder = [];
    dcFlatten(children).forEach((sec) => {
      if (!sec || sec.type !== DCSection) return;
      const sid = sec.props.id ?? sec.props.title;
      if (!sid) return;
      sectionOrder.push(sid);
      const persisted = state.sections[sid] || {};
      const abs = [];
      dcFlatten(sec.props.children).forEach((ab) => {
        if (!ab || ab.type !== DCArtboard) return;
        const aid = ab.props.id ?? ab.props.label;
        if (aid) abs.push([aid, ab]);
      });
      const srcKey = abs.map(([k]) => k).join("");
      const hidden = persisted.srcKey === srcKey ? persisted.hidden || [] : [];
      const srcIds = [];
      abs.forEach(([aid, ab]) => {
        if (hidden.includes(aid)) return;
        registry[`${sid}/${aid}`] = { sectionId: sid, artboard: ab };
        srcIds.push(aid);
      });
      const kept = (persisted.order || []).filter((k) => srcIds.includes(k));
      sectionMeta[sid] = {
        title: persisted.title ?? sec.props.title,
        subtitle: sec.props.subtitle,
        slotIds: [...kept, ...srcIds.filter((k) => !kept.includes(k))]
      };
    });
    const api = React.useMemo(() => ({
      state,
      section: (id) => state.sections[id] || {},
      patchSection: (id, p) => setState((s) => ({
        ...s,
        sections: { ...s.sections, [id]: { ...s.sections[id], ...typeof p === "function" ? p(s.sections[id] || {}) : p } }
      })),
      setFocus: (slotId) => setState((s) => ({ ...s, focus: slotId }))
    }), [state]);
    React.useEffect(() => {
      const onKey = (e) => {
        if (e.key === "Escape") api.setFocus(null);
      };
      const onPd = (e) => {
        const ae = document.activeElement;
        if (ae && ae.isContentEditable && !ae.contains(e.target)) ae.blur();
      };
      document.addEventListener("keydown", onKey);
      document.addEventListener("pointerdown", onPd, true);
      return () => {
        document.removeEventListener("keydown", onKey);
        document.removeEventListener("pointerdown", onPd, true);
      };
    }, [api]);
    return /* @__PURE__ */ React.createElement(DCCtx.Provider, { value: api }, /* @__PURE__ */ React.createElement(DCViewport, { minScale, maxScale, style }, ready && children), state.focus && registry[state.focus] && /* @__PURE__ */ React.createElement(DCFocusOverlay, { entry: registry[state.focus], sectionMeta, sectionOrder }));
  }
  function DCViewport({ children, minScale = 0.1, maxScale = 8, style = {} }) {
    const vpRef = React.useRef(null);
    const worldRef = React.useRef(null);
    const tf = React.useRef({ x: 0, y: 0, scale: 1 });
    const tfKey = "dc-viewport:" + location.pathname;
    const saveT = React.useRef(0);
    const lastPostedScale = React.useRef();
    const apply = React.useCallback(() => {
      const { x, y, scale } = tf.current;
      const el = worldRef.current;
      if (!el) return;
      el.style.transform = `translate3d(${x}px, ${y}px, 0) scale(${scale})`;
      el.style.setProperty("--dc-inv-zoom", String(1 / scale));
      if (lastPostedScale.current !== scale) {
        lastPostedScale.current = scale;
        window.parent.postMessage({ type: "__dc_zoom", scale }, "*");
      }
      clearTimeout(saveT.current);
      saveT.current = setTimeout(() => {
        try {
          localStorage.setItem(tfKey, JSON.stringify(tf.current));
        } catch {
        }
      }, 200);
    }, [tfKey]);
    React.useLayoutEffect(() => {
      const flush = () => {
        clearTimeout(saveT.current);
        try {
          localStorage.setItem(tfKey, JSON.stringify(tf.current));
        } catch {
        }
      };
      try {
        const s = JSON.parse(localStorage.getItem(tfKey) || "null");
        if (s && Number.isFinite(s.x) && Number.isFinite(s.y) && Number.isFinite(s.scale)) {
          tf.current = { x: s.x, y: s.y, scale: Math.min(maxScale, Math.max(minScale, s.scale)) };
          apply();
        }
      } catch {
      }
      window.addEventListener("pagehide", flush);
      return () => {
        window.removeEventListener("pagehide", flush);
        flush();
      };
    }, []);
    React.useEffect(() => {
      const vp = vpRef.current;
      if (!vp) return;
      const zoomAt = (cx, cy, factor) => {
        const r = vp.getBoundingClientRect();
        const px = cx - r.left, py = cy - r.top;
        const t = tf.current;
        const next = Math.min(maxScale, Math.max(minScale, t.scale * factor));
        const k = next / t.scale;
        let marker = null, markerY0 = 0;
        if (k !== 1) {
          const hit = document.elementFromPoint(cx, cy);
          marker = hit && hit.closest ? hit.closest("[data-dc-slot],[data-dc-section]") : null;
          if (marker) markerY0 = marker.getBoundingClientRect().top;
        }
        t.x = px - (px - t.x) * k;
        t.y = py - (py - t.y) * k;
        t.scale = next;
        apply();
        if (marker) {
          const drift = marker.getBoundingClientRect().top - (cy + (markerY0 - cy) * k);
          if (Math.abs(drift) > 0.1) {
            t.y -= drift;
            apply();
          }
        }
      };
      const isMouseWheel = (e) => e.deltaMode !== 0 || e.deltaX === 0 && Number.isInteger(e.deltaY) && Math.abs(e.deltaY) >= 40;
      const onWheel = (e) => {
        e.preventDefault();
        if (isGesturing) return;
        if ((e.ctrlKey || e.metaKey) && !isMouseWheel(e)) {
          zoomAt(e.clientX, e.clientY, Math.exp(-e.deltaY * 0.01));
        } else if (isMouseWheel(e)) {
          zoomAt(e.clientX, e.clientY, Math.exp(-Math.sign(e.deltaY) * 0.18));
        } else {
          tf.current.x -= e.deltaX;
          tf.current.y -= e.deltaY;
          apply();
        }
      };
      let gsBase = 1;
      let isGesturing = false;
      const onGestureStart = (e) => {
        e.preventDefault();
        isGesturing = true;
        gsBase = tf.current.scale;
      };
      const onGestureChange = (e) => {
        e.preventDefault();
        zoomAt(e.clientX, e.clientY, gsBase * e.scale / tf.current.scale);
      };
      const onGestureEnd = (e) => {
        e.preventDefault();
        isGesturing = false;
      };
      let drag = null;
      const onPointerDown = (e) => {
        const onBg = !e.target.closest("[data-dc-slot], .dc-editable");
        if (!(e.button === 1 || e.button === 0 && onBg)) return;
        e.preventDefault();
        vp.setPointerCapture(e.pointerId);
        drag = { id: e.pointerId, lx: e.clientX, ly: e.clientY };
        vp.style.cursor = "grabbing";
      };
      const onPointerMove = (e) => {
        if (!drag || e.pointerId !== drag.id) return;
        tf.current.x += e.clientX - drag.lx;
        tf.current.y += e.clientY - drag.ly;
        drag.lx = e.clientX;
        drag.ly = e.clientY;
        apply();
      };
      const onPointerUp = (e) => {
        if (!drag || e.pointerId !== drag.id) return;
        vp.releasePointerCapture(e.pointerId);
        drag = null;
        vp.style.cursor = "";
      };
      const onHostMsg = (e) => {
        const d = e.data;
        if (d && d.type === "__dc_set_zoom" && typeof d.scale === "number") {
          const r = vp.getBoundingClientRect();
          zoomAt(r.left + r.width / 2, r.top + r.height / 2, d.scale / tf.current.scale);
        } else if (d && d.type === "__dc_probe") {
          window.parent.postMessage({ type: "__dc_present" }, "*");
          lastPostedScale.current = void 0;
          apply();
        }
      };
      window.addEventListener("message", onHostMsg);
      window.parent.postMessage({ type: "__dc_present" }, "*");
      lastPostedScale.current = void 0;
      apply();
      vp.addEventListener("wheel", onWheel, { passive: false });
      vp.addEventListener("gesturestart", onGestureStart, { passive: false });
      vp.addEventListener("gesturechange", onGestureChange, { passive: false });
      vp.addEventListener("gestureend", onGestureEnd, { passive: false });
      vp.addEventListener("pointerdown", onPointerDown);
      vp.addEventListener("pointermove", onPointerMove);
      vp.addEventListener("pointerup", onPointerUp);
      vp.addEventListener("pointercancel", onPointerUp);
      return () => {
        window.removeEventListener("message", onHostMsg);
        vp.removeEventListener("wheel", onWheel);
        vp.removeEventListener("gesturestart", onGestureStart);
        vp.removeEventListener("gesturechange", onGestureChange);
        vp.removeEventListener("gestureend", onGestureEnd);
        vp.removeEventListener("pointerdown", onPointerDown);
        vp.removeEventListener("pointermove", onPointerMove);
        vp.removeEventListener("pointerup", onPointerUp);
        vp.removeEventListener("pointercancel", onPointerUp);
      };
    }, [apply, minScale, maxScale]);
    const gridSvg = `url("data:image/svg+xml,%3Csvg width='120' height='120' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M120 0H0v120' fill='none' stroke='${encodeURIComponent(DC.grid)}' stroke-width='1'/%3E%3C/svg%3E")`;
    return /* @__PURE__ */ React.createElement(
      "div",
      {
        ref: vpRef,
        className: "design-canvas",
        style: {
          height: "100vh",
          width: "100vw",
          background: DC.bg,
          overflow: "hidden",
          overscrollBehavior: "none",
          touchAction: "none",
          position: "relative",
          fontFamily: DC.font,
          boxSizing: "border-box",
          ...style
        }
      },
      /* @__PURE__ */ React.createElement(
        "div",
        {
          ref: worldRef,
          style: {
            position: "absolute",
            top: 0,
            left: 0,
            transformOrigin: "0 0",
            willChange: "transform",
            width: "max-content",
            minWidth: "100%",
            minHeight: "100%",
            padding: "60px 0 80px"
          }
        },
        /* @__PURE__ */ React.createElement("div", { style: { position: "absolute", inset: -6e3, backgroundImage: gridSvg, backgroundSize: "120px 120px", pointerEvents: "none", zIndex: -1 } }),
        children
      )
    );
  }
  function DCSection({ id, title, subtitle, children, gap = 48 }) {
    const ctx = React.useContext(DCCtx);
    const sid = id ?? title;
    const all = React.Children.toArray(dcFlatten(children));
    const artboards = all.filter((c) => c && c.type === DCArtboard);
    const rest = all.filter((c) => !(c && c.type === DCArtboard));
    const sec = ctx && sid && ctx.section(sid) || {};
    const allIds = artboards.map((a) => a.props.id ?? a.props.label).filter(Boolean);
    const srcKey = allIds.join("");
    const hidden = sec.srcKey === srcKey ? sec.hidden || [] : [];
    const srcOrder = allIds.filter((k) => !hidden.includes(k));
    const order = React.useMemo(() => {
      const kept = (sec.order || []).filter((k) => srcOrder.includes(k));
      return [...kept, ...srcOrder.filter((k) => !kept.includes(k))];
    }, [sec.order, srcOrder.join("|")]);
    const byId = Object.fromEntries(artboards.map((a) => [a.props.id ?? a.props.label, a]));
    return /* @__PURE__ */ React.createElement(
      "div",
      {
        "data-dc-section": sid,
        style: { marginBottom: "calc(80px * var(--dc-inv-zoom, 1))", position: "relative" }
      },
      /* @__PURE__ */ React.createElement("div", { style: { padding: "0 60px" } }, /* @__PURE__ */ React.createElement("div", { className: "dc-sectionhead", style: { paddingBottom: 36 } }, /* @__PURE__ */ React.createElement(
        DCEditable,
        {
          tag: "div",
          value: sec.title ?? title,
          onChange: (v) => ctx && sid && ctx.patchSection(sid, { title: v }),
          style: { fontSize: 28, fontWeight: 600, color: DC.title, letterSpacing: -0.4, marginBottom: 6, display: "inline-block" }
        }
      ), subtitle && /* @__PURE__ */ React.createElement("div", { style: { fontSize: 16, color: DC.subtitle } }, subtitle))),
      /* @__PURE__ */ React.createElement("div", { style: { display: "flex", gap, padding: "0 60px", alignItems: "flex-start", width: "max-content" } }, order.map((k) => /* @__PURE__ */ React.createElement(
        DCArtboardFrame,
        {
          key: k,
          sectionId: sid,
          artboard: byId[k],
          order,
          label: (sec.labels || {})[k] ?? byId[k].props.label,
          onRename: (v) => ctx && ctx.patchSection(sid, (x) => ({ labels: { ...x.labels, [k]: v } })),
          onReorder: (next) => ctx && ctx.patchSection(sid, { order: next }),
          onDelete: () => ctx && ctx.patchSection(sid, (x) => ({
            hidden: [...x.srcKey === srcKey ? x.hidden || [] : [], k],
            srcKey
          })),
          onFocus: () => ctx && ctx.setFocus(`${sid}/${k}`)
        }
      ))),
      rest
    );
  }
  function DCArtboard() {
    return null;
  }
  async function dcExport(node, w, h, name, kind) {
    try {
      await document.fonts.ready;
    } catch {
    }
    const toDataURL = (url) => fetch(url).then((r) => r.blob()).then((b) => new Promise((res) => {
      const fr = new FileReader();
      fr.onload = () => res(fr.result);
      fr.onerror = () => res(url);
      fr.readAsDataURL(b);
    })).catch(() => url);
    const fontRules = [], pending = [], seen = /* @__PURE__ */ new Set();
    const scrapeCss = (href) => {
      if (seen.has(href)) return;
      seen.add(href);
      pending.push(fetch(href).then((r) => r.text()).then((css) => {
        for (const m of css.match(/@font-face\s*{[^}]*}/g) || []) fontRules.push({ css: m, base: href });
        for (const m of css.matchAll(/@import\s+(?:url\()?['"]?([^'")\s;]+)/g))
          scrapeCss(new URL(m[1], href).href);
      }).catch(() => {
      }));
    };
    const walk = (rules, base) => {
      for (const r of rules) {
        if (r.type === CSSRule.FONT_FACE_RULE) fontRules.push({ css: r.cssText, base });
        else if (r.type === CSSRule.IMPORT_RULE && r.styleSheet) {
          const ibase = r.styleSheet.href || base;
          try {
            walk(r.styleSheet.cssRules, ibase);
          } catch {
            scrapeCss(ibase);
          }
        } else if (r.cssRules) walk(r.cssRules, base);
      }
    };
    for (const ss of document.styleSheets) {
      const base = ss.href || location.href;
      try {
        walk(ss.cssRules, base);
      } catch {
        if (ss.href) scrapeCss(ss.href);
      }
    }
    while (pending.length) await pending.shift();
    const fontCss = (await Promise.all(fontRules.map(async (rule) => {
      let out = rule.css, m;
      const re = /url\((['"]?)([^'")]+)\1\)/g;
      while (m = re.exec(rule.css)) {
        if (m[2].indexOf("data:") === 0) continue;
        let abs;
        try {
          abs = new URL(m[2], rule.base).href;
        } catch {
          continue;
        }
        out = out.split(m[0]).join('url("' + await toDataURL(abs) + '")');
      }
      return out;
    }))).join("\n");
    const cloneStyled = (src) => {
      if (src.nodeType === 8 || src.nodeType === 1 && src.tagName === "SCRIPT") return document.createTextNode("");
      const dst = src.cloneNode(false);
      if (src.nodeType === 1) {
        const cs = getComputedStyle(src);
        let txt = "";
        for (let i = 0; i < cs.length; i++) txt += cs[i] + ":" + cs.getPropertyValue(cs[i]) + ";";
        dst.setAttribute("style", txt + "animation:none;transition:none;");
        if (src.tagName === "CANVAS") try {
          const im = document.createElement("img");
          im.src = src.toDataURL();
          im.setAttribute("style", txt);
          return im;
        } catch {
        }
      }
      for (let c = src.firstChild; c; c = c.nextSibling) dst.appendChild(cloneStyled(c));
      return dst;
    };
    const clone = cloneStyled(node);
    clone.setAttribute("xmlns", "http://www.w3.org/1999/xhtml");
    clone.style.boxShadow = "none";
    clone.style.borderRadius = "0";
    const jobs = [];
    clone.querySelectorAll("img").forEach((el) => {
      const s = el.getAttribute("src");
      if (s && s.indexOf("data:") !== 0) jobs.push(toDataURL(el.src).then((d) => el.setAttribute("src", d)));
    });
    [clone, ...clone.querySelectorAll("*")].forEach((el) => {
      const bg = el.style.backgroundImage;
      if (!bg) return;
      let m;
      const re = /url\(["']?([^"')]+)["']?\)/g;
      while (m = re.exec(bg)) {
        const tok = m[0], url = m[1];
        if (url.indexOf("data:") === 0) continue;
        jobs.push(toDataURL(url).then((d) => {
          el.style.backgroundImage = el.style.backgroundImage.split(tok).join('url("' + d + '")');
        }));
      }
    });
    await Promise.all(jobs);
    const xml = new XMLSerializer().serializeToString(clone);
    const save = (blob, ext) => {
      if (!blob) return;
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = name + "." + ext;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 1e3);
    };
    if (kind === "html") {
      const html = '<!doctype html><html><head><meta charset="utf-8"><title>' + name + "</title>" + (fontCss ? "<style>" + fontCss + "</style>" : "") + '</head><body style="margin:0">' + xml + "</body></html>";
      return save(new Blob([html], { type: "text/html" }), "html");
    }
    const px = 3;
    const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="' + w * px + '" height="' + h * px + '" viewBox="0 0 ' + w + " " + h + '"><foreignObject width="' + w + '" height="' + h + '">' + (fontCss ? "<style><![CDATA[" + fontCss + "]]></style>" : "") + xml + "</foreignObject></svg>";
    const img = new Image();
    await new Promise((res, rej) => {
      img.onload = res;
      img.onerror = () => rej(new Error("svg load failed"));
      img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
    });
    const cv = document.createElement("canvas");
    cv.width = w * px;
    cv.height = h * px;
    cv.getContext("2d").drawImage(img, 0, 0);
    cv.toBlob((blob) => save(blob, "png"), "image/png");
  }
  function DCArtboardFrame({ sectionId, artboard, label, order, onRename, onReorder, onFocus, onDelete }) {
    const { id: rawId, label: rawLabel, width = 260, height = 480, children, style = {} } = artboard.props;
    const id = rawId ?? rawLabel;
    const ref = React.useRef(null);
    const cardRef = React.useRef(null);
    const menuRef = React.useRef(null);
    const [menuOpen, setMenuOpen] = React.useState(false);
    const [confirming, setConfirming] = React.useState(false);
    React.useEffect(() => {
      if (!menuOpen) {
        setConfirming(false);
        return;
      }
      const off = (e) => {
        if (!menuRef.current || !menuRef.current.contains(e.target)) setMenuOpen(false);
      };
      document.addEventListener("pointerdown", off, true);
      return () => document.removeEventListener("pointerdown", off, true);
    }, [menuOpen]);
    const doExport = (kind) => {
      setMenuOpen(false);
      if (!cardRef.current) return;
      const name = String(label || id || "artboard").replace(/[^\w\s.-]+/g, "_");
      dcExport(cardRef.current, width, height, name, kind).catch((e) => console.error("[design-canvas] export failed:", e));
    };
    const onGripDown = (e) => {
      e.preventDefault();
      e.stopPropagation();
      const me = ref.current;
      const scale = me.getBoundingClientRect().width / me.offsetWidth || 1;
      const peers = Array.from(document.querySelectorAll(`[data-dc-section="${sectionId}"] [data-dc-slot]`));
      const homes = peers.map((el) => ({ el, id: el.dataset.dcSlot, x: el.getBoundingClientRect().left }));
      const slotXs = homes.map((h) => h.x);
      const startIdx = order.indexOf(id);
      const startX = e.clientX;
      let liveOrder = order.slice();
      me.classList.add("dc-dragging");
      const layout = () => {
        for (const h of homes) {
          if (h.id === id) continue;
          const slot = liveOrder.indexOf(h.id);
          h.el.style.transform = `translateX(${(slotXs[slot] - h.x) / scale}px)`;
        }
      };
      const move = (ev) => {
        const dx = ev.clientX - startX;
        me.style.transform = `translateX(${dx / scale}px)`;
        const cur = homes[startIdx].x + dx;
        let nearest = 0, best = Infinity;
        for (let i = 0; i < slotXs.length; i++) {
          const d = Math.abs(slotXs[i] - cur);
          if (d < best) {
            best = d;
            nearest = i;
          }
        }
        if (liveOrder.indexOf(id) !== nearest) {
          liveOrder = order.filter((k) => k !== id);
          liveOrder.splice(nearest, 0, id);
          layout();
        }
      };
      const up = () => {
        document.removeEventListener("pointermove", move);
        document.removeEventListener("pointerup", up);
        const finalSlot = liveOrder.indexOf(id);
        me.classList.remove("dc-dragging");
        me.style.transform = `translateX(${(slotXs[finalSlot] - homes[startIdx].x) / scale}px)`;
        setTimeout(() => {
          for (const h of homes) {
            h.el.style.transition = "none";
            h.el.style.transform = "";
          }
          if (liveOrder.join("|") !== order.join("|")) onReorder(liveOrder);
          requestAnimationFrame(() => requestAnimationFrame(() => {
            for (const h of homes) h.el.style.transition = "";
          }));
        }, 180);
      };
      document.addEventListener("pointermove", move);
      document.addEventListener("pointerup", up);
    };
    return /* @__PURE__ */ React.createElement("div", { ref, "data-dc-slot": id, style: { position: "relative", flexShrink: 0 } }, /* @__PURE__ */ React.createElement("div", { className: "dc-header", "data-noncommentable": "", style: { color: DC.label }, onPointerDown: (e) => e.stopPropagation() }, /* @__PURE__ */ React.createElement("div", { className: "dc-labelrow" }, /* @__PURE__ */ React.createElement("div", { className: "dc-grip", onPointerDown: onGripDown, title: "Drag to reorder" }, /* @__PURE__ */ React.createElement("svg", { width: "9", height: "13", viewBox: "0 0 9 13", fill: "currentColor" }, /* @__PURE__ */ React.createElement("circle", { cx: "2", cy: "2", r: "1.1" }), /* @__PURE__ */ React.createElement("circle", { cx: "7", cy: "2", r: "1.1" }), /* @__PURE__ */ React.createElement("circle", { cx: "2", cy: "6.5", r: "1.1" }), /* @__PURE__ */ React.createElement("circle", { cx: "7", cy: "6.5", r: "1.1" }), /* @__PURE__ */ React.createElement("circle", { cx: "2", cy: "11", r: "1.1" }), /* @__PURE__ */ React.createElement("circle", { cx: "7", cy: "11", r: "1.1" }))), /* @__PURE__ */ React.createElement("div", { className: "dc-labeltext", onClick: onFocus, title: "Click to focus" }, /* @__PURE__ */ React.createElement(
      DCEditable,
      {
        value: label,
        onChange: onRename,
        onClick: (e) => e.stopPropagation(),
        style: { fontSize: 15, fontWeight: 500, color: DC.label, lineHeight: 1 }
      }
    ))), /* @__PURE__ */ React.createElement("div", { className: "dc-btns" }, /* @__PURE__ */ React.createElement("div", { ref: menuRef, style: { position: "relative" } }, /* @__PURE__ */ React.createElement("button", { className: "dc-kebab", title: "More", onClick: () => setMenuOpen((o) => !o) }, /* @__PURE__ */ React.createElement("svg", { width: "12", height: "12", viewBox: "0 0 12 12", fill: "currentColor" }, /* @__PURE__ */ React.createElement("circle", { cx: "2.5", cy: "6", r: "1.1" }), /* @__PURE__ */ React.createElement("circle", { cx: "6", cy: "6", r: "1.1" }), /* @__PURE__ */ React.createElement("circle", { cx: "9.5", cy: "6", r: "1.1" }))), menuOpen && /* @__PURE__ */ React.createElement("div", { className: "dc-menu", onPointerDown: (e) => e.stopPropagation() }, /* @__PURE__ */ React.createElement("button", { onClick: () => doExport("png") }, "Download PNG"), /* @__PURE__ */ React.createElement("button", { onClick: () => doExport("html") }, "Download HTML"), /* @__PURE__ */ React.createElement("hr", null), /* @__PURE__ */ React.createElement(
      "button",
      {
        className: "dc-danger",
        onClick: () => {
          if (confirming) {
            setMenuOpen(false);
            onDelete();
          } else setConfirming(true);
        }
      },
      confirming ? "Click again to delete" : "Delete"
    ))), /* @__PURE__ */ React.createElement("button", { className: "dc-expand", onClick: onFocus, title: "Focus" }, /* @__PURE__ */ React.createElement("svg", { width: "12", height: "12", viewBox: "0 0 12 12", fill: "none", stroke: "currentColor", strokeWidth: "1.6", strokeLinecap: "round" }, /* @__PURE__ */ React.createElement("path", { d: "M7 1h4v4M5 11H1V7M11 1L7.5 4.5M1 11l3.5-3.5" }))))), /* @__PURE__ */ React.createElement(
      "div",
      {
        ref: cardRef,
        className: "dc-card",
        style: { borderRadius: 2, boxShadow: "0 1px 3px rgba(0,0,0,.08),0 4px 16px rgba(0,0,0,.06)", overflow: "hidden", width, height, background: "#fff", ...style }
      },
      children || /* @__PURE__ */ React.createElement("div", { style: { height: "100%", display: "flex", alignItems: "center", justifyContent: "center", color: "#bbb", fontSize: 13, fontFamily: DC.font } }, id)
    ));
  }
  function DCEditable({ value, onChange, style, tag = "span", onClick }) {
    const T = tag;
    return /* @__PURE__ */ React.createElement(
      T,
      {
        className: "dc-editable",
        contentEditable: true,
        suppressContentEditableWarning: true,
        onClick,
        onPointerDown: (e) => e.stopPropagation(),
        onBlur: (e) => onChange && onChange(e.currentTarget.textContent),
        onKeyDown: (e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            e.currentTarget.blur();
          }
        },
        style
      },
      value
    );
  }
  function DCFocusOverlay({ entry, sectionMeta, sectionOrder }) {
    const ctx = React.useContext(DCCtx);
    const { sectionId, artboard } = entry;
    const sec = ctx.section(sectionId);
    const meta = sectionMeta[sectionId];
    const peers = meta.slotIds;
    const aid = artboard.props.id ?? artboard.props.label;
    const idx = peers.indexOf(aid);
    const secIdx = sectionOrder.indexOf(sectionId);
    const go = (d) => {
      const n = peers[(idx + d + peers.length) % peers.length];
      if (n) ctx.setFocus(`${sectionId}/${n}`);
    };
    const goSection = (d) => {
      const n = sectionOrder.length;
      for (let i = 1; i < n; i++) {
        const ns = sectionOrder[((secIdx + d * i) % n + n) % n];
        const first = sectionMeta[ns] && sectionMeta[ns].slotIds[0];
        if (first) {
          ctx.setFocus(`${ns}/${first}`);
          return;
        }
      }
    };
    React.useEffect(() => {
      const k = (e) => {
        if (e.key === "ArrowLeft") {
          e.preventDefault();
          go(-1);
        }
        if (e.key === "ArrowRight") {
          e.preventDefault();
          go(1);
        }
        if (e.key === "ArrowUp") {
          e.preventDefault();
          goSection(-1);
        }
        if (e.key === "ArrowDown") {
          e.preventDefault();
          goSection(1);
        }
      };
      document.addEventListener("keydown", k);
      return () => document.removeEventListener("keydown", k);
    });
    const { width = 260, height = 480, children } = artboard.props;
    const [vp, setVp] = React.useState({ w: window.innerWidth, h: window.innerHeight });
    React.useEffect(() => {
      const r = () => setVp({ w: window.innerWidth, h: window.innerHeight });
      window.addEventListener("resize", r);
      return () => window.removeEventListener("resize", r);
    }, []);
    const scale = Math.max(0.1, Math.min((vp.w - 200) / width, (vp.h - 260) / height, 2));
    const [ddOpen, setDd] = React.useState(false);
    const Arrow = ({ dir, onClick }) => /* @__PURE__ */ React.createElement(
      "button",
      {
        onClick: (e) => {
          e.stopPropagation();
          onClick();
        },
        style: {
          position: "absolute",
          top: "50%",
          [dir]: 28,
          transform: "translateY(-50%)",
          border: "none",
          background: "rgba(255,255,255,.08)",
          color: "rgba(255,255,255,.9)",
          width: 44,
          height: 44,
          borderRadius: 22,
          fontSize: 18,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transition: "background .15s"
        },
        onMouseEnter: (e) => e.currentTarget.style.background = "rgba(255,255,255,.18)",
        onMouseLeave: (e) => e.currentTarget.style.background = "rgba(255,255,255,.08)"
      },
      /* @__PURE__ */ React.createElement("svg", { width: "18", height: "18", viewBox: "0 0 18 18", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round" }, /* @__PURE__ */ React.createElement("path", { d: dir === "left" ? "M11 3L5 9l6 6" : "M7 3l6 6-6 6" }))
    );
    return ReactDOM.createPortal(
      /* @__PURE__ */ React.createElement(
        "div",
        {
          onClick: () => ctx.setFocus(null),
          onWheel: (e) => e.preventDefault(),
          style: {
            position: "fixed",
            inset: 0,
            zIndex: 100,
            background: "rgba(24,20,16,.6)",
            backdropFilter: "blur(14px)",
            fontFamily: DC.font,
            color: "#fff"
          }
        },
        /* @__PURE__ */ React.createElement(
          "div",
          {
            onClick: (e) => e.stopPropagation(),
            style: { position: "absolute", top: 0, left: 0, right: 0, height: 72, display: "flex", alignItems: "flex-start", padding: "16px 20px 0", gap: 16 }
          },
          /* @__PURE__ */ React.createElement("div", { style: { position: "relative" } }, /* @__PURE__ */ React.createElement(
            "button",
            {
              onClick: () => setDd((o) => !o),
              style: {
                border: "none",
                background: "transparent",
                color: "#fff",
                cursor: "pointer",
                padding: "6px 8px",
                borderRadius: 6,
                textAlign: "left",
                fontFamily: "inherit"
              }
            },
            /* @__PURE__ */ React.createElement("span", { style: { display: "flex", alignItems: "center", gap: 8 } }, /* @__PURE__ */ React.createElement("span", { style: { fontSize: 18, fontWeight: 600, letterSpacing: -0.3 } }, meta.title), /* @__PURE__ */ React.createElement("svg", { width: "11", height: "11", viewBox: "0 0 11 11", fill: "none", stroke: "currentColor", strokeWidth: "1.8", strokeLinecap: "round", style: { opacity: 0.7 } }, /* @__PURE__ */ React.createElement("path", { d: "M2 4l3.5 3.5L9 4" }))),
            meta.subtitle && /* @__PURE__ */ React.createElement("span", { style: { display: "block", fontSize: 13, opacity: 0.6, fontWeight: 400, marginTop: 2 } }, meta.subtitle)
          ), ddOpen && /* @__PURE__ */ React.createElement("div", { style: {
            position: "absolute",
            top: "100%",
            left: 0,
            marginTop: 4,
            background: "#2a251f",
            borderRadius: 8,
            boxShadow: "0 8px 32px rgba(0,0,0,.4)",
            padding: 4,
            minWidth: 200,
            zIndex: 10
          } }, sectionOrder.filter((sid) => sectionMeta[sid].slotIds.length).map((sid) => /* @__PURE__ */ React.createElement(
            "button",
            {
              key: sid,
              onClick: () => {
                setDd(false);
                const f = sectionMeta[sid].slotIds[0];
                if (f) ctx.setFocus(`${sid}/${f}`);
              },
              style: {
                display: "block",
                width: "100%",
                textAlign: "left",
                border: "none",
                cursor: "pointer",
                background: sid === sectionId ? "rgba(255,255,255,.1)" : "transparent",
                color: "#fff",
                padding: "8px 12px",
                borderRadius: 5,
                fontSize: 14,
                fontWeight: sid === sectionId ? 600 : 400,
                fontFamily: "inherit"
              }
            },
            sectionMeta[sid].title
          )))),
          /* @__PURE__ */ React.createElement("div", { style: { flex: 1 } }),
          /* @__PURE__ */ React.createElement(
            "button",
            {
              onClick: () => ctx.setFocus(null),
              onMouseEnter: (e) => e.currentTarget.style.background = "rgba(255,255,255,.12)",
              onMouseLeave: (e) => e.currentTarget.style.background = "transparent",
              style: {
                border: "none",
                background: "transparent",
                color: "rgba(255,255,255,.7)",
                width: 32,
                height: 32,
                borderRadius: 16,
                fontSize: 20,
                cursor: "pointer",
                lineHeight: 1,
                transition: "background .12s"
              }
            },
            "\xD7"
          )
        ),
        /* @__PURE__ */ React.createElement(
          "div",
          {
            style: { position: "absolute", top: 64, bottom: 56, left: 100, right: 100, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16 }
          },
          /* @__PURE__ */ React.createElement("div", { onClick: (e) => e.stopPropagation(), style: { width: width * scale, height: height * scale, position: "relative" } }, /* @__PURE__ */ React.createElement("div", { style: {
            width,
            height,
            transform: `scale(${scale})`,
            transformOrigin: "top left",
            background: "#fff",
            borderRadius: 2,
            overflow: "hidden",
            boxShadow: "0 20px 80px rgba(0,0,0,.4)"
          } }, children || /* @__PURE__ */ React.createElement("div", { style: { height: "100%", display: "flex", alignItems: "center", justifyContent: "center", color: "#bbb" } }, aid))),
          /* @__PURE__ */ React.createElement("div", { onClick: (e) => e.stopPropagation(), style: { fontSize: 14, fontWeight: 500, opacity: 0.85, textAlign: "center" } }, (sec.labels || {})[aid] ?? artboard.props.label, /* @__PURE__ */ React.createElement("span", { style: { opacity: 0.5, marginLeft: 10, fontVariantNumeric: "tabular-nums" } }, idx + 1, " / ", peers.length))
        ),
        /* @__PURE__ */ React.createElement(Arrow, { dir: "left", onClick: () => go(-1) }),
        /* @__PURE__ */ React.createElement(Arrow, { dir: "right", onClick: () => go(1) }),
        /* @__PURE__ */ React.createElement(
          "div",
          {
            onClick: (e) => e.stopPropagation(),
            style: { position: "absolute", bottom: 20, left: "50%", transform: "translateX(-50%)", display: "flex", gap: 8 }
          },
          peers.map((p, i) => /* @__PURE__ */ React.createElement(
            "button",
            {
              key: p,
              onClick: () => ctx.setFocus(`${sectionId}/${p}`),
              style: {
                border: "none",
                padding: 0,
                cursor: "pointer",
                width: 6,
                height: 6,
                borderRadius: 3,
                background: i === idx ? "#fff" : "rgba(255,255,255,.3)"
              }
            }
          ))
        )
      ),
      document.body
    );
  }
  function DCPostIt({ children, top, left, right, bottom, rotate = -2, width = 180 }) {
    return /* @__PURE__ */ React.createElement("div", { style: {
      position: "absolute",
      top,
      left,
      right,
      bottom,
      width,
      background: DC.postitBg,
      padding: "14px 16px",
      fontFamily: '"Comic Sans MS", "Marker Felt", "Segoe Print", cursive',
      fontSize: 14,
      lineHeight: 1.4,
      color: DC.postitText,
      boxShadow: "0 2px 8px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.08)",
      transform: `rotate(${rotate}deg)`,
      zIndex: 5
    } }, children);
  }
  Object.assign(window, { DesignCanvas, DCSection, DCArtboard, DCPostIt });
})();

// ── shared.jsx ──
(() => {
  const CMP = {
    no: "#08",
    date: "20.05.2026",
    time: "17:42",
    org: "ACME sp. z o.o.",
    product: "easyCARE Sterile Gauze Swabs \xB7 200 szt.",
    sku: "ZAY-easyCARE(200)-BNPFE",
    ean: "5900010822690",
    ref: "INVS2603110009",
    fileA: {
      name: "ZAY-easyCARE(200)-BNPFE-260320.pdf",
      version: "v1.4",
      date: "24.02.2026",
      author: "A. Kowalska",
      pages: 1,
      size: "4.2 MB",
      dim: "218 \xD7 142 mm",
      bleed: "3 mm",
      colors: "4C + Pantone 286 C",
      fonts: "Helvetica Neue, Arial"
    },
    fileB: {
      name: "ZAY-easyCARE(200)-BNPFE-260320-rev.pdf",
      version: "v1.5",
      date: "19.05.2026",
      author: "M. Nowak (dostawca: PrintHub Wuhan)",
      pages: 1,
      size: "4.5 MB",
      dim: "218 \xD7 142 mm",
      bleed: "2 mm",
      colors: "4C + Pantone 286 C",
      fonts: "Helvetica Neue, Arial, Liberation Sans"
    },
    summary: { critical: 5, warning: 8, info: 4, ok: 17, items: 34 },
    modules: [
      { id: "visual", name: "Diff wizualny", status: "fail", crit: 2, warn: 3, ok: 11, note: "2 elementy przesuni\u0119te > 2 mm" },
      { id: "text", name: "Tekst regulacyjny", status: "fail", crit: 1, warn: 1, ok: 6, note: 'Brak ostrze\u017Cenia "do u\u017Cytku zewn\u0119trznego"' },
      { id: "codes", name: "EAN / LOT / GTIN", status: "fail", crit: 1, warn: 0, ok: 4, note: "Niezgodno\u015B\u0107 EAN" },
      { id: "symbols", name: "Symbole CE / piktogramy", status: "warn", crit: 0, warn: 1, ok: 9, note: "CE przesuni\u0119te 2.3 mm" },
      { id: "lang", name: "Wersje j\u0119zykowe", status: "fail", crit: 1, warn: 0, ok: 2, note: "Brak wersji DE" },
      { id: "color", name: "Kolorystyka / Pantone", status: "warn", crit: 0, warn: 1, ok: 3, note: "\u0394E 4.2 vs pr\xF3bka" },
      { id: "type", name: "Typografia / czytelno\u015B\u0107", status: "warn", crit: 0, warn: 2, ok: 4, note: "Instrukcja < 7 pt" },
      { id: "meta", name: "Metadane PDF", status: "info", crit: 0, warn: 0, ok: 2, note: "Inny autor i edytor" }
    ],
    diffs: [
      {
        id: "D-01",
        sev: "crit",
        cat: "codes",
        field: "EAN-13",
        a: "5900010822690",
        b: "5900010822960",
        note: "Zamiana cyfr na pozycji 11\u201312 (69 \u2194 96). Walidacja sumy kontrolnej: B niepoprawne.",
        where: "Sp\xF3d, o\u015B X 162 mm, Y 12 mm",
        blocker: true
      },
      {
        id: "D-02",
        sev: "crit",
        cat: "text",
        field: "Ostrze\u017Cenie",
        a: "Wy\u0142\u0105cznie do u\u017Cytku zewn\u0119trznego. Nie spo\u017Cywa\u0107.",
        b: "\u2014",
        note: "Wymagane zgodnie z PN-EN 15986. Usuni\u0119cie blokuje rejestracj\u0119.",
        where: "Front, blok ostrze\u017Ce\u0144 (R3)",
        blocker: true
      },
      {
        id: "D-03",
        sev: "crit",
        cat: "lang",
        field: "Wersja j\u0119zykowa DE",
        a: "obecna (Deutsch)",
        b: "usuni\u0119ta",
        note: 'Wymagana dla rynku DACH. Sprawd\u017A pole "Markets" w PIM.',
        where: "Ty\u0142, kolumna 2",
        blocker: true
      },
      {
        id: "D-04",
        sev: "crit",
        cat: "codes",
        field: "Format kodu LOT",
        a: "LOT 240520",
        b: "LOT/24/05/20",
        note: "Niezgodne ze standardem GS1 zatwierdzonym przez QA (2024-11).",
        where: "Sp\xF3d, R4",
        blocker: false
      },
      {
        id: "D-05",
        sev: "crit",
        cat: "visual",
        field: "Logo ACME",
        a: "szer. 38 mm, lewy-g\xF3rny",
        b: "szer. 32 mm, przesuni\u0119te 4 mm w prawo",
        note: "Naruszenie brand guidelines \u2014 minimalny rozmiar i pole ochronne.",
        where: "Front, R1",
        blocker: false
      },
      {
        id: "D-06",
        sev: "warn",
        cat: "visual",
        field: "Symbol CE",
        a: "X 192 mm, Y 8 mm",
        b: "X 194.3 mm, Y 8 mm",
        note: "Przesuni\u0119cie 2.3 mm \u2014 w granicach tolerancji druku, ale poza siatk\u0105.",
        where: "Ty\u0142, R5",
        blocker: false
      },
      {
        id: "D-07",
        sev: "warn",
        cat: "type",
        field: "Wielko\u015B\u0107 czcionki \u2014 instrukcja",
        a: "7.0 pt",
        b: "6.5 pt",
        note: "Poni\u017Cej minimum 7 pt wg dyrektywy MDR \u2014 sprawd\u017A renderowanie.",
        where: "Ty\u0142, kolumna 1",
        blocker: false
      },
      {
        id: "D-08",
        sev: "warn",
        cat: "visual",
        field: "Spad / bleed",
        a: "3 mm",
        b: "2 mm",
        note: "Drukarnia wymaga 3 mm dla maszyny offsetowej KBA Rapida.",
        where: "Ca\u0142y arkusz",
        blocker: false
      },
      {
        id: "D-09",
        sev: "warn",
        cat: "color",
        field: "Pantone 286 C",
        a: "\u0394E 0.4 vs pr\xF3bka",
        b: "\u0394E 4.2 vs pr\xF3bka",
        note: "Powy\u017Cej akceptowalnego progu \u0394E = 2.0.",
        where: "Pasek nag\u0142\xF3wka",
        blocker: false
      },
      {
        id: "D-10",
        sev: "warn",
        cat: "visual",
        field: 'Pole "Data wa\u017Cno\u015Bci"',
        a: "Y 118 mm",
        b: "Y 122 mm",
        note: "Przesuni\u0119cie 4 mm w d\xF3\u0142; koliduje z liniami ci\u0119cia.",
        where: "Sp\xF3d, R4",
        blocker: false
      },
      {
        id: "D-11",
        sev: "warn",
        cat: "symbols",
        field: 'Piktogram "trzyma\u0107 z dala od s\u0142o\u0144ca"',
        a: "wektor",
        b: "rastrowy 220 dpi",
        note: "Rekomendowane 300 dpi lub wektor \u2014 mo\u017Cliwa pikseloza w druku.",
        where: "Sp\xF3d, R5",
        blocker: false
      },
      {
        id: "D-12",
        sev: "warn",
        cat: "type",
        field: "Czcionka dodana",
        a: "\u2014",
        b: "Liberation Sans (substytut)",
        note: "Drukarnia mo\u017Ce nie mie\u0107 tej rodziny \u2014 zaembedduj fonty.",
        where: "Metadane",
        blocker: false
      },
      {
        id: "D-13",
        sev: "warn",
        cat: "text",
        field: "Numer rejestracyjny",
        a: "PL/CA01/0258/26",
        b: "PL/CA01/0258/2026",
        note: "Format roku \u2014 zatwierdzi\u0107 z dzia\u0142em regulacyjnym.",
        where: "Ty\u0142, R6",
        blocker: false
      },
      {
        id: "D-14",
        sev: "info",
        cat: "meta",
        field: "Autor PDF",
        a: "A. Kowalska",
        b: "M. Nowak (PrintHub Wuhan)",
        note: "Plik B przygotowany przez dostawc\u0119 zewn\u0119trznego.",
        where: "Metadane",
        blocker: false
      },
      {
        id: "D-15",
        sev: "info",
        cat: "meta",
        field: "Producent PDF",
        a: "Adobe InDesign 19.5",
        b: "Adobe Acrobat 24.2 (Distiller)",
        note: "",
        where: "Metadane",
        blocker: false
      },
      {
        id: "D-16",
        sev: "info",
        cat: "visual",
        field: "Znaki ci\u0119cia",
        a: "standardowe",
        b: "standardowe + japo\u0144skie",
        note: "Dodatkowe \u2014 bez wp\u0142ywu na druk PL.",
        where: "Ca\u0142y arkusz",
        blocker: false
      },
      {
        id: "D-17",
        sev: "info",
        cat: "visual",
        field: "Profil ICC",
        a: "ISO Coated v2 (ECI)",
        b: "ISO Coated v2 300% (ECI)",
        note: "",
        where: "Metadane",
        blocker: false
      }
    ]
  };
  const CATEGORIES = {
    visual: { label: "Wizualne", icon: "\u25D0" },
    text: { label: "Tekst", icon: "\xB6" },
    codes: { label: "Kody", icon: "\u25A6" },
    symbols: { label: "Symbole", icon: "\u2295" },
    lang: { label: "J\u0119zyki", icon: "Aa" },
    color: { label: "Kolor", icon: "\u25CD" },
    type: { label: "Typografia", icon: "T" },
    meta: { label: "Metadane", icon: "\u24D8" }
  };
  const SEV = {
    crit: { label: "Krytyczny", short: "CRIT", color: "var(--critical)", bg: "var(--critical-bg)", dot: "\u25CF" },
    warn: { label: "Ostrze\u017Cenie", short: "WARN", color: "var(--warn)", bg: "var(--warn-bg)", dot: "\u25CF" },
    info: { label: "Informacja", short: "INFO", color: "var(--info)", bg: "var(--info-bg)", dot: "\u25CF" },
    ok: { label: "Zgodne", short: "OK", color: "var(--ok)", bg: "var(--ok-bg)", dot: "\u25CF" }
  };
  function SevTag({ sev, size = "sm" }) {
    const s = SEV[sev];
    const pad = size === "sm" ? "2px 7px" : "4px 9px";
    const fs = size === "sm" ? 10 : 11;
    return /* @__PURE__ */ React.createElement("span", { style: {
      display: "inline-flex",
      alignItems: "center",
      gap: 5,
      padding: pad,
      fontSize: fs,
      fontFamily: "'Geist Mono', monospace",
      fontWeight: 600,
      letterSpacing: ".04em",
      color: s.color,
      background: s.bg,
      borderRadius: 3
    } }, /* @__PURE__ */ React.createElement("span", { style: { fontSize: 8, lineHeight: 1, color: s.color } }, "\u25CF"), s.short);
  }
  function Rule({ vertical, color = "var(--rule)", style = {} }) {
    return vertical ? /* @__PURE__ */ React.createElement("div", { style: { width: 1, alignSelf: "stretch", background: color, ...style } }) : /* @__PURE__ */ React.createElement("div", { style: { height: 1, width: "100%", background: color, ...style } });
  }
  function KV({ k, v, mono, style = {} }) {
    return /* @__PURE__ */ React.createElement("div", { style: { display: "flex", alignItems: "baseline", gap: 8, ...style } }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 10, color: "var(--ink-3)", letterSpacing: ".06em", textTransform: "uppercase", minWidth: 80 } }, k), /* @__PURE__ */ React.createElement("div", { style: {
      fontSize: 12,
      color: "var(--ink)",
      fontFamily: mono ? "'Geist Mono', monospace" : "inherit"
    } }, v));
  }
  function AcmeWordmark({ color = "var(--ink)", size = 14 }) {
    return /* @__PURE__ */ React.createElement("div", { style: { display: "inline-flex", alignItems: "center", gap: 8, fontFamily: "'Geist', sans-serif", color } }, /* @__PURE__ */ React.createElement("div", { style: {
      width: size + 4,
      height: size + 4,
      borderRadius: 2,
      background: "var(--accent)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      color: "#0d1b2c",
      fontWeight: 700,
      fontSize: size - 2,
      letterSpacing: "-.02em"
    } }, "A"), /* @__PURE__ */ React.createElement("div", { style: { fontSize: size, fontWeight: 600, letterSpacing: "-.01em" } }, "ACME"));
  }
  Object.assign(window, { CMP, CATEGORIES, SEV, SevTag, Rule, KV, AcmeWordmark });
})();

// ── artwork-svg.jsx ──
(() => {
  function PackArtwork({ variant = "a", width = 520, markers = [], showGrid = false, showBleed = true }) {
    const W = 540, H = 340;
    const isA = variant === "a";
    const teal = isA ? "#1f5b75" : "#2d6e8a";
    const logoW = isA ? 84 : 70;
    const logoX = isA ? 22 : 28;
    const ceX = isA ? 460 : 466;
    const expY = isA ? 296 : 304;
    const bleed = isA ? 8 : 4;
    return /* @__PURE__ */ React.createElement("div", { style: { position: "relative", width, aspectRatio: `${W}/${H}`, userSelect: "none" } }, /* @__PURE__ */ React.createElement(
      "svg",
      {
        viewBox: `0 0 ${W} ${H}`,
        width: "100%",
        height: "100%",
        style: { display: "block", background: "#fdfcf7", borderRadius: 2 }
      },
      /* @__PURE__ */ React.createElement("rect", { x: "0", y: "0", width: W, height: H, fill: "#fdfcf7" }),
      showBleed && /* @__PURE__ */ React.createElement(
        "rect",
        {
          x: bleed,
          y: bleed,
          width: W - bleed * 2,
          height: H - bleed * 2,
          fill: "none",
          stroke: "#d1cdbe",
          strokeDasharray: "2 2",
          strokeWidth: "0.5"
        }
      ),
      /* @__PURE__ */ React.createElement("rect", { x: "0", y: "0", width: W, height: "46", fill: teal }),
      /* @__PURE__ */ React.createElement("rect", { x: "0", y: "46", width: W, height: "6", fill: isA ? "#163f54" : "#1a5570" }),
      /* @__PURE__ */ React.createElement("g", { transform: `translate(${logoX}, 12)` }, /* @__PURE__ */ React.createElement("rect", { width: logoW * 0.28, height: "22", fill: "#fdfcf7", rx: "1" }), /* @__PURE__ */ React.createElement(
        "text",
        {
          x: logoW * 0.14,
          y: "17",
          fontFamily: "Geist, sans-serif",
          fontWeight: "700",
          fontSize: "14",
          fill: teal,
          textAnchor: "middle",
          letterSpacing: "-0.5"
        },
        "Z"
      ), /* @__PURE__ */ React.createElement(
        "text",
        {
          x: logoW * 0.28 + 6,
          y: "17",
          fontFamily: "Geist, sans-serif",
          fontWeight: "600",
          fontSize: "12",
          fill: "#fdfcf7",
          letterSpacing: ".02em"
        },
        "ACME"
      )),
      /* @__PURE__ */ React.createElement(
        "text",
        {
          x: W / 2,
          y: "36",
          textAnchor: "middle",
          fontFamily: "Newsreader, serif",
          fontStyle: "italic",
          fontSize: "18",
          fill: "#fdfcf7",
          letterSpacing: ".01em"
        },
        "easyCARE"
      ),
      /* @__PURE__ */ React.createElement(
        "text",
        {
          x: "22",
          y: "78",
          fontFamily: "Geist, sans-serif",
          fontWeight: "600",
          fontSize: "11",
          fill: "#14130f",
          letterSpacing: ".02em"
        },
        "Ja\u0142owe gaziki / Sterile gauze swabs"
      ),
      /* @__PURE__ */ React.createElement(
        "text",
        {
          x: "22",
          y: "92",
          fontFamily: "Geist Mono, monospace",
          fontSize: "9",
          fill: "#6e6c63"
        },
        "7.5 \xD7 7.5 cm \xB7 8 warstw \xB7 200 szt."
      ),
      /* @__PURE__ */ React.createElement("g", { transform: "translate(22, 108)" }, /* @__PURE__ */ React.createElement("line", { x1: "0", y1: "0", x2: "240", y2: "0", stroke: "#e2dfd4", strokeWidth: "0.5" }), /* @__PURE__ */ React.createElement("text", { y: "14", fontFamily: "Geist, sans-serif", fontWeight: "600", fontSize: "7", fill: "#14130f" }, "PL"), /* @__PURE__ */ React.createElement("text", { y: "26", fontFamily: "Geist, sans-serif", fontSize: "6", fill: "#3b3a35" }, "Sterylne kompresy gazowe z w\u0142\xF3kna bawe\u0142nianego."), /* @__PURE__ */ React.createElement("text", { y: "35", fontFamily: "Geist, sans-serif", fontSize: "6", fill: "#3b3a35" }, "Do opatrywania ran i absorpcji wysi\u0119k\xF3w."), /* @__PURE__ */ React.createElement(
        "text",
        {
          y: "48",
          fontFamily: "Geist, sans-serif",
          fontSize: "6",
          fill: isA ? "#b13a2f" : "#3b3a35",
          fontWeight: isA ? "600" : "400"
        },
        isA ? "\u26A0 Wy\u0142\u0105cznie do u\u017Cytku zewn\u0119trznego. Nie spo\u017Cywa\u0107." : "Nie stosowa\u0107 po up\u0142ywie terminu wa\u017Cno\u015Bci."
      ), /* @__PURE__ */ React.createElement("text", { y: "64", fontFamily: "Geist, sans-serif", fontWeight: "600", fontSize: "7", fill: "#14130f" }, "EN"), /* @__PURE__ */ React.createElement("text", { y: "76", fontFamily: "Geist, sans-serif", fontSize: "6", fill: "#3b3a35" }, "Sterile cotton gauze swabs for wound care."), isA && /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("text", { y: "92", fontFamily: "Geist, sans-serif", fontWeight: "600", fontSize: "7", fill: "#14130f" }, "DE"), /* @__PURE__ */ React.createElement("text", { y: "104", fontFamily: "Geist, sans-serif", fontSize: "6", fill: "#3b3a35" }, "Sterile Baumwoll-Gazetupfer f\xFCr die Wundversorgung."))),
      /* @__PURE__ */ React.createElement("g", { transform: "translate(290, 70)" }, /* @__PURE__ */ React.createElement("rect", { width: "230", height: "150", fill: "#f6f3ea", stroke: "#e2dfd4", strokeWidth: "0.5", rx: "2" }), /* @__PURE__ */ React.createElement("g", { transform: "translate(40, 30)" }, /* @__PURE__ */ React.createElement("rect", { width: "150", height: "90", rx: "6", fill: "#fdfcf7", stroke: "#d1cdbe", strokeWidth: "0.5" }), /* @__PURE__ */ React.createElement("g", { opacity: ".4" }, Array.from({ length: 8 }).map((_, i) => /* @__PURE__ */ React.createElement(
        "line",
        {
          key: i,
          x1: "14",
          y1: 20 + i * 8,
          x2: "136",
          y2: 20 + i * 8,
          stroke: teal,
          strokeWidth: "0.5"
        }
      ))), /* @__PURE__ */ React.createElement(
        "text",
        {
          x: "75",
          y: "56",
          textAnchor: "middle",
          fontFamily: "Geist Mono, monospace",
          fontSize: "6",
          fill: "#a3a097"
        },
        "[ product photo ]"
      ))),
      /* @__PURE__ */ React.createElement("g", { transform: `translate(22, 248)` }, /* @__PURE__ */ React.createElement("line", { x1: "0", y1: "0", x2: W - 44, y2: "0", stroke: "#e2dfd4", strokeWidth: "0.5" }), /* @__PURE__ */ React.createElement(
        "text",
        {
          x: "0",
          y: "14",
          fontFamily: "Geist, sans-serif",
          fontWeight: "600",
          fontSize: "7",
          fill: "#6e6c63",
          letterSpacing: ".06em"
        },
        "LOT"
      ), /* @__PURE__ */ React.createElement("text", { x: "0", y: "26", fontFamily: "Geist Mono, monospace", fontSize: "9", fill: "#14130f" }, isA ? "LOT 240520" : "LOT/24/05/20"), /* @__PURE__ */ React.createElement(
        "text",
        {
          x: "86",
          y: "14",
          fontFamily: "Geist, sans-serif",
          fontWeight: "600",
          fontSize: "7",
          fill: "#6e6c63",
          letterSpacing: ".06em"
        },
        "REF"
      ), /* @__PURE__ */ React.createElement("text", { x: "86", y: "26", fontFamily: "Geist Mono, monospace", fontSize: "9", fill: "#14130f" }, "ZAY-EC-200"), /* @__PURE__ */ React.createElement(
        "text",
        {
          x: "172",
          y: isA ? 14 : 18,
          fontFamily: "Geist, sans-serif",
          fontWeight: "600",
          fontSize: "7",
          fill: "#6e6c63",
          letterSpacing: ".06em"
        },
        "EXP"
      ), /* @__PURE__ */ React.createElement("text", { x: "172", y: isA ? 26 : 32, fontFamily: "Geist Mono, monospace", fontSize: "9", fill: "#14130f" }, "2029-03")),
      /* @__PURE__ */ React.createElement("g", { transform: `translate(${W - 150}, 256)` }, /* @__PURE__ */ React.createElement("rect", { width: "130", height: "44", fill: "#fdfcf7" }), Array.from({ length: 38 }).map((_, i) => {
        const x = 4 + i * 3.2;
        const h = i % 3 === 0 ? 32 : 28;
        return /* @__PURE__ */ React.createElement("rect", { key: i, x, y: "4", width: i % 2 === 0 ? 1.4 : 0.8, height: h, fill: "#14130f" });
      }), /* @__PURE__ */ React.createElement(
        "text",
        {
          x: "65",
          y: "42",
          textAnchor: "middle",
          fontFamily: "Geist Mono, monospace",
          fontSize: "7",
          fill: "#14130f"
        },
        isA ? "5 907996 822690" : "5 907996 822960"
      )),
      /* @__PURE__ */ React.createElement("g", { transform: `translate(${ceX}, 16)` }, /* @__PURE__ */ React.createElement("text", { fontFamily: "Geist, sans-serif", fontWeight: "700", fontSize: "14", fill: "#fdfcf7" }, "CE"), /* @__PURE__ */ React.createElement("text", { x: "0", y: "22", fontFamily: "Geist Mono, monospace", fontSize: "6", fill: "#fdfcf7" }, "2274")),
      /* @__PURE__ */ React.createElement("g", { transform: "translate(290, 230)", fontFamily: "Geist Mono, monospace", fontSize: "8", fill: "#14130f" }, /* @__PURE__ */ React.createElement("g", null, /* @__PURE__ */ React.createElement("circle", { cx: "6", cy: "6", r: "5.5", fill: "none", stroke: "#14130f", strokeWidth: "0.7" }), /* @__PURE__ */ React.createElement("text", { x: "6", y: "9", textAnchor: "middle" }, "R")), /* @__PURE__ */ React.createElement("g", { transform: "translate(22,0)" }, /* @__PURE__ */ React.createElement("rect", { width: "12", height: "12", fill: "none", stroke: "#14130f", strokeWidth: "0.7" }), /* @__PURE__ */ React.createElement("text", { x: "6", y: "9", textAnchor: "middle" }, "2")), /* @__PURE__ */ React.createElement("g", { transform: "translate(44,0)" }, /* @__PURE__ */ React.createElement("circle", { cx: "6", cy: "6", r: "5.5", fill: "none", stroke: "#14130f", strokeWidth: "0.7" }), /* @__PURE__ */ React.createElement("text", { x: "6", y: "9", textAnchor: "middle" }, "\u263C")), /* @__PURE__ */ React.createElement("g", { transform: "translate(66,0)" }, /* @__PURE__ */ React.createElement("rect", { width: "12", height: "12", fill: "none", stroke: "#14130f", strokeWidth: "0.7" }), /* @__PURE__ */ React.createElement("text", { x: "6", y: "9", textAnchor: "middle" }, "\u2195"))),
      /* @__PURE__ */ React.createElement("text", { x: "22", y: "328", fontFamily: "Geist Mono, monospace", fontSize: "6", fill: "#6e6c63" }, isA ? "PL/CA01/0258/26" : "PL/CA01/0258/2026"),
      showGrid && /* @__PURE__ */ React.createElement("g", { opacity: ".15" }, Array.from({ length: Math.floor(W / 20) }).map((_, i) => /* @__PURE__ */ React.createElement("line", { key: "v" + i, x1: i * 20, y1: 0, x2: i * 20, y2: H, stroke: "#2a5c80", strokeWidth: "0.3" })), Array.from({ length: Math.floor(H / 20) }).map((_, i) => /* @__PURE__ */ React.createElement("line", { key: "h" + i, x1: 0, y1: i * 20, x2: W, y2: i * 20, stroke: "#2a5c80", strokeWidth: "0.3" })))
    ), markers.map((m) => /* @__PURE__ */ React.createElement(Marker, { key: m.id, ...m })));
  }
  function Marker({ id, sev = "warn", x, y, w = 24, h = 18, label, side = "right" }) {
    const color = SEV[sev].color;
    const bg = SEV[sev].bg;
    return /* @__PURE__ */ React.createElement("div", { style: {
      position: "absolute",
      left: `${x}%`,
      top: `${y}%`,
      width: `${w}%`,
      height: `${h}%`,
      border: `1.5px solid ${color}`,
      borderRadius: 2,
      background: `${color}10`,
      pointerEvents: "none"
    } }, label && /* @__PURE__ */ React.createElement("div", { style: {
      position: "absolute",
      [side === "right" ? "left" : "right"]: "100%",
      [side === "right" ? "marginLeft" : "marginRight"]: 6,
      top: "50%",
      transform: "translateY(-50%)",
      background: color,
      color: "#fdfcf7",
      fontFamily: "'Geist Mono', monospace",
      fontSize: 9,
      fontWeight: 600,
      padding: "2px 5px",
      borderRadius: 2,
      whiteSpace: "nowrap"
    } }, id));
  }
  function ComparePair({ width = 460, markers = { a: [], b: [] }, showBleed = true }) {
    return /* @__PURE__ */ React.createElement("div", { style: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 } }, /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 } }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 10, color: "var(--ink-3)", letterSpacing: ".08em", textTransform: "uppercase" } }, "A \xB7 v1.4"), /* @__PURE__ */ React.createElement("div", { style: { fontSize: 10, color: "var(--ink-4)", fontFamily: "'Geist Mono', monospace" } }, CMP.fileA.date)), /* @__PURE__ */ React.createElement(PackArtwork, { variant: "a", width, markers: markers.a, showBleed })), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 } }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 10, color: "var(--ink-3)", letterSpacing: ".08em", textTransform: "uppercase" } }, "B \xB7 v1.5"), /* @__PURE__ */ React.createElement("div", { style: { fontSize: 10, color: "var(--ink-4)", fontFamily: "'Geist Mono', monospace" } }, CMP.fileB.date)), /* @__PURE__ */ React.createElement(PackArtwork, { variant: "b", width, markers: markers.b, showBleed })));
  }
  Object.assign(window, { PackArtwork, Marker, ComparePair });
})();

// ── variant-a.jsx ──
(() => {
  function VariantA() {
    return /* @__PURE__ */ React.createElement("div", { style: {
      background: "var(--paper)",
      width: "100%",
      minHeight: "100%",
      padding: "36px 44px",
      fontFamily: "'Geist', sans-serif",
      color: "var(--ink)",
      fontSize: 12,
      lineHeight: 1.45
    } }, /* @__PURE__ */ React.createElement(ARHeader, null), /* @__PURE__ */ React.createElement("div", { style: { height: 24 } }), /* @__PURE__ */ React.createElement(ARTopGrid, null), /* @__PURE__ */ React.createElement("div", { style: { height: 28 } }), /* @__PURE__ */ React.createElement(ARModules, null), /* @__PURE__ */ React.createElement("div", { style: { height: 28 } }), /* @__PURE__ */ React.createElement(ARArtworkOverview, null), /* @__PURE__ */ React.createElement("div", { style: { height: 28 } }), /* @__PURE__ */ React.createElement(ARCriticalSection, null), /* @__PURE__ */ React.createElement("div", { style: { height: 24 } }), /* @__PURE__ */ React.createElement(ARWarningSection, null), /* @__PURE__ */ React.createElement("div", { style: { height: 24 } }), /* @__PURE__ */ React.createElement(ARFooter, null));
  }
  function ARHeader() {
    return /* @__PURE__ */ React.createElement("header", null, /* @__PURE__ */ React.createElement("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "flex-end", gap: 16 } }, /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("div", { style: {
      fontFamily: "'Newsreader', serif",
      fontStyle: "italic",
      fontSize: 13,
      color: "var(--ink-3)",
      letterSpacing: ".01em"
    } }, "ACME \xB7 ArtCompare v1.0"), /* @__PURE__ */ React.createElement("h1", { style: {
      margin: "6px 0 0",
      fontFamily: "'Newsreader', serif",
      fontWeight: 500,
      fontSize: 38,
      letterSpacing: "-.015em",
      lineHeight: 1.05
    } }, "Raport por\xF3wnania ", /* @__PURE__ */ React.createElement("span", { style: { fontStyle: "italic" } }, "artwork\xF3w")), /* @__PURE__ */ React.createElement("div", { style: {
      marginTop: 6,
      fontSize: 12,
      color: "var(--ink-2)"
    } }, CMP.product, " \xA0\xB7\xA0 ", /* @__PURE__ */ React.createElement("span", { className: "mono", style: { color: "var(--ink-3)" } }, CMP.sku))), /* @__PURE__ */ React.createElement("div", { style: { textAlign: "right", minWidth: 230 } }, /* @__PURE__ */ React.createElement(AcmeWordmark, null), /* @__PURE__ */ React.createElement("div", { style: {
      marginTop: 10,
      display: "inline-flex",
      gap: 10,
      fontFamily: "'Geist Mono', monospace",
      fontSize: 11,
      color: "var(--ink-3)"
    } }, /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("span", { style: { color: "var(--ink-4)" } }, "NR"), "\xA0", CMP.no), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("span", { style: { color: "var(--ink-4)" } }, "\xB7")), /* @__PURE__ */ React.createElement("div", null, CMP.date, " ", CMP.time)))), /* @__PURE__ */ React.createElement("div", { style: { height: 16 } }), /* @__PURE__ */ React.createElement("div", { style: { height: 1, background: "var(--rule-3)" } }), /* @__PURE__ */ React.createElement("div", { style: { height: 4 } }), /* @__PURE__ */ React.createElement("div", { style: { height: 0.5, background: "var(--rule-3)" } }));
  }
  function ARTopGrid() {
    const cellStyle = {
      background: "var(--paper-2)",
      padding: "14px 16px",
      borderRadius: 2
    };
    const Verdict = ({ count, label, color, bg }) => /* @__PURE__ */ React.createElement("div", { style: {
      flex: 1,
      padding: "12px 10px",
      background: bg,
      borderRadius: 2,
      textAlign: "center"
    } }, /* @__PURE__ */ React.createElement("div", { style: {
      fontFamily: "'Geist Mono', monospace",
      fontSize: 28,
      fontWeight: 600,
      color,
      lineHeight: 1,
      fontVariantNumeric: "tabular-nums"
    } }, count), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 4, fontSize: 10, color, letterSpacing: ".06em", textTransform: "uppercase" } }, label));
    return /* @__PURE__ */ React.createElement("section", { style: { display: "grid", gridTemplateColumns: "1fr 1fr 1.2fr", gap: 12 } }, /* @__PURE__ */ React.createElement(DocCell, { label: "Dokument A \xB7 \u017Ar\xF3d\u0142o", file: CMP.fileA }), /* @__PURE__ */ React.createElement(DocCell, { label: "Dokument B \xB7 por\xF3wnywany", file: CMP.fileB, highlight: true }), /* @__PURE__ */ React.createElement("div", { style: cellStyle }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 10, color: "var(--ink-3)", letterSpacing: ".08em", textTransform: "uppercase" } }, "Werdykt automatyczny"), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 10, display: "flex", gap: 6 } }, /* @__PURE__ */ React.createElement(Verdict, { count: CMP.summary.critical, label: "Krytyczne", color: "var(--critical)", bg: "var(--critical-bg)" }), /* @__PURE__ */ React.createElement(Verdict, { count: CMP.summary.warning, label: "Ostrze\u017Cenia", color: "var(--warn)", bg: "var(--warn-bg)" }), /* @__PURE__ */ React.createElement(Verdict, { count: CMP.summary.info, label: "Info", color: "var(--info)", bg: "var(--info-bg)" }), /* @__PURE__ */ React.createElement(Verdict, { count: CMP.summary.ok, label: "Zgodnych", color: "var(--ok)", bg: "var(--ok-bg)" })), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 12, display: "flex", alignItems: "center", gap: 10 } }, /* @__PURE__ */ React.createElement("div", { style: {
      padding: "5px 9px",
      background: "var(--critical)",
      color: "var(--paper)",
      fontFamily: "'Geist Mono', monospace",
      fontSize: 10,
      fontWeight: 600,
      letterSpacing: ".08em"
    } }, "NIE DOPUSZCZA\u0106 DO DRUKU"), /* @__PURE__ */ React.createElement("div", { style: { fontSize: 11, color: "var(--ink-3)" } }, "3 rozbie\u017Cno\u015Bci blokuj\u0105ce"))));
  }
  function DocCell({ label, file, highlight }) {
    return /* @__PURE__ */ React.createElement("div", { style: {
      background: highlight ? "var(--paper-3)" : "var(--paper-2)",
      padding: "14px 16px",
      borderRadius: 2,
      borderLeft: highlight ? "2px solid #14130f" : "2px solid transparent"
    } }, /* @__PURE__ */ React.createElement("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center" } }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 10, color: "var(--ink-3)", letterSpacing: ".08em", textTransform: "uppercase" } }, label), /* @__PURE__ */ React.createElement("div", { style: {
      fontFamily: "'Geist Mono', monospace",
      fontSize: 10,
      color: "var(--ink-2)",
      background: "var(--paper-3)",
      padding: "2px 6px",
      borderRadius: 2
    } }, file.version)), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 8, fontFamily: "'Geist Mono', monospace", fontSize: 12, color: "var(--ink)", wordBreak: "break-all" } }, file.name), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 10, display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px 12px" } }, /* @__PURE__ */ React.createElement(KV, { k: "Data", v: file.date }), /* @__PURE__ */ React.createElement(KV, { k: "Autor", v: file.author }), /* @__PURE__ */ React.createElement(KV, { k: "Strony", v: `${file.pages}`, mono: true }), /* @__PURE__ */ React.createElement(KV, { k: "Rozmiar", v: file.size, mono: true }), /* @__PURE__ */ React.createElement(KV, { k: "Format", v: file.dim, mono: true }), /* @__PURE__ */ React.createElement(KV, { k: "Spad", v: file.bleed, mono: true }), /* @__PURE__ */ React.createElement(KV, { k: "Kolory", v: file.colors }), /* @__PURE__ */ React.createElement(KV, { k: "Fonty", v: file.fonts })));
  }
  function ARModules() {
    return /* @__PURE__ */ React.createElement("section", null, /* @__PURE__ */ React.createElement(SectionHead, { n: "01", title: "Podsumowanie modu\u0142\xF3w", hint: "8 modu\u0142\xF3w detekcji \xB7 34 sprawdzane pola" }), /* @__PURE__ */ React.createElement("table", { style: { width: "100%", borderCollapse: "collapse", fontSize: 12 } }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", { style: { textAlign: "left", color: "var(--ink-3)" } }, /* @__PURE__ */ React.createElement("th", { style: th(36) }), /* @__PURE__ */ React.createElement("th", { style: th() }, "Modu\u0142"), /* @__PURE__ */ React.createElement("th", { style: th(110) }, "Status"), /* @__PURE__ */ React.createElement("th", { style: th(70) }, "Krytyczne"), /* @__PURE__ */ React.createElement("th", { style: th(80) }, "Ostrze\u017Cenia"), /* @__PURE__ */ React.createElement("th", { style: th(60) }, "OK"), /* @__PURE__ */ React.createElement("th", { style: th() }, "Komentarz"))), /* @__PURE__ */ React.createElement("tbody", null, CMP.modules.map((m, i) => /* @__PURE__ */ React.createElement("tr", { key: m.id, style: { borderTop: "0.5px solid var(--rule)" } }, /* @__PURE__ */ React.createElement("td", { style: td() }, /* @__PURE__ */ React.createElement("span", { style: {
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      width: 22,
      height: 22,
      borderRadius: 2,
      background: "var(--paper-2)",
      fontFamily: "'Geist Mono', monospace",
      fontSize: 11,
      color: "var(--ink-2)"
    } }, CATEGORIES[m.id]?.icon || "\xB7")), /* @__PURE__ */ React.createElement("td", { style: td() }, /* @__PURE__ */ React.createElement("div", { style: { fontWeight: 500 } }, m.name)), /* @__PURE__ */ React.createElement("td", { style: td() }, /* @__PURE__ */ React.createElement(SevTag, { sev: m.status === "fail" ? "crit" : m.status === "warn" ? "warn" : m.status === "info" ? "info" : "ok" })), /* @__PURE__ */ React.createElement("td", { style: { ...td(), fontFamily: "'Geist Mono', monospace", color: m.crit ? "var(--critical)" : "var(--ink-4)", fontWeight: m.crit ? 600 : 400 } }, m.crit), /* @__PURE__ */ React.createElement("td", { style: { ...td(), fontFamily: "'Geist Mono', monospace", color: m.warn ? "var(--warn)" : "var(--ink-4)", fontWeight: m.warn ? 600 : 400 } }, m.warn), /* @__PURE__ */ React.createElement("td", { style: { ...td(), fontFamily: "'Geist Mono', monospace", color: "var(--ok)" } }, m.ok), /* @__PURE__ */ React.createElement("td", { style: { ...td(), color: "var(--ink-2)" } }, m.note))))));
  }
  const th = (w) => ({
    padding: "8px 8px 8px 0",
    fontSize: 10,
    fontWeight: 500,
    letterSpacing: ".06em",
    textTransform: "uppercase",
    borderBottom: "0.5px solid var(--rule-3)",
    width: w,
    color: "var(--ink-3)"
  });
  const td = () => ({ padding: "10px 8px 10px 0", verticalAlign: "top" });
  function SectionHead({ n, title, hint }) {
    return /* @__PURE__ */ React.createElement("div", { style: { display: "flex", alignItems: "flex-end", gap: 12, marginBottom: 10 } }, /* @__PURE__ */ React.createElement("div", { style: {
      fontFamily: "'Geist Mono', monospace",
      fontSize: 10,
      color: "var(--ink-3)",
      letterSpacing: ".08em"
    } }, n), /* @__PURE__ */ React.createElement("h2", { style: {
      margin: 0,
      fontFamily: "'Newsreader', serif",
      fontWeight: 500,
      fontSize: 20,
      letterSpacing: "-.01em"
    } }, title), hint && /* @__PURE__ */ React.createElement("div", { style: {
      flex: 1,
      paddingBottom: 4,
      paddingLeft: 8,
      borderBottom: "0.5px dotted var(--rule-2)",
      fontSize: 11,
      color: "var(--ink-3)",
      alignSelf: "baseline"
    } }, hint));
  }
  function ARArtworkOverview() {
    const aMarkers = [
      { id: "D-05", sev: "crit", x: 3, y: 4, w: 18, h: 14, label: "D-05" },
      { id: "D-02", sev: "crit", x: 4, y: 45, w: 38, h: 8, label: "D-02", side: "right" },
      { id: "D-03", sev: "crit", x: 4, y: 73, w: 38, h: 10, label: "D-03", side: "right" }
    ];
    const bMarkers = [
      { id: "D-01", sev: "crit", x: 72, y: 75, w: 24, h: 17, label: "D-01" },
      { id: "D-04", sev: "crit", x: 4, y: 75, w: 18, h: 8, label: "D-04", side: "right" },
      { id: "D-06", sev: "warn", x: 85, y: 3, w: 12, h: 11, label: "D-06", side: "left" },
      { id: "D-10", sev: "warn", x: 30, y: 78, w: 12, h: 8, label: "D-10", side: "right" }
    ];
    return /* @__PURE__ */ React.createElement("section", null, /* @__PURE__ */ React.createElement(SectionHead, { n: "02", title: "Podgl\u0105d artwork\xF3w", hint: "Diff wizualny \u2014 krytyczne i wybrane ostrze\u017Cenia" }), /* @__PURE__ */ React.createElement(ComparePair, { width: "100%", markers: { a: aMarkers, b: bMarkers } }), /* @__PURE__ */ React.createElement("div", { style: {
      marginTop: 12,
      display: "flex",
      gap: 14,
      fontSize: 10,
      color: "var(--ink-3)",
      fontFamily: "'Geist Mono', monospace"
    } }, /* @__PURE__ */ React.createElement(LegendDot, { color: "var(--critical)", label: "Krytyczne (blokuj\u0105ce + niezgodne)" }), /* @__PURE__ */ React.createElement(LegendDot, { color: "var(--warn)", label: "Ostrze\u017Cenia (przesuni\u0119cia, kolor, czcionki)" }), /* @__PURE__ */ React.createElement(LegendDot, { color: "var(--info)", label: "Informacyjne (metadane)" }), /* @__PURE__ */ React.createElement("div", { style: { marginLeft: "auto" } }, "spad / bleed \xB7 linia kropkowana")));
  }
  function LegendDot({ color, label }) {
    return /* @__PURE__ */ React.createElement("div", { style: { display: "inline-flex", alignItems: "center", gap: 6 } }, /* @__PURE__ */ React.createElement("span", { style: { width: 8, height: 8, borderRadius: 2, background: color, display: "inline-block" } }), /* @__PURE__ */ React.createElement("span", { style: { textTransform: "uppercase", letterSpacing: ".06em" } }, label));
  }
  function ARCriticalSection() {
    const crits = CMP.diffs.filter((d) => d.sev === "crit");
    return /* @__PURE__ */ React.createElement("section", null, /* @__PURE__ */ React.createElement(SectionHead, { n: "03", title: "Krytyczne rozbie\u017Cno\u015Bci", hint: `${crits.length} pozycji \xB7 ${crits.filter((c) => c.blocker).length} blokuj\u0105cych druk` }), /* @__PURE__ */ React.createElement("div", { style: { display: "flex", flexDirection: "column" } }, crits.map((d, i) => /* @__PURE__ */ React.createElement(DiffRow, { key: d.id, d, idx: i, dense: false }))));
  }
  function ARWarningSection() {
    const warns = CMP.diffs.filter((d) => d.sev === "warn");
    return /* @__PURE__ */ React.createElement("section", null, /* @__PURE__ */ React.createElement(SectionHead, { n: "04", title: "Ostrze\u017Cenia", hint: `${warns.length} pozycji do przegl\u0105du` }), /* @__PURE__ */ React.createElement("table", { style: { width: "100%", borderCollapse: "collapse", fontSize: 12 } }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: th(46) }, "ID"), /* @__PURE__ */ React.createElement("th", { style: th(90) }, "Kategoria"), /* @__PURE__ */ React.createElement("th", { style: th() }, "Pole"), /* @__PURE__ */ React.createElement("th", { style: th() }, "Warto\u015B\u0107 A"), /* @__PURE__ */ React.createElement("th", { style: th() }, "Warto\u015B\u0107 B"), /* @__PURE__ */ React.createElement("th", { style: th() }, "Komentarz"))), /* @__PURE__ */ React.createElement("tbody", null, warns.map((d) => /* @__PURE__ */ React.createElement("tr", { key: d.id, style: { borderTop: "0.5px solid var(--rule)" } }, /* @__PURE__ */ React.createElement("td", { style: { ...td(), fontFamily: "'Geist Mono', monospace", color: "var(--ink-3)" } }, d.id), /* @__PURE__ */ React.createElement("td", { style: td() }, /* @__PURE__ */ React.createElement("span", { style: {
      fontSize: 10,
      padding: "2px 6px",
      background: "var(--paper-2)",
      color: "var(--ink-2)",
      letterSpacing: ".04em",
      textTransform: "uppercase",
      borderRadius: 2
    } }, CATEGORIES[d.cat]?.label)), /* @__PURE__ */ React.createElement("td", { style: { ...td(), fontWeight: 500 } }, d.field), /* @__PURE__ */ React.createElement("td", { style: { ...td(), fontFamily: "'Geist Mono', monospace", color: "var(--ink-2)" } }, d.a), /* @__PURE__ */ React.createElement("td", { style: { ...td(), fontFamily: "'Geist Mono', monospace", color: "var(--warn)" } }, d.b), /* @__PURE__ */ React.createElement("td", { style: { ...td(), color: "var(--ink-2)" } }, d.note))))));
  }
  function DiffRow({ d, idx }) {
    return /* @__PURE__ */ React.createElement("div", { style: {
      padding: "14px 0",
      borderTop: idx === 0 ? "0.5px solid var(--rule-3)" : "0.5px solid var(--rule)",
      display: "grid",
      gridTemplateColumns: "60px 1fr 1fr 1fr",
      gap: 16,
      alignItems: "start"
    } }, /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("div", { style: {
      fontFamily: "'Geist Mono', monospace",
      fontSize: 12,
      fontWeight: 600,
      color: "var(--critical)"
    } }, d.id), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 6 } }, /* @__PURE__ */ React.createElement(SevTag, { sev: d.sev })), d.blocker && /* @__PURE__ */ React.createElement("div", { style: {
      marginTop: 6,
      fontSize: 9,
      padding: "2px 5px",
      background: "var(--critical)",
      color: "var(--paper)",
      display: "inline-block",
      letterSpacing: ".08em",
      fontFamily: "'Geist Mono', monospace"
    } }, "BLOKER")), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("div", { style: {
      fontSize: 11,
      color: "var(--ink-3)",
      letterSpacing: ".06em",
      textTransform: "uppercase"
    } }, CATEGORIES[d.cat]?.label, " \xB7 ", d.field), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 4, fontSize: 13, color: "var(--ink)", lineHeight: 1.4 } }, d.note), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 8, fontSize: 11, color: "var(--ink-3)" } }, /* @__PURE__ */ React.createElement("span", { style: { fontFamily: "'Geist Mono', monospace" } }, "\u21B3 "), d.where)), /* @__PURE__ */ React.createElement(ValueCell, { label: "A \xB7 v1.4", value: d.a, tone: "neutral" }), /* @__PURE__ */ React.createElement(ValueCell, { label: "B \xB7 v1.5", value: d.b, tone: "diff" }));
  }
  function ValueCell({ label, value, tone }) {
    const isDiff = tone === "diff";
    return /* @__PURE__ */ React.createElement("div", { style: {
      background: isDiff ? "var(--critical-bg)" : "var(--paper-2)",
      borderLeft: isDiff ? "2px solid var(--critical)" : "2px solid var(--ink-4)",
      padding: "10px 12px",
      borderRadius: 0
    } }, /* @__PURE__ */ React.createElement("div", { style: {
      fontSize: 10,
      color: isDiff ? "var(--critical)" : "var(--ink-3)",
      letterSpacing: ".06em",
      textTransform: "uppercase",
      fontWeight: 500
    } }, label), /* @__PURE__ */ React.createElement("div", { style: {
      marginTop: 6,
      fontFamily: "'Geist Mono', monospace",
      fontSize: 12,
      color: "var(--ink)",
      wordBreak: "break-word",
      lineHeight: 1.4
    } }, value || "\u2014"));
  }
  function ARFooter() {
    return /* @__PURE__ */ React.createElement("footer", { style: {
      marginTop: 24,
      paddingTop: 14,
      borderTop: "0.5px solid var(--rule-3)",
      display: "flex",
      justifyContent: "space-between",
      fontFamily: "'Geist Mono', monospace",
      fontSize: 10,
      color: "var(--ink-3)",
      letterSpacing: ".04em"
    } }, /* @__PURE__ */ React.createElement("div", null, "ArtCompare v1.0 \xB7 ACME sp. z o.o."), /* @__PURE__ */ React.createElement("div", null, "Wygenerowano: ", CMP.date, " ", CMP.time, " \xB7 por\xF3wnanie ", CMP.no, " \xB7 str. 1/1"));
  }
  Object.assign(window, { VariantA });
})();

// ── variant-b.jsx ──
(() => {
  const vbDims = { W: 1440, H: 900 };
  function VariantB() {
    const [mode, setMode] = React.useState("split");
    const [selected, setSelected] = React.useState("D-01");
    const [filter, setFilter] = React.useState("all");
    const diffs = CMP.diffs.filter((d) => filter === "all" ? true : d.sev === filter);
    const sel = CMP.diffs.find((d) => d.id === selected);
    return /* @__PURE__ */ React.createElement("div", { style: {
      width: vbDims.W,
      height: vbDims.H,
      background: "var(--paper)",
      fontFamily: "'Geist', sans-serif",
      color: "var(--ink)",
      fontSize: 13,
      display: "flex",
      flexDirection: "column",
      overflow: "hidden"
    } }, /* @__PURE__ */ React.createElement(BTopbar, null), /* @__PURE__ */ React.createElement("div", { style: { flex: 1, display: "flex", minHeight: 0 } }, /* @__PURE__ */ React.createElement(BLeftRail, { selected }), /* @__PURE__ */ React.createElement(BViewer, { mode, setMode, selected: sel }), /* @__PURE__ */ React.createElement(
      BRightPanel,
      {
        diffs,
        selected,
        setSelected,
        filter,
        setFilter,
        sel
      }
    )), /* @__PURE__ */ React.createElement(BStatusBar, null));
  }
  function BTopbar() {
    return /* @__PURE__ */ React.createElement("header", { style: {
      height: 52,
      flexShrink: 0,
      borderBottom: "0.5px solid var(--rule-2)",
      background: "var(--paper-2)",
      display: "flex",
      alignItems: "center",
      padding: "0 18px",
      gap: 18
    } }, /* @__PURE__ */ React.createElement("div", { style: { display: "flex", alignItems: "center", gap: 10 } }, /* @__PURE__ */ React.createElement(AcmeWordmark, { size: 12 }), /* @__PURE__ */ React.createElement("span", { style: { color: "var(--ink-4)" } }, "\u203A"), /* @__PURE__ */ React.createElement("span", { style: { fontWeight: 500 } }, "ArtCompare"), /* @__PURE__ */ React.createElement("span", { style: {
      fontSize: 10,
      padding: "2px 6px",
      background: "var(--paper-2)",
      color: "var(--ink-3)",
      letterSpacing: ".06em",
      fontFamily: "'Geist Mono', monospace",
      borderRadius: 2
    } }, "v1.0 BETA")), /* @__PURE__ */ React.createElement("div", { style: { height: 18, width: 1, background: "var(--rule-2)" } }), /* @__PURE__ */ React.createElement("div", { style: { display: "flex", alignItems: "center", gap: 8, fontFamily: "'Geist Mono', monospace", fontSize: 11 } }, /* @__PURE__ */ React.createElement("span", { style: { color: "var(--ink-3)" } }, "RUN"), /* @__PURE__ */ React.createElement("span", null, CMP.no), /* @__PURE__ */ React.createElement("span", { style: { color: "var(--ink-4)" } }, "/"), /* @__PURE__ */ React.createElement("span", null, CMP.sku), /* @__PURE__ */ React.createElement("span", { style: { color: "var(--ink-4)" } }, "\xB7"), /* @__PURE__ */ React.createElement("span", { style: { color: "var(--ink-3)" } }, CMP.date, " ", CMP.time)), /* @__PURE__ */ React.createElement("div", { style: { flex: 1 } }), /* @__PURE__ */ React.createElement("div", { style: {
      display: "inline-flex",
      alignItems: "center",
      gap: 6,
      padding: "5px 10px",
      background: "var(--critical-bg)",
      color: "var(--critical)",
      fontFamily: "'Geist Mono', monospace",
      fontSize: 11,
      fontWeight: 600,
      borderRadius: 2,
      letterSpacing: ".04em"
    } }, /* @__PURE__ */ React.createElement("span", { style: { width: 6, height: 6, borderRadius: "50%", background: "var(--critical)" } }), "NIE DOPUSZCZA\u0106 DO DRUKU"), /* @__PURE__ */ React.createElement("div", { style: { display: "flex", gap: 6, alignItems: "center" } }, /* @__PURE__ */ React.createElement(Avatar, { initials: "AK", tone: "ink" }), /* @__PURE__ */ React.createElement(Avatar, { initials: "MN", tone: "warn" }), /* @__PURE__ */ React.createElement(Avatar, { initials: "JZ", tone: "ok" }), /* @__PURE__ */ React.createElement("div", { style: { fontSize: 11, color: "var(--ink-3)", marginLeft: 4 } }, "3 online")), /* @__PURE__ */ React.createElement("div", { style: { height: 18, width: 1, background: "var(--rule-2)", marginLeft: 8 } }), /* @__PURE__ */ React.createElement(BButton, { variant: "ghost" }, "Eksport"), /* @__PURE__ */ React.createElement(BButton, { variant: "dark" }, "Wy\u015Blij do dostawcy"));
  }
  function Avatar({ initials, tone }) {
    const colors = {
      ink: { bg: "var(--rule-3)", fg: "var(--ink)" },
      warn: { bg: "var(--warn)", fg: "var(--paper)" },
      ok: { bg: "var(--ok)", fg: "var(--paper)" }
    }[tone];
    return /* @__PURE__ */ React.createElement("div", { style: {
      width: 26,
      height: 26,
      borderRadius: "50%",
      background: colors.bg,
      color: colors.fg,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontSize: 10,
      fontWeight: 600,
      fontFamily: "'Geist Mono', monospace"
    } }, initials);
  }
  function BButton({ variant = "ghost", children, onClick, active }) {
    const styles = {
      ghost: { background: "transparent", color: "var(--ink-2)", border: "0.5px solid var(--rule-2)" },
      dark: { background: "var(--accent)", color: "var(--paper)", border: "0.5px solid var(--accent)" },
      pill: { background: "transparent", color: "var(--ink-2)", border: "0.5px solid var(--rule-2)" }
    }[variant];
    return /* @__PURE__ */ React.createElement("button", { onClick, style: {
      ...styles,
      padding: "6px 12px",
      fontSize: 11,
      fontFamily: "'Geist', sans-serif",
      fontWeight: 500,
      letterSpacing: ".02em",
      borderRadius: 2,
      cursor: "pointer",
      ...active ? { background: "var(--accent)", color: "var(--paper)", borderColor: "var(--accent)" } : {}
    } }, children);
  }
  function BLeftRail({ selected }) {
    return /* @__PURE__ */ React.createElement("aside", { style: {
      width: 240,
      flexShrink: 0,
      borderRight: "0.5px solid var(--rule-2)",
      background: "var(--paper-2)",
      display: "flex",
      flexDirection: "column"
    } }, /* @__PURE__ */ React.createElement("div", { style: { padding: "14px 16px 8px" } }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 10, color: "var(--ink-3)", letterSpacing: ".08em", textTransform: "uppercase" } }, "Bie\u017C\u0105cy run"), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 6, fontWeight: 500, fontSize: 13, lineHeight: 1.3 } }, CMP.product), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 4, fontSize: 11, color: "var(--ink-3)", fontFamily: "'Geist Mono', monospace" } }, CMP.sku)), /* @__PURE__ */ React.createElement("div", { style: { padding: "4px 12px" } }, /* @__PURE__ */ React.createElement(FileNode, { active: true, label: "v1.4 \xB7 \u017Ar\xF3d\u0142o", sub: CMP.fileA.date, icon: "A", tone: "ink-2" }), /* @__PURE__ */ React.createElement(FileNode, { active: true, label: "v1.5 \xB7 por\xF3wnywany", sub: CMP.fileB.date, icon: "B", tone: "warn", highlight: true })), /* @__PURE__ */ React.createElement("div", { style: { padding: "18px 16px 6px" } }, /* @__PURE__ */ React.createElement("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between" } }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 10, color: "var(--ink-3)", letterSpacing: ".08em", textTransform: "uppercase" } }, "Historia por\xF3wna\u0144"), /* @__PURE__ */ React.createElement("div", { style: { fontSize: 10, color: "var(--ink-4)" } }, "8"))), /* @__PURE__ */ React.createElement("div", { style: { padding: "2px 12px", overflowY: "auto", flex: 1 } }, /* @__PURE__ */ React.createElement(HistRow, { id: "#08", sku: "ZAY-easyCARE(200)", date: "20.05", status: "crit", current: true }), /* @__PURE__ */ React.createElement(HistRow, { id: "#07", sku: "ZAY-easyCARE(100)", date: "14.05", status: "warn" }), /* @__PURE__ */ React.createElement(HistRow, { id: "#06", sku: "ZAY-COMFIT(50)", date: "11.05", status: "ok" }), /* @__PURE__ */ React.createElement(HistRow, { id: "#05", sku: "ZAY-MEDISORB", date: "08.05", status: "ok" }), /* @__PURE__ */ React.createElement(HistRow, { id: "#04", sku: "ZAY-easyCARE(500)", date: "02.05", status: "warn" }), /* @__PURE__ */ React.createElement(HistRow, { id: "#03", sku: "ZAY-DERMO-PRO", date: "28.04", status: "crit" }), /* @__PURE__ */ React.createElement(HistRow, { id: "#02", sku: "ZAY-COMFIT(200)", date: "22.04", status: "ok" }), /* @__PURE__ */ React.createElement(HistRow, { id: "#01", sku: "ZAY-easyCARE(50)", date: "18.04", status: "ok" })), /* @__PURE__ */ React.createElement("div", { style: {
      padding: "12px 16px",
      borderTop: "0.5px solid var(--rule-2)",
      background: "var(--paper-2)"
    } }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 10, color: "var(--ink-3)", letterSpacing: ".08em", textTransform: "uppercase", marginBottom: 6 } }, "Regu\u0142y QA"), /* @__PURE__ */ React.createElement("div", { style: { fontSize: 11, color: "var(--ink-2)", lineHeight: 1.6 } }, "MDR \xB7 PN-EN 980 \xB7 GS1 GTIN", /* @__PURE__ */ React.createElement("br", null), "Pantone \u0394E \u2264 2.0", /* @__PURE__ */ React.createElement("br", null), "Min. typografia 7 pt")));
  }
  function FileNode({ label, sub, icon, tone, highlight, active }) {
    return /* @__PURE__ */ React.createElement("div", { style: {
      display: "flex",
      alignItems: "center",
      gap: 10,
      padding: "8px 10px",
      borderRadius: 3,
      background: highlight ? "var(--paper-3)" : "transparent",
      marginBottom: 2
    } }, /* @__PURE__ */ React.createElement("div", { style: {
      width: 22,
      height: 28,
      borderRadius: 2,
      background: tone === "warn" ? "var(--warn)" : "var(--rule-3)",
      color: tone === "warn" ? "var(--paper)" : "var(--ink)",
      fontSize: 10,
      fontFamily: "'Geist Mono', monospace",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontWeight: 600
    } }, icon), /* @__PURE__ */ React.createElement("div", { style: { flex: 1, minWidth: 0 } }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 12, fontWeight: 500 } }, label), /* @__PURE__ */ React.createElement("div", { style: { fontSize: 10, color: "var(--ink-3)", fontFamily: "'Geist Mono', monospace" } }, sub)));
  }
  function HistRow({ id, sku, date, status, current }) {
    const color = status === "crit" ? "var(--critical)" : status === "warn" ? "var(--warn)" : "var(--ok)";
    return /* @__PURE__ */ React.createElement("div", { style: {
      display: "flex",
      alignItems: "center",
      gap: 8,
      padding: "6px 8px",
      borderRadius: 2,
      background: current ? "var(--paper-2)" : "transparent",
      marginBottom: 1,
      cursor: "pointer"
    } }, /* @__PURE__ */ React.createElement("span", { style: { width: 6, height: 6, borderRadius: "50%", background: color, flexShrink: 0 } }), /* @__PURE__ */ React.createElement("span", { style: { fontFamily: "'Geist Mono', monospace", fontSize: 10, color: "var(--ink-3)", minWidth: 24 } }, id), /* @__PURE__ */ React.createElement("span", { style: { flex: 1, fontSize: 11, color: "var(--ink-2)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" } }, sku), /* @__PURE__ */ React.createElement("span", { style: { fontFamily: "'Geist Mono', monospace", fontSize: 10, color: "var(--ink-4)" } }, date));
  }
  function BViewer({ mode, setMode, selected }) {
    const aMarkers = [
      { id: "D-05", sev: "crit", x: 3, y: 4, w: 18, h: 14, label: "D-05" },
      { id: "D-02", sev: "crit", x: 4, y: 45, w: 38, h: 8, label: "D-02", side: "right" },
      { id: "D-03", sev: "crit", x: 4, y: 73, w: 38, h: 10, label: "D-03", side: "right" }
    ];
    const bMarkers = [
      { id: "D-01", sev: "crit", x: 72, y: 75, w: 24, h: 17, label: "D-01" },
      { id: "D-04", sev: "crit", x: 4, y: 75, w: 18, h: 8, label: "D-04", side: "right" },
      { id: "D-06", sev: "warn", x: 85, y: 3, w: 12, h: 11, label: "D-06", side: "left" },
      { id: "D-10", sev: "warn", x: 30, y: 78, w: 12, h: 8, label: "D-10", side: "right" }
    ];
    return /* @__PURE__ */ React.createElement("main", { style: {
      flex: 1,
      minWidth: 0,
      display: "flex",
      flexDirection: "column",
      background: "var(--paper-2)"
    } }, /* @__PURE__ */ React.createElement("div", { style: {
      height: 44,
      flexShrink: 0,
      background: "var(--paper-2)",
      borderBottom: "0.5px solid var(--rule-2)",
      display: "flex",
      alignItems: "center",
      padding: "0 16px",
      gap: 10
    } }, /* @__PURE__ */ React.createElement("div", { style: { display: "flex", gap: 2, padding: 2, background: "var(--paper-2)", borderRadius: 3 } }, [
      ["split", "Side-by-side"],
      ["overlay", "Overlay"],
      ["onion", "Onion-skin"]
    ].map(([k, label]) => /* @__PURE__ */ React.createElement("button", { key: k, onClick: () => setMode(k), style: {
      padding: "5px 10px",
      fontSize: 11,
      border: "none",
      cursor: "pointer",
      background: mode === k ? "var(--paper-3)" : "transparent",
      color: mode === k ? "var(--ink)" : "var(--ink-3)",
      fontWeight: mode === k ? 500 : 400,
      borderRadius: 2,
      boxShadow: mode === k ? "0 1px 2px rgba(0,0,0,.06)" : "none"
    } }, label))), /* @__PURE__ */ React.createElement("div", { style: { height: 18, width: 1, background: "var(--rule-2)" } }), /* @__PURE__ */ React.createElement("div", { style: { display: "flex", gap: 4, alignItems: "center" } }, /* @__PURE__ */ React.createElement(Toggle, { label: "Spady", on: true }), /* @__PURE__ */ React.createElement(Toggle, { label: "Siatka" }), /* @__PURE__ */ React.createElement(Toggle, { label: "Linijka", on: true }), /* @__PURE__ */ React.createElement(Toggle, { label: "Etykiety", on: true })), /* @__PURE__ */ React.createElement("div", { style: { flex: 1 } }), /* @__PURE__ */ React.createElement("div", { style: { fontFamily: "'Geist Mono', monospace", fontSize: 11, color: "var(--ink-3)", display: "flex", gap: 12 } }, /* @__PURE__ */ React.createElement("span", null, "218 \xD7 142 mm"), /* @__PURE__ */ React.createElement("span", null, "\xB7"), /* @__PURE__ */ React.createElement("span", null, "120% zoom"), /* @__PURE__ */ React.createElement("span", null, "\xB7"), /* @__PURE__ */ React.createElement("span", null, "x 154.3 mm  y 88.7 mm"))), /* @__PURE__ */ React.createElement("div", { style: { flex: 1, padding: 18, overflow: "auto", position: "relative" } }, mode === "split" && /* @__PURE__ */ React.createElement("div", { style: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 } }, /* @__PURE__ */ React.createElement(ViewerPane, { label: "A \xB7 v1.4 \xB7 \u017Ar\xF3d\u0142o", variant: "a", markers: aMarkers, stamp: "ZATWIERDZONE", stampColor: "var(--ok)" }), /* @__PURE__ */ React.createElement(ViewerPane, { label: "B \xB7 v1.5 \xB7 por\xF3wnywany", variant: "b", markers: bMarkers, stamp: "WYMAGA POPRAWY", stampColor: "var(--critical)" })), mode === "overlay" && /* @__PURE__ */ React.createElement(OverlayViewer, null), mode === "onion" && /* @__PURE__ */ React.createElement(OnionViewer, null), selected && /* @__PURE__ */ React.createElement("div", { style: {
      marginTop: 18,
      background: "var(--paper-3)",
      border: "0.5px solid var(--rule-2)",
      borderRadius: 2,
      padding: 14,
      display: "grid",
      gridTemplateColumns: "auto 1fr 1fr",
      gap: 18,
      alignItems: "start"
    } }, /* @__PURE__ */ React.createElement("div", { style: {
      padding: "10px 14px",
      background: SEV[selected.sev].bg,
      borderLeft: `2px solid ${SEV[selected.sev].color}`
    } }, /* @__PURE__ */ React.createElement("div", { style: { fontFamily: "'Geist Mono', monospace", fontSize: 18, fontWeight: 600, color: SEV[selected.sev].color } }, selected.id), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 4 } }, /* @__PURE__ */ React.createElement(SevTag, { sev: selected.sev }))), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 10, color: "var(--ink-3)", letterSpacing: ".08em", textTransform: "uppercase" } }, CATEGORIES[selected.cat]?.label, " \xB7 ", selected.field), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 4, fontSize: 13, color: "var(--ink)", lineHeight: 1.4 } }, selected.note), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 8, fontSize: 11, color: "var(--ink-3)", fontFamily: "'Geist Mono', monospace" } }, "\u21B3 ", selected.where)), /* @__PURE__ */ React.createElement("div", { style: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 } }, /* @__PURE__ */ React.createElement(ValueChip, { label: "A \xB7 v1.4", value: selected.a }), /* @__PURE__ */ React.createElement(ValueChip, { label: "B \xB7 v1.5", value: selected.b, diff: true })))));
  }
  function Toggle({ label, on }) {
    return /* @__PURE__ */ React.createElement("button", { style: {
      padding: "5px 9px",
      fontSize: 11,
      cursor: "pointer",
      background: on ? "var(--paper-2)" : "transparent",
      color: on ? "var(--ink)" : "var(--ink-3)",
      border: "0.5px solid " + (on ? "var(--rule-2)" : "transparent"),
      borderRadius: 2,
      display: "inline-flex",
      alignItems: "center",
      gap: 5
    } }, /* @__PURE__ */ React.createElement("span", { style: {
      width: 8,
      height: 8,
      borderRadius: 2,
      border: "1px solid " + (on ? "var(--ink-2)" : "var(--rule-2)"),
      background: on ? "var(--ink-2)" : "transparent"
    } }), label);
  }
  function ViewerPane({ label, variant, markers, stamp, stampColor }) {
    return /* @__PURE__ */ React.createElement("div", { style: {
      position: "relative",
      background: "var(--paper-3)",
      padding: 12,
      borderRadius: 2,
      border: "0.5px solid var(--rule-2)"
    } }, /* @__PURE__ */ React.createElement("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 } }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 11, color: "var(--ink-2)", letterSpacing: ".04em", fontWeight: 500 } }, label), /* @__PURE__ */ React.createElement("div", { style: {
      padding: "2px 6px",
      fontSize: 9,
      fontFamily: "'Geist Mono', monospace",
      fontWeight: 600,
      letterSpacing: ".08em",
      color: stampColor,
      border: "0.5px solid " + stampColor
    } }, stamp)), /* @__PURE__ */ React.createElement(PackArtwork, { variant, width: "100%", markers }));
  }
  function OverlayViewer() {
    return /* @__PURE__ */ React.createElement("div", { style: {
      position: "relative",
      background: "var(--paper-3)",
      padding: 12,
      borderRadius: 2,
      border: "0.5px solid var(--rule-2)",
      maxWidth: 760,
      margin: "0 auto"
    } }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 11, color: "var(--ink-3)", marginBottom: 8 } }, "Przeci\u0105gnij lini\u0119 aby por\xF3wna\u0107 A \u2194 B"), /* @__PURE__ */ React.createElement("div", { style: { position: "relative" } }, /* @__PURE__ */ React.createElement(PackArtwork, { variant: "a", width: "100%" }), /* @__PURE__ */ React.createElement("div", { style: {
      position: "absolute",
      inset: 0,
      width: "45%",
      overflow: "hidden"
    } }, /* @__PURE__ */ React.createElement("div", { style: { width: "222.2%" } }, /* @__PURE__ */ React.createElement(PackArtwork, { variant: "b", width: "100%" }))), /* @__PURE__ */ React.createElement("div", { style: {
      position: "absolute",
      left: "45%",
      top: 0,
      bottom: 0,
      width: 2,
      background: "var(--accent)"
    } }, /* @__PURE__ */ React.createElement("div", { style: {
      position: "absolute",
      top: "50%",
      left: "50%",
      transform: "translate(-50%, -50%)",
      background: "var(--accent)",
      color: "var(--paper)",
      width: 28,
      height: 28,
      borderRadius: "50%",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontSize: 14
    } }, "\u2194"))));
  }
  function OnionViewer() {
    return /* @__PURE__ */ React.createElement("div", { style: {
      position: "relative",
      background: "var(--paper-3)",
      padding: 12,
      borderRadius: 2,
      border: "0.5px solid var(--rule-2)",
      maxWidth: 760,
      margin: "0 auto"
    } }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 11, color: "var(--ink-3)", marginBottom: 8, display: "flex", justifyContent: "space-between" } }, /* @__PURE__ */ React.createElement("span", null, "Onion-skin \xB7 A pod, B na wierzchu (60% opacity)"), /* @__PURE__ */ React.createElement("span", { style: { fontFamily: "'Geist Mono', monospace" } }, "opacity \u2501\u2501\u2501\u2501\u2501\u2501\u2501\u25CF\u2501\u2501\u2501 60%")), /* @__PURE__ */ React.createElement("div", { style: { position: "relative" } }, /* @__PURE__ */ React.createElement(PackArtwork, { variant: "a", width: "100%" }), /* @__PURE__ */ React.createElement("div", { style: { position: "absolute", inset: 0, opacity: 0.6 } }, /* @__PURE__ */ React.createElement(PackArtwork, { variant: "b", width: "100%" }))));
  }
  function ValueChip({ label, value, diff }) {
    return /* @__PURE__ */ React.createElement("div", { style: {
      padding: "8px 10px",
      borderRadius: 2,
      background: diff ? "var(--critical-bg)" : "var(--paper-2)",
      borderLeft: `2px solid ${diff ? "var(--critical)" : "var(--ink-4)"}`
    } }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 9, color: diff ? "var(--critical)" : "var(--ink-3)", letterSpacing: ".06em", textTransform: "uppercase" } }, label), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 3, fontFamily: "'Geist Mono', monospace", fontSize: 11 } }, value || "\u2014"));
  }
  function BRightPanel({ diffs, selected, setSelected, filter, setFilter, sel }) {
    return /* @__PURE__ */ React.createElement("aside", { style: {
      width: 360,
      flexShrink: 0,
      borderLeft: "0.5px solid var(--rule-2)",
      background: "var(--paper-2)",
      display: "flex",
      flexDirection: "column"
    } }, /* @__PURE__ */ React.createElement("div", { style: { padding: "14px 16px 8px" } }, /* @__PURE__ */ React.createElement("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center" } }, /* @__PURE__ */ React.createElement("div", { style: { fontWeight: 500, fontSize: 13 } }, "Rozbie\u017Cno\u015Bci"), /* @__PURE__ */ React.createElement("div", { style: { fontFamily: "'Geist Mono', monospace", fontSize: 11, color: "var(--ink-3)" } }, diffs.length, " / ", CMP.diffs.length))), /* @__PURE__ */ React.createElement("div", { style: { padding: "0 12px 8px", display: "flex", gap: 4 } }, [
      ["all", "Wszystkie", CMP.diffs.length, "var(--ink-2)"],
      ["crit", "Krytyczne", CMP.summary.critical, "var(--critical)"],
      ["warn", "Ostrze\u017Cenia", CMP.summary.warning, "var(--warn)"],
      ["info", "Info", CMP.summary.info, "var(--info)"]
    ].map(([k, lbl, n, c]) => /* @__PURE__ */ React.createElement("button", { key: k, onClick: () => setFilter(k), style: {
      flex: 1,
      padding: "6px 4px",
      fontSize: 10,
      cursor: "pointer",
      background: filter === k ? c : "transparent",
      color: filter === k ? "var(--paper)" : c,
      border: "0.5px solid " + (filter === k ? c : "var(--rule-2)"),
      borderRadius: 2,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: 2,
      fontFamily: "'Geist', sans-serif"
    } }, /* @__PURE__ */ React.createElement("span", { style: { fontFamily: "'Geist Mono', monospace", fontWeight: 600, fontSize: 12 } }, n), /* @__PURE__ */ React.createElement("span", { style: { fontSize: 9, letterSpacing: ".04em" } }, lbl)))), /* @__PURE__ */ React.createElement("div", { style: { flex: 1, overflowY: "auto", padding: "0 6px 12px" } }, diffs.map((d) => /* @__PURE__ */ React.createElement(DiffListItem, { key: d.id, d, active: d.id === selected, onClick: () => setSelected(d.id) }))), sel && /* @__PURE__ */ React.createElement("div", { style: {
      padding: "14px 16px",
      borderTop: "0.5px solid var(--rule-2)",
      background: "var(--paper-2)"
    } }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 10, color: "var(--ink-3)", letterSpacing: ".08em", textTransform: "uppercase", marginBottom: 6 } }, "Dzia\u0142ania dla ", sel.id), /* @__PURE__ */ React.createElement("div", { style: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 } }, /* @__PURE__ */ React.createElement(BButton, { variant: "ghost" }, "Akceptuj A"), /* @__PURE__ */ React.createElement(BButton, { variant: "ghost" }, "Akceptuj B"), /* @__PURE__ */ React.createElement(BButton, { variant: "ghost" }, "Komentuj"), /* @__PURE__ */ React.createElement(BButton, { variant: "dark" }, "Eskaluj do QA")), /* @__PURE__ */ React.createElement("div", { style: {
      marginTop: 10,
      padding: "8px 10px",
      background: "var(--paper-3)",
      borderRadius: 2,
      border: "0.5px solid var(--rule-2)",
      fontSize: 11,
      color: "var(--ink-2)",
      lineHeight: 1.4
    } }, /* @__PURE__ */ React.createElement("span", { style: { color: "var(--ink-3)", fontFamily: "'Geist Mono', monospace", fontSize: 10 } }, "JZ \xB7 17:31"), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 2 } }, "Sprawdzi\u0107 z dostawc\u0105 \u2014 podejrzewam pomy\u0142k\u0119 przy generowaniu kodu."))));
  }
  function DiffListItem({ d, active, onClick }) {
    return /* @__PURE__ */ React.createElement("button", { onClick, style: {
      width: "100%",
      textAlign: "left",
      cursor: "pointer",
      padding: "10px 10px",
      marginBottom: 2,
      background: active ? "var(--paper-3)" : "transparent",
      border: "none",
      borderLeft: active ? "2px solid var(--accent)" : "2px solid transparent",
      borderRadius: 0,
      display: "flex",
      gap: 10,
      alignItems: "flex-start",
      fontFamily: "inherit"
    } }, /* @__PURE__ */ React.createElement("span", { style: {
      width: 6,
      height: 6,
      borderRadius: "50%",
      background: SEV[d.sev].color,
      marginTop: 5,
      flexShrink: 0
    } }), /* @__PURE__ */ React.createElement("div", { style: { flex: 1, minWidth: 0 } }, /* @__PURE__ */ React.createElement("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 6 } }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 12, fontWeight: 500, color: "var(--ink)" } }, d.field), /* @__PURE__ */ React.createElement("div", { style: { fontFamily: "'Geist Mono', monospace", fontSize: 10, color: "var(--ink-3)" } }, d.id)), /* @__PURE__ */ React.createElement("div", { style: { fontSize: 10, color: "var(--ink-3)", letterSpacing: ".04em", marginTop: 2 } }, CATEGORIES[d.cat]?.label.toUpperCase(), " ", d.blocker ? " \xB7 BLOKER" : ""), /* @__PURE__ */ React.createElement("div", { style: {
      marginTop: 6,
      fontSize: 11,
      color: "var(--ink-2)",
      lineHeight: 1.35,
      overflow: "hidden",
      textOverflow: "ellipsis",
      display: "-webkit-box",
      WebkitLineClamp: 2,
      WebkitBoxOrient: "vertical"
    } }, d.note)));
  }
  function BStatusBar() {
    return /* @__PURE__ */ React.createElement("footer", { style: {
      height: 26,
      flexShrink: 0,
      borderTop: "0.5px solid var(--rule-2)",
      background: "var(--paper-2)",
      display: "flex",
      alignItems: "center",
      padding: "0 16px",
      gap: 14,
      fontFamily: "'Geist Mono', monospace",
      fontSize: 10,
      color: "var(--ink-3)"
    } }, /* @__PURE__ */ React.createElement("span", null, "ANALIZA: 14.2 s"), /* @__PURE__ */ React.createElement("span", null, "\xB7"), /* @__PURE__ */ React.createElement("span", null, "RENDERERA: cairo 1.18"), /* @__PURE__ */ React.createElement("span", null, "\xB7"), /* @__PURE__ */ React.createElement("span", null, "OCR: tesseract 5.4 \xB7 PL/EN/DE"), /* @__PURE__ */ React.createElement("span", null, "\xB7"), /* @__PURE__ */ React.createElement("span", null, "REGU\u0141Y: 142 aktywne"), /* @__PURE__ */ React.createElement("span", { style: { flex: 1 } }), /* @__PURE__ */ React.createElement("span", { style: { color: "var(--ok)" } }, "\u25CF po\u0142\u0105czono z PIM"), /* @__PURE__ */ React.createElement("span", null, "\xB7"), /* @__PURE__ */ React.createElement("span", null, "autozapis 17:42"));
  }
  Object.assign(window, { VariantB });
})();

// ── variant-c.jsx ──
(() => {
  const vcDims = { W: 1280, H: 900 };
  const LANES = [
    { id: "todo", title: "Do przegl\u0105du", color: "var(--ink-3)", bg: "var(--paper-2)" },
    { id: "doing", title: "W trakcie", color: "var(--info)", bg: "var(--info-bg)" },
    { id: "supplier", title: "Do poprawy u dostawcy", color: "var(--warn)", bg: "var(--warn-bg)" },
    { id: "done", title: "Zaakceptowane", color: "var(--ok)", bg: "var(--ok-bg)" }
  ];
  const LANE_OF = {
    "D-01": "supplier",
    "D-02": "supplier",
    "D-03": "supplier",
    "D-04": "doing",
    "D-05": "doing",
    "D-06": "todo",
    "D-07": "todo",
    "D-08": "todo",
    "D-09": "doing",
    "D-10": "todo",
    "D-11": "todo",
    "D-12": "done",
    "D-13": "doing",
    "D-14": "done",
    "D-15": "done",
    "D-16": "done",
    "D-17": "done"
  };
  const OWNERS = {
    "D-01": { name: "M. Nowak", role: "dostawca", tone: "warn" },
    "D-02": { name: "J. Zieli\u0144ska", role: "QA", tone: "ok" },
    "D-03": { name: "P. Wojtas", role: "Reg.", tone: "ink" },
    "D-04": { name: "M. Nowak", role: "dostawca", tone: "warn" },
    "D-05": { name: "A. Kowalska", role: "Brand", tone: "ink" },
    "D-06": { name: "A. Kowalska", role: "Brand", tone: "ink" },
    "D-07": { name: "J. Zieli\u0144ska", role: "QA", tone: "ok" },
    "D-08": { name: "T. B\u0105k", role: "DTP", tone: "ink" },
    "D-09": { name: "A. Kowalska", role: "Brand", tone: "ink" },
    "D-10": { name: "T. B\u0105k", role: "DTP", tone: "ink" },
    "D-11": { name: "T. B\u0105k", role: "DTP", tone: "ink" },
    "D-12": { name: "T. B\u0105k", role: "DTP", tone: "ink" },
    "D-13": { name: "P. Wojtas", role: "Reg.", tone: "ink" },
    "D-14": { name: "J. Zieli\u0144ska", role: "QA", tone: "ok" },
    "D-15": { name: "\u2014", role: "auto", tone: "ink" },
    "D-16": { name: "\u2014", role: "auto", tone: "ink" },
    "D-17": { name: "\u2014", role: "auto", tone: "ink" }
  };
  const COMMENTS = {
    "D-01": 2,
    "D-02": 4,
    "D-03": 1,
    "D-05": 1,
    "D-09": 2
  };
  function VariantC() {
    return /* @__PURE__ */ React.createElement("div", { style: {
      width: vcDims.W,
      minHeight: vcDims.H,
      background: "var(--paper-2)",
      fontFamily: "'Geist', sans-serif",
      color: "var(--ink)",
      fontSize: 13,
      display: "flex",
      flexDirection: "column"
    } }, /* @__PURE__ */ React.createElement(CHeader, null), /* @__PURE__ */ React.createElement(CHero, null), /* @__PURE__ */ React.createElement(CBoard, null));
  }
  function CHeader() {
    return /* @__PURE__ */ React.createElement("header", { style: {
      padding: "16px 28px",
      background: "var(--paper-2)",
      borderBottom: "0.5px solid var(--rule-2)",
      display: "flex",
      alignItems: "center",
      gap: 14
    } }, /* @__PURE__ */ React.createElement(AcmeWordmark, { size: 13 }), /* @__PURE__ */ React.createElement("span", { style: { color: "var(--ink-4)" } }, "/"), /* @__PURE__ */ React.createElement("span", { style: { fontWeight: 500 } }, "ArtCompare"), /* @__PURE__ */ React.createElement("span", { style: { color: "var(--ink-4)" } }, "/"), /* @__PURE__ */ React.createElement("span", { style: { fontFamily: "'Geist Mono', monospace", color: "var(--ink-3)", fontSize: 12 } }, CMP.no), /* @__PURE__ */ React.createElement("span", { style: { fontWeight: 500 } }, "\xB7 ", CMP.product), /* @__PURE__ */ React.createElement("div", { style: { flex: 1 } }), /* @__PURE__ */ React.createElement("div", { style: { display: "flex", alignItems: "center", gap: 8, fontSize: 11, color: "var(--ink-3)" } }, /* @__PURE__ */ React.createElement("span", null, "Otwarte"), /* @__PURE__ */ React.createElement("span", { style: { fontFamily: "'Geist Mono', monospace", color: "var(--ink)", fontWeight: 500 } }, CMP.summary.critical + CMP.summary.warning + CMP.summary.info - 5), /* @__PURE__ */ React.createElement("span", null, "\xB7 Zaakceptowane"), /* @__PURE__ */ React.createElement("span", { style: { fontFamily: "'Geist Mono', monospace", color: "var(--ok)", fontWeight: 500 } }, "5"), /* @__PURE__ */ React.createElement("span", null, "\xB7 Czas przegl\u0105du"), /* @__PURE__ */ React.createElement("span", { style: { fontFamily: "'Geist Mono', monospace", color: "var(--ink)", fontWeight: 500 } }, "2 dni 4 h")), /* @__PURE__ */ React.createElement("button", { style: {
      padding: "7px 14px",
      background: "var(--accent)",
      color: "var(--paper)",
      border: "none",
      cursor: "pointer",
      borderRadius: 2,
      fontFamily: "'Geist', sans-serif",
      fontSize: 12,
      fontWeight: 500
    } }, "Zaakceptuj wszystko + ode\u015Blij"));
  }
  function CHero() {
    return /* @__PURE__ */ React.createElement("section", { style: {
      padding: "24px 28px",
      background: "var(--paper-tint)",
      borderBottom: "0.5px solid var(--rule-2)",
      display: "grid",
      gridTemplateColumns: "1fr 380px",
      gap: 32,
      alignItems: "start"
    } }, /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 10, color: "var(--ink-3)", letterSpacing: ".1em", textTransform: "uppercase" } }, "Por\xF3wnanie wersji"), /* @__PURE__ */ React.createElement("h1", { style: {
      margin: "8px 0 4px",
      fontFamily: "'Newsreader', serif",
      fontWeight: 500,
      fontSize: 30,
      letterSpacing: "-.01em"
    } }, "v1.4 ", /* @__PURE__ */ React.createElement("span", { style: { color: "var(--ink-4)", fontSize: 24 } }, "\u2192"), " v1.5", /* @__PURE__ */ React.createElement("span", { style: { fontStyle: "italic", color: "var(--ink-3)", marginLeft: 12, fontSize: 18 } }, "rev. dostawcy")), /* @__PURE__ */ React.createElement("div", { style: { fontFamily: "'Geist Mono', monospace", fontSize: 11, color: "var(--ink-3)", marginTop: 4 } }, CMP.sku, " \xB7 EAN ", CMP.ean, " \xB7 ", CMP.date), /* @__PURE__ */ React.createElement("div", { style: {
      marginTop: 18,
      display: "grid",
      gridTemplateColumns: "repeat(4, 1fr)",
      gap: 10
    } }, /* @__PURE__ */ React.createElement(Kpi, { n: CMP.summary.critical, label: "Krytyczne", sub: "3 blokuj\u0105ce", color: "var(--critical)" }), /* @__PURE__ */ React.createElement(Kpi, { n: CMP.summary.warning, label: "Ostrze\u017Cenia", sub: "0 blokuj\u0105ce", color: "var(--warn)" }), /* @__PURE__ */ React.createElement(Kpi, { n: CMP.summary.ok, label: "Zgodne", sub: "auto-OK", color: "var(--ok)" }), /* @__PURE__ */ React.createElement(Kpi, { n: `${Math.round(CMP.summary.ok / (CMP.summary.ok + CMP.summary.critical + CMP.summary.warning + CMP.summary.info) * 100)}%`, label: "Zgodno\u015B\u0107", sub: "aktualna", color: "var(--ink)" }))), /* @__PURE__ */ React.createElement("div", { style: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 } }, /* @__PURE__ */ React.createElement(ThumbCard, { variant: "a", label: "A \xB7 v1.4", date: CMP.fileA.date }), /* @__PURE__ */ React.createElement(ThumbCard, { variant: "b", label: "B \xB7 v1.5", date: CMP.fileB.date, flagged: true })));
  }
  function Kpi({ n, label, sub, color }) {
    return /* @__PURE__ */ React.createElement("div", { style: {
      padding: "14px 16px",
      background: "var(--paper-2)",
      borderTop: `2px solid ${color}`,
      borderRadius: 0
    } }, /* @__PURE__ */ React.createElement("div", { style: {
      fontFamily: "'Geist Mono', monospace",
      fontSize: 32,
      fontWeight: 500,
      color,
      lineHeight: 1,
      fontVariantNumeric: "tabular-nums"
    } }, n), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 6, fontSize: 12, fontWeight: 500, color: "var(--ink)" } }, label), /* @__PURE__ */ React.createElement("div", { style: { fontSize: 10, color: "var(--ink-3)", marginTop: 1 } }, sub));
  }
  function ThumbCard({ variant, label, date, flagged }) {
    return /* @__PURE__ */ React.createElement("div", { style: {
      position: "relative",
      background: "var(--paper-3)",
      borderRadius: 2,
      border: "0.5px solid var(--rule-2)",
      overflow: "hidden"
    } }, /* @__PURE__ */ React.createElement("div", { style: { padding: "6px 10px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "0.5px solid var(--rule-2)" } }, /* @__PURE__ */ React.createElement("span", { style: { fontSize: 10, fontFamily: "'Geist Mono', monospace", color: "var(--ink-2)" } }, label), /* @__PURE__ */ React.createElement("span", { style: { fontSize: 10, color: "var(--ink-4)", fontFamily: "'Geist Mono', monospace" } }, date)), /* @__PURE__ */ React.createElement("div", { style: { padding: 6 } }, /* @__PURE__ */ React.createElement(PackArtwork, { variant, width: "100%", showBleed: false })), flagged && /* @__PURE__ */ React.createElement("div", { style: {
      position: "absolute",
      top: 28,
      right: 6,
      padding: "2px 6px",
      background: "var(--critical)",
      color: "var(--paper)",
      fontFamily: "'Geist Mono', monospace",
      fontSize: 9,
      letterSpacing: ".06em"
    } }, "5 KRYT."));
  }
  function CBoard() {
    return /* @__PURE__ */ React.createElement("div", { style: {
      padding: "20px 28px 28px",
      flex: 1,
      display: "grid",
      gridTemplateColumns: "repeat(4, 1fr)",
      gap: 14
    } }, LANES.map((lane) => /* @__PURE__ */ React.createElement(
      BoardColumn,
      {
        key: lane.id,
        lane,
        diffs: CMP.diffs.filter((d) => LANE_OF[d.id] === lane.id)
      }
    )));
  }
  function BoardColumn({ lane, diffs }) {
    return /* @__PURE__ */ React.createElement("div", { style: { display: "flex", flexDirection: "column", minWidth: 0 } }, /* @__PURE__ */ React.createElement("div", { style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "8px 10px",
      marginBottom: 10,
      borderTop: `2px solid ${lane.color}`,
      background: "var(--paper-2)"
    } }, /* @__PURE__ */ React.createElement("div", { style: { display: "flex", alignItems: "center", gap: 8 } }, /* @__PURE__ */ React.createElement("span", { style: {
      width: 6,
      height: 6,
      borderRadius: "50%",
      background: lane.color
    } }), /* @__PURE__ */ React.createElement("span", { style: { fontSize: 12, fontWeight: 500 } }, lane.title)), /* @__PURE__ */ React.createElement("span", { style: {
      fontFamily: "'Geist Mono', monospace",
      fontSize: 11,
      color: lane.color,
      fontWeight: 500
    } }, diffs.length)), /* @__PURE__ */ React.createElement("div", { style: { display: "flex", flexDirection: "column", gap: 8 } }, diffs.map((d) => /* @__PURE__ */ React.createElement(DiffCard, { key: d.id, d })), diffs.length === 0 && /* @__PURE__ */ React.createElement("div", { style: {
      padding: "18px",
      fontSize: 11,
      color: "var(--ink-4)",
      textAlign: "center",
      fontStyle: "italic",
      border: "0.5px dashed var(--rule-2)",
      borderRadius: 2
    } }, "brak pozycji")));
  }
  function DiffCard({ d }) {
    const owner = OWNERS[d.id];
    const comments = COMMENTS[d.id] || 0;
    return /* @__PURE__ */ React.createElement("article", { style: {
      background: "var(--paper-3)",
      borderRadius: 2,
      border: "0.5px solid var(--rule-2)",
      overflow: "hidden"
    } }, /* @__PURE__ */ React.createElement("div", { style: { height: 3, background: SEV[d.sev].color } }), /* @__PURE__ */ React.createElement("div", { style: { padding: "10px 12px" } }, /* @__PURE__ */ React.createElement("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center" } }, /* @__PURE__ */ React.createElement("span", { style: {
      fontFamily: "'Geist Mono', monospace",
      fontSize: 10,
      color: "var(--ink-3)",
      letterSpacing: ".04em"
    } }, d.id, " \xB7 ", CATEGORIES[d.cat]?.label.toUpperCase()), d.blocker && /* @__PURE__ */ React.createElement("span", { style: {
      padding: "1px 4px",
      fontFamily: "'Geist Mono', monospace",
      fontSize: 8,
      background: "var(--critical)",
      color: "var(--paper)",
      letterSpacing: ".08em"
    } }, "BLOKER")), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 6, fontWeight: 500, fontSize: 13, lineHeight: 1.3 } }, d.field), /* @__PURE__ */ React.createElement("div", { style: {
      marginTop: 4,
      fontSize: 11,
      color: "var(--ink-2)",
      lineHeight: 1.4,
      overflow: "hidden",
      textOverflow: "ellipsis",
      display: "-webkit-box",
      WebkitLineClamp: 2,
      WebkitBoxOrient: "vertical"
    } }, d.note), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 8, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4 } }, /* @__PURE__ */ React.createElement(MiniValue, { label: "A", value: d.a }), /* @__PURE__ */ React.createElement(MiniValue, { label: "B", value: d.b, diff: true })), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 10, display: "flex", alignItems: "center", gap: 8 } }, /* @__PURE__ */ React.createElement(Avatar2, { initials: owner.name.split(" ").map((s) => s[0]).join(""), tone: owner.tone }), /* @__PURE__ */ React.createElement("div", { style: { flex: 1, minWidth: 0 } }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 11, color: "var(--ink-2)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" } }, owner.name), /* @__PURE__ */ React.createElement("div", { style: { fontSize: 9, color: "var(--ink-4)", letterSpacing: ".04em" } }, owner.role.toUpperCase())), comments > 0 && /* @__PURE__ */ React.createElement("div", { style: {
      display: "inline-flex",
      alignItems: "center",
      gap: 3,
      fontFamily: "'Geist Mono', monospace",
      fontSize: 10,
      color: "var(--ink-3)"
    } }, /* @__PURE__ */ React.createElement("span", null, "\u275D"), comments), /* @__PURE__ */ React.createElement("div", { style: {
      fontFamily: "'Geist Mono', monospace",
      fontSize: 10,
      color: "var(--ink-4)",
      whiteSpace: "nowrap"
    } }, d.where.split(",")[0]))));
  }
  function MiniValue({ label, value, diff }) {
    return /* @__PURE__ */ React.createElement("div", { style: {
      padding: "5px 7px",
      borderRadius: 2,
      background: diff ? "var(--critical-bg)" : "var(--paper-2)"
    } }, /* @__PURE__ */ React.createElement("div", { style: {
      fontSize: 8,
      color: diff ? "var(--critical)" : "var(--ink-4)",
      letterSpacing: ".08em",
      fontFamily: "'Geist Mono', monospace"
    } }, label), /* @__PURE__ */ React.createElement("div", { style: {
      marginTop: 1,
      fontFamily: "'Geist Mono', monospace",
      fontSize: 10,
      color: "var(--ink)",
      lineHeight: 1.25,
      overflow: "hidden",
      textOverflow: "ellipsis",
      whiteSpace: "nowrap"
    } }, value || "\u2014"));
  }
  function Avatar2({ initials, tone }) {
    const colors = {
      ink: { bg: "var(--rule-3)", fg: "var(--ink)" },
      warn: { bg: "var(--warn)", fg: "var(--paper)" },
      ok: { bg: "var(--ok)", fg: "var(--paper)" }
    }[tone];
    return /* @__PURE__ */ React.createElement("div", { style: {
      width: 22,
      height: 22,
      borderRadius: "50%",
      background: colors.bg,
      color: colors.fg,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      flexShrink: 0,
      fontSize: 9,
      fontWeight: 600,
      fontFamily: "'Geist Mono', monospace"
    } }, initials);
  }
  Object.assign(window, { VariantC });
})();

// ── variant-d.jsx ──
(() => {
  function VariantD() {
    const [side, setSide] = React.useState("B");
    const pins = [
      { id: "D-01", sev: "crit", x: 84, y: 80, n: 1 },
      { id: "D-02", sev: "crit", x: 23, y: 47, n: 2 },
      { id: "D-03", sev: "crit", x: 23, y: 77, n: 3 },
      { id: "D-04", sev: "crit", x: 11, y: 80, n: 4 },
      { id: "D-05", sev: "crit", x: 9, y: 11, n: 5 },
      { id: "D-06", sev: "warn", x: 91, y: 9, n: 6 },
      { id: "D-09", sev: "warn", x: 50, y: 5, n: 7 },
      { id: "D-10", sev: "warn", x: 36, y: 82, n: 8 }
    ];
    return /* @__PURE__ */ React.createElement("div", { style: {
      width: 1280,
      minHeight: 1100,
      background: "var(--paper)",
      fontFamily: "'Geist', sans-serif",
      color: "var(--ink)",
      display: "flex",
      flexDirection: "column"
    } }, /* @__PURE__ */ React.createElement(DTopBar, { side, setSide }), /* @__PURE__ */ React.createElement("div", { style: {
      flex: 1,
      display: "grid",
      gridTemplateColumns: "1fr 320px",
      gap: 0
    } }, /* @__PURE__ */ React.createElement(DCanvas, { side, pins }), /* @__PURE__ */ React.createElement(DPinsList, { pins })));
  }
  function DTopBar({ side, setSide }) {
    return /* @__PURE__ */ React.createElement("div", { style: {
      padding: "14px 28px",
      borderBottom: "0.5px solid var(--rule-2)",
      background: "var(--paper-2)",
      display: "flex",
      alignItems: "center",
      gap: 16
    } }, /* @__PURE__ */ React.createElement("div", { style: { display: "flex", alignItems: "center", gap: 10 } }, /* @__PURE__ */ React.createElement(AcmeWordmark, { size: 12 }), /* @__PURE__ */ React.createElement("span", { style: { color: "var(--ink-4)" } }, "/"), /* @__PURE__ */ React.createElement("span", { style: { fontSize: 12, fontWeight: 500 } }, "Annotated review")), /* @__PURE__ */ React.createElement("span", { style: {
      fontFamily: "'Geist Mono', monospace",
      fontSize: 11,
      color: "var(--ink-3)"
    } }, CMP.sku, " \xB7 por\xF3wnanie ", CMP.no), /* @__PURE__ */ React.createElement("div", { style: { flex: 1 } }), /* @__PURE__ */ React.createElement("div", { style: { display: "flex", gap: 2, padding: 2, background: "var(--paper)", borderRadius: 4, border: "0.5px solid var(--rule-2)" } }, ["A", "B", "diff", "overlay"].map((s) => /* @__PURE__ */ React.createElement("button", { key: s, onClick: () => setSide(s), style: {
      padding: "5px 12px",
      fontSize: 11,
      cursor: "pointer",
      background: side === s ? "var(--paper-3)" : "transparent",
      color: side === s ? "var(--ink)" : "var(--ink-3)",
      border: "none",
      borderRadius: 3,
      fontFamily: "'Geist', sans-serif",
      fontWeight: side === s ? 500 : 400
    } }, s === "A" ? "A \xB7 v1.4" : s === "B" ? "B \xB7 v1.5" : s === "diff" ? "tylko r\xF3\u017Cnice" : "overlay"))), /* @__PURE__ */ React.createElement("div", { style: { display: "flex", alignItems: "center", gap: 8, padding: "5px 10px", background: "var(--paper)", borderRadius: 3, border: "0.5px solid var(--rule-2)" } }, /* @__PURE__ */ React.createElement("span", { style: { fontFamily: "'Geist Mono', monospace", fontSize: 11, color: "var(--ink-3)" } }, "zoom"), /* @__PURE__ */ React.createElement("span", { style: { fontFamily: "'Geist Mono', monospace", fontSize: 11, color: "var(--ink)" } }, "185%"), /* @__PURE__ */ React.createElement("span", { style: { color: "var(--rule-3)" } }, "\xB7"), /* @__PURE__ */ React.createElement("span", { style: { fontFamily: "'Geist Mono', monospace", fontSize: 11, color: "var(--ink-3)" } }, "200 DPI")), /* @__PURE__ */ React.createElement("button", { style: {
      padding: "7px 14px",
      background: "var(--accent)",
      color: "var(--paper)",
      border: "none",
      cursor: "pointer",
      borderRadius: 3,
      fontSize: 12,
      fontWeight: 500
    } }, "Rozwi\u0105\u017C wszystkie (", pinCount("warn"), ")"));
  }
  function pinCount(sev) {
    return CMP.diffs.filter((d) => d.sev === sev).length;
  }
  function DCanvas({ side, pins }) {
    const showA = side === "A" || side === "overlay";
    const showB = side === "B" || side === "overlay" || side === "diff";
    return /* @__PURE__ */ React.createElement("div", { style: {
      position: "relative",
      padding: 36,
      background: "var(--paper)",
      // grid pattern background
      backgroundImage: "radial-gradient(circle at 1px 1px, rgba(255,255,255,.04) 1px, transparent 0)",
      backgroundSize: "24px 24px",
      overflow: "hidden"
    } }, /* @__PURE__ */ React.createElement("div", { style: {
      position: "relative",
      maxWidth: 780,
      margin: "0 auto",
      boxShadow: "0 30px 80px rgba(0,0,0,.4), 0 0 0 1px var(--rule-2)"
    } }, showA && /* @__PURE__ */ React.createElement("div", { style: { position: showB && side === "overlay" ? "absolute" : "relative", inset: 0, opacity: side === "overlay" ? 0.45 : 1 } }, /* @__PURE__ */ React.createElement(PackArtwork, { variant: "a", width: "100%", showBleed: true })), showB && side !== "overlay" && /* @__PURE__ */ React.createElement(PackArtwork, { variant: "b", width: "100%", showBleed: true }), showB && side === "overlay" && /* @__PURE__ */ React.createElement("div", { style: { opacity: 0.7 } }, /* @__PURE__ */ React.createElement(PackArtwork, { variant: "b", width: "100%", showBleed: true })), /* @__PURE__ */ React.createElement("div", { style: { position: "absolute", inset: 0, pointerEvents: "none" } }, pins.map((p) => /* @__PURE__ */ React.createElement(Pin, { key: p.id, ...p })))), /* @__PURE__ */ React.createElement("div", { style: {
      position: "absolute",
      bottom: 16,
      left: 28,
      display: "flex",
      gap: 12,
      fontFamily: "'Geist Mono', monospace",
      fontSize: 10,
      color: "var(--ink-3)"
    } }, /* @__PURE__ */ React.createElement(Legend, { color: "var(--critical)", label: "krytyczne" }), /* @__PURE__ */ React.createElement(Legend, { color: "var(--warn)", label: "ostrze\u017Cenia" }), /* @__PURE__ */ React.createElement(Legend, { color: "var(--info)", label: "info" }), /* @__PURE__ */ React.createElement("span", { style: { marginLeft: 6 } }, "\xB7 218 \xD7 142 mm @ 200 DPI")), /* @__PURE__ */ React.createElement("div", { style: {
      position: "absolute",
      bottom: 16,
      right: 28,
      display: "flex",
      alignItems: "center",
      gap: 8,
      fontFamily: "'Geist Mono', monospace",
      fontSize: 10,
      color: "var(--ink-3)"
    } }, /* @__PURE__ */ React.createElement("span", null, "0"), /* @__PURE__ */ React.createElement("span", { style: { display: "inline-block", width: 80, height: 1, background: "var(--ink-3)", position: "relative" } }, /* @__PURE__ */ React.createElement("span", { style: { position: "absolute", left: 0, top: -3, width: 1, height: 7, background: "var(--ink-3)" } }), /* @__PURE__ */ React.createElement("span", { style: { position: "absolute", left: "50%", top: -3, width: 1, height: 7, background: "var(--ink-3)" } }), /* @__PURE__ */ React.createElement("span", { style: { position: "absolute", right: 0, top: -3, width: 1, height: 7, background: "var(--ink-3)" } })), /* @__PURE__ */ React.createElement("span", null, "20 mm")));
  }
  function Legend({ color, label }) {
    return /* @__PURE__ */ React.createElement("span", { style: { display: "inline-flex", alignItems: "center", gap: 5 } }, /* @__PURE__ */ React.createElement("span", { style: { width: 8, height: 8, borderRadius: "50%", background: color, display: "inline-block" } }), /* @__PURE__ */ React.createElement("span", { style: { letterSpacing: ".06em" } }, label));
  }
  function Pin({ id, sev, x, y, n }) {
    const c = sev === "crit" ? "var(--critical)" : sev === "warn" ? "var(--warn)" : "var(--info)";
    return /* @__PURE__ */ React.createElement("div", { style: {
      position: "absolute",
      left: `${x}%`,
      top: `${y}%`,
      transform: "translate(-50%, -100%)",
      pointerEvents: "auto"
    } }, /* @__PURE__ */ React.createElement("div", { style: {
      width: 24,
      height: 24,
      borderRadius: "50% 50% 50% 2px",
      transform: "rotate(-45deg)",
      background: c,
      color: "var(--paper)",
      boxShadow: `0 2px 6px rgba(0,0,0,.4), 0 0 0 2px var(--paper)`,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontFamily: "'Geist Mono', monospace",
      fontSize: 10,
      fontWeight: 700
    } }, /* @__PURE__ */ React.createElement("span", { style: { transform: "rotate(45deg)" } }, n)));
  }
  function DPinsList({ pins }) {
    return /* @__PURE__ */ React.createElement("aside", { style: {
      borderLeft: "0.5px solid var(--rule-2)",
      background: "var(--paper-2)",
      padding: "20px 18px",
      display: "flex",
      flexDirection: "column",
      gap: 10,
      overflowY: "auto"
    } }, /* @__PURE__ */ React.createElement("div", { style: { display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 4 } }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 12, fontWeight: 500 } }, "Piny komentarzy"), /* @__PURE__ */ React.createElement("div", { style: { fontFamily: "'Geist Mono', monospace", fontSize: 10, color: "var(--ink-3)" } }, pins.length)), pins.map((p) => {
      const d = CMP.diffs.find((x) => x.id === p.id);
      return /* @__PURE__ */ React.createElement(PinCard, { key: p.id, pin: p, d });
    }));
  }
  function PinCard({ pin, d }) {
    const c = pin.sev === "crit" ? "var(--critical)" : pin.sev === "warn" ? "var(--warn)" : "var(--info)";
    const commentsByPin = {
      "D-01": [
        { who: "JZ", when: "17:31", text: "EAN nie waliduje sumy kontrolnej. Sprawdzi\u0107 z dostawc\u0105." },
        { who: "PW", when: "17:55", text: "Wymaga ponownego druku \u2014 blokuje rejestracj\u0119." }
      ],
      "D-02": [{ who: "PW", when: "17:38", text: "MDR Art. 23 ust. 4 \u2014 bez tej linii nie wpu\u015Bcimy do obrotu." }],
      "D-03": [{ who: "JZ", when: "17:42", text: "Rynek DACH jest aktywny w PIM, sprawdzam u marketingu." }],
      "D-05": [{ who: "AK", when: "17:14", text: "Sprawdzi\u0107 pole ochronne loga \u2014 minimum 8 mm wok\xF3\u0142." }],
      "D-09": [
        { who: "AK", when: "16:58", text: "\u0394E 4.2 to za du\u017Co. Wymaga pr\xF3by drukarskiej." },
        { who: "TB", when: "17:05", text: "Mog\u0119 przeliczy\u0107 z profilu Coated v2 300% \u2014 wraca w pn." }
      ]
    };
    const comments = commentsByPin[d.id] || [];
    return /* @__PURE__ */ React.createElement("div", { style: {
      background: "var(--paper)",
      borderRadius: 3,
      border: "0.5px solid var(--rule-2)",
      borderLeft: `2px solid ${c}`,
      padding: "10px 12px"
    } }, /* @__PURE__ */ React.createElement("div", { style: { display: "flex", alignItems: "center", gap: 8 } }, /* @__PURE__ */ React.createElement("span", { style: {
      width: 18,
      height: 18,
      borderRadius: "50%",
      background: c,
      color: "var(--paper)",
      fontFamily: "'Geist Mono', monospace",
      fontSize: 10,
      fontWeight: 700,
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center"
    } }, pin.n), /* @__PURE__ */ React.createElement("span", { style: { fontFamily: "'Geist Mono', monospace", fontSize: 10, color: "var(--ink-3)" } }, d.id), /* @__PURE__ */ React.createElement("span", { style: { flex: 1 } }), d.blocker && /* @__PURE__ */ React.createElement("span", { style: { padding: "1px 4px", fontFamily: "'Geist Mono', monospace", fontSize: 8, background: "var(--critical)", color: "var(--paper)", letterSpacing: ".08em" } }, "BLOKER")), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 6, fontSize: 12, fontWeight: 500 } }, d.field), /* @__PURE__ */ React.createElement("div", { style: {
      marginTop: 4,
      fontSize: 11,
      color: "var(--ink-2)",
      lineHeight: 1.4,
      overflow: "hidden",
      textOverflow: "ellipsis",
      display: "-webkit-box",
      WebkitLineClamp: 2,
      WebkitBoxOrient: "vertical"
    } }, d.note), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 6, fontFamily: "'Geist Mono', monospace", fontSize: 10, color: "var(--ink-4)" } }, "\u21B3 ", d.where), comments.length > 0 && /* @__PURE__ */ React.createElement("div", { style: { marginTop: 8, paddingTop: 8, borderTop: "0.5px dashed var(--rule-2)", display: "flex", flexDirection: "column", gap: 6 } }, comments.map((cm, i) => /* @__PURE__ */ React.createElement("div", { key: i, style: { display: "flex", gap: 6 } }, /* @__PURE__ */ React.createElement("div", { style: {
      width: 18,
      height: 18,
      borderRadius: "50%",
      background: "var(--rule-3)",
      color: "var(--ink)",
      fontSize: 9,
      fontWeight: 600,
      fontFamily: "'Geist Mono', monospace",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      flexShrink: 0
    } }, cm.who), /* @__PURE__ */ React.createElement("div", { style: { flex: 1, minWidth: 0 } }, /* @__PURE__ */ React.createElement("div", { style: { display: "flex", gap: 6, alignItems: "baseline" } }, /* @__PURE__ */ React.createElement("span", { style: { fontSize: 10, fontWeight: 500, color: "var(--ink-2)" } }, cm.who), /* @__PURE__ */ React.createElement("span", { style: { fontFamily: "'Geist Mono', monospace", fontSize: 9, color: "var(--ink-4)" } }, cm.when)), /* @__PURE__ */ React.createElement("div", { style: { fontSize: 11, color: "var(--ink-2)", lineHeight: 1.4, marginTop: 1 } }, cm.text)))), /* @__PURE__ */ React.createElement("div", { style: {
      marginTop: 2,
      display: "flex",
      alignItems: "center",
      gap: 6,
      padding: "6px 8px",
      borderRadius: 3,
      background: "var(--paper-2)",
      fontSize: 11,
      color: "var(--ink-4)"
    } }, /* @__PURE__ */ React.createElement("span", null, "\uFF0B"), /* @__PURE__ */ React.createElement("span", { style: { fontStyle: "italic" } }, "odpowiedz\u2026"))));
  }
  Object.assign(window, { VariantD });
})();

// ── variant-e.jsx ──
(() => {
  function VariantE() {
    return /* @__PURE__ */ React.createElement("div", { style: {
      width: 920,
      minHeight: 1320,
      background: "var(--paper)",
      fontFamily: "'Geist', sans-serif",
      color: "var(--ink)",
      display: "flex",
      flexDirection: "column"
    } }, /* @__PURE__ */ React.createElement(EMailChrome, null), /* @__PURE__ */ React.createElement(EReportBody, null));
  }
  function EMailChrome() {
    return /* @__PURE__ */ React.createElement("header", { style: {
      background: "var(--paper-2)",
      borderBottom: "0.5px solid var(--rule-2)",
      padding: "14px 28px 12px"
    } }, /* @__PURE__ */ React.createElement("div", { style: { display: "flex", alignItems: "center", gap: 14 } }, /* @__PURE__ */ React.createElement("span", { style: {
      padding: "3px 8px",
      background: "var(--paper)",
      border: "0.5px solid var(--rule-2)",
      fontFamily: "'Geist Mono', monospace",
      fontSize: 10,
      color: "var(--ink-3)",
      letterSpacing: ".06em",
      borderRadius: 2
    } }, "SKRZYNKA"), /* @__PURE__ */ React.createElement("span", { style: { fontSize: 12, color: "var(--ink-3)" } }, "artcompare@example.com"), /* @__PURE__ */ React.createElement("span", { style: { flex: 1 } }), /* @__PURE__ */ React.createElement("span", { style: { fontFamily: "'Geist Mono', monospace", fontSize: 11, color: "var(--ink-4)" } }, CMP.date, " \xB7 ", CMP.time)), /* @__PURE__ */ React.createElement("h1", { style: {
      margin: "14px 0 4px",
      fontFamily: "'Newsreader', serif",
      fontWeight: 500,
      fontSize: 28,
      letterSpacing: "-.01em",
      lineHeight: 1.15
    } }, "Re: ", /* @__PURE__ */ React.createElement("span", { style: { fontStyle: "italic", color: "var(--ink-2)" } }, "easyCARE 200 \xB7 gaziki sterylne"), /* @__PURE__ */ React.createElement("br", null), /* @__PURE__ */ React.createElement("span", { style: { color: "var(--critical)" } }, "5 krytycznych"), " rozbie\u017Cno\u015Bci w v1.5"), /* @__PURE__ */ React.createElement("div", { style: { display: "grid", gridTemplateColumns: "80px 1fr", gap: "4px 14px", marginTop: 14, fontSize: 12 } }, /* @__PURE__ */ React.createElement("div", { style: { color: "var(--ink-3)" } }, "Od"), /* @__PURE__ */ React.createElement("div", null, "ArtCompare <artcompare@example.com>"), /* @__PURE__ */ React.createElement("div", { style: { color: "var(--ink-3)" } }, "Do"), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement(Chip, { name: "J. Zieli\u0144ska \xB7 QA Lead" }), /* @__PURE__ */ React.createElement(Chip, { name: "A. Kowalska \xB7 Brand" }), /* @__PURE__ */ React.createElement(Chip, { name: "P. Wojtas \xB7 Regulatory" })), /* @__PURE__ */ React.createElement("div", { style: { color: "var(--ink-3)" } }, "DW"), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement(Chip, { name: "M. Nowak \xB7 PrintHub Wuhan (dostawca)" }), /* @__PURE__ */ React.createElement(Chip, { name: "T. B\u0105k \xB7 DTP" })), /* @__PURE__ */ React.createElement("div", { style: { color: "var(--ink-3)" } }, "Za\u0142\u0105czniki"), /* @__PURE__ */ React.createElement("div", { style: { display: "flex", gap: 8, flexWrap: "wrap" } }, /* @__PURE__ */ React.createElement(Attachment, { label: "raport_28.pdf", size: "412 KB" }), /* @__PURE__ */ React.createElement(Attachment, { label: "diff.zip", size: "2.4 MB" }), /* @__PURE__ */ React.createElement(Attachment, { label: "v1.5_marked.pdf", size: "6.1 MB" }))));
  }
  function Chip({ name }) {
    return /* @__PURE__ */ React.createElement("span", { style: {
      display: "inline-block",
      padding: "2px 8px",
      marginRight: 6,
      marginBottom: 2,
      background: "var(--paper-3)",
      borderRadius: 12,
      fontSize: 11,
      color: "var(--ink-2)"
    } }, name);
  }
  function Attachment({ label, size }) {
    return /* @__PURE__ */ React.createElement("span", { style: {
      display: "inline-flex",
      alignItems: "center",
      gap: 6,
      padding: "4px 10px",
      background: "var(--paper)",
      border: "0.5px solid var(--rule-2)",
      borderRadius: 2,
      fontSize: 11,
      color: "var(--ink-2)"
    } }, /* @__PURE__ */ React.createElement("span", { style: { fontFamily: "'Geist Mono', monospace", color: "var(--accent)" } }, "\u258E"), label, /* @__PURE__ */ React.createElement("span", { style: { color: "var(--ink-4)", fontFamily: "'Geist Mono', monospace", fontSize: 10 } }, size));
  }
  function EReportBody() {
    return /* @__PURE__ */ React.createElement("main", { style: { padding: "24px 28px 32px" } }, /* @__PURE__ */ React.createElement(EOpening, null), /* @__PURE__ */ React.createElement(EVerdictStrip, null), /* @__PURE__ */ React.createElement(EThumbnails, null), /* @__PURE__ */ React.createElement(ETopFindings, null), /* @__PURE__ */ React.createElement(EByModule, null), /* @__PURE__ */ React.createElement(ECTA, null), /* @__PURE__ */ React.createElement(EFooter, null));
  }
  function EOpening() {
    return /* @__PURE__ */ React.createElement("section", { style: { marginBottom: 24 } }, /* @__PURE__ */ React.createElement("p", { style: { margin: "0 0 10px", fontSize: 14, lineHeight: 1.6, color: "var(--ink)" } }, "Cze\u015B\u0107 zespole \u2014 automatyczne por\xF3wnanie ", /* @__PURE__ */ React.createElement("span", { style: { fontFamily: "'Geist Mono', monospace", color: "var(--accent-2)" } }, CMP.sku, "-260320"), " v1.4 vs v1.5 (rev. dostawcy) wykry\u0142o", /* @__PURE__ */ React.createElement("span", { style: { color: "var(--critical)", fontWeight: 500 } }, " ", CMP.summary.critical, " krytycznych"), " rozbie\u017Cno\u015Bci, w tym ", /* @__PURE__ */ React.createElement("strong", { style: { color: "var(--ink)", fontWeight: 600 } }, "3 blokuj\u0105ce druk"), "."), /* @__PURE__ */ React.createElement("p", { style: { margin: 0, fontSize: 13, lineHeight: 1.6, color: "var(--ink-2)" } }, "Najpowa\u017Cniejsze: niezgodny ", /* @__PURE__ */ React.createElement("strong", null, "kod EAN-13"), " (zamiana cyfr, suma kontrolna niepoprawna), usuni\u0119ty wymagany ", /* @__PURE__ */ React.createElement("strong", null, "znak ostrzegawczy MDR"), " i brak ", /* @__PURE__ */ React.createElement("strong", null, "wersji DE"), ". Rekomendowane: zatrzymanie wysy\u0142ki do drukarni, eskalacja do Reg. + QA, korekta u dostawcy w 24 h."));
  }
  function EVerdictStrip() {
    const totals = [
      { n: CMP.summary.critical, label: "Krytyczne", c: "var(--critical)" },
      { n: CMP.summary.warning, label: "Ostrze\u017Cenia", c: "var(--warn)" },
      { n: CMP.summary.info, label: "Informacja", c: "var(--info)" },
      { n: CMP.summary.ok, label: "Zgodne", c: "var(--ok)" }
    ];
    return /* @__PURE__ */ React.createElement("section", { style: {
      marginBottom: 24,
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: 12
    } }, /* @__PURE__ */ React.createElement("div", { style: {
      padding: "16px 18px",
      background: "var(--critical-bg)",
      borderLeft: "2px solid var(--critical)",
      borderRadius: 2,
      display: "flex",
      alignItems: "center",
      gap: 14
    } }, /* @__PURE__ */ React.createElement("div", { style: {
      fontFamily: "'Geist Mono', monospace",
      fontSize: 11,
      fontWeight: 600,
      letterSpacing: ".1em",
      color: "var(--critical)",
      padding: "4px 8px",
      background: "var(--paper-2)",
      borderRadius: 2
    } }, "WERDYKT"), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("div", { style: { fontFamily: "'Newsreader', serif", fontStyle: "italic", fontSize: 18, color: "var(--ink)" } }, "Nie dopuszcza\u0107 do druku"), /* @__PURE__ */ React.createElement("div", { style: { fontSize: 11, color: "var(--ink-2)", marginTop: 2 } }, "3 blokery \xB7 oczekuje na korekt\u0119 dostawcy"))), /* @__PURE__ */ React.createElement("div", { style: {
      padding: "12px 14px",
      background: "var(--paper-2)",
      borderRadius: 2,
      display: "grid",
      gridTemplateColumns: "repeat(4, 1fr)",
      gap: 6
    } }, totals.map((t) => /* @__PURE__ */ React.createElement("div", { key: t.label, style: { textAlign: "center" } }, /* @__PURE__ */ React.createElement("div", { style: {
      fontFamily: "'Geist Mono', monospace",
      fontSize: 22,
      fontWeight: 600,
      color: t.c,
      lineHeight: 1
    } }, t.n), /* @__PURE__ */ React.createElement("div", { style: {
      fontSize: 9,
      color: "var(--ink-3)",
      letterSpacing: ".08em",
      textTransform: "uppercase",
      marginTop: 5
    } }, t.label)))));
  }
  function EThumbnails() {
    return /* @__PURE__ */ React.createElement("section", { style: { marginBottom: 24 } }, /* @__PURE__ */ React.createElement(SubHead, { title: "Wersje", no: "01" }), /* @__PURE__ */ React.createElement("div", { style: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 } }, /* @__PURE__ */ React.createElement(ThumbBlock, { variant: "a", label: "A \xB7 v1.4 \xB7 \u017Ar\xF3d\u0142o \xB7 ZATWIERDZONE 24.02", stamp: "OK", stampColor: "var(--ok)" }), /* @__PURE__ */ React.createElement(ThumbBlock, { variant: "b", label: "B \xB7 v1.5 \xB7 rev. dostawcy \xB7 19.05", stamp: "5 KRYT.", stampColor: "var(--critical)", flagged: true })));
  }
  function ThumbBlock({ variant, label, stamp, stampColor, flagged }) {
    return /* @__PURE__ */ React.createElement("div", { style: {
      background: "var(--paper-2)",
      borderRadius: 2,
      border: flagged ? "1px solid var(--critical)" : "0.5px solid var(--rule-2)",
      padding: 10
    } }, /* @__PURE__ */ React.createElement("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 } }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 10, color: "var(--ink-3)", letterSpacing: ".04em" } }, label), /* @__PURE__ */ React.createElement("div", { style: {
      padding: "2px 6px",
      fontFamily: "'Geist Mono', monospace",
      fontSize: 9,
      fontWeight: 600,
      letterSpacing: ".08em",
      color: stampColor,
      border: `0.5px solid ${stampColor}`
    } }, stamp)), /* @__PURE__ */ React.createElement(PackArtwork, { variant, width: "100%", showBleed: false }));
  }
  function SubHead({ title, no }) {
    return /* @__PURE__ */ React.createElement("div", { style: {
      display: "flex",
      alignItems: "baseline",
      gap: 10,
      marginBottom: 12
    } }, /* @__PURE__ */ React.createElement("span", { style: {
      fontFamily: "'Geist Mono', monospace",
      fontSize: 10,
      color: "var(--accent)",
      letterSpacing: ".1em"
    } }, no), /* @__PURE__ */ React.createElement("h2", { style: { margin: 0, fontFamily: "'Newsreader', serif", fontWeight: 500, fontSize: 19, letterSpacing: "-.01em" } }, title), /* @__PURE__ */ React.createElement("div", { style: { flex: 1, height: 1, background: "var(--rule-2)", alignSelf: "center", marginLeft: 6 } }));
  }
  function ETopFindings() {
    const crits = CMP.diffs.filter((d) => d.sev === "crit");
    return /* @__PURE__ */ React.createElement("section", { style: { marginBottom: 24 } }, /* @__PURE__ */ React.createElement(SubHead, { title: "Krytyczne ustalenia", no: "02" }), /* @__PURE__ */ React.createElement("div", { style: { display: "flex", flexDirection: "column", gap: 8 } }, crits.map((d, i) => /* @__PURE__ */ React.createElement(ETopRow, { key: d.id, d, idx: i + 1 }))));
  }
  function ETopRow({ d, idx }) {
    return /* @__PURE__ */ React.createElement("div", { style: {
      display: "grid",
      gridTemplateColumns: "28px 1fr 220px",
      gap: 14,
      alignItems: "flex-start",
      padding: "12px 14px",
      background: "var(--paper-2)",
      borderLeft: "2px solid var(--critical)",
      borderRadius: 2
    } }, /* @__PURE__ */ React.createElement("div", { style: {
      fontFamily: "'Geist Mono', monospace",
      fontSize: 18,
      fontWeight: 500,
      color: "var(--critical)",
      lineHeight: 1
    } }, String(idx).padStart(2, "0")), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("div", { style: {
      display: "flex",
      alignItems: "center",
      gap: 8,
      fontSize: 10,
      color: "var(--ink-3)",
      letterSpacing: ".04em",
      textTransform: "uppercase"
    } }, /* @__PURE__ */ React.createElement("span", { style: { fontFamily: "'Geist Mono', monospace", color: "var(--ink-2)" } }, d.id), /* @__PURE__ */ React.createElement("span", null, "\xB7"), /* @__PURE__ */ React.createElement("span", null, CATEGORIES[d.cat]?.label), d.blocker && /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("span", null, "\xB7"), /* @__PURE__ */ React.createElement("span", { style: {
      padding: "1px 5px",
      background: "var(--critical)",
      color: "var(--paper)",
      fontFamily: "'Geist Mono', monospace",
      fontSize: 9,
      letterSpacing: ".08em"
    } }, "BLOKER"))), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 4, fontSize: 14, fontWeight: 500, color: "var(--ink)" } }, d.field), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 4, fontSize: 12, color: "var(--ink-2)", lineHeight: 1.45 } }, d.note)), /* @__PURE__ */ React.createElement("div", { style: { display: "flex", flexDirection: "column", gap: 4 } }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 9, color: "var(--ink-3)", letterSpacing: ".06em", textTransform: "uppercase" } }, "A \u2192 B"), /* @__PURE__ */ React.createElement("div", { style: {
      fontFamily: "'Geist Mono', monospace",
      fontSize: 11,
      color: "var(--ink-2)",
      padding: "4px 7px",
      background: "var(--paper)",
      borderRadius: 2,
      whiteSpace: "nowrap",
      overflow: "hidden",
      textOverflow: "ellipsis"
    } }, d.a || "\u2014"), /* @__PURE__ */ React.createElement("div", { style: {
      fontFamily: "'Geist Mono', monospace",
      fontSize: 11,
      color: "var(--critical)",
      padding: "4px 7px",
      background: "var(--critical-bg)",
      borderRadius: 2,
      whiteSpace: "nowrap",
      overflow: "hidden",
      textOverflow: "ellipsis"
    } }, d.b || "\u2014")));
  }
  function EByModule() {
    return /* @__PURE__ */ React.createElement("section", { style: { marginBottom: 24 } }, /* @__PURE__ */ React.createElement(SubHead, { title: "Status modu\u0142\xF3w", no: "03" }), /* @__PURE__ */ React.createElement("div", { style: {
      display: "grid",
      gridTemplateColumns: "repeat(4, 1fr)",
      gap: 8
    } }, CMP.modules.map((m) => {
      const sevKey = m.status === "fail" ? "crit" : m.status === "warn" ? "warn" : m.status === "info" ? "info" : "ok";
      return /* @__PURE__ */ React.createElement("div", { key: m.id, style: {
        padding: "10px 12px",
        background: "var(--paper-2)",
        borderRadius: 2,
        borderTop: `2px solid ${SEV[sevKey].color}`
      } }, /* @__PURE__ */ React.createElement("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center" } }, /* @__PURE__ */ React.createElement("span", { style: { fontFamily: "'Geist Mono', monospace", color: "var(--ink-3)", fontSize: 11 } }, CATEGORIES[m.id]?.icon), /* @__PURE__ */ React.createElement(SevTag, { sev: sevKey })), /* @__PURE__ */ React.createElement("div", { style: { marginTop: 6, fontSize: 11, fontWeight: 500, lineHeight: 1.3 } }, m.name), /* @__PURE__ */ React.createElement("div", { style: {
        marginTop: 6,
        display: "flex",
        gap: 6,
        fontFamily: "'Geist Mono', monospace",
        fontSize: 10
      } }, m.crit > 0 && /* @__PURE__ */ React.createElement("span", { style: { color: "var(--critical)" } }, m.crit, "c"), m.warn > 0 && /* @__PURE__ */ React.createElement("span", { style: { color: "var(--warn)" } }, m.warn, "w"), /* @__PURE__ */ React.createElement("span", { style: { color: "var(--ok)" } }, m.ok, "\u2713")));
    })));
  }
  function ECTA() {
    return /* @__PURE__ */ React.createElement("section", { style: {
      marginBottom: 24,
      padding: "18px 22px",
      background: "var(--paper-2)",
      borderRadius: 2,
      border: "0.5px solid var(--rule-2)"
    } }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 11, color: "var(--ink-3)", letterSpacing: ".08em", textTransform: "uppercase", marginBottom: 8 } }, "Rekomendowane dzia\u0142ania"), /* @__PURE__ */ React.createElement("ol", { style: { margin: 0, paddingLeft: 18, fontSize: 13, color: "var(--ink-2)", lineHeight: 1.7 } }, /* @__PURE__ */ React.createElement("li", null, /* @__PURE__ */ React.createElement("strong", { style: { color: "var(--ink)" } }, "QA"), " \xB7 zatrzyma\u0107 release v1.5, oznaczy\u0107 blokery"), /* @__PURE__ */ React.createElement("li", null, /* @__PURE__ */ React.createElement("strong", { style: { color: "var(--ink)" } }, "Regulatory"), " \xB7 zweryfikowa\u0107 braki MDR (warning + wersja DE)"), /* @__PURE__ */ React.createElement("li", null, /* @__PURE__ */ React.createElement("strong", { style: { color: "var(--ink)" } }, "Brand"), " \xB7 sprawdzi\u0107 pole ochronne loga i \u0394E Pantone"), /* @__PURE__ */ React.createElement("li", null, /* @__PURE__ */ React.createElement("strong", { style: { color: "var(--ink)" } }, "Dostawca"), " \xB7 korekta pliku do ", /* @__PURE__ */ React.createElement("span", { style: { fontFamily: "'Geist Mono', monospace", color: "var(--ink)" } }, "22.05 16:00"))), /* @__PURE__ */ React.createElement("div", { style: {
      marginTop: 16,
      display: "flex",
      gap: 8,
      alignItems: "center"
    } }, /* @__PURE__ */ React.createElement("button", { style: {
      padding: "8px 14px",
      background: "var(--accent)",
      color: "var(--paper)",
      border: "none",
      borderRadius: 2,
      fontFamily: "'Geist', sans-serif",
      fontSize: 12,
      fontWeight: 500,
      cursor: "pointer"
    } }, "Otw\xF3rz w ArtCompare \u203A"), /* @__PURE__ */ React.createElement("button", { style: {
      padding: "8px 14px",
      background: "transparent",
      color: "var(--ink-2)",
      border: "0.5px solid var(--rule-3)",
      borderRadius: 2,
      fontFamily: "'Geist', sans-serif",
      fontSize: 12,
      fontWeight: 500,
      cursor: "pointer"
    } }, "Pobierz raport"), /* @__PURE__ */ React.createElement("button", { style: {
      padding: "8px 14px",
      background: "transparent",
      color: "var(--ink-2)",
      border: "0.5px solid var(--rule-3)",
      borderRadius: 2,
      fontFamily: "'Geist', sans-serif",
      fontSize: 12,
      fontWeight: 500,
      cursor: "pointer"
    } }, "Eskaluj do dyr. QA"), /* @__PURE__ */ React.createElement("span", { style: { flex: 1 } }), /* @__PURE__ */ React.createElement("span", { style: { fontSize: 11, color: "var(--ink-4)", fontStyle: "italic" } }, "raport wygenerowany automatycznie")));
  }
  function EFooter() {
    return /* @__PURE__ */ React.createElement("footer", { style: {
      paddingTop: 16,
      borderTop: "0.5px solid var(--rule-2)",
      fontFamily: "'Geist Mono', monospace",
      fontSize: 10,
      color: "var(--ink-4)",
      display: "flex",
      justifyContent: "space-between"
    } }, /* @__PURE__ */ React.createElement("span", null, "ArtCompare v1.0 \xB7 ACME sp. z o.o."), /* @__PURE__ */ React.createElement("span", null, CMP.date, " \xB7 ", CMP.time, " \xB7 por\xF3wnanie ", CMP.no));
  }
  Object.assign(window, { VariantE });
})();

// ── app.jsx ──
(() => {
  function App() {
    return /* @__PURE__ */ React.createElement(
      DesignCanvas,
      {
        title: "ArtCompare \xB7 raport por\xF3wnania artwork\xF3w opakowa\u0144",
        subtitle: "5 wariant\xF3w \xB7 case: ZAY-easyCARE(200)-BNPFE-260320 v1.4 \u2192 v1.5"
      },
      /* @__PURE__ */ React.createElement(
        DCSection,
        {
          id: "paper",
          title: "A \xB7 Raport audytowy (print-grade)",
          subtitle: "Ewolucja DocCompare v6 \u2014 A4 portrait, do druku i archiwum. G\u0119sta typografia, podgl\u0105d artwork\xF3w inline."
        },
        /* @__PURE__ */ React.createElement(
          DCArtboard,
          {
            id: "paper-1",
            label: "A \xB7 raport audytowy",
            width: 920,
            height: 1640
          },
          /* @__PURE__ */ React.createElement(VariantA, null)
        )
      ),
      /* @__PURE__ */ React.createElement(
        DCSection,
        {
          id: "workspace",
          title: "B \xB7 Workspace inspekcji",
          subtitle: "Aplikacja webowa. Tryby diff (side-by-side / overlay / onion), lista rozbie\u017Cno\u015Bci z akcjami, komentarze."
        },
        /* @__PURE__ */ React.createElement(
          DCArtboard,
          {
            id: "workspace-1",
            label: "B \xB7 workspace inspekcji",
            width: 1440,
            height: 900
          },
          /* @__PURE__ */ React.createElement(VariantB, null)
        )
      ),
      /* @__PURE__ */ React.createElement(
        DCSection,
        {
          id: "board",
          title: "C \xB7 Review board",
          subtitle: "Kanban rozbie\u017Cno\u015Bci. Ka\u017Cda jako karta z odpowiedzialn\u0105 osob\u0105, statusem przegl\u0105du i komentarzami."
        },
        /* @__PURE__ */ React.createElement(
          DCArtboard,
          {
            id: "board-1",
            label: "C \xB7 review board",
            width: 1280,
            height: 1100
          },
          /* @__PURE__ */ React.createElement(VariantC, null)
        )
      ),
      /* @__PURE__ */ React.createElement(
        DCSection,
        {
          id: "annotated",
          title: "D \xB7 Annotated zoom",
          subtitle: "Jeden du\u017Cy podgl\u0105d artworku z pinami komentarzy w stylu Figmy. Tryby A / B / tylko r\xF3\u017Cnice / overlay."
        },
        /* @__PURE__ */ React.createElement(
          DCArtboard,
          {
            id: "annotated-1",
            label: "D \xB7 annotated zoom",
            width: 1280,
            height: 1100
          },
          /* @__PURE__ */ React.createElement(VariantD, null)
        )
      ),
      /* @__PURE__ */ React.createElement(
        DCSection,
        {
          id: "email",
          title: "E \xB7 Email / exec summary",
          subtitle: "Jednostronicowe podsumowanie do wysy\u0142ki interesariuszom. Werdykt, top-5 ustale\u0144, status modu\u0142\xF3w, akcje."
        },
        /* @__PURE__ */ React.createElement(
          DCArtboard,
          {
            id: "email-1",
            label: "E \xB7 email summary",
            width: 920,
            height: 1480
          },
          /* @__PURE__ */ React.createElement(VariantE, null)
        )
      )
    );
  }
  const root = ReactDOM.createRoot(document.getElementById("root"));
  root.render(/* @__PURE__ */ React.createElement(App, null));
})();
