# EE143 course hooks for the STM dopant-qubit deck

Compiled 2026-11-21 from the EE143 Fall 2026 course PDFs in
`course_materials/EE143_Fall_2026_Course_Materials/`. Text only; no figures copied.

Conventions
- **File, page** = PDF page index (1-based) as opened in a viewer. In the lecture decks the printed slide number equals the PDF page, except `Section 3  Etching.pdf`, where the printed slide number runs ahead of the PDF page from p. 37 onward (+1 for pp. 37–57, +2 from p. 58); the printed number is given as "slide N".
- **Exact quote** = verbatim from the PDF text layer. Quotes marked **[slide image]** were transcribed from a rendered slide because the equation/table is an image or an equation object. Superscript "o" degree marks in the slides are written as °C; line breaks are joined; "1E15", "1019" etc. are kept as printed (1019 = 10^19 where the PDF lost the superscript).
- **[digitized]** = number read off a course chart by pixel measurement on the log axes (my reading, estimated ±10 %). **[derived]** = my calculation using the course's own equation/constants; not printed in the course.
- Abbreviations: PM = `03_Lab/Process Manual Fall 2026.pdf` (version compiled 19 Oct 2026; the older 10 Sep copy `Process Manual Fall 2026 1.pdf` has the same steps). CM = `03_Lab/Characterization Manual.pdf`.

---

## 0. Strongest tie-ins (one line each)

1. **Diffusion Table 4.1 (Jaeger) is in the deck**: P D0 = 10.5 cm²/s, EA = 3.69 eV; As D0 = 0.32 cm²/s, EA = 3.56 eV (Diffusion p. 11). With the course's 2√(Dt) (p. 13): P moves 8.5×10⁻⁷ nm at 350 °C × 2 min, 2.4×10⁻⁴ nm at 500 °C × 15 s, ≈3×10⁻⁹ nm at 250 °C × 10 min. The EE143 lab's own 1050 °C predep + drive-in gives ≈300 nm. [derived]
2. **Thermal budget slide** (Diffusion p. 21): "(Dt)effective = Σ (Dt)i ... only those steps with high Dt values are important". Qubit flow Σ(Dt) for P ≈ 1.4×10⁻²² cm², dominated by the 500 °C step; EE143 lab ≈ 2.3×10⁻¹⁰ cm², about 10¹² times larger. [derived]
3. **Rp/ΔRp chart** (Implantation p. 12) [digitized]: As at ~10 keV: Rp ≈ 11 nm, ΔRp ≈ 3.8 nm; P at ~10 keV: Rp ≈ 14 nm, ΔRp ≈ 7.5 nm; at 100 keV P Rp ≈ 123 nm / ΔRp ≈ 47 nm, As 59 nm / 22 nm. The lowest-energy straggle in the course is 10× (As) to 20× (P) larger than STM's ±0.384 nm, and lateral straggle is comparable or larger ("ΔRt/ΔRp > 1", p. 14).
4. **The delta-function slide** (Diffusion p. 17): "Approximate predep profile as a delta function at x=0". The δ-layer is that idealization made real; the Gaussian-implant-plus-diffusion formula (p. 20) with σ² = ΔRp² + 2Dt tells you why: at 350 °C, 2Dt ≈ 10⁻¹³ nm², so σ stays at whatever the deposition gave.
5. **Gas sources named in class**: "(a) Gas Source: AsH3, PH3, B2H6" (Diffusion p. 5); PH3 in PSG LPCVD at 350–500 °C (TF Dep p. 27); the lab's own poly furnace "uses silane to supply silicon and phosphine for phosphorus" (PM p. 12).
6. **Four-point probe**: Rs = (π/ln2)(V/I) ≅ 4.53 V/I [Ω/square] (Metallization p. 15). Lab SOG doping gives "≈4 Ω/□" (PM p. 16); 100 nm Al ≈ 0.28 Ω/□ [derived]; a 10¹⁴ cm⁻² δ-layer at μ ≈ 50 cm²/Vs ≈ 1.2 kΩ/□ [derived; μ is illustrative and must come from the qubit literature]. **Hall effect and van der Pauw do not appear anywhere in the course PDFs.**
7. **Lithography scaling**: R = k1λ/NA, DOF = k2λ/NA², "k1 cannot be smaller than 0.25" (Litho pp. 29–36); EUV examples in the answer key: NA 0.33 → R ≈ 14 nm, high-NA 0.55 → R ≈ 8.6 nm; course target "Linewidth <10 nm, Overlay <4 nm, CD control <2 nm" (Class 1 p. 8). STM's ±0.384 nm placement is ~10× tighter than that overlay spec. E-beam: "Higher throughput always results in lower resolution" and "hours per wafer not wafers per hour" (Litho pp. 92, 94), the same trade STM lithography makes.
8. **Vacuum rule of thumb**: "About one monolayer in 1 sec at 10-6T" (TF Dep p. 7). The lab evaporator runs at 2–5×10⁻⁶ Torr (PM p. 22); at UHV (~10⁻¹⁰ Torr) the same rule gives ~10⁴ s ≈ 3 h per monolayer, which is why the H resist survives long enough to be patterned. [derived]

---

## 1. Ion implantation (`01_Lectures/Section 6 - Ion Implantation.pdf`)

| Topic | Equation / number | Exact quote | File, page | Suggested slide tie-in |
|---|---|---|---|---|
| Why implant is the incumbent | Dose control a few % | "Tight Dose Control (A few % vs. 20-30% for high temperature pre-deposition processes)" ; "Low Temperature Process" | Implantation p. 2 | Open the comparison slide: implant already beat diffusion on dose control. STM δ-doping beats implant on *placement*. |
| Dose from beam current | Q = (1/nqA) ∫₀ᵀ I(t) dt | "Implanted Dose" Q = 1/(nqA) ∫0^T I(t)dt **[slide image]**; accelerator labelled "0 to 175 kV" | Implantation p. 3 | Dose is counted electrically for ~10¹² ions at a time; STM deposits P where the tip removed H, one site at a time. |
| Dose definition | Φ = (I/q)·t / area, #/cm² | "Dose Φ = (Ion Beam Current in amps / q) × (Implant time) / [Ion Beam Scanning Area] = #/cm2" **[slide image]**; "Over-scanning of beam across wafer is common. In general , Implant area > Wafer area" | Implantation p. 6 | Same unit as the δ-layer: 1×10¹⁴ cm⁻². Poisson count in a patch: N = Q·A, so 10¹⁴ cm⁻² in 10 nm × 10 nm = 100 ions (±10 %); 10¹² cm⁻² gives N = 1 (±100 %). [derived] |
| Dose vs concentration | — | "Dose [#/area] : looking downward, how many fish per unit area for ALL depths ?" ; "Concentration [#/volume] : Looking at a particular location, how many fish per unit volume ?" | Implantation p. 7 | δ-layer: 10¹⁴ cm⁻² squeezed into <1 nm → ≥10²¹ cm⁻³ (2 % of Si's 5.0×10²² cm⁻³, PS2 p. 5). [derived] |
| Anneal requirement | >900 °C | "Reminder: During implantation, temperature is ambient. However, post-implant annealing step (>900oC) is required to anneal out defects." | Implantation p. 4 | Contrast with the 350 °C incorporation anneal: no lattice damage to repair. |
| Implant advantages | <1 % lateral uniformity | "Precise control of dose and depth profile – Very high dose and ultra-shallow depth possible" ; "Excellent lateral uniformity (< 1% variation across 12” wafer)" | Implantation p. 5 | Uniformity is a wafer-average statistic; a qubit needs one atom at one site. |
| Stopping | — | "Light ions/at higher energy → more electronic stopping" ; "Heavier ions/at lower energy → more nuclear stopping" ; As+ labelled "Nuclear stopping dominates" | Implantation p. 9 | Heavy As at low energy causes the most damage per ion. |
| Gaussian profile | N(x) = Np exp[−(x−Rp)²/(2ΔRp²)]; Q = ∫N dx = √(2π) Np ΔRp | "Gaussian Profile ... Rp = Projected Range ... ΔRp = Straggle ... Dose Q = ∫0^∞ N(x)dx = √(2π) Np ΔRp" **[slide image]**; profile marks 0.61 Np at Rp ± ΔRp, 0.14 Np at ±2ΔRp, 0.011 Np at ±3ΔRp | Implantation p. 11 | Each implanted ion is one random draw from this Gaussian: vertical placement σ = ΔRp. Compare the δ-layer, which is "<1 nm thick". |
| Rp, ΔRp source | — | "Rp and ΔRp values are given in tables or charts" | Implantation p. 12 | See digitized table below. |
| Lateral straggle model | N(x,y) = N(x)F(y); F(y) = ½[erfc((y−a)/(√2 ΔR⊥)) − erfc((y+a)/(√2 ΔR⊥))] | "ΔR⊥ = transverse straggle" ; "N(x) is one-dimensional solution" **[slide image]**; worked example "Rp = 0.5 µm, ΔRp = 0.1 µm, ΔR⊥ = 0.115 µm" | Implantation p. 13 | Lateral placement σ = ΔR⊥, independent of how small the mask opening is. |
| Lateral > vertical | ΔRt/ΔRp > 1 | "Transverse (or Lateral) Straggle (ΔRt or ΔR⊥)" ; "ΔRt / ΔRp >1" **[slide image]**; chart: lateral σ of As ≈ 0.02 µm at 100 keV, ≈ 0.053 µm at 300 keV [digitized] | Implantation p. 14 | Lateral is what sets qubit-to-qubit spacing errors. |
| Feature enlargement | — | "Implanted species has lateral distribution, larger than mask opening" ; "Feature Enlargement due to lateral straggle" | Implantation p. 15 | A 10 nm mask hole still leaves ~4–9 nm σ placement at 10 keV. |
| Mask thickness rule | d = Rp + 4.3ΔRp gives C(d)/C(Rp) ~ 10⁻⁴ | "Rule of thumb : Good masking thickness" d = Rp + 4.3ΔRp **[slide image]** ; T = ½ erfc[(d−Rp)/(√2 ΔRp)] | Implantation p. 18 | In STM lithography the "mask" is one monolayer of H. It blocks PH3 chemically, not by stopping power. |
| Junction depth | xj = Rp + ΔRp √(2 ln(Np/NB)) | "The junction depth is calculated from the point at which the implant profile concentration = bulk concentration" | Implantation p. 19 | Optional: δ-layer "junction" is set by deposition, not by a tail. |
| Channeling | 0° vs tilted | Plot legend: "0° to <110> Q = 1.2 × 10^12/cm2" ; "2°, 8°, 3° to <110> Q = 5 × 10^12/cm2" ; "32P: Si Room temperature"; 0° tail extends to ~0.9 µm **[slide image]** | Implantation p. 20 | Channeled ions are placement outliers far beyond ΔRp. |
| Tilt | 7° | "To minimize channeling, we tilt wafer by 7o with respect to ion beam." ; "Lucky ions fall into channel despite tilt" | Implantation p. 21 | The lab's B implant uses exactly this 7° tilt (PM p. 5). |
| Pre-amorphization | 1E15 Si+ | "Step 1 High dose Si+ implantation to covert surface layer into amorphous Si" ; "Si+ 1 E15/cm2" ; "Disadvantage : Needs an additional high-dose implantation step" | Implantation p. 22 | More damage to fix the damage problem. |
| Damage | — | "Schematic of the disorder produced along the individual paths of light and heavy ions and the formation of an amorphous region." | Implantation p. 25 | Every ion leaves a collision cascade around the very atom you want as a qubit. |
| Damage vs dose | 40 keV P: disorder rises from 10¹³, saturates ("Amorphous") above ~5×10¹⁴ cm⁻² **[digitized]** | Chart labels "Disorder zones", "Amorphous", "40-keV P → Si", x-axis "Ions/cm2" 10¹³–10¹⁶ | Implantation p. 26 | The δ-layer's 10¹⁴ cm⁻² sits on the steep part of this curve: as an implant it would heavily damage the lattice. |
| Anneal purpose | — | "After implantation, we need an annealing step. A typical anneal will: (1) Restore Si crystallinity. (2) Place dopants into Si substitutional sites for electrical activation" | Implantation p. 27 | Exact parallel: the 350 °C anneal does (2) only, moving P from adsorbed PH_x into a substitutional site; (1) is unnecessary. |
| Non-Gaussian | >200 keV | "Curves deviate from Gaussian for deeper implants (> 200 keV)" | Implantation p. 28 | — |
| Shallow implants + RTA | As/P "as implanted" vs "950°C, 10s"; P profile broadens from ~30 nm to ~60–70 nm depth at 10¹⁷ cm⁻³ **[slide image/digitized]**; B "Dose: 1×10^15 cm−2 B+ as implanted", 0.5–5 keV; "Annealed: 1050 °C/10s" | Implantation p. 29 | Even a 10 s anneal moves P by tens of nm. Our intrinsic-D estimate for 950 °C, 10 s is only 2√(Dt) ≈ 5 nm, so measured spreading is ~10× larger (TED, Diffusion p. 31). |
| Application space | S/D extension ~10¹⁴ cm⁻², ~0.3–30 keV | Box labels "Source–drain extension (As, BF2, B)", "Threshold voltage adjust (As, BF2, B, P, In)", "Channel engineering", "Preamorphization (Ge, Si)" ; axes "DOSE (atoms/cm2)" 10¹¹–10¹⁷, "ENERGY (keV)" 0.1–10,000 **[slide image]** | Implantation p. 30 | Place the δ-layer on this map: same dose as an S/D extension, at "0 keV" and zero damage. |
| Overview statement | 1–200 keV; 900–1000 °C anneal | "Ion Energy ~1 keV to 200 keV" ; "Room temp during implantation. After implantation, a 900oC-1000oC anneal step is needed to: 1) activate dopants 2) restore Si crystallinity" | `Section 1  Overview 2.pdf` p. 26 | Recap line for the comparison slide. |

### 1a. Rp, ΔRp, ΔR⊥ for P and As in Si [digitized from Implantation p. 12, chart (a) Rp and chart (b) "Normal and transverse straggle", solid = ΔRp, dashed = ΔR⊥]

Axes calibrated on the 0.01/0.1/1 µm ticks (a) and 0.01/0.10 µm ticks (b); estimated reading error ±10 %. Where the As ΔRp and ΔR⊥ curves overlap (low energy), one value is given. The 100 keV values agree with commonly tabulated LSS values (P 100 keV: Rp ≈ 0.12 µm, ΔRp ≈ 0.046 µm; As 100 keV: Rp ≈ 0.058 µm, ΔRp ≈ 0.021 µm).

| Energy (keV) | P Rp (nm) | P ΔRp (nm) | P ΔR⊥ (nm) | As Rp (nm) | As ΔRp (nm) | As ΔR⊥ (nm) |
|---|---|---|---|---|---|---|
| ~10 (left edge) | 13–14 | ≈7.5 | ≈8.8 | 10–11 | ≈3.8 | ≈4.1 |
| 15 | 19 | ≈10 | ≈11 | 13 | ≈4.8 | ≈4.8 |
| 20 | 25 | 12 | 14 | 16 | 5.9 | ≈6 |
| 30 | 36 | 17 | 20 | 22 | ≈8 | ≈9 |
| 50 | 60 | 26 | 31 | 32 | 12 | ≈12 |
| 100 | 123 (marked dot) | 47 (marked dot) | ≈58 (interp.) | 59 | 22 | ≈22 |

**Slide-ready comparison [derived]:** STM placement ±0.384 nm vs lowest-energy course data (~10 keV): As ΔRp 3.8 nm (≈10×), P ΔRp 7.5 nm (≈20×); lateral ΔR⊥ is the same or larger. Profile FWHM = 2.355 ΔRp → As ≈ 9 nm, P ≈ 18 nm, vs δ-layer "<1 nm". Course charts stop at 10 keV, so sub-10 keV values are not in the course.

---

## 2. Diffusion (`01_Lectures/Section 7 - Diffusion.pdf`)

| Topic | Equation / number | Exact quote | File, page | Suggested slide tie-in |
|---|---|---|---|---|
| Gas sources | AsH3, PH3, B2H6 | "Surface Diffusion: Dopant Sources (a) Gas Source: AsH3, PH3, B2H6" | Diffusion p. 5 | Same molecules as STM δ-doping; the difference is the H-resist mask and the ~350 °C (not ~1000 °C) temperature. |
| Mechanisms | — | "(b) Substitutional Diffusion ... (c) Interstitialcy Diffusion Example: Dopants in Si ( e.g. B, P,As,Sb)" ; interstitial "Fast Diffusion Example: Cu, Fe, Li, H" | Diffusion p. 4 (repeated p. 9), p. 3 | Substitutional P must swap with a vacancy to move; at 350 °C this almost never happens. H (the resist) is a fast interstitial diffuser. |
| Fick's 1st law | J = −D ∂N/∂x | "Fick’s First Law of Diffusion" ; "D = diffusion coefficient" | Diffusion p. 6 | — |
| Fick's 2nd law | ∂N/∂t = D ∂²N/∂x² | "Fick's Second Law of Diffusion : Combine First Law with Continuity Eqn." ; "Assumes D is concentration - independent, which isn't true in many situations in modern devices" ; continuity "∂N/∂t = −∂J/∂x (in one dimension)" | Diffusion p. 7 | Caveat for our estimate: a 10²¹ cm⁻³ δ-layer is the high-concentration case. |
| Arrhenius D | D = D0 exp(−EA/kT) | "D = DO exp(−EA/kT) Arrhenius Relationship ; EA = activation energy ; k = Boltzmann's constant = 1.38 x10-23 J/K ; T = absolute temperature" **[slide image]** | Diffusion p. 11 | The core equation for the "how far does P move" slide. |
| **D0, EA table** | **P: D0 = 10.5 cm²/s, EA = 3.69 eV; As: D0 = 0.32 cm²/s, EA = 3.56 eV** (also B 10.5/3.69, Al 8.00/3.47, Ga 3.60/3.51, In 16.5/3.90, Sb 5.60/3.95) | "TABLE 4.1 Typical Diffusion Coefficient Values for a Number of Impurities." Columns "Element  D0(cm²/sec)  EA(eV)"; rows "P 10.5 3.69", "As 0.32 3.56" **[slide image; the header prints "EA(cV)", a scan artifact for eV]** | Diffusion p. 11 | Use these for every diffusion-length number in the deck (table 2a). Note the table gives P the same values as B. |
| D vs 1/T chart | B,P curve and As curve, 10⁻¹⁴ to 10⁻⁹ cm²/s over ~1000–1400 °C | "Substitutional Diffusion Coefficients in Si" ; "Substitutional Diffusers" ; arrows "B,P" and "As" **[slide image]** | Diffusion p. 10 | The chart stops at ~1000 °C (10⁻¹⁴ cm²/s). The qubit flow (250–500 °C) sits 9–21 orders of magnitude below its bottom edge [derived]. |
| Solid solubility | P solubility ≈ 5.6×10²⁰ (900 °C) to ≈1.3×10²¹ cm⁻³ (~1100 °C); electrically active P ≈ 3–4×10²⁰; As active ≈ 3–5×10²⁰ cm⁻³ [digitized] | "There is a limit to the amount of a given impurity that can be “dissolved” in silicon (the Solid Solubility Limit)" ; "At high concentrations, all of the impurities introduced into silicon will not be electrically active" | Diffusion p. 12 | δ-layer ≥10²¹ cm⁻³ is above the furnace "electrically active" ceiling; it is reached only by low-T, kinetically limited placement. |
| erfc solution, characteristic length | C = C0 erfc(x/(2√(Dt))) | "2√Dt = Characteristic distance for diffusion." ; "C0 ≡ Surface Concentration (solid solubility limit)" **[slide image]** | Diffusion p. 13 | Define L = 2√(Dt) on the slide exactly as the course does. |
| Two-step diffusion | — | "(1) Predeposition ... dose control" ; "(2) Drive-in ... profile control (junction depth; concentration)" ; "Note: Predeposition by diffusion can also be replaced by a shallow implantation step." | Diffusion p. 15 | STM flow = predep (PH3 dose, 1 site at a time) with essentially no drive-in. |
| **Delta-function predep** | C(x,t) = Q/√(π(Dt)drive-in) · exp[−x²/4(Dt)drive-in]; Q = C0·2√(Dt)predep/√π | "Solution of Drive-in Profile with Shallow Predeposition Approximation:" ; "Approximate predep profile as a delta function at x=0" **[slide image]** | Diffusion p. 17 | Headline hook: the δ-layer *is* the course's delta-function idealization. (For a buried layer away from the surface the prefactor becomes Q/(2√(πDt)); the width is still √(2Dt).) |
| **Implant + diffusion** | C(x,t) = φ/[√(2π)(ΔRp² + 2Dt)^½] · exp[−(x−Rp)²/(2(ΔRp² + 2Dt))] | "Diffusion of Gaussian Implantation Profile" ; "Note: φ is the implantation dose" **[slide image]** | Diffusion p. 20 | Effective σ = √(ΔRp² + 2Dt). For the qubit flow 2Dt ≈ 10⁻¹³ nm² (P at 350 °C × 2 min), so σ is set entirely by placement. For implant, σ ≥ ΔRp ≈ 4–8 nm before any anneal. |
| **Thermal budget** | (Dt)effective = Σi (Dt)i | "Successive Diffusions" ; "Thermal Budget" ; "Example Dttotal of : Well drive-in and S/D annealing" ; "For a complete process flow, only those steps with high Dt values are important" | Diffusion p. 21 | Tabulate Σ(Dt) for the qubit flow vs the EE143 lab flow (table 2b). |
| Intrinsic vs extrinsic | ni(1000 °C) = 5×10¹⁸ cm⁻³ | "First, Check if doping concentration is > ni(T) or < ni(T) (example: at 1000C, ni = 5E18 cm-3)" ; "If doping conc < ni: D= Do Use constant diffusivity solutions" ; "If doping conc > ni: (Solution requires numerical techniques)" | Diffusion p. 29 | δ-layer at 10²¹ cm⁻³ is extrinsic, so D is enhanced. |
| Enhancement magnitude | D/Di rises to ~30 at n/ni ≈ 40 [digitized] | "INTRINSIC DIFFUSION" / "EXTRINSIC DIFFUSION", axes "D/Di(T)" vs "n/ni(T)" **[slide image]** | Diffusion p. 30 | Even ×30 on D is only ×5.5 on length; 350 °C numbers stay sub-picometre. |
| High concentration | — | "C(x) goes deeper but the shape looks “flatter”at high conc. regions" ; "Basic mechanism: E-field effects from charged vacancies, vacancy diffusion." | Diffusion p. 27 | — |
| TED | 1000× excess defects | "Implantation creates large number of excess Si interstitials and vacancies. (1000X than thermal process)." ; "900oC, several sec (TED)" ; "Extremely rapid diffusion due to excess point defects" | Diffusion p. 31 | Implant-specific problem that STM δ-doping avoids (no damage, so no excess point defects). |
| Ultra-shallow limit | <100 nm | "Difficult to make ultra-shallow (< 100nm) junctions with implantation and annealing" | Diffusion p. 32 | The δ-layer is <1 nm. |
| OED | ΔD ∝ (dXox/dt)ⁿ, 0.4 < n < 0.6 | "Diffusivity is enhanced for B and P underneath a growing oxide" ; "DOED = D + ∆D" | Diffusion p. 33 | Reason to avoid oxidation over the δ-layer. |
| SIMS | 2–5 Å/s | "Secondary Ion Mass Spectroscopy (SIMS)" ; "Typically Cs Sputter 2-5 A/sec" | Diffusion p. 34 | SIMS is the standard way δ-layer thickness is measured. |
| Overview versions | √(Dt); 850–1150 °C | "Diffusion distance (≅ √Dt)" **[slide image]**; "Processing Temperature 850-1150 oC" | Overview p. 34; p. 30 | Note the course uses both √(Dt) (Overview) and 2√(Dt) (Diffusion p. 13). Say which one you quote. |
| RTA | xj < 50 nm, ≥0.5 s, 200 °C/s | "Sub-micron MOSFETs need ultra-shallow junctions (xj<50 nm)" ; "ramp rates as fast as 200oC/second" ; "anneal times as short as 0.5 second" ; "Dopant diffusion during “activation” anneal must be minimized" | Overview p. 31 | Industry's best thermal-budget tool still targets tens of nm. |

### 2a. Diffusion lengths with the course's own D0, EA [derived]

D = D0 exp(−EA/kT) with Table 4.1 values (Diffusion p. 11), k = 8.617×10⁻⁵ eV/K (as given in PS2/PS3), T in K; L = 2√(Dt) (Diffusion p. 13). Intrinsic (low-concentration) D, extrapolated far below the chart's temperature range. Read the result as an order of magnitude, not a prediction.

| Step | t | D_P (cm²/s) | 2√(Dt) P | D_As (cm²/s) | 2√(Dt) As |
|---|---|---|---|---|---|
| 250 °C Si overgrowth | 10 min | 3.0×10⁻³⁵ | 2.7×10⁻⁹ nm | 1.6×10⁻³⁵ | 2.0×10⁻⁹ nm |
| 250 °C Si overgrowth | 1 h | 3.0×10⁻³⁵ | 6.5×10⁻⁹ nm | 1.6×10⁻³⁵ | 4.8×10⁻⁹ nm |
| **350 °C incorporation anneal** | **2 min** | **1.5×10⁻²⁹** | **8.5×10⁻⁷ nm** | **5.2×10⁻³⁰** | **5.0×10⁻⁷ nm** |
| 400 °C forming-gas sinter (EE143 lab, PM p. 25) | 20 min | 2.5×10⁻²⁷ | 3.5×10⁻⁵ nm | 7.1×10⁻²⁸ | 1.9×10⁻⁵ nm |
| **500 °C anneal** | **15 s** | **9.3×10⁻²⁴** | **2.4×10⁻⁴ nm** | **2.0×10⁻²⁴** | **1.1×10⁻⁴ nm** |
| 615 °C poly LPCVD (lab; 131 min per NanoLab sheet) | 131 min | 1.2×10⁻²⁰ | 0.20 nm | 2.0×10⁻²¹ | 0.08 nm |
| 950 °C RTA (Implantation p. 29) | 10 s | 6.6×10⁻¹⁵ | 5.1 nm | 6.9×10⁻¹⁶ | 1.7 nm |
| 1000 °C | 30 min | 2.6×10⁻¹⁴ | 137 nm | 2.6×10⁻¹⁵ | 43 nm |
| 1050 °C lab SOG predep (PM p. 16) | 10 min | 9.3×10⁻¹⁴ | 149 nm | 8.8×10⁻¹⁵ | 46 nm |
| 1050 °C lab predep + wet ox + N₂ anneal (PM pp. 16–18: 10 + 12 + 20 min) | 42 min | 9.3×10⁻¹⁴ | 305 nm | 8.8×10⁻¹⁵ | 94 nm |

Comparison anchors: STM placement ±0.384 nm; Si lattice constant 0.543 nm (not in course).

Arrhenius sensitivity (PS3 5(d) form d ln D/dT = EA/kT²): P at 350 °C ≈ 11 % per K. [derived]

### 2b. Thermal budget Σ(Dt) (Diffusion p. 21) [derived]

| Flow | Steps included | Σ(Dt) P (cm²) | Σ(Dt) As (cm²) |
|---|---|---|---|
| STM qubit (example) | 350 °C 2 min + 250 °C 10 min + 500 °C 15 s + 400 °C 20 min | 1.4×10⁻²² (500 °C step = 98 %) | 3.1×10⁻²³ |
| EE143 lab S/D | 1050 °C × 42 min | 2.3×10⁻¹⁰ | 2.2×10⁻¹¹ |
| Ratio lab/qubit | | ≈1.6×10¹² | ≈7×10¹¹ |

This illustrates the slide's own rule ("only those steps with high Dt values are important"): the single hottest step dominates.

**Caveat for the speaker:** Fick-law bulk diffusion is *not* what limits δ-layer sharpness at 250–500 °C. Measured smearing of ~1 nm comes from surface segregation/riding of P on the growth front during overgrowth, which the course does not cover. The nearest course concept is dopant segregation/pile-up at the Si/SiO₂ interface (Oxidation pp. 43–45; PS2 5(e)). Present the table as "bulk diffusion is negligible, so whatever smearing exists comes from a different mechanism."

---

## 3. Sheet resistance, four-point probe, Hall effect

| Topic | Equation / number | Exact quote | File, page | Suggested slide tie-in |
|---|---|---|---|---|
| Four-point probe (thin layer) | Rs = 4.532 V/I, valid for t ≤ s/2 | "The Four-Point Probe is used to measure Rs independent of contact resistance effects" ; "4 probes are arranged in-line with equal spacing s" ; "2 outer probes used to flow current I through the sample" ; "2 inner probes are used to sense the resultant voltage drop V with a voltmeter" ; "For a thin layer (t ≤ s/2), Rs = 4.532 V/I (Typically, s ≈ 1 mm >>t)" | `Section 8 - Metallization.pdf` p. 14 | A δ-layer is the ultimate thin layer (t < 1 nm ≪ s ≈ 1 mm), so the course's thin-film formula applies exactly. |
| Four-point probe (general) | ρ = 2πs V/I (t ≫ s); ρ = (πt/ln2)(V/I) (s ≫ t); Rs = ρ/t = (π/ln2)(V/I) ≅ 4.53 V/I [Ω/square] | "Four Point Probe Resistivity" ; "Four Terminal Resistance Measurement" ; "If ρ is known, then Rs measurement can be used to determine thickness t" **[equations from slide image]** | Metallization p. 15 | For a δ-layer, "t" has no meaning; quote Rs (Ω/□) only, which is why δ-layer papers report Rs and sheet density. |
| Al resistivity | Al 2.8 µΩ-cm (Ag 1.6, Au 2.4, Cu 1.7, Mo 5.6, W 5.5) | "Resistivity of Pure Metals" (bar chart values) ; "Poly-Si (min) =1E-3 Ω-cm" **[slide image]** | Metallization p. 8 | 100 nm Al → Rs = 0.28 Ω/□. [derived] |
| Al thickness check | t = ρ/Rs; ρAl ≈ 2.7 µΩ·cm; 1 µm ≈ 27 mΩ/sq | "Check with the four-point probe: t = ρ/Rs with ρAl ≈2.7 µΩ·cm, so 1 µm corresponds to about 27 mΩ/sq." | `02_Problem_Sets/PS3_deposition_solutions.pdf` p. 1 | Same 4-pt check used on the qubit's Al contacts. |
| Interconnect R | RI = R/L = ρ/(WAl TAl) | "Interconnect Resistance RI =R/L = ρ / (WAlTAl)" | Metallization p. 29 | Number of squares in a δ-doped lead: R = Rs·L/W. |
| Mobility | v = μE | "Average drift velocity = \| v \| = µ E" ; "Carrier mobility" | Overview p. 51 | Only mobility statement in the course. |
| **Rs from dose and mobility** | Rs = 1/(q·Ns·μ) | **Not stated verbatim anywhere in the course PDFs.** Closest: Rs = ρ/t (Metallization p. 15) with the standard ρ = 1/(qnμ) (Jaeger, not in slides). | — | [derived] Ns = 10¹⁴ cm⁻²: μ = 30 → 2.1 kΩ/□; μ = 50 → 1.25 kΩ/□; μ = 100 → 0.62 kΩ/□; four-point V/I = Rs/4.532 → 459 / 275 / 138 Ω. μ values are placeholders; take the measured μ and Rs from the qubit papers. |
| Lab's measured doping Rs | ≈4 Ω/□ after SOG | "It should have decreased about two orders of magnitude to ≈4 Ω/□." | PM p. 16 | Lab furnace doping ≈4 Ω/□ vs δ-layer ~10² to 10³ Ω/□: a single atomic plane carries far less charge than a ~µm junction. |
| Lab measurement points | — | "Measure their resistivity using the four-point probe. Record this measurement as the initial resistivity of the wafers." (PM p. 9) ; "Strip oxide from control wafer(s) and measure its sheet resistance with the four-point probe. This is an indicator of the source/drain doping concentration (and resistivity)." (PM p. 18) ; "Use four-point probe to measure sheet resistance of deposited aluminum on control wafer" (PM p. 22) | PM pp. 9, 18, 22 | "Our lab measures Rs three times; δ-layer devices are first characterized the same way (then Hall)." |
| On-chip 4-pt resistor | 20 squares | "Use 4-point probing for measurement of R" ; "Inner line segment is 20 squares (L = 200 µm, W = 10 µm)" | CM p. 20 | A δ-doped Hall bar is the same idea: a defined number of squares between voltage taps. |
| 4-pt measurement setup | — | "2A & 2B – 4155B - SHEET Mode" ; F1P current sweep "Start -0.1 Stop 0.1 Compliance 5" ; checklist "4-Point Resistors (2a and 2b) – I vs ∆V, where ∆V is the difference between your measured voltages" | CM p. 7; p. 5 | Same instrument class (SMU) as cryogenic δ-layer measurements, at room temperature. |
| Contact chains | 14 contacts | "Each chain has 14 series contacts and 7 series resistive pads" ; "2C: 14 contacts connecting metal to diffused Si" | CM p. 21 | Contact resistance to a buried δ-layer is the hard part (see §5c). |
| Single-contact structures | — | "17B: Metal/Diffused Si 2 Diffused Si Line Segments -- Length: 160 µm; Width: 20 µm (1 square overlap w/contact)" | CM p. 40 | — |
| Lab-report ask | — | "Sheet resistance of areas with no phosphorus doping (Ω/square)" ; "Sheet resistance of areas with phosphorus doping (Ω/square)" ; "Assuming the ideal thickness of evaporated aluminum is 100nm, please compute the sheet resistance of this film." | `03_Lab/Lab Report 1 2.pdf` p. 9 | Students have already done the δ-layer-style calculation for their own wafer. |
| **Hall effect / van der Pauw** | — | **Not found.** Searched every PDF (text layer) for "Hall", "van der Pauw", "Hall coefficient", "Hall bar": only hits are "Prentice Hall" and "Cory Hall". | — | Introduce R_H = 1/(q·Ns) and van der Pauw as new material beyond EE143, building on the 4-pt slide. |

---

## 4. Lithography (`01_Lectures/Section_2_Lithography_30MB.pdf`, Tony Yen decks, Class 1)

| Topic | Equation / number | Exact quote | File, page | Suggested slide tie-in |
|---|---|---|---|---|
| Industry targets | <10 nm / <4 nm / <2 nm | "Linewidth <10 nm Overlay <4 nm CD control <2 nm" | `Microfabrication_Fall_2026_class_1 1.pdf` p. 8 (also Litho p. 11) | STM: ±0.384 nm placement, ≈10× tighter than the overlay spec. |
| Grating derivation | R = λ/(2NA) (k1 = 0.5); R = λ/(4NA) (k1 = 0.25) | "The mask is a diffraction grating p sin θₘ = mλ" ; "NA = n sin θ" ; "sin θ₁ = λ/p ≤ NA" ; "On-axis illumination R = p/2 = λ / (2 NA) k₁ = 0.5" ; "Tilted illumination — physical floor R = λ / (4 NA) k₁ = 0.25" | Litho p. 29 | — |
| k1 floor | 0.25 | "k1 cannot be smaller than 0.25" | Litho p. 30; Class 1 p. 36 | Optical lithography has a diffraction floor; STM placement is set by the lattice. |
| Resolution / DOF | lm = k1 λ/NA; DOF = k2 λ/NA² | "1) Minimum feature resolution lm = k1 (λ/NA) 2) Depth of Focus DOF = k2 λ/ (NA)2 NOTE: NA has contradictory effects on lm and DOF where k1 and k2 are the technology factors" | Litho p. 35 | — |
| EUV worked examples | 13 nm EUV: NA = 0.067 → DOF 2.9 µm; NA 0.6 → 13 nm, DOF 36 nm | "What NA is required to print the same feature with EUV (13 nm wavelength)? – NA = k1λ/lm = 0.067 – What is the DOF? • k2λ/(NA)2 = 2.9 µm • What is the minimum feature that can be printed using EUV radiation with NA=0.6? – k1λ/NA = 13 nm – What is the DOF? • k2λ/(NA)2 = 36 nm" (assumes "k1 = 0.6; k2 = 1") | Litho p. 36 | EUV scaling slide: reuse the course numbers directly. |
| EUV, answer key | NA 0.33: R ≈ 14 nm, DOF ≈ 124 nm; NA 0.55: R ≈ 8.6 nm, DOF ≈ 45 nm (k1 = 0.35, k2 = 1) | "(d) EUV NA = 0.33: R = 0.35 × 13.5 / 0.33 ≈ 14 nm, DOF = 13.5 / 0.109 ≈ 124 nm. High-NA 0.55: R ≈ 8.6 nm, DOF ≈ 45 nm." | `02_Problem_Sets/Section_2_Lithography_Answer_Key.pdf` p. 1 (Problem 1d) | High-NA EUV half-pitch 8.6 nm ≈ 22 Si(001) dimer-row spacings (0.384 nm per half-row as given); STM addresses single rows. |
| EUV wavelength | 13.5 nm; "<10 nm" | "EUV litho using soft x-rays to extend to <10 nm!" (p. 18) ; "Laser pulsed plasma (13nm, EUV)" (p. 21) ; "EUV Lithography λ =13 nm" (p. 38) | Litho pp. 18, 21, 38 | — |
| EUV (Yen) | Min. half-pitch = k1 λ/NA (k1 ≥ 0.25); 13.5 nm; 19 nm pitch | "Min. Half−Pitch = 𝑘1 λ/NA (𝑘1 ≥0.25)" ; "19nm-pitch lines formed by extreme ultraviolet (13.5nm) lithography" | `Tony Yen Photolithography Lectures 1  2 Combined and Revised.pdf` pp. 37, 38 | — |
| EUV throughput (Yen) | <1 → 160 wph | "<1 wph <10 wph <50 wph 135 wph @30mJ/cm2 160 wph @30mJ/cm2" ; "2019 ASML ships 1st NA 0.33 HVM system NXE:3400C" ; "wph: wafers exposed per hour" | Tony Yen combined p. 47 | Throughput contrast for STM lithography (serial, hours per device). |
| High-NA EUV | 0.55 NA; $275 M | "Joint lab with IMEC available for industry to develop 0.55 NA lithography process" (Yen p. 48) ; "The latest high-NA system $275 M" (Litho p. 77) | Tony Yen combined p. 48; Litho p. 77 | — |
| Scanner throughput | 230 wph, ~100 fields | "A modern scanner 230 wafers/hour Each wafer ~100 exposure fields" ; key: "3600 s / (230 × 100) ≈ 0.16 s per field" | Litho p. 20; Answer Key p. 2 (Problem 3d) | — |
| Node history | 1.5 µm (early 1980s) → 5 nm (~2022); G-line 436, I-line 365, KrF 248, ArF 193, ArFi 193, EUV ~13.5 nm | "Photon Sources vs. Moore’s Law" (chart labels: "1.5 µm", "1 µm", "800 nm", ..., "10 nm", "7 nm", "5 nm"; "Physical minimum feature size") **[slide image]**; source "https://doi.org/10.33079/jomm.19020202" | Litho p. 22 | Extend the course's own chart with a point for atomic placement (~0.4 nm). Note the slide's distinction between node names and "physical minimum feature size". |
| Moore's law | — | "Moore’s Law 1.0: scaling up – Doubling the number of transistors every 1–2 years" ; "Moore’s Law 2.0: scaling down – Shrinking transistor area lowers the cost of a transistor by about 30%/year" ; "Moore’s Law 3.0: Scaling Out (Innovation through Integration)" ; "Moore’s Law is primarily an economic law" | Class 1 pp. 30, 33, 35 | Donor qubits as "scaling out": a new device class, not a smaller transistor. |
| 3 nm nanosheet | — | "The Transistors are Nano! Nanosheet 3 nm 2022" | Class 1 p. 21 | — |
| Syllabus | Nanolitho week | "Nanolithography and Nanofabrication (1 week)" | Class 1 p. 15 | The tutorial fills that slot. |
| E-beam wavelength | λ = 12.3/√V Å; 30 kV → 0.07 Å; NA 0.002–0.005; resolution < 1 nm | "Example: 30 kV e-beam => λ = 0.07 Angstroms NA = 0.002 – 0.005 Resolution < 1 nm But beam current needs to be 10’s of mA for a throughput of more than 10 wafers an hour." | Litho p. 80 | Apply the same formula to STM electrons: λ = 12.3/√V Å → ≈6.2 Å at 4 V, ≈4.6 Å at 7 V [derived]. STM resolution comes from tunnelling locality, not diffraction. |
| E-beam practical resolution | 1.4 nm diffraction vs ~5–20 nm practical | "Practical resolution (~5–20 nm) is set not by diffraction but by (i) forward scattering of electrons in the resist, (ii) secondary-electron generation and range, (iii) resist molecular size and development, and (iv) backscatter from the substrate (proximity effect)." | Lithography Answer Key p. 4 (Problem 6a) | The STM "resist" is one H atom per Si, so resist molecular size is ~0.4 nm. |
| E-beam resist / dose | — | "E-beam resolution depends on photoresist and substrate" (p. 85) ; "The Proximity Effect Monte Carlo simulation of electron trajectories" (p. 81) | Litho pp. 81, 85 | Analogy: STM desorption dose (electrons per H) vs EBL dose. |
| Throughput vs resolution | — | "To get higher throughput 1) Larger spot size (Gaussian sytems) 2) Larger address grid (shaped beam systems) 3) Higher current (can result in electron-electron repulsion) 4) Faster stage (harder to control) Higher throughput always results in lower resolution" | Litho p. 92 | STM lithography sits at the extreme low-throughput, high-resolution end of this curve. |
| E-beam summary | 20 nm / 5 nm; hours per wafer | "2) High resolution (20 nm easily, 5nm with some work)" ; "1) Very slow (hours per wafer not wafers per hour)" ; "4) Multiple beams offer some hope" | Litho p. 94 | Multi-tip STM and the multi-beam analogy. |
| Serial vs parallel | — | "Photolithography VS E-beam lithography Needs a mask ... No mask needed Parallel ... Serial" | Litho p. 83 | STM = maskless and serial, like EBL. |
| Resist contrast | γ = 1/log10(D100/D0) | "Contrast γ = 1 / log₁₀(D₁₀₀ / D₀). DNQ-novolac ≈ 2–3; chemically amplified DUV resists reach 5–10." | Litho p. 45 | H-resist is binary at the atom level (H present or not). |
| EUV resist chain | — | "EUV: Photons -> Electrons -> Secondary electrons -> Acid" | Class 1 p. 40 | EUV ends up exposing resist with low-energy electrons too. |
| DOF problem | 382 nm vs 500 nm step | "DOF = 0.5 × 248 / 0.57² = 124 / 0.325 = 382 nm." ; "The 500 nm step exceeds the 382 nm focus budget" | `solutions_student PS1 1.pdf` p. 2 | STM needs atomically flat terraces, a far stricter version of "topography > DOF". |
| Lab litho | 2–8 µm lines; 0.2 µm vernier | "2, 3, 4, and 8 µm linewidths" (CM p. 16) ; "Vernier step = 0.2 µm" (CM p. 17) | CM pp. 16–17 | EE143 overlay is read to 0.2 µm; STM overlay (to buried δ-layer) needs registration markers at nm scale. |

---

## 5. Etching, Deposition, Metallization, Oxidation

### 5a. Etching (RIE) (`01_Lectures/Section 3  Etching.pdf`)

| Topic | Equation / number | Exact quote | File, page | Suggested slide tie-in |
|---|---|---|---|---|
| Figures of merit | — | "Etch Process - Figures of Merit • Etch rate • Etch rate uniformity • Selectivity • Anisotropy" | Etching p. 3 | RIE step that opens vias to the buried δ-layer. |
| Bias / anisotropy | b = (df − dm)/2; Af = 1 − b/hf | "Bias b = (df – dm)/2" ; "Complete Isotropic Etching Vertical Etching = Lateral Etching Rate" ; "Complete Anisotropic Etching Lateral Etching rate = 0 b = 0" | Etching pp. 4–5 | — |
| Selectivity | SAB = vA/vB; RIE SiO2/Si ≥ 10 | "SiO2/Si etched by RIE (e.g. CF4 plasma) SSiO2, Si Selectivity is finite ( ≥ 10 )" ; HF: "Selectivity is very large ( ~ infinity)" | Etching pp. 6–7 | Etching *to* a δ-layer has no etch stop: Si on Si, selectivity = 1. Must rely on timing. |
| Worst-case etch time | tT = hf(1+δ)(1+Δ)/[vf(1−φf)] | "Total worst-case etching time" ; "Fractional over-etch time to completely remove film = h1 / hf" | Etching p. 12 (repeated p. 62) | Apply to the via depth: δ-layer cap thickness × (1+δ) with no stop layer. |
| Substrate erosion | vsub·(t2 − t1) | "Worst-case substrate erosion = vsubstrate • (t2 - t1)" | Etching p. 13 | — |
| KOH Arrhenius | 0.15 eV gap → e⁵ ≈ 150 | "Ea ≈ 0.75 eV vs 0.60 eV → gap = 5 kT at 80 °C → e5 ≈ 150 → measured selectivity 100–400 : 1" ; "kT is only 30 meV at etch temperature — the rate ratio is exponential in the gap, not linear." | Etching p. 23 | Same exponential argument as D(T): a 0.13 eV EA difference between P and As changes D only ≈3× at 350 °C, while going from 1050 °C to 350 °C lowers D by ~10¹⁶ [derived]. |
| RF plasma | 13.56 MHz | "Plasma RF frequency = 13.56 MHz" | Etching p. 31 | — |
| RIE | — | "Reactive Ion Etching (RIE) ~ plasma wafers RF 13.56 MHz Parallel-Plate Reactor Plasma generates (1) Ions (2) Activated neutrals Enhance chemical reaction Sputtering" | Etching p. 34 | — |
| Remote plasma | 1–10 mTorr | "Pressure 1mTorr 10mTorr" ; "(1) Transformer Coupled Plasma (TCP) (2) Electron Cyclotron Resonance (ECR)" | Etching p. 35 | — |
| Si etch chemistry | Si + 4F → SiF4(gas) | "CF4 is an inert gas (Freon 14)" ; "Then chemically form volatile SiF4" **[slide image]** | Etching p. 41 (slide 42) | Fluorine RIE for mesa/via etch. |
| Anisotropy control | — | "1) ionic bombardment to damage expose surface. 2) sidewall coating by inhibitor prevents sidewall etching." | Etching p. 54 (slide 55) | — |
| Selectivity vs T | S = (A1/A2) exp[−(Q1−Q2)/kT] | "Temperature Dependence of Selectivity" | Etching p. 57 (slide 58) | — |
| RIE lag | — | "smaller trenches etch at a slower rate than larger trenches." | Etching p. 61 (slide 63) | Small vias to nanoscale leads etch slower. |
| Summary | — | "Selectivity Control - Gas mixture, Temperature • Anisotropy Control – Inhibitor deposition, Substrate bombardment" | Etching p. 68 | — |

### 5b. Thin-film deposition, vacuum, epitaxy (`01_Lectures/Section 5 - TF Deposition 2026.pdf`)

| Topic | Equation / number | Exact quote | File, page | Suggested slide tie-in |
|---|---|---|---|---|
| Monolayer rule | ~1 s at 10⁻⁶ Torr | "Assume close packed molecules, 3.6Å radius → 2.2 X 1014 cm2 At 300K for O2 at 10-6T: Φ = 3.6 X 1014 /cm2-s So one monolayer in ~0.6 sec. Good rule of thumb to remember! About one monolayer in 1 sec at 10-6T" | TF Dep p. 7 | Why STM work is done in UHV: at ~10⁻¹⁰ Torr the rule gives ~10⁴ s (≈3 h) per monolayer; the PS3 formula gives 2.2×10¹⁴/(3.8×10²⁰ × 10⁻¹⁰) ≈ 5800 s. [derived] |
| Impingement | Φ = 3.8×10²⁰ P (Torr) | "For air at 300K: Φ = 3.8 x 1020 P (P in Torr)" | TF Dep p. 6 | — |
| Mean free path | λ = 0.05/P(torr) mm | "λ = 6.6 / P(in Pa) = 0.05 / P(in torr)" | TF Dep p. 5 | — |
| Vacuum regimes | — | Chart "At 25oC" with regions "Residual Vacuum", "Plasma Processing", "CVD"; "1 meter!" ; "1 µm/min" **[slide image]** | TF Dep p. 8 | Place STM UHV chamber and PH3 dosing pressure on this chart. |
| Ideal gas | PV = NkT; kT = 3.1E-20 torr-liter at 300 K | "[Note] At T = 300 K ; kT = 3.1E-20 torr-liter" | TF Dep p. 3 | PH3 dose (Langmuir) from pressure × time. |
| Evaporation | < 10⁻⁵ Torr | "Thermal Evaporation Electron Beam Evaporation Gas Pressure: < 10-5 Torr" | TF Dep p. 11 | Al contacts are evaporated in both flows. |
| Sputtering | 1–10 mTorr | "Gas Pressure 1-10 m Torr" ; "heat substrate to ~ 300oC (optional)" | TF Dep p. 15 | — |
| **PH3 in CVD** | 350–500 °C | "(b)PSG :phospho silicate glass.[P2O5 + SiO2]" ; "4PH3 + 5O2 → 2P2O5 + 6H2" ; "SiH4 + O2 → SiO2 + 2H2 ↑" ; "350oC-500oC" **[slide image]** | TF Dep p. 27 | PH3 is already a course precursor; the qubit flow uses it on bare Si(001) in UHV with no O2. |
| Grove model | ks = ko exp(−Ea/kT); film rate = F3/N | "Surface reaction parameter kS = koexp (-Ea/kT)" ; "kS << hG Surface Reaction limited" ; "hG << kS Mass Transport limited" | TF Dep pp. 30, 32 | PH3 adsorption/dissociation is surface-reaction limited (in UHV, effectively zero transport resistance). |
| **Epitaxy** | 950–1150 °C | "Epitaxial Growth • Requires an ultra-clean Si surface prior to epi growth. • Requires deposition of Si at very high temperature for perfect crystallinity. Processing Temperature 950-1150oC" | TF Dep p. 43 | The qubit flow's 250 °C encapsulation (low-temperature MBE) is 700–900 °C colder than the course's epitaxy. That is what keeps the δ-layer sharp; trade-off is crystal quality. |
| ALD self-limiting | — | "The process involves two self-limiting half reactions that are repeated in cycles" ; "ALD is highly conformal and enables excellent thickness uniformity and control down to nm-scale" | TF Dep p. 44 | Analogy: PH3 dose on an H-resist window is self-limiting (saturates at the available bare sites). |
| MBE | — | **Not found** in the course PDFs (no "MBE"/"molecular beam"). | — | Introduce MBE as new. |
| Summary | — | "Epitaxial Growth - qualitative Atomic Layer Deposition (ALD) - qualitative" | TF Dep p. 48 | — |

### 5c. Metallization and contacts (`01_Lectures/Section 8 - Metallization.pdf`)

| Topic | Equation / number | Exact quote | File, page | Suggested slide tie-in |
|---|---|---|---|---|
| Interconnect needs | — | "low ohmic resistance – interconnects material has low resistivity • low contact resistance to semiconductor device • reliable long-term operation" | Metallization p. 6 | — |
| Tunnelling ohmic contact | N > 10¹⁹ cm⁻³ | "Tunneling “ohmic” contacts" ; "1019 - 1021/cm3" ; "> 1019/cm3" **[text layer lost superscripts: 10^19–10^21]** | Metallization p. 9 | δ-layer ≈10²¹ cm⁻³ is at the top of the course's tunnelling-contact range, provided the Al actually reaches the buried plane. |
| Schottky vs ohmic | — | "Small depletion width (highly doped Si)" → "Tunneling Ohmic Contact" ; "Large depletion width (lightly doped Si)" → "Thermionic emission" | Metallization p. 10 | At 4 K the lightly doped Si around the δ-layer freezes out, so only the tunnelling path works. |
| Contact resistance | Rc = ρc/A; ρc(metal–Si) ~ 10⁻⁵ to 10⁻⁷ Ω·cm² | "Rc = ρc / (contact area )" ; "ρc of Metal-Si contacts ~ 1E-5 to 1E-7 Ω-cm2" ; "ρc of Metal-Metal contacts < 1E-8 Ω-cm2" | Metallization p. 11 | 1 µm² contact at ρc = 10⁻⁶ Ω·cm² → Rc = 100 Ω. [derived] |
| Specific contact resistivity | ρc ≡ (∂J/∂V)⁻¹ at V≈0; ρc = ρc0 exp[(2√(m*εs)/ħ)(φB/√N)] | "Specific contact resistivity ρc ≡ (∂J/∂V)^-1 at V~0" ; "Approaches to lowering of contact resistance: 1) Use highly doped Si as contact semicodnuctor 2) Choose metal with lower Schottky barrier height" **[slide image]** | Metallization p. 12 | ρc falls exponentially with 1/√N: the δ-layer's very high N is what makes Al contact to it work. |
| Barrier heights | ΦB(n) + ΦB(p) = Eg | "Note: ΦB (n-type) + ΦB (p-type) = Eg of semiconductor" | Metallization p. 13 | — |
| Al spiking | Al–1 % Si; ~2 % Si | "Silicon absorption into the aluminum results in aluminum spikes" ; "Spikes can short junctions or cause excess leakage" ; "Sputter deposition of Al - 1% Si" (p. 16) ; "1. Add ~2% Si to Al to prevent Si outdiffusion 2. Use diffusion barrier layer to block Al/substrate interaction" (p. 17) | Metallization pp. 16–17 | Spiking through a δ-layer only tens of nm deep is the risk (and sometimes the intended mechanism) when contacting it. |
| Deposition | — | "Sputtering has been the technique of choice" | Metallization p. 24 | — |
| Four-point probe | see §3 | — | Metallization pp. 14–15 | — |

### 5d. Oxidation and native oxide (`01_Lectures/Section 4 - Oxidation.pdf`)

| Topic | Equation / number | Exact quote | File, page | Suggested slide tie-in |
|---|---|---|---|---|
| SiO2 as dopant mask | DSiO2 ≪ DSi | "(5) SiO2 is a good diffusion mask for common dopants ... e.g. B, P, As, Sb." ; "*exceptions are Ga (a p-type dopant) and some metals, e.g. Cu, Au" | Oxidation p. 3 | Course mask = ~100s nm oxide; STM mask = 1 monolayer of H. |
| HF selectivity | — | "(6) Very good etching selectivity between Si and SiO2." | Oxidation p. 4 | — |
| Si consumption | 0.46 | "1µm Si oxidized 2.17 µm SiO2" ; Xsi = 0.46 Xox | Oxidation p. 9 | Any oxide on the cap consumes Si; a few nm of native oxide eats into a thin cap over the δ-layer. |
| Thin-oxide correction | Xi = 30 nm | "The Deal-Grove model provides excellent agreement with experimental data except for thin (<20 nm) SiO2 grown in O2" ; "assume Xi = 30 nm when using the Deal-Grove equations" | Oxidation p. 28 | This is a fit parameter, **not** a native-oxide thickness. |
| Forming gas H passivation | 400–450 °C, 10 % H2 | "A final annealing step at 400-450oC is performed with 10%H2+90%N2 ambient (“forming gas”) after the IC metallization step." | Oxidation p. 37 | Same chemistry as the resist: H atoms passivate Si dangling bonds. The course uses it to fix interface states; STM lithography uses it as a resist and removes it one atom at a time. |
| Dopant segregation | m = C_Si/C_SiO2 | "Segregation Coefficient m ≡ equilibrium dopant conc. in Si / equilibrium dopant conc. in SiO2" ; "m > 1, slow diffusion in SiO2. ... e.g. P, As, Sb ⇒ dopant piling up near Si interface for P, As & Sb" | Oxidation pp. 43, 45 | Closest course concept to the δ-layer's real broadening mechanism (P segregation at a moving growth front). |
| Oxidation T | 900–1100 °C | "Processing Temperature 900-1100 oC" | Overview p. 16 | — |
| **Native oxide thickness** | — | **Not found as a number.** Qualitative only: "Dip in 12:1 BHF for 5 seconds, agitating gently. This HF dip removes the native oxide." (PM p. 10); "Dip wafers into the 12:1 BHF solution for 20 s to remove any native oxide" (PM p. 13); "Clean the wafers just before they are put into evaporator in order to minimize the time native oxide can grow." (PM p. 21) | PM pp. 10, 13, 21 | Take a native-oxide number (~1–2 nm) from outside the course and cite it separately. |
| Hydrophobic = bare Si | — | "Etching is complete when the etchant “beads” on bare Si (SiO2 is hydrophilic, but bare Si is hydrophobic)" | PM p. 9 | The hydrophobic HF-last surface students see is H-terminated Si (my interpretation, not stated in the course): a wet, rough cousin of the UHV H:Si(001) resist. |

---

## 6. EE143 lab process vs qubit flow (side by side)

Left columns are from the EE143 lab documents. The qubit column restates the user's brief (H:Si(001) resist, STM HDL, PH3/AsH3, 350 °C incorporation, low-T epitaxy, δ-layer ~10¹⁴ cm⁻² and <1 nm, RIE + Al, Hall bar/4-pt). It is not sourced from the course.

| Step | Our lab does (exact quote) | File, page | Qubit flow does | Hook |
|---|---|---|---|---|
| Substrate | "Begin with 3” p-type silicon wafers with 10 Ω· cm to 20 Ω· cm resistivity and ⟨100⟩ crystal orientation." ; "Each wafer has a thickness of 381 ± 25 µm." | PM p. 5 | Si(001), the same ⟨100⟩ orientation | Same crystal face; the qubit flow uses its 2×1 reconstructed surface. |
| Background implant | "Blanket implant with type 11B+, a dose of 3.0 × 1012 cm−2, energy of 60 keV, and 7◦ tilt." | PM p. 5 | δ-layer 1×10¹⁴ cm⁻², no implant | δ-layer dose is ≈33× the lab's B implant; the 7° tilt matches Implantation p. 21. |
| Pre-furnace clean | "Follow the standard msink6 procedure to clean the wafers in piranha, 25:1 HF, HCl, and HF again" (p. 5) ; "Dip in 12:1 BHF for 5 seconds ... This HF dip removes the native oxide." (p. 10) | PM pp. 5, 10 | UHV flash-clean + atomic-H termination | Wet HF-last vs UHV monohydride. |
| Field oxidation | "Oxidize wafers (including controls) at 1000 ◦C for 5-90-5 minutes (dry-wet-dry)." ; "In 2021 ... 125 min wet oxidation step which grew 522 nm oxide. In 2023 ... 88 min and obtained 445 nm." ; NanoLab sheet: "5min -120min -5min dry-wet-dry oxidation Grew 6000 angstroms" | PM pp. 5–6; `03_Lab/NanoLab wafer processing.pdf` p. 1 | None; the H monolayer is the "field" mask | 500 nm oxide mask vs ~0.1 nm H mask. |
| Lithography | "3000 RPM spin speed for 30 s, which should result in a photoresist film about 1 µm thick" ; "Fall 2026 suggested exposure time (based on TA calibration): 10 s" ; "Underexposing is much worse than overexposing" | PM pp. 7–8 | STM tip bias pulses remove individual H atoms | 1 µm resist / 2 µm lines vs one-atom resist / one-dimer pixels. |
| Gate oxidation | "Use tube #3 (bottom) at 1100 ◦C." ; "Let the wafers oxidize for approximately 60 min" ; "The target is 1000 ˚A." | PM pp. 10–11 | No oxide on the device | — |
| Poly-Si with PH3 | "Deposit 4000 ˚A Phosphorus-doped polysilicon in tystar10" ; "The standard tystar10 process temperature is 615 ◦C." ; "The furnace uses silane to supply silicon and phosphine for phosphorus for n-type doping." ; NanoLab: "131 min at 615 degrees Celsius" | PM p. 12; NanoLab p. 1 | PH3 dosed at room temperature onto patched H-free windows | **Our lab already uses PH3**, in a 615 °C furnace for blanket doping. Even that step moves P only ≈0.2 nm (2√(Dt), [derived]). |
| Doping | "Spin ... Filmtronics Phosphorosilica P509 spin-on glass (SOG) at 3000 RPM for 20 s." ; "Use furnace tube #2 (center) at 1050 ◦C." ; "Hold 10 minutes in hot zone." ; "decreased about two orders of magnitude to ≈4 Ω/□" | PM pp. 15–16 | PH3 adsorbs only where H was removed; 350 °C incorporates P into the lattice | 1050 °C SOG predep vs 350 °C incorporation; Rs ≈4 Ω/□ vs δ-layer ~10²–10³ Ω/□. |
| Drive-in | "Drive-in and wet oxidize wafers (and control(s)) in furnace tube #2 at 1050 ◦C." ; "Allow wafers to wet oxidize for approximately 12 min" ; "Anneal for 20 minutes in N2." | PM pp. 17–18 | Deliberately none | 2√(Dt) ≈ 300 nm (lab) vs ~10⁻⁴ nm (qubit) [derived]. |
| Encapsulation | (no epitaxy step in the lab flow) | — | Low-T Si overgrowth (~250 °C) | Course epi is 950–1150 °C (TF Dep p. 43). |
| Contact etch | "Pour buffered 6:1 HF (BHF) ... The etch rate of thermal SiO2 using 6:1 BHF is ≈1000 ˚A min−1 at 25 ◦C." ; "An overetch (50% or even 100%) is strongly preferred to an underetch for this step" | PM pp. 8, 19 | RIE through the Si cap to the δ-layer | Wet isotropic vs dry anisotropic; no etch stop in the qubit case. |
| Metal | "Ideally the vacuum would reach 2 × 10−6 torr to 5 × 10−6 torr. At this pressure, the flux of the residual gases (mostly H2O) is about 1% of the Al flux during deposition." ; "wait only until the pressure is below 1 × 10−5 torr" ; "We want the aluminum thickness to be greater than about 100 nm." | PM pp. 22–23 | Evaporated Al contacts to the buried δ-layer | Same tool class. |
| Metal etch | "The etch rate of Al is ≈530 nm/min at 50 ◦C." ; "Al etchant has a composition of approximately 80% Phosphoric acid, 10% H2O, 5% acetic acid, and 5% nitric acid." | PM p. 24 | Lift-off or etch | — |
| Sinter | "Sinter wafers in furnace tube 1 at 400 ◦C in forming gas (90% N2, 10% H2) for 20 min." ; "It allows the aluminum and silicon to interdiffuse, forming a good contact. It also allows hydrogen atoms from the forming gas to diffuse into the silicon and tie up surface states at the oxide channel interface." | PM p. 25 | Any post-metal anneal must keep the thermal budget low | 400 °C × 20 min is hotter than the 350 °C incorporation, yet P still moves only ~3×10⁻⁵ nm [derived]; the risk is Al–Si interdiffusion/spiking, not P diffusion. |
| Measure | "Use four-point probe to measure sheet resistance of deposited aluminum" ; CM "2A & 2B – 4155B - SHEET Mode" | PM p. 22; CM p. 7 | 4-pt + Hall bar at cryogenic T | 4-pt carries over; Hall is new. |
| Lab-report question | "10. For two different processes, please explain how they could be replaced with a different process you learned about in lecture, and the pros and cons of doing so (e.g., replacing spin-on glass with ion implantation)." | Lab Report p. 11 | Replace SOG with STM δ-doping | Closing slide: answer Q10 with the qubit flow. |

---

## 7. Problem-set analogues

No problem set covers ion implantation or diffusion directly. PS1 is scaling and lithography, PS2 oxidation, PS3 deposition, plus Section 2 (lithography) and Section 3 (etching) problem sets. The nearest analogues:

| Problem | What it asks | Exact quote | File, page | Qubit-deck analogue |
|---|---|---|---|---|
| Lab Report "Dopants (15 pts)" | Hand-calculate P and B profiles and sheet resistance | "Using hand calculations with the equations you have learned from class and the Jaeger textbook, calculate the distribution of dopants vs. wafer depth in the N-doped areas of the final wafer." ; "Don't forget to account for diffusion from each furnace step." | `03_Lab/Lab Report 1 2.pdf` p. 8 (table on p. 9) | The δ-layer version of this calculation: Σ(Dt) for every hot step (table 2a/2b), then Rs = 1/(qNsμ). |
| Lab Report "Aluminum (5 pts)" | Rs of 100 nm Al | "Assuming the ideal thickness of evaporated aluminum is 100nm, please compute the sheet resistance of this film. (hint: look up the value for aluminum bulk resistivity)" | Lab Report p. 9 | Answer 0.28 Ω/□ (ρ = 2.8 µΩ·cm, Metallization p. 8) [derived]; compare with δ-layer kΩ/□. |
| Lab Report "Doping (5 pts)" | Theory vs measured Rs | "Compare the theoretical and measured wafer doping profiles by using sheet resistance" | Lab Report p. 10 | Same theory-vs-measurement check δ-layer papers make (Hall Ns vs STM-counted dose). |
| PS1 Q2(b)–(c) | R = k1λ/NA and DOF for a KrF stepper | "For the stepper, compute the resolution R = k1λ/NA at k1 = 0.5 and at k1 = 0.25." ; solutions: 218 nm, 109 nm, DOF 382 nm | `problems PS1 1.pdf` p. 2; `solutions_student PS1 1.pdf` pp. 1–2 | Redo for EUV 13.5 nm and contrast with STM. |
| Section 2 Problem 1(d) | EUV R and DOF at NA 0.33 / 0.55 | "An EUV scanner uses λ = 13.5 nm with NA = 0.33; the newest high-NA tool has NA = 0.55. ... compute R and DOF for both." | `Section_2_Lithography_Problems.pdf` p. 1; key p. 1 | EUV scaling slide numbers (14 nm / 8.6 nm). |
| Section 2 Problem 3(d) | Time per field | "Modern scanners expose ~230 wafers per hour with ~100 fields per wafer. Estimate the exposure time budget per field." | Problems p. 3; key p. 2 | Contrast ~0.16 s per field with STM patterning time per device. |
| Section 2 Problem 6(a),(d) | De Broglie λ, throughput knobs | "Compute the de Broglie wavelength of a 30 keV electron." ; "(d) Give four knobs that increase EBL throughput and state, for each, what it costs in resolution or beam quality." | Problems p. 4; key p. 4 | Same formula at STM bias (4–7 V → 4.6–6.2 Å); same throughput/resolution trade. |
| PS2 header | Arrhenius constants C exp(−Ea/kT) | "Each constant follows C exp(−Ea/kT)." ; "Useful: k = 8.617 × 10−5 eV/K." | `PS2_oxidation_problems.pdf` p. 1 | Same form as D = D0 exp(−EA/kT). |
| PS2 Q4(a) | Si atomic density | "SiO2 has a molecular density of 2.3 × 1022 cm−3 and silicon an atomic density of 5.0 × 1022 cm−3." | PS2 p. 4 | 10¹⁴ cm⁻² in 1 nm = 10²¹ cm⁻³ = 2 % of Si atoms [derived]. |
| PS2 Q5(e) | Segregation | "Boron has a segregation coefficient m ≈0.3 and phosphorus m ≈10" | PS2 p. 5 | P pile-up/segregation, the real δ-broadening mechanism. |
| PS3 header | Monolayer density | "one monolayer ≈2.2×1014 sites/cm2" | `PS3_deposition_problems.pdf` p. 1 | 10¹⁴ cm⁻² ≈ 0.45 of the course's "monolayer". Against the actual Si(001) surface atom density (6.8×10¹⁴ cm⁻², not in course) it is ≈0.15 ML. [derived] Say which reference you use. |
| PS3 Q1(b) | Monolayer time | "Compute the residual-gas impingement flux and the time to form one monolayer at 3 × 10−6 and 5 × 10−5 Torr." ; solution: "one monolayer every 0.19 s" / "every 12 ms" | PS3 p. 1; solutions p. 1 | Extend to UHV: ~10⁴ s at 10⁻¹⁰ Torr [derived]. |
| PS3 Q1(c) | t = ρ/Rs for Al | "t = ρ/Rs with ρAl ≈2.7 µΩ·cm, so 1 µm corresponds to about 27 mΩ/sq." | PS3 solutions p. 1 | Contact metal check. |
| PS3 Q5(d) | Arrhenius sensitivity per K | "d ln v/dT = Ea/kT 2 = 1.7/(8.617 × 10−5 × 8982) = 2.4% per K." | PS3 solutions p. 4 | For P diffusion at 350 °C: EA/kT² ≈ 11 % per K [derived]. |
| PS3 Q5(e) | ALD self-limiting growth | "Each half-reaction saturates once all surface sites have reacted, so the growth per cycle is fixed by surface chemistry" | PS3 solutions p. 4 | PH3 saturation dose on an H-free window. |
| Section 3 Problem 2 | Worst-case over-etch | "What is the total worst-case etch time required to guarantee the film is fully removed" | `Section_3_Etching_Problems.pdf` pp. 1–2 | Via etch to the δ-layer with no stop layer. |
| Section 3 Problem 4(c) | Arrhenius selectivity vs T | "A plasma etches two materials with Arrhenius rates R = A exp(−Q /kT)" ; key: "S increases with temperature (heating favors the higher-...)" | Etching Problems p. 3; `Section_3_Etching_Answer_Key.pdf` p. 3 | Same math as comparing D_P and D_As vs T. |

---

## 8. Requested but not found in the course PDFs

- Hall effect, Hall coefficient, van der Pauw: no occurrence.
- Rs = 1/(q N μ) as an explicit equation: not printed (only Rs = ρ/t and v = μE).
- Native oxide thickness as a number: not given (qualitative HF-dip statements only).
- MBE / molecular beam epitaxy, low-temperature epitaxy: not mentioned; epitaxy only "950-1150oC" (TF Dep p. 43).
- Rp/ΔRp *tables*: only charts (Implantation p. 12, p. 14); numbers above are digitized. No values below 10 keV.
- Implant "statistics/precision" beyond "A few %" dose control and "< 1%" lateral uniformity: no discussion of Poisson counting or single-ion placement.
- Damage/anneal temperatures: only ">900oC" (Implantation p. 4), "900oC-1000oC" (Overview p. 26), the 950 °C/10 s and 1050 °C/10 s RTA examples (Implantation p. 29), and TED "900oC, several sec" (Diffusion p. 31). No solid-phase-epitaxy regrowth temperature (~500–600 °C) is given.
- Specific EBL resist names (PMMA, HSQ) and doses in µC/cm²: not given.
- Hydrogen desorption temperature or STM: not mentioned.
