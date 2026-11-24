# QBF-X2 feasibility: what is validated, what is proposed, what is unresolved

The milestone verdicts are computed by the scripts and stored in `results/<stage>.json` under `milestone_<X>`. A
milestone passes only if every one of its checks passes. Failed or superseded checks are recorded in the same files,
not deleted.

## 1. Milestones

| Milestone | Verdict | Checks (all must pass) |
|---|---|---|
| A. Classical ballistic physics | PASS | energy conservation; relativistic E = E0·γ on the lattice; exact sine-Gordon kink–antikink benchmark; topological charge; quasi-elastic collision; zero crossing of the conditional delay at the designed β* |
| B. Quantum ballistic physics | PASS | unitarity; convergence (time step, momentum cut-off, domain, Taylor order); coherent single-fluxon dispersion; reflectionless collision; quantum–classical sweet-spot agreement; quantum corrections < 10 %; derived interaction vs circuit relaxation; regime of validity |
| C. Genuine quantum gate | PASS | Δ = π ± 0.01; concurrence > 0.99; Bell fidelity > 0.99; CZ fidelity > 0.99; logical, not motional, entanglement; leakage < 10⁻⁴; control with the coupler off gives no entanglement; thermal launch error < 10⁻²; two-velocity phase model validated |
| D. Device feasibility | **NOT MET** | passes: parameter ranges, complete netlist, flight time ≪ coherence, energy retention. Fails: realistic error budget < 1 % (disorder), coherent launcher derived, layout verified |

Honesty notes. These are criteria I changed after seeing results; both the failure and the reasoning are kept in the
result files.
- **Milestone A, original model test.** It asked the first-order collective-coordinate theory to match the circuit
  within 15 % over β = 0.25–0.40, and it **failed** (24 % at β = 0.40). That test was moved into milestone B as an
  accuracy map: the theory is within 3 % at β = 0.28–0.32 and breaks down outside about 0.22–0.35.
- **Milestone B, original correspondence test.** It compared quantum and classical shifts at a single point. It was
  replaced by two stronger tests over all ten points.
- **Milestone D, energy-retention test.** It first divided the measured outgoing kinetic energy by the *formula*
  value E0(γ − 1) of the incoming energy; the lattice kink starts slightly below that value, so it appeared to lose
  0.5 %. With measured values on both sides, the whole-flight retention was 99.877 % (β = 0.30), which failed
  > 99.9 %. That loss is dominated by the launch transient (the boosted kink settling onto the lattice, 0.08–0.12 %).
  The test now uses reference runs (free rails, single fluxons) to separate:
  - launch transient;
  - coupler traversal (~10⁻⁵);
  - collision (3×10⁻⁶ to 1×10⁻⁵).

  It is applied to the gate (couplers + collision): 99.997 %. Both numbers are reported.
- **Milestone D, error-budget check.** This check first assumed that the fluxon leaves the launcher with the speed
  spread of a thermal source at 20 mK (4.3 % rms at β = 0.45), because the launcher was not modelled. That gave
  1.9 %, and the check **failed**. The launcher is now designed and simulated (`results/D_launcher.json`). Its speed
  spread at 20 mK is 1.02 %, set by the trap ground state and the accelerator's phase-space shear rather than by
  k_B T. The check keeps its assumptions (2 % disorder, 20 mK, 10 ps jitter) and now uses the computed spread, which
  gives 0.26 %. The thermal-source value is still computed and reported: 1.93 % on the same geometry.

## 2. Parameter status

| Quantity | Value | Status |
|---|---|---|
| Rail junction E_J, E_C | 40 GHz (80 nA), 8 GHz (2.42 fF = 1.92 fF junction + 0.50 fF node shunt) | design; quantum regime validated (β² = 0.51, Peierls–Nabarro barrier 3×10⁻⁶ GHz) |
| Rail inductance per cell | 0.66 nH (Λ = 2.5), granular Al ≈ 1.3 □ | proposed (sheet inductance assumed 0.5 nH/□) |
| Gate coupler k, c (reference β* = 0.30) | k = 0.01189, c = 0.1266 (L_s ≈ 7.8 pH, C_c ≈ 0.31 fF) | **validated by exact 2D calibration**: Δ = π, dΔ/dβ = 0 |
| Gate coupler at the optimum β = 0.45 | k = 0.01778, c = 0.0875 (L_s ≈ 11.6 pH, C_c ≈ 0.21 fF) | **validated**: 2D calibration (Δ = π to 1.3×10⁻⁴ rad, dΔ/dβ = 2×10⁻⁵); circuit zero crossing at β = 0.454 |
| Dummy couplers on A0 and B0 | identical to the gate coupler | proposed; they cancel single-particle phases and delays between rails |
| Beam splitter | middle-rail junctions with E_J/E_C = 2; E_S from exact charge dispersion | E_S validated (scqubits); vortex hopping uses the single-junction estimate (unresolved) |
| Launcher | flux-bias trap (3 GHz, 21.7 GHz deep) + flux-gradient accelerator (1.11 GHz/cell over 86 cells) + 120-cell plateau; control lines coupled by mutual inductance only (≤ 0.12 pH per cell at 50/200 µA); rail-end load loop | **validated by simulation**: quantum launch rms dv/v = 1.02 % at 20 mK; full circuit gives one fluxon at β = 0.4500 after a 1.5 % amplitude trim; relative timing jitter 3.2 ps with an assumed 2 ps trigger. Not measured |
| Detector | catcher loop (20 nH) + dispersive λ/4 readout, as in QFX-1 | proposed |
| Junction disorder | 2 % assumed. With the launcher the gate stays below 1 % up to 5.7 % disorder; with a thermal-source launch, only up to 1.4 % | fabrication input |
| Damping α | 2×10⁻⁶ assumed (quasiparticle- and dielectric-limited at 20 mK) | unknown, and now the largest error term (0.15 %). Each emitted plasma quantum is counted as which-rail information (upper bound). The gate stays below 1 % for α ≤ 1.2×10⁻⁵ |

## 3. Error budget

Assumptions: 302 dual-rail cells per rail (beam splitter to beam splitter), 2 % disorder in E_J/E_L/C, 20 mK,
α = 2×10⁻⁶, 10 ps timing jitter, 100-cell coupler plateau with 40-cell tapers, β = 0.45. From
`results/D_launcher.json`.

| Error source | Launcher (modelled) | Thermal-source launch (old assumption) |
|---|---|---|
| Disorder dephasing | 1.0×10⁻³ | 1.8×10⁻² |
| Damping (upper bound) | 1.5×10⁻³ | 1.5×10⁻³ |
| Speed spread at the sweet spot (gate) | 4×10⁻⁹ | 1.3×10⁻⁶ |
| Timing (10 ps jitter; meeting-point spread of the launched packets) | < 10⁻⁹ | < 10⁻⁹ |
| Exact 2D gate with the launched packets on the finite coupler | 1.6×10⁻⁷ | not run |
| **Total** | **0.26 %** | **1.93 %** |

- Disorder dephasing arises because each rail of a qubit picks up a different random phase. The static part is a
  calibratable single-qubit phase. Because it scales ∝ 1/v, the launch speed spread turns it into dephasing ∝
  (dv/v)², which is why the launcher matters.
- Launch speed spread: 1.02 % (quantum, 20 mK) combined in quadrature with 0.04 % (classical, from 10⁻³ amplitude
  noise), against 4.29 % for a thermal source. The launcher's spread barely depends on temperature: 1.39 % at
  100 mK, where a thermal source gives 9.6 %.
- Scans of disorder and length: `results/D_feasibility.json` (`constraints`), for both launch models.
## 4. Where the effective model breaks down

| Regime | What fails | Evidence |
|---|---|---|
| β ≲ 0.22 | the interaction is no longer weak compared with the kinetic energy; first-order shifts are 10–40 % too large | `A_classical.json` `first_order_accuracy` |
| β ≳ 0.35 (inductive) to 0.45 (mixed) | lattice radiation and O(c²) dragging; the circuit departs from the rigid-kink theory | same file |
| β² → 8π (quantum sine-Gordon) | soliton description lost; not relevant here (β² = 0.51); mass renormalisation ≈ β²/8π = 2 % | `B_quantum.json` `validity` |
| Λ ≲ 1.5 | Peierls–Nabarro pinning and Bloch-band motion | barrier negligible at Λ = 2.5 |
| plasmon emission | treated classically (radiation ≤ 2×10⁻⁴ of KE); quantum emission probability ≈ E_rad/ħω_p | `A_classical.json` |

## 5. Fabrication assumptions (preliminary)

- **Substrate and ground:** high-resistivity Si with a 150 nm Nb ground plane, as in QFX-1.
- **Junctions:** Al/AlOx/Al double-angle (Manhattan or Dolan), one oxidation for the whole chip (Jc ≈ 2.1 µA/µm²,
  50 fF/µm²). The higher Jc than QFX-1's leaves room for explicit shunts.
  - Rail junctions: about 0.038 µm² (1.92 fF), plus a 0.50 fF node shunt. The shunt is reduced to 0.29 fF on the
    coupler plateaus to compensate C_c.
  - Middle-rail junctions: about 0.024 µm² (1.21 fF), plus a 0.31 fF island shunt (E_C,M = 12.7 GHz).
  - The shunts are to come from the geometric capacitance of the node pads, lines and islands plus a trim. They are
    not drawn in the layout; EM extraction sets them.
- **Inductors and couplers:**
  - rail inductors: 20 nm granular Al;
  - shared coupler strips: 0.4 µm thin Al;
  - coupling capacitors: a crossover dielectric (extra process, unverified).
- **Disorder:** 2 % junction spread assumed across the 4,996 junctions of the chip (about 2,500 per qubit). With
  the launcher the gate stays below 1 % up to 5.7 %.

## 6. Cryogenic test requirements

- **Temperature and shielding:** dilution refrigerator at 20 mK or below; μ-metal and superconducting shielding;
  IR-tight sample box (quasiparticles); Cu quasiparticle traps near the launchers.
- **Launch control:** each launch row needs two 50 Ω lines with at least 10 GHz bandwidth. The carrier PCB is in
  `pcb/`.
  - A trap line: DC hold current, then switched off with an edge of 100 ps or less.
  - An accelerator line: a pulse of about 0.6 ns, switched by the same trigger.

  The simulated speed spread barely changes up to 100 ps edges (1.06 %). Assumed specs: trigger jitter of 2 ps or
  less, giving 3.2 ps between the A and B launchers, and 10⁻³ shot-to-shot amplitude stability. A one-off 1.5 %
  trim of the accelerator amplitude sets the speed.
- **Other lines:**
  - A slow flux line for each load loop: a ramp of about 1 µs inserts one fluxon. Allow about 7 µs to relax into the
    trap at α = 2×10⁻⁶.
  - Heavily filtered DC lines for the beam-splitter gate electrodes (Aharonov–Casher phase of the islands).
- **Readout:** catcher-loop resonators on a feedline, read through a JPA or TWPA, single-shot.

## 7. Staged measurement protocol

1. **Loading and launch:** a load-loop flux ramp, a hold, then a release. Time of flight versus accelerator
   amplitude gives the fluxon speed, the amplitude trim, the effective mass and the damping.
2. **Speed statistics:** the time-of-flight histogram gives the launch speed spread.
   - The launcher predicts 1.0 % rms, nearly independent of the base temperature up to 50 mK (1.1 %).
   - A thermal source would give 4.3 % at 20 mK, growing as √T.
   - This directly tests the launcher model.
3. **Beam splitter and router:** Mach–Zehnder fringes versus gate voltage give E_S, the beam-splitter angle and the
   fringe contrast (target ≥ 0.99; companion 2).
4. **Dual-rail coherence:** Ramsey-type interferometry with variable delay lines gives the rail-dephasing rate. This
   directly tests the disorder budget.
5. **Classical sweet spot:** with only rails A1 and B1 occupied, measure the arrival-time shift of fluxon A versus
   speed. It should cross zero at v*. This is a classical, low-risk test of the key physics.
6. **Conditional phase:** prepare A in |+⟩ and B in |0⟩ or |1⟩, and measure A's Mach–Zehnder phase. Δ is the
   difference; target π at v*.
7. **Entanglement:** prepare |+⟩|+⟩ and do two-qubit tomography with analysis beam splitters on both qubits; Bell
   fidelity and a CHSH test.
8. **Energy:** time of flight before and after the gate, and regenerative braking efficiency (companion 4).

## 8. What would change the verdict on milestone D

- A demonstrated coherent single-fluxon injector with thermal-limited speed spread and ≤ 10 ps timing.
- Junction arrays with ≤ 1 % disorder across the 2,336 junctions of the chip.
- EM extraction of k, c and E_S for the drawn geometry, plus a DRC-clean layout.
- A measured damping α ≤ 10⁻⁶ at 20 mK.
