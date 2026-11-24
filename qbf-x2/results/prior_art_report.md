# QBF-X2 prior-art check (papers and patents, to Nov 2026)

**How to read this.** "Verified" means a tool returned the DOI or metadata. "Read" means I read the full text. I could not open any patent claims, because WebFetch was blocked for patents.google.com, patents.justia.com, uspto.report, arxiv.org and journals.aps.org. Patent content therefore comes from abstracts and search summaries. Finding nothing in these tools does not prove novelty.

## 1. Wustmann & Osborn, PRB 101, 014516 (2020): confirmed
W. Wustmann, K. D. Osborn, "Reversible fluxon logic: Topological particles allow ballistic gates along one-dimensional paths," *Phys. Rev. B* 101, 014516 (2020), doi:10.1103/PhysRevB.101.014516, arXiv:1711.04339 (read).
- **What it shows:** Ballistic reversible gates in which a bit is the polarity of a fluxon in a discrete long Josephson junction (LJJ). One-bit identity and NOT gates come from resonant scattering at a three-junction interface with large capacitors. A two-bit NSWAP gate uses two synchronised fluxons that interact at a shared interface, giving a conditional polarity flip with more than 97% of the energy kept. The paper notes that collisions inside a single sine-Gordon line give "only time delays."
- **Status:** classical theory and simulation.
- **Relevance:** This is the closest classical ancestor of (a). It has no quantum phase, no superposition and no encoding by rail.

## 2. Wustmann & Osborn, Phys. Rev. Applied 25 (2026): confirmed, except the article number
W. Wustmann, K. D. Osborn, "Rapid qubit readout dependent on the transmission of a single fluxon," *Phys. Rev. Applied* 25 (2026), doi:10.1103/lq5c-3j66, online 20 Jan 2026 according to Paperguide/OpenAlex. The preprint is arXiv:2504.18915, "Simulation of a rapid qubit readout…" (v1 April 2025, v2 December 2025; read).
- **Article number 034027 is not verified.** No tool showed it, and a 20 January online date would normally mean issue 1.
- **What it shows:** A fluxonium is galvanically coupled to the interface between two discrete LJJs. A ballistic fluxon is reflected for one qubit state and transmitted, after several bounces, for the other. Readout takes under 1 ns (T_M ≈ 0.33 ns) with about 0.1% back-action. Results come from circuit simulations and a three-coordinate model treated in a mixed quantum-classical (Born-Oppenheimer) approximation.
- **Status:** theory and simulation.
- **Relevance:** The fluxon is used only as a measurement probe. The paper discusses fluxon quantum fluctuations (β² = 0.4), but proposes no fluxon qubit and no gate.

## 3. US 9,812,836: confirmed, claims not read
K. D. Osborn, "Reversible computation with flux solitons," US 9,812,836. Filed 12 Nov 2014 and granted 7 Nov 2017. The assignee is the National Security Agency according to a Justia listing found by web search; I did not see the front page.
- **What it claims (abstract):** Discretised-LJJ transmission lines carry a control fluxon when an input is active and a target fluxon launched at the same time. If the control fluxon is present, the interaction steers the target into a third line. Otherwise the target follows an "adiabatic trajectory" into a fourth line.
- **Status:** patent for classical reversible logic.
- **Relevance:** This is the closest patent to (a) and (b). It is classical which-rail switching by a fluxon-fluxon interaction, not a phase gate on superpositions.
- **Related classical patents (titles from search listings):** US 10,778,229 B1 (Osborn, Wustmann); US 12,166,259 B1 (NSA); Sandia US 11,289,156 B2 and US 12,620,993 B1.

## 4. Classical fluxon collisions and coupled LJJs
- S. Sakai, P. Bodin, N. F. Pedersen, *J. Appl. Phys.* 73, 2411 (1993), doi:10.1063/1.353095. The standard model of inductively coupled sine-Gordon equations for stacked junctions.
- R. Kleiner, *PRB* 50, 6919 (1994), doi:10.1103/PhysRevB.50.6919. Coherent vortex motion in stacks.
- A. V. Ustinov, "Solitons in Josephson junctions," *Physica D* 123, 315 (1998), doi:10.1016/S0167-2789(98)00131-6. Review article.
- Y. S. Kivshar, B. A. Malomed, *PRB* 37, 9325 (1988), doi:10.1103/PhysRevB.37.9325. Collisions between fluxons in *different* coupled junctions.
- N. Grønbech-Jensen et al., *PRB* 50, 6352 (1994), doi:10.1103/PhysRevB.50.6352. Both inductive and capacitive coupling; bunched fluxon states whose stability depends on velocity.
- A. V. Ustinov, H. Kohlstedt, *PRB* 54, 6111 (1996), doi:10.1103/PhysRevB.54.6111. Experiment: fluxons in neighbouring layers repel at low velocity and attract at high velocity.
- A. Fujimaki et al., *PRL* 59, 2895 (1987), doi:10.1103/PhysRevLett.59.2895, and K. Nakajima et al., *PRL* 65, 1667 (1990), doi:10.1103/PhysRevLett.65.1667. Measured fluxon-antifluxon collisions; the collision phase shifts came out negative, which the authors attribute to dissipation.

**Status:** all classical. **Relevance:** These give the collision physics, inter-rail forces that depend on velocity, and combined inductive and capacitive coupling, which together are the classical basis for (a) and (d). None deals with a quantum conditional phase.

## 5. Quantum sine-Gordon scattering
- A. B. Zamolodchikov, Al. B. Zamolodchikov, *Ann. Phys.* 120, 253 (1979), doi:10.1016/0003-4916(79)90391-9. The exact soliton S-matrix of the sine-Gordon model (theory).
- A. Roy, H. Saleur, "Quantum electronic circuit simulation of generalized sine-Gordon models," *PRB* 100, 155425 (2019), doi:10.1103/PhysRevB.100.155425 (theory).
- A. Roy, D. Schuricht, J. Hauschild, F. Pollmann, H. Saleur, "The quantum sine-Gordon model with quantum circuits," *Nucl. Phys. B* 968, 115445 (2021), doi:10.1016/j.nuclphysb.2021.115445 (DMRG numerics).
- I. T. Rosen et al., arXiv:2610.11071 (Oct 2026). A proposed superconducting line that would collide kinks and antikinks in real time (theory).

**Relevance:** Exact soliton scattering gives two-body phases that depend on the rapidity difference. That is the source both of a collision phase and of its Wigner delay. Superconducting circuits have been proposed only as simulators of this scattering, never as gates.

## 6. Quantum fluxon tunnelling and interference
- A. Wallraff et al., *Nature* 425, 155 (2003), doi:10.1038/nature01826. Experiment: quantised energy levels and tunnelling of a single vortex in an LJJ.
- S. S. Seidov, M. V. Fistul, *PRA* 103, 062410 (2021), doi:10.1103/PhysRevA.103.062410. Theory: a fluxon tunnels coherently between neighbouring cells of a high-kinetic-inductance array, forming energy bands. In annular arrays the Aharonov-Casher phase gives gate-voltage control.
- M. M. Wildermuth, "Quantum Tunneling of Josephson Vortices in High-Impedance Long Junctions," KIT dissertation (2023), doi:10.5445/IR/1000158804. Experiment: according to the abstract, a single vortex tunnelling coherently forms a "Josephson vortex quantum bit", with Rabi oscillations and coherence times in the microsecond range. Related paper: Wildermuth et al., *APL* 120, 112601 (2022), doi:10.1063/5.0082197.
- W. J. Elion, J. J. Wachters, L. L. Sohn, J. E. Mooij, *PRL* 71, 2311 (1993), doi:10.1103/PhysRevLett.71.2311. Experiment: Aharonov-Casher interference of vortices around a doubly connected path.
- H. S. J. van der Zant, F. C. Fritschy, T. P. Orlando, J. E. Mooij, "Ballistic vortices in Josephson-junction arrays," *EPL* 18, 343 (1992), doi:10.1209/0295-5075/18/4/011. Experiment: a classical beam of vortices in a 2D array.
- Quantum vortices in 1D arrays: A. van Oudenaarden, J. E. Mooij, *PRL* 76, 4947 (1996), doi:10.1103/PhysRevLett.76.4947.
- Also: I. N. Moskalenko et al., *PRB* 103, 224528 (2021), on fluxon quantum beats between two cells; the authors note that coherent dynamics of "flying" excitations is unexplored. Pop et al., *PRB* 85, 094503 (2012), on Aharonov-Casher interference of quantum phase slips.

**Relevance:** The quantum regime for fluxons, and inter-cell tunnelling through quantum phase slips, are established. That tunnelling is the elementary process behind (c). I found no beam splitter between ladder rails and no interferometer for a moving vortex.

## 7. Entangling flying qubits
- **Microwave photons (experiments):** P. Kurpiers et al., *Nature* 558, 264 (2018), doi:10.1038/s41586-018-0195-y; C. J. Axline et al., *Nat. Phys.* 14, 705 (2018), doi:10.1038/s41567-018-0115-y; P. Campagne-Ibarcq et al., *PRL* 120, 200501 (2018), doi:10.1103/PhysRevLett.120.200501. All three show deterministic transfer or remote entanglement using travelling photons, with fidelities of about 73–80%.
- A. Bertoni, P. Bordone, R. Brunetti, C. Jacoboni, S. Reggiani, *PRL* 84, 5912 (2000), doi:10.1103/PhysRevLett.84.5912. Simulation of dual-rail electrons in two tunnel-coupled wires; the Coulomb interaction gives a CNOT gate.
- R. Ionicioiu, G. A. J. Amaratunga, F. Udrea, *IJMPB* 15, 125 (2001), doi:10.1142/S0217979201003521. Theory of ballistic-electron flying qubits.
- **Recent flying-electron experiments (Coulomb interaction seen, no entangling gate shown):**
  - J. D. Fletcher et al., *Nat. Nanotechnol.* (2023), doi:10.1038/s41565-023-01369-4: time-resolved Coulomb collision of counter-propagating electrons.
  - N. Ubbelohde et al., *Nat. Nanotechnol.* (2023), doi:10.1038/s41565-023-01370-x.
  - J. Wang et al., *Nat. Nanotechnol.* (2023), doi:10.1038/s41565-023-01368-5: electrons carried by surface acoustic waves through coupled quantum rails.
- **General collision gates (theory):** S. Bose, V. Korepin, arXiv:1106.2329 (2011), and L. Banchi et al., *Quantum* 1, 36 (2017), doi:10.22331/q-2017-11-30-36, derive controlled-Z-type gates from collisions of counter-propagating particles. D. J. Brod, J. Combes, *PRL* 117, 080502 (2016), doi:10.1103/PhysRevLett.117.080502, use counter-propagating photons through distributed cross-Kerr sites to suppress spectral entanglement.

**Relevance:** Bertoni et al. is the closest template for (a)–(c), but in electrons.

## 8. Fluxon-mediated gates from the Hatakenaka group (theory)
- S. Matsuo, K. Furuta, T. Fujii, K. Nagai, N. Hatakenaka, *APL* 91, 093103 (2007), doi:10.1063/1.2772770. A moving fluxon tunes a switch qubit into resonance and so gates two stationary qubits.
- T. Fujii, S. Matsuo, N. Hatakenaka, "Quantum knitting computer," arXiv:0905.2246 (2009) (read). A single fluxon passing a zigzag chain of flux qubits gives joint-phase-plus-SWAP gates and error correction. The fluxon is a classical "carriage", not a qubit.
- T. Fujii, S. Matsuo, N. Hatakenaka, "Fluxon-controlled quantum computer," *IJQI* 14, 1650040 (2016), doi:10.1142/S0219749916500404.
- **Closer to QBF-X2:**
  - T. Fujii, T. Shibata, M. Nishida, N. Hatakenaka, "Flying superconducting qubits," *IEEE TAS* 17, 97 (2007), doi:10.1109/TASC.2007.898035. I have only the abstract: a flying qubit made from an "elementary excitation" in circuits with JTLs, with logic gates. **The full text was not read; obtain it.**
  - T. Fujii, M. Nishida, N. Hatakenaka, *PRB* 77, 024505 (2008), doi:10.1103/PhysRevB.77.024505: a quantum breather (a bound fluxon-antifluxon pair) used as a mobile qubit.

**Relevance:** Mobile soliton qubits have been proposed, but they encode the qubit in internal energy levels. None of the abstracts shows dual-rail encoding or a gate from a fluxon-fluxon collision.

## 9. Nambisan et al., Nature 2026: confirmed
A. Nambisan, S. Günzler, D. Rieger, …, M. Spiecker, I. M. Pop, "Quantum coherent manipulation and readout of superconducting vortex states," *Nature* 653, 63–67 (2026), doi:10.1038/s41586-026-10441-7; arXiv:2510.19769 (v1 read).
- **What it shows:** Vortices pinned in a granular-aluminium resonator behave as qubits: f_q ≈ 2 GHz, g/2π = 92.5 MHz, T1 = 186 µs (range 40–300 µs), T2* = 440 ns, T2 echo = 1.2 µs, quantum non-demolition readout.
- **The 10–100 MHz figure is confirmed.** The v1 text says "We estimate the VQ-VQ interaction in the 10–100 MHz range (cf. App. I)". I did not check whether the Nature version keeps that wording.
- **Status:** experiment.
- **Relevance:** It supports coherent vortex states with couplings of tens of MHz, but these are static Pearl vortices, not flying Josephson fluxons.

## 10. Searches aimed directly at QBF-X2's novelty
- **Gates from a coherent two-fluxon collision: none found.** The nearest are items 1, 3 and 4, plus:
  - M. V. Fistul, A. V. Ustinov, *PRB* 68, 132509 (2003), doi:10.1103/PhysRevB.68.132509: vortex-vortex coupling mediated by cavity modes, proportional to the product of the fluxon velocities, proposed for entangling *trapped* vortex qubits.
  - US 6,627,915 B1 (Ustinov, Walraff [sic], Koval; D-Wave; 2003): static LJJ vortex qubits coupled magnetically.
- **Dual-rail flying fluxon qubits: none found.** The nearest is Q. Deng, D. V. Averin, "nSQUID arrays as conveyers of quantum information," *JETP* (2014) 1152–1162, doi:10.1134/S1063776114120012 (read). The array is described as an "effective dual-rail" structure, but the qubit sits in a differential mode carried by a *classical* fluxon. Quantum motion of the fluxon is left as future work.
- **Quantum vortex beam splitters or interferometers in ladders: none found.** The nearest are the works in item 6, plus the classical "Josephson vortex interferometer" detector of I. I. Soloviev et al., *APL* 105 (2014), doi:10.1063/1.4902327.
- **Conditional phase made insensitive to velocity (inductive plus capacitive coupling, zero conditional Wigner delay): none found.** Related: Grønbech-Jensen 1994 and Ustinov & Kohlstedt 1996; Fistul & Ustinov 2003; Brod & Combes 2016; Banchi et al. 2017; and A. G. Semenov et al., arXiv:2505.06720 (2025) on fluxon cotunnelling in capacitively coupled junctions.
- **Other patents:** Only readout (US 8,508,280 B2, "Qubit readout via resonant scattering of Josephson solitons"; assignee not verified) and classical ballistic logic surfaced.

## Novelty verdict

| Element | Closest prior art | What it already covers | What it does not cover | Verdict |
|---|---|---|---|---|
| (a) CZ gate from colliding fluxons | US 9,812,836; Wustmann & Osborn 2020; Kivshar & Malomed 1988; Fistul & Ustinov 2003; Bertoni 2000; Bose & Korepin / Banchi | Classical two-fluxon interaction gates; collisions in coupled LJJs; coupling of trapped vortex qubits; collision CZ gates for electrons and atoms | A coherent collision of two flying *quantum* fluxons giving a conditional phase across rails A1/B1 | partially anticipated |
| (b) Dual-rail fluxon qubit | Deng & Averin 2014; Fujii 2007/2008; US 9,812,836; Bertoni 2000 | Qubits carried by moving fluxons or breathers; a dual-rail array; classical encoding by output line; dual-rail electrons | One fluxon in a superposition of two rails as the logical qubit | partially anticipated |
| (c) Fluxon beam splitter / Mach-Zehnder | Seidov & Fistul 2021; Moskalenko 2021; Wildermuth 2023; Elion 1993; Pop 2012 | Coherent inter-cell tunnelling through quantum phase slips; Aharonov-Casher interference of vortices | A moving vortex tunnelling between ladder rails, used as a beam splitter or interferometer | partially anticipated (the mechanism is known; the device was not found) |
| (d) Conditional phase stationary in velocity | Grønbech-Jensen 1994; Ustinov & Kohlstedt 1996; Fistul & Ustinov 2003; Brod & Combes 2016 | Combined inductive and capacitive coupling (classical); interactions that depend on velocity; the problem of timing information in flying-qubit gates | Designing φ_c(v) = a/v + b·v so that dφ_c/dv = 0 | not found in searched sources |
| Overall QBF-X2 architecture | Fujii et al. 2007 (unread); Bertoni 2000 (electron analogue) | Each ingredient, or an analogue on another platform | The integrated flying-quantum-fluxon architecture with dual rails, ladder beam splitter, collision CZ and velocity compensation | not found in searched sources |

## Tools used, and queries that returned nothing
- **Lune:** search_papers_many was refused (free-plan quota). My one search_papers query on collision gates between solitons or fluxons returned only irrelevant computer-science papers.
- **alphaXiv:** discover_papers and answer_pdf_queries; full texts read are listed above.
- **SciSpace, Valency, Paperguide:** most DOI checks were done here.
- **Undermind:** an existing completed deep search, "Quantum fluxon qubits and ballistic fluxon coherent control prior art", plus search_papers ×2 and get_paper_info.
- **WebSearch:** about 20 queries, including patents. WebFetch was blocked for every host tried.
- **Queries with no relevant hit:**
  - Patent queries on "fluxon flying qubit / entangling gate / collision".
  - "dual-rail fluxon flying qubit".
  - Patents on vortex qubits in granular aluminium or high-kinetic-inductance arrays.
  - Valency: a vortex beam splitter or Mach-Zehnder in a ladder.
  - Valency: inductive and capacitive fluxon interaction cancelling at a critical velocity.
  - Valency: a velocity-insensitive conditional phase between flying qubits (photonic hits only).
  - Undermind: controlled-Z from colliding fluxons, and the ladder beam splitter.
  - The full text of Fujii et al. 2007.
  - The article number 034027.
