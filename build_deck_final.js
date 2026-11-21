// Build deck/atom_by_atom_silicon.pptx  —  run: node build_deck.js
// Every number on a slide comes from REFERENCES.md (Key numbers). Derived values are labelled "our calc." / "model".
const pptxgen = require("pptxgenjs");
const sizeOf = require("image-size");
const fs = require("fs");

// ---------------------------------------------------------------- theme (defined once)
const T = {
  font: "Arial",
  ink: "1F2A36", muted: "5B6770", light: "E5E8EB", panel: "F4F6F8",
  P: "D9731A", As: "0F9FA0",
  mat: { si: "8C96A0", cap: "C9D1D8", h: "9CC8E6", p: "D9731A", as: "0F9FA0", al: "5E6A75", ox: "E3DDF0" },
  title: 26, body: 15, cap: 10, src: 9,
};
const F = (f) => `figures/final/${f}`;
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.author = "Hanah Rahman";
pres.title = "Atom-by-Atom Silicon: Building Quantum Processors from Single Dopant Atoms";

// ---------------------------------------------------------------- slide masters (one per frame)
const titlePH = { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.26, w: 7.3, h: 0.62, fontFace: T.font, fontSize: T.title, bold: true, color: T.ink, align: "left", valign: "top", margin: 0 }, text: "" } };
const srcPH = { placeholder: { options: { name: "src", type: "body", x: 0.5, y: 5.2, w: 6.9, h: 0.32, fontFace: T.font, fontSize: T.src, color: "7A858E", align: "left", valign: "top", margin: 0 }, text: "" } };
const footer = { text: { text: "EE143 · H. Rahman", options: { x: 7.45, y: 5.24, w: 1.5, h: 0.25, fontFace: T.font, fontSize: 9, color: "7A858E", align: "right", margin: 0 } } };
const slideNum = { x: 9.0, y: 5.24, w: 0.5, h: 0.25, fontFace: T.font, fontSize: 9, color: "7A858E", align: "right" };
const frame = (name) => pres.defineSlideMaster({ title: name, background: { color: "FFFFFF" }, objects: [titlePH, srcPH, footer], slideNumber: slideNum });
["FIG_TEXT", "TWO_FIG", "TABLE", "TITLE_ONLY", "PROCESS"].forEach(frame);
pres.defineSlideMaster({ title: "REFS", background: { color: "FFFFFF" }, objects: [titlePH, footer], slideNumber: slideNum });
pres.defineSlideMaster({ title: "TITLE", background: { color: "111A22" }, objects: [] });
pres.defineSlideMaster({ title: "SECTION", background: { color: "FFFFFF" }, objects: [titlePH, footer], slideNumber: slideNum });

["Intro", "Act 1", "Act 2", "Act 3", "Act 4", "Wrap-up", "Backup"].forEach((t) => pres.addSection({ title: t }));

// ---------------------------------------------------------------- helpers (fresh option objects every call)
const NOTES = [];
function newSlide(master, title, section) {
  const s = pres.addSlide({ masterName: master, sectionTitle: section });
  if (title) s.addText(title, { placeholder: "title", x: 0.5, y: 0.26, w: master === "PROCESS" ? 7.3 : 9.0, h: 0.62, fontFace: T.font, fontSize: T.title, bold: true, color: T.ink, align: "left", valign: "top", margin: 0 });
  s._title = title || "";
  const ACT = { "Act 1": "ACT 1 · WHY SINGLE ATOMS", "Act 2": "ACT 2 · HOW IT'S BUILT", "Act 3": "ACT 3 · DOES IT WORK?", "Act 4": "ACT 4 · HOW IT SCALES" };
  if (ACT[section]) s.addText(ACT[section], { x: 0.5, y: 0.06, w: 6, h: 0.2, fontFace: T.font, fontSize: 8.5, bold: true, color: T.As, charSpacing: 1, margin: 0, isTextBox: true });
  return s;
}
function notes(s, text) { s.addNotes(text); NOTES.push({ title: s._title, text }); }
function src(s, text) { s.addText(text, { placeholder: "src", x: 0.5, y: 5.2, w: 6.9, h: 0.32, fontFace: T.font, fontSize: T.src, color: "7A858E", align: "left", valign: "top", margin: 0 }); }
function img(s, file, x, y, w, h, align = "center", valign = "top") {
  const d = sizeOf(F(file)); const r = Math.min(w / d.width, h / d.height);
  const iw = d.width * r, ih = d.height * r;
  const ix = align === "left" ? x : align === "right" ? x + w - iw : x + (w - iw) / 2;
  const iy = valign === "top" ? y : valign === "bottom" ? y + h - ih : y + (h - ih) / 2;
  s.addImage({ path: F(file), x: ix, y: iy, w: iw, h: ih });
  return { x: ix, y: iy, w: iw, h: ih };
}
function text(s, t, x, y, w, h, o = {}) {
  s.addText(t, Object.assign({ x, y, w, h, fontFace: T.font, fontSize: T.body, color: T.ink, valign: "top", align: "left", margin: 0, isTextBox: true }, o));
}
function bullets(s, items, x, y, w, h, fs = T.body) {
  const runs = items.map((it) => ({ text: it, options: { bullet: { indent: 14 }, paraSpaceAfter: 8, breakLine: true } }));
  s.addText(runs, { x, y, w, h, fontFace: T.font, fontSize: fs, color: T.ink, valign: "top", align: "left", margin: 0, isTextBox: true });
}
function caption(s, t, x, y, w, h = 0.3) { text(s, t, x, y, w, h, { fontSize: T.cap, color: T.muted }); }
function tracker(s, label) { text(s, label, 7.85, 0.33, 1.65, 0.3, { fontSize: 11, color: T.muted, align: "right", bold: true }); }
function legend(s, x, y) {
  const items = [["Si substrate", T.mat.si], ["Si cap", T.mat.cap], ["H resist", T.mat.h], ["P", T.mat.p], ["As", T.mat.as], ["Al", T.mat.al], ["SiO₂", T.mat.ox]];
  let cx = x;
  items.forEach(([lab, col]) => {
    s.addShape(pres.shapes.RECTANGLE, { x: cx, y: y + 0.04, w: 0.14, h: 0.14, fill: { color: col }, line: { color: col, width: 0 } });
    const w = 0.1 + lab.length * 0.047;
    text(s, lab, cx + 0.18, y, w, 0.22, { fontSize: 9, color: T.muted });
    cx += 0.19 + w + 0.02;
  });
}
function callout(s, t, x, y, w, h, o = {}) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: T.panel }, line: { color: T.panel, width: 0 } });
  text(s, t, x + 0.12, y + 0.08, w - 0.24, h - 0.16, Object.assign({ fontSize: 12 }, o));
}
const chartBase = () => ({ fontFace: T.font, catAxisLabelColor: T.ink, valAxisLabelColor: T.ink, catAxisLabelFontFace: T.font, valAxisLabelFontFace: T.font,
  catAxisLabelFontSize: 10, valAxisLabelFontSize: 10, titleColor: T.ink, titleFontFace: T.font, titleFontSize: 12, showTitle: true,
  valGridLine: { color: "E5E8EB", size: 0.5 }, catGridLine: { style: "none" }, catAxisLineColor: "9AA3AC", valAxisLineShow: false,
  legendFontFace: T.font, legendFontSize: 10, legendColor: T.ink, catAxisTitleColor: T.ink, valAxisTitleColor: T.ink,
  catAxisTitleFontSize: 10, valAxisTitleFontSize: 10, catAxisTitleFontFace: T.font, valAxisTitleFontFace: T.font });

// ============================================================================ 1. Title (dark, silicon-qubit hero)
{
  const s = pres.addSlide({ masterName: "TITLE", sectionTitle: "Intro" }); s._title = "Title";
  s.background = { color: "111A22" };
  img(s, "O_hero_title.png", 3.95, 0.0, 6.05, 5.625, "right", "middle");
  text(s, "EE143 · DEVICE PROFILE", 0.5, 0.75, 4.0, 0.25, { fontSize: 10, bold: true, color: "5FC9C9", charSpacing: 2 });
  text(s, "Atom-by-Atom Silicon", 0.5, 1.05, 5.4, 0.6, { fontSize: 32, bold: true, color: "FFFFFF" });
  text(s, "Building Quantum Processors from Single Dopant Atoms", 0.5, 1.68, 4.3, 0.85, { fontSize: 19, color: "E6ECF1" });
  text(s, "Device profile: STM-patterned P and As dopant qubits, featuring the work of Neil J. Curson (UCL)", 0.5, 2.65, 4.0, 0.7, { fontSize: 12.5, color: "9FB0BE" });
  [["As", T.As], ["P", T.P]].forEach(([lab, col], i) => {
    s.addShape(pres.shapes.OVAL, { x: 0.52 + i * 1.05, y: 3.55, w: 0.16, h: 0.16, fill: { color: col }, line: { color: col, width: 0 } });
    text(s, lab === "As" ? "arsenic" : "phosphorus", 0.74 + i * 1.05, 3.5, 0.95, 0.26, { fontSize: 10.5, color: "C9D3DC" });
  });
  text(s, "Hanah Rahman · EE143 · Fall 2026", 0.5, 4.05, 4.2, 0.3, { fontSize: 13, bold: true, color: "FFFFFF" });
  text(s, "AI disclosure: AI tools were used to draft and lay out these slides and to code the original diagrams.", 0.5, 4.55, 3.7, 0.45, { fontSize: 9, color: "8C9AA6" });
  text(s, "Cover: original 3D render of a diamond-cubic Si crystal with a 2×2 As register (teal), one P donor (orange) and an STM tip.", 0.5, 5.12, 3.7, 0.35, { fontSize: 8, color: "8C9AA6" });
  notes(s, "Hi everyone. Today's device is a quantum processor where every qubit is a single dopant atom, put into silicon one at a time with a scanning tunnelling microscope. That's the picture behind me: a silicon crystal, four arsenic atoms in a 2×2 register, one phosphorus, and the STM tip that places them. You already know every ingredient from EE143: a clean surface, a resist, lithography, gas-phase doping, an activation anneal, epitaxy, etch and metal. The twist is that the resist is one atom thick and the 'implant' is one molecule. I'll follow the work of Neil Curson at UCL through the process. Likely question: is the picture real data? No, it's my 3D render of the real crystal structure; every micrograph after this is published data, credited on the slide.");
}
// ============================================================================ Agenda (story in four acts)
{
  const s = newSlide("TITLE_ONLY", "The story in four acts", "Intro");
  const acts = [
    ["1", "Why single atoms?", "A donor is a natural qubit, but only if you can place it exactly.", "O2_surface_H.png", T.ink],
    ["2", "How is it built?", "Eleven steps, each one an EE143 module shrunk to one atom.", "O2_surface_window.png", T.ink],
    ["3", "Does it work?", "Buried layers conduct, single atoms switch, arsenic fixes yield, processors run.", "F1_stock2024_fig1_4x4.png", T.As],
    ["4", "How does it scale?", "Throughput is the wall; EUV and our prototype show a way through.", "O_prototype3d.png", T.ink]];
  const cw = 2.15, gap = 0.12;
  acts.forEach(([n, h, d, im, col], i) => {
    const x = 0.5 + i * (cw + gap);
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.05, w: cw, h: 3.75, fill: { color: T.panel }, line: { color: T.panel, width: 0 } });
    img(s, im, x + 0.1, 1.15, cw - 0.2, 1.45, "center", "middle");
    s.addShape(pres.shapes.OVAL, { x: x + 0.12, y: 2.75, w: 0.42, h: 0.42, fill: { color: col }, line: { color: col, width: 0 } });
    text(s, n, x + 0.12, 2.81, 0.42, 0.3, { fontSize: 14, bold: true, color: "FFFFFF", align: "center" });
    text(s, h, x + 0.65, 2.79, cw - 0.75, 0.4, { fontSize: 14, bold: true });
    text(s, d, x + 0.15, 3.3, cw - 0.3, 1.4, { fontSize: 12, color: T.muted });
  });
  src(s, "Roadmap of this talk");
  notes(s, "Here's the plan, in four acts. Act one: why anyone would want a single atom as a qubit, and why the obvious tool, ion implantation, can't place one. Act two: how the device is actually built, eleven steps that each map onto an EE143 module, just shrunk to one atom. Act three: does it work? We'll check the buried wiring, the first single-atom devices, the yield problem and Curson's arsenic fix, and today's processors. Act four: the throughput wall, how EUV could get around it, and a prototype we designed from the papers. Keep one question in mind the whole time: how do you put exactly one atom exactly where you want it?");
}
// ============================================================================ 4. Why a donor
{
  const s = newSlide("TWO_FIG", "A single donor atom is a natural qubit", "Act 1");
  bullets(s, ["P nucleus (I = 1/2) + its electron = 4 spin states", "Electron Bohr radius ~2 nm; exchange depends on exact donor position, so atomic precision matters", "In ²⁸Si: coherence up to 35.6 s and single-qubit gates close to 99.99% (ion-implanted donors)"], 0.5, 1.1, 3.6, 2.7, 14);
  img(s, "O_levels_4state.png", 0.6, 3.3, 2.2, 1.75, "left");
  caption(s, "Spin levels, schematic (ours)", 2.8, 4.6, 1.3, 0.45);
  const b = img(s, "F5_schofield2025_s32_fig1.png", 4.4, 1.05, 5.1, 3.6, "center");
  caption(s, "Donor control and readout: SET charge sensor + on-chip microwave antenna (a); ion-implanted device (b). Reproduced from Schofield et al., Nano Futures 9, 012001 (2025) §3.2 Fig. 1, CC BY 4.0", 4.4, b.y + b.h + 0.04, 5.1, 0.45);
  src(s, "Schofield2025 §1, §3.2");
  notes(s, "Why bother with single atoms? A phosphorus donor brings two spins for free: its nucleus with spin one-half and its bound electron. Two times two gives four states, shown in my sketch on the left; we drive the electron with ESR and the nucleus with NMR. On the right is how you read it out: a single-electron transistor senses charge, spin-dependent tunnelling turns spin into charge, and an on-chip antenna delivers the microwaves. In silicon-28, coherence reaches 35.6 seconds, which is enormous for a qubit. The catch is the electron's Bohr radius of about 2 nm: the exchange coupling between two donors depends on their exact lattice positions. That's why fabrication precision is the whole game. Likely question: what's ESR? Electron spin resonance, flipping the electron with microwaves.");
}

// ============================================================================ 4b. Quantum coupling to scale
{
  const s = newSlide("TWO_FIG", "Why one site matters: wavefunction overlap", "Act 1");
  const a = img(s, "O_wavefunction_scale.png", 0.4, 1.0, 6.3, 2.75, "left");
  caption(s, "To scale: two P donors 13.0 nm apart over the Si(001) surface lattice, hydrogenic envelope |ψ|² ∝ e^(−2r/a_B) with a_B ≈ 2 nm (our model; inputs He2019, Schofield2025 §3.2, Stock2024).", 0.5, a.y + a.h + 0.04, 6.2, 0.5);
  const b = img(s, "O_bloch.png", 6.9, 0.95, 2.6, 2.45, "center");
  caption(s, "Each spin is a qubit: |ψ⟩ = α|0⟩ + β|1⟩ on the Bloch sphere (schematic).", 6.9, b.y + b.h + 0.02, 2.6, 0.45);
  bullets(s, ["Qubits interact through exchange, set by how their electron clouds overlap", "Exchange depends strongly on exact donor position (valley oscillations), so a one-site error changes the gate"], 0.5, 4.3, 9.0, 0.85, 13);
  src(s, "Schofield2025 §3.2; He2019; Stock2024. Envelope plot is our model, not a full valley calculation");
  notes(s, "This is the quantum reason the whole talk is about placement. Each donor's electron is a cloud about 2 nanometres in radius; drawn to scale, 13 nanometres apart as in the He 2019 gate, over the real surface lattice. The colour is log scale: the clouds barely touch in the middle, and that faint overlap is what sets the exchange coupling J, the interaction a two-qubit gate uses. The roadmap says exchange depends strongly on the exact donor position because of valley oscillations, so moving one donor by one site changes the gate. On the right, each spin is a qubit on the Bloch sphere. Likely question: is your plot exact? It's a simple hydrogen-like envelope; real donors add valley oscillations on top.");
}
// ============================================================================ 5. Why not ion implantation?
{
  const s = newSlide("TABLE", "The problem: implantation can't place one atom", "Act 1");
  const H = (t) => ({ text: t, options: { bold: true, color: T.ink, fill: { color: "F2F4F6" } } });
  const rows = [[H(""), H("Ion implantation"), H("STM H-resist lithography")],
    [{ text: "Placement", options: { bold: true } }, "Sub-100 nm routine; Kane-type devices need ≈15 nm", "±1 atomic spacing"],
    [{ text: "One dopant per site", options: { bold: true } }, "36% (Poisson, without ion counting)", { text: "97 ± 2% (As, 4-site window)", options: { color: T.As, bold: true } }],
    [{ text: "Best ion counting", options: { bold: true } }, "99.85 ± 0.02% detection confidence, 14 keV ³¹P⁺; yield limit 98.1% (Jakob2022)", "Placement still set by ion straggling, not by the lattice"]];
  s.addTable(rows, { x: 0.5, y: 1.0, w: 5.0, colW: [1.15, 2.05, 1.8], fontFace: T.font, fontSize: 10.5, color: T.ink, valign: "middle", rowH: [0.36, 0.6, 0.5, 0.62], border: { type: "solid", pt: 0.75, color: "E0E4E8" } });
  s.addChart(pres.charts.BAR, [{ name: "Probability", labels: ["0", "1", "2", "3", "≥4"], values: [36.8, 36.8, 18.4, 6.1, 1.9] }],
    Object.assign(chartBase(), { x: 0.4, y: 3.2, w: 5.1, h: 1.95, barDir: "col", chartColors: ["8C96A0"], showValue: true, dataLabelColor: T.ink, dataLabelFontSize: 9, dataLabelFormatCode: "0.0",
      title: "Ions per site at mean 1 ion/site: exactly one only ~36%", valAxisHidden: true, valGridLine: { style: "none" }, showLegend: false, catAxisTitle: "ions landing in one site (Poisson, our calc.)", showCatAxisTitle: true, barGapWidthPct: 60 }));
  const b = img(s, "F7_schofield2025_s24_fig2.jpg", 6.0, 1.05, 3.4, 3.55, "center");
  caption(s, "Deterministic single-ion implanter column. Reproduced from Schofield et al., Nano Futures 9, 012001 (2025) §2.4 Fig. 2, CC BY 4.0", 5.8, b.y + b.h + 0.04, 3.8, 0.45);
  src(s, "Schofield2025 §1, §2.4; Stock2024; Jakob2022. Poisson bars: P(k)=e⁻¹/k!, our calculation of the 36% in Schofield2025");
  notes(s, "This is the obvious EE143 question: we implant dopants every day, so why an STM? Two reasons in the table. Placement: implantation is routinely sub-100 nm, but a Kane-type device needs about 15 nm, and the STM gives plus or minus one atomic spacing. Second, counting: ions arrive randomly. If you aim for one ion per site on average, Poisson statistics say only 36% of sites get exactly one; the bar chart is that distribution, which I calculated. Compare that 36% with the 97% Curson's group gets for arsenic. The bottom row is the strongest rival: Jakob 2022 detect each 14 keV phosphorus ion with 99.85% confidence, but where the ion stops is still set by random straggling, not by the lattice.");
}

// ============================================================================ 2. Device at a glance
{
  const s = newSlide("FIG_TEXT", "The answer: write the device atom by atom", "Act 1");
  const rows = [["Host", "Si(001); ²⁸Si for qubit devices"], ["Dopants", "P (from PH₃) or As (from AsH₃)"], ["Placement", "±1 atomic spacing (±0.384 nm)"], ["δ-layer leads", "≈10¹⁴ cm⁻², <1 nm thick"], ["Activation", "100% of placed P (Reiner2024)"], ["Measured at", "millikelvin temperatures"]];
  const tbl = rows.map(([k, v]) => [{ text: k, options: { bold: true, color: T.ink } }, { text: v, options: { color: T.ink } }]);
  s.addTable(tbl, { x: 0.5, y: 1.05, w: 4.1, colW: [1.25, 2.85], fontFace: T.font, fontSize: 12, rowH: 0.46, valign: "middle",
    border: { type: "solid", pt: 0.75, color: "E0E4E8" }, fill: { color: "FFFFFF" } });
  const kb = img(s, "O1_kane_crosssection.png", 4.85, 1.1, 4.7, 2.6, "center");
  caption(s, "Kane architecture, x to scale: ³¹P donors under A-gates, J-gates between, donors ≈10 nm apart (Kane2000: \"of order 100 Å\"; UNSW papers restate 20 nm: OBrien2001, Schofield2003), a_B ≈ 2 nm. Original drawing after Kane1998/Kane2000.", 4.85, kb.y + kb.h + 0.05, 4.7, 0.65);
  callout(s, "EE143 lens: a doped-Si device whose 'diffusions' are single atoms and whose wiring is δ-doped silicon.", 0.5, 4.35, 4.1, 0.65, { fontSize: 11.5 });
  src(s, "Schofield2025 §3.2, §5.4; Stock2024; Constantinou2023; Reiner2024 (Table 1); Kane1998; Kane2000; OBrien2001");
  notes(s, "Here's the spec sheet. The substrate is ordinary Si(001), switched to silicon-28 for the qubit devices. The dopants are phosphorus, from phosphine, or arsenic, from arsine. The headline is placement: plus or minus one atomic spacing. The wires are δ-layers, sheets around 10^14 per square centimetre that are less than a nanometre thick. Everything is measured at millikelvin. On the right is the original idea, Kane 1998: phosphorus-31 donors under A-gates, with J-gates in between. The number to remember: ±1 atomic spacing. Likely question: why silicon-28? The record results in this talk, 35.6 s coherence and the 2025 processors, were all in ²⁸Si; later I'll flag why that matters when comparing fidelities.");
}

// ============================================================================ 3. Timeline (O9)
function timeline(s, x, y, w, events, small = false) {
  const y0 = y + (small ? 0.35 : 1.15);
  s.addShape(pres.shapes.LINE, { x, y: y0, w, h: 0, line: { color: "9AA3AC", width: 1.5 } });
  const yr0 = 1993, yr1 = 2026;
  events.forEach((e, i) => {
    const cx = x + ((e.year - yr0) / (yr1 - yr0)) * w; const col = e.curson ? T.As : T.ink;
    s.addShape(pres.shapes.OVAL, { x: cx - 0.07, y: y0 - 0.07, w: 0.14, h: 0.14, fill: { color: col }, line: { color: "FFFFFF", width: 1 } });
    if (small) { text(s, String(e.year), cx - 0.3, i % 2 ? y0 - 0.3 : y0 + 0.1, 0.6, 0.2, { fontSize: 9, color: col, align: "center" }); return; }
    const up = e.up !== undefined ? e.up : i % 2 === 0; const bw = e.w || 1.35;
    const ty = up ? y0 - 1.05 : y0 + 0.18;
    s.addShape(pres.shapes.LINE, { x: cx, y: up ? y0 - 0.25 : y0 + 0.07, w: 0, h: 0.18, line: { color: "C3CAD1", width: 1 } });
    text(s, [{ text: String(e.year) + "\n", options: { bold: true, color: col, fontSize: 12 } }, { text: e.label, options: { color: col, fontSize: 10.5 } }],
      cx - bw / 2 + (e.dx || 0), ty, bw, 0.85, { align: "center", valign: up ? "bottom" : "top" });
  });
}
const EVENTS = [
  { year: 1994, label: "H depassivation lithography", up: true, w: 1.35 },
  { year: 1998, label: "Kane proposal: ³¹P spin qubits", up: false, w: 1.4 },
  { year: 2003, label: "Single P atoms placed", curson: true, up: true },
  { year: 2012, label: "Single-atom transistor", up: false },
  { year: 2019, label: "Donor 2-qubit gate; 3D device", up: true, w: 1.3, dx: -0.35 },
  { year: 2020, label: "Arsenic patterned by STM", curson: true, up: false, w: 1.3, dx: -0.3 },
  { year: 2024, label: "97% single-As yield; EUV H removal", curson: true, up: true, w: 1.45, dx: 0.15 },
  { year: 2025, label: "4-qubit Grover; 11-qubit processor", up: false, w: 1.45, dx: 0.35 },
];
{
  const s = newSlide("TITLE_ONLY", "30 years: from one H atom to 11 qubits", "Act 1");
  timeline(s, 0.75, 1.55, 8.4, EVENTS);
  s.addShape(pres.shapes.OVAL, { x: 0.6, y: 4.62, w: 0.14, h: 0.14, fill: { color: T.As }, line: { color: T.As, width: 0 } });
  text(s, "Curson is an author (teal)", 0.82, 4.56, 2.6, 0.25, { fontSize: 11, color: T.muted });
  callout(s, "Each step reused the same EE143 recipe: passivate → pattern → dose → anneal → cap.", 3.6, 4.45, 5.9, 0.5, { fontSize: 12 });
  src(s, "Lyding1994; Kane1998; Schofield2003; Fuechsle2012; He2019; Koch2019; Stock2020; Stock2024; Constantinou2024; Thorvaldson2025; Edlbauer2025");
  notes(s, "Thirty years in one line. 1994: Lyding shows an STM tip can pull hydrogen off silicon, which gives us lithography. 1998: Kane proposes phosphorus nuclear spins as qubits. 2003: the first single phosphorus atoms placed on purpose, Curson among the authors. 2012: a transistor whose active region is one atom. 2019: the first two-qubit gate between donors and a 3D stacked device. 2020 and 2024: Curson's group adds arsenic and pushes single-atom yield to 97%, and also shows EUV light can do the hydrogen removal. 2025: a four-qubit Grover search and an 11-qubit processor. Likely question: what changed in 2012? The atom became a working device, wired up and measured as a transistor, not just imaged.");
}

// ============================================================================ 6. Neil J. Curson
{
  const s = newSlide("TITLE_ONLY", "The researcher: Neil J. Curson (UCL)", "Act 1");
  text(s, "London Centre for Nanotechnology and Dept. of Electronic & Electrical Engineering, UCL", 0.5, 0.95, 9.0, 0.3, { fontSize: 13, color: T.muted });
  const cards = [
    { y: 2003, t: "Co-author: first single P atoms placed", k: "Schofield2003" },
    { y: 2020, t: "Corresponding author: arsenic patterned by STM", k: "Stock2020" },
    { y: 2023, t: "As in germanium · ARPES of δ-layers · X-ray imaging of buried devices", k: "Hofmann2023; Constantinou2023; DAnna2023" },
    { y: 2024, t: "Corresponding author: 97% single-As yield · EUV H desorption", k: "Stock2024; Constantinou2024" },
    { y: 2025, t: "Guest editor: roadmap on atomic-scale devices", k: "Schofield2025" }];
  const x0 = 0.5, cw = 1.72, gap = 0.1;
  s.addShape(pres.shapes.LINE, { x: 0.6, y: 1.85, w: 8.8, h: 0, line: { color: "9AA3AC", width: 1.5 } });
  cards.forEach((c, i) => {
    const x = x0 + i * (cw + gap);
    s.addShape(pres.shapes.OVAL, { x: x + cw / 2 - 0.09, y: 1.76, w: 0.18, h: 0.18, fill: { color: T.As }, line: { color: "FFFFFF", width: 1 } });
    text(s, String(c.y), x, 1.4, cw, 0.3, { fontSize: 14, bold: true, color: T.As, align: "center" });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 2.1, w: cw, h: 1.75, fill: { color: T.panel }, line: { color: T.panel, width: 0 } });
    text(s, c.t, x + 0.1, 2.2, cw - 0.2, 1.15, { fontSize: 12 });
    text(s, c.k, x + 0.1, 3.38, cw - 0.2, 0.42, { fontSize: 9, color: T.muted });
  });
  callout(s, "Theme of his work: new dopant chemistry (As, Bi, Ge hosts), new ways to see buried atoms, and a path to scale (EUV).", 0.5, 4.15, 9.0, 0.55, { fontSize: 13 });
  src(s, "REFERENCES.md, Neil J. Curson's papers table (authorship verified against Crossref)");
  notes(s, "A quick profile of the researcher. Neil Curson is at the London Centre for Nanotechnology and UCL's electrical engineering department. In 2003 he co-authored the paper that first placed single phosphorus atoms. In 2020 his group, with him as corresponding author, showed arsenic could be patterned the same way. In 2023 the group took arsenic into germanium, imaged δ-layers in momentum space with X-ray ARPES, and mapped a buried device with X-ray fluorescence. 2024 is the big one: 97% single-atom yield for arsenic, plus the first hydrogen removal with EUV light. And he co-edited the 2025 roadmap I lean on throughout. Likely question: is he a physicist or an engineer? His appointment is in electronic and electrical engineering.");
}

// ============================================================================ 7. Process flow (O3)
{
  const s = newSlide("TITLE_ONLY", "The process: 11 steps, each an EE143 module", "Act 2");
  const steps = [
    ["1", "Clean + outgas", "600 °C, >8 h", "Wafer clean", "prep"], ["2", "Flash anneal", "≈1200 °C", "Thermal process", "prep"],
    ["3", "H-terminate", "330 °C atomic H", "Resist coat", "prep"], ["4", "STM lithography", "±1 atomic spacing", "E-beam litho", "litho"],
    ["5", "Dose PH₃ / AsH₃", "room temp.", "Gas-phase doping", "dose"], ["6", "Incorporate", "350 °C, 2 min", "Activation anneal", "incorp"],
    ["7", "Lock layer + RTA", "500 °C × 15 s", "RTA", "cap"], ["8", "Si overgrowth", "28 nm at 250 °C", "Epitaxy", "cap"],
    ["9", "Find device", "registration marks", "Alignment marks", "cap"], ["10", "Etch + Al contacts", "RIE holes, Al", "Etch + metallization", "contact"],
    ["11", "Measure", "millikelvin", "Hall / 4-point probe", "contact"]];
  const tw = 1.42, th = 1.78, gx = 0.1;
  steps.forEach((st, i) => {
    const row = i < 6 ? 0 : 1, col = row ? i - 6 : i;
    const x = 0.5 + col * (tw + gx) + (row ? (tw + gx) / 2 : 0), y = 1.05 + row * (th + 0.18);
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: tw, h: th, fill: { color: T.panel }, line: { color: T.panel, width: 0 } });
    img(s, `icon_${st[4]}.png`, x + 0.06, y + 0.06, tw - 0.12, 0.62, "center");
    text(s, [{ text: st[0] + "  ", options: { bold: true, color: T.muted } }, { text: st[1], options: { bold: true } }], x + 0.08, y + 0.72, tw - 0.12, 0.42, { fontSize: 11 });
    text(s, st[2], x + 0.08, y + 1.12, tw - 0.12, 0.25, { fontSize: 10, color: T.muted });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 0.08, y: y + 1.42, w: tw - 0.16, h: 0.26, rectRadius: 0.06, fill: { color: "FFFFFF" }, line: { color: "C3CAD1", width: 0.75 } });
    text(s, st[3], x + 0.1, y + 1.44, tw - 0.2, 0.22, { fontSize: 8.5, color: T.ink, align: "center", valign: "middle" });
  });
  text(s, "white tag = EE143 module", 0.55, 4.9, 3, 0.22, { fontSize: 9, color: T.muted });
  src(s, "Stock2020; Stock2024; DAnna2023 (steps 6–8); Constantinou2024 (step 3); Ruess2004; Fuechsle2012; Schofield2025 §5.4");
  notes(s, "Steps one to three make a perfect surface: clean and outgas at 600 °C for more than eight hours, flash to about 1200 °C, then cap every surface atom with hydrogen. Step four is the lithography. Five and six dose the precursor gas and anneal at 350 °C to lock the dopant into the lattice. Seven and eight bury it under epitaxial silicon. Nine to eleven are what you'd recognise from lab: find the device with alignment marks, etch holes, deposit aluminium, measure. White tags give the EE143 module. The number to remember: 350 °C, because the whole flow is designed around not losing the hydrogen resist. Likely question: is this in vacuum? The STM work runs below 5×10^-11 millibar.");
}

// ============================================================================ process slide helper
function processSlide(title, step, bulletsArr, xsecFile, rightFn, srcText, noteText) {
  const s = newSlide("PROCESS", title, "Act 2");
  tracker(s, step);
  bullets(s, bulletsArr, 0.5, 1.05, 4.05, 2.0, 14);
  img(s, xsecFile, 0.5, 3.05, 4.05, 1.65, "left", "bottom");
  legend(s, 0.5, 4.83);
  rightFn(s);
  src(s, srcText);
  notes(s, noteText);
  return s;
}

// ============================================================================ 8. Steps 1-3
processSlide("Steps 1–3 · Clean surface, 1-atom resist", "Steps 1–3 of 11",
  ["Clean: acetone/IPA, outgas >8 h at 600 °C, ≈1200 °C flashes, UHV <5×10⁻¹¹ mbar", "Resist: atomic H at 330 °C, 5×10⁻⁷ mbar, 5 min caps every surface Si", "EE143 hook: a resist coat one atom thick, no spin speed"],
  "xsec_prep.png", (s) => {
    const b = img(s, "O2_surface_H.png", 4.8, 1.0, 4.7, 3.6, "center");
    caption(s, "H-terminated Si(001): dimer rows (grey) each capped by H (blue). Original 3D render, geometry only.", 4.8, b.y + b.h + 0.04, 4.7, 0.4);
  }, "Stock2020; Stock2024; Constantinou2024 (H termination)",
  "Step one is about cleanliness, because a single stray atom is a defect at this scale. Samples get an acetone and IPA clean, then outgas for more than eight hours at 600 °C, then repeated flash anneals to about 1200 °C, all in ultra-high vacuum below 5×10^-11 millibar. Then atomic hydrogen goes onto every surface silicon. My render on the right shows the result: rows of silicon dimers, each atom capped by one hydrogen. That monolayer is the resist. Think of it as spin-coating, except the thickness is exactly one atom and perfectly uniform. The number to remember: one atom thick. Likely question: why flash to 1200 °C? It's the standard surface prep in these papers; the pack gives the recipe, not the mechanism.");

// ============================================================================ 9. Step 4
processSlide("Step 4 · Writing with the tip", "Step 4 of 11",
  ["Tip pulses strip H atom by atom: atom-wide lines at 3 V, 10 nA, 10 nm/s", "As windows: 3.5 V, 3000 pA, 50 nm/s, 2 dimers each, ≈12 lattice vectors (4.6 nm) apart", "EE143 hook: e-beam lithography where the resist is one atom thick"],
  "xsec_litho.png", (s) => {
    const a = img(s, "O2_surface_window.png", 4.8, 1.0, 4.7, 2.4, "center");
    caption(s, "Bare (tinted) Si sites form the windows. Original render.", 4.8, a.y + a.h, 4.7, 0.22);
    const b = img(s, "F4_schofield2025_s22_line.jpg", 4.8, 3.65, 4.7, 0.95, "center");
    caption(s, "HDL line written at 3 V, 10 nA. Reproduced from Schofield et al., Nano Futures 9, 012001 (2025) §2.2 Fig. 1 (Lyding, unpublished), CC BY 4.0", 4.8, b.y + b.h + 0.02, 4.7, 0.36);
  }, "Schofield2025 §2.2, §5.4; Stock2024",
  "Step four is the lithography. A voltage and current pulse from the STM tip knocks hydrogen off, exposing bare silicon where molecules can later stick. Atom-wide lines are written at 3 volts, 10 nanoamps, 10 nanometres per second; the STM image at the bottom is one of those lines. For arsenic single-atom windows Curson's group used 3.5 volts, 3000 picoamps, 50 nm per second. In my render, the orange patch is a six-site window for phosphorus and the teal patch a four-site window for arsenic. Placement is ±1 atomic spacing. So: e-beam lithography with a one-atom resist. Likely question: how do you know a window is right? The same STM images the surface after each step, as in Stock 2024's Figure 1.");

// ============================================================================ 10. Step 5
processSlide("Step 5 · Dosing: phosphine vs arsine", "Step 5 of 11",
  ["PH₃ breaks down stepwise, PH₂+H → PH+2H → P+3H, over minutes", "AsH₃ dissociates three orders of magnitude faster: tens of seconds", "Single-atom dose: AsH₃ at 5×10⁻⁹ mbar for 10 min; As saturates at 0.24 ± 0.04 ML"],
  "xsec_dose.png", (s) => {
    const a = img(s, "O2_surface_dose.png", 4.8, 1.0, 4.7, 2.45, "center");
    caption(s, "Fragments in each window. Original render.", 4.8, a.y + a.h, 4.7, 0.22);
    const b = img(s, "F2_stock2024_fig3_ae.png", 4.8, 3.7, 4.7, 0.95, "center");
    caption(s, "Window array before/after AsH₃. Reproduced from Stock et al., Adv. Mater. 36, 2312282 (2024) Fig. 3, CC BY 4.0", 4.8, b.y + b.h + 0.02, 4.7, 0.36);
  }, "Stock2020 (citing Wilson2004); Stock2024",
  "Now we expose the whole sample to a dopant gas, like a pre-deposition step, except molecules only stick in the bare windows. Phosphine is slow: it sheds hydrogens one at a time, PH2 plus H, then PH plus two H, then P plus three H, over minutes, and each fragment needs a free site. Arsine is the key difference: it dissociates three orders of magnitude faster, in tens of seconds, so it needs fewer sites and fewer things go wrong. The single-atom recipe is arsine at 5×10^-9 millibar for ten minutes. Arsenic saturates at 0.24 monolayer. Bottom right: a window array before and after dosing. Likely question: why does faster dissociation help? Arsenic gets by with a four-site window instead of six, so there are fewer ways to fail.");

// ============================================================================ 11. Step 6
processSlide("Step 6 · Incorporation anneal", "Step 6 of 11",
  ["350 °C anneal (1–2 min), below the 380 °C onset of H₂ desorption, so the H resist survives", "Each incorporated As ejects one Si atom", "So counting ejected Si counts the dopants: built-in metrology"],
  "xsec_incorp.png", (s) => {
    const b = img(s, "F11_stock2020_fig3_ad.png", 4.8, 1.0, 4.7, 3.3, "center");
    caption(s, "STM of a patterned square: H resist (a), lithography (b), AsH₃ dose (c), 350 °C anneal (d). Reproduced from Stock et al., ACS Nano 14, 3316 (2020) Fig. 3, CC BY 4.0", 4.8, b.y + b.h + 0.03, 4.7, 0.45);
  }, "Stock2020; Stock2024",
  "Step six is the drive-in, but tiny. A 350 °C anneal for one to two minutes lets the dopant swap into the top silicon layer. Why 350? Hydrogen starts leaving the surface at 380 °C, so we stay just under it and the resist survives everywhere else. On the right, real data: a patterned square through dose and anneal, with clean resist outside. There's a neat bonus: each arsenic that goes in kicks out one silicon atom, which sits on the surface as an adatom. Count adatoms and you've counted dopants, metrology for free. The number to remember: 350 °C versus 380 °C. Likely question: can you overshoot? Above 380 °C hydrogen starts to desorb, so the resist stops protecting the rest of the surface.");

// ============================================================================ 12. Steps 7-8
processSlide("Steps 7–8 · Burying the dopants", "Steps 7–8 of 11",
  ["Trade-off: low T keeps atoms in place, high T grows good crystal", "P: constant 250 °C (≈5 nm segregation, full activation)", "As: 2 nm at RT, 500 °C × 15 s RTA, 28 nm at 250 °C, 0.003 nm/s: layer 30 nm deep"],
  "xsec_cap.png", (s) => {
    const a = img(s, "O5_overgrowth_program.png", 4.7, 1.0, 4.8, 2.1, "center");
    caption(s, "Exact temperature programs: (a) Stock2020 Fig. 4e inset + text; (b) DAnna2023 Methods. Redrawn (ours).", 4.7, a.y + a.h + 0.02, 4.8, 0.25);
    const b = img(s, "F11_stock2020_fig4_sims.png", 4.7, 3.45, 1.65, 1.6, "left");
    caption(s, "SIMS: As stays sharp at 15 nm. Stock et al., ACS Nano 14, 3316 (2020) Fig. 4e, CC BY 4.0", b.x + b.w + 0.08, 3.45, 1.3, 1.3);
    callout(s, "EE143 link: a thermal-budget problem, like keeping a shallow junction shallow.", 7.95, 3.5, 1.55, 1.25, { fontSize: 10.5 });
  }, "Oberbeck2002; Stock2020; DAnna2023",
  "Steps seven and eight bury the dopants: a classic thermal-budget fight. Low temperature keeps atoms in place; high temperature gives good crystal. For phosphorus the answer is a constant 250 °C overgrowth, with about 5 nm of segregation and full activation. For arsenic, Curson's group grows a thin unheated locking layer, does a quick 500 °C, ten-second RTA, then continues epitaxy. A worked example: 2 nm unheated, 500 °C for 15 seconds, then 28 nm at 250 °C, so the layer sits 30 nm down. The SIMS profile on the right shows the arsenic still in a sharp spike. Likely question: why not grow everything hot? That's the trade-off on the slide: even at 250 °C phosphorus segregates about 5 nm.");

// ============================================================================ 13. Steps 9-11
processSlide("Steps 9–11 · Back to the outside world", "Steps 9–11 of 11",
  ["Relocate the buried device: markers + STM–SEM; KPFM alignment from nm to mm pads, 95% yield on >150 devices", "20 × 200 µm² Hall bars by optical litho + RIE; Al into holes etched through the δ-layer", "Transport at 1.8 K; qubits at millikelvin"],
  "xsec_contact.png", (s) => {
    const b = img(s, "F10_danna2023_fig2_maps.jpg", 4.8, 1.0, 4.7, 2.75, "center");
    caption(s, "X-ray fluorescence maps of a buried As Hall bar: Al contacts, Fe, and the As δ-layer itself. Reproduced from D'Anna et al., Adv. Electron. Mater. 9, 2201212 (2023) Fig. 2, CC BY 4.0", 4.8, b.y + b.h + 0.04, 4.7, 0.5);
  }, "Ruess2004; Namboodiri2024; DAnna2023",
  "The last three steps will feel most familiar. Once the dopants are buried, you can't see them with the STM, so you need alignment marks: registration markers plus a combined STM and SEM system to find the device again. Then it's normal cleanroom work. In the D'Anna paper, Hall bars were defined with optical lithography and reactive ion etching, and aluminium was deposited into holes etched down through the δ-layer, like a via. The maps on the right are X-ray fluorescence: you can see the aluminium pads, and in the right panel the arsenic δ-layer itself, buried 30 nm down. Then cool to millikelvin and measure. Likely question: does the X-ray beam damage the device? We'll see next slide that it barely moves the dopants.");

// ============================================================================ 14. Did it work?
{
  const s = newSlide("TWO_FIG", "Proof 1: the buried δ-layer conducts", "Act 3");
  bullets(s, ["As δ-layer: 1.6 ± 0.1 kΩ/□, 28 ± 1 cm²/V·s; 81% activation (88% at 560 °C); P layers reach 2.4×10¹⁴ cm⁻²", "ARPES and X-ray reflectometry: <1 nm thick (SIMS resolves only ~2 nm); As confines better than P", "XRF at ≈1 µm: <0.2 Å As motion, <3% loss of active dopants"], 0.5, 1.05, 4.1, 2.45, 13);
  callout(s, "EE143 check (our calc.):  Rₛ = 1/(q·Nₛ·μ)  →  Nₛ = 1/(1.6×10⁻¹⁹ C × 1600 Ω × 28 cm²/V·s) ≈ 1.4×10¹⁴ cm⁻², consistent with the ≈10¹⁴ cm⁻² sheets.", 0.5, 3.6, 4.1, 1.05, { fontSize: 12 });
  const b = img(s, "F9_constantinou2023_fig2.jpg", 4.8, 1.0, 4.7, 1.95, "center");
  caption(s, "ARPES Fermi surfaces of P (top) and As (bottom) δ-layers. Reproduced from Constantinou et al., Adv. Sci. 10, 2302101 (2023) Fig. 2, CC BY 4.0", 4.8, b.y + b.h + 0.03, 4.7, 0.4);
  const a = img(s, "F11_stock2020_fig4_transport.png", 4.8, 3.33, 1.8, 1.78, "left");
  caption(s, "Mobility, carrier density and Rₛ vs RTA temperature. Reproduced from Stock et al., ACS Nano 14, 3316 (2020) Fig. 4f,g, CC BY 4.0", a.x + a.w + 0.12, 3.6, 2.75, 0.9);
  src(s, "Stock2020; Constantinou2023; DAnna2023; DAnna2026. Nₛ check is our calculation from Stock2020's numbers");
  notes(s, "Did the process work? Three kinds of evidence. Electrical: an arsenic δ-layer measures 1.6 kilo-ohms per square with mobility of 28, and 81% of the arsenic is active after the 500 °C RTA, 88% at 560. EE143 check: Rs = 1/(q·Ns·μ) with 1.6 kΩ and 28 gives about 1.4×10^14 per square centimetre, right where it should be. Second, X-ray ARPES, top right, shows the layers are under a nanometre thick, and arsenic is tighter than phosphorus. Curson's newest paper, D'Anna 2026, uses X-ray reflectometry to show the chemical layer is also sub-nanometre, below SIMS's 2 nm resolution. Third, X-ray fluorescence imaging moved the arsenic less than 0.2 Å. Likely question: does the X-ray beam change the device? Less than 3% loss of active dopants.");
}

// ============================================================================ 15. Landmarks
{
  const s = newSlide("TWO_FIG", "Proof 2: one atom, then one transistor", "Act 3");
  const a = img(s, "O_landmark2003.png", 0.5, 1.05, 4.3, 3.3, "center");
  caption(s, "Schematic after Schofield2003 (original drawing)", 0.5, a.y + a.h + 0.04, 4.3, 0.25);
  const b = img(s, "O_landmark2012.png", 5.2, 1.05, 4.3, 3.3, "center");
  caption(s, "Schematic after Fuechsle2012 (original drawing)", 5.2, b.y + b.h + 0.04, 4.3, 0.25);
  text(s, "2012 device works at liquid-helium temperature; at mK its transport shows the atom's discrete levels.", 0.5, 4.75, 9.0, 0.35, { fontSize: 13 });
  src(s, "Schofield2003; Schofield2025 §4.1; Fuechsle2012");
  notes(s, "Two landmark results, which I've redrawn because the originals are paywalled. Left, 2003: the first deliberate placement of single phosphorus atoms, with about 1 nm accuracy. They put a pair about 12 nm apart on the same dimer row. That proved the lithography-plus-phosphine idea works for single atoms. Right, 2012: the single-atom transistor. One phosphorus atom sits between source, drain and gates, placed with one-lattice-site accuracy. It works at liquid-helium temperature, and at millikelvin its current shows the discrete energy levels of that one atom. Curson is on the 2003 paper. Likely question: why is a transistor from one atom useful? It proves you can wire up and electrically address a single placed dopant.");
}

// ============================================================================ 16. Yield problem (O6)
{
  const s = newSlide("TWO_FIG", "The catch: every site must work", "Act 3");
  const n = Array.from({ length: 16 }, (_, i) => i + 1);
  s.addChart(pres.charts.LINE, [
    { name: "P: 0.7ⁿ", labels: n.map(String), values: n.map((k) => Math.pow(0.7, k)) },
    { name: "As: 0.97ⁿ", labels: n.map(String), values: n.map((k) => Math.pow(0.97, k)) }],
    Object.assign(chartBase(), { x: 0.4, y: 0.95, w: 4.6, h: 3.05, chartColors: [T.P, T.As], lineSize: 2, lineDataSymbol: "none",
      title: "Array yield collapses unless per-site yield is near 1", showLegend: true, legendPos: "b", valAxisMaxVal: 1, valAxisMinVal: 0, valAxisLabelFormatCode: "0%",
      catAxisTitle: "atoms in array n", showCatAxisTitle: true, valAxisTitle: "array yield", showValAxisTitle: true }));
  text(s, "As 0.97¹⁶ ≈ 61%", 3.45, 1.62, 1.45, 0.25, { fontSize: 10, color: T.ink, bold: true });
  text(s, "P 0.7¹⁶ < 0.4%", 3.3, 2.65, 1.4, 0.25, { fontSize: 10, color: T.ink, bold: true });
  bullets(s, ["P fills an ideal 3-dimer window 63 ± 10% of the time (\"less than 70%\" in 6-site windows)", "Array yield 0.7ⁿ: 16 P atoms <0.4%; a ~50-donor array ~10⁻¹⁰. Modelled fix: dose hot (150 °C, >1 L)"], 0.5, 4.08, 4.6, 1.0, 11.5);
  const b = img(s, "O_yield_surface3d.png", 5.2, 1.0, 4.3, 3.3, "center");
  caption(s, "The same law in 3D: array yield pⁿ against per-site yield p and array size n (our model). Orange and teal lines are the measured P (0.7) and As (0.97) yields.", 5.2, b.y + b.h + 0.05, 4.3, 0.55);
  src(s, "Ivie2021 (incl. kinetic model); Stock2024; Schofield2025 §4.1. As curve and 3D surface are our model");
  notes(s, "Here's the problem that motivated Curson's arsenic work. Phosphorus lands in an ideal three-dimer window only 63 ± 10% of the time; Stock 2024 says less than 70% in six-site windows. That sounds fine until you need many sites at once. Array yield multiplies: 0.7 to the n. The orange line falls to under 0.4% by 16 atoms. The teal line is the same formula with arsenic's 97%, still about 61% at 16. On the right I simulated 4×4 arrays: the phosphorus row is full of red failures, the arsenic row has mostly perfect boxed arrays. This is the same logic as die yield in a fab: defects multiply. Number to remember: 0.7^16 < 0.4%. Likely question: can you repair a failed site? Possibly, by repeating lithography and dosing.");
}

// ============================================================================ 17. Arsenic fix
{
  const s = newSlide("TWO_FIG", "Curson's fix: arsenic in a 4-site window", "Act 3");
  bullets(s, ["97 ± 2% single-atom yield in a 4-site window: 1-in-4 lattice sites (≈0.6 nm²), 33% better precision than P", "First defect-free 2×2 single-dopant array in Si", "Iterative litho/dose cycles could push yield toward 100%"], 0.5, 1.05, 3.75, 2.2, 13);
  const a = img(s, "F3_schofield2025_s41_fig1.png", 4.45, 1.0, 5.05, 3.25, "center");
  caption(s, "2×2 As array steps and the ideal 4-site window. Reproduced from Schofield et al., Nano Futures 9, 012001 (2025) §4.1 Fig. 1, CC BY 4.0", 4.45, a.y + a.h + 0.04, 5.05, 0.4);
  const b = img(s, "F2_stock2024_fig3_stats.png", 0.5, 3.25, 3.0, 1.45, "left");
  caption(s, "Statistics behind the 97%. Stock et al., Adv. Mater. 36, 2312282 (2024) Fig. 3l, CC BY 4.0", 0.5, b.y + b.h + 0.03, 3.9, 0.35);
  src(s, "Stock2024; Schofield2025 §4.1");
  notes(s, "Because arsine dissociates so fast and needs fewer sites, a window of just four lattice sites, two dimers, is enough. In that window a single arsenic atom incorporates 97 ± 2% of the time. That window is one site in four, about 0.6 square nanometres, which is 33% better placement precision than phosphorus. With that yield they made the first defect-free 2×2 single-dopant array in silicon, shown in the top figure: lithography, dose, anneal, plus the ideal window sketch. The histogram at the bottom is the statistics behind the 97%. And if a site fails, you could repeat lithography and dosing to push yield toward 100%. Likely question: what about other dopants? Bismuth chemistry is on the next slide; the pack has no yield numbers for others.");
}

// ============================================================================ 18. Beyond Si:P
{
  const s = newSlide("TWO_FIG", "Beyond Si:P: new dopants, new hosts", "Act 3");
  bullets(s, ["Ge(001): As from arsine incorporates at room temperature, no anneal; H leaves by 330 °C", "Bi on Si(001): ~1 nm triphenyl-bismuth; phenyls detach ~140 °C, Bi incorporates ~360 °C"], 0.5, 1.05, 3.7, 2.4, 13.5);
  callout(s, "Why it matters: the same STM toolbox, with a different gas or substrate, gives a new qubit or device platform.", 0.5, 3.55, 3.7, 0.95, { fontSize: 12 });
  const a = img(s, "F12_hofmann2023_fig1a.jpg", 4.4, 1.0, 2.6, 2.5, "left");
  caption(s, "STM of arsine on Ge(001) at room temperature. Hofmann et al., Angew. Chem. Int. Ed. 62, e202213982 (2023) Fig. 1a, CC BY 4.0", 4.4, a.y + a.h + 0.04, 2.6, 0.75);
  const b = img(s, "F12b_lundgren2023_fig1.jpg", 7.1, 1.0, 2.4, 2.5, "right");
  caption(s, "Triphenyl-bismuth on Si(001). Lundgren et al., J. Phys. Chem. C 127, 16433 (2023), CC BY 4.0", 7.1, b.y + b.h + 0.04, 2.4, 0.75);
  src(s, "Hofmann2023; Lundgren2023");
  notes(s, "Two side projects from Curson's group show the method generalises. First, germanium: arsenic from arsine goes into the germanium surface at room temperature with no anneal at all, the STM image on the left. That removes a thermal step entirely. Second, bismuth: they studied how a triphenyl-bismuth molecule sticks to and breaks apart on Si(001), on the right, as a route to ultra-shallow bismuth doping. The point for us: the toolbox is the same, a hydrogen resist, a tip and a gas. Change the gas or the substrate and you get a different device platform. Likely question: why germanium? It's another group-IV host used in quantum devices; the pack doesn't go further, so I won't either.");
}

// ============================================================================ 19. Processors
{
  const s = newSlide("TWO_FIG", "The payoff: from devices to processors", "Act 3");
  bullets(s, ["2019: ≈800 ps exchange gate (natural Si); 3D device, 97.9% readout, <5 nm layer alignment", "2025, 4 qubits: 3P + 1 e⁻, 45 nm ²⁸Si cap, 1.45 T, 15 mK; CZ 99.32–99.65%, Grover search", "2025, 11 qubits: 4P + 5P registers 13(1) nm apart, SET 17 nm away, ~1.39 T; Bell 99.5% local, 97.0% across"], 0.5, 1.05, 3.75, 3.0, 12);
  callout(s, "Caveat: 2019 used natural Si and electron spins; 2025 used ²⁸Si and nuclear-spin registers, so don't compare fidelities directly.", 0.5, 4.05, 3.75, 0.85, { fontSize: 11 });
  const c = img(s, "F14_edlbauer2025_fig1ab.png", 4.4, 1.0, 5.1, 2.35, "center");
  caption(s, "11-qubit processor: connectivity and STM of the 4P and 5P registers. Reproduced from Edlbauer et al., Nature 648, 569 (2025) Fig. 1a,b, CC BY 4.0", 4.4, c.y + c.h + 0.03, 5.1, 0.4);
  const b = img(s, "F13_thorvaldson2025_fig4b.png", 4.4, 3.7, 2.4, 1.42, "left");
  caption(s, "Grover output, marked state ⇓⇓⇓: 98.87% of ideal. Reproduced from Thorvaldson et al., Nat. Nanotechnol. 20, 472 (2025) Fig. 4b, CC BY 4.0", b.x + b.w + 0.12, 3.85, 2.8, 0.9);
  src(s, "He2019; Koch2019; Thorvaldson2025 (Methods); Edlbauer2025 (Fig. 1 caption, SI)");
  notes(s, "Now the payoff: processors. 2019 gave the first exchange gate between two phosphorus donor electrons, about 800 picoseconds, and a 3D device with stacked dopant layers aligned within 5 nm. In 2025 a four-qubit processor, three phosphorus nuclei plus one electron in silicon-28, ran Grover's search; the bar chart shows the marked state found 93.46% of the time, 98.87% of ideal. And an 11-qubit processor linked a four-phosphorus and a five-phosphorus register by exchange: Bell states 99.5% within a register, 97% across. Please read the caveat box: 2019 used natural silicon and electron spins, 2025 used silicon-28 and nuclear spins, so the numbers aren't apples to apples. Likely question: are these Curson's devices? No, these are context papers from other groups using the same fabrication.");
}

// ============================================================================ Q1. Spin Hamiltonian, measured
{
  const s = newSlide("TWO_FIG", "The qubit as a spin Hamiltonian, and its spectrum", "Act 3");
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.0, w: 4.3, h: 0.95, fill: { color: "111A22" }, line: { color: "111A22", width: 0 } });
  text(s, [{ text: "H = γₑ B·S + Σᵢ γₙ B·Iᵢ + Σᵢ S·Āᵢ(E)·Iᵢ", options: { fontSize: 15, color: "FFFFFF", bold: true, breakLine: true } },
    { text: "electron Zeeman + nuclear Zeeman + hyperfine (ħ = 1), N-donor register", options: { fontSize: 9.5, color: "9FB0BE" } }], 0.65, 1.1, 4.0, 0.8, { fontFace: "Arial" });
  bullets(s, ["3 P nuclei share 1 electron: A₁ = 6, A₂ = 68, A₃ = 103 MHz; B = 1.45 T, 15 mK", "2³ = 8 ESR lines: the electron's frequency reads out the nuclear register", "Field-tunable hyperfine Āᵢ(E): gates address each nucleus"], 0.5, 2.05, 4.3, 1.6, 11.5);
  const a = img(s, "F24_thorvaldson2025_fig1bc.png", 5.0, 0.95, 4.5, 2.25, "center");
  caption(s, "Measured ESR: one peak per nuclear configuration. Thorvaldson et al., Nat. Nanotechnol. 20, 472 (2025) Fig. 1b, CC BY 4.0", 5.0, a.y + a.h + 0.02, 4.5, 0.36);
  const c = img(s, "C_coherence_times.png", 5.0, 3.55, 4.5, 1.6, "center");
  caption(s, "Right: our chart of published T₂* values; 35.6 s is the best donor coherence (implanted donors, ²⁸Si).", 0.5, 4.1, 4.3, 0.45);
  src(s, "Hamiltonian: Reiner2024 Eq. 1; Thorvaldson2025 (A, B, T, T₂*); Reiner2024 (T₂*); Schofield2025 §3.2");
  notes(s, "Zooming into that four-qubit processor, here's the physicist's view. Reiner 2024 writes the register's Hamiltonian: electron Zeeman, nuclear Zeeman, and the hyperfine coupling between the shared electron and each phosphorus nucleus. In Thorvaldson's processor, three nuclei share one electron, with hyperfine couplings of 6, 68 and 103 megahertz, at 1.45 tesla and 15 millikelvin. Because each nucleus shifts the electron's resonance, the ESR spectrum on the right splits into two-cubed, eight peaks, one per nuclear configuration. So reading the electron reads the register. The chart shows why nuclei are the memory: electron dephasing in tens of microseconds, nuclei in milliseconds, and the best donor coherence reaches 35.6 seconds. Likely question: why does A depend on E? Gate fields distort the electron wavefunction, tuning its overlap with each nucleus.");
}

// ============================================================================ Q2. Entanglement by tomography
{
  const s = newSlide("TWO_FIG", "Entanglement, measured by full state tomography", "Act 3");
  const a = img(s, "F24_thorvaldson2025_fig2bd.png", 0.4, 0.95, 5.7, 2.2, "left");
  caption(s, "Bell-state density matrices for each nuclear pair, with fidelities. Thorvaldson2025 Fig. 2b–d, CC BY 4.0", 0.45, a.y + a.h + 0.02, 5.6, 0.25);
  const g = img(s, "F24_thorvaldson2025_fig3b.png", 6.25, 0.95, 3.25, 2.35, "center");
  caption(s, "Three-qubit GHZ state, F = 96.2 ± 0.5%. Thorvaldson2025 Fig. 3b, CC BY 4.0", 6.25, g.y + g.h + 0.02, 3.25, 0.4);
  const c = img(s, "F24_thorvaldson2025_fig4a.png", 0.4, 3.5, 5.7, 1.15, "left");
  caption(s, "Grover search on three nuclear spins: oracle (red), diffusion operator (blue), r = 2. Thorvaldson2025 Fig. 4a, CC BY 4.0", 0.45, c.y + c.h + 0.02, 5.6, 0.3);
  bullets(s, ["Bell fidelities 97.5 ± 0.3, 97.7 ± 0.4, 96.8 ± 0.4%", "Grover finds the marked state at 98.87% of ideal"], 6.25, 3.75, 3.25, 1.2, 11.5);
  src(s, "Thorvaldson2025 (²⁸Si, 3P + 1 e⁻ register; fidelities include SPAM for GHZ)");
  notes(s, "Here is the quantum evidence, straight from the 2025 four-qubit paper. Top left: they reconstruct the full density matrix of a Bell state for each pair of phosphorus nuclei. The four tall bars in the corners are exactly what a maximally entangled state looks like; everything else should be zero. Fidelities are about 97% for every pair. Right: a three-qubit GHZ state, all three nuclei entangled, 96.2% fidelity including state preparation and measurement errors. Bottom: the Grover circuit they ran, an oracle that marks one of eight states and a diffusion operator, repeated twice; it found the marked state at 98.87% of the ideal probability. Likely question: what is tomography? Measuring many copies in different bases to rebuild the full quantum state.");
}

// ============================================================================ 20. Simulator
{
  const s = newSlide("TWO_FIG", "Same atoms, new job: a quantum simulator", "Act 3");
  bullets(s, ["2022: 3×3 dopant dots, 2 ± 1 P each, spacing 4.1, 6.6, 10.7 ± 0.3 nm: metallic → Mott-insulating", "2022: 10-dot chain, ~25 P per dot, ≤10 nm apart, 40 nm cap at 0.125 nm/min: topological states"], 0.5, 1.05, 3.9, 2.6, 13);
  callout(s, "EE143 view: the 'circuit' here is a lattice of doped islands with in-plane δ-layer gates and leads.", 0.5, 3.7, 4.0, 0.8, { fontSize: 12 });
  const b = img(s, "F15_wang2022_fig1.jpg", 4.6, 1.0, 2.6, 3.0, "left");
  caption(s, "3×3 dopant-dot array. Wang et al., Nat. Commun. 13, 6824 (2022) Fig. 1, CC BY 4.0", 4.6, b.y + b.h + 0.04, 2.6, 0.6);
  const c = img(s, "F18_kiczynski2022_fig2a.png", 7.35, 1.0, 2.15, 2.0, "right");
  caption(s, "10-dot chain with 6 in-plane gates (STM, 50 nm scale in original). Kiczynski et al., Nature 606, 694 (2022) Fig. 2a, CC BY 4.0", 7.35, c.y + c.h + 0.04, 2.15, 0.85);
  src(s, "Wang2022; Kiczynski2022 (Methods)");
  notes(s, "Same fabrication, different job. Instead of qubits, this group wrote a 3×3 grid of tiny dopant-based quantum dots, shown in the schematic and the STM images on the right, with gates and leads written in the same layer. Electrons hopping between dots behave like electrons in a crystal, so the device simulates a material physics model directly in hardware. By changing the array, they tuned it from metallic behaviour toward a Mott insulator, where repulsion between electrons stops conduction. For us the interesting part is that it's a circuit made only of doped islands and δ-layer wiring. Likely question: why not simulate on a computer? Interacting-electron problems get exponentially hard as the lattice grows.");
}

// ============================================================================ 21. Throughput wall (O8)
{
  const s = newSlide("TWO_FIG", "The next wall: throughput", "Act 4");
  s.addChart(pres.charts.BAR, [{ name: "write speed (nm/s)", labels: ["STM, atom-wide lines", "STM, 2 V / hundreds of nA", "EUV (equivalent)"], values: [10, 1000, 1e14] }],
    Object.assign(chartBase(), { x: 0.4, y: 1.0, w: 5.2, h: 3.6, barDir: "bar", chartColors: ["5B6770"], valAxisLogScaleBase: 10, valAxisMinVal: 1, valAxisMaxVal: 1e15,
      valAxisLabelFormatCode: "0E+0", showValue: true, dataLabelFormatCode: "0E+0", dataLabelColor: T.ink, dataLabelFontSize: 10, dataLabelPosition: "outEnd",
      title: "EUV writes 11 orders of magnitude faster than STM", showLegend: false, valAxisTitle: "write speed (nm/s, log scale)", showValAxisTitle: true, catAxisLabelFontSize: 10 }));
  bullets(s, ["STM: 10–1000 nm/s; precise mode ≈100 atoms/s", "EUV: equivalent ≈10¹⁴ nm/s", "Even 10⁷ MEMS tips over a 300 mm wafer stay orders of magnitude too slow for CMOS volumes"], 5.85, 1.15, 3.65, 3.2, 14);
  src(s, "Schofield2025 §2.2, §5.4");
  notes(s, "Here's the wall. The STM writes at 10 nm per second for atom-wide lines, up to about 1000 nm per second at 2 volts and hundreds of nanoamps. In atomically precise mode that's around 100 atoms a second. EUV lithography, as used in CMOS fabs, writes at an equivalent of about 10^14 nm per second, eleven orders of magnitude faster. Note the log axis. People have proposed massively parallel MEMS tip arrays, up to ten million tips over a 300 mm wafer, and the roadmap says even that stays orders of magnitude too slow for CMOS volumes. The number to remember: eleven orders of magnitude. Likely question: so is this a dead end? Not for qubit cores, which is where the hybrid idea next comes in.");
}

// ============================================================================ 22. Scaling with EUV
{
  const s = newSlide("TWO_FIG", "Scaling: EUV photons instead of a tip", "Act 4");
  bullets(s, ["First H removal from Si(001):H with monochromatic EUV (109 eV), driven by secondary electrons", "Doses up to 18 000 J/cm²: several minutes per chip with 300 W sources", "Hybrid flow: STM for qubits, EUV for contacts, gates and wiring"], 0.5, 1.05, 3.8, 2.9, 14);
  const a = img(s, "F8_constantinou2024_fig5.png", 4.5, 1.0, 5.0, 2.95, "center");
  caption(s, "Proposed 4-stage UHV flow combining EUV and STM lithography. Reproduced from Constantinou et al., Nat. Commun. 15, 694 (2024) Fig. 5, CC BY 4.0", 4.5, a.y + a.h + 0.02, 5.0, 0.36);
  const b = img(s, "F6_schofield2025_s53_fig1_sem.jpg", 0.5, 3.95, 1.75, 1.1, "left");
  caption(s, "Resistless EUV lines, 75 nm half-pitch. Schofield2025 §5.3 Fig. 1 (adapted from Tseng2023), CC BY 4.0", 2.35, 4.3, 2.0, 0.75);
  src(s, "Constantinou2024; Schofield2025 §5.3; Tseng2023");
  notes(s, "Curson's 2024 Nature Communications paper showed for the first time that monochromatic EUV light at 109 eV removes hydrogen from the same silicon surface; it's mostly the secondary electrons from the silicon that do the work. It needs doses up to 18,000 joules per square centimetre, several minutes per chip with a 300 watt source, but it's parallel. The proposed flow on the right uses the same hydrogen resist: EUV patterns the big contacts and wiring, the STM writes the qubit cores, then dose and encapsulate as before. The SEM bottom-left shows resistless EUV lines at 75 nm half-pitch. Likely question: why not normal photoresist? The proposed flow keeps the hydrogen monolayer as the resist so every stage stays in UHV, and Tseng 2023 patterned with no photoresist at all.");
}

// ============================================================================ 23. Our prototype
{
  const s = newSlide("TWO_FIG", "Our prototype: a 2×2 arsenic register", "Act 4");
  const a = img(s, "O_prototype_layout.png", 0.4, 0.95, 5.9, 3.05, "left");
  caption(s, "Layout to scale (ours). Inputs: 2×2 pitch 4.6 nm and 4-site windows (Stock2024); SET 17 nm away, gates 146.6 nm apart (Edlbauer2025); buried 30 nm (DAnna2023).", 0.5, a.y + a.h + 0.03, 5.8, 0.45);
  const b = img(s, "O_prototype3d.png", 6.45, 0.95, 3.05, 2.6, "center");
  caption(s, "3D concept (not to scale): As δ-layer leads, Al vias, epitaxial cap.", 6.45, b.y + b.h + 0.02, 3.05, 0.4);
  bullets(s, ["Four single As atoms, one per 4-site window, ≈12 lattice vectors apart", "Design rule from pⁿ: 16 sites at p = 0.97 give ≈61% perfect arrays; at p = 0.7, ≈0.3%"], 0.5, 4.5, 9.0, 0.65, 12.5);
  src(s, "Our design. Inputs: Stock2024; Edlbauer2025; DAnna2023; Stock2020. Lead widths not given in the papers");
  notes(s, "To pull it together, here's a prototype we designed on paper, using only recipes from the papers. Four single arsenic atoms in four-site windows form a 2×2 register, with source, drain and two gates written as arsenic δ-layers in the same plane, buried under epitaxial silicon and reached by aluminium vias. The 3D surface on the right is our yield model, p to the n. It shows why the dopant choice decides the design: at arsenic's 0.97 a 16-site array comes out perfect about 61% of the time, at phosphorus's 0.7 about 0.3%. So the register size you can afford is set by chemistry, not by lithography resolution. Likely question: did you build it? No, it's a design exercise; the next slide is its traveler.");
}

// ============================================================================ 24. Prototype traveler
{
  const s = newSlide("TABLE", "Prototype traveler, mapped to EE143", "Act 4");
  const H = (t) => ({ text: t, options: { bold: true, fill: { color: "F2F4F6" } } });
  const rows = [[H("#"), H("Step (recipe from the papers)"), H("EE143 analogue")],
    ["1–2", "Acetone/IPA, outgas 600 °C >8 h; flash ≈1200 °C", "Clean + bake"],
    ["3", "Atomic H on Si(001): 1-atom resist", "Resist coat"],
    ["4", "STM: 3.5 V, 3000 pA, 50 nm/s, 4-site windows", "E-beam lithography"],
    ["5", "AsH₃, 5×10⁻⁹ mbar × 10 min", "Gas-phase pre-dep"],
    ["6", "350 °C, 1–2 min (H₂ leaves at 380 °C)", "Drive-in / activation"],
    ["7–8", "2 nm unheated; 500 °C × 15 s; 28 nm Si at 250 °C", "RTA + epitaxy"],
    ["9–10", "Markers + STM–SEM; optical litho, RIE, Al into holes", "Alignment, etch, metal"],
    ["11", "Hall bar at mK: Rₛ, μ, Nₛ", "Hall / 4-point probe"]];
  s.addTable(rows.map((r) => r.map((c) => (typeof c === "string" ? { text: c } : c))), { x: 0.5, y: 1.0, w: 5.6, colW: [0.5, 3.35, 1.75], fontFace: T.font, fontSize: 10.5, color: T.ink, valign: "middle", rowH: 0.42, border: { type: "solid", pt: 0.75, color: "E0E4E8" } });
  s.addChart(pres.charts.BAR, [{ name: "peak T (°C)", labels: ["Flash anneal", "Outgas", "RTA (As)", "Incorporation", "Overgrowth"], values: [1200, 600, 500, 350, 250] }],
    Object.assign(chartBase(), { x: 6.3, y: 1.0, w: 3.3, h: 3.8, barDir: "bar", chartColors: ["8C96A0"], showValue: true, dataLabelColor: T.ink, dataLabelFontSize: 10,
      title: "Thermal budget: after patterning, ≤500 °C", showLegend: false, valAxisHidden: true, valGridLine: { style: "none" }, catAxisOrientation: "maxMin", barGapWidthPct: 50 }));
  src(s, "Stock2020; Stock2024; DAnna2023; Ruess2004. Module mapping and thermal-budget chart are ours");
  notes(s, "And here's the traveler for that prototype, every step with its recipe and the EE143 module it maps to. It's a normal process flow: clean and bake, coat a resist, write it, pre-deposit dopant from the gas phase, drive in, RTA, epitaxy, alignment marks, etch, metal, and a Hall measurement. On the right I plotted each step's peak temperature. The two hot steps, outgas and the 1200 °C flash, happen before any patterning. After the pattern exists, nothing exceeds the 500 °C, 15-second RTA. That's the design principle: front-load the heat, then protect the atoms. Likely question: where does it break? Step 4 throughput, which is why the EUV hybrid matters.");
}

// ============================================================================ 25. Takeaways
{
  const s = newSlide("TITLE_ONLY", "Takeaways: one atom, exactly where you want it", "Wrap-up");
  const items = [["1", "Placing single atoms works.", "H-resist lithography + PH₃/AsH₃ + a 350 °C anneal gives ±1 atomic spacing."],
    ["2", "Arsenic brought single-atom yield to ~97%.", "Curson's 4-site window beats P's <70%; that's what makes arrays possible."],
    ["3", "Throughput is the next wall; EUV is the bridge.", "Same resist, photons for wiring, STM for qubits."]];
  items.forEach(([n, h, d], i) => {
    const y = 1.05 + i * 1.02;
    s.addShape(pres.shapes.OVAL, { x: 0.5, y, w: 0.55, h: 0.55, fill: { color: i === 1 ? T.As : T.ink }, line: { color: "FFFFFF", width: 0 } });
    text(s, n, 0.5, y + 0.1, 0.55, 0.35, { fontSize: 16, bold: true, color: "FFFFFF", align: "center" });
    text(s, h, 1.25, y, 8.2, 0.35, { fontSize: 17, bold: true });
    text(s, d, 1.25, y + 0.4, 8.2, 0.35, { fontSize: 13, color: T.muted });
  });
  timeline(s, 0.9, 4.15, 8.2, EVENTS, true);
  src(s, "Stock2020; Stock2024; Ivie2021; Constantinou2024; Schofield2025");
  notes(s, "Three things to take home. One: placing single atoms works, using the same steps you know, a resist, lithography, gas-phase doping and an anneal, at the scale of one atom. Two: arsenic brought single-atom yield to about 97%, versus under 70% for phosphorus, and because array yield multiplies, that's the difference between arrays that work and arrays that don't. That's Neil Curson's group's key result. Three: throughput is the next wall, eleven orders of magnitude behind EUV, and the bridge is to use EUV on the same hydrogen resist for everything except the qubit cores. Thanks, happy to take questions. Likely question: when will this be a product? The pack doesn't make that prediction, and I won't either.");
}

// ============================================================================ 26. References
const REFS = [
  ["Constantinou2023", "\"Momentum-space imaging of ultra-thin electron liquids in δ-doped silicon,\" Adv. Sci. 10, 2302101 (2023). doi:10.1002/advs.202302101"],
  ["Constantinou2024", "\"EUV-induced hydrogen desorption as a step towards large-scale silicon quantum device patterning,\" Nat. Commun. 15, 694 (2024). doi:10.1038/s41467-024-44790-6"],
  ["DAnna2023", "\"Non-destructive X-ray imaging of patterned delta-layer devices in silicon,\" Adv. Electron. Mater. 9, 2201212 (2023). doi:10.1002/aelm.202201212"],
  ["Edlbauer2025", "\"An 11-qubit atom processor in silicon,\" Nature 648, 569–575 (2025). doi:10.1038/s41586-025-09827-w"],
  ["Fuechsle2012", "\"A single-atom transistor,\" Nat. Nanotechnol. 7, 242–246 (2012). doi:10.1038/nnano.2012.21"],
  ["He2019", "\"A two-qubit gate between phosphorus donor electrons in silicon,\" Nature 571, 371–375 (2019). doi:10.1038/s41586-019-1381-2"],
  ["Hofmann2023", "\"Room temperature incorporation of arsenic atoms into the germanium (001) surface,\" Angew. Chem. Int. Ed. 62, e202213982 (2023). doi:10.1002/anie.202213982"],
  ["Ivie2021", "\"Impact of incorporation kinetics on device fabrication with atomic precision,\" Phys. Rev. Applied 16, 054037 (2021). doi:10.1103/PhysRevApplied.16.054037"],
  ["Kane1998", "\"A silicon-based nuclear spin quantum computer,\" Nature 393, 133–137 (1998). doi:10.1038/30156"],
  ["Koch2019", "\"Spin read-out in atomic qubits in an all-epitaxial three-dimensional transistor,\" Nat. Nanotechnol. 14, 137–140 (2019). doi:10.1038/s41565-018-0338-1"],
  ["Lundgren2023", "\"Adsorption and thermal decomposition of triphenyl bismuth on silicon (001),\" J. Phys. Chem. C 127, 16433 (2023). doi:10.1021/acs.jpcc.3c03916"],
  ["Lyding1994", "\"Nanoscale patterning and oxidation of H-passivated Si(100)-2×1 surfaces with an ultrahigh vacuum STM,\" Appl. Phys. Lett. 64, 2010–2012 (1994). doi:10.1063/1.111722"],
  ["Oberbeck2002", "\"Encapsulation of phosphorus dopants in silicon for the fabrication of a quantum computer,\" Appl. Phys. Lett. 81, 3197 (2002). doi:10.1063/1.1516859"],
  ["Ruess2004", "\"Toward atomic-scale device fabrication in silicon using scanning probe microscopy,\" Nano Lett. 4, 1969–1973 (2004). doi:10.1021/nl048808v"],
  ["Schofield2003", "\"Atomically precise placement of single dopants in Si,\" Phys. Rev. Lett. 91, 136104 (2003). doi:10.1103/PhysRevLett.91.136104"],
  ["Schofield2025", "\"Roadmap on atomic-scale semiconductor devices,\" Nano Futures 9, 012001 (2025). doi:10.1088/2399-1984/ada901"],
  ["Stock2020", "\"Atomic-scale patterning of arsenic in silicon by scanning tunneling microscopy,\" ACS Nano 14, 3316 (2020). doi:10.1021/acsnano.9b08943"],
  ["Stock2024", "\"Single-atom control of arsenic incorporation in silicon for high-yield artificial lattice fabrication,\" Adv. Mater. 36, 2312282 (2024). doi:10.1002/adma.202312282"],
  ["Thorvaldson2025", "\"Grover's algorithm in a four-qubit silicon processor above the fault-tolerant threshold,\" Nat. Nanotechnol. 20, 472–477 (2025). doi:10.1038/s41565-024-01853-5"],
  ["Tseng2023", "\"Resistless EUV lithography: photon-induced oxide patterning on silicon,\" Sci. Adv. 9, eadf5997 (2023). doi:10.1126/sciadv.adf5997"],
  ["Wang2022", "\"Experimental realization of an extended Fermi-Hubbard model using a 2D lattice of dopant-based quantum dots,\" Nat. Commun. 13, 6824 (2022). doi:10.1038/s41467-022-34220-w"],
  ["Wilson2004", "\"Phosphine dissociation on the Si(001) surface,\" Phys. Rev. Lett. 93, 226102 (2004). doi:10.1103/PhysRevLett.93.226102"],
  ["Jakob2022", "\"Deterministic shallow dopant implantation in silicon with detection confidence upper-bound to 99.85% by ion–solid interactions,\" Adv. Mater. 34, 2103235 (2022). doi:10.1002/adma.202103235"],
  ["Reiner2024", "\"High-fidelity initialization and control of electron and nuclear spins in a four-qubit register,\" Nat. Nanotechnol. 19, 605–611 (2024). doi:10.1038/s41565-023-01596-9"],
  ["Namboodiri2024", "\"Multi-scale alignment to buried atom-scale devices using Kelvin probe force microscopy,\" Nanotechnol. Rev. 13, 20230196 (2024). doi:10.1515/ntrev-2023-0196"],
  ["DAnna2026", "\"Element-specific, non-destructive profiling of two-dimensional dopant layers in silicon,\" npj Quantum Inf. (2026, online 11 Nov). doi:10.1038/s41534-026-01393-x"],
  ["Kiczynski2022", "\"Engineering topological states in atom-based semiconductor quantum dots,\" Nature 606, 694–699 (2022). doi:10.1038/s41586-022-04706-0"],
  ["Kane2000", "\"Silicon-based quantum computation,\" Fortschr. Phys. 48, 1023–1041 (2000). doi:10.1002/1521-3978(200009)48:9/11<1023::AID-PROP1023>3.0.CO;2-J"],
  ["OBrien2001", "\"Towards the fabrication of phosphorus qubits for a silicon quantum computer,\" Phys. Rev. B 64, 161401 (2001). doi:10.1103/PhysRevB.64.161401"],
  ["Ren2016", "\"Origin of symmetric dimer images of Si(001) observed by low-temperature scanning tunneling microscopy,\" Sci. Rep. 6, 27868 (2016). doi:10.1038/srep27868"],
  ["Xiang2025", "\"Self-passivation reduces the Fermi level pinning in the metal-semiconductor contacts,\" Nat. Commun. 16, 10675 (2025). doi:10.1038/s41467-025-65695-y"],
];
REFS.sort((p, q) => p[0].localeCompare(q[0]));
for (let pg = 0; pg * 16 < REFS.length; pg++) {
  const chunk = REFS.slice(pg * 16, pg * 16 + 16);
  const s = newSlide("REFS", pg ? "References (2 of 2)" : "References (1 of 2)", "Wrap-up");
  [chunk.slice(0, 8), chunk.slice(8)].forEach((col, ci) => {
    const runs = col.map(([k, r], i) => ({ text: `[${pg * 16 + ci * 8 + i + 1}] ${k}: ${r}`, options: { breakLine: true, paraSpaceAfter: 4 } }));
    text(s, runs, 0.5 + ci * 4.6, 0.95, 4.4, 4.25, { fontSize: 9.5, color: T.ink });
  });
  notes(s, pg ? "Second page of references, continuing alphabetically. Kane 2000 and O'Brien 2001 supply the Kane-architecture numbers on slide 5, since the 1998 paper itself isn't open; Ren 2016 and Xiang 2025 give the dimer and silicon–hydrogen bond lengths used in my surface renders. New papers beyond my original pack, like Jakob 2022, Reiner 2024, Namboodiri 2024, Kiczynski 2022 and Curson's newest, D'Anna 2026, are here too, all open access. Likely question: why cite a contact-physics paper for a bond length? It states the 1.51 Å Si–H bond I used; I only use that number." :
    "References, alphabetical by key; keys match each slide's source line. Figures marked 'Reproduced from' are CC BY 4.0 and credited on the slide; paywalled or no-derivatives figures were redrawn as original schematics instead of copied. Diagrams marked 'ours' or 'our model' are original and use only published numbers, with the exact spec and its source in notes/specs. If someone wants one paper to start with, I'd point them to the 2025 roadmap, Schofield et al. in Nano Futures, which covers the whole field and is open access. Likely question: are the figures licensed? Yes: CC BY figures are reproduced with credit, and everything else is redrawn.");
}

// ============================================================================ Backup: alternate titles
{
  const s = newSlide("SECTION", "Backup · Alternate titles", "Backup");
  bullets(s, ["Atom-by-Atom Silicon: Building Quantum Processors from Single Dopant Atoms (used)", "How an Atom-Precise Silicon Qubit Is Built", "Writing Qubits with an STM: Atomic-Precision Dopant Devices in Silicon", "Single-Dopant Silicon Devices: The Atomic-Scale Route to Quantum Processors", "From Phosphine to Processors: Atomic-Scale Dopant Engineering for Silicon Quantum Computing"], 0.5, 1.1, 5.2, 3.6, 14);
  img(s, "F1_stock2024_fig1_4x4.png", 6.0, 1.0, 3.5, 3.5, "center");
  caption(s, "4×4 single-As array: lithography, incorporation, dopant map. Reproduced from Stock et al., Adv. Mater. 36, 2312282 (2024) Fig. 1g–i, CC BY 4.0", 6.0, 4.55, 3.5, 0.55);
  notes(s, "Backup slide with the alternate titles from the reference pack, in case the course wants a 'How X is built' style title like the DMD and CMOS decks. The image is the 4×4 arsenic array from Stock 2024, with the lithography, the incorporated atoms and the dopant map. If asked about it: with non-ideal windows, 10 to 12 of 15 sites were single atoms, up to 80%, which shows that window shape matters as much as the chemistry. That 4×4 result is why the 2×2 is described as the first defect-free array: the bigger array still had defects.");
}


// ============================================================================ Backup: Monte Carlo
{
  const s = newSlide("SECTION", "Backup · Monte Carlo of 4×4 arrays", "Backup");
  const b = img(s, "O_montecarlo_4x4.png", 0.5, 1.05, 9.0, 3.6, "center");
  caption(s, "Our model, not data: filled = one atom, red = failed site; boxed = perfect array. 100 000 simulated arrays per row at the measured per-site yields (P 0.7, As 0.97; Stock2024).", 0.5, b.y + b.h + 0.05, 9.0, 0.4);
  src(s, "Stock2024 (per-site yields); simulation ours");
  notes(s, "Backup for the yield slide. I simulated 100,000 four-by-four arrays at each per-site yield. With phosphorus at 0.7, almost every array has failed sites, about 0.3% come out perfect, matching 0.7 to the 16th. With arsenic at 0.97, about 61% are perfect. This is a model, not data: it assumes sites fail independently, which is the same assumption behind the p to the n formula in Stock 2024. If asked whether failures are really independent: the papers quote the formula, they don't test correlations, so I'd say it's the simplest reasonable assumption.");
}

// ---------------------------------------------------------------- write outputs
fs.mkdirSync("deck", { recursive: true });
let md = "# Speaker notes: Atom-by-Atom Silicon\n\nGenerated by build_deck.js (same text as the notes in the .pptx).\n\n" +
  "## 15-minute timing plan\n\nThe notes are a full script (~3,300 words, about 22 min read aloud). For 15 min, say the figure pointer, the number to remember and one sentence per slide, and keep the Q&A lines for questions.\n\n" +
  "| Slides | Block | Target |\n|---|---|---|\n| 1-3 | Intro, device, timeline | 1:30 |\n| 4-6 | Why donors, why not implant, Curson | 2:00 |\n| 7-13 | Process flow, steps 1-11 | 4:30 |\n| 14-20 | Results: metrology, landmarks, yield, As, Ge/Bi, processors, simulator | 4:00 |\n| 21-22 | Throughput, EUV | 1:15 |\n| 23-24 | Our prototype + traveler | 1:00 |\n| 25-26 | Takeaways, references | 0:30 |\n| **Total** | | **14:45** |\n\n";
NOTES.forEach((n, i) => { md += `## Slide ${i + 1}: ${n.title}\n\n${n.text}\n\n_${n.text.split(/\s+/).length} words_\n\n`; });
fs.writeFileSync("notes/speaker_notes.md", md);
pres.writeFile({ fileName: "deck/atom_by_atom_silicon.pptx" }).then((f) => console.log("wrote", f, NOTES.length, "slides"));
