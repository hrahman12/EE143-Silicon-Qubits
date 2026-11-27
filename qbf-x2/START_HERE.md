# QBF-X2: start here

This is the orientation file for a reader picking the project up cold, human or AI. Paths are relative to the
`qbf-x2/` folder. The exact commit of a bundle is recorded in `BUNDLE_MANIFEST.json`, next to this file at the bundle
root.

## What this is

QBF-X2 is a proposed superconducting chip. Two **quantum fluxons** (Josephson vortices: 2π kinks of the
superconducting phase, each carrying one flux quantum) fly in opposite directions along coupled Josephson-junction
array rails and pass each other.

- Each fluxon is a **dual-rail flying qubit**: |0⟩ means the fluxon is in rail 0, |1⟩ in rail 1. Beam splitters made
  of phase-slip junctions put it in a superposition of the two rails.
- Only the rail-1 lines of the two qubits are coupled. So only the |11⟩ branch picks up a collision phase Δ, and with
  Δ = π the collision is a **CZ gate**.

Everything here is theory, simulation and design. **Nothing has been fabricated or measured.**

## Read in this order

1. This file.
2. `README.md`: the full technical overview, the results table and the limits.
3. `FEASIBILITY.md`: validated vs proposed vs open; the parameter table; the error budget; cryogenic requirements; a
   staged measurement protocol.
4. `NOVELTY.md`: prior art, and exactly what is and is not claimed. The full search report is
   `results/prior_art_report.md`.
5. Key figures:
   - `figures/fig05_phase_vs_coupling.png`: Δ reaches π exactly where the concurrence reaches 1;
   - `figures/fig07_fidelity_vs_timing.png`: gate fidelity vs launch-time mismatch;
   - `figures/fig12_error_budget.png`: the error budget by source;
   - `figures/fig03_joint_probability.png`: the two-fluxon collision.
6. `paper/main.pdf`: the long write-up. **It is out of date for milestone D**: it predates the coherent launcher, the
   beam-splitter redesign and the rev-B differential lines. Where it disagrees with `README.md` or `FEASIBILITY.md`,
   those two files are current.

## The core idea: the velocity sweet spot

A plain inductive coupler gives a conditional phase ∝ 1/v. That has two costs:
- a conditional time delay, which leaks which-path information;
- sensitivity to the spread in launch speed.

QBF-X2 adds a capacitive coupler, whose phase for counter-propagating fluxons grows ∝ v. Together they give

    Δ(v) = (2π)² (E_J / h f_p) [Λ² k̃ / (2v) + c v / 2],    stationary at  v* = Λ (k̃ / c)^½

At v* the conditional delay vanishes and speed spread enters only at second order. Here k̃ = k/(1−k²), k is the
per-cell mutual-inductance fraction and c the per-cell coupling-capacitance fraction.

## Status at a glance

| Milestone | Verdict | Where the checks live |
|---|---|---|
| A. Classical ballistic physics | PASS | `results/A_classical.json` → `milestone_A` |
| B. Quantum ballistic physics | PASS | `results/B_quantum.json` → `milestone_B` |
| C. Genuine quantum gate | PASS | `results/C_gate.json` → `milestone_C` |
| D. Device feasibility | **NOT MET: 7 of 9 checks pass** | `results/D_feasibility.json` → `milestone_D` |

The two open D checks:
- The layout must be re-verified after the beam-splitter redesign. DRC finds 608 known violations: the middle-rail
  junction is drawn 86 nm wide against a 100 nm rule, and the fix is a 114 nm square.
- The 10 mm die floorplan is unfinished; its partial code is in `wip/`.

**Test suite** (41 tests): 38 pass and 2 are expected failures, marked `xfail(strict=True)` in the code with their
reasons. One fails: `tests/test_extraction.py::test_extraction_gate_quantities_pass`. It fails for the same open
layout item. The layout has not been redrawn for the redesigned beam splitter, so:
- DRC is not clean;
- the drawn middle junction is off target: C_M 0.95 vs 2.87 fF, E_C,M 20.4 vs 6.7 GHz, E_S 3.6 vs 0.58 GHz
  (`circuits/extraction.json`).

The full suite takes about 4 minutes.

## Headline numbers and their sources

All of these are simulated.

| Quantity | Value | Source |
|---|---|---|
| Concurrence from \|+⟩\|+⟩ (pure wavepackets, exact 2D scattering) | 1.000000 | `C_gate.json` → `milestone_C` |
| Bell fidelity / CZ average gate fidelity | 0.999999 / 0.999999 | same |
| Conditional phase Δ | 3.1432 rad (π + 0.0016) | same |
| Leakage (reflection or loss of a fluxon) | 6.2×10⁻⁸ | same |
| Control run, coupler off: concurrence | 2.1×10⁻⁸ | same |
| Thermal launch at 20 mK: intrinsic gate error at the sweet spot / inductive-only coupler | 1.2×10⁻⁵ / 3.8×10⁻³ | same |
| Sweet spot β*: classical circuit / quantum 2D (design 0.300) | 0.302 / 0.293 | `A_classical.json`, `B_quantum.json` → `classical_sweet_spot_beta`, `quantum_sweet_spot_beta` |
| Operating point | β = 0.45, k = 0.01778, c = 0.0875 | `C_gate.json` → `optimum_validation` |
| Launch speed spread (rms dv/v), coherent launcher / thermal source, 20 mK | 1.02 % / 4.29 % | `D_launcher.json` → `quantum_launch_20mK`, `budget_*.velocity_spread_rel` |
| Gate error budget: launcher as designed / as drawn (post-layout) / thermal source | 0.32 % / 0.90 % / 2.36 % | `D_launcher.json` → `budget_launcher`, `post_layout.budget`, `budget_thermal_source` |
| 2D gate with the as-drawn launched packets: CZ process fidelity, Δ, leakage | 0.9978, 3.1371 rad, 1.8×10⁻³ | `D_launcher.json` → `post_layout.gate_with_as_drawn_packets` |
| Damping needed for < 1 % gate error | α ≤ 1.2×10⁻⁵ (2×10⁻⁶ assumed) | `FEASIBILITY.md` §2 |
| Junction disorder tolerated (< 1 % gate error, with the launcher) | up to 5.7 % (2 % assumed) | `FEASIBILITY.md` §2 |
| Carrier PCB (rev B) | DRC clean; 0 schematic-vs-PCB mismatches; Z_diff 95.8 Ω (2D field solve); intra-pair skew ≤ 0.0011 ps | `pcb/README.md`, `pcb/reports/` |

## What is not validated (the weak points)

These are the places most worth attacking.

1. **Damping.** α must be ≤ 1.2×10⁻⁵ at 20 mK; 2×10⁻⁶ is assumed. The damping estimate does not yet include
   dielectric loss in the SiNx crossover layer, and the damping term is an upper bound: each emitted plasma quantum
   is counted as which-rail information.
2. **Beam splitter.** Vortex hopping between rows uses a single-junction phase-slip estimate with network-loaded E_C
   (E_J,M = 13.5 GHz, E_S = 0.58 GHz, 77-cell beam splitters). Coherent hopping of a *moving* vortex has not been shown,
   and the islands' offset-charge stability is not modelled.
3. **Model validity.** The quantum model is a first-order collective-coordinate theory, checked against the classical
   circuit. It holds for roughly β ≈ 0.22 to 0.35 (inductive coupling) or 0.45 (mixed). **The operating point β = 0.45
   sits at the upper edge**; the circuit's zero crossing at β = 0.454 supports it there. Plasmon emission is
   estimated classically.
4. **Electromagnetics.** k, c, L, C_M and E_S come from a 2D cross-section extraction, not a full-wave solver (no HFSS,
   Sonnet or Palace). The circuit model has not been cross-checked in JoSIM or WRspice.
5. **Not modelled at all:**
   - preparing the launched fluxon's motional state beyond the trap model;
   - quasiparticles and 1/f noise beyond the damping estimate;
   - common-mode rejection at the package;
   - transient coupling between the trap loop and the accelerator loop.
6. **Novelty.** The prior-art search was a literature search run by an AI agent. There has been no patent search, and
   the full text of Fujii et al., *IEEE TAS* **17**, 97 (2007) is still unread. Treat "not found in the sources
   searched" as exactly that.

## Reproducing

```bash
pip install -r requirements.txt   # Python 3.11+; pinned versions inside
python -m pytest                  # the suite described above
./run_all.sh                      # every simulation, figure, circuit file and the paper: ~45 min on 4 cores
```

Each stage writes `results/<stage>.json` together with its acceptance checks. To run one stage:
`cd simulations && python C_gate.py`. The stages are:
- `A_classical.py`, `B_quantum.py`, `C_gate.py`;
- `D_launcher.py`, `D_feasibility.py` (about 20 min), `D_diffpairs.py`;
- `fig12_error_budget.py`;
- `companions/c1_bell_pair.py` … `companions/c5_qec.py`.

Two files from the repository's earlier QFX-1 project are read by QBF-X2. In a bundle they sit at
`../quantum_chip/out/qfx_sim.json`, used by companion 1, and `../quantum_chip/src/rf_calc.py`, the CPW impedance
formula used by the carrier scripts. The rest of that project, about 290 MB of CAD and renders, is not needed here.

`requirements.txt` covers the simulations and the core tests. Three optional tools are not on PyPI:
- KiCad 7 (`kicad-cli` and the `pcbnew` module) with `cadquery-ocp`, for the carrier scripts and
  `tests/test_carrier.py`;
- the altium-designer-mcp binary (set `ALTIUM_MCP_BIN`), for `tests/test_altium_libs.py`;
- Blender with `bpy`, for the nanoscale 3D render.

The two tests skip when their tools are missing, so a plain Python environment reports 2 skipped.

`simulations/D_diffpairs.py` reads the rev-A sizing from git history for its before/after comparison. Outside a git
checkout it records that comparison as unavailable; the committed `results/D_diffpairs.json` still holds it.

Note that `tests/test_altium_libs.py` rewrites `pcb/altium/QBFX2_Carrier.PcbLib` and `.SchLib` in place, leaving
timestamped `.bak` copies; the libraries' content is unchanged.

## Map

```
src/classical/      discrete sine-Gordon circuit model with mutual-L and C couplers; exact sine-Gordon results
src/quantum/        collective-coordinate quantum model of one and two fluxons
src/scattering/     1D/2D split-operator propagation, collision driver, first-order (eikonal) S-matrix, launcher
src/gates/          logical channel from motional overlaps; concurrence, Bell and CZ fidelities
src/optimization/   error budget (launch spread, disorder, damping, timing, coupler) and operating-point search
src/hardware/       parameters, architecture, netlist, GDS layout, DRC, 2D extraction, launcher, differential pairs
simulations/        milestone scripts A–D, the fig12 script, companions/ (five side devices)
results/            one JSON per stage with every number and its acceptance checks; prior_art_report.md
figures/            fig01–fig12 and companion1–5
circuits/           qbfx2_layout.gds, qbfx2_netlist.cir, die_pads.json, block_ports.json, extraction.json,
                    views/ (layer views, Altium-style views, nanoscale views)
pcb/                KiCad 7 six-layer carrier (rev B), fab outputs (Gerbers, drill, BOM, STEP, PDFs), checks and
                    reports, altium/ (native libraries and views)
paper/              main.tex, main.pdf (out of date for milestone D; see above)
tests/              pytest suite
wip/                unfinished: second-pass layout, extraction and DRC; die floorplan
```

## Glossary

- **β** (speed): v / c0, where c0 = Λ ω_p is the array's maximum fluxon speed in cells per unit time. Do not confuse
  it with the quantum sine-Gordon coupling **β² = 0.51**, which measures how quantum the fluxon is (its rest energy is
  15.8 plasma quanta).
- **Λ = 2.5:** the Josephson length in cells.
- **Rail junctions:** E_J/h = 40 GHz (I_c ≈ 80 nA) and E_C/h = 8 GHz.
- **Rails** are named D_A, A0, A1, B1, B0, D_B.
  - The gate coupler joins A1 and B1.
  - Identical dummy couplers join A0 to D_A and B0 to D_B. D_A and D_B carry no fluxon; the dummy couplers cancel
    single-particle phases and delays between the rails.
- **k̃, c:** the coupler's inductive and capacitive strengths per cell. **Δ:** the conditional (collision) phase.
- **E_S:** the beam-splitter phase-slip (hopping) amplitude. **α:** the dimensionless sub-gap damping.
- **Launcher.** A flux-bias trap (3 GHz) holds the fluxon in its motional ground state. A flux-gradient accelerator
  then shears its phase space, which gives a speed spread well below thermal. Both are driven by floating
  differential control loops (rev B), coupled by mutual inductance only.

## Suggested tasks for a reviewer

1. Re-derive Δ(v) from the circuit Lagrangian and check the sweet spot. Then judge whether the first-order model can
   be trusted at β = 0.45 (`src/classical/`, `src/scattering/eikonal.py`, `results/A_classical.json`
   `first_order_accuracy`).
2. Audit the error budget in `src/optimization/budget.py`. Is disorder dephasing ∝ (dv/v)² right? Is the damping
   bound sound? What is missing: TLS loss in SiNx, quasiparticles, flux noise on the trap?
3. Judge the beam splitter: can a moving vortex hop coherently between rows through a middle-junction phase slip?
   What would destroy the coherence?
4. Check the prior art, starting with Fujii et al. (2007); Wustmann and Osborn, *PRB* **101**, 014516 (2020);
   Osborn's reversible-fluxon patents; and dispersion-free conditional phases in flying-electron and photon
   collisions.
5. Propose the cheapest experiment that could falsify the approach. Candidates from `FEASIBILITY.md` §7:
   - time-of-flight statistics of one launched fluxon: the launcher predicts 1.0 % against 4.3 % thermal;
   - the classical sweet-spot arrival-time shift;
   - a single-fluxon Mach–Zehnder interferometer.
6. Bring `paper/main.tex` up to date with `README.md` and `FEASIBILITY.md`.

## Provenance

Developed in November 2026 in Claude Code sessions with the project owner. The code, simulations, layout, PCB and
text were produced with heavy AI assistance. They are checked by the test suite and by internal consistency checks,
but **no independent human expert has reviewed them**. Treat every result as unreviewed until it is checked.
