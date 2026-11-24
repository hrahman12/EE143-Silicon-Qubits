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

## 2. Parameter status

| Quantity | Value | Status |
|---|---|---|
| Rail junction E_J, E_C | 40 GHz (80 nA), 8 GHz (2.42 fF = 1.92 fF junction + 0.50 fF node shunt) | design; quantum regime validated (β² = 0.51, Peierls–Nabarro barrier 3×10⁻⁶ GHz) |
| Rail inductance per cell | 0.66 nH (Λ = 2.5), granular Al ≈ 1.3 □ | proposed (sheet inductance assumed 0.5 nH/□) |
| Gate coupler k, c (reference β* = 0.30) | k = 0.01189, c = 0.1266 (L_s ≈ 7.8 pH, C_c ≈ 0.31 fF) | **validated by exact 2D calibration**: Δ = π, dΔ/dβ = 0 |
| Gate coupler at the optimum β = 0.45 | k = 0.01778, c = 0.0875 (L_s ≈ 11.6 pH, C_c ≈ 0.21 fF) | **validated**: 2D calibration (Δ = π to 1.3×10⁻⁴ rad, dΔ/dβ = 2×10⁻⁵); circuit zero crossing at β = 0.454 |
| Dummy couplers on A0 and B0 | identical to the gate coupler | proposed; they cancel single-particle phases and delays between rails |
| Beam splitter | middle-rail junctions with E_J/E_C = 2; E_S from exact charge dispersion | E_S validated (scqubits); vortex hopping uses the single-junction estimate (unresolved) |
| Launcher | injection junction (2 I_c) + current pulse + 40-cell accelerator | **UNRESOLVED**: motional-state preparation and timing (≤ 10 ps) not modelled |
| Detector | catcher loop (20 nH) + dispersive λ/4 readout, as in QFX-1 | proposed |
| Junction disorder | 2 % assumed; needs ≤ 1 % for a sub-1 % gate error | **open fabrication requirement** |
| Damping α | 2×10⁻⁶ assumed (quasiparticle- and dielectric-limited at 20 mK) | unknown; each emitted plasma quantum is counted as which-rail information (upper bound) |

## 3. Error budget

Assumptions: 300 cells per rail, 2 % disorder in E_J/E_L/C, 20 mK launch, α = 2×10⁻⁶, 10 ps jitter, 100-cell
coupler plateau.

| Error source | Effect |
|---|---|
| Thermal launch speed spread (gate) | second order at the sweet spot: 1.2×10⁻⁵ at β = 0.30 |
| Junction disorder | dominant; the rail phase difference scales ∝ 1/v, so its dephasing falls ∝ β⁻⁴ |
| Damping | about 10⁻³ |
| Timing jitter | negligible while the meeting point stays on the coupler plateau |
| Coupler strength error | needs calibration, a flux-tunable L_s, or speed retuning |

Totals:
- Optimum, β = 0.45: **1.9 %**. Disorder 1.8 %, damping 0.15 %, thermal gate 1.3×10⁻⁶, timing 0.
- Requirements, from the disorder/length scan in `results/D_feasibility.json` (`constraints`):
  - < 1 % needs junction disorder ≤ 1 % (0.73 % over the full 362-cell design) or flights ≤ 150 cells at 2 % (0.97 %);
  - 0.5 % disorder gives 0.13–0.32 %.
- Per-speed totals: `results/C_gate.json` (`budget_scan_default`).

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
  - Injection junctions: about 0.077 µm² (2 I_c).
  - The shunts are to come from the geometric capacitance of the node pads, lines and islands plus a trim. They are
    not drawn in the layout; EM extraction sets them.
- **Inductors and couplers:**
  - rail inductors: 20 nm granular Al;
  - shared coupler strips: 0.4 µm thin Al;
  - coupling capacitors: a crossover dielectric (extra process, unverified).
- **Disorder:** junction spread of 1 % or better across the 2,336 junctions of the chip (about 1,170 per qubit).

## 6. Cryogenic test requirements

- **Temperature and shielding:** dilution refrigerator at 20 mK or below; μ-metal and superconducting shielding;
  IR-tight sample box (quasiparticles); Cu quasiparticle traps near the injectors.
- **Launch control:** fast lines for the injectors (rise time ≤ 20 ps, relative timing between the A and B launchers
  ≤ 10 ps). This could come from on-chip SFQ clocking or cryo-CMOS pulse generators.
- **Other lines:** dc lines for the accelerators and gate electrodes (Aharonov–Casher phase of the beam-splitter
  islands).
- **Readout:** catcher-loop resonators on a feedline, read through a JPA or TWPA, single-shot.

## 7. Staged measurement protocol

1. **Single-rail transit:** time of flight versus accelerator bias gives fluxon speed, effective mass and damping.
2. **Velocity statistics:** the time-of-flight histogram gives the launch speed spread; compare it with the thermal
   prediction at the base temperature.
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
