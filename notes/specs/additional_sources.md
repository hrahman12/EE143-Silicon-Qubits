# Additional sources (beyond REFERENCES.md)

Compiled 2026-11-21. Author lists for papers 1, 3, 4, 6, 7, 8 and 15 were checked against Crossref. Every DOI was checked against Crossref (`api.crossref.org/works/<DOI>`) for title, first author, year, journal, volume and pages. Licences come from (a) the `<license>` element in the PMC article XML, (b) Europe PMC's `license` field, or (c) the publisher-deposited Crossref `license` URL for the version of record (`content-version: vor`), as noted for each paper. Licences were not taken from memory.

Each quote is verbatim from the source named in its "Location" column. Where only a preprint or the abstract could be read (publisher sites returned HTTP 403), the table says so. Check the wording against the version of record before putting it on a slide.

Raw downloads (CC BY + in PMC only) are in `figures/raw/<Key>/`: Kiczynski2022, Reiner2024, Achal2018, Cowie2024, Siegl2025, Leeuwenhoek2020. Each folder holds the figure JPGs, PMC XML, TXT, JSON and PDF (every PDF is under 20 MB).

Suggested credit line: "Reproduced from <Author> et al., <Journal> <vol>, <page> (<year>), CC BY 4.0."

---

## Ranked shortlist

| Rank | Key | Why it's useful for the deck | Licence | Figures on disk? |
|---|---|---|---|---|
| 1 | Kiczynski2022 | Full STM-device recipe in one paragraph, plus an STM image of a 10-dot, 6-gate device | CC BY 4.0 | Yes |
| 2 | DAnna2026 | New 2026 Curson-group metrology: X-ray reflectometry shows As δ-layers are chemically under 1 nm thick, where SIMS gives more than 2 nm | CC BY 4.0 | No (accelerated preview, figures not in HTML yet) |
| 3 | Reiner2024 | STM-patterned 3P registers in ²⁸Si. Table 1 compares Si:P (±0.384 nm placement, 100% activation) with NV centres | CC BY 4.0 | Yes |
| 4 | Jakob2022 | Ion-implantation comparison: 99.85% single-ion detection confidence, 98.1% yield limit | CC BY-NC-ND 4.0 (link or redraw only) | No |
| 5 | Namboodiri2024 | Contacting buried devices: KPFM multi-scale alignment, "95% yield on more than 150 devices" | CC BY 4.0 | No (not in PMC) |
| 6 | Ivie2021 | Kinetic model: hot dosing (75–150 °C) could make single-P incorporation near-deterministic | CC BY 4.0 | No (not in PMC) |
| 7 | Achal2018 | H-lithography recipe (20 ms pulses at 1.8–3.0 V) plus atom-by-atom error correction (repassivation) | CC BY 4.0 | Yes |
| 8 | Masteghin2024 | Curson backup paper: XRF reaches hundreds of atoms (650 detected, 3000 in a 1 s shot) | CC BY 4.0 | No (not in PMC) |
| 9 | Lundgren2023b | Curson group: BiCl₃ as the first STM-compatible Bi precursor | CC BY 4.0 | No (not in PMC) |
| 10 | Chapman2022 | Curson group: Si:P δ-layer microwave transmission lines (4–26 GHz) | CC BY 4.0 | No (not in PMC) |
| 11 | Katzenmeyer2021 | Scaling: UV-laser photothermal H-depassivation replaces STM lithography | CC BY 4.0 | No |
| 12 | Anderson2020 | Low-thermal-budget Al₂O₃ top gate over a buried SET | CC BY 4.0 | No |
| 13 | Siegl2025 | Curson backup paper: STM wavefunction imaging of acceptors, gives an H-termination recipe | CC BY 4.0 | Yes |
| 14 | Cowie2024 | Curson backup paper: single-trap noise at Si/SiO₂ (interface noise near qubits) | CC BY 4.0 | Yes |
| 15 | Leeuwenhoek2020 | MEMS/microfabricated on-chip double-tip STM probes (multi-tip scaling, EE143 process flow) | CC BY 4.0 | Yes |

---

## 1. Kiczynski2022

- **Citation:** M. Kiczynski, S. K. Gorman, H. Geng, M. B. Donnelly, Y. Chung, Y. He, J. G. Keizer, M. Y. Simmons, "Engineering topological states in atom-based semiconductor quantum dots," *Nature* **606**, 694–699 (2022).
- **DOI:** 10.1038/s41586-022-04706-0
- **Licence:** CC BY 4.0, verified from the PMC XML `<license xlink:href="https://creativecommons.org/licenses/by/4.0/">`, and Europe PMC "cc by".
- **Open copy:** PMC9217742. Files are in `figures/raw/Kiczynski2022/`.
- **Figures:**
  - Fig. 1 (`41586_2022_4706_Fig1_HTML.jpg`): the SSH model, and (e, f) STM images of the two 10-dot arrays with the open hydrogen mask outlined.
  - Fig. 2 (`..._Fig2_HTML.jpg`): (a) "An STM micrograph of device I, which shows the six control gates, labelled G1 to G6". Good for showing what a finished STM pattern looks like.
  - Extended Data Fig. 1 (`..._Fig4_ESM.jpg`): measurement wiring, with an STM image of the device.

| Spec | Verbatim quote | Location |
|---|---|---|
| Surface prep | "The substrate was prepared via a series of high-temperature anneals, up to 1,100 °C, followed by a controlled cooling to 330 °C, resulting in a (2 × 1) reconstructed surface." | Methods |
| Dose + incorporation | "After STM lithography, the substrate was exposed to a phosphine (PH3) precursor gas, in which phosphorus was absorbed and incorporated, at 350 °C, into the exposed areas." | Methods |
| Encapsulation | "The device was then encapsulated with 40 nm of natural silicon using molecular beam epitaxy at a rate of about 0.125 nm min−1." | Methods |
| Dot size | "We therefore fabricate quantum dots with an area of about 25 nm2 (about 25 phosphorus donors per site35)." | Main text |
| Spacing → coupling | "The small separation of ≤10 nm also allows us to achieve large tunnel couplings t ≈ 1–10 meV for these quantum dot sizes35." | Main text |
| Complexity | "for 10 quantum dots, we require precision control across 110 different experimental parameters related to U, V, t and ϵ." | Main text |

## 2. DAnna2026 (Curson group, newest result)

- **Citation:** N. D'Anna, J. Bragg, E. Skoropata, N. Ortiz Hernández, A. G. McConnell, M. Clémence, H. Ueda, P. C. Constantinou, K. Spruce, T. J. Z. Stock, S. Fearn, S. R. Schofield, N. J. Curson, D. Ferreira Sanchez, D. Grolimund, U. Staub, G. Matmon, S. Gerber, G. Aeppli, "Element-specific, non-destructive profiling of two-dimensional dopant layers in silicon," *npj Quantum Information* (published online 11 Nov 2026; accelerated article preview, no volume or pages yet).
- **DOI:** 10.1038/s41534-026-01393-x
- **Licence:** CC BY 4.0, verified from the Crossref licence (`creativecommons.org/licenses/by/4.0`) and the article page's rights statement ("licensed under a Creative Commons Attribution 4.0 International License"). The arXiv preprint (2410.00241v2, titled "…profiling of layered heterostructures") is **CC BY-NC-ND**, so take figures from the version of record, not arXiv.
- **Open URL:** https://www.nature.com/articles/s41534-026-01393-x. It is not in PMC, and the accelerated preview has no figure files yet. Re-pull the figures once the final version of record posts.
- **Figures (numbering from arXiv v2, confirm against the VoR):**
  - Fig. 1: schematic of the X-ray reflectometry geometry and the layer stack (SiO₂ / Si cap / As δ-layer).
  - Fig. 3: the resonant reflectometry edge at the As L₃ edge, 1324 eV.
  - Fig. 4: δ-layer thickness and depth from resonant-contrast X-ray reflectometry (RCXR) against SIMS.

| Spec | Verbatim quote | Location |
|---|---|---|
| Headline | "δ-layers acting as quantum wells with widths down to 0.5 nm inferred from magneto-transport and angle-resolved photoemission" | Published abstract |
| SIMS limit | "considerably smaller than the resolution-limited chemical thickness of 2 nm from the standard measurement technique, namely secondary-ion mass spectroscopy" | Published abstract |
| Result | "demonstrate that the sub-nm electronic thickness of the δ-layers corresponds to sub-nm chemical thickness." | Published abstract |
| Measured δ | "yielding a thickness of δ=0.6 (+0.7/−0.2) (0.4−1.3) nm and depth of d=18.4±0.1 nm" (sample #1) | arXiv v2, Results |
| Recipe | "Each sample was dosed with AsH3, to the saturation As density of (1.6±0.3)×10^14 cm-2 [5], and heated to 350 ∘C for 1−2 min … a 1−4 nm silicon 'locking layer' was deposited, without resistive sample heating … Three of the samples were then heated to 500 ∘C for 15 s … More silicon (14−71 nm depending on sample) was deposited, with the sample at 250 ∘C. Silicon was deposited at a rate of 0.1−0.4 nm/min" | arXiv v2, Methods |
| X-ray energy | "the arsenic L3-absorption edge at 1324 eV"; data taken at "1300 eV" and "1335 eV" | arXiv v2, Results |

## 3. Reiner2024

- **Citation:** J. Reiner, Y. Chung, S. H. Misha, C. Lehner, C. Moehle, D. Poulos, S. Monir, K. J. Charde, P. Macha, L. Kranz, I. Thorvaldson, B. Thorgrimsson, D. Keith, Y. L. Hsueh, R. Rahman, S. K. Gorman, J. G. Keizer, M. Y. Simmons, "High-fidelity initialization and control of electron and nuclear spins in a four-qubit register," *Nat. Nanotechnol.* **19**, 605–611 (2024).
- **DOI:** 10.1038/s41565-023-01596-9
- **Licence:** CC BY 4.0, verified from the PMC XML `<license>` and Crossref (vor).
- **Open copy:** PMC11106007. Files are in `figures/raw/Reiner2024/`.
- **Figures:**
  - Fig. 1 (`41565_2023_1596_Fig1_HTML.jpg`): (a) register schematic, (c) STM image of two four-qubit registers, (d) lithographic patches with the predicted donor sites.
  - Fig. 5: Rabi oscillations, Ramsey decay and randomized benchmarking.
  - Table 1 (text): Si:P against NV centres. Redraw it as a native table.

| Spec | Verbatim quote | Location |
|---|---|---|
| Placement | "Fabrication accuracy ±0.384 nm (ref. 43)" (Si:P) against "±5 nm (ref. 26)" (C:NV) | Table 1 |
| Activation | "Dopant activation 100% (ref. 43)" (Si:P) against "2.5% (ref. 44)" (NV) | Table 1 |
| Device | "The device consists of two small quantum dot registers, each defined by three phosphorus atoms (3P) … weakly tunnel-coupled to a single-electron transistor patterned ~17 nm away" | Main text |
| Fab | "the bright regions correspond to regions in which the hydrogen mask has been selectively removed to allow incorporation of phosphorus donors via phosphine dosing" | Main text, Fig. 1c |
| Fidelity | "we demonstrated coherent control of the electron spin qubit with T2*=12μs and gate fidelities FG = 99.78 ± 0.07% using randomized benchmarking" | Conclusion |
| Init | "high-fidelity (F=100−6+0%) initialization of all the nuclear spins within a four-qubit nuclear spin register" | Abstract |

## 4. Jakob2022 (single-ion implantation comparison)

- **Citation:** A. M. Jakob, S. G. Robson, V. Schmitt, V. Mourik, M. Posselt, D. Spemann, B. C. Johnson, H. R. Firgau, E. Mayes, J. C. McCallum, A. Morello, D. N. Jamieson, "Deterministic Shallow Dopant Implantation in Silicon with Detection Confidence Upper-Bound to 99.85% by Ion–Solid Interactions," *Adv. Mater.* **34**, 2103235 (2022).
- **DOI:** 10.1002/adma.202103235
- **Licence:** **CC BY-NC-ND 4.0**, verified from Europe PMC "cc by-nc-nd". Do not crop or modify its figures. Link to it, or redraw as "Schematic after Jakob2022". The text was read from PMC11468509 (not saved to raw/).
- **Figures (for redraw):** Fig. 1 and Fig. 2 show the AFM-nanostencil implanter with on-chip p–i–n detector electrodes.

| Spec | Verbatim quote | Location |
|---|---|---|
| Detector | "an on‐chip detector electrode system with 70 eV root‐mean‐square noise (≈20 electrons) is employed to demonstrate near‐room‐temperature implantation of single 14 keV 31P+ ions" | Abstract |
| Confidence | "an unprecedented upper‐bound single‐ion‐detection confidence of 99.85 ± 0.02% for near‐surface implants" | Abstract |
| Yield | "For a device with 6 nm gate oxide and 14 keV 31P+ implants, a yield limit of 98.1% is demonstrated." | Abstract |
| Depth/energy | "placing them about ≈7–20 nm beneath the gate oxide interface … the kinetic ion implantation energy lies in the range of ≈8–35 keV." | Introduction |
| Conventional | "This limits the single‐ion‐detection confidence with conventional secondary electron detectors to ≈90%." | Introduction |

Contrast for the slide: STM placement is ±1 lattice site (REFERENCES.md, Schofield2025 §5.4), while implanted ions scatter randomly ("straggling"). The 98.1% figure is a yield limit set by the gate oxide, a different quantity from Stock2024's 97 ± 2% single-atom incorporation yield, so label the two clearly.

## 5. Namboodiri2024 (contacting buried devices)

- **Citation:** P. Namboodiri et al., "Multi-scale alignment to buried atom-scale devices using Kelvin probe force microscopy," *Nanotechnology Reviews* **13**, 20230196 (2024).
- **DOI:** 10.1515/ntrev-2023-0196
- **Licence:** CC BY 4.0, verified from the Crossref licence URL `creativecommons.org/licenses/by/4.0`. OpenAlex lists it as gold OA, cc-by.
- **Open URL:** https://www.degruyterbrill.com/document/doi/10.1515/ntrev-2023-0196/html. Not in PMC, and the publisher blocked automated download, so figure numbers still need checking by hand.
- **Figures to look for:** the KPFM image of the buried pattern registered to fiducials, and the EBL contact-lead overlay.

| Spec | Verbatim quote | Location |
|---|---|---|
| Process scope | "We have developed atomic precision lithography, dopant incorporation, device encapsulation, ex situ device re-location, and contact processes to enable high-yield device fabrication." | Abstract |
| Method | "a multiscale alignment strategy using Kelvin probe force microscopy to enable the alignment of buried device components to electronic support structures such as source/drain leads, in-plane and top gates, and waveguides" | Abstract |
| Scale bridge | "bridging the gap from nanometer STM patterns to the millimeter-scale electrical contact fabrication with a 95% yield on more than 150 devices fabricated to date." | Abstract |
| Steps | "a multi-step alignment process at various stages of fabrication, including atom-scale device fabrication using STM, re-location and registration, and electron beam lithography for contact leads and pads." | Abstract |

## 6. Ivie2021 (evaluated)

- **Citation:** J. A. Ivie, Q. Campbell, J. C. Koepke, M. I. Brickson, P. A. Schultz, R. P. Muller, A. M. Mounce, D. R. Ward, M. S. Carroll, E. Bussmann, A. D. Baczewski, S. Misra, "Impact of Incorporation Kinetics on Device Fabrication with Atomic Precision," *Phys. Rev. Applied* **16**, 054037 (2021).
- **DOI:** 10.1103/PhysRevApplied.16.054037
- **Licence:** CC BY 4.0, verified from Crossref (vor). APS blocked automated download.
- **Open copy:** arXiv:2105.12074, titled "The impact of stochastic incorporation on atomic-precision Si:P arrays". The quotes below come from this preprint.
- **Figures (preprint numbering):**
  - FIG. 1: "Example STM lithography array. (a) STM image of 25 patterned windows".
  - FIG. 3: KMC incorporation model against experiment, with the PH₃ → PH₂ → … → P reaction pathway.
  - FIG. 4: "The simulated probability of incorporation as a function of both dose time and pressure", with constant-exposure lines in Langmuirs. This map is the best figure for a "how to beat 63%" slide.

| Spec | Verbatim quote | Location |
|---|---|---|
| Yield (already in pack) | "the likelihood of incorporating into an ideally written three-dimer single- donor window is 63 ± 10% for room-temperature dosing" | Abstract |
| Scaling penalty | "Even with perfect lithography and processing the probability of successfully fabricating a ∼50-donor array for analog quantum simulation is ∼10 −10 ." | Main text |
| Model check | "we predict P I (n = 1|w = 3) = 59% ± 2% compared to the measured value of 63% ± 10%." | Results |
| Hot dosing | "At temperatures as low as 75 °C, near-deterministic incorporation is possible within a more typical range of pressures and tempera- tures, with conditions of 3 × 10 −10 Torr for 6000 s (∼1.6 hours), P I (n = 1|w = 3) = 98…" (the number after 98 was cut off in the extracted text, so check the PDF) | Results |
| 150 °C | "all ex- posures > 1 L producing deterministic incorporation at 150 °C." | Results |

## 7. Achal2018 (H-depassivation lithography + error correction)

- **Citation:** R. Achal, M. Rashidi, J. Croshaw, D. Churchill, M. Taucer, T. Huff, M. Cloutier, J. Pitters, R. A. Wolkow, "Lithography for robust and editable atomic-scale silicon devices and memories," *Nat. Commun.* **9**, 2778 (2018).
- **DOI:** 10.1038/s41467-018-05171-y
- **Licence:** CC BY 4.0, verified from the PMC XML `<license>`, Europe PMC "cc by" and Crossref.
- **Open copy:** PMC6056515. Files are in `figures/raw/Achal2018/`.
- **Figures:**
  - Fig. 1: STM of the H–Si(100)-2×1 lattice with site spacings.
  - Fig. 2 (`41467_2018_5171_Fig2_HTML.jpg`): fabrication of a dangling-bond structure, then correction by hydrogen repassivation. This is the best "write–inspect–fix" visual.
  - Fig. 4: 8-bit and 192-bit rewritable atomic memories.

| Spec | Verbatim quote | Location |
|---|---|---|
| Pulse recipe | "the tip is brought over each lattice site of the pattern and 20 ms voltage pulses between 1.8 and 3.0 V are applied at a fixed tip-height (V = 1.4 V, I = 50 pA) until the successful removal of hydrogen has been detected." | Results |
| Detection rule | "If the measured current is 60% larger than the reference value, it is deemed a successful hydrogen removal event." | Methods |
| Imaging | "(V = 1.4 V, I = 50 pA, T = 4.5 K, 2 × 3 nm2)" | Fig. 1 caption |
| Density | "bit density of 1.70 bits per nm2" | Fig. 4 caption / text |
| Editing | "It can be initiated at the press of a button and repeated until a successful repassivation signature is observed." | Results |

## 8. Masteghin2024 (Curson backup paper, evaluated)

- **Citation:** M. G. Masteghin, T. Gervais, S. K. Clowes, D. C. Cox, V. Zelyk, A. Pattammattel, Y. S. Chu, N. Kolev, T. Z. Stock, N. Curson, P. G. Evans, M. Stuckelberger, B. N. Murdin, "Benchmarking of X-Ray Fluorescence Microscopy with Ion Beam Implanted Samples Showing Detection Sensitivity of Hundreds of Atoms," *Small Methods* 2301610 (2024).
  - Crossref lists the article number 2301610 and date 2024-05, but no volume. Get the volume from the Wiley page.
- **DOI:** 10.1002/smtd.202301610
- **Licence:** CC BY 4.0, verified from Crossref (vor and am) and Europe PMC "cc by". It has no PMCID.
- **Open copy:** arXiv:2310.03409, titled "Detection Sensitivity Limit of Hundreds of Atoms with X-Ray Fluorescence Microscopy". The quotes below come from this preprint. Wiley blocked automated download.
- **Figures (preprint numbering):**
  - Fig. 1: SEM with Cr markers, and KPFM of the Ga implant patterns.
  - Fig. 4: count histograms against Ga density, showing Poisson statistics.
  - Fig. 5: the integrated line signal, down to 650 atoms.

| Spec | Verbatim quote | Location |
|---|---|---|
| Single shot | "with a single shot detection of 1 second integration time, the sensitivity of the XRF would be sufficient to find amongst background a single isolated inclusion of unknown location comprising only 3000 Ga impurities (a mass of just 350 zg)" | Abstract |
| Best | "With increased integration we were able to detect 650 impurities." | Abstract |
| Beam | "a monochromatic beam with an energy of 13.5 keV (above the Ga K-edge)"; focus "FWHM … 13.9 × 12.3 nm2" by ptychography | §II.2 |
| Implant | "singly charged gallium ions (Ga+) with an energy of 30 keV were implanted using a dual beam Focused Ion Beam" | §II.1 |
| Outlook | "would then allow single atom detection N=1 with an integration time of just T=2 s (still background limited)" | §IV |

## 9. Lundgren2023b (Curson group, Bi precursor)

- **Citation:** E. A. S. Lundgren et al., "Bismuth trichloride as a molecular precursor for silicon doping," *Appl. Phys. Lett.* **122**, 151601 (2023).
- **DOI:** 10.1063/5.0145772
- **Licence:** CC BY 4.0, verified from Crossref (vor). Not in PMC.
- **Open URL:** https://doi.org/10.1063/5.0145772. AIP blocked automated download, so the quotes come from the abstract only and figure numbers need checking by hand.
- **Figure to look for:** atomic-resolution STM of BiCl₃-dosed Si(001) next to DFT structures.
- **Pairing:** pairs with the pack's Lundgren2023 (triphenyl bismuth, JPCC).

| Spec | Verbatim quote | Location |
|---|---|---|
| Precursor family | "Examples include phosphine (PH3), arsine (AsH3), and diborane (B2H6) for the incorporation of phosphorus, arsenic, and boron, respectively." | Abstract |
| Gap | "there is currently no known precursor for the incorporation of bismuth that is compatible with this STM-based lithographic method." | Abstract |
| Result | "at room temperature, BiCl3 completely dissociates to produce bismuth ad-atoms, ad-dimers, and surface-bound chlorine" | Abstract |

## 10. Chapman2022 (Curson group, δ-layer microwave lines)

- **Citation:** G. Chapman et al., "Microwave Properties of 2D CMOS Compatible Co-Planar Waveguides Made from Phosphorus Dopant Monolayers in Silicon," *Adv. Electron. Mater.* **8**, 2100989 (2022).
- **DOI:** 10.1002/aelm.202100989
- **Licence:** CC BY 4.0, verified from Crossref (vor). Not in PMC.
- **Open URL:** https://doi.org/10.1002/aelm.202100989. Wiley blocked automated download, so the quotes come from the abstract only and figure numbers need checking by hand.

| Spec | Verbatim quote | Location |
|---|---|---|
| Method | "the characteristics of transmission lines made from silicon doped with phosphorus are investigated using phosphine monolayer doping." | Abstract |
| Range | "S‐parameter measurements are performed between 4–26 GHz from room temperature down to 4.5 K." | Abstract |
| Numbers | "At 20 GHz, the measured monolayer transmission line characteristics consist of an attenuation constant of 40 dB mm−1 and a characteristic impedance of 600 Ω." | Abstract |

## 11. Katzenmeyer2021 (scaling: photothermal patterning)

- **Citation:** A. M. Katzenmeyer et al., "Photothermal alternative to device fabrication using atomic precision advanced manufacturing techniques," *J. Micro/Nanopatterning, Materials, and Metrology* **20**(1), 014901 (2021).
- **DOI:** 10.1117/1.JMM.20.1.014901
- **Licence:** CC BY 4.0, verified from Crossref (vor). Not in PMC. Quotes come from the abstract.

| Spec | Verbatim quote | Location |
|---|---|---|
| Swap | "an APAM device workflow where scanned probe lithography of the atomic layer resist has been replaced by photolithography." | Abstract |
| Mechanism | "An ultraviolet laser is shown to locally and controllably heat silicon above the temperature required for hydrogen depassivation on a nanosecond timescale" | Abstract |
| Device | "A phosphorus-doped van der Pauw structure … is found to have a similar mobility and higher carrier density compared with devices patterned by STM." | Abstract |

This sits beside Constantinou2024 (EUV) as a second optical route to resist-free patterning.

## 12. Anderson2020 (gate stack on buried devices)

- **Citation:** E. M. Anderson et al., "Low thermal budget high-k/metal surface gate for buried donor-based devices," *J. Phys.: Mater.* **3**, 035002 (2020).
- **DOI:** 10.1088/2515-7639/ab953b
- **Licence:** CC BY 4.0, verified from Crossref (vor). The arXiv copy is 2002.09075. Quotes come from the abstract.

| Spec | Verbatim quote | Location |
|---|---|---|
| Trade-off | "There exists a tradeoff between low thermal budget (LT) processes to limit dopant diffusion and high thermal budget (HT) processes to grow defect-free layers of epitaxial Si and gate oxide." | Abstract |
| Stack | "an LT epitaxial Si cap and LT deposited Al 2 O 3 gate oxide integrated with an atomically precise single-electron transistor (SET)" | Abstract |
| Limit | "the gate's leverage over the SET is limited by defects in the layers above the SET" | Abstract |

## 13. Siegl2025 (Curson backup paper, evaluated)

- **Citation:** M. Siegl et al., "Imaging the Acceptor Wave Function Anisotropy in Silicon," *Nano Lett.* **25**(38), 13996–14001 (2025).
- **DOI:** 10.1021/acs.nanolett.5c02675
- **Licence:** CC BY 4.0, verified from the PMC XML ("This article is licensed under CC-BY 4.0"), Europe PMC and Crossref.
- **Open copy:** PMC12464996. Files are in `figures/raw/Siegl2025/`.
- **Figures:**
  - Fig. 1 (`nl5c02675_0001.jpg`): filled- and empty-state STM of six subsurface acceptors.
  - Fig. 3: STM against effective-mass and tight-binding calculations.
- **Use:** a backup slide on imaging single buried dopants. It also gives a concrete H-termination recipe.

| Spec | Verbatim quote | Location |
|---|---|---|
| Prep | "annealed at 500 °C overnight under ultrahigh vacuum (<2 × 10–10 mbar), followed by a 10 s flash anneal at 1150 °C by direct current heating" | Methods |
| H-termination | "passivated with hydrogen by being exposed to an atomic hydrogen beam (chamber background 5 × 10–7 mbar for 5 min), while the sample was maintained at 340 °C." | Methods |
| Imaging | "STM images were taken at 77 K." / "Detailed analysis of 75 individual acceptors" | Methods / Results |

## 14. Cowie2024 (Curson backup paper, evaluated)

- **Citation:** M. Cowie et al., "Spatially resolved random telegraph fluctuations of a single trap at the Si/SiO₂ interface," *PNAS* **121**(44), e2404456121 (2024).
- **DOI:** 10.1073/pnas.2404456121
- **Licence:** CC BY 4.0, verified from the PMC XML ("Creative Commons Attribution License 4.0 (CC BY)") and Crossref.
- **Open copy:** PMC11536084. Files are in `figures/raw/Cowie2024/`.
- **Figures:**
  - Fig. 1 (`pnas.2404456121fig01.jpg`): fm-AFM maps of individual traps.
  - Fig. 3: telegraph-noise time trace.
  - Fig. 5: ensemble 1/f spectrum.
- **Use:** backup slide only, on why interfaces near qubits matter. It is not a fabrication paper.

| Spec | Verbatim quote | Location |
|---|---|---|
| Conditions | "using frequency-modulated atomic force microscopy (fm-AFM) (13, 14) at room temperature in ultrahigh vacuum (∼10−10 mbar)" | Introduction |
| Gap | "an insulating gap composed of vacuum (∼10 nm) and SiO2 (1nm)" | Results |
| Timescales | "ranging from static (0Hz, Ta) to slow (∼Hz, Tb) to fast (∼kHz, Tc)" | Results |
| Link to qubits | "challenges the scaling of emerging spin-based quantum sensors and computers" | Significance |

## 15. Leeuwenhoek2020 (MEMS / multi-tip)

- **Citation:** M. Leeuwenhoek, F. Groenewoud, K. van Oosten, T. Benschop, M. Allan, S. Gröblacher, "Fabrication of on-chip probes for double-tip scanning tunneling microscopy," *Microsyst. Nanoeng.* **6**, 99 (2020).
- **DOI:** 10.1038/s41378-020-00209-y
- **Licence:** CC BY 4.0, verified from the PMC XML `<license>` and Europe PMC.
- **Open copy:** PMC8433193. Files are in `figures/raw/Leeuwenhoek2020/`.
- **Figures:**
  - Fig. 1: coloured SEM of the double tips. The caption gives a "~35 nm" gap between tips.
  - Fig. 2: the EBL → SiN etch → Si etch → Au process flow. This makes a good EE143 tie-in.
- **Caveat:** this is for multi-probe measurement, not parallel lithography. Use it only to show that STM tips can be microfabricated. The pack's Schofield2025 §2.2 already covers "10⁷ MEMS tips".

---

## Evaluated and not recommended for figure reuse

| Paper | Licence (verified) | Verdict |
|---|---|---|
| Usman2016, Nat. Nanotechnol. 11, 763 (10.1038/nnano.2016.83) | Crossref gives only a Springer TDM licence, and Europe PMC has no licence. Not CC. | Redraw only. Cite for "exact lattice-site metrology". |
| Cowie2024b, PRL 132, 256202 (10.1103/PhysRevLett.132.256202) | Crossref: APS default licence (not CC) | Cite only. No figure reuse. |
| Banerjee2025, Appl. Phys. Rev. 12, 041328 (10.1063/5.0294020) | Crossref: CC BY-NC-ND 4.0 | Cite or link. Don't modify figures. |
| Gramse2020, Nat. Electron. 3, 531 (10.1038/s41928-020-0450-8), SMM of δ-doped p–n junctions, Curson co-author | Version of record is under the Springer TDM licence. OpenAlex gives the green EPFL copy as CC BY-NC-ND. | Cite only. |
| Kölker2022, Nanoscale 14, 6437 (10.1039/d1nr08381c), in operando imaging of δ-layer devices, Curson co-author | RSC terms (am). OpenAlex: green, "other-oa". | Cite only. |
| Jakob2024, Adv. Mater. (10.1002/adma.202405006), "Scalable Atomic Arrays…" | Europe PMC: CC BY-NC-ND | Possible ion-implant scaling cite. Unmodified figures only. |
| Holmes2024, Adv. Quantum Technol. (10.1002/qute.202300316), molecule-ion implants | OpenAlex: CC BY-NC-ND | Optional cite. |
| Kranz2023, Phys. Rev. Applied 19, 024068 (10.1103/PhysRevApplied.19.024068) | Crossref: CC BY 4.0 | Usable, but theory-heavy. Abstract: "two-qubit CNOT gate fidelities as high as 99.98% are realistic". Text was not read beyond the abstract. |
| Kolev2026, Mach. Learn.: Sci. Technol. 7, 025041 (10.1088/2632-2153/ae520e), few-shot ML defect classification in STM, Curson group | Crossref: CC BY 4.0 | Niche (automation for scaling). arXiv 2506.01678: "the prototypical network performs best, overall, with up to 99% accuracy in our test cases." |
| Hydrogen passivation / charge traps, AIP Adv. 2025 (10.1063/5.0283324), Curson group | OpenAlex: CC BY-NC | Cite only. Crossref not checked. |
| Needle in a haystack, RSI 2024 (10.1063/5.0208571), Curson group | No CC licence listed | Cite only. Crossref not checked. |

Other leads not checked: Adshead2026, "Deterministic Detection of Single Ion Implantation" (Adv. Eng. Mater., 10.1002/adem.202502911, OpenAlex lists cc-by), and Murdin2021, "Error Rates in Deterministic Ion Implantation for Qubit Arrays" (pss(b), 10.1002/pssb.202000615, cc-by). Both could help an ion-implantation comparison slide, but neither was read.
