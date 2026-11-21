# Device and surface geometry specs: Thorvaldson 2025, Edlbauer 2025, Wang 2022, Hofmann 2023, Lundgren 2023, Schofield 2025 roadmap, plus Si(001) lattice constants

Purpose: numbers for redrawing slide diagrams to scale. Every row has a verbatim quote and a location. If a source does not give a number, the row says **not stated**.

## Sources

| Key | Paper | DOI | Files read |
|---|---|---|---|
| THO | Thorvaldson *et al.*, Nat. Nanotechnol. 20, 472 (2025) | 10.1038/s41565-024-01853-5 | `figures/raw/Thorvaldson2025/PMC12014505.1.txt`, `PMC12014505.1.pdf` (text layer for figure labels), and the supplementary file MOESM1 (15 pp.), fetched from the PMC OA bucket into the session scratchpad. It is not saved in the repo. |
| EDL | Edlbauer *et al.*, Nature 648, 569 (2025) | 10.1038/s41586-025-09827-w | `figures/raw/Edlbauer2025/PMC12711558.1.txt`, `PMC12711558.1.pdf` (text layer of Fig. 1), `41586_2025_9827_Fig1_HTML.jpg`, and MOESM1 (20 pp.), fetched the same way (scratchpad only). |
| WAN | Wang *et al.*, Nat. Commun. 13, 6824 (2022) | 10.1038/s41467-022-34220-w | `figures/raw/Wang2022/PMC9652469.1.txt`, `41467_2022_34220_Fig1_HTML.jpg`, and MOESM1 (Supplementary Notes), fetched the same way (scratchpad only). |
| HOF | Hofmann *et al.*, Angew. Chem. Int. Ed. 62, e202213982 (2023). **Note: this paper covers arsine (AsH3) on Ge(001). It is not about Bi.** | 10.1002/anie.202213982 | `figures/raw/Hofmann2023/PMC10108107.1.txt` |
| LUN | Lundgren *et al.*, J. Phys. Chem. C (2023), "Adsorption and Thermal Decomposition of Triphenyl Bismuth on Silicon (001)". This is the Bi paper. | 10.1021/acs.jpcc.3c03916 | `figures/raw/Lundgren2023/PMC10461293.1.txt` |
| SCH | Schofield *et al.*, "Roadmap on Atomic-scale Semiconductor Devices", arXiv:2501.04535v2 | arXiv:2501.04535 | `figures/raw/Schofield2025/arxiv_2501.04535v2.pdf`. Page numbers are PDF pages. Figure labels were read from the embedded raster images. |
| CON24 | Constantinou *et al.*, Nat. Commun. (2024) | 10.1038/s41467-024-44790-6 | `figures/raw/Constantinou2024/PMC10808421.1.txt` |
| STO20 | Stock *et al.*, ACS Nano 14, 3316 (2020) | 10.1021/acsnano.9b08943 | `figures/raw/Stock2020/PMC7146850.1.txt` |
| WAR16 | Warschkow *et al.*, J. Chem. Phys. 144, 014705 (2016) | 10.1063/1.4939124 | Open-access publisher version from figshare (file 54396491), fetched into the scratchpad. |
| SR16 | Origin of Symmetric Dimer Images of Si(001) Observed by Low-Temperature STM, Sci. Rep. 6, 27868 (2016) | 10.1038/srep27868 | Europe PMC full text, PMC4904415 |
| SR17 | Layer-dependent semiconductor-metal transition of SnO/Si(001) heterostructure and device application, Sci. Rep. 7 (2017) | 10.1038/s41598-017-02832-8 | Europe PMC full text, PMC5451440 |
| NC25 | Self-passivation reduces the Fermi level pinning in the metal-semiconductor contacts, Nat. Commun. (2025) | 10.1038/s41467-025-65695-y | Europe PMC full text, PMC12660972 |
| MAT25 | Induction of Strong Magneto-Optical Effect and High Compatibility with Si of BiFeO3 Thin Films, Materials 18, 2953 (2025) | 10.3390/ma18132953 | Europe PMC full text, PMC12250978 |

## Conventions

- **Verbatim quote** is copied from the PMC plain text or the PDF text layer. Superscripts are flattened in those sources. For example, `2x10-2C/cm` means 2×10⁻² C/cm, and `2×1014/cm2` means 2×10¹⁴ cm⁻². The **Value** column gives the clean form.
- **[GRAPHIC]** means the value is a label inside a figure image, not in the prose. Some of these labels are in the PDF text layer. Others I read from the raster image, and those rows say so.
- **DERIVED** means arithmetic on the paper's own numbers. The paper does not state the result.
- "p." is the PDF page of the cited file. "Supp. p." is the PDF page of the MOESM1 supplementary file.

---

## A. Thorvaldson 2025 (four-qubit 3P register, Grover search)

| Spec | Value | Verbatim quote | Location | Key/DOI |
|---|---|---|---|---|
| P atoms per site | 3 P in one register, sharing one electron | "The multi-qubit processor studied in this work is formed by patterning three 31P atoms into isotopically purified 28Si with atomic precision using STM hydrogen lithography, as previously described for the same device by Reiner et. al.28." | Main text, "Single-qubit operations", p. 2 | THO |
| P atoms per site (abstract) | 3 P, 1 electron | "Our processor is made of three phosphorus atoms precision-patterned into isotopically pure silicon, which localise one electron." | Abstract, p. 1 | THO |
| Inter-donor distances | **not stated** in the main text or the supplement. The device is the same one as Reiner *et al.* 2024 (ref. 28, Nat. Nanotechnol. 19, 605), whose STM image is cited. | "An STM image of the device is shown in fig. 1c,d in ref. 28, where the same device as studied in this work was also studied." | Methods › Fabrication, p. 7 | THO |
| Donor-to-SET distance | **not stated**. The SET is described only qualitatively. | "An electron can be loaded onto the P atoms from a nearby, tunnel-coupled single-electron transistor (SET, yellow) that also serves as a charge sensor." | Main text, "Single-qubit operations", p. 2 | THO |
| Gate names/positions | Labelled only as "in-plane gates" (red), the SET (yellow), and an antenna on top. No gate names, count, or distances are given. | "Highly phosphorus-doped silicon in-plane gates allow control of the electrostatic environment of the P atoms (highlighted in red in the schematic illustration of the device in Fig. 1a, top)." | Main text, p. 2 | THO |
| Antenna | Broadband antenna on top of the device. Distance: **not stated**. | "a broadband antenna (grey) is placed on top of the device, delivering the radiofrequency and microwave signals for nuclear magnetic resonance (NMR) and for electron spin resonance (ESR), respectively." | Main text, p. 2 | THO |
| Fig. 1a schematic | A cartoon with no scale. Elements: in-plane gates (red), SET charge sensor (yellow), antenna (light grey wire). | "a, Top: a schematic illustration of the device consisting of in-plane gates (red), a SET charge sensor (yellow) and an antenna (light-grey wire)." | Fig. 1 caption | THO |
| ²⁸Si enrichment | ~200 ppm residual ²⁹Si; 45 nm ²⁸Si buffer | "The device was fabricated using hydrogen STM lithography on a silicon chip with a 45 nm layer of isotopically purified silicon-28 (~200 ppm of residual Si-29 atoms)." | Methods › Fabrication, p. 7 | THO |
| Buffer purpose | — | "This epitaxial buffer layer decouples the device from the nuclear spin bath of the natural silicon substrate." | Methods › Fabrication | THO |
| Lithography dose / bias | **not stated** | — | — | THO |
| PH3 dose | **not stated** (the paper says only "dosed with phosphine gas") | "After patterning the device, the sample is dosed with phosphine gas, followed by an incorporation anneal at 350 °C for 60 s to incorporate P atoms into the silicon crystal lattice." | Methods › Fabrication | THO |
| Incorporation anneal | 350 °C, 60 s | (same quote) | Methods › Fabrication | THO |
| Encapsulation (overgrowth) | 45 nm ²⁸Si, grown at 250 °C, at 0.15 nm min⁻¹ | "A 45 nm epitaxial layer of Si-28 is then grown at 250 °C and at a rate of 0.15 nm min−1 to ensure high-quality epitaxy." | Methods › Fabrication | THO |
| Overgrowth time | ≈300 min (45 nm ÷ 0.15 nm min⁻¹). **DERIVED** | — | — | THO |
| Stack (for drawing) | ²⁸Si buffer 45 nm / P layer / ²⁸Si cap 45 nm | "The buffer layer separates the qubits from any charged defects on the silicon surface and, together with the encapsulation layer, provides a monolithic qubit environment with minimal levels of spin and charge noise40." | Methods › Fabrication | THO |
| Magnetic field | 1.45 T | "Electron spin initialization and readout is performed via a ramped technique29 at a dilution refrigerator base temperature of 15 mK, with an applied magnetic field of 1.45 T." | Main text, p. 2 | THO |
| Fridge temperature | 15 mK base | (same quote) | Main text, p. 2 | THO |
| Electron temperature | **not stated** | — | — | THO |
| Electron Zeeman energy | ~39 GHz | "it is also valid to work in the secular approximation as γeB0 ∼39 GHz is much larger than other energy scales of the Hamiltonian" | Supp. Section IX, Supp. p. 10 | THO |
| Hyperfine couplings | A1 = 6 MHz, A2 = 68 MHz, A3 = 103 MHz | "From the ESR peak separations, we find hyperfine interaction strengths of A1 = 6 MHz, A2 = 68 MHz and A3 = 103 MHz." | Main text, p. 3 | THO |
| ESR peak frequencies | 38.980, 38.986, 39.048, 39.054, 39.083, 39.089, 39.151, 39.157 GHz | [GRAPHIC] x-axis tick labels of Fig. 1b, from the PDF text layer: "38.980 … 39.157" | Fig. 1b, p. 2 | THO |
| NMR peak frequencies | 27.182, 20.939, 58.003, 9.824, 75.594, 27.337 MHz | [GRAPHIC] x-axis tick labels of Fig. 1c, from the PDF text layer | Fig. 1c, p. 2 | THO |
| ESR Rabi frequency | ≈170 kHz (171.57 kHz for ⇓⇓⇓) | "the drive amplitudes for each ESR peak have been adjusted to have all ESR rabi frequencies in the proximity of 170 kHz, and that these settings are used throughout the rest of this work." | Supp. Section IV + Table SII, Supp. p. 7 | THO |
| NMR Rabi frequencies | n1 11.22 kHz, n2 24.16 kHz, n3 31.44 kHz | Table SII rows: "n1 11.22 1260 71.75 / n2 24.16 490 3.50 / n3 31.44 600 2.21" (columns fRabi (kHz), T2* (µs), T2Rabi (ms)) | Supp. Table SII, Supp. p. 7 | THO |
| Gate times | **not stated explicitly.** The CZ gate is one ESR 2π pulse; at f_Rabi ≈ 171 kHz this is ≈5.8 µs (**DERIVED**). | "simply by enacting a 2π rotation of the electron spin conditional on the configuration of the nuclear spins, we implement a geometric CZ gate between the nuclear spins23,30." | Main text, "Two- and three-qubit entanglement" | THO |
| T2* | e 28.1 µs; n1 1.26 ms; n2 0.49 ms; n3 0.60 ms | "We find T2*=28.1μs for the electron spin and 1.26 ms, 0.49 ms and 0.60 ms for nuclear spins 1, 2 and 3, respectively" | Main text, p. 3 | THO |
| 1Q fidelities | 99.94, 99.98, 99.95, 99.95 % (e, n1, n2, n3) | "We achieve single-qubit gate fidelities for all four individual qubits of (99.94 ± 0.01)%, (99.98 ± 0.01)%, (99.95 ± 0.01)% and (99.95 ± 0.01)%." | Main text (intro), p. 2 | THO |
| CZ fidelities | 99.65 %, 99.49 %, 99.32 % | "we find CZ gate fidelities of FCZ12=(99.65±0.35)%, FCZ13=(99.49±0.39)% and FCZ23=(99.32±0.22)% for the three pairs of nuclear spins." | Main text, p. 3 | THO |
| Bell fidelities | 97.5 %, 97.7 %, 96.8 % | "We achieve average Bell state fidelities of FBS12=(97.5±0.3)%, FBS13=(97.7±0.4)% and FBS23=(96.8±0.4)%" | Main text, p. 3 | THO |
| GHZ fidelity | 96.2 % | "We achieve a fidelity of FGHZ123=(96.2±0.5)% (including SPAM errors)" | Main text, p. 4 | THO |
| Grover search | 94.57 % of ideal (89.40 % raw average) | "find an average probability of (89.40 ± 2.49)% of finding the marked state, which corresponds to (94.57 ± 2.63)% of the ideal value." | Main text, p. 4 | THO |
| Readout fidelity | >99 % after post-selection | "readout of all nuclear spin qubits with a fidelity above 99% after post-selection" | Main text (intro) | THO |

---

## B. Edlbauer 2025 (11-qubit 4P–5P processor)

| Spec | Value | Verbatim quote | Location | Key/DOI |
|---|---|---|---|---|
| Register composition | 4P register (n1–n4, e1) and 5P register (n5–n9, e2) | "Scanning tunnelling micrograph of the processor core after hydrogen lithography showing the 4P register hosting n1–n4 and e1 (square) and the 5P register hosting n5–n9 and e2 (pentagon)." | Fig. 1b caption, p. 2 | EDL |
| Register-to-register distance | 13(1) nm, centre to centre | "The distance 13(1) nm (centre to centre) between the nuclear spin registers is atomically engineered to enable exchange coupling26,54. Scale bar, 10 nm." | Fig. 1b caption, p. 2 | EDL |
| Fig. 1b scale bar | 10 nm | (same quote) | Fig. 1b caption | EDL |
| Fig. 1b orientation labels | Detuning along [100]; B along [110]; "28Si"; SET sensor at right | [GRAPHIC] Fig. 1b, PDF text-layer labels: "4P register", "5P register", "Detuning [100]", "SET sensor", "B [110]", "28Si" | Fig. 1b, p. 2 | EDL |
| Intra-register P–P spacing | ≲3 nm (a general platform statement, not a measured spacing for this device). The individual P positions inside each register are **not stated**. | "The 14\|15 platform uses precision manufacturing21 to place individual phosphorus atoms in close proximity (≲3 nm) to each other, in which a single loaded electron exhibits a hyperfine interaction with several nuclei." | Main text, p. 1 | EDL |
| Register radius (abstract) | "a few nanometres" | "By placing several phosphorus atoms within a radius of a few nanometres, they couple by means of the hyperfine interaction to a single, shared electron." | Abstract | EDL |
| SET position | 17(1) nm from the registers, centre to edge | "Gate 1 and 2 control the number of electrons on each register that are loaded from a single-electron transistor (SET) located 17(1) nm away from the registers (center to edge)." | Supp. Section I, Supp. p. 3 | EDL |
| Gate count | 2 detuning gates (gate 1, gate 2) + SET + on-chip antenna | "We operate the spin registers via two gates (gate 1 and 2), a single-electron transistor (SET) and an on-chip antenna." | Supp. Section I, Supp. p. 3 | EDL |
| Gate–gate distance | d_gate = 146.6 nm (between G1 and G2) | "employing the distance between the gates G1 and G2 dgate = 146.6 nm and the V-to-eV conversion factor α = 0.07." | Supp. Fig. S6 caption, Supp. p. 13 | EDL |
| Supp. Fig. S1a scale bar | 100 nm; labels Gate 1, Gate 2, SET Sensor, 4P e1, 5P e2, B (110), Detuning [100], 28Si | [GRAPHIC] Supp. Fig. S1a, text-layer labels "Gate 1", "Gate 2", "SET", "Sensor", "28Si", "100 nm", "B", "(110)", "[100]" | Supp. Fig. S1a, Supp. p. 3 | EDL |
| Antenna position | On top of the chip, ≈300 nm horizontal offset | "On top of the chip, an antenna is horizontally offset from the dots by  about 300 nm (refs. 5,55)." | Methods › Experimental set-up, p. 8 | EDL |
| Antenna (supp.) | ≈300 nm | "broadband antenna, which is located on top of the chip at a horizontal distance of ≈300 nm [2, 3]." | Supp. Section I | EDL |
| Encapsulation thickness | about 45 nm | "The encapsulation is about 45 nm." | Methods › Experimental set-up, p. 8 | EDL |
| Fabrication recipe (lithography, dose, anneal, overgrowth temperature) | **not stated** in the main text or the supplement. The supplement says only that the gate/SET mask was imaged "after incorporation". | "Figure S1a shows the hydrogen lithography mask for the gates and the SET after incorporation of the spin registers." | Supp. Section I | EDL |
| ²⁹Si concentration | "sub-200 ppm" (stated for the platform, citing ref. 22). No device-specific ppm value is given. | "Combined with recent advances in silicon purification with sub-200 ppm of 29Si (ref. 22), these features enabled nuclear–nuclear CZ operations with fidelities exceeding 99%" | Main text, p. 1 | EDL |
| ²⁹Si check | No ²⁹Si NMR signal seen | "We performed ionised NMR experiments [7], and observed no signal from Si29." | Supp. Section III.A, Supp. p. 5 | EDL |
| Magnetic field | B ≈ 1.39 T along [110] | "Spin polarization is activated by a magnetic field B ≈ 1.39 T along the [110] crystal direction." | Methods › Experimental set-up, p. 8 | EDL |
| Fridge temperature | about 16 mK | "The experiment is performed in a cryogen-free dilution refrigerator at a base temperature of about 16 mK." | Methods › Experimental set-up, p. 8 | EDL |
| Electron temperature | **not stated** | — | — | EDL |
| Hyperfine, 4P register (MHz) | n1 1.0, n2 1.1, n3 2.2, n4 83.6 | [GRAPHIC] Fig. 1a, PDF text-layer labels "2.2", "1.1", "83.6", "1.0". Each value was assigned to its nucleus by its label position next to that nucleus (n3 2.2, n2 1.1, n4 83.6, n1 1.0). | Fig. 1a, p. 2. Caption: "a, Connectivity of nuclear spins (n1–n9) and electron spins (e1 and e2) through hyperfine and exchange coupling with energies in MHz." | EDL |
| Hyperfine, 5P register (MHz) | n5 0.6, n6 8.2, n7 20.8, n8 40.0, n9 197.8 | [GRAPHIC] Fig. 1a, text-layer labels "0.6", "8.2", "20.8", "40.0", "197.8", assigned by position. The ordering agrees with the Table S4 NMR frequencies (n5 lowest, n9 highest). | Fig. 1a, p. 2 | EDL |
| Exchange J (Fig. 1a) | 1.55 MHz | [GRAPHIC] Fig. 1a label "1.55", on the exchange (dashed) line e1–e2 | Fig. 1a | EDL |
| Exchange J (operating point) | J ≈ 1.55 MHz | "Here we operate in a weak exchange-coupled regime with J ≈ 1.55 MHz (Fig. 1c)." | Main text, p. 2 | EDL |
| Exchange J (Bell tomography) | J ≈ 1.69 MHz; CROT Rabi frequency 436 kHz | "Here the experiments are performed with J ≈ 1.69 MHz, which sets the optimal Rabi frequency for CROT operations to 436 kHz." | Main text, p. 4 | EDL |
| Exchange J (supp. fit) | 4P: 1.691(2) MHz; 5P: 1.689(2) MHz | "4P: J=1.691(2) MHz" … "5P: J=1.689(2) MHz" | Supp. Fig. S3, Supp. p. 7 | EDL |
| Example Hyperfine Stark plot (n6) | ≈8.1–8.4 MHz over the detuning sweep | [GRAPHIC] Supp. Fig. S6c axis "Hyperfine (MHz) 8.1 8.2 8.3 8.4", "n6", "Slope: eff. = 2.087 kHz/mV" | Supp. Fig. S6c, Supp. p. 13 | EDL |
| ³¹P nuclear gyromagnetic ratio used | γn ≈ −17.23 MHz/T | "The second term is the 31P nuclear Zeeman with gyromagnetic ratio γn ≈−17.23 MHz/T." | Supp. Section II, Supp. p. 3 | EDL |
| NMR frequencies (MHz) | n1 24.450, n2 24.534, n3 24.985, n4 65.412, n5 24.221, n6 28.110, n7 34.324, n8 43.902, n9 123.026 | Table S4: "#Qubit fNMR (MHz) fRabi (kHz) ANMR (mV) n1 24.450 3.582 4.726 … n9 123.026 18.025 6.393" | Supp. Table S4, Supp. p. 16 | EDL |
| ESR frequency scale | ≈38.71 GHz (Fig. 1c axis "ESR frequency + 38,710 (MHz)"); off-resonant ESR 38.86 GHz | [GRAPHIC] Fig. 1c axis label "38,710". Supp.: "resonant NMR (ESR) driving at 50 MHz (38.86 GHz)" | Fig. 1c, p. 2; Supp. Section VIII, Supp. p. 14 | EDL |
| Gate time (CROT) | f_Rabi ≈ 400 kHz → CROT π ≈ 1.25 µs | "the Rabi frequency is optimized to fRabi ≈ 400 kHz for the chosen exchange coupling J ≈ 1.55 MHz (ref. 40) … This choice sets the duration of the CROT π rotation to approximately 1.25 μs." | Main text, p. 3 | EDL |
| Rabi periods T_Rabi (µs) | n1 277, n2 277, n3 270, n4 102, n5 279, n6 241, n7 197, n8 155, n9 55, e1 11, e2 7 | [GRAPHIC] Fig. 1d, text-layer row "T_Rabi (µs) 277 277 270 102 279 241 197 155 55 11 7" | Fig. 1d, p. 2 | EDL |
| Coherence | Nuclear T2* 1–46 ms; T2Hahn 3–660 ms; electron T2* ≈20 µs, T2Hahn ≈350 µs | "For the nuclear spins, the phase coherence time extracted from Ramsey measurements, T2⋆, ranges from 1 to 46 ms. Refocusing with Hahn echo greatly extends such a phase coherence, T2Hahn, to values between 3 and 660 ms." / "For the electrons e1 and e2, we measure similar phase coherence times of T2⋆≈20μs and T2Hahn≈350μs." | Main text, p. 3 | EDL |
| Fidelity range | 99.10–99.99 % (all 1Q and multi-qubit gates) | "we achieve single-qubit and multi-qubit gates with all fidelities ranging from 99.10% to 99.99%." | Abstract | EDL |
| CROT fidelity | 99.64(8) % | "The extracted electron–electron CROT gate fidelity of 99.64(8)% indicates excellent performance" | Main text, p. 3 | EDL |
| Nuclear CZ fidelity | 99.90(4) % (n6–n9) | "giving a nuclear two-qubit-gate fidelity of 99.90(4)%." | Main text, p. 3 | EDL |
| Bell fidelities | local 91.4(5)–99.5(1) %; non-local 87.0(4)–97.0(2) % | "Bell-state fidelities ranging from 91.4(5)% to 99.5(1)% within registers and from 87.0(4)% to 97.0(2)% across registers." | Conclusion | EDL |
| GHZ | 3-qubit 90.8(3) %; entanglement up to 8 nuclei | "the data demonstrate that entanglement is maintained for up to eight nuclear spins." | Main text, p. 5 | EDL |
| ESR count | 2⁴ + 2⁵ = 48, doubled to 96 with exchange | "The initial calibration of the 11-qubit atom processor requires the characterization of 24 + 25 = 48 electron spin resonances (ESRs), which is doubled to 96 in the presence of electron exchange interaction." | Main text, p. 2 | EDL |

---

## C. Wang 2022 (3×3 few-dopant quantum-dot arrays, NIST)

| Spec | Value | Verbatim quote | Location | Key/DOI |
|---|---|---|---|---|
| Lattice constants, arrays #1–#3 | a1 = 4.1±0.3 nm, a2 = 6.6±0.3 nm, a3 = 10.7±0.3 nm | "a, d, g are STM images of the three arrays, where the lattice constants vary from a1=4.1±0.3nm, a2=6.6±0.3nm to a3=10.7±0.3nm, respectively." | Fig. 2 caption, p. 3 | WAN |
| Definition of a | Average nearest-neighbour centre-to-centre distance | "We define the 2D square lattice constant, a, as the averaged center-to-center distance between nearest neighboring dots within the array." | Fig. 1c caption, p. 2 | WAN |
| Ruler | Dimer-row pitch 0.77 nm | "the locations of the artificial lattice sites and the lattice constants can be determined by using the surface reconstruction dimer unit cells as an atomically precise ruler and counting the number of dimer rows (dimer-row pitch = 0.77 nm) between neighboring sites." | Results, p. 2 | WAN |
| a in dimer rows | a1 ≈ 5.3, a2 ≈ 8.6, a3 ≈ 13.9 dimer-row pitches. **DERIVED** (a ÷ 0.77 nm) | — | — | WAN |
| Equivalent bulk densities | ~1.5×10¹⁹, ~3.5×10¹⁸, ~8×10¹⁷ cm⁻³ | "the lattice constant in the first, second, and the third arrays correspond to a bulk doping density of ~1.5×1019/cm3, ~3.5×1018/cm3, and ~8×1017/cm3" | Results, p. 3 | WAN |
| Dot (site) lithographic size | ~10 to ~20 adjacent H atoms removed per site | "Each lattice site is defined by using an STM tip to remove a small patch of (~10 to ~20) adjacent hydrogen atoms" | Results, p. 2 | WAN |
| Dot size is constant across arrays | Same gates and average lithographic dot size for all arrays | "For the arrays in this study, we design the in-plane gates and average lithographic dot size to be the same for all arrays and only alter the lattice constant" | Results, p. 3 | WAN |
| Dopants per dot | 2 ± 1 P (range 1–3) | "We estimate the number of dopant atoms in the quantum dots to be within the range of 2±1 dopants by characterizing the binding energies of few-dopant quantum dots with a similar lithographic patch" | Results, p. 3 | WAN |
| Dopants per dot (patch rule) | 1 to 3 P per patch | "We have recently demonstrated that a dangling bond patch of similar size typically forms a few-dopant cluster quantum dot incorporating 1 to 3 phosphorus atoms14." | Results, p. 2 | WAN |
| P-incorporation counting rule | ≥3 contiguous bare dimers per P; upper bound 0.25 ML; lower bound 0.09 ML | "Having at least three adjacent H-desorbed dimers within the same dimer row is a necessary condition to incorporate one P dopant into the surface silicon lattice." / "The upper bound of our estimate of the number of incorporated P atoms is set by 25% of the number of dangling bonds sites within allowed dimers, according to the 0.25 monolayer of P incorporation density in saturate-doped Si:P 𝛿-layers." / "the P incorporation density in nm scale desorbed areas decreases to 0.09 monolayer" | Supp. Note 2, Supp. pp. 7–8 | WAN |
| Gate/lead–array distances | **not stated** in the main text or Supp. Note 2. Fig. 1b has a 60 nm scale bar and Fig. 1c a 12 nm scale bar ([GRAPHIC], read from the raster image). | Fig. 1b shows Gate 1 (top), Gate 2 (bottom), Source (left), Drain (right) | Fig. 1b,c | WAN |
| Terrace step | Gates sit one mono-atomic layer (~0.14 nm) above and below the array terrace | "Gate 1 and Gate 2 reside on surface terraces one mono-atomic layer (~0.14 nm) above and below the middle terrace." | Fig. 1b caption, p. 2 | WAN |
| Dimer-row direction (Fig. 1c) | Upper left to lower right | "2 × 1 surface reconstruction dimer rows on the Si(100) surface run from the upper left to lower right direction in the image." | Fig. 1c caption | WAN |
| STM imaging | −2 V, 0.1 nA | "The STM image is taken at −2 V sample bias and 0.1 nA setpoint current." | Fig. 1c caption | WAN |
| δ-layer (leads/gates) density | ~2×10¹⁴ cm⁻² (≈2×10²¹ cm⁻³) | "The STM-patterned in-plane source/drain leads and gates are saturation-doped49 with a dopant density of ~2×1014/cm2, corresponding to a 3D doping density of ~2×1021/cm3" | Methods › Device fabrication, p. 9 | WAN |
| Electrostatic seam (model) | Lateral 2.5 nm, vertical 2 nm | "a lateral seam of 2.5 nm and a vertical thickness of 2 nm have been included to account for the Bohr-radius-like electron density extension beyond the lithographic patterns" | Methods › Theory, p. 10 | WAN |
| UHV base pressure | <4×10⁻⁹ Pa (3×10⁻¹¹ Torr) | "fabricated in an ultrahigh vacuum (UHV) environment with a base pressure below 4×10−9 Pa (3×10−11 Torr)" | Methods, p. 9 | WAN |
| PH3 dose | Saturation dose at room temperature | "The substrate is then saturation-dosed with PH3 gas at room temperature, where PH3 molecules selectively absorb only onto the lithographic regions" | Methods, p. 9 | WAN |
| Incorporation anneal | 350 °C, 1 min RTA | "A subsequent rapid thermal anneal process at 350 °C for 1 min incorporates the absorbed phosphorus atoms into the Si surface lattice sites" | Methods, p. 9 | WAN |
| Locking layer + overgrowth | Room-temperature locking layer, then ~250 °C overgrowth. Encapsulation thickness: **not stated**. | "We use a room-temperature grown locking layer technique to suppress atomic-scale movement of the precisely defined dopant atom positions26 before a subsequent low-temperature (~250 °C) epitaxial Si overgrowth" | Results, p. 2 | WAN |
| Contacts | Low-thermal-budget silicide | "Finally, ohmic contacts to the buried electrodes are formed using a low thermal budget silicide contacting technique27." | Results, p. 2 | WAN |
| Fridge temperature / electron temperature | ~10 mK base; electron ~300 mK | "measured at T ~ 10 mK base temperature (electron temperature ~300 mK)" | Results, p. 4 | WAN |
| Elevated-temperature range | up to ~16 K (substrate leakage limit); data at 4, 8, 12 K | "The experimental temperature range investigated is limited by the temperature (~16 K) at which leakage current through the Si substrate becomes comparable to conductance through the array." | Results, "Thermal activation" section | WAN |
| Hopping used in model | t = 8, 2, 0.5 meV (arrays 1, 2, 3) | "The hopping amplitudes are set as t = 8 meV, t = 2 meV, and t = 0.5 meV for simulating the first, second, and third arrays, respectively" | Methods | WAN |

---

## D. Si(001) surface and lattice geometry

| Spec | Value | Verbatim quote | Location | Key/DOI |
|---|---|---|---|---|
| Dimer-row pitch | 0.77 nm | "counting the number of dimer rows (dimer-row pitch = 0.77 nm) between neighboring sites" | WAN Results, p. 2 | WAN, 10.1038/s41467-022-34220-w |
| Dimer-row pitch (roadmap §4.2) | 0.77 nm | "Length scales in STM images are given by the pitch of dimer rows of 0.77 nm." | SCH §4.2 Fig. 2 caption, p. 54 | SCH, arXiv:2501.04535 |
| Dimer-row pitch, 3 s.f. (roadmap §5.5) | 0.768 nm | "The problem is that Tennant's Law [5] suggests that a serial writing tool with 0.768nm resolution will require >200 hours to write a square micron." | SCH §5.5, p. 87 | SCH |
| "7.68 Å" verbatim | **not found** in any source read. The closest is "0.768nm" above. | — | — | — |
| Half-dimer-row line width | 0.3 nm | "This line is mostly half dimer row (0.3nm) in width." | SCH §2.2 Fig. 1 caption, p. 13 | SCH |
| Surface lattice constant (1×1) | 3.84 Å | "We note that the lattice constant of SnO is very close to that of the Si(001) surface (3.84 Å)." | SR17 Introduction | SR17, 10.1038/s41598-017-02832-8 |
| Dimer bond length (bare, buckled) | 2.357 Å; buckling angle 18.0° (DFT, c(4×2)) | "We find that the c (4 × 2) structure has a dimer bond length of d D = 2.357 Å and a dimer buckling angle of θ = 18.0°." | SR16 Results | SR16, 10.1038/srep27868 |
| Dimer bond length, H-terminated (monohydride) | **not found** in any source read | — | — | — |
| Si–H bond length | 1.51 Å (dangling-bond termination, after Northrup) | "we terminate each surface dangling bond by a H atom using a bond length of 1.51 Å for the Si–H bond and 1.56 Å for the Ge–H bond, a configuration found to be stable by Northrup 56." | NC25 Results | NC25, 10.1038/s41467-025-65695-y |
| Si–H bond length (cluster termination) | 1.49 Å. This is a modelling constraint for the cluster boundary, not a surface measurement. | "placing hydrogen atoms along the direction of the broken bond such that the bond length between the extracted cluster Si atom and the hydrogen atom is 1.49 Å." | WAR16 Sec. II (methods), p. 5 | WAR16, 10.1063/1.4939124 |
| WAR16 template surface | 25-layer slab, (2×1) monohydride, H–Si–Si–H dimers | "This structure template is composed of 25 atomic layers of silicon and is terminated on both sides with a (2 × 1) monohydride surface reconstruction (i.e., H–Si–Si–H dimers; see note in Ref. 61)." | WAR16 p. 5 | WAR16 |
| Bulk lattice constant (experimental) | 5.431 Å | "a significant lattice mismatch exists between garnet ferrites and silicon (YIG: 12.376 Å; Si: 5.431 Å)" | MAT25 Introduction | MAT25, 10.3390/ma18132953 |
| Bulk lattice constant (DFT-PBE) | 5.418 Å | "The Si(001) surafce (with the Si lattice constant a 0 = 5.418 Å) was modeled by a twelve-layer slab with ~30 Å of vacuum in between the slabs" | SR16 Methods | SR16 |
| Monatomic step / layer height | ~0.14 nm | "one mono-atomic layer (~0.14 nm)" | WAN Fig. 1b caption | WAN |
| "0.136 nm" verbatim | **not found** in any source read. a/4 = 5.431/4 = 1.358 Å (**DERIVED**). | — | — | — |
| Monolayer atom density | 1 ML = 6.78×10¹⁴ atoms cm⁻² | "We quantify the surface density of clean silicon in terms of monolayers (MLs; where 1 ML = 6.78 × 1014 atoms cm−2)" | CON24 Results › "Non-monochromatic irradiation of Si(001):H" | CON24, 10.1038/s41467-024-44790-6 |
| Check of 6.78×10¹⁴ | 1/(3.84 Å)² = 6.78×10¹⁴ cm⁻². **DERIVED** | — | — | — |
| ML ↔ Å growth-rate equivalence (STO20) | The Methods give 1.5 Å/min; the Results give the same source as 1 ML/min | "operated at a deposition rate of 1.5 Å/min" (Experimental Methods › Sample Preparation) and "overgrown with 15 nm of silicon at a rate of 1 ML/min" (Results › Encapsulation of Arsenic Layers) | STO20 pp. 9 and 7 | STO20, 10.1021/acsnano.9b08943 |
| Surface reconstruction (LUN) | c(4×2) buckled dimers at 78 K | "The Si(001) surface consists of rows of buckled dimers in a c(4 × 2) periodicity; these dimer rows run horizontally in Figure 1b and their periodicity is evident by a zig-zagged appearance.25" | LUN Results | LUN |
| P δ-layer saturation density | 0.25 ML | "according to the 0.25 monolayer of P incorporation density in saturate-doped Si:P 𝛿-layers." | WAN Supp. Note 2 | WAN |
| Ideal single-dopant window (As) | 4 Si-atom adsorption window | "presents the ideal 4 atom silicon-site adsorption window that can be used to ensure incorporation of single arsenic atoms with 97±2% probability." | SCH §4.1 Fig. 1 caption, p. 48 | SCH |
| Ge vs Si lattice constant | Ge is 4.3 % larger | "Because the lattice constant of Ge is 4.3% larger than that of Si, energy gain from the dimer reconstruction on the Ge (001) surface is less than that on the Si (001) surface" | NC25 Results | NC25 |
| STM tip–sample distance (simulation context) | ~5 Å | "Note that an STM bias voltage of 1.5 V and a tip-sample distance of ~5 Å would give rise to an electrical field of ~0.3 V/Å." | SR16 Results | SR16 |

---

## E. Hofmann 2023 (AsH3 on Ge(001)) and Lundgren 2023 (triphenyl-Bi on Si(001))

### Hofmann 2023: arsine on Ge(001)

| Spec | Value | Verbatim quote | Location | Key/DOI |
|---|---|---|---|---|
| Incorporation temperature | Room temperature; no anneal needed | "Here, we show that at room temperature, arsenic atoms fully incorporate into the germanium surface layer from adsorbed arsine molecules. Remarkably, and unlike all previously studied systems, no thermal anneal is required" | Introduction | HOF, 10.1002/anie.202213982 |
| AsH3 dose (pressure × time) | **not stated** in the main text | — | — | HOF |
| Time to imaging after dose | <15 min | "We have performed arsine dosing in situ, allowing us to restart imaging <15 minutes after arsine exposure." | Discussion | HOF |
| Ge(001) reconstruction | Dimer rows; buckled c(4×2) or 2×1 | "Rows of germanium dimers run horizontally across the image and form either a buckled c(4×2) configuration or a more symmetric appearing 2×1 configuration. [23]" | Results, Fig. 1 discussion | HOF |
| Ge(001) lattice/dimer dimensions | **not stated** in Å or nm | — | — | HOF |
| Feature footprints | m1 = 2 dimers; t1 and h1 = 3 dimers wide (t1 spans 2 rows) | "Both features are three dimers wide. The t1 feature exhibits a complicated appearance and spans two dimer rows" | Results | HOF |
| Anneal 140 °C | Most RT features gone; epitaxial Ge islands appear | "Figure 3a shows an image of a dosed surface after annealing to 140 °C. Almost all the room temperature features have disappeared, except the m1 features." | Results (Fig. 3 discussion) | HOF |
| Anneal 250–300 °C | H/As = 3:1; As–Ge heterodimers plus monohydrides | "The ratio of hydrogen to arsenic in the range 250–300 °C is equal to the expected stoichiometric ratio of 3 : 1 to within our experimental uncertainties" | Results (Fig. 4e) | HOF |
| Anneal 420 °C | Only H-free As–Ge heterodimers remain | "Figure 4b shows an STM image of the surface after annealing to 420 °C, and here we find the only surviving features are hydrogen‐free arsenic‐germanium heterodimers." | Results | HOF |
| H desorption from Ge(001) | 330 °C | "consistent with the known desorption temperature of hydrogen from the monohydride phase on Ge(001) of 330 °C. [34]" | Results | HOF |
| As loss | Gradual up to 500 °C; strong at 800 °C; As2 desorption above 500 °C | "There is a slight systematic reduction in arsenic coverage for temperatures up to 500 °C, and dramatic reduction at our highest anneal temperature of 800 °C." / "above 500 °C we anticipate also arsenic desorption from the surface in the form of As2 molecules" | Results | HOF |
| P2 desorption from Si(001) (cited) | 670–820 °C | "as is known to occur for desorption of P2 molecules from the silicon (001) surface between 670 and 820 °C. [37]" | Results | HOF |
| Typical incorporation anneal elsewhere | 350 °C | "In all previously studied systems an incorporation anneal (typically 350 °C) is required" | Discussion | HOF |
| STM image parameters | −1.5 V, 200 pA; Fig. 1a 30×22 nm² | "STM image parameters: all images −1.5 V, 200 pA. … (a) 30×22 nm2, (b), (f), (g) 5.7×3.8 nm2, (d) 6.9×3.8 nm2, (h)–(m) 8.0×6.1 nm2." | Fig. 1 caption | HOF |
| DFT energies | h1–h3 −2.8 eV; g1 −2.9 eV; m1 −3.1 eV | "the formation energies for h1–h3 are all equal at −2.8 eV, and structure g1 is nearly equal at −2.9 eV. … Structure m1 is slightly more stable at −3.1 eV." | Results | HOF |
| Ge–H bond length (other source) | 1.56 Å | (see NC25 Si–H row in Section D) | NC25 | NC25 |

### Lundgren 2023: triphenyl bismuth (TPB, Bi(C6H5)3) on Si(001)

| Spec | Value | Verbatim quote | Location | Key/DOI |
|---|---|---|---|---|
| Molecule size on surface | Three lobes within a diameter of ~1 nm. "1.1 nm" is **not stated**. | "each present three bright lobes clustered together within a diameter of ∼1 nm. Comparison to the threefold symmetric structure and dimensions of TPB (Figure 1a) suggests that these features can be attributed to molecularly adsorbed TPB" | Results, Fig. 1 discussion | LUN, 10.1021/acs.jpcc.3c03916 |
| Dissociated-phenyl separation | ≥1 nm | "the third protrusion is spatially separated by a distance ≥1 nm." | Results | LUN |
| Substrate preparation | Degassed at 550 °C overnight; flashed at 1200 °C for 10 s | "Silicon (001) samples (0.04–0.06 Ω cm, Sb-doped; Virginia Semiconductor Inc.) were degassed at 550 °C overnight, then flash annealed to 1200 °C for 10 s to produce an atomically clean Si(001) surface." | Methods | LUN |
| Dose | TPB cell at 80 °C; substrate at RT; 2×10⁻⁹ mbar | "with the TPB source heated to 80 °C and the silicon substrate held at room temperature. The chamber background pressure during TPB evaporation was 2 × 10–9 mbar." | Methods | LUN |
| Exposure times | 1 s (STM anneal series); 15 s (XPS); 1–60 s series | "A clean Si(001) surface was exposed to TPB for 1 s and then annealed for 5 min at consecutively higher temperatures." / "we have exposed the sample to TPB for 15 s" / "as a function of TPB exposure time from 1 to 60 s" | Results | LUN |
| STM temperature | 78 K | "We obtained atomic resolution STM images at a temperature of 78 kelvin" | Methods | LUN |
| Anneal steps (STM) | RT, 40, 140, 360, 580 °C (5 min each) | "Images of the surface after dosing at room temperature and subsequent annealing to 40, 140, 360, and 580 °C are shown in Figure 3a–e." | Results | LUN |
| Decomposition: phenyl detachment | ~140 °C | "we find complete phenyl detachment at around 140 °C, while bismuth migration into the bulk occurs at higher temperatures of around 360 °C." | Introduction | LUN |
| Bi incorporation | 360 °C (epitaxial Si rows from ejected Si) | "their appearance on the surface after annealing to 360 °C is a strong indicator that bismuth atoms have incorporated into the Si(001) surface,11,28 ejecting silicon atoms onto the surface in the process." | Results | LUN |
| SiC / 4×4 reconstruction | 580 °C | "We observe a 4 × 4 reconstruction, characteristic of silicon-carbide formation,15 after annealing to 580 °C." | Introduction | LUN |
| XPS anneal steps | 75, 220, 366, 482, 600 °C | "Figure 4 XPS measurements of Si(001) surfaces exposed to TPB for 15 s and then subsequently annealed to 75, 220, 366, 482, and 600 °C" | Fig. 4 caption | LUN |
| Bi signal loss | above 482 °C | "up to the annealing temperatures above 482 °C, where the overall bismuth signal decreases, which appears to correspond to the diffusion of Bi into the subsurface" | Results (XPS) | LUN |
| P2 desorption (cited) | ~800 °C | "it is known that phosphorus desorbs from Si(001) as P2 at a temperature of around 800 °C, or slightly lower at very high coverages.50−52" | Results (XPS) | LUN |
| STM image parameters | −2 V, 50 pA; panels 4×4 nm² | "Image parameters: −2 V, 50 pA, and z-range 180 pm. (b–l) 4 × 4 nm2, 78 K." | Fig. 1 caption | LUN |

---

## F. Schofield 2025 roadmap (arXiv:2501.04535v2)

### §2.2 Hydrogen depassivation lithography (Lyding)

| Spec | Value | Verbatim quote | Location | Key/DOI |
|---|---|---|---|---|
| HDL line, Fig. 1 | 3 V, 10 nA, **2×10⁻² C/cm**; half-dimer-row (0.3 nm) width | "Figure 1. (a) Image showing an HDL line patterned at 3V, 10nA, and 2x10-2C/cm. This line is mostly half dimer row (0.3nm) in width." | §2.2 Fig. 1 caption, p. 13 | SCH |
| Typical conditions, text | 3 V, 10 nA, 10 nm/s → **10⁻² C/cm** | "A typical set of patterning conditions for FCL or atom-wide line writing might be 3V and 10 nA (see Figure 1), with a write speed of 10 nm/s corresponding to an electron dose of 10-2 C/cm." | §2.2 Current and Future Challenges, p. 14 | SCH |
| Dose discrepancy | The caption gives 2×10⁻² C/cm and the text gives 10⁻² C/cm. 10 nA ÷ 10 nm/s = 1×10⁻² C/cm, so the text value matches its stated speed. 2×10⁻² C/cm at 10 nA implies 5 nm/s. **DERIVED** | — | — | SCH |
| Fast mode | Hundreds of nA, 2 V, 1000 nm/s | "Increasing the current to hundreds of nA, and reducing the voltage to 2 V retains the patterning resolution while increasing the writing speed to 1000 nm/s." | §2.2, p. 14 | SCH |
| EUV comparison | 10¹⁴ nm/s, 11 orders faster | "corresponds to linear write speed of 1014 nm/s, or eleven orders of magnitude faster than HDL." | §2.2, p. 14 | SCH |
| Bandgap of H-terminated surface | 1.1 eV | "showing the expected 1.1eV bandgap except for the white surface defect position." | §2.2 Fig. 1 caption | SCH |
| Wire electronics | Single-atom-wide lines are metallic; dimer-wide lines are semiconducting | "HDL patterns exhibit electronic contrast with single atom wide patterns being metallic and dimer-wide patterns being semiconducting[8]." | §2.2 Status | SCH |
| MEMS scale-up | 10⁷ scanners per 300 mm wafer | "MEMS based scanners with the potential of scaling to 107 scanners over the area of a 300 mm wafer are under development[14]." | §2.2 Advances | SCH |

### §2.3 P in Si device fabrication (Silver, Fei, Namboodiri, Wyrick)

| Spec | Value | Verbatim quote | Location | Key/DOI |
|---|---|---|---|---|
| Process sequence | Fiducials → reconstruction → H passivation → STM patterning → precursor dose and incorporation → overgrowth → ex-situ location, contacts, top gates, ESR lines | "The complete process is complex and typically includes pre-patterned fiducial marks for device re-location, Si surface reconstruction, H passivation, STM patterning, dopant precursor exposure and incorporation, and silicon overgrowth, followed by ex-situ steps to locate the buried devices and subsequent cleanroom processes to make contacts or place top gates and electron spin resonance (ESR) lines, see Figure 1 [5]." | §2.3 Status, p. 16 | SCH |
| Fig. 1 upper panel steps | Hydrogen Depassivation Lithography → Gas Phase Dosing and Si Overgrowth → Palladium Silicide Contacts | [GRAPHIC] raster labels: "Hydrogen terminated surface", "STM Tip", "PH3 molecules adsorb on patterned regions", "Epitaxial Si overgrowth", "Palladium Silicide Contacts" | §2.3 Fig. 1, p. 17 | SCH |
| Fig. 1(a) donor/SET device dimensions | Arrows labelled 100, 50, 68, 65, 90 (unit label cropped: "Unit: n…", presumably nm). Labels: Gate 1, Gate 2, Source, Drain, Donor Cluster, SET Island. | [GRAPHIC] raster image, §2.3 Fig. 1a: "Gate 2 … 100", "50 … Donor Cluster", "68", "65", "90 Gate 1", "Unit: n" | §2.3 Fig. 1a, p. 17 | SCH |
| Fig. 1(b) | ~15 nm feature spacing; 10 nm scale bar | [GRAPHIC] raster image: "~15 nm", "10nm" | §2.3 Fig. 1b, p. 17 | SCH |
| Overgrowth rate requirement | Monolayer-per-minute range | "One ongoing process challenge is that maintaining low temperatures during silicon overgrowth, yet achieving high quality epitaxy, mandates low growth rates in the monolayer per minute range, see Figure 2." | §2.3 Challenges, p. 17 | SCH |
| UHV requirement | few 10⁻¹¹ torr (~10⁻⁹ Pa) | "fabrication in an exceptional UHV environment with maximum pressures in the few 10-11 torr (~10-9 Pa) range." | §2.3 Challenges, p. 17 | SCH |
| Fig. 2 caption | In-situ dosing, incorporation, overgrowth | "Figure 2 An example of the in-situ dosing, incorporation, and overgrowth steps. While the TEM shows good confinement of a delta layer (red arrow), detailed atomic information is better gleaned using low temperature electrical measurements." | §2.3 Fig. 2 caption, p. 18 | SCH |
| Fig. 2 step 1 | 1200 °C flash anneal | [GRAPHIC] raster label "1200°C Flash Anneal" (partly obscured) | §2.3 Fig. 2, p. 18 | SCH |
| Fig. 2 step 2 | PH3 dosing (temperature not labelled; drawn at the baseline) | [GRAPHIC] "PH3 Dosing" | §2.3 Fig. 2 | SCH |
| Fig. 2 step 3 | Incorporation at 384 ± 24 °C | [GRAPHIC] "384±24°C Incorporatio[n]" (label cropped in the image) | §2.3 Fig. 2 | SCH |
| Fig. 2 step 4 (locking layer) | Si locking-layer deposition, 0–16 ML at RT | [GRAPHIC] "Si Locking Layer Deposition 0~16ML @ RT" (inside a dashed box titled "Locking Layer") | §2.3 Fig. 2 | SCH |
| Fig. 2 step 5 | RTA at 384 ± 24 °C | [GRAPHIC] "384 ± 24°C RTA" | §2.3 Fig. 2 | SCH |
| Fig. 2 step 6 | Soak at 274 ± 17 °C | [GRAPHIC] "274±17°C Soak" | §2.3 Fig. 2 | SCH |
| Fig. 2 step 7 | Encapsulation overgrowth at 274 ± 17 °C | [GRAPHIC] "274±17°C Encapsulation Overgrowth" | §2.3 Fig. 2 | SCH |
| Fig. 2 TEM inset | 11 ML RT locking layer at 1.8 ML/min + RTA; 59 nm overgrowth at 274 ± 17 °C; 8 nm scale bar | [GRAPHIC] "11ML RT LL @ 1.8ML/min + RTA", "59nm Overgrowth @ 274±17°C", "Locking Layer Interface", "Growth Direction", "8 nm" | §2.3 Fig. 2 inset, p. 18 | SCH |
| Time axis of Fig. 2 | **not labelled** (no times or durations shown) | — | §2.3 Fig. 2 | SCH |

### §3.1 Atom qubits (Keizer, Simmons)

| Spec | Value | Verbatim quote | Location | Key/DOI |
|---|---|---|---|---|
| 3P register T1 | ~30 s | "resulting in stronger electron confinement, and longer electron spin lifetimes (~30 sec in a 3P register) [WATSON2017]." | §3.1 Challenges, pp. 24–25 | SCH |
| Molecular-qubit P separation | ~8 nm | "electrons bound to phosphorus atoms separated by larger distances ~8nm exhibit excellent qubit properties" | §3.1, p. 25 | SCH |
| Hyperfine Stark coefficient | ~70 MHz/(MV m⁻¹) | "the engineering of large hyperfine Stark coefficients (~70MHz/MV m-1)" | §3.1, p. 25 | SCH |
| Exchange gate time | 0.8 ns (√SWAP, natural Si) | "extremely fast (0.8ns) two-qubit exchange or ÖSWAP gates have been demonstrated between two phosphorus multi-nuclear spin registers in natural silicon [HE2019]." | §3.1, p. 25 | SCH |
| Field gradient / CNOT | >800 MHz; 99.98 % for 2P–3P | "atomic engineering a large magnetic field gradient (>800 MHz) between the qubits with CNOT gate fidelities of 99.98% achievable for a 2P-3P system [KRANZ2023B]." | §3.1, p. 25 | SCH |
| Placement direction | [110] removes valley interference | "Aligning the qubits along the [110]-direction negates fluctuations in the strength of the exchange coupling as function of separation due to valley interference." | §3.1 Fig. 1 caption, p. 27 | SCH |
| Kinetic-control temperatures | 150 °C or 77 K; tip-assisted <77 K | "control the incorporation kinetics through precursor dosing pressures, times, and temperatures (150oC or 77K)" / "practically limits its application to low temperature (<77K) lithography and few sites." | §3.1 Advances, p. 25 | SCH |
| Current scale | ~1000 qubits with current processes | "Manufacturing of the accompanying large-scale integrated control and sensing components is achievable for qubit counts to ~1000 with current processes." | §3.1 Concluding, p. 26 | SCH |

### §4.1 Deterministic dopant incorporation (Stock, Schofield, Curson)

| Spec | Value | Verbatim quote | Location | Key/DOI |
|---|---|---|---|---|
| 2003 placement | 1 nm precision; P pair ~12 nm apart along one dimer row | "A single phosphorus atom was positioned with 1 nm precision and a pair of phosphorus dopants were positioned along a single dimer row separated by approximately 12 nm." | §4.1 Status, p. 48 | SCH |
| PH3 incorporation probability | 63 ± 10 % | "with a demonstrated probability of only 63 ± 10% [2]" | §4.1, p. 48 | SCH |
| AsH3 incorporation probability | 97 ± 2 % at a 4-Si-atom site | "arsine incorporation at a lithographically defined four silicon lattice adsorption site occurs with a 97 ± 2% probability." | §4.1, p. 48 | SCH |
| As array recipe | Lithography 3.5 V, 3000 pA, 50 nm s⁻¹; AsH3 5×10⁻⁹ mbar × 10 min; anneal 350 °C × 1 min | "Lithography parameters: 3.5 V, 3000 pA, 50 nm×s−1. AsH3 dosing: 5 × 10−9 mbar × 10 min. Incorporation anneal: 350 °C × 1 min." | §4.1 Fig. 1 caption, p. 48 | SCH |
| Imaging | −2 V, 40 pA / 100 pA | "Imaging parameters: a) −2 V, 40 pA; b,c) −2 V, 100 pA." | §4.1 Fig. 1 caption | SCH |

### §5.4 Scaling up HDL (Owen, Fowler, Moheimani)

| Spec | Value | Verbatim quote | Location | Key/DOI |
|---|---|---|---|---|
| Placement precision | ±1 atomic spacing | "with current processes able to achieve placement precision of ± 1 atomic spacing." | §5.4 Status, p. 82 | SCH |
| Conventional lithography limit | ~15 nm linewidths | "conventional lithography processes, such as e-beam and EUV lithography are reaching their limits at around 15 nm linewidths" | §5.4, p. 82 | SCH |
| HDL nanoimprint template | 6 nm linewidth | "creating a nanoimprint template with a linewidth as small as 6 nm by using selective Atomic Layer Deposition (ALD) of TiO2 as a hard mask" | §5.4, p. 82 | SCH |
| AP-mode write speed | 10–20 nm/s, ~100 atoms/s | "Currently, for the Atomically Precise (AP) mode, the linear tip speed is 10-20 nm/s, giving a write speed of ~100 atoms/s." | §5.4, p. 82 | SCH |
| FE mode | ~1000 atoms/s; several dimer rows wide | "In the higher-voltage Field Emission (FE) mode, where the linewidth is several dimer rows and the required dose is smaller, throughput of around 1000 atoms/s is possible" | §5.4, p. 82 | SCH |
| Tip–sample gap | <1 nm; currents up to 90 nA; speed approaching 1 µm/s | "Joe Lyding has demonstrated single dimer row writing at higher speeds using tunnel currents up to 90 nA. However, with a tip speed approaching 1 µm/s and a tip-sample gap less than 1 nm, the standard PI control loop is likely to insufficient to prevent tip crashes." | §5.4 Challenges, p. 82 | SCH |
| Scan field / z bandwidth | ±10 µm; 1 kHz | "move from a single piezo-driven tip scanning over a ± 10 µm scan field to an array of parallel MEMS-actuated tips. The mass of the piezo tube and STM tip assembly limits the z-axis bandwidth to 1 kHz" | §5.4, p. 83 | SCH |
| MEMS hybrid scan speed | 2 µm/s (10× standard) | "STM image of an HDL spiral pattern taken at 2 µm/s using a hybrid STM … This is 10x faster than our standard scan speed" | §5.4 Fig. 1 caption, p. 83 | SCH |
| Tip activation voltage | ~100 V | "Each tip will require a tunnelling control loop, control signals, and have activation voltages around 100 V." | §5.4, p. 83 | SCH |

---

## Gaps (not stated in any source read)

- THO: inter-donor distances, donor–SET distance, gate names and distances, electron temperature, lithography and PH3 dose. The geometry is in Reiner *et al.*, Nat. Nanotechnol. 19, 605 (2024), doi 10.1038/s41565-023-01596-9, which I did not read.
- EDL: P positions inside each register, the fabrication recipe (dose, anneal, overgrowth temperature), electron temperature, and a device-specific ²⁹Si ppm.
- WAN: gate-to-array and lead-to-array distances in text (only the scale bars in Fig. 1b,c), and encapsulation thickness.
- HOF: AsH3 dose and Ge(001) lattice dimensions.
- LUN: "1.1 nm" molecule size (the paper says ~1 nm).
- D: "7.68 Å", "0.136 nm", and the monohydride Si–Si dimer bond length were not found verbatim. Use 0.768 nm (SCH §5.5), ~0.14 nm (WAN), and 2.357 Å for the bare buckled dimer (SR16) instead.
