# QBF-X2: a collision-powered entangling gate between two flying quantum fluxons

**QBF-X2** is a proposed superconducting chip in which two *quantum* fluxons travel in opposite directions and pass
each other on coupled Josephson transmission lines. They come out entangled.

- **Fluxons:** a fluxon is a Josephson vortex, a 2π kink of the superconducting phase that carries one flux
  quantum Φ0.
- **Encoding:** each fluxon is a dual-rail flying qubit: |0⟩ = fluxon in rail 0, |1⟩ = fluxon in rail 1.
- **Interaction:** only the rail-1 lines of the two qubits are coupled. So only the |11⟩ branch picks up the
  collision phase, and with the coupler set for Δ = π the collision is a CZ gate.
- **Status:** this repository derives, simulates and tests the physics and gives a *preliminary* chip design.
  Nothing here has been fabricated or measured.

> **Is it a quantum fluxon?** Yes. The rails are high-impedance junction arrays (E_J = 40 GHz, E_C = 8 GHz,
> Λ = 2.5) in which a fluxon's rest energy is only 15.8 plasma quanta (quantum sine-Gordon coupling β² = 0.51). The
> fluxon therefore behaves as a quantum particle with a 3 cell de Broglie wavelength, a coherent wavepacket and
> coherent superpositions of rails. It is **not** an SFQ pulse: a classical heavy fluxon (QFX-1's kick line, rest
> energy 213 THz·h) cannot carry a dual-rail qubit or become entangled.

## The idea that makes it work: the velocity sweet spot

**The problem.** A conditional phase from a plain inductive coupler scales as 1/v. That has two consequences:
- *Which-path information:* the |11⟩ fluxons come out *delayed* (Wigner delay τ = ħ ∂Δ/∂E), so their timing
  records which branch they took.
- *Thermal smearing:* any spread in launch speed (thermal at 20 mK) blurs Δ.

**The fix.** QBF-X2 adds a capacitive coupler. For counter-propagating fluxons it contributes a phase that grows ∝ v,
so the circuit Lagrangian gives

    Δ(v) = (2π)² (E_J/h f_p) [Λ² k̃ / (2v) + c v / 2],    stationary at  v* = Λ (k̃/c)^½

At v* the conditional delay vanishes, *classically and quantum mechanically*, and thermal speed spread enters only at
second order. Here k is the mutual-inductance fraction (k̃ = k/(1−k²)) and c the coupling-capacitance fraction,
both per cell.

- *Classical:* the full circuit simulation shows the conditional shift of each fluxon crossing zero at β = 0.302
  (first-order prediction 0.300).
- *Quantum:* the 2D scattering simulation puts the stationary point at β = 0.293.
- Prior-art status: see [NOVELTY.md](NOVELTY.md). This element was not found in the sources searched.

## Results (every number is produced by the scripts in `simulations/`)

| Milestone | Verdict | Evidence |
|---|---|---|
| **A** Classical ballistic physics | **PASS** | Energy conserved to 1.2×10⁻⁶. Exact sine-Gordon kink–antikink shift reproduced within 3.5 % (Λ = 10). Topological charge conserved. Collision radiation ≤ 2.2×10⁻⁴ of the kinetic energy. Conditional delay crosses zero at β = 0.302. |
| **B** Quantum ballistic physics | **PASS** | Norm conserved to 3×10⁻⁸. Phase converged to 7×10⁻⁴ rad (time step, momentum cut-off, domain, Taylor order). Reflection 7×10⁻⁸. Derived interaction within 0.8 % of a constrained relaxation of the full circuit. Quantum vs classical sweet spot 0.293 vs 0.302. |
| **C** Genuine quantum gate | **PASS** | From \|+⟩\|+⟩, exact 2D scattering gives concurrence **1.000**, Bell fidelity **0.999999**, CZ process fidelity **0.999999** and Δ = π (error 0.0017 rad). Motional (position–position) purity 0.999999, so the entanglement is logical, not motional. Thermal launch at 20 mK: gate error 1.2×10⁻⁵ at the sweet spot vs 3.8×10⁻³ with an inductive-only coupler. |
| **D** Device feasibility | **NOT MET (2 of 9 checks open)** | **Fixed:** the realistic error budget is **0.32 %** (< 1 %) with a modelled coherent launcher. Speed spread is 1.02 % vs 4.3 % thermal, and the 2D gate with launched packets has F_avg 0.9999999. The carrier PCB passes DRC, schematic-vs-PCB, impedance and length checks. **Open:** (1) layout re-verification for the redesigned beam splitter (the previous revision was DRC-clean, with every gate quantity within ±5 % and 3 open items); (2) the 10 mm die floorplan (unfinished, in `wip/`). |

**Milestone D status.** Fabrication disorder used to limit the device: a 1.9 % gate error, coming from a speed spread
assumed to be thermal.
- **The launcher.** `simulations/D_launcher.py` designs and simulates a coherent launcher.
  - A flux-bias trap holds the fluxon in its motional ground state at 20 mK. A flux-gradient accelerator then shears
    its phase space. Both are driven by control lines coupled by mutual inductance only, with no bias taps.
  - Rms speed spread: 1.02 % against 4.3 % for a thermal source, and 1.39 % at 100 mK.
  - Full-circuit launch: one fluxon at β = 0.4500, after a 1.5 % amplitude trim.
  - Relative timing jitter: 3.2 ps, with an assumed 2 ps trigger.
- **Error budget.** At the same assumptions (2 % disorder, 20 mK, 10 ps) the budget is 0.32 %; a thermal-source launch
  on the same geometry would give 2.37 %. The gate now tolerates up to 5.7 % junction disorder. Damping is the largest
  term and needs α ≤ 1.2×10⁻⁵.
- **Design errors found and fixed by the hardware checks.**
  - The rows were not symmetric about the coupler: B met the coupler before its own beam splitter.
  - The beam-splitter phase-slip amplitude was 8× optimistic, because the rail-junction network loads the middle
    junction. It was redesigned to E_J,M = 13.5 GHz, giving E_S = 0.58 GHz and 77-cell beam splitters.
- **Still open.**
  - The layout's second extraction pass for the redesigned beam splitter. The previous revision was DRC-clean, with
    k, c, L, L_s, C_M, E_S and the strays all within ±5 %. Its 3 open items were the outer-taper node capacitance, the
    mesh-converged plateau nodes and the launcher mutual inductances.
  - The die-level floorplan. Both were stopped unfinished; the partial code is in `wip/`.
  - `results/D_feasibility.json` predates these changes. The status above comes from `results/D_launcher.json`,
    `pcb/reports/` and `circuits/extraction.json`.

**Board and libraries.**
- `pcb/`: a complete KiCad 7 carrier — schematic, 6-layer Rogers board, DRC, Gerbers, BOM and STEP.
- `pcb/altium/`: native Altium `.PcbLib`/`.SchLib`/`.LibPkg`, written with altium-designer-mcp.

### Five companion devices (same codebase, one executed simulation each)

| # | Device | Result (simulated) | Verdict |
|---|---|---|---|
| 1 | Two-vortex Bell-pair chip (QFX-1 qubits, `../quantum_chip`) | Bell fidelity 0.9956 (T1 = 20 µs), 0.9976 (100 µs). Frequency-staggered double sweet spots; 6.6 ns exchange pulse | Works in simulation; no addressable entangled two-vortex processor was found in the literature |
| 2 | Coherent ballistic fluxon router | A fluxon is split, carried on two rails and recombined. Fringe contrast 0.9954 for a thermal launch at 20 mK, 0.9935 with 0.01e charge noise. Exit rail set by a gate voltage | Works in simulation; needs charge-stable beam-splitter islands |
| 3 | Reusable fluxon (mediator) gate | Conditional phase ≤ 0.077 rad and concurrence ≤ 0.04, even with overlapping couplers | **Negative result**: needs a coupling nonlinear in the qubit operators, or a mediator that is itself a qubit (as in QBF-X2) |
| 4 | Reversible quantum-fluxon logic cell | Kinetic energy retained through the gate 99.997 % (couplers + collision); regenerative braking returns 99.1–99.4 % of it to the bias supply (98.7 % at alpha = 1e-5); ~10⁻²¹ J per CZ on chip (estimate) | Recovery simulated, not measured; no thermodynamic advantage claimed |
| 5 | Fluxon QEC module | One syndrome-extraction cycle of a 3-qubit phase-flip code (density matrix). With a 10⁻³ CZ error it beats an unencoded qubit for memory errors of 1–10 % per cycle. With the 1.9 % budget error it never breaks even | Needs a gate error of about 10⁻³; full module not attempted |

## Figures

| | |
|---|---|
| `fig01_classical_collision.png` | Classical collisions; sine-Gordon benchmark; conditional shift vs speed; energy |
| `fig02_single_wavepacket.png` | Propagation and dispersion of one quantum fluxon wavepacket |
| `fig03_joint_probability.png` | Joint two-fluxon probability \|ψ(X_A, X_B)\|² before, during and after the collision |
| `fig04_scattering_before_after.png` | Marginals before and after; phase vs momentum (flat at the sweet spot) |
| `fig05_phase_vs_coupling.png` | Conditional phase vs coupling strength (exact 2D vs first order) |
| `fig06_concurrence_vs_strength.png` | Concurrence vs interaction strength: pure, thermal sweet spot, thermal inductive-only |
| `fig07_fidelity_vs_timing.png` | Gate fidelity vs launch-time mismatch (exact 2D and model, several coupler lengths) |
| `fig08_noise_loss_sensitivity.png` | Temperature, speed mismatch, coupler error, junction disorder, error budget vs speed, damping |
| `fig09_quantum_vs_classical.png` | Conditional phase, quantum ⟨ΔX⟩ vs classical shift, which-path distinguishability |
| `fig10_energy_budget.png` | Energy retention, where the energy goes, cost per operation |
| `fig11_launcher.png` | Coherent launcher: potentials, launch speed distribution vs a thermal source, temperature dependence, full-circuit launch, 2D gate with launched packets, error budget |
| `companion1-5_*.png` | The five companion devices |
| `circuits/` | `qbfx2_netlist.cir` (complete), `schematic_unit_cells.png/.svg`, `qbfx2_layout.gds` and previews |

## Run it

```bash
pip install -r requirements.txt      # numpy, scipy, matplotlib, qutip 5, scqubits, schemdraw, gdstk, klayout, pytest
./run_all.sh                          # all simulations, figures, circuits, tests and the paper (~45 min on 4 cores)
python -m pytest                      # 18 tests: sine-Gordon benchmarks, unitarity, eikonal limit, sweet spot, metrics, netlist
```

Single stages: `cd simulations && python A_classical.py` (or `B_quantum.py`, `C_gate.py`, `D_launcher.py`,
`D_feasibility.py`, `companions/c1_bell_pair.py` … `c5_qec.py`). Each stage writes `results/<stage>.json` with its
acceptance checks.

## Layout

```
src/classical/      circuit model: multi-rail discrete sine-Gordon with mutual L and C couplers; exact results
src/quantum/        collective-coordinate quantum model of a light fluxon and of two fluxons; checks vs the circuit
src/scattering/     1D/2D split-operator propagation, collision driver, first-order (eikonal) S-matrix
src/gates/          logical channel from motional overlaps; concurrence, entropy, Bell and CZ fidelities
src/optimization/   error budget (thermal launch, disorder, damping, timing, coupler) and operating-point search
src/hardware/       parameters, architecture, netlist, layout, schematic
simulations/        milestone scripts A-D and companions/
results/ figures/ circuits/ paper/ tests/
```

## Limits (read before building anything)

- **Model.** The quantum model is a first-order collective-coordinate theory, validated against the classical circuit
  near the operating point. It breaks down below β ≈ 0.22 and above β ≈ 0.35–0.45 (accuracy map in
  `results/A_classical.json`, `results/B_quantum.json`). Plasmon emission is estimated classically, not quantised.
- **Not modelled:**
  - preparing the launched fluxon's motional state;
  - quasiparticles and 1/f noise beyond a damping estimate;
  - offset-charge drift of the beam-splitter islands;
  - EM extraction of k, c and E_S for the drawn geometry.
- **Layout.** Preliminary, not fabrication-ready: no DRC, the crossover process for the coupling capacitors is
  unverified, and the node and island shunt capacitors are not drawn (EM extraction is to set them).

See [FEASIBILITY.md](FEASIBILITY.md) for the parameter-status table, cryogenic test requirements and a staged
measurement protocol, and `paper/main.pdf` for the full write-up. The paper describes the state before the launcher and the beam-splitter redesign; for milestone D it still reports the 1.9 % budget and NOT MET with three failing checks. The current milestone-D status is the one above.
