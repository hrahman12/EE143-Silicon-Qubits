# Landmark donor-qubit devices: verbatim geometry specs

Compiled 2026-11-21 for redrawing the devices in the deck. Every value below is a verbatim quote from the source named in the table, located by PDF page (arXiv preprint pagination), figure caption or section. Nothing comes from memory. Where a requested number was not in an accessible copy, the table says **not found** or **not accessible**.

Transcription conventions: PDF ligature glyphs (ﬁ, ﬀ) are written as plain letters, words hyphenated across line breaks are rejoined, and "˚A" from the PDF text layer is written as Å. No other changes were made.

## Access summary

| Key | Open full text obtained? | Copy used | Licence of copy |
|---|---|---|---|
| Fuechsle2012 | **No.** Nature Nanotech landing page has the abstract only; OpenAlex and Semantic Scholar list it as closed; Purdue e-Pubs and CiteSeerX entries are metadata only; not on arXiv | Abstract only | Publisher copyright (no reuse) |
| Schofield2003 | Yes | arXiv cond-mat/0307599v1 | arXiv "assumed-1991-2003" licence (arXiv's perpetual non-exclusive distribution licence, assumed for pre-2004 submissions). **Not CC BY** |
| Kane1998 | **No** (Nature, closed). Substitutes used: Kane's own 2000 architecture review (arXiv quant-ph/0003031) and O'Brien et al. 2001 PRB (arXiv cond-mat/0104569), which restates the architecture | Substitutes | Both arXiv "assumed-1991-2003" (non-exclusive). **Not CC BY** |
| OBrien2002 (SMS) | **No.** IOP PDF is behind a Cloudflare challenge (HTML returned); UCL Discovery 403; Bristol Pure page has no file | Abstract (OpenAlex) only | Publisher |
| He2019 | **No.** UNSWorks lists the published PDF (CC BY-NC-ND 3.0 AU, 3,540,307 bytes), but the server returns 1 byte (range request gives 416; browser UA gives 403). Not on arXiv or in PMC | Abstract only | (UNSWorks copy would be CC BY-NC-ND, which allows no derivatives) |
| Koch2019 | **No.** Same UNSWorks failure (CC BY-NC-ND 3.0 AU listed, 1,873,531 bytes, 1 byte served). Not on arXiv or in PMC | Abstract only | (same) |
| Oberbeck2002 | Yes | arXiv cond-mat/0208355 | arXiv "assumed-1991-2003" (non-exclusive). **Not CC BY** |
| Ruess2004 | **No.** ACS closed; UCL Discovery (eprint 170062) 403 via Cloudflare; not on arXiv | Nothing | Publisher |
| Schofield2025 roadmap (secondary) | Yes (local file) | arXiv 2501.04535v2 (Nano Futures 9, 012001 (2025)) | **CC BY 4.0**, the only CC BY source here |

Figure reuse: none of the primary landmark sources is under a CC BY copy. All figures must be redrawn from the numbers below. Only figures in the Schofield2025 roadmap (CC BY 4.0) could be reused with attribution.

Files saved under `/home/user/EE143-Silicon-Qubits/figures/raw/<Key>/`:
- PDFs: `Schofield2003/arxiv_cond-mat_0307599.pdf`, `Oberbeck2002/arxiv_cond-mat_0208355.pdf`, `Kane1998/arxiv_quant-ph_0003031_Kane2000.pdf`, `OBrien2001/arxiv_cond-mat_0104569.pdf`.
- Abstract text from the Nature landing pages: `Fuechsle2012/`, `He2019/`, `Koch2019/` and `Kane1998/` each hold a `nature_landing_abstract.txt`.
- Metadata only: `OBrien2002/openalex_metadata.json` and `Ruess2004/openalex_metadata.json`.

---

## 1. Fuechsle2012: "A single-atom transistor", Nat. Nanotechnol. 7, 242 (2012), doi:10.1038/nnano.2012.21

Source: https://www.nature.com/articles/nnano.2012.21 (abstract only). Licence: publisher copyright, paywalled.

| Spec | Value | Verbatim quote | Location |
|---|---|---|---|
| P atom placement accuracy | one lattice site | "an individual phosphorus dopant atom has been deterministically placed within an epitaxial silicon device architecture with a spatial accuracy of one lattice site" | Abstract |
| Lithography | STM + H-resist | "we use a combination of scanning tunnelling microscopy and hydrogen-resist lithography to demonstrate a single-atom transistor" | Abstract |
| Operating temperature | liquid He; mK transport | "The transistor operates at liquid helium temperatures, and millikelvin electron transport measurements confirm the presence of discrete quantum levels" | Abstract |
| Charging energy | close to bulk (no number in abstract) | "We find a charging energy that is close to the bulk value, previously only observed by optical spectroscopy" | Abstract |
| Source–drain gap, gate–gate separation, lead widths, δ-layer density, encapsulation thickness, number of P in leads, binding energy value | **not accessible** (full text closed) | — | — |
| Figure titles (for redraw reference) | — | "Figure 1: Single-atom transistor based on deterministic positioning of a phosphorus atom in epitaxial silicon. Figure 2: Calculation of the donor potential within the device architecture. Figure 3: Electronic spectrum of a single-atom transistor." | Landing page figure list |

Secondary (CC BY 4.0, Schofield2025 roadmap, arXiv 2501.04535v2): "Using atomic precision P-dopant placement and encapsulation in an epitaxial silicon layer, a variety of functional devices have been fabricated, including single atom transistors [1,2]" (p. 16, §2.3). This gives no dimensions.

---

## 2. Schofield2003: "Atomically precise placement of single dopants in Si", PRL 91, 136104 (2003), doi:10.1103/PhysRevLett.91.136104

Source: https://arxiv.org/abs/cond-mat/0307599 (PDF https://arxiv.org/pdf/cond-mat/0307599, v1, 24 Jul 2003). Licence: arXiv assumed-1991-2003 (http://arxiv.org/licenses/assumed-1991-2003/), non-exclusive, **not CC BY**.

| Spec | Value | Verbatim quote | Location |
|---|---|---|---|
| Single-P lithography site | ~1 nm diameter, ~3 dimers | "H-terminated Si (001) with a ∼1 nm diameter H-desorption point (∼3 dimers long)" | Fig. 4(a) caption, p. 4 |
| Single-P site (text) | 2–3 dimers exposed | "a controlled desorption site of diameter ∼1 nm, exposing just two or three of the substrate Si dimers" | p. 3, col. 2 |
| Two-P separation | ~12 nm | "Two H-desorption sites separated by ∼12 nm." ... "The separation of these two P atoms (∼12 nm) is of the order of the 20 nm separation required for the P qubit array of the Kane solid-state quantum computer [3]." | Fig. 4(c),(d) caption, p. 4 |
| Placement accuracy | ~1 nm | "We demonstrate the positioning of single P atoms in Si with ∼1 nm accuracy" | Abstract, p. 1 |
| Large patch | 200 × 30 nm² | "200 × 30 nm2 rectangular patch" | Fig. 1(a) caption, p. 2 |
| Finest lithography | single H at ~0.75 nm intervals | "we have desorbed single H atoms by pulsing the STM tip at ∼0.75 nm intervals" | p. 1, col. 2 |
| Line widths | ~2 nm; ~4 nm | "a ∼2 nm wide line of exposed Si" (p. 1); "two perpendicular ∼4 nm wide lithographic lines" | p. 1 col. 2; Fig. 3 caption p. 4 |
| Desorption conditions | +4 V, 1 nA; 40 nm/s | "The desorption parameters used were +4 V sample bias and 1 nA tunnel current." / "moving the tip with a velocity of 40 nm/s while applying tunneling conditions of +4 V sample bias and 1 nA tunnel current" | Fig. 1 caption p. 2; Fig. 3 caption p. 4 |
| PH3 dose | 0.3 L | "dosed with 0.3 Langmuir (L = 0.75 × 10−6 mbar s) of PH3 gas at room temperature" | p. 1, col. 2 |
| PH3 dose rate / fluence | 10⁻⁹ mbar, 0.3 L | "with the low dose rate and fluence used here (10−9 mbar and 0.3 L) we have observed an almost complete absence of adsorption at single H desorption sites" | p. 3, col. 2 |
| Higher dose (avoid) | 10⁻⁸ mbar, ~3 L | "Using both higher PH3 dose rates (10−8 mbar chamber pressure) and total doses (∼3 L), we have noted the adsorption of PH3 at single H desorption sites" | p. 3, col. 2 |
| Incorporation anneal | ~350 °C | "Here, we use an anneal temperature of ∼350◦C, which we find is sufficient to incorporate P atoms, while being below the H-desorption temperature." | p. 2, col. 2 |
| Prior (H-incompatible) anneal | ~550 °C | "formation of P-Si heterodimers upon annealing PH3 dosed surfaces to ∼550◦C. However, at this temperature all H is desorbed" | p. 2, col. 2 |
| Surface prep | flash 1200 °C | "flash-annealed to 1200◦C, cooled to room temperature and dosed with 0.01 L PH3" | p. 2, col. 1 |
| P desorption | ~750 °C | "annealing to ∼750◦C causes the removal of the P-Si heterodimers" | p. 3, col. 1 |
| Heterodimer height (H-terminated) | ~0.04 nm | "Line profile taken over a single P-Si-H heterodimer, showing a ∼0.04 nm height increase due to tunneling from the P lone pair orbital" | Fig. 3(d) caption, p. 4 |
| Heterodimer height (clean surface) | ~0.03 nm | "We measure a ∼0.03 nm height increase of the P-Si heterodimer compared to the neighbouring Si dimers" | p. 3, col. 1 |
| PH3 apparent height | ~0.07 nm | "molecularly adsorbed PH3 with an apparent height of ∼0.07 nm above the substrate dimer rows" | p. 2, col. 1 |
| Ejected Si chains | ~0.14 nm, perpendicular to rows | "These 1D lines run perpendicular to the underlying dimer rows ... The apparent height (∼0.14 nm) and orientation of these 1D lines confirm that they are single dimer rows of epitaxial Si" | p. 2, col. 2 |
| Dimer-row geometry / adsorbate order | c(4×2) PH3, p(2×2) PH2 | "adsorbed PH3 molecules by their appearance as circular protrusions centered on the dimer rows and ordered into a c(4×2) periodicity" / "PH2 molecules as adsorbate protrusions positioned asymmetrically about the dimer rows and ordered with a p(2×2) periodicity" | p. 1, col. 2 |
| Dimer-row pitch / dimer spacing (Å) | **not found**: the paper gives no numeric dimer-row spacing | — | — |
| Imaging conditions | −1.6 V, 0.1 nA | "Parameters for all STM images were -1.6 V and 0.1 nA except (d), which was imaged at +1.6 V." | Fig. 2 caption, p. 2 |
| Images available | Figs 1–4 | Fig. 1: lithography and PH3/PH2 adsorption; Fig. 2: PH3 dose and 350 °C anneal; Fig. 3: P along two ~4 nm lines; Fig. 4: single P and two P ~12 nm apart | pp. 2–4 |

---

## 3. Kane1998: "A silicon-based nuclear spin quantum computer", Nature 393, 133 (1998), doi:10.1038/30156

Primary: **not accessible.** Nature lists it as closed and OpenAlex and Semantic Scholar have no open copy. From the landing page (https://www.nature.com/articles/30156), the only public items are the abstract and figure titles. Figure 1 title: "Illustration of two cells in a one-dimensional array containing 31 P donors and electrons in a Si host, separated by a barrier from metal gates on the surface." Figure 2 title: "An electric field applied to an A gate pulls the electron wavefunction away from the donor and towards the barrier, reducing the hyperfine interaction and the resonance frequency of the nucleus." The abstract and figure titles contain no numbers.

### 3a. Substitute: B. E. Kane, "Silicon-based quantum computation", Fortschr. Phys. 48, 1023 (2000), arXiv quant-ph/0003031

Source: https://arxiv.org/abs/quant-ph/0003031. Licence: arXiv assumed-1991-2003 (non-exclusive). **Not CC BY.** This is Kane's own later description of the same architecture, not the 1998 paper.

| Spec | Value | Verbatim quote | Location |
|---|---|---|---|
| Donor and gate spacing | ~100 Å (10 nm) | "the donors and gates must be spaced of order 100 Å apart, a scale which is near the limit of current nanofabrication technology" | §V, p. 4 |
| Donor spacing (Fig. 5) | ~100 Å | "This requirement means the donor spacing must be of order 100 Å." | Fig. 5 caption, p. 5 |
| Donor spacing (restated) | ~100 Å | "these spins must be extremely close together (∼100 Å) for the computer to operate" | §IX, p. 8 |
| Bohr radius / binding energy | 15–30 Å; 10–50 meV | "an expanded Bohr radius (aB ≅15-30 Å) and a reduced binding energy (Eb ≅ 10-50 meV)" | §II, p. 2 |
| Magnetic field / temperature | B ≃ 1 T, T ≃ 0.1 K | "Strong polarization of the electrons requires both high magnetic fields (B ≃1 T) and very low temperatures (T ≃0.1 K). These conditions were assumed in the original quantum computer proposal" | §IV, p. 4 |
| Field / temperature (figure) | 100 mK, 1 T | "While T=100 mK and B=1 T (filled circle) may readily be obtained in the laboratory" | Fig. 2 caption, p. 3 |
| Relaxation-time limit | T ≤ 4 K | "the long relaxation times of Si:P necessary for quantum computation only occur at T ≤4 K" | §IV, p. 4 |
| A-gate placement | directly above donor, over barrier | "A metal “A-gate” is located directly above a donor site, separated by a barrier from the Si semiconductor material" | §V, p. 4 |
| J-gate placement | between donors | "a “J-gate” lying between donor sites (Fig. 4)" | §V, p. 4 |
| Brf | 10⁻³ T | "A reasonable value of Brf is 10−3 T." | §VI, p. 5 |
| Barrier material | Si/SixGe1−x (SiO2/nitride problematic) | "Silicon oxide and nitride layers - used in conventional MOS structures - are amorphous materials, and their interfaces with Si will inevitably contain charge centers ... rendering their use in a quantum computer highly problematic" | §X, p. 11 |
| Barrier / well thickness | ~200 Å strained Si well in Si0.85Ge0.15 | "For Si/Si0.85Ge0.15 this thickness is approximately 200 Å, sufficiently thick so that the electron wavefunction of a donor in the center of the well is almost entirely in pure Si." | §X, p. 11–12 (Fig. 12 shows "200 Å" and "Si0.85Ge0.15") |
| Well depth (energy) | ~100 meV | "the depth of the well is about 100 meV" | §X, p. 12 |
| Donor depth below surface, A-gate width, J-gate width | **not found** in this source | — | — |

### 3b. Substitute: O'Brien et al., "Towards the fabrication of phosphorus qubits for a silicon quantum computer", PRB 64, 161401(R) (2001), arXiv cond-mat/0104569

Source: https://arxiv.org/abs/cond-mat/0104569. Licence: arXiv assumed-1991-2003 (non-exclusive). **Not CC BY.** This is the companion PRB paper by the same group, not the 2002 Smart Mater. Struct. paper.

| Spec | Value | Verbatim quote | Location |
|---|---|---|---|
| Kane donor spacing (as restated) | ~20 nm | "with phosphorus qubits embedded in silicon approximately 20 nm apart. This separation allows the donor electron wavefunctions to overlap, whilst an insulating barrier isolates them from the surface control A and J gates." | p. 1, col. 1 |
| Required qubit spacing | 20 nm | "The distance between sites can easily be increased to the required qubit spacing of 20 nm" | p. 3 |
| Barrier | insulating | "isolated from surface metal A and J gates by an insulating barrier" | Fig. 1 caption, p. 2 |
| Desorption sites | <1 nm, pitch ~4 nm | "three < 1 nm diameter hydrogen desorption sites in a row with a pitch of ∼4 nm" | p. 3 |
| Encapsulation plan | 10–30 Å at low T, then ~500 K | "10-30 Å of epitaxial silicon can be grown at low temperatures, down to room temperature to encapsulate the phosphorus, followed by elevated temperature growth at ∼500 K to maintain crystallinity" | p. 2 |

**Discrepancy to flag on the slide:** Kane's own 2000 text says donor spacing "of order 100 Å" (~10 nm). The UNSW papers (O'Brien 2001; Schofield 2003, Fig. 4 caption) say "20 nm" for the Kane array. Without the 1998 paper, I cannot say which number Kane 1998 used. The Schofield2025 roadmap (CC BY 4.0, p. 5, §1) adds a precision figure, not a spacing: "achieving the positional accuracies of approximately 15 nm required for device architectures such as the Kane quantum computer remains a challenge".

### 3c. OBrien2002 (Smart Mater. Struct. 11, 741), doi:10.1088/0964-1726/11/5/318

**Full text not accessible.** The IOP PDF URL returned a Cloudflare challenge page. OpenAlex calls it "bronze" OA, but it could not be fetched here. The OpenAlex abstract has no dimensions; it says only "fabrication of atomically precise arrays of single phosphorus bearing molecules on a silicon surface".

---

## 4. He2019: "A two-qubit gate between phosphorus donor electrons in silicon", Nature 571, 371 (2019), doi:10.1038/s41586-019-1381-2

Source: https://www.nature.com/articles/s41586-019-1381-2 (abstract only). UNSWorks lists an open published copy (https://unsworks.unsw.edu.au/bitstreams/bb6cfc8c-c272-4253-8844-4f059aaa6ece/download, licence CC BY-NC-ND 3.0 AU), but the server returned only 1 byte of the 3.5 MB file, so **the full text was not obtained.**

| Spec | Value | Verbatim quote | Location |
|---|---|---|---|
| Gate time | ~800 ps √SWAP | "Here we report a fast (about 800 picoseconds) √SWAP two-qubit exchange gate between phosphorus donor electron spin qubits in silicon" | Abstract |
| Readout fidelity | ~94% | "using independent single-shot spin readout with a readout fidelity of about 94 per cent on a complete set of basis states" | Abstract |
| Placement | atomic-scale engineering | "By engineering qubit placement on the atomic scale" | Abstract |
| Donor cluster sizes (2P/1P), 13.0 ± 0.5 nm separation, SET distance, gate layout, exchange values, B field, temperature | **not accessible**: the 13.0 ± 0.5 nm figure could **not** be verified | — | — |
| Figure titles | — | "Fig. 1: High-fidelity, independent single-shot spin readout of two donor qubits. Fig. 2: Electrostatic control over the electron-exchange interaction. Fig. 3: Exchange-driven coherent spin–spin oscillations. Fig. 4: Two-qubit SWAP gate with truth table." | Landing page |

Secondary (Schofield2025 roadmap, CC BY 4.0, p. 25, §3.1): "extremely fast (0.8ns) two-qubit exchange or √SWAP gates have been demonstrated between two phosphorus multi-nuclear spin registers in natural silicon [HE2019]". In the PDF text layer "√SWAP" appears as "ÖSWAP", a font artefact. This adds **natural Si** and **multi-nuclear registers**, but no cluster sizes or separation.

---

## 5. Koch2019: "Spin read-out in atomic qubits in an all-epitaxial three-dimensional transistor", Nat. Nanotechnol. 14, 137 (2019), doi:10.1038/s41565-018-0338-1

Source: https://www.nature.com/articles/s41565-018-0338-1 (abstract only). The UNSWorks copy (CC BY-NC-ND 3.0 AU) failed in the same way as He2019, so **the full text was not obtained.**

| Spec | Value | Verbatim quote | Location |
|---|---|---|---|
| Interlayer alignment | <5 nm | "demonstrate single-shot spin read-out with 97.9% measurement fidelity of a phosphorus dopant qubit within a vertically gated single-electron transistor with <5 nm interlayer alignment accuracy" | Abstract |
| Read-out fidelity | 97.9% | (same sentence) | Abstract |
| Architecture | vertically separated dopant planes | "This vertical three-dimensional device architecture requires the ability to pattern dopants in multiple, vertically separated planes of the silicon crystal with nanometre precision interlayer alignment." | Abstract |
| Materials | P and Si only | "Our strategy ensures the formation of a fully crystalline transistor using just two atomic species: phosphorus and silicon." | Abstract |
| Registration markers | etched trenches (no dimensions public) | "Fig. 2: Etched trench registration markers." | Landing page figure titles |
| Regrowth | kinetic growth manipulation | "Fig. 3: Use of kinetic growth manipulation to optimize the regrowth surface for second-layer lithography." | Landing page figure titles |
| Vertical layer separation, layer depths, SET/gate dimensions, marker depth/size | **not accessible** | — | — |

Secondary (Schofield2025, CC BY 4.0, p. 24, §3.1): "this ultra-high vacuum technique allows for three-dimensional manufacturing [KOC2019], in which multiple device layers can be stacked and aligned on top of each other with nanometre precision, all within the same silicon crystal." This gives no numeric layer separation.

---

## 6. Oberbeck2002: "Encapsulation of phosphorus dopants in silicon for the fabrication of a quantum computer", APL 81, 3197 (2002), doi:10.1063/1.1516859

Source: https://arxiv.org/abs/cond-mat/0208355 (PDF https://arxiv.org/pdf/cond-mat/0208355). Licence: arXiv assumed-1991-2003 (non-exclusive). **Not CC BY.**

| Spec | Value | Verbatim quote | Location |
|---|---|---|---|
| Segregation | ~5 nm | "We observe minimal dopant segregation (~5 nm), complete electrical activation at a silicon growth temperature of 250 °C" | Abstract, p. 1 |
| Spreading after overgrowth | <5 nm | "SIMS analysis displays minimal spreading of the donors after low temperature overgrowth (<5 nm)" | p. 1, col. 2 |
| Growth temperature | 250 °C | "deposited at a substrate temperature of 250 °C" | p. 2, col. 1 |
| Encapsulation thickness | 24 nm | "overgrown by a 24 nm thick epitaxial i-Si film (ρ > 1 kΩcm)" | p. 1–2 |
| **Growth rate** | **not found**: the paper gives no growth rate | — | — |
| Surface prep | ~1150 °C, 30 s | "flashing samples of resistance ~1 Ωcm for 30 s at a temperature of ~1150 °C" | p. 1, col. 2 |
| Incorporation anneal | 5 min at 550 °C | "anneal the sample for 5 min at 550 °C, which not only incorporates P atoms into the surface with a density of 0.25 monolayers (ML) (corresponding to a concentration of 1.7 × 1014 cm-2) but also desorbs the hydrogen" | p. 1, col. 2 |
| δ-layer density (SIMS) | 1.4 ± 0.3 × 10¹⁴ cm⁻² | "found to be 1.4 ± 0.3 × 1014 cm-2, in close agreement with the concentration expected for 0.25 ML of P atoms of 1.7 × 1014 cm-2" | p. 2, col. 1 |
| SIMS FWHM | 5, 6, 14 nm | "a full width at half maximum of the 31P peak of 5, 6, and 14 nm for Cs+ primary ion energies of 2, 5.5, and 15 keV, respectively" | p. 2, col. 1 |
| Activation (Hall) | 2.0 ± 0.4 × 10¹⁴ cm⁻²; complete | "the two-dimensional (2D) electron concentration to be 2.0 ± 0.4 × 1014 cm-2 ... we conclude that the P atoms are completely electrically activated" | p. 2, col. 2 |
| Mobility at 4.2 K | ~102 cm²/Vs | "a high two-dimensional electron mobility of ~102 cm2/Vs at a temperature of 4.2 K" | Abstract, p. 1 |
| Heterodimer height | ~0.04 nm (after ~530 °C) | "After annealing at ~ 530 °C the P atoms are incorporated into the Si surface to form Si-P heterodimers with a reduced height of ~0.04 nm above the surface" | p. 2, col. 1 |
| RT encapsulation test | 1 ML Si, re-anneal 600/340 °C | "encapsulated by 1 ML of Si at room temperature and re-annealed at (a) 600 °C or (b) 340 °C" | Fig. 4 caption, p. 3 |

---

## 7. Ruess2004: "Toward atomic-scale device fabrication in silicon using scanning probe microscopy", Nano Lett. 4, 1969 (2004), doi:10.1021/nl048808v

**Not accessible.** ACS is closed. The UCL Discovery repository copy (https://discovery.ucl.ac.uk/id/eprint/170062/) returned 403 (Cloudflare challenge). There is no arXiv or PMC copy. Marker geometry (etched registration mark depth and size), alignment accuracy and contact process were **not obtained**.

Secondary pointer only: the Schofield2025 roadmap reference list cites a later paper by the same group, "Rueß F J, Oberbeck L, Goh K E J, Butcher M J, Gauja E, Hamilton A R and Simmons M Y 2005 The use of etched registration markers to make four-terminal electrical contacts to STM-patterned nanostructures Nanotechnology 16 2446" (ref. [10], p. 80). That Nanotechnology 2005 paper may be an easier source for marker dimensions. The roadmap body (§2.3, p. 16) says only: "The complete process is complex and typically includes pre-patterned fiducial marks for device re-location, Si surface reconstruction, H passivation, STM patterning, dopant precursor exposure and incorporation, and silicon overgrowth, followed by ex-situ steps to locate the buried devices". It gives no dimensions.

---

## Gaps to close manually (institutional access needed)

- Fuechsle2012 full text: source–drain gap, gate separations, lead widths, δ-layer density, encapsulation thickness, charging energy value.
- He2019 full text: 2P/1P cluster sizes, the 13.0 ± 0.5 nm separation, SET distance, exchange values, B, T. UNSWorks advertises a CC BY-NC-ND published PDF; it may download from a normal browser.
- Koch2019 full text: vertical layer separation and marker dimensions. A UNSWorks CC BY-NC-ND PDF is advertised.
- Ruess2004 and OBrien2002 full texts.
- Kane1998 original: to settle the 10 nm vs 20 nm donor-spacing question and get the barrier and gate dimensions.
