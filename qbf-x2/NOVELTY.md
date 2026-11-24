# QBF-X2: established physics vs. what this project proposes

**Bottom line.**
- Every physical ingredient of QBF-X2 is established or has been proposed before.
- The prior-art search found no earlier example of two pieces:
  - the combination: two *flying quantum fluxons*, dual-rail encoded, entangled by a coherent collision, with ladder beam splitters;
  - the **velocity-sweet-spot coupler**, which makes the conditional phase stationary in fluxon speed and so removes the
    which-path timing information.
- That is a statement about what the searched sources contain. It is **not** proof of novelty: a patent search and a
  full-text review are still needed before claiming a first invention.

The search was run in November 2026, by a research agent using Undermind, alphaXiv, SciSpace, Valency, Paperguide,
Lune and web/patent search.
- Unavailable: Consensus (quota), Scite (paid plan), Elicit (no API access) and Scholar Gateway (access denied).
- Patent claims could not be read: patent pages were blocked, so patents are summarised from their abstracts.
- The full report is in `results/prior_art_report.md`.

## 1. What is established, and by whom

| Ingredient | Status | Key sources |
|---|---|---|
| Classical ballistic fluxon gates and fluxon–fluxon interaction gates | theory, numerical simulation and patents (classical reversible logic) | Wustmann & Osborn, *PRB* **101**, 014516 (2020); K. D. Osborn, US 9,812,836 "Reversible computation with flux solitons" (2017); related US 10,778,229, US 11,289,156, US 12,620,993 |
| Fluxon-transmission qubit readout | theory and simulation | Wustmann & Osborn, *Phys. Rev. Applied* **25** (2026), doi:10.1103/lq5c-3j66, arXiv:2504.18915; the article number 034027 given in the brief could not be verified |
| Collisions of fluxons in coupled / stacked long junctions; inductive **and** capacitive coupling; interactions that depend on velocity (repulsion at low speed, attraction at high speed) | classical theory and experiment | Sakai, Bodin & Pedersen, *J. Appl. Phys.* **73**, 2411 (1993); Kivshar & Malomed, *PRB* **37**, 9325 (1988); Grønbech-Jensen et al., *PRB* **50**, 6352 (1994); Ustinov & Kohlstedt, *PRB* **54**, 6111 (1996); Ustinov, *Physica D* **123**, 315 (1998) |
| Exact quantum soliton scattering, including two-body phases that depend on rapidity | theory | Zamolodchikov & Zamolodchikov, *Ann. Phys.* **120**, 253 (1979); Roy & Saleur, *PRB* **100**, 155425 (2019); Roy et al., *Nucl. Phys. B* **968**, 115445 (2021); Rosen et al., arXiv:2610.11071 (2026) |
| Quantum fluxons: level quantisation, tunnelling, coherent tunnelling bands, vortex qubits | experiment and theory | Wallraff et al., *Nature* **425**, 155 (2003); Seidov & Fistul, *PRA* **103**, 062410 (2021); M. M. Wildermuth, KIT thesis (2023), doi:10.5445/IR/1000158804; Nambisan et al., *Nature* **653**, 63 (2026) |
| Vortex interference and quantum phase slips (the elementary process behind our beam splitter) | experiment | Elion et al., *PRL* **71**, 2311 (1993); van Oudenaarden & Mooij, *PRL* **76**, 4947 (1996); Pop et al., *PRB* **85**, 094503 (2012); Moskalenko et al., *PRB* **103**, 224528 (2021) |
| Mobile soliton qubits and fluxon-mediated gates on stationary qubits | theory | Fujii et al., "Flying superconducting qubits", *IEEE TAS* **17**, 97 (2007) (only the abstract was read; high-priority follow-up); Fujii et al., *PRB* **77**, 024505 (2008); Matsuo et al., *APL* **91**, 093103 (2007); Fujii, Matsuo & Hatakenaka, arXiv:0905.2246 (2009); Deng & Averin, *JETP* (2014) |
| Dual-rail flying qubits entangled by an interaction while in flight | simulation and experiment in other platforms | electrons: Bertoni et al., *PRL* **84**, 5912 (2000); Ionicioiu et al. (2001); Coulomb collisions of flying electrons: Fletcher et al., Ubbelohde et al., Wang et al., *Nat. Nanotechnol.* (2023). Collision gates and spectral entanglement: Bose & Korepin (2011); Banchi et al., *Quantum* **1**, 36 (2017); Brod & Combes, *PRL* **117**, 080502 (2016) |
| Entangling flying superconducting qubits with photons | experiment | Kurpiers et al., *Nature* **558**, 264 (2018); Axline et al., *Nat. Phys.* **14**, 705 (2018); Campagne-Ibarcq et al., *PRL* **120**, 200501 (2018) |

## 2. What QBF-X2 adds (not found in the sources searched)

1. **A quantum two-fluxon collision gate.** Two flying fluxons, each a quantum particle (soliton-to-plasmon energy
   ratio 15.8, quantum sine-Gordon coupling β² = 0.51), pass each other on coupled rails. They acquire a conditional
   phase of π that entangles two dual-rail qubits.
   - The classical analogue (US 9,812,836; Wustmann & Osborn 2020) uses the interaction to *switch which line a
     fluxon leaves on*. Here the interaction makes a *phase* on superpositions.
   - Verdict: partially anticipated (the classical gates; collision gates on other platforms).
2. **Dual-rail flying-fluxon encoding.** One fluxon in a superposition of two ladder rows is the logical qubit.
   - Nearest prior art: mobile qubits carried by solitons or breathers (Fujii 2007/2008), and the nSQUID "effective
     dual-rail" conveyor (Deng & Averin 2014), which uses a classical fluxon.
   - Verdict: partially anticipated.
3. **A beam splitter between ladder rows.** A moving vortex hops between rows by a phase slip of a middle-rail
   junction; together with a gate-controlled Aharonov–Casher phase this gives a coherent fluxon router.
   - The underlying mechanism (quantum phase slips, vortex Aharonov–Casher interference) is established. The device,
     a beam splitter or interferometer for a flying vortex, was not found.
   - Verdict: partially anticipated.
4. **The velocity-sweet-spot coupler.**
   - *Mechanism:* inductive coupling gives a conditional phase ∝ 1/v; capacitive coupling of counter-propagating
     fluxons gives one ∝ v. With both, Δ(v) = A/v + B·v is stationary at v* = (A/B)^½.
   - *Consequence:* at v* the conditional Wigner delay vanishes. The fluxons carry no which-path timing information,
     and a thermal spread in launch speed affects the gate only at second order.
   - *Related work:* the classical velocity dependence of such interactions is known (Grønbech-Jensen 1994; Ustinov &
     Kohlstedt 1996), and spectral entanglement in photon collisions has been addressed with distributed nonlinear
     sites (Brod & Combes 2016). Using the two couplings to null the conditional delay was not found.
   - Verdict: **not found in the sources searched.**

**Status of every result here:** it comes from simulation in this repository and has not been measured.

## 3. What this project does *not* claim

- Not that fluxon qubits, fluxon readout, fluxon-mediated gates or flying-qubit collision gates are new; see section 1.
- Not that the chip has been built or would work as drawn. The layout is preliminary, and milestone D is **not met**:
  - a coherent single-fluxon launcher is unresolved;
  - junction disorder must be at or below about 1 % for a gate error under 1 %;
  - the coupler and beam-splitter values still need EM extraction.
- Not a thermodynamic advantage from unitary evolution (see `results/companion4_reversible_cell.json`).

## 4. Follow-up before any novelty or patent claim

1. Read the full text of Fujii, Shibata, Nishida & Hatakenaka, *IEEE TAS* **17**, 97 (2007), and its citations.
2. Do a professional patent search covering the claims of US 9,812,836, US 10,778,229, US 11,289,156, US 12,166,259
   and US 12,620,993, and the D-Wave vortex-qubit patent US 6,627,915.
3. Search the literature on collisions of flying electrons and photons for dispersion-free (velocity-compensated)
   conditional phases.
