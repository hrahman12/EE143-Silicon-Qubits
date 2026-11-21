# Fabrication and geometry specs: Stock 2020 (ACS Nano) and Stock 2024 (Adv. Mater.)

Sources (all read directly from the files):

- **S20**: Stock *et al.*, ACS Nano 14, 3316 (2020), doi 10.1021/acsnano.9b08943. Main text: `figures/raw/Stock2020/PMC7146850.1.txt` / `.xml`. SI: `nn9b08943_si_001.pdf`, fetched from the PMC OA bucket (it was not in the folder; the copy is in the session scratchpad, not the repo).
- **S24**: Stock *et al.*, Adv. Mater. 36, 2312282 (2024), doi 10.1002/adma.202312282. Main text: `figures/raw/Stock2024/PMC11475292.1.txt` / `.xml`. SI: `ADMA-36-2312282-s001.pdf`, fetched the same way.

Conventions:

- **Verbatim quote** is copied from the PMC plain text. In that text, superscripts are flattened, so `5 × 10−9 mbar` means 5 × 10⁻⁹ mbar, `cm2` means cm², and `0.716` means 0.7¹⁶. The **Value** column gives the same number in clean notation.
- **Location** names the section heading, figure caption, Methods subsection, Table, or SI item.
- A **[GRAPHIC]** location means the value is a label printed inside the figure image, not in the text. I read it from the high-resolution PDF image in `pdfimg/`. Use it for redrawing, but it is not prose.
- A **DERIVED** entry is arithmetic on the papers' own numbers. It is not stated in either paper.
- **Key** is a stable ID for cross-referencing from slides.

---

## 1. Sample / substrate

| Spec | Value | Verbatim quote | Location | Key |
|---|---|---|---|---|
| S20 wafer: dicing, thickness, growth, dopant, resistivity | 2 × 9 mm pieces, 0.3 mm thick, Czochralski (CZ), P-doped, 1–10 Ω·cm | "Si(001) samples were diced to 2 × 9 mm from a 0.3 mm thick, Czochralski grown, bulk phosphorus doped wafer with a resistivity of 1–10 Ω·cm." | S20 Experimental Methods › Sample Preparation and Scanning Tunneling Microscopy | S20-SUB-01 |
| S20 substrate donor concentration | N_D = 5×10¹⁴ to 5×10¹⁵ cm⁻³ | "We note that phosphorus doped, n-type substrates (donor concentration ND = 5 × 1014 to 5 × 1015 cm–3) are used in this work. This doping level allows for direct current sample heating and room temperature STM measurements, and does not interfere with the low temperature transport measurements of the delta layers." | S20 Results › Electrical Activation and Contacting of Arsenic δ-Layers | S20-SUB-02 |
| S20 orientation | Si(001) | (see S20-SUB-01) | S20 Methods | S20-SUB-03 |
| S20 ex situ clean | ultrasonic acetone, then IPA | "Samples were cleaned ultrasonically ex situ in acetone followed by isopropyl alcohol," | S20 Methods › Sample Preparation | S20-SUB-04 |
| S20 outgas | >8 h at 600 °C, base pressure <1×10⁻¹⁰ mbar | "then thermally outgassed in situ (base pressure <1 × 10−10 mbar) for >8 h at 600 °C," | S20 Methods › Sample Preparation | S20-SUB-05 |
| S20 flash anneal | 1200 °C, "multiple times", DC resistive heating. Duration: not stated | "and finally flash annealed multiple times at 1200 °C, using direct current resistive sample heating." | S20 Methods › Sample Preparation | S20-SUB-06 |
| S20 cooling after flash | not stated | n/a | n/a | S20-SUB-07 |
| S20 pyrometer, uncertainty | IMPAC IGA50-LO plus, ±30 °C | "Sample temperature was monitored using an infrared pyrometer (IMPAC IGA50-LO plus), with a total estimated measurement uncertainty of ±30 °C." | S20 Methods › Sample Preparation | S20-SUB-08 |
| S20 STM base pressure | <5×10⁻¹¹ mbar, room temperature, Omicron VT | "All scanning tunneling microscopy measurements were performed in an Omicron variable temperature series STM at room temperature with a base pressure of <5 × 10−11mbar." | S20 Methods › Sample Preparation | S20-SUB-09 |
| S24 wafer | n-type, As-doped, nominal 15 Ω·cm, Si(001). Thickness, dicing size, growth method: not stated | "Si(001) substrates were n‐type, arsenic doped, with a nominal resistivity of 15 Ohm cm." | S24 4 Experimental Section › Experimental Methods | S24-SUB-01 |
| S24 fiducial markers | 300 nm deep, dry etched | "Prior to UHV processing, substrates were patterned with 300 nm deep, dry etched, fiducial markers, allowing for alignment to the HRL patterns in subsequent process steps." | S24 Experimental Methods | S24-SUB-02 |
| S24 outgas and flash | 600 °C × 8 h outgas, multiple ≈1200 °C flashes, DC heating, prep-chamber base pressure 2×10⁻¹⁰ mbar. Flash duration: not stated | "Clean silicon surfaces were prepared using a standard direct current heating recipe with a 600 °C × 8‐h outgas, followed by multiple ≈1200 °C flash anneals, in a preparation chamber with a base pressure of 2 × 10−10 mbar." | S24 Experimental Methods | S24-SUB-03 |
| S24 ex situ clean | not stated | n/a | n/a | S24-SUB-04 |
| S24 cooling after flash | not stated | n/a | n/a | S24-SUB-05 |
| S24 STM, tip, base pressure | ScientaOmicron VT-STM, room temperature, 3×10⁻¹¹ mbar | "All STM imaging was performed using a ScientaOmicron VT‐STM operated at room temperature and a base pressure of 3 × 10−11 mbar." | S24 Experimental Methods | S24-SUB-06 |
| S24 pyrometer, uncertainty | Impact IR IGA 50-LO, ±20 °C | "Sample temperatures were monitored using an Impact IR IGA 50‐LO optical pyrometer, with an estimated measurement uncertainty of ±20 °C." | S24 Experimental Methods | S24-SUB-07 |
| S24 pressure gauges | Bayard–Alpert gauges and SRS RGA100 | "Total and partial pressures were measured using Bayard–Alpert ionization gauges and an SRS RGA100 quadrupole mass spectrometer." | S24 Experimental Methods | S24-SUB-08 |

## 2. Hydrogen termination

| Spec | Value | Verbatim quote | Location | Key |
|---|---|---|---|---|
| S20 H-termination recipe | **not stated** in the main text or SI. Only the result is described: DB density <1% | "Each silicon atom has one or two hydrogen atoms bonded to it, except in a few cases where the hydrogen atom is missing, leaving a dangling bond (DB). The DBs have the appearance of bright dots in the image and the DB density is <1%." | S20 Results › Adsorption and Incorporation of Arsenic through a Hydrogen Resist | S20-H-01 |
| S24 atomic H source | Tektra H-flux, thermal cracking of H₂ | "Surfaces were hydrogen terminated by exposure to an atomic hydrogen beam, generated by thermally cracking of H2 gas in a Tektra H‐flux Atomic Hydrogen Source," | S24 Experimental Methods | S24-H-01 |
| S24 H₂ pressure, substrate temperature | 5×10⁻⁷ mbar H₂, 320 °C (DC heating). Dose and exposure time: **not stated** | "using an H2 partial pressure of 5 × 10−7 mbar, and a substrate temperature of 320 °C maintained by direct current heating." | S24 Experimental Methods | S24-H-02 |
| S24 resulting DB density | ≈0.008 nm⁻² | "1DB densities of half this maximum permissible value are routinely achieved using standard hydrogen termination parameters, as demonstrated in Figure 2a, which shows a hydrogen‐terminated surface with a DB density of ≈0.008 nm−2." | S24 §2.2 | S24-H-03 |

## 3. STM lithography and pattern geometry

### 3a. Stock 2020

| Spec | Value | Verbatim quote | Location | Key |
|---|---|---|---|---|
| Tip material | not stated | n/a | n/a | S20-LITH-01 |
| Bias, current, speed, area | +7.0 V, 1.0 nA, 100 nm/s, 50 × 50 nm square | "Selective removal of a region of the hydrogen “resist” layer is achieved by scanning over a 50 × 50 nm region of the surface using an increased bias/current of +7.0 V and 1.0 nA, at a tip raster speed of 100 nm/s (Figure 3b)." | S20 Results › Adsorption and Incorporation through a Hydrogen Resist | S20-LITH-02 |
| Same, caption version | 50 × 50 nm, +7.0 V, 1 nA, 100 nm/s | "(b) Selected area hydrogen desorption of a 50 × 50 nm square (V = +7.0 V, I = 1 nA, s = 100 nm/s)." | S20 Figure 3 caption | S20-LITH-03 |
| Field of view, Fig. 3a–f | 100 × 100 nm | "(a–f) Sequential STM images of the same 100 × 100 nm area on a Si(001)-H surface" | S20 Figure 3 caption | S20-LITH-04 |
| Desorbed-area DB coverage | approaches 100% | "The patterned region, in the center of the image, shows the density of bright dots now approaches 100% coverage of the surface," | S20 Results | S20-LITH-05 |
| Narrow line | 2 dimer rows wide | "(g) Sequential images of hydrogen desorption, AsH3 adsorption, and As incorporation along a line that is only 2 Si dimer rows wide." | S20 Figure 3 caption | S20-LITH-06 |
| Narrow line result | "at most a few atoms wide" | "The resulting patterned line of incorporated arsenic atoms is at most a few atoms wide." | S20 Results | S20-LITH-07 |
| Line dose | not stated | n/a | n/a | S20-LITH-08 |
| [GRAPHIC] Scale bars, Fig. 3 | a–d: 20 nm. e, f: 5 nm. g: 2 nm | printed labels "20 nm", "5 nm", "2 nm" | S20 Fig. 3 image | S20-LITH-09 |
| [GRAPHIC] Scale bars, Figs. 1 and 2 | Fig. 1a,b: 5 nm. Fig. 2a,b: 5 nm. Fig. 2d,e: 20 nm (insets 5 nm) | printed labels | S20 Fig. 1, Fig. 2 images | S20-LITH-10 |

### 3b. Stock 2024

| Spec | Value | Verbatim quote | Location | Key |
|---|---|---|---|---|
| Tip | Pt-Ir (90:10), mechanically cut | "STM tips were prepared by mechanical cutting of Pt‐Ir (90:10) wire." | S24 Experimental Methods | S24-LITH-01 |
| Lithography, Methods version | +4 V, 3.5 nA, 50 nm/s | "All STM lithography was performed at a tip‐sample bias of +4 V, a tunnel current setpoint of 3.5 nA, and a write speed of 50 nm s−1." | S24 Experimental Methods | S24-LITH-02 |
| Lithography, caption version (**conflicts with Methods**) | 3.5 V, 3000 pA (3.0 nA), 50 nm/s | "Lithography parameters: 3.5 V, 3000 pA, 50 nm s−1." | S24 Figure 1 caption and Figure 3 caption (identical) | S24-LITH-03 |
| Feedback control | none for the 10 × 10 array | "these 100 lithographic sites were patterned without feedback control so as to rapidly produce adsorption windows of various sizes, nDB where n ranges from 2 to 10, and various shapes, spanning one to three silicon dimer rows." | S24 §2.3 | S24-LITH-04 |
| Line dose | not stated | n/a | n/a | S24-LITH-05 |
| Array pitch | ≈12 surface lattice vectors = 4.6 nm (2×2, 7×1, 4×4) | "a 2 × 2 array (Figure 1a,c); a 7 × 1 chain (Figure 1d,e); and a 4 × 4 array (Figure 1f–i), each with a pitch of ≈12 Si(001) surface lattice vectors, or 4.6 nm." | S24 §2.1 | S24-LITH-06 |
| Array pitch, alternative statement | "5 nm array pitch". Active area 625 nm² including a 5 nm border | "Taking the 4 × 4 array of Figure 1g as an example, complete avoidance of spurious arsenic incorporation within the active device area of 625 nm2 (5 nm array pitch plus 5 nm border) would permit a maximum density of spurious arsenic incorporation of 0.0016 nm−2." | S24 §2.2 | S24-LITH-07 |
| DERIVED: active-area side | 625 nm² = 25 nm × 25 nm = 3 × 5 nm pitch + 2 × 5 nm border | arithmetic | n/a | S24-LITH-08 |
| DERIVED: implied lattice vector | 4.6 nm / 12 = 0.383 nm, consistent with the [GRAPHIC] a = 3.84 Å (S24-GEO-01). 12 × 3.84 Å = 4.61 nm | arithmetic | n/a | S24-LITH-09 |
| SI 4×4 arrays | ten 4×4 arrays, each ~20 × 20 nm, ~5 nm pitch, on one terrace | "The 30 STM images above show ten 4×4 arrays patterned on a single atomic terrace of H:Si(001) shown in Figure S3. Each array is ~20×20 nm with a ~5 nm pitch." | S24 SI Figure S4 caption | S24-LITH-10 |
| 2×2 windows | nDB with 2 < n < 8. Lower-left window spans 2 dimer rows; the other three are on 1 row | "Figure 1a shows hydrogen desorption to create a 2 × 2 array of adsorption windows, each consisting of n DBs (2 < n < 8) and therefore labeled nDB. It is notable that the lower‐left corner window extends across two dimer rows, while the other three sites are all on a single dimer row." | S24 §2.1 | S24-LITH-11 |
| 7×1 chain windows | nDB, 2DB, 4DB, 6DB, plus 3 spurious 1DB | "The seven patterned adsorption windows shown in Figure 1d are labeled nDB, 2DB, 4DB, or 6DB, while three spurious single‐dangling bond sites are labeled 1DB." | S24 §2.1 | S24-LITH-12 |
| [GRAPHIC] 7×1 chain labels, left to right | nDB, 4DB, 2DB, 6DB, nDB, nDB, 4DB. After dosing the features are B, E, A, D, E+A, B, C | printed labels in Fig. 1d,e | S24 Fig. 1d,e image | S24-LITH-13 |
| 4×4 window footprint | 6 windows on 1 row, 6 on 2 rows, 3 on 3 rows, a4 = contaminant | "Of these 16 nDB windows, six are contained within single silicon dimer rows (b2, b3, c3, c4, d2, d3), six extend across two dimer rows (a1, a2, b1, c1, c2, d1), and three across three rows (a3, b4, d4). The final remaining element (a4) is of considerably greater height than all the other lithographic array elements because it is a pre‐existing point contaminant." | S24 §2.1 | S24-LITH-14 |
| 10×10 array window census | n = 2–10. 6 × 2DB, 14 × 4DB, 8 × 6DB, all on single rows | "Within this distribution, there are 6 2DB, 14 4DB, and 8 6DB sites, all of which are confined to single‐dimer rows." | S24 §2.3 | S24-LITH-15 |
| Window geometry nomenclature | 2DB = 1 dimer, 4DB = 2 dimers (2 × 2), 6DB = 3 contiguous dimers | "At the locations of high symmetry 6DB adsorption windows (three contiguous 2DB sites as in Figure 3d)" | S24 §2.3 | S24-LITH-16 |
| [GRAPHIC] Window panel titles | "1-dimer - 2DB", "2-dimer - 4DB", "3-dimer - 6DB" | printed titles of Fig. 3b,c,d | S24 Fig. 3 image | S24-LITH-17 |
| Ideal 4DB window | exactly 4 H removed, "2 × 2, double‐dimer formation" | "a well‐controlled STM lithography procedure capable of reliable removal of exactly four hydrogen atoms in a 2 × 2, double‐dimer formation, as can be achieved through feedback‐controlled lithography." | S24 3 Conclusion | S24-LITH-18 |
| Spatial precision | 1-in-4 lattice sites, up to 1-in-8 | "controlled positioning of single arsenic atoms into the Si(001) surface lattice with a nominal spatial precision of 1‐in‐4 (up to a possible 1‐in‐8) lattice sites" | S24 3 Conclusion | S24-LITH-19 |
| Incorporation-site spread | up to ±1 lattice spacing along the dimer row | "the resulting incorporation window is assumed to extend at most by one lattice spacing in either direction beyond the original adsorption window." | S24 §2.3 | S24-LITH-20 |
| Window-size precision (intro) | <1 nm | "producing a chemically‐sensitive mask to spatially confine the adsorption and reaction of gas‐phase dopant precursor molecules to nearly exact surface lattice sites (<1 nm precision)." | S24 1 Introduction | S24-LITH-21 |
| P comparison window | 6 sites minimum for PH₃ | "The placement of a single phosphorus atom from a phosphine molecule using HRL fabrication requires the removal of a minimum of six hydrogen atoms from the hydrogen‐terminated Si(001) surface, exposing three adjacent pairs of silicon lattice sites." | S24 1 Introduction | S24-LITH-22 |
| **Fig. 1f gated device: electrodes** | 4 large rectangular, saturation-doped regions: source, drain, 2 gates. **Electrode widths, lengths, gaps, and distances to the array: not stated in text or SI** | "Also visible in this larger area image are four regions where we have incorporated many arsenic atoms into much larger rectangular adsorption windows near the 4 × 4 array. These extended and metallically doped regions would form the source, drain, and gate electrodes, as indicated, for inclusion of the 4 × 4 array in a field‐effect device architecture." | S24 §2.1 (last paragraph) | S24-DEV-01 |
| Fig. 1f inset | 15 × 15 nm inset at the gate edge. Ejected ad-Si dimer rows indicate saturation doping. The text says "top edge of the bottom gate"; the caption says "bottom gate edge" | "as seen in the 15 × 15 nm inset image showing detail of the top edge of the bottom gate electrode." and "The 15 nm inset of panel (f) shows detail of the bottom gate edge; ejected ad‐Si dimer rows, perpendicular to dimer rows on the substrate, indicate saturation doping of the large area electrodes." | S24 §2.1; Figure 1 caption | S24-DEV-02 |
| [GRAPHIC] Fig. 1f scale bar and layout | Scale bar **25 nm**. Electrodes are parallel diagonal strips: "gate" upper-left, "drain" upper-right, "source" lower-left, "gate" lower-right, with the 4×4 array (dashed green square) in the center gap. Use the 25 nm bar to measure any dimension | printed "25 nm" and labels "gate", "drain", "source", "gate" | S24 Fig. 1f image (`pdfimg/p3_x27_2050x1929.jpeg`) | S24-DEV-03 |
| [GRAPHIC] Fig. 1i lattice key | unit cell a × 2a, "Si(001) lattice a = 3.84 Å" | printed "Si(001) lattice a = 3.84 Å" with arrows "a" (vertical) and "2a" (horizontal) | S24 Fig. 1i legend | S24-DEV-04 |
| P-based analog | 3 × 3 array of clusters (ref. 24) | "Similar device structures have been fabricated using phosphorus in silicon (for a 3 × 3 array of dopant clusters)" | S24 §2.1 | S24-DEV-05 |

## 4. Dosing (AsH₃; PH₃ only mentioned)

| Spec | Value | Verbatim quote | Location | Key |
|---|---|---|---|---|
| S20 low-coverage dose | 0.015 L at 5×10⁻¹¹ mbar, room temperature | "we exposed atomically clean Si(001)2 × 1 to a low dose of arsine (0.015 L at 5 × 10−11 mbar) at room temperature." | S20 Results › Dissociation of Isolated AsH3 Molecules | S20-DOSE-01 |
| S20 low-coverage density | 0.02 adsorbates/nm² | "(a) STM image of low coverage (0.02 adsorbates/nm2), room temperature AsH3 on Si(001)." | S20 Figure 2 caption | S20-DOSE-02 |
| S20 saturation dose | 1.5 L = 5×10⁻⁹ mbar × 5 min, room temperature | "(d) STM image of a Si(001) surface following a 1.5 L (5 × 10–9 mbar × 5 min) room temperature, arsine exposure." | S20 Figure 2 caption | S20-DOSE-03 |
| S20 rate-independence test | 5×10⁻⁹ mbar for 5 min vs 5×10⁻¹⁰ mbar for 50 min gives the same coverage | "When the arsine dose rate is varied by decreasing the arsine partial pressure from 5 × 10–9 mbar to 5 × 10–10 mbar (along with a dose equalizing change in total exposure time from 5 to 50 min), the resulting total arsenic coverage is found to be constant within measurement error." | S20 Results › Saturation Arsine Coverage | S20-DOSE-04 |
| S20 saturation coverage | 0.24 ± 0.04 ML | "Arsine adsorption on Si(001), at room temperature, is self-terminating at a saturation coverage of 0.24 ± 0.04 molecules/surface silicon atom, independent of gas exposure rate" | S20 Introduction | S20-DOSE-05 |
| S20 saturation coverage (incorporated) | 0.24 ± 0.04 ML after 1.5 L + 350 °C | "we estimate the incorporated arsenic coverage in samples prepared by a saturation arsine dose of 1.5 L and thermal anneal of 350 °C to be 0.24 ± 0.04 ML." | S20 Results › Saturation Arsine Coverage | S20-DOSE-06 |
| S20 KMC coverage range | 0.24–0.26 ML | "the total number of arsenic atoms present on the surface remains in the 0.24–0.26 ML range, and the arsenic surface concentration only increases by 2–3% as the dose rate is increased across the full range." | S20 Results › Saturation Arsine Coverage | S20-DOSE-07 |
| [GRAPHIC] S20 KMC axis | 10⁻¹¹ to 10⁻⁶ mbar, "(10 L exposure)" | printed axis "AsH3 Partial Pressure (mbar) (10 L exposure)" | S20 Fig. 2c image | S20-DOSE-08 |
| S20 low-coverage dissociation | ≲2×10¹² molecule/cm², ~10 s | "(i) At low coverages (≲ 2 × 1012 molecule/cm2), AsH3 moieties dissociate rapidly (∼10 s) and completely at random locations." | S20 Results › Saturation Arsine Coverage | S20-DOSE-09 |
| S20 dose through resist | 1.5 L gives 0.24 ML inside the window | "Dosing the patterned surface of Figure 3b with 1.5 L of arsine results in AsHx moieties (where x = 0–3) selectively adsorbing within the patterned area, producing a saturation arsenic density of 0.24 ML." | S20 Results › through a Hydrogen Resist | S20-DOSE-10 |
| S20 literature context | Kipp: ~20% ML. Others: ~0.25–1 ML, >600 °C growth | "saturates at an As concentration of ∼20% of a silicon monolayer (ML)" / "self-limiting at an arsenic coverage of ∼0.25–1 ML, dependent on the growth temperature" | S20 Introduction | S20-DOSE-11 |
| S24 dose | 5×10⁻⁹ mbar × 10 min, room temperature | "AsH3 dosing: 5 × 10−9 mbar × 10 min." | S24 Figure 1, 2, 3 captions | S24-DOSE-01 |
| S24 dose in Langmuir | 3 L | "Figure 1b shows the same surface after arsine gas exposure (3 Langmuir)" | S24 §2.1 | S24-DOSE-02 |
| S24 SI doses | 3 L | "b) following a 3 L AsH3 exposure" / "b) AsH3 dosing (3 L)" | S24 SI Fig. S2 and S3 captions | S24-DOSE-03 |
| PH₃ dosing parameters | not stated in either paper (PH₃ is discussed only as a comparison; S24 mentions plugging 2DBs with PH₃ as a proposal, with no parameters) | "Prior to arsine dosing, this surface can first be exposed to phosphine, effectively plugging all 2DB sites with PH2 adsorbates that will eventually desorb during the incorporation anneal." | S24 §2.2 | S24-DOSE-04 |

## 5. Incorporation anneal

| Spec | Value | Verbatim quote | Location | Key |
|---|---|---|---|---|
| S20 low-coverage anneal | 500 °C × 1 min | "Figure 2b shows the same surface (but a different area) after a 1 min thermal anneal at 500 °C." | S20 Results › Substitutional Incorporation | S20-INC-01 |
| S20 saturation anneal, text | 350 °C × 5 min | "The result of annealing the arsine saturated surface to 350 °C for 5 min is shown in the STM images in Figure 2e." | S20 Results › Saturation Arsine Coverage | S20-INC-02 |
| S20 saturation anneal, caption (**conflicts: 1 min vs 5 min**) | 350 °C × 1 min | "(e) Surface from panel (a) subsequent to a 350 °C × 1 min anneal. Inset shows ejected silicon dimer chains indicative of arsenic incorporation." | S20 Figure 2 caption | S20-INC-03 |
| S20 resist-pattern anneal, text | 350 °C × 2 min | "In the final step, shown in Figure 3d, annealing the surface to 350 °C for 2 min results in substitutional incorporation of arsenic" | S20 Results › through a Hydrogen Resist | S20-INC-04 |
| S20 resist-pattern anneal, caption (**conflicts: 1 min vs 2 min**) | 350 °C × 1 min | "(d) 350 °C × 1 min anneal, results in incorporation of the adsorbed arsenic atoms as evidenced by presence of ejected Si." | S20 Figure 3 caption | S20-INC-05 |
| S20 incorporation threshold | below 350 °C | "Arsenic atoms from dissociated AsH3 molecules incorporate substitutionally into the silicon lattice at temperatures below 350 °C, and at all surface coverages." | S20 Introduction | S20-INC-06 |
| S20 H₂ desorption onset | 380 °C | "arsenic should also incorporate into the silicon lattice at anneal temperatures below the onset of H2 desorption (380 °C)." | S20 Results › through a Hydrogen Resist | S20-INC-07 |
| S20 ejected Si | 1 Si per As, forming ad-dimer chains perpendicular to the rows | "These bright linear protrusions correspond to short ad-dimer chains, formed from the silicon atoms ejected during arsenic incorporation." / "Because there is one ejected silicon atom for every incorporated arsenic atom," | S20 Results › Saturation Arsine Coverage | S20-INC-08 |
| S20 ejected Si orientation | perpendicular to the underlying dimer rows | "evidenced in Figure 2e by the bright linear protrusions running perpendicular to the underlying dimer rows" | S20 Results › Saturation Arsine Coverage | S20-INC-09 |
| S20 ejected Si at 500 °C | diffuses to step edges and ad-dimer rows. All H desorbed | "At the temperature of 500 °C used in the annealing experiment above, all hydrogen atoms are expected to desorb from the silicon surface, … the substituted silicon atoms, which are ejected from the surface as the As–Si dimers are formed, rapidly diffuse away from the ejection site and are eventually captured at the existing step edges, or newly formed ad-dimer rows." | S20 Results › Substitutional Incorporation | S20-INC-10 |
| S20 resist after anneal | small density of new DBs | "The surrounding hydrogen resist remains essentially intact with only a small density of additional dangling bonds produced by the incorporation anneal." | S20 Figure 3 caption | S20-INC-11 |
| Ramp rate | not stated in either paper | n/a | n/a | INC-RAMP |
| S24 anneal (Figs. 1, 3) | 350 °C × 1 min | "Incorporation anneal: 350 °C × 1 min." | S24 Figure 1 and Figure 3 captions | S24-INC-01 |
| S24 anneal (Fig. 2) | 350 °C × 2 min | "Incorporation anneal: 350 °C × 2 min." | S24 Figure 2 caption | S24-INC-02 |
| S24 text versions | "1 min at 350 °C", "≈350 °C" | "After the thermal incorporation anneal (1 min at 350 °C)," / "Figure 2c shows the same surface after a ≈350 °C incorporation anneal." | S24 §2.1, §2.2 | S24-INC-03 |
| S24 SI anneal | "above 350 °C"; "~350 °C" | "When annealed above 350 °C, the five AsHx adsorbates can produce a variety of reaction products." / "c) thermal annealing (~350 °C) for dopant incorporation" | S24 SI Fig. S1, S3 captions | S24-INC-04 |
| S24 thermal DB generation | anneal of the H-terminated surface above 325 °C (SI: ~375 °C) | "We have prepared a large statistical distribution of 1DB and 2DB windows via thermal desorption by annealing hydrogen‐terminated surfaces above 325 °C." / SI: "following a ~375 °C anneal" | S24 §2.2; SI Fig. S2 caption | S24-INC-05 |
| S24 mechanism window | 350–380 °C. H in the resist becomes mobile | "We suggest that a 350–380 °C anneal is insufficient to excite recombinative desorption of arsine but is sufficient to produce additional dangling bond sites immediately at the location of an AsH x adsorbate. At this temperature the hydrogen resist atoms become mobile," | S24 §2.3 | S24-INC-06 |
| S24 PH₂ comparison | PH₂ desorbs as PH₃ at ≈360 °C | "It is known that when a PH2 fragment, adsorbed at a 2DB site, is annealed to ≈360 °C, it will recombine with hydrogen and desorb as PH3." | S24 §2.3 | S24-INC-07 |
| S24 products | As–Si heterodimer on one half of a dimer, plus ad-Si (e-Si end-bridge or b-Si dimer-bridge) | "This produces arsenic‐silicon heterodimers (As‐Si) in the surface and ejected silicon ad‐atoms on the surface (ad‐Si). The four small protrusions that each occur on one‐half of individual silicon dimers in Figure 1c are readily identified as As‐Si features" | S24 §2.1; SI Fig. S1 caption | S24-INC-08 |

## 6. Encapsulation (S20 only; S24 has no overgrowth step)

| Spec | Value | Verbatim quote | Location | Key |
|---|---|---|---|---|
| Si source | SUSI-40 solid sublimation source | "This protective capping layer is grown via molecular beam epitaxy, using a solid intrinsic silicon sublimation source (SUSI-40, MBE Komponenten GmbH)." | S20 Results › Encapsulation | S20-ENC-01 |
| Rate (Methods) | 1.5 Å/min, base pressure 1×10⁻¹⁰ mbar | "Silicon epitaxy was performed at a base pressure of 1 × 10−10 mbar, using an all silicon, solid sublimation source (SUSI-40, MBE Komponenten GmbH) operated at a deposition rate of 1.5 Å/min." | S20 Methods › Sample Preparation | S20-ENC-02 |
| Rate and thickness (Results) | 15 nm at 1 ML/min | "a number of saturation arsenic delta layers were overgrown with 15 nm of silicon at a rate of 1 ML/min, using different sample temperature programs." | S20 Results › Encapsulation | S20-ENC-03 |
| Temperature measurement during growth | inferred from sample resistance (DC heating) | "During silicon overgrowth, sample temperature was indirectly monitoring by measuring sample resistance, while the sample was heated using direct current resistive sample heating." | S20 Methods | S20-ENC-04 |
| P reference | constant 250 °C works for P but not for As | "In the case of phosphorus, these two requirements can be reasonably satisfied by holding the sample temperature constant at 250 °C, throughout. In the case of arsenic we find (via secondary ion mass spectrometry; SIMS) that this approach is inadequate." | S20 Results › Encapsulation | S20-ENC-05 |
| Number of SIMS programs | Text says four; the caption shows five (a–e) | text: "Figure 4 shows SIMS data for four different temperature programs" / caption: "(a–e) SIMS profiles of five different saturation arsenic δ-layer samples overgrown with 15 nm Si, at a deposition rate of 1 ML/min." | S20 Results; Figure 4 caption | S20-ENC-06 |
| **Fig. 4a** | constant 240 °C. Surface peak at ~1 nm, plateau >1×10¹⁸ cm⁻³, small peak at 15 nm. Detection limit 1×10¹⁸ cm⁻³ | "Figure 4a shows the result of silicon overgrowth at a constant sample temperature of 240 °C. This arsenic distribution is dominated by a high and narrow peak located at a depth of ∼1 nm. Beneath this narrow surface peak the arsenic concentration reduces to a much lower, but not an insignificant constant level (>1 × 1018 atoms/cm-3) before terminating in a slight peak at the δ-layer origin depth, 15 nm below the surface. Beyond this depth, the arsenic concentration rapidly drops below the instrument’s detection limit (1 × 1018 atoms/cm3)." | S20 Results › Encapsulation | S20-ENC-07 |
| **Fig. 4b** | constant 190 °C. Asymmetric peak at ~15 nm | "Figure 4b shows the arsenic profile for overgrowth at a constant but lower temperature of 190 °C. … Below the surface peak, it slowly rises to an asymmetric peak at the arsenic origin depth of ∼15 nm, before rapidly falling off below the detection limit." | S20 Results › Encapsulation | S20-ENC-08 |
| **Fig. 4c** | no Joule heating: 40 °C rising to a stable 100 °C after 12 min (12 ML). <2 nm FWHM, ~5×10²⁰ cm⁻³ at 15 nm, falls below detection within 3 nm | "The substrate begins overgrowth at 40 °C increasing to a stable 100 °C after the first 12 min of growth (12 ML). From the SIMS profile, we see that arsenic surface segregation is highly suppressed in this sample, resulting in a very well confined (<2 nm fwhm) and symmetric peak (∼ 5 × 1020 atoms/cm-3) located at the origin depth of 15 nm. This peak, which falls rapidly to below the instrument’s detection limit within 3 nm in either direction," | S20 Results › Encapsulation | S20-ENC-09 |
| Fig. 4c amorphization | critical thickness <2 nm at 100 °C and 1 ML/min, so the upper ≥13 nm is amorphous | "At a temperature of 100 °C, and deposition rate of 1 ML/min, the critical thickness is expected to reduce below 2 nm, meaning the upper 13 nm or more of silicon will be amorphous, and unsuitable for device encapsulation." | S20 Results › Encapsulation | S20-ENC-10 |
| **Fig. 4d** (locking layer) | unheated for the first 10 min (10 ML), then rapid heat to 250 °C, held for the remaining 230 min | "Here the sample is not actively heated for the first 10 min (10 ML for a 1 ML/min growth rate) after which it is then rapidly heated to 250 °C, and held constant for the remaining 230 min of overgrowth." | S20 Results › Encapsulation | S20-ENC-11 |
| **Fig. 4e** (locking layer + RTA) | same as 4d plus a 500 °C × 10 s RTA between the locking layer and 250 °C growth | "It is similar to the profile shown in the inset of Figure 4d, with the exception of the additional 500 °C × 10 s RTA, occurring between the locking layer growth and constant temperature epitaxy stages." | S20 Results › Electrical Activation | S20-ENC-12 |
| RTA (Conclusions) | 500 °C × 10 s, immediately after the locking layer | "A rapid thermal anneal stage of 500 C × 10 s immediately following locking layer growth improves electronic transport properties resulting in 2 nm thick, conductive layers" | S20 Conclusions | S20-ENC-13 |
| RTA range explored | 250–560 °C, five samples. Optimum ~500 °C | "with heating profiles identical to that of Figure 4e, except with each using a different RTA peak value, covering the range from 250 to 560 °C. For a RTA greater than 500 °C, the electronic layer thickness increases beyond 2 nm, … the RTA temperature maximum is considered optimum at ∼500 °C." | S20 Results › Electrical Activation | S20-ENC-14 |
| Locking-layer thickness | 10 ML, "very thin", below the critical amorphization thickness | "growing a very thin, reduced temperature “locking layer” that is kept below the critical amorphization thickness." | S20 Results › Encapsulation | S20-ENC-15 |
| [GRAPHIC] Fig. 4a–d insets | a: 240 °C flat. b: 190 °C flat. c: "40 °C" then "100 °C". d: "40 °C" then "250 °C". Time axis 0, 10, (break), 160, 220 min. T axis 0–500 °C | printed inset labels | S20 Fig. 4 image (`pdfimg/p7_x699_1950x1373.png`) | S20-ENC-16 |
| [GRAPHIC] Fig. 4e inset | "40 °C LL" (locking layer, slow rise over 0–10 min), ramp to the "500 °C RTA" spike at ~13–14 min, then "250 °C LTE" to the end (~240 min). Axis "Si epitaxy growth time (min)" | printed inset labels | S20 Fig. 4e image | S20-ENC-17 |
| [GRAPHIC] Fig. 4e SIMS peak | peak ~9×10²⁰ atoms/cc at ~17 nm depth (approximate visual reading) | axis reading | S20 Fig. 4e image | S20-ENC-18 |
| [GRAPHIC] Fig. 4c peak | peak reaches ~1×10²¹ atoms/cc on the plotted axis, but the text says ~5×10²⁰ (approximate visual reading) | axis reading | S20 Fig. 4c image | S20-ENC-19 |
| DERIVED: thickness consistency | Locking layer 10 ML ≈ 10 min × 1.5 Å/min = 1.5 nm. Total time 10 + 230 = 240 min gives 240 ML at "1 ML/min", or 36 nm at "1.5 Å/min". **That does not match "15 nm"** (15 nm at 1.5 Å/min = 100 min). The inset time axis also runs to ~240 min | arithmetic on S20-ENC-02/03/11 | n/a | S20-ENC-20 |
| Final δ-layer depth | 15 nm (nominal origin depth) | "located at the origin depth of 15 nm" | S20 Results | S20-ENC-21 |
| Width | <2 nm FWHM (Fig. 4c). ~2 nm thick electrically at 500 °C RTA | see S20-ENC-09, S20-ENC-13 | n/a | S20-ENC-22 |
| SIMS instrument | IONTOF ToF-SIMS5, 25 keV Bi⁺ (HCBM), 500 eV 35 nA Cs⁺ sputter, 300 μm² crater, central 50 μm² gated | "Time of flight (ToF) SIMS measurements were made using an IONTOF ToF-SIMS5 system with a 25 keV Bi+ primary ion beam in high current bunch mode (HCBM), and a 500 eV, 35 nA Cs+ sputter beam. Depth profiles were made with a 300 μm2 sputter crater, and the analytical region was gated to the central 50 μm2 of the sputter region" | S20 Methods › Secondary Ion Mass Spectrometry | S20-ENC-23 |

## 7. Electrical results (S20)

| Spec | Value | Verbatim quote | Location | Key |
|---|---|---|---|---|
| Plateau mobility and R_s | 28 ± 1 cm²/(V·s), 1.6 ± 0.1 kΩ/□ | "Despite the fact that both the mobility and sheet resistance values plateau at 28 ± 1 cm2/(V·s), and 1.6 ± 0.1 kΩ/square, respectively, the carrier density continues increasing beyond this optimum RTA temperature." | S20 Results › Electrical Activation | S20-EL-01 |
| Max carrier density | 1.45×10¹⁴ cm⁻² at 560 °C RTA, i.e. 0.21 ML, 88% activation | "At the highest RTA temperature maximum examined, 560 °C, we measure a carrier density of 1.45 × 1014 cm–2, which corresponds to an arsenic donor atom density of only 0.21 ML. Given our estimate of arsenic saturation coverage at 0.24 ML, this maximum value represents an activation of 88% of the donor atoms." | S20 Results › Electrical Activation | S20-EL-02 |
| Activation at 500 °C | 81% | "At the optimized RTA temperature of 500 °C, this activation percentage is even lower at 81%." | S20 Results | S20-EL-03 |
| P reference density | 2.4×10¹⁴ cm⁻² | "greater than 1/2 of the typical carrier density of 2.4 × 1014 cm–2 found in phosphorus δ-layers." | S20 Results | S20-EL-04 |
| Conclusions summary (**unit typo cm⁻³; R_s differs from 1.6**) | 1.5 kΩ/□, 1.3×10¹⁴ "cm–3", 2 nm thick | "resulting in 2 nm thick, conductive layers with sheet resistance, and carrier concentration of 1.5 kΩ/square, and 1.3 × 1014 cm–3, respectively." | S20 Conclusions | S20-EL-05 |
| Abstract summary | >80% activation, <2 kΩ/□ | "while still retaining >80% carrier activation and sheet resistances of <2 kΩ/square." | S20 Abstract | S20-EL-06 |
| **SI Table S1, sample (a)** | RTA 250 ± 15 °C: n = 1.15 ± 0.02 ×10¹⁴ cm⁻²; R₀ = 4.18 ± 0.02 kΩ/□; μ = 13.0 ± 0.2; L = 7.6 ± 0.2 nm; L_φ = 30.9 ± 0.1 nm; γ = 6.5 ± 0.4 ×10⁻⁴ T⁻²; T = 0.8 ± 0.1 nm | "(a) 250±15 1.15 ± 0.02 4.18 ± 0.02 13.0 ± 0.2 7.6 ± 0.2 30.9 ± 0.1 6.5 ± 0.4 0.8 ± 0.1" | S20 SI Table S1 | S20-EL-07 |
| SI Table S1, sample (b) | 384 ± 15 °C: 1.19 ± 0.07; 2.49 ± 0.04; 20.0 ± 1.3; 8.1 ± 0.7; 58.6 ± 0.6; 27.0 ± 3.5; 0.9 ± 0.1 nm | "(b) 384±15 1.19 ± 0.07 2.49 ± 0.04 20.0 ± 1.3 8.1 ± 0.7 58.6 ± 0.6 27.0 ± 3.5 0.9 ± 0.1" | S20 SI Table S1 | S20-EL-08 |
| SI Table S1, sample (c) | 438 ± 15 °C: 1.29 ± 0.02; 2.41 ± 0.02; 20.0 ± 0.3; no WL fit | "(c) 438±15 1.29 ± 0.02 2.41 ± 0.02 20.0 ± 0.3 − − − −" | S20 SI Table S1 | S20-EL-09 |
| SI Table S1, sample (d) | 498 ± 15 °C: 1.32 ± 0.01; 1.69 ± 0.02; 28.1 ± 0.2; 7.1 ± 0.3; 52.2 ± 0.2; 75.0 ± 1.0; 1.7 ± 0.1 nm | "(d) 498±15 1.32 ± 0.01 1.69 ± 0.02 28.1 ± 0.2 7.1 ± 0.3 52.2 ± 0.2 75.0 ± 1.0 1.7 ± 0.1" | S20 SI Table S1 | S20-EL-10 |
| SI Table S1, sample (e) | 562 ± 15 °C: 1.45 ± 0.10; 1.54 ± 0.06; 28.0 ± 2.0; 16.0 ± 0.7; 55.3 ± 0.8; 67.0 ± 7.3; 2.3 ± 0.2 nm | "(e) 562±15 1.45 ± 0.10 1.54 ± 0.06 28.0 ± 2.0 16.0 ± 0.7 55.3 ± 0.8 67.0 ± 7.3 2.3 ± 0.2" | S20 SI Table S1 | S20-EL-11 |
| Measurement conditions | 5 K, up to 5 T, Cryogenics Ltd. cryogen-free system | "Magnetotransport measurements were made at a temperature of 5 K in a Cryogenics Ltd. cryogen free measurement system using magnetic fields up to 5 T." | S20 Methods › Hall Bar Fabrication | S20-EL-12 |
| Hall bar, main text | **6-terminal**, UV photolithography, Al evaporated over the mesa edge | "Arsenic delta layer samples were fabricated into 6 terminal Hall bars using standard UV photolithography, with electrical contact made via aluminum thermally evaporated over the edge of the mesa structures." | S20 Methods › Hall Bar Fabrication | S20-EL-13 |
| Hall bar, SI (**conflict: 8 vs 6 terminals**) | **8-terminal**. Ohmic contact confirmed by 2-terminal IV (terminals 8–4, sample d, RTA 500 °C, 5 K) | "Eight-terminal Hall bars were fabricated from multiple Si:As delta layer samples and electrically characterized by IV, Hall, and magnetoresistance measurements." / "b) A two-terminal IV measurement (across terminals 8 and 4) on sample d (RTA = 500 °C) measured at 5 K, is both linear and symmetric indicating that the delta layer contacting is Ohmic." | S20 SI §b, Figure S2 caption | S20-EL-14 |
| Contact method | Al deposited directly onto the δ-layer edge | "Ohmic contacts achieved through deposition of aluminum directly onto the δ-layer edge." | S20 Results › Electrical Activation | S20-EL-15 |
| Sample count conflict | Text: five δ-layers. SI: "all six" samples, but Table S1 lists five (a–e) | "obtained from Hall measurements on five arsenic δ-layers" / SI: "Figure S3 shows Hall and magnetoresistance measurements for all six As delta-layer Hall bar samples" | S20 Results; SI §b | S20-EL-16 |
| Hall bar dimensions | not stated | n/a | n/a | S20-EL-17 |

## 8. Yield statistics (S24)

### 8a. Text and Table 1

| Spec | Value | Verbatim quote | Location | Key |
|---|---|---|---|---|
| 1DB adsorption [n = 286] | H re-termination 89 ± 2%; type-A AsH₂ 10 ± 2% | "From a total count of 286 1DB sites, we find 89 ± 2% have undergone re‐termination with a hydrogen atom and 10 ± 2% of 1DB sites have an adsorbed AsH2 fragment." | S24 §2.2 | S24-Y-01 |
| Table 1 rows, 1DB | H 89 ± 2% (N/A); type-A 10 ± 2% (incorporation 92 ± 6%); type-B 0.6 ± 0.6% (N/A) | "1DB (single dangling bond) H (re‐termination) 89 ± 2% N/A / 1DB Type‐A (dimer‐end AsH2) 10 ± 2% 92 ± 6% / 1DB Type‐B (dimer‐bridge AsH2) 0.6 ± 0.6% N/A" | S24 Table 1 | S24-Y-02 |
| Table 1 rows, 2DB | 2H 26 ± 5% (N/A); type-A 57 ± 10% (94 ± 3%); type-B 17 ± 10% (94 ± 3%) | "2DB (dimer dangling bond) 2H (re‐termination) 26 ± 5% N/A / 2DB Type‐A (dimer‐end AsH2+H) 57 ± 10% 94 ± 3% / 2DB Type‐B (dimer‐bridge AsH2) 17 ± 10% 94 ± 3%" | S24 Table 1 | S24-Y-03 |
| 2DB adsorption [n = 92] | as in Table 1 | "Following a statistical analysis of 92 2DB sites, we find 57 ± 10% of them contain a type‐A feature after saturation arsine exposure, 17 ± 10% contain a type‐B feature, and the remaining 26 ± 5% of 2DB sites are found to re‐terminate with hydrogen." | S24 §2.2 | S24-Y-04 |
| 1DB+2DB incorporation [n = 156] | 94 ± 3% at 2DB once AsH₂ is adsorbed | "To quantify this efficiency, we have analyzed arsenic incorporation at a combined 156 1DB and 2DB sites, and the results are presented in Table 1. We find a very high probability, 94 ± 3%, for arsenic incorporation at 2DB sites, once an AsH2 fragment has adsorbed." | S24 §2.2 | S24-Y-05 |
| 2DB overall (dose + anneal) | 70 ± 21% | "If we include the adsorption stage as well as the thermal incorporation stage, the arsenic incorporation success rate at 2DB sites drops to 70 ± 21%," | S24 §2.2 | S24-Y-06 |
| 1DB overall | 10 ± 3% | "The overall incorporation probability of arsenic at 1DB sites, including both the dosing and annealing stages, is 10 ± 3%" | S24 §2.2 | S24-Y-07 |
| 4DB adsorption [n = 24] | type-C 18/24 (75%); A/B 17%; D/E 8%; always exactly one AsHₓ (100%) | "This type‐C feature is never observed to form at 1DB or 2DB adsorption windows but is found to form at 18 of the total 24 measured 4DB adsorption windows (75%), following exposure to arsine. In addition to the type‐C feature, 4DB sites are also found to occasionally adsorb single type‐A or type‐B AsH2 + H features, or type‐D or type‐E As + 3H adsorbates, with probabilities of 17% and 8%, respectively." / "from our statistics of 24 4DB sites, we find 100% adsorption probability for a single AsH x species" | S24 §2.3 | S24-Y-08 |
| 6DB adsorption [n = 19] | A+C pair 12/19 (63%); lone D/E 21%; C 11%; A/B 5% | "This AsH3 adsorption structure is detected at 12 out of 19 exposed 6DB windows (63%). The remaining 37% of the 6DBs exhibit the adsorption of lone type‐D or type‐E features (21%), type‐C features (11%) or, type‐A or type‐B features (5%)." | S24 §2.3 | S24-Y-09 |
| Incorporation total [n = 206] | 206 isolated A–E features annealed to 350 °C | "we have assessed a combined total of 206 instances of isolated type A, B, C, D, and E features after thermal annealing to 350 °C" | S24 §2.3 | S24-Y-10 |
| Headline yield | 97 ± 2% at a 4DB window | "the result will be the incorporation of a single arsenic atom with a yield of 97 ± 2%." | S24 §2.3 | S24-Y-11 |
| Failure statement | 1% failure, all from H re-termination | "the 1% incorporation failure results exclusively from the re‐termination of the adsorption site with hydrogen, and not from the unintentional incorporation of more than one arsenic atom." | S24 §2.3 | S24-Y-12 |
| Sample sizes | adsorption n = 286, 92 (85+6+2), 24 (11+13), 19 (10+9). Incorporation n = 166 (156+10), 20, 20 | "Samples sizes for AsH3 adsorption at 1DB, 2DB, 4DB, and 6DB were n = 286, 92 (= 85 + 6 + 2), 24 (= 11 + 13), and 19 (= 10 + 9), respectively, and for incorporation anneals of type‐A/B, type‐C, and type‐D/E were n = 166 (= 156 + 10), 20 and 20, respectively," | S24 Experimental › Statistical Analysis | S24-Y-13 |
| Experiments | 3 adsorption experiments, 2 incorporation experiments | "Statistical data presented in Table 1 and Figure 3i,l are measured in three adsorption experiments and two incorporation experiments." | S24 Statistical Analysis | S24-Y-14 |
| 4×4 array result | 10/16 single As. 10–12 single atoms across 15 elements, up to 80% | "we infer that 10 out of the 16 intended array sites contain single arsenic atoms. Two further sites contain one or more As atoms and the remaining 4 sites either contain more than one arsenic atom or an unidentified feature. Excluding site a4, … this tally of 10 to 12 single atoms across 15 array elements represents a compounded single‐dopant‐atom placement success rate of up to 80%." | S24 §2.1 | S24-Y-15 |
| 4×4 site-by-site | single As–Si: a1, b1, c1, c2, c3. Double As–Si: a3, d3. ad-Si: a2, b2, b3, b4, d4. ad-Si clusters: c4, d1. Contaminant: a4, d2 | "Single As‐Si heterodimers can be observed in the five array sites a1, b1, c1, c2, c3; double As‐Si heterodimers in the two array sites a3, d3; isolated ad‐Si atoms in the five array sites a2, b2, b3, b4, d4; and ad‐Si clusters in the two array sites c4, d1. The remaining two sites, a4 and d2, feature unidentified contaminants." | S24 §2.1 | S24-Y-16 |
| 2×2 result | 4/4 incorporated; 1 shifted by 1 lattice spacing | "while 3‐of‐4 As‐Si remains at the site of delivery, the fourth example in the upper left corner appears to have shifted downward by 1 lattice spacing" | S24 §2.1 | S24-Y-17 |
| Spurious-density limits | 0.0016 nm⁻² As; 0.016 nm⁻² 1DB; achieved ≈0.008 nm⁻² | see S24-LITH-07 and S24-H-03; "the maximum permissible density of 1DBs prior to AsH3 exposure would then be 0.016 nm−2." | S24 §2.2 | S24-Y-18 |
| P comparison | <70% per atom; 0.7¹⁶ < 0.4% for 16 atoms | "the success rate of single phosphorus atom surface incorporation resulting from the thermal annealing of phosphine adsorbed in idealized six‐site windows is less than 70%." / "the probability of successfully creating a 16‐element single phosphorus‐atom array is 0.716, that is, less than 0.4%." | S24 1 Introduction | S24-Y-19 |

### 8b. [GRAPHIC] Fig. 3i and Fig. 3l values (labels printed on the bars; counts in brackets under the axis)

The caption says: "Numbers in square brackets below histogram columns indicate total counts per species." (S24 Figure 3 caption)

| Panel | Category [count] | Printed bar values (%) | Key |
|---|---|---|---|
| 3i adsorption | 1DB [286] | Terminated 89; A/B 11; C 0; D/E 0; C+A 0 | S24-G-01 |
| 3i adsorption | 2DB [92] | Terminated 26; A/B 74; C 0; D/E 0; C+A 0 | S24-G-02 |
| 3i adsorption | 4DB [24] | Terminated 0; A/B 17; C 75; D/E 8; C+A 0 | S24-G-03 |
| 3i adsorption | 6DB [19] | Terminated 0; A/B 5; C 11; D/E 21; C+A 63 | S24-G-04 |
| 3l incorporation | A/B (AsH₂) [166] | Incorporated 90.4; Indeterminate 6.6; Failed 3.0 | S24-G-05 |
| 3l incorporation | C (AsH) [20] | 100.0; 0.0; 0.0 | S24-G-06 |
| 3l incorporation | D/E (As) [20] | 85.0; 10.0; 5.0 | S24-G-07 |
| 3l incorporation | All AsHₓ (4DB weight) | 97.1; 0.9; 1.9 | S24-G-08 |

Notes: the graphic gives 1DB A/B as 11%, versus 10 ± 2% + 0.6 ± 0.6% in Table 1, and 2DB A/B as 74 = 57 + 17. The 4DB-weighted "Failed" bar is 1.9%, while the text (S24-Y-12) says "1% incorporation failure".

## 9. Surface geometry and adsorbate structure

| Spec | Value | Verbatim quote | Location | Key |
|---|---|---|---|---|
| Surface lattice constant a | 3.84 Å (graphic only). Not given in either paper's prose | printed "Si(001) lattice a = 3.84 Å" (unit cell a × 2a) | S24 Fig. 1i legend [GRAPHIC] | S24-GEO-01 |
| Lattice vector (text) | pitch 4.6 nm = ≈12 surface lattice vectors | see S24-LITH-06 | S24 §2.1 | S24-GEO-02 |
| Dimer-row spacing | not stated numerically in either paper. (The [GRAPHIC] unit cell shows 2a along one axis) | n/a | n/a | GEO-ROW |
| Bond lengths | not stated in either paper | n/a | n/a | GEO-BOND |
| H:Si(001) description | rows of dimers, 1 H per Si (monohydride) | "The hydrogen‐terminated Si(001) surface consists of rows of paired silicon atoms (dimers) with one hydrogen atom bonded to each silicon." | S24 §2.1 | S24-GEO-03 |
| Atomic radii, Z, I, ionization energies | r_As = 115 pm, r_P = 100 pm; Z 33/15; I 3/2 vs 1/2; 53.76 vs 45.59 meV | "a higher ionization energy in silicon (53.76 meV, compared to 45.59 meV for phosphorus), a larger atomic radius (rAs = 115 pm, rP = 100 pm), larger atomic spin–orbit interaction (ZAs = 33, ZP = 15), and a higher nuclear spin value (IAs = 3/2, IP = 1/2) than phosphorus." | S20 Introduction | S20-GEO-01 |
| Type-1 (isolated) structure | inter-row end-bridge As + 3H | "We assign the type-1 STM feature to the structure shown in Figure 1d, which we call the inter-row end-bridge As + 3H configuration." | S20 Results › Dissociation | S20-GEO-02 |
| Type-1 detail | As bridges 2 dimer ends on the lower row, with 2 H opposite it; hemihydride on the upper row | "The two protrusions in the STM images are assigned to the dangling bond end of a Si–Si–H hemihydride dimer on the upper row, and a dimer end-bridge arsenic atom on the lower row (where the remaining two hydrogen atoms are attached to the lower row, directly across from the end-bridge arsenic atom)." | S20 Results › Dissociation | S20-GEO-03 |
| Footprint | 2.5 dimers | "We assume that isolated molecules will dissociate in the type-1 structure, with a 2.5 dimer footprint" | S20 Results › Saturation Arsine Coverage | S20-GEO-04 |
| Type-1 / type-2 fractions | type-1 >75%; type-2 ~10–15% (intrarow end bridge) | "accounting for more than 75% of all AsH3-associated features" / "the type-2 feature comprises roughly 10–15% of the total AsH3 associated STM features, and corresponds to the intrarow end bridge structure" | S20 Results › Dissociation | S20-GEO-05 |
| DFT activation energies | (i) inter-row H-shift 0.23 eV (on-dimer 0.53, interdimer 0.29); (ii) on-dimer 0.63 eV (interdimer 0.72); (iv) 0.89 eV (rate-limiting) | "The calculated activation barrier for this reaction step is only 0.23 eV" / "which have calculated activation energies of 0.53 and 0.29 eV, respectively" / "The calculated activation energy for this reaction is 0.63 eV" / "has a slightly larger activation barrier of 0.72 eV" / "The reaction barrier for this final hydrogen-shift is calculated to be 0.89 eV; this is the rate-determining activation energy along the full dissociation path." | S20 Results › Dissociation | S20-GEO-06 |
| [GRAPHIC] Adsorption energies, Fig. 1g | dative AsH₃ −0.52; inter-row AsH₂+H −1.85; dimer-end AsH+2H −2.20; end-bridge AsH+2H −2.62; end-bridge As+3H −3.09 eV. Step (iii) E_A < 0.05 eV | printed labels | S20 Fig. 1g image | S20-GEO-07 |
| DFT method | Gaussian 09, B3LYP, 6-311G(2df,2pd), Si₁₅H₁₆ or Si₅₄H₄₄ clusters (CCM) | "This approach uses the B3LYP hybrid exact-exchange density functional and a large 6-311G(2df,2pd) atom-centered basis set, and the Si(001) surface is represented using hydrogen-truncated cluster models, such as Si15H16 or Si54H44, with correction terms applied to minimize the effects of finite cluster size." | S20 Methods › DFT | S20-GEO-08 |
| KMC parameters | 10¹³ s⁻¹ attempt frequency, 298 K, 40 × 40 supercells, 100 trajectories | "an assumed attempt frequency of 1013 s-1 and a temperature of 298 K" / "using large 40x40 super cells and an average over 100 trajectories for each pressure" | S20 SI §a | S20-GEO-09 |
| As–Si heterodimer | analogous to P–Si. Sits in the first layer | "High-resolution filled and empty state images of two such As–Si heterodimers (inset of Figure 2b) reveal an appearance that is very similar to that of P–Si heterodimers" / "Isolated As–Si heterodimers (HD) are observed in the first layer of the silicon surface" | S20 Results; Figure 2 caption | S20-GEO-10 |
| S24 adsorbate types A–E | A: AsH₂ dimer-end (asymmetric). B: AsH₂ dimer-bridge (symmetric). C: AsH+2H (AsH bridging one dimer, 2H on the neighbor). D/E: As+3H variants | "in the case of the type‐A feature, the AsH2 occupies a dimer‐end position and the feature is therefore asymmetric about the dimer row, while in the type‐B feature, we suggest that the AsH2 is bridge bonded across a silicon dimer … The type‐C feature is an AsH+2H configuration where the AsH fragment is bound symmetrically across one dimer, while the two dissociated hydrogen atoms passivate the neighboring dimer. The type‐D and type‐E features are assigned to two variants of an As+3H configuration that only occur at sites large enough to accommodate the full dissociation of the molecule." | S24 §2.1 | S24-GEO-04 |
| S24 structures are tentative | not assigned with certainty | "The exact structural arrangements of each feature type are not assigned here with absolute certainty but are offered as probable arrangements" | S24 §2.1 | S24-GEO-05 |
| S24 SI product types | e-Si (end-bridge), b-Si (dimer-bridge), As–Si, 2DB | "adsorbed silicon monomers e‐Si (end-bridge) and b-Si (dimer bridge), arsenic-silicon heterodimer (As-Si), and silicon dangling bonds (2DB)" | S24 SI Fig. S1 caption | S24-GEO-06 |
| DB contrast mechanism | DB orbital energy closer to E_F | "appear bright in the images due to the existence of broken, or “dangling” bonds (DBs) whose orbital energy lies closer to the Fermi level" | S24 §2.1 | S24-GEO-07 |

## 10. Other dimensional and thermal items

| Spec | Value | Verbatim quote | Location | Key |
|---|---|---|---|---|
| S20 imaging, Fig. 1 | −1.7 V / +1.6 V, 0.10 nA | "Sample voltage, V = −1.7 V, +1.6 V; tunneling current, I = 0.10 nA." | S20 Figure 1 caption | S20-X-01 |
| S20 imaging, Fig. 3 | −2.0 V, 0.10 nA | "V = −2.0 V, I = 0.10 nA." | S20 Figure 3 caption | S20-X-02 |
| S20 dose-rate ratio | AsH₃ dissociates 3 orders of magnitude faster than PH₃ | "due to a dissociation rate that is 3 orders of magnitude more rapid than that of PH3." | S20 Results | S20-X-03 |
| S20 incomplete-activation reference | >10²⁰ cm⁻³ (2×10¹³ cm⁻²) | "resulting in incomplete activation at concentrations >1020 cm–3 (or 2 × 1013 cm–2)" | S20 Results › Electrical Activation | S20-X-04 |
| S20 "few nanometers" cap | generic statement | "the dopant structure must then be buried beneath a few nanometers of epitaxial silicon." | S20 Results › Encapsulation | S20-X-05 |
| S24 imaging params | a) −2 V, 40 pA; b,c) −2 V, 100 pA; d,e) −2 V, 60 pA; f–h) −2 V, 40 pA (Fig. 1). Fig. 2: −2.1 V, 20 pA. Fig. 3: a–h −2 V, 60 pA; j,k −2 V, 100 pA | "Imaging parameters: a) −2 V, 40 pA; b,c) −2 V, 100 pA; d,e) −2 V, 60 pA; f–h) −2 V, 40 pA." / "Imaging parameters: a–c) −2.1 V, 20 pA." / "Imagining parameters: a–h) −2 V, 60 pA, j,k) −2 V, 100 pA." | S24 Fig. 1, 2, 3 captions | S24-X-01 |
| S24 false-color height scales | Fig. 1: a) −200 to +400 pm; b) −100 to +250 pm; c) −75 to +200; f–h) "100‐+200 pm". Fig. 2: main −225 to +200 pm, insets −100 to +225 pm | "False color scales: a) −200‐+400 pm; b) −100‐+250 pm, c) −75‐+200, f–h) = 100‐+200 pm." / "False color scales: main −225‐+200 pm; insets −100‐+225 pm." | S24 Fig. 1, 2 captions | S24-X-02 |
| S24 SI image areas | Fig. S2: 100 × 80 nm. Fig. S3: 190 × 150 nm | "The same 100×80 nm area of an H:Si(001) surface" / "The same 190 ×150 nm area of a H:Si(001) surface" | S24 SI Fig. S2, S3 captions | S24-X-03 |
| S24 SI line-profile color scales | a) −100 to 350 pm; b) −50 to 250 pm | "False colour scales: a) -100..350 pm; b) -50..250 pm." | S24 SI Fig. S1 caption | S24-X-04 |
| S24 incorporation exclusion rule | adsorbates within 1 dimer of a defect are excluded | "Incorporation data was sorted to exclude AsH x adsorbates positioned within one silicon dimer of a defect or another adsorbate, pre‐anneal." | S24 Statistical Analysis | S24-X-05 |

---

## Contradictions and inconsistencies found

1. **S24 lithography settings**: the Methods give "+4 V, … 3.5 nA, … 50 nm s−1", but the Fig. 1 and Fig. 3 captions give "3.5 V, 3000 pA, 50 nm s−1" (S24-LITH-02 vs -03).
2. **S24 pitch**: the text gives "≈12 … lattice vectors, or 4.6 nm"; §2.2 says "5 nm array pitch"; the SI says "~5 nm pitch" (S24-LITH-06/07/10).
3. **S20 anneal times**: for Fig. 2e the text says 5 min and the caption says 1 min. For Fig. 3d the text says 2 min and the caption says 1 min (S20-INC-02 to -05).
4. **S20 SIMS panels**: the text says "four different temperature programs", but the caption and figure show five (a–e).
5. **S20 overgrowth time and thickness**: "10 min" plus "230 min" at "1 ML/min" or "1.5 Å/min" does not equal "15 nm" (S20-ENC-20). The figure's time axis does run to ~240 min.
6. **S20 Fig. 4c peak**: the text says ~5×10²⁰ cm⁻³; the plotted peak reads ~1×10²¹ (visual reading). The Fig. 4e peak sits at ~17 nm, not 15 nm (visual reading).
7. **S20 Hall bars**: the main Methods say "6 terminal"; the SI says "Eight-terminal". The text says five samples; the SI says "all six" but its table lists five.
8. **S20 Conclusions**: "1.5 kΩ/square" and "1.3 × 10¹⁴ cm–3" (unit typo; it should be cm⁻²). The Results give a 1.6 ± 0.1 kΩ/□ plateau. Table S1 has 1.69 kΩ/□ and 1.32×10¹⁴ at 498 °C, and 1.54 kΩ/□ at 562 °C.
9. **S24 failure rate**: the text says "1% incorporation failure"; the Fig. 3l bar reads Failed 1.9%, Indeterminate 0.9%.
10. **Substrates differ**: S20 uses P-doped CZ, 1–10 Ω·cm; S24 uses As-doped, 15 Ω·cm. Pyrometer uncertainty is ±30 °C in S20 and ±20 °C in S24. STM base pressure is <5×10⁻¹¹ mbar in S20 and 3×10⁻¹¹ mbar in S24.
11. **Saturation dose**: S20 uses 1.5 L (5×10⁻⁹ mbar × 5 min); S24 uses 3 L (5×10⁻⁹ mbar × 10 min).
12. **S20 H-termination recipe, both papers' flash duration and cooling, ramp rates, line dose, bond lengths, dimer-row spacing, Fig. 1f electrode dimensions and gaps, and Hall-bar dimensions** are all **not stated**.
