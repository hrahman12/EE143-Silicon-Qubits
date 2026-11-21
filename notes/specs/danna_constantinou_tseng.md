# Fabrication / geometry / measurement specs: D'Anna 2023, Constantinou 2023, Constantinou 2024, Tseng 2023

Extracted from the local open-access copies in `figures/raw/` (D'Anna: UCL Discovery PDF; the others: PMC full text, with figures checked against the PMC JPGs and PDF renders).

Conventions:
- **Verbatim quote** is copied from the paper. In the PDF/PMC text extraction, superscripts were flattened (e.g. "10−10 mBar"). I restored them with Unicode superscripts (10⁻¹⁰) and changed nothing else. "[...]" marks an omission.
- **Location** gives the section, Methods/Experimental subsection, table or figure caption, plus the PDF page for D'Anna.
- Rows marked **(figure label)** come from text printed inside a figure, not from the body or caption. The quote column then holds the label exactly as drawn, and I describe what it labels.
- **not stated**: I searched the full text and captions and found no value. No value here comes from memory.
- **Key**: a stable ID for slide cross-referencing. ★ marks the rows that matter most for diagram redraws.

---

## 1. D'Anna et al., Adv. Electron. Mater. 9, 2201212 (2023), doi:10.1002/aelm.202201212

### 1a. Sample stack (cross-section, bottom to top)

| Spec | Value | Verbatim quote | Location | Key |
|---|---|---|---|---|
| Substrate | Si(001), CZ, 0.5 mm thick, bulk As 3 × 10¹⁴ cm⁻³, >15 Ω cm; die 2 × 9 mm² | "Si(001) samples were diced to 2 × 9 mm² from a 0.5 mm thick, Czochralski-grown wafer, with bulk As doping of density 3 × 10¹⁴ cm⁻³, and resistivity >15 Ω cm." | §6 Experimental Section, *Sample Preparation* (p. 6) | ★ DA-SUB |
| Surface clean | Ultrasonic acetone then IPA; outgas >8 h at 600 °C; multiple flashes at 1200 °C; base <5 × 10⁻¹⁰ mBar | "These samples were cleaned ultrasonically in acetone followed by isopropyl alcohol. Each sample was thermally outgassed in vacuum (base pressure <5 × 10⁻¹⁰ mBar) for >8 h at 600 °C, and flash-annealed multiple times at 1200 °C, using direct current resistive sample heating." | §6, *Sample Preparation* (p. 6) | ★ DA-CLEAN |
| Pyrometer | IMPAC IGA50-LO plus, ±30 °C | "Sample temperature was monitored using an infrared pyrometer (IMPAC IGA50-LO plus) with a total estimated measurement uncertainty of ± 30 °C." | §6, *Sample Preparation* (p. 6) | DA-PYRO |
| δ-layer dosing | AsH₃ (arsine) dose; density set by total exposure | "The samples were dosed with AsH₃ with varying total exposures to control the dopant density." | §6, *Sample Preparation* (p. 6) | ★ DA-DOSE |
| Incorporation anneal | 350 °C, 2 min | "They were then heated at 350 °C for 2 min to incorporate the dopants into the Si lattice." | §6, *Sample Preparation* (p. 6) | ★ DA-INC |
| STM check | Omicron VT-STM, RT, <5 × 10⁻¹¹ mBar | "All STM measurements were performed in an Omicron variable temperature series STM at room temperature with a base pressure of <5 × 10⁻¹¹ mBar." | §6, *Sample Preparation* (p. 6) | DA-STM |
| Lock layer | 2 nm Si, no heating (room temperature) | "After incorporation, 2 nm of Si were deposited on the samples with no resistive sample heating." | §6, *Sample Preparation* (p. 6) | ★ DA-LOCK |
| RTA | 500 °C, 15 s | "The samples were then resistively heated to 500 °C for 15 s. This procedure gives a well-confined, electrically active dopant layer." | §6, *Sample Preparation* (p. 6) | ★ DA-RTA |
| Cap | 28 nm Si at 250 °C | "A further 28 nm of Si were deposited on the samples held at 250 °C." | §6, *Sample Preparation* (p. 6) | ★ DA-CAP |
| Si deposition source / rate / pressure | SUSI-40 sublimation source, 0.003 nm s⁻¹, 2 × 10⁻¹⁰ mBar | "Si deposition was performed at a base pressure of 2 × 10⁻¹⁰ mBar, using an all-silicon, solid sublimation source (SUSI-40, MBE Komponenten GmbH) operated at a deposition rate of 0.003 nm s⁻¹." | §6, *Sample Preparation* (p. 6) | ★ DA-RATE |
| Temperature during growth | Inferred from sample resistance | "During Si deposition, the sample temperature was indirectly monitored by measuring the sample resistance, while heating using a direct current resistive sample heater." | §6, *Sample Preparation* (p. 6) | DA-TGROW |
| Total δ-layer depth | 30 nm (= 2 + 28 nm) | "Structures consisting of atomically thin layers of As ("As δ-layers") buried 30 nm below the Si(100) surface were patterned into 20 × 200 µm² Hall bars and contacted with Al" | §3 Subsurface Imaging (p. 3) | ★ DA-DEPTH |
| Process summary | Dose, anneal, overgrow | "The As layer is made by exposing atomically flat Si to a dose of arsine, annealing the wafer to incorporate the As into the surface layers, then overgrowing with epitaxial Si." | §3 (p. 3) | DA-FLOW |
| Native oxide / passivation on top | not stated | — | — | DA-OX |

### 1b. Device geometry and patterning

| Spec | Value | Verbatim quote | Location | Key |
|---|---|---|---|---|
| Hall-bar size | 20 × 200 µm² | "patterned into 20 × 200 µm² Hall bars and contacted with Al" | §3 (p. 3) | ★ DA-HB |
| Hall-bar width (confirmed by XRF) | 20 µm | "The As fluorescence signal clearly resolves the 20 µm width of the Hall bar" | Fig. 3 caption (p. 4) | ★ DA-HBW |
| Fig. 2d "100 µm" | Spacing along the bar between adjacent voltage-probe arms. The arrow runs from the left arm to the centre arm; whether it is edge-to-edge or centre-to-centre cannot be resolved at this scale | "100 µm" (figure label) | Fig. 2d schematic (p. 3) | ★ DA-F2d-100 |
| Fig. 2d "20 µm" | Width of the horizontal Hall-bar channel (arrows above and below the bar) | "20 µm" (figure label) | Fig. 2d schematic (p. 3) | ★ DA-F2d-20 |
| Fig. 2d "5 µm" | Width of a vertical voltage-probe arm at its narrowest point, where it meets the channel. The arms taper outward into trapezoidal leads | "5 µm" (figure label) | Fig. 2d schematic (p. 3) | ★ DA-F2d-5 |
| Fig. 2d caption | Top view; orange = As layer | "d) Sketch of the top view of the samples with the As Hall-bar structure shown in orange." | Fig. 2 caption (p. 3) | DA-F2d-CAP |
| Layout seen in As XRF map (Fig. 2c) | Cross-shaped bar with 6 side arms (3 up, 3 down) plus 2 end leads, all fanning into large pads. Scale bar 200 µm | "200 µm" (figure label, scale bar on panels a–c) | Fig. 2a–c (p. 3) | DA-F2c |
| Bond / contact pad size | not stated (square Al pads visible in the Fe map, Fig. 2b) | — | — | DA-PAD |
| Number of Hall bars per die | 2, plus an unetched SIMS region; die cleaved between them | "On each sample, two Hall bars were produced, as well as an unetched region to be used for SIMS. The samples were cleaved between the two Hall bars." | §6, *Sample Preparation* (p. 6) | DA-NHB |
| Lithography | Optical lithography | "the samples were etched into Hall bars. This was done using optical lithography and reactive ion etching." | §6, *Sample Preparation* (p. 6) | ★ DA-LITH |
| EBL | not stated (only optical lithography is mentioned) | — | — | DA-EBL |
| Etch method | Reactive ion etching (RIE) | (same quote as DA-LITH) | §6 (p. 6) | ★ DA-ETCH |
| Etch depth (mesa) | not stated | — | — | DA-ETCHD |
| Ohmic contacts | Al deposited into arrays of etched holes that extend through the δ-layer | "Ohmic contacts were established by deposition of Al into arrays of etched holes extending through the δ-layer.[47]" | §6, *Sample Preparation* (p. 6) | ★ DA-OHM |
| Al thickness | not stated | — | — | DA-ALT |
| Al deposition method | not stated | — | — | DA-ALDEP |
| Contact anneal | not stated | — | — | DA-ALANN |
| Contact-hole size / pitch | not stated | — | — | DA-HOLE |
| Areal Al / Fe density in contacts (XRF) | n_Al = 6.0 × 10¹⁵ cm⁻²; n_Fe = 1 × 10¹³ cm⁻² | "While the Fe density is only n_Fe = 1 × 10¹³ cm⁻² in the Al contacts, it provides a stronger XRF signal than the Al whose density is n_Al = 6.0 × 10¹⁵ cm⁻²." | §3 (p. 4) | DA-ALN |
| Packaging | Chip carrier, Al wire bonds | "Each Hall bar was mounted on a chip carrier, and electrically connected to the carrier by Al wire bonds." | §6 (p. 6) | DA-PKG |
| Registration markers / alignment | not stated | — | — | DA-MARK |

### 1c. X-ray fluorescence (XRF) imaging

| Spec | Value | Verbatim quote | Location | Key |
|---|---|---|---|---|
| Beamline | microXAS, Swiss Light Source; range ≈4–22 keV | "XRF experiments reported here were conducted at the microXAS beamline of the Swiss Light Source synchrotron.[21] The beamline employs high brightness X-rays in the energy range from ≈4 to 22 keV." | §2 X-Ray Fluorescence (p. 2) | DA-BL |
| Photon energy | 11.88 keV (confirmed) | "At the photon energy of 11.88 keV used here, the delivered photon flux is approximately I₀ = 10¹⁰ photons s⁻¹ when the beam is focused to 1 × 1 µm² using a Kirkpatrick–Baez mirror system, and an energy resolution of ΔE/E < 10⁻⁴ is chosen." | §2 (p. 2) | ★ DA-E |
| Why 11.88 keV | Above the As K edge; below the Au excitation threshold | "An X-ray energy of 11.88 keV is sufficiently high to dislodge core electrons from the As K-levels, without exciting the gold atoms found in parts of the sample holder." | §2 (p. 2) | DA-EWHY |
| Spot size (device #1) | 1 × 1 µm², KB mirrors, flux 10¹⁰ ph s⁻¹ | (see DA-E) and "The X-ray beam with a photon energy of 11.88 keV from the synchrotron is focused to 1 µm with the help of a Kirkpatrick-Baez (KB) mirror system." | §2; Fig. 1 caption (p. 2) | ★ DA-SPOT |
| Spot size (device #2) | 1 × 3 µm² (3 µm horizontal), flux 10¹¹ ph s⁻¹ | "The low-density device #2 was also measured in an identical fashion except that the beam size was increased to 1 × 3 µm² yielding a photon flux of I₀ = 10¹¹ photons s⁻¹." / "(red, 3 × 1 µm² spot size, with 3 µm horizontal width and photon flux I₀ = 10¹¹ photons s⁻¹)" | §3 (p. 4); Fig. 3 caption | DA-SPOT2 |
| Incidence | Normal incidence | "The beam was set to normal incidence." | §2 (p. 2) | DA-INCID |
| Step size | 500 nm (0.5 µm) | "the sample swept across the beam with a step size of 500 nm, and for each position a full fluorescence spectrum was recorded." | §2 (p. 3) | ★ DA-STEP |
| Dwell per pixel | 200 ms | "For each pixel of the image a spectrum is recorded for a duration of 200 ms." / Fig. 2: "a beam size of 1 × 1 µm², and a step-size of 0.5 µm. At each step a spectrum is recorded during 200 ms." | §3 (p. 3); Fig. 2 caption | ★ DA-DWELL |
| Detector | Silicon drift detector, 50 mm² active area, d = 2 cm, Ω = 0.04π, He-flushed 15 mm pinhole cavity, gas exit 2 mm from sample | "with a gentle flow of helium gas into a 15 mm long pinhole cavity that encapsulates a silicon drift detector, with the exit gas flow located 2 mm from the sample position. The silicon drift detector with an active area of 50 mm² was placed in close proximity of the sample [...] the solid angle captured by the detector is Ω = 0.04π." / "a photodetector is placed at d = 2 cm away from the sample" | §2 (p. 2); Fig. 1 caption | ★ DA-DET |
| Ambient | Air, room temperature | "Measurements were conducted in air at room temperature" | §2 (p. 2) | DA-AMB |
| Spectral decomposition | PyMca; reference standard from nanoXRF_standards | "The collected spectrum is then decomposed into the sum of the individual atom-specific spectra with the PyMca software.[22] [...] it is compared to an As-containing reference sample from nanoXRF_standards[23]" | §2 (p. 2) | DA-PYMCA |
| Dose | 2000 photons nm⁻² at 11.88 keV; 1.5 × 10¹⁰ Sv (1.5 × 10¹⁶ Rad cm⁻², 1.7 × 10⁻¹⁴ J nm⁻³); 0.3 photons absorbed per As atom | "During the X-ray imaging the sample absorbs 2′000 photons nm⁻² at an energy of 11.88 keV, corresponding to a radiation dose of 1.5 × 10¹⁰ Sv (1.5 × 10¹⁶ Rad cm⁻² or 1.7 × 10⁻¹⁴ J nm⁻³). [...] we find that each As atom absorbs on average 0.3 photons during the measurement." | §4.1 Magneto-Conductance (p. 5) | ★ DA-DOSEX |
| As atoms in spot; photons absorbed per 200 ms | 1.7 × 10⁵ (#2) and 1.4 × 10⁶ (#1) atoms; 1.9 × 10⁵ and 4.8 × 10⁵ photons | "in the low- and high-density device there were 1.7 × 10⁵ and 1.4 × 10⁶ As atoms within the spot size, respectively. [...] the number of photons absorbed collectively by the As atoms in 200 ms was 1.9 × 10⁵ and 4.8 × 10⁵ photons for the low- and high-density device, respectively." | §3 (p. 4) | DA-NSPOT |
| Signal/noise | ≈7 (#1), ≈2 (#2) | "features a signal/noise ratio of ≈7 and ≈2 for the high- and low-density Hall bars, respectively." | Fig. 3 caption (p. 4) | DA-SNR |
| Uncertainty of XRF density | <5 % | "the use of a reference sample yields an error of less than 5%." | §3 (p. 4) | DA-XERR |
| Projected resolution | 5 nm spot at 10⁹ ph s⁻¹ (Döring et al.); single-dopant images within 5 nm radii | "a 5 nm spot size is obtained with a flux of 10⁹ photons s⁻¹." / Abstract: "it will be possible to obtain X-ray images of single dopant atoms within resolved radii of 5 nm." | §3 (p. 4); Abstract | DA-FUT |

### 1d. Densities, transport, and non-destructiveness

| Spec | Value | Verbatim quote | Location | Key |
|---|---|---|---|---|
| Nominal densities | 1.6 × 10¹⁴ and 1 × 10¹³ cm⁻² | "one with a nominal As density of n_As = 1.6 × 10¹⁴ cm⁻² and the other with n_As = 1 × 10¹³ cm⁻²." | §3 (p. 3) | DA-NNOM |
| Table 1, device #1 | n_STM 1.6 ± 0.3; n_XRF 1.40 ± 0.07; n_Hall 1.31 ± 0.03; n_SIMS 1.8 ± 0.2 (×10¹⁴ cm⁻²); t_SIMS 2.7 ± 0.2 nm; t_MR 0.97 ± 0.02 nm | Table row: "#1 1.6 ± 0.3 1.40 ± 0.07 1.31 ± 0.03 1.8 ± 0.2 2.7 ± 0.2 0.97 ± 0.02" | Table 1 (p. 4) | ★ DA-T1-1 |
| Table 1, device #2 | n_STM 0.10 ± 0.03; n_XRF 0.06 ± 0.01; n_SIMS 0.21 ± 0.02 (×10¹⁴); t_SIMS 3.6 ± 0.4 nm; no Hall or MR (not conductive) | Table row: "#2 0.10 ± 0.03 0.06 ± 0.01 – 0.21 ± 0.02 3.6 ± 0.4 –" / "Device #2 was not conductive and, therefore, Hall measurements were not possible." | Table 1 and footnote (p. 4) | DA-T1-2 |
| Activation | 94 ± 5 % (#1) | "we find that the dopant activation in the high-density Hall bar #1 is 94 ± 5%." | §3 (p. 4) | ★ DA-ACT |
| Hall density before / after | 1.31 ± 0.03 → 1.27 ± 0.06 × 10¹⁴ cm⁻² | "The derived Hall electron density is n = 1.31 ± 0.03 × 10¹⁴ cm⁻² before and n = 1.27 ± 0.06 × 10¹⁴ cm⁻² after the XRF measurements." | §4.1 (p. 6) | ★ DA-NHALL |
| Mobility | not stated as a number (only the mean free path is given) | — | — | DA-MU |
| Mean free path before / after | 4.8 ± 0.1 nm → 4.9 ± 0.2 nm | "gives a mean free path L = ℏ√(2πn)µ/e = 4.8 ± 0.1 nm and L = 4.9 ± 0.2 nm before and after the XRF measurements, respectively" (formula rendered from the garbled PDF text) | §4.1 (p. 6) | DA-MFP |
| Coherence length before / after | 73.6 ± 0.4 nm → 74.2 ± 0.3 nm | "Before the XRF, the magneto-conductance yields a coherence length of Lφ = 73.6 ± 0.4 nm and δ-layer thickness of t = 0.98 ± 0.02 nm. After the XRF measurement we obtain Lφ = 74.2 ± 0.3 nm and t = 0.97 ± 0.02 nm." | §4.1 (p. 6) | DA-LPHI |
| Electronic thickness (WL) before / after | 0.98 ± 0.02 nm → 0.97 ± 0.02 nm | (same quote as DA-LPHI) | §4.1 (p. 6) | ★ DA-TMR |
| Tilt exponent p before / after | 1.9 ± 0.3 → 2.3 ± 0.5 | "we obtain p = 1.9 ± 0.3 and p = 2.3 ± 0.5 before and after the XRF, respectively." | §4.1 (p. 6) | DA-P |
| Dopant-motion bound | 0.2 Å | "the determination of the thickness by the weak-localization measurements has a precision of 0.2 Å, which sets a strict bound to the extent X-rays could have displaced the atoms." / Abstract: "upper bounds of 0.2 Angstroms for the radiation-induced motion of the typical As atom and 3% for the loss of activated, carrier-contributing dopants." | §4.1 (p. 6); Abstract | ★ DA-BOUND |
| Activated-dopant loss bound | 3 % | (see DA-BOUND, Abstract) | Abstract (p. 1) | ★ DA-LOSS |
| Measurement temperature | T = 1.8 K; fields up to 9 T (PPMS) | "we measure the magneto-transport at T = 1.8 K of the high-density device #1 before and after the exposure to the X-rays." / "can control the temperature down to T = 1.8 K and the magnetic field up to B = 9 T." | §4.1 (p. 5); §6 *Magneto-Transport Setup* (p. 7) | ★ DA-TMEAS |
| Transport excitation | Four-point, 5 Hz square wave, 100 nA | "The resistance is measured in a four-point geometry using a resistance bridge and with a 5 Hz square-wave 100 nA current." | §6 *Magneto-Transport Setup* (p. 7) | DA-IEXC |
| SIMS | IONTOF ToF-SIMS5; 25 keV Bi⁺ probe; 500 eV, 35 nA Cs⁺ sputter; 300 × 300 µm² crater; 50 × 50 µm² analysis area | "using an IONTOF ToF-SIMS(5) system with a 25 keV Bi⁺ primary ion beam in high current bunch mode, and a 500 eV, 35 nA Cs⁺ sputter beam. Depth profiles were made with a 300 × 300 µm² sputter crater, and the analytical region was the central 50 × 50 µm² of the sputter region." | §6 *Secondary-Ion Mass Spectrometry* (p. 7) | DA-SIMS |

---

## 2. Constantinou et al., Adv. Sci. 10, 2302101 (2023), doi:10.1002/advs.202302101

| Spec | Value | Verbatim quote | Location | Key |
|---|---|---|---|---|
| Substrate | n-type Si(001), 10 Ω cm | "Silicon n‐type (10 Ω cm) Si(001) substrates were degassed and flash annealed to ≈1200 °C under ultra‐high vacuum (< 5 × 10⁻¹⁰ mbar)." | §5 Experimental Section, *Sample Fabrication* | ★ C23-SUB |
| Flash | ≈1200 °C, <5 × 10⁻¹⁰ mbar | (same quote as C23-SUB) | §5, *Sample Fabrication* | ★ C23-FLASH |
| Sample types | P (phosphine) and As (arsine) δ-layers, saturation dose | "The atomically clean and flat surfaces were exposed to a saturation dose of phosphine or arsine, and then annealed at 350 °C for 2 min to substitutionally incorporate the dopants." | §5, *Sample Fabrication* | ★ C23-TYPES |
| Incorporation anneal | 350 °C, 2 min | (same quote as C23-TYPES) | §5 | ★ C23-INC |
| Overgrowth thickness | 2 or 3 nm (also 1 and 4 nm attempted) | "The dopant layer was then encapsulated by overgrowing either 2 or 3 nm of silicon using a silicon sublimation source, with a deposition rate of 1 ML/min." | §5, *Sample Fabrication* | ★ C23-OG |
| Four analysed samples | P 2 nm, P 3 nm, As 2 nm, As 3 nm | "Two of the samples were phosphorous δ‐layers and two were arsenic δ‐layers, and for each dopant species we have performed a nominal silicon overgrowth of 2 and 3 nm." | §3.2 | C23-SET |
| 1 nm and 4 nm overgrowth | 1 nm: no conduction states (fully oxidised); 4 nm: signal too weak | "We note that measurements were also made on samples overgrown with 1 and 4 nm of silicon. For the former, no conduction states were observed, which we attribute to the complete oxidation of the δ‐layer [...] For the latter, the spectral intensity of the conduction states became very weak" | §3.2 | C23-1-4 |
| Si deposition rate | 1 ML/min | (see C23-OG) | §5 | C23-RATE |
| Lock-layer recipe | First 1.3 nm at RT; RTA 500 °C 15 s; rest at 250 °C | "the first 1.3 nm of silicon was grown at room temperature, followed by a rapid thermal anneal at 500 °C for 15 s and a low‐temperature epitaxial growth at 250 °C for the remainder of the overgrowth." | §5, *Sample Fabrication* | ★ C23-LOCK |
| Top surface | Native oxide from ambient exposure | "Schematic representation of our δ‐layer samples, with a native oxide that forms due to ambient exposure. The silicon overgrowth thickness, z, is indicated, as is the electronic thickness of the δ‐layer, δz." | Fig. 1a caption | ★ C23-OX |
| Fig. 1a stack labels | SiO₂ / δ-layer / Silicon; depth tick marks 1 nm apart | "SiO₂", "δ-layer", "Silicon" (figure labels); caption: "The tic‐marks on the depth axis indicate 1 nm steps." | Fig. 1a | C23-F1a |
| Carrier density (ARPES Luttinger count) | (0.88 ± 0.10) × 10¹⁴ cm⁻² for all samples | "We find that the resulting total carrier density for all samples lie within the range (0.88 ± 0.10) × 10¹⁴ cm⁻², consistent with Hall effect measurements for all but one of the samples considered" | §3.1 | ★ C23-N |
| Saturation limit | ≈1.4 × 10¹⁴ cm⁻² (¼ ML) | "at the self‐saturation limit of δ‐doping, one in every four silicon (001) surface atoms is replaced with a dopant, corresponding to a density of ≈ 1.4 × 10¹⁴ cm⁻²." | §3.1 | C23-NSAT |
| δz, As (text summary) | 5.4 ± 0.1 Å | "We find that for the arsenic δ‐layer samples, δz = 5.4 ± 0.1 Å, whereas for the phosphorus δ‐layer samples, δz = 9.7 ± 4.1 Å." | §3.2 | ★ C23-DZ-As |
| δz, P (text summary) | 9.7 ± 4.1 Å | (same quote as C23-DZ-As) | §3.2 | ★ C23-DZ-P |
| Table 1: As, z = 2 nm | SIMS 2.01 ± 0.2 nm; SX-ARPES 0.45 ± 0.04 nm | "As, z = 2 nm 2.01 ± 0.2 0.45 ± 0.04" | Table 1 | ★ C23-T-As2 |
| Table 1: As, 3 nm | SIMS 2.22 ± 0.2 nm; SX-ARPES 0.62 ± 0.10 nm | "As, 3 nm 2.22 ± 0.2 0.62 ± 0.10" | Table 1 | ★ C23-T-As3 |
| Table 1: P, 2 nm | SIMS 2.24 ± 0.2 nm; SX-ARPES 0.91 ± 0.21 nm | "P, 2 nm 2.24 ± 0.2 0.91 ± 0.21" | Table 1 | ★ C23-T-P2 |
| Table 1: P, 3 nm | SIMS 2.86 ± 0.2 nm; SX-ARPES 1.03 ± 0.35 nm | "P, 3 nm 2.86 ± 0.2 1.03 ± 0.35" | Table 1 | ★ C23-T-P3 |
| Thinnest layer | 0.45 ± 0.04 nm (As, 2 nm cap) | "our thinnest arsenic δ‐layer has an electronic thickness of 0.45 ± 0.04 nm." | §4 Conclusion | C23-MIN |
| δz equation | δz = 1/(δk_z − δk_∞) | "(1) δz=1δkz−δk∞" (PMC rendering of δz = 1/(δk_z − δk_∞)) | §2 Background, Eq. 1 | C23-EQ1 |
| Subbands supported | 1Γ, 2Γ, 1Δ (only one Δ subband observed) | "our calculations show that each of our δ‐layer samples should support 1Γ, 2Γ, and 1Δ states." / "only a single 1Δ state is observed experimentally." | §3.3 | ★ C23-SB |
| Subband energies (numbers) | Not tabulated in the text; plotted only in Fig. 4a. Read from the plot (approximate): theory curves near δz ≈ 4–5 Å give 1Γ ≈ −0.21 eV, 1Δ ≈ −0.10 eV, 2Γ ≈ 0 eV; at 22 Å, 1Γ ≈ −0.15, 1Δ ≈ −0.10, 2Γ ≈ −0.065 eV. ARPES points cluster between −0.02 and −0.18 eV | Fig. 4a axis "E_B − E_F (eV)" vs "δz (Å)"; caption: "a) Measured and calculated energies of the δ‐layer subbands." | Fig. 4a (plot reading, not a stated number) | C23-EN |
| Subband occupations (theory) | 1Δ 68 %, 1Γ 26 %, 2Γ 6 %; ≈16.6 % per valley | "68%", "26%", "6%" (figure labels, "Theory" bar); caption: "For the theory, the percentages denote the occupation of each δ‐layer subband; when the degeneracy is accounted for, each one of the six valleys have an equal occupancy of ≈16.6%." | Fig. 4b and caption | ★ C23-OCC |
| Occupation (experiment) | Carriers split equally between Γ and Δ (per-sample bars in Fig. 4b, no numbers) | "we find that the carriers are equally distributed within the Γ and Δ subbands (see Supporting Information)" | §3.1 | C23-OCCX |
| Longitudinal effective mass | (0.90 ± 0.05) mₑ | "from which we extract a value of (0.90 ± 0.05)mₑ, in agreement with its accepted value." | §3.2 | C23-ML |
| Photon energies | Range 300–1600 eV; k_x–k_z maps at 350–410 eV; Γ dispersions at 380 eV; also ≈820 eV | "k x‐k z Fermi surfaces (hν = 350 – 410 eV, integrated from −50 meV to E F)" / "whereas the triangle data points are taken from the same valley, but at a higher photon energy (≈ 820 eV)" / "Γ band dispersions [...] at hν = 380 eV" | Fig. 3 caption; Fig. 4 caption; §5 | ★ C23-HV |
| Beamline / facility | SX-ARPES endstation, ADRESS beamline, SLS | "The ARPES measurements were performed at the soft X‐ray ARPES facility[54] of the ADRESS beamline[55] at the Swiss Light Source, PSI, Switzerland." | §5 *SX‐ARPES Experiments* | C23-BL |
| Flux; temperature; polarisation | Up to 10¹³ ph/s/(0.01 % BW); 12 K; circular polarisation | "with a photon flux of up to 10¹³ photons / s / (0.01% BW). [...] the experiments were performed at a base temperature of 12 K, using circular polarized light." | §5 | C23-FLUX |
| Energy / angular resolution | 50 meV at 400 eV, 90 meV at ≈700 eV; PHOIBOS-150, 0.1° | "The combined (beamline and analyzer) energy resolution varied from 50 meV at hν = 400 eV, to 90 meV at ≈700 eV. [...] The angular resolution of the ARPES analyzer (PHOIBOS‐150) is 0.1°." | §5 | C23-RES |
| X-ray spot | (10 × 73) µm² | "Our SX‐ARPES experiments feature an X‐ray spot size of (10 × 73) µm², which is comparable to the size of the Hall‐bars" | §1 Introduction | C23-SPOT |
| Electron mean free path | λₑ ≈ 2 nm (SX) vs ≈0.5 nm (VUV) | "give access to a much longer electron mean free path (λe ≈ 2 nm)" / "(λ e ≈ 0.5 nm)" | §1 | C23-IMFP |
| Hall-bar fabrication in this paper | not stated (Hall data only in the SI) | — | — | C23-HB |

---

## 3. Constantinou et al., Nat. Commun. 15, 694 (2024), doi:10.1038/s41467-024-44790-6

### 3a. Sample preparation

| Spec | Value | Verbatim quote | Location | Key |
|---|---|---|---|---|
| Substrate | Sb-doped n-type Si(001), miscut <0.01°, 0.05 Ω cm | "The starting point for both is an Sb-doped, n-type Si(001) substrate, with a miscut <0.01° and a resistivity of 0.05 Ω cm." | Methods, *Sample fabrication* | ★ C24-SUB |
| Outgas and flash | ~12 h at 600 °C; flash 1200 °C for 15 s; prep base <10⁻¹⁰ mbar | "The substrate was loaded into the PEARL preparation chamber, with a nominal base pressure < 10⁻¹⁰ mbar. Sample outgassing was carried out overnight (~12 h) at 600°C by passing a direct current through the sample, followed by flash annealing to 1200°C for 15 s." | Methods, *Sample fabrication* | ★ C24-FLASH |
| H termination (Methods) | **330 °C**; atomic H at 5 × 10⁻⁷ mbar for 5 min; MBE Komponenten source | "the sample is held at a constant temperature of 330°C whilst dosing with atomic hydrogen at 5 × 10⁻⁷ mbar for 5 min, which saturates the Si(001) surface with hydrogen." | Methods, *Sample fabrication* | ★ C24-HTERM |
| H termination (Fig. 5) | **310 °C** printed in the figure. This disagrees with the 330 °C in Methods | "310°C" (figure label, Stage 1 (ii) "Atomic H dose") | Fig. 5, Stage 1 | ★ C24-F5-H |
| Result | Monohydride Si(001)-(2 × 1):H | "This induces the monohydride Si(001)-(2 × 1):H surface, which is again verified with in situ STM and XPS" | Methods | C24-2x1 |
| Pyrometer | IMPAC IGA50-LO-plus, ±30 °C | "The sample temperature was monitored using an infrared pyrometer (IMPAC IGA50-LO-plus), with an estimated uncertainty of ±30°C." | Methods | C24-PYRO |
| Base pressures | Analysis / STM / XPS <5 × 10⁻¹⁰ mbar; prep <10⁻¹⁰ mbar; XIL ~5 × 10⁻⁷ mbar | "In both cases, the measurements were carried out at a base pressure < 5 × 10⁻¹⁰ mbar." / "it currently operates in the high vacuum regime (~5 × 10⁻⁷ mbar)" | Methods *Combined XPS and STM at PEARL*; Results *Towards large-scale…* | C24-PBASE |

### 3b. Irradiation, beamlines, and desorption kinetics

| Spec | Value | Verbatim quote | Location | Key |
|---|---|---|---|---|
| Beamlines | PEARL (bending magnet; XPS + STM); SIM (two APPLE II undulators; XPEEM); XIL proposed | "Non-monochromatic irradiation was performed at the PEARL beamline (featuring a bending magnet) at the Swiss Light Source" / "we have completed measurements of XPEEM at the endstation of the SIM beamline of the SLS." / "Since the SIM beamline utilises two APPLE II type undulators" | Methods; Results | ★ C24-BL |
| Non-monochromatic flux | 3 × 10¹⁴ ph/s (zero order) | "this leads to a non-monochromatic photon flux of 3 × 10¹⁴ ph/s, as measured by the drain current of the refocussing mirror." | Methods, *Non-monochromatic photon irradiation* | C24-NMCF |
| Exposure cycle | 10 min steps up to 140 min; RT and 77 K | "The non-monochromatic irradiations were repeated cyclically in 10 min intervals, with XPS measurements made after every 10 min irradiation, until a total irradiation time of 140 min was reached." | Methods | ★ C24-CYC |
| Monochromatic flux | PEARL ≈10¹² ph/s; SIM ≈10¹⁴ ph/s (E/ΔE > 5000) | "the monochromatic photon flux ≈10¹² ph/s was measured via the drain current of the refocussing mirror. [...] an extremely high monochromatic (E/ΔE > 5000) flux of ≈10¹⁴ ph/s is achieved" | Methods, *Monochromatic photon irradiations* | C24-MCF |
| Photon energies | XPS probe 140 eV; PEARL monochromatic exposure 109 eV; SIM exposures 93 and 106 eV | "a photon energy of 140 eV was used" / "we chose a photon energy of 109 eV, which is 10 eV above the Si 2p core-level" / "we exposed a Si(001):H surface to EUV light at 93 and 106 eV, respectively." | Methods; Results | ★ C24-HV |
| XPS settings | Scienta EW4000; pass energy 10 eV; 0.1 s; 10 meV steps; 5 iterations; θ = 60° | "a photon energy of 140 eV was used, a pass energy of 10 eV, integration time of 0.1 s, with an energy step size of 10 meV, with a total of 5 iterations." / "hν = 140 eV at θ = 60°" | Methods; Fig. 1 caption | C24-XPS |
| STM | Omicron LT-STM at 77 K; imaging −2.5 V, 50 pA | "All STM experiments were performed within an Omicron low-temperature series STM at 77 K." / "Corresponding STM data (−2.5 V, 50 pA)" | Methods; Fig. 1 caption | C24-STM |
| Irradiance definition | Σ_ph = Φ_ph t / A | "Σph=ΦphAt" (PMC rendering of Σ_ph = Φ_ph·t/A) | Methods, Eq. 7 | C24-SIG |
| Fit domain | 0–2.75 × 10²⁰ ph/cm² (0–140 min) | "performed over the domain 0 – 2.75 × 10²⁰ ph/cm² (or 0 – 140 min) using a one-parameter fit" | Fig. 2 caption | C24-DOM |
| Cross-section | σ = (0.7 ± 0.1) × 10⁻²⁰ cm² | "we find that the desorption cross-section is σ = (0.7 ± 0.1) × 10⁻²⁰ cm²." | Results, *Quantifying…* | ★ C24-XS |
| Yield | **Y = (3.7 ± 0.6) × 10⁻⁵ ph⁻¹**. The exponent is −5, not the −6 guessed in the request | "gives an estimate of the desorption yield, Y = (3.7 ± 0.6) × 10⁻⁵ ph⁻¹." | Results, *Quantifying…* | ★ C24-Y |
| Desorption rate | ν_des = (0.015 ± 0.001) ML/min | "the rate constant then becomes the desorption rate, νdes = (0.015 ± 0.001) ML/min." | Results | ★ C24-NU |
| Kinetic model | ρ_Si = 1/(1 + 1/(σΣ_ph)) | "ρSiΣph=11+1σΣph" (PMC rendering) | Results, Eq. 3 | C24-EQ3 |
| STM clean-Si coverage after 100 min | 0.55 ± 0.10 ML (1 ML = 6.78 × 10¹⁴ cm⁻²) | "We quantify the surface density of clean silicon in terms of monolayers (MLs; where 1 ML = 6.78 × 10¹⁴ atoms cm⁻²) [...] and find it to be 0.55 ± 0.10 ML" | Results, *Non-monochromatic irradiation* | C24-055 |
| Dose for 0.95 ML | 12 × 10²⁰ ph/cm² = 18,000 J/cm², i.e. 3 min at 100 W/cm² (13.5 nm) | "to achieve a clean silicon atom density of 0.95 ML, a photon irradiance of 12 × 10²⁰ ph/cm² is needed – equivalent to 18,000 Joules/cm² or a three-minute exposure with an EUV (13.5 nm) intensity of 100 W/cm²." | Results | ★ C24-095 |
| PEARL monochromatic result | 0.05 × 10²⁰ ph cm⁻² (900 min) at 109 eV gives 0.05 ML of dangling bonds | "taken before and after 0.05 × 10²⁰ ph cm⁻² (or 900 min), 109 eV monochromatic photon irradiation. [...] corresponding to a created dangling bond density of 0.05 ML" | Results, *Monochromatic irradiation* | C24-MC |
| Filters | Al 256.6 nm, Zr 247.8 nm, C 243.2 nm (137.8 nm C + 105.4 nm polyimide); bands 17–72, 70–200, 100–280 eV; relative rates 2 %, 16 %, 69 % | "The final reported film thicknesses were: (i) 256.6 nm for Al; (ii) 247.8 nm for Zr; (iii) 243.2 nm for C." / "the Al filter reduces the desorption almost to zero (2% relative to the unfiltered exposure), and the Zr filter also heavily attenuates the desorption (16%). [...] (69% as efficient as unfiltered)." | Methods; Results | C24-FILT |
| Active photon window | 100–210 eV | "the relative ordering of the transmission for photon energies between 100 – 210 eV (Al < Zr < C) matches our experimental hydrogen desorption data" | Results | C24-WIN |
| Intensity scaling | ν_des = A (I_ph/I₀)^¾, with A = 8.5 × 10⁻¹⁷ ML s⁻¹ cm⁻² | "A is a fit constant equal to 8.5 × 10⁻¹⁷ ML s⁻¹ cm⁻². The exponent which is 3/4 in Eq. 5 provides the best description of the data" | Results, Eq. 5 | C24-POW |
| Temperature dependence | None (RT = 77 K) | "showing that the desorption mechanism is temperature-independent" | Results | C24-TIND |

### 3c. XPEEM patterning demonstration and resolution

| Spec | Value | Verbatim quote | Location | Key |
|---|---|---|---|---|
| Exposed stripe | 25 µm vertical band, 157 min | "the exit slit of the X-ray optics was narrowed so that only a 25 μm vertical, rectangular band of the sample surface was irradiated. After 157 min, the exit slit was widened" | Results, *XPEEM imaging…* | ★ C24-STRIPE |
| XPEEM field of view | 50 µm; start voltage −0.8 V | "XPEEM images taken with a start voltage of −0.8 V and 50 μm field-of-view after a (a) 93 eV and (c) 106 eV irradiation for 157 min." | Fig. 4 caption | ★ C24-FOV |
| Measured edge width | FWHM 4.5 µm | "the measured FWHM of the edge being 4.5 μm." | Fig. 4 caption | ★ C24-FWHM |
| Work-function shift | ~0.3 eV measured; expected 0.56 ± 0.14 eV | "the work function increases by ~0.3 eV during the exposure [...] since Δϕ=ϕSi−ϕSiH=0.56±0.14eV" | Results | C24-WF |
| Proposed resolution | IMFP 3.5 nm at ≈6.5 eV, so "a few nanometres" | "For electrons with a kinetic energy ≈6.5 eV, an IMFP of 3.5 nm is found. [...] we expect that a spatial resolution of a few nanometres can be realistically achieved with EUV-based hydrogen desorption lithography." | Results, *Resolution…* | ★ C24-RES |
| Compared e-beam result | 380 nm Gaussian edge width at 40–150 eV | "where incident electrons between 40 – 150 eV yielded a Gaussian width of 380 nm across the desorption edge" | Results | C24-EBL |
| Throughput claim | Minutes per chip with 300 W sources | "the data imply useful exposure times of order minutes for the 300 W sources characteristic of EUV infrastructure." | Abstract | C24-TPUT |

### 3d. Fig. 5 proposed four-stage process flow

| Spec | Value | Verbatim quote | Location | Key |
|---|---|---|---|---|
| Stage 1 | Hydrogen passivation of Si(001): (i) Clean Si(001) at **1200 °C**; (ii) Atomic H dose at **310 °C**; (iii) Si(001):H | Figure headers: "Stage 1: Hydrogen passivation of Si(001)", "(i) Clean Si(001)" + "1200°C", "(ii) Atomic H dose" + "310°C", "(iii) Si(001):H" (figure labels). Caption: "Stage 1: The process begins with preparing a clean silicon surface, followed by the atomic hydrogen passivation of Si(001)." | Fig. 5 (labels and caption) | ★ C24-S1 |
| Stage 2 | EUV patterning of large-scale contacts ("Photolithography") | "Stage 2: EUV patterning of large-scale contacts" (figure label); caption: "Stage 2: EUV hydrogen-desorption lithography of large-scale contacts." | Fig. 5 | ★ C24-S2 |
| Stage 3 | High-resolution patterning of quantum devices: STM lithography (tip label "+4V") **or** EUV lithography, centred on the fiducials | "Stage 3: High-resolution patterning of quantum devices", "STM Lithography Or EUV Lithography", "+4V", "STM tip" (figure labels); caption: "Stage 3: STM or EUV hydrogen-desorption lithography for patterning the nm-scale quantum device at the centre of the fiduciary markers." | Fig. 5 | ★ C24-S3 |
| Stage 4 | Dopant incorporation and Si encapsulation: (i) XH₃ dosing; (ii) Incorporate X at **350 °C**; (iii) Si overgrowth at **250 °C** (printed as a second "(ii)" in the figure); (iv) Final buried device | "Stage 4: Dopant incorporation & Silicon encapsulation", "(i) XH₃ dosing", "(ii) Incorporate X" + "350°C", "(ii) Si overgrowth" + "250°C", "(iv) Final buried device" (figure labels); caption: "Stage 4: Dopant incorporation and silicon encapsulation." | Fig. 5 | ★ C24-S4 |
| Fiducials | Pre-etched e-beam fiducial structures (cross plus 4 square pads in the sketch) | "Pre-etched e-beam fiducial structures" (figure label); text: "a proven method involves the use of pre-etched e-beam fiducial structures on the initial silicon substrate that can withstand the UHV surface preparation" | Fig. 5; Results | ★ C24-FID |
| UHV cluster | Load-lock, transfer chamber, Prep (stages 1 & 4), EUV-Lith (stage 2), STM (stage 3); all <5 × 10⁻¹⁰ mbar | "In-situ UHV processing stages", "Prep. stage 1 & 4", "EUV-Lith stage 2", "STM stage 3", "Transfer chamber", "LL" (figure labels); caption: "Three chambers are branched from the transfer chamber, all of which have a UHV environment with a base pressure < 5 × 10⁻¹⁰ mbar: the preparation, EUV-lithography and STM chamber." | Fig. 5 | ★ C24-CLUSTER |
| After UHV | Ex situ cleanroom vertical contacts | "After this, the sample can be extracted from UHV into ambient and standard cleanroom processing techniques can be used to contact the buried device with vertical electrical connections" | Fig. 5 caption | C24-EXSITU |
| Overgrowth thickness in Fig. 5 | not stated | — | — | C24-S4OG |

---

## 4. Tseng et al., Sci. Adv. 9, eadf5997 (2023), doi:10.1126/sciadv.adf5997

| Spec | Value | Verbatim quote | Location | Key |
|---|---|---|---|---|
| Substrate | p-type Si(100), 100 mm wafer | "A p-type Si(100) wafer is immersed into a buffered HF solution to remove its native oxide layer" / "a clean Si(100) 100 mm wafer" | Results; Materials and Methods | ★ TS-SUB |
| HF treatment | Buffered oxide etch 7:1 (Technic), 5 min; DI rinse <10 s; packed in N₂ | "immersing a clean Si(100) 100 mm wafer into a buffered HF solution (Buffered Oxide Etch 7:1, Technic, France) for 5 min, followed by a quick rinse of deionized (DI) water (<10 s). We then pack the Si wafer in a nitrogen atmosphere before loading it into the EUV chamber." | Materials and Methods | ★ TS-HF |
| Air exposure before load | ~5 min in air; half-hour delay before pump-down | "there is a half-hour delay between the surface preparation and pump down of the lithography tool and, during this time, the samples are packed in a nitrogen-flushed transfer box and exposed to ambient air for about 5 min." | Results | TS-AIR |
| Exposure tool | XIL-II beamline, SLS; ~5 × 10⁻⁷ mbar | "We carry out the EUV exposures at the XIL-II beamline of the SLS with a chamber pressure of ~5 × 10⁻⁷ mbar." | Materials and Methods | ★ TS-TOOL |
| Photon energies | 107.8 eV (11.5 nm), 102 eV (12.15 nm), 91.9 eV (13.5 nm) | "at different photon energies of 107.8 eV (λ = 11.5 nm), 102 eV (λ = 12.15 nm), and 91.9 eV (λ = 13.5 nm)." | Materials and Methods | ★ TS-HV |
| Open-frame aperture | 0.5 mm × 0.5 mm | "The dose tests are done by open-frame exposures with an aperture of 0.5 mm by 0.5 mm" | Materials and Methods | TS-AP |
| Dose-to-pattern | About 2× lower at 107.8 eV than at 91.9 eV | "the Si etch depth reaches the same maximum at the dose-to-pattern value, which is about a factor 2 lower for E = 107.8 eV compared to E = 91.9 eV." | Results | TS-D2P |
| XPS doses | 6.8, 68, 204 J/cm²; expected depths 0, 20, 45 nm | "a low dose of 6.8 J/cm², a medium dose of 68 J/cm², and a high dose of 204 J/cm². From Fig. 2C, we expect that the low dose should correspond to no measured etched depth, the medium dose to a depth of 20 nm, and the high dose to a depth of 45 nm." | Results | ★ TS-DOSE |
| Suboxide / SiO₂ crossover | 68 J/cm² | "At a dose below 68 J/cm², the formation of suboxides dominates, whereas the growth of SiO₂ prevails at higher doses." | Introduction | TS-68 |
| Maximum etch depth | ~50 nm | "it is a notable observation that it is possible to etch 50 nm into Si simply by a surface modification." | Results | TS-50 |
| Oxide thickness | ≲1 nm (5 s TMAH removes it vs 60 s for native oxide; at 150 J/cm²) | "Fully removing the native oxide by etching in TMAH required approximately 60 s, while fully removing the EUV-induced oxide required only 5 s (for an exposure dose of 150 J/cm²). Therefore, it is reasonable to infer that the thickness of grown oxide is a nanometer or below." | Results | ★ TS-OXT |
| TMAH solutions (dose tests) | 25 wt %; 10 wt %; 10 wt % + 30 vol % IPA; 85 °C, 5 s | "25 wt % TMAH (VLSI grade, Technic, France), 10 wt % TMAH, and 10 wt % TMAH + 30 vol % IPA (ULSI grade, Technic, France) at 85°C for 5 s, followed by a quick DI water rinse and N₂ blow-drying." | Materials and Methods | ★ TS-TMAH |
| Etch-depth metrology | Dektak 150 profilometer | "We then measure the obtained etched Si depth with a profilometer (Veeco, Dektak 150)" | Materials and Methods | TS-DEKTAK |
| ATL optics | Transmission grating on SiNₓ membrane; 2× demagnification; 4 % bandwidth; 300 nm mask pitch gives 150 nm wafer pitch | "passes through a transmission diffraction grating, fabricated on a thin silicon nitride membrane and placed at a certain distance from the exposed wafer, where a stationary aerial image is formed with 2× demagnification. The stationary intensity is due to the 4% bandwidth of the light [...] The mask used in these experiments consists of a linear grating with a pitch of 300 nm, which corresponds to half-pitch 75-nm lines on the wafer." / "The resulting aerial image recorded on the substrate has a pitch of 150 nm" | Results, *High-resolution…*; Methods | ★ TS-ATL |
| Mask–wafer gap | not stated ("a certain distance") | — | Results | TS-GAP |
| Membrane transmission | 42 % | "only 42% of the light is transmitted through the silicon nitride membrane." | Results | TS-T42 |
| Fig. 7A schematic labels | Synchrotron EUV light; Si frame; Si₃N₄ membrane; Grating; Talbot self-image; Stationary intensity; HF-treated Si substrate | "Synchrotron EUV light", "Si", "SiₓNᵧ", "Grating", "Talbot self-image", "Stationary intensity", "HF-treated Si substrate" (figure labels) | Fig. 7A | TS-F7A |
| Best result | 75 nm half-pitch, 31.2 nm height; ~33 J/cm² on mask; 10 wt % TMAH + 30 vol % IPA, 85 °C, 5 s | "75-nm half-pitch SiO₂/Si lines obtained from the EUV ATL exposure with a dose on the mask of roughly 33 J/cm² after etching in a 10 wt % TMAH + 30 vol % IPA solution at 85°C for 5 s. The corresponding atomic force microscopy (AFM) measurements in Fig. 7E indicate that the average height of the etched SiO₂/Si lines is 31.2 nm." | Results | ★ TS-BEST |
| Abstract headline | 75 nm half-pitch, 31 nm height | "We achieve silicon dioxide/silicon gratings with 75-nanometer half-pitch and 31-nanometer height" | Abstract | ★ TS-ABS |
| 75 °C variant | ~28 J/cm² gives 15.8 nm | "75-nm SiO₂/Si lines etched at 75°C for 5 s after exposure at a dose of about 28 J/cm². In this case, the average height of the SiO₂/Si lines is reduced to 15.8 nm." | Results | TS-75C |
| 65 °C variant | 10 J/cm² gives 11.2 nm | "We could further reduce the dose to 10 J/cm² by lowering the etching temperature even further, down to 65°C [...] this also further reduced the average etch depth to 11.2 nm." | Results | TS-65C |
| Imaging | SEM Zeiss Supra 55 VP; AFM Bruker Dimension 3100 | "obtained by SEM (Zeiss Supra 55 VP) and AFM (Bruker Dimension 3100) imaging" | Materials and Methods | TS-IMG |
| XPS | PEARL; survey 990 eV; Si 2p at 150 eV; 30° incidence; spot 190 × 70 µm; pass energy 10 eV | "We carry out the survey scans with an incident photon energy of 990 eV, an incidence angle of 30°, and a beam spot size of 190 μm by 70 μm. [...] we use a photon energy of 150 eV and an incidence angle of 30° to measure the Si 2p spectra with a pass energy of 10 eV." | Materials and Methods | TS-XPS |
| Mechanism | Secondary-electron-assisted water dissociation leads to oxide growth (not H desorption) | "The generation of secondary electrons due to the EUV absorption plays a key role in the dissociation of absorbed water, which promotes the formation of silicon oxide." | Results | TS-MECH |

---

## Discrepancies and corrections to the request's guesses

1. **Constantinou 2024, H-termination temperature.** Methods say **330 °C**; Fig. 5 prints **310 °C**. Use 330 °C for the actual experiment and 310 °C only to redraw Fig. 5 as published.
2. **Constantinou 2024, yield.** Y = (3.7 ± 0.6) × 10⁻**⁵** ph⁻¹, not 10⁻⁶. The paper gives the unit as ph⁻¹, not "H/ph".
3. **Constantinou 2024, photon energies.** Exposures were at 93 and 106 eV (SIM, XPEEM) and 109 eV (PEARL monochromatic). XPS was probed at 140 eV. The paper also cites 13.5 nm as "~92 eV".
4. **Constantinou 2024, Fig. 5 labels.** Stage 4 shows two steps labelled "(ii)": Incorporate X at 350 °C, and Si overgrowth at 250 °C.
5. **Lock layer differs between papers.** D'Anna 2023: 2 nm at RT, RTA 500 °C 15 s, then 28 nm at 250 °C (30 nm total), at 0.003 nm s⁻¹. Constantinou 2023: first 1.3 nm at RT, same RTA, rest at 250 °C (2 or 3 nm total), at 1 ML/min.
6. **Constantinou 2023, δz.** The text gives As 5.4 ± 0.1 Å and P 9.7 ± 4.1 Å. Table 1 gives per-sample values: As 0.45 / 0.62 nm, P 0.91 / 1.03 nm (2 / 3 nm caps). Use Table 1 for per-sample diagrams.
7. **D'Anna 2023, missing details.** Contact Al thickness, deposition method and anneal, etch depth, contact-hole geometry, pad size, alignment markers, EBL and mobility are **not stated** in the paper or captions. Contacts cite a thesis, ref. [47] (Fuechsle, UNSW 2011).
