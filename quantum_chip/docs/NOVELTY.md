# QFX-1: what's new and what isn't

**Short version.** A qubit made from a single quantum fluxon is **not new**. A KIT PhD thesis (2023) already reported
Rabi oscillations of a single Josephson vortex. QFX-1 combines three things we found **no prior example of** in the
literature we searched:

- a *classical* fluxon flying down a ballistic line that applies a coherent gate to a *quantum* fluxon qubit;
- the momentum rule that sets how clean that gate can be;
- two quantum-fluxon qubits coupled on one chip.

"No prior example" means only that none turned up in what the search tools listed in section 3 returned. It is a
claim to check, not a proof. Nothing here has been fabricated or measured: all QFX-1 numbers come from
`src/qfx_sim.py`.

## 1. Prior work

| Area | Status in the literature | Sources |
|---|---|---|
| Quantum levels and tunnelling of one Josephson vortex | **Demonstrated** in an annular long junction: quantised energy levels and macroscopic quantum tunnelling of a single fluxon | Wallraff et al., *Nature* 425, 155 (2003); theory: Kato & Imada, *J. Phys. Soc. Jpn.* 65, 2963 (1996) |
| Josephson-vortex qubit designs | **Proposed** several times: double wells made with microshorts, field-tuned annular or confocal junctions; decoherence estimates | Kemp, Wallraff & Ustinov, *phys. stat. sol. (b)* 233, 472 (2002); Price et al., *Phys. Rev. B* (2008); Kim, Dhungana & Park, *Phys. Rev. B* (2006); Monaco, Mygind & Koshelets, arXiv:1707.01672 and *Supercond. Sci. Technol.* (2018) |
| Quantum fluxon in discrete arrays with large kinetic inductance | **Theory**: coherent tunnelling bands, Aharonov–Casher (gate-voltage) control, 4π kinks; fluxon-based quantum simulation in circuit QED | Seidov & Fistul, *Phys. Rev. A* 103, 062410 (2021), doi:10.1103/PhysRevA.103.062410; Seidov & Fistul, *Phys. Rev. B* (2022); Petrescu … Pop, *Phys. Rev. B* |
| **A working Josephson-vortex qubit** | **Demonstrated** in a high-impedance long junction galvanically embedded in a resonator. Coherent tunnelling of single vortices forms a two-level system, read out dispersively. Rabi oscillations, with T1 and T2 in the µs range | KIT PhD thesis *Quantum Tunneling of Josephson Vortices in High-Impedance Long Junctions* (2023), doi:10.5445/IR/1000158804; Wildermuth et al., *Fluxons in high-impedance long Josephson junctions*, *Appl. Phys. Lett.* (2022), doi:10.1063/5.0082197 |
| Coherent superconducting-vortex states in granular Al | **Demonstrated**: coherent manipulation and QND readout. This is a different platform (a vortex in a film, not a Josephson vortex in a junction array) | Nambisan … Pop, *Nature* (2026), doi:10.1038/s41586-026-10441-7 (arXiv:2510.19769) |
| Ballistic fluxons used to **read out** qubits | Theory and experiments, including analyses of measurement back-action | Averin, Rabenstein & Semenov, *Phys. Rev. B* 73, 094504 (2006); Fedorov et al., *Appl. Phys. Lett.* (2013), doi:10.1063/1.4800585; Fedorov et al., *Phys. Rev. Lett.* 112, 160502 (2014); Wustmann & Osborn, *Phys. Rev. Applied* (2025), arXiv:2504.18915; fluxon time-delay readout, arXiv:2603.13175 (2026) |
| Fluxons or SFQ pulses **driving** conventional qubits | Proposals and simulations for flux, phase and transmon qubits; resonant SFQ pulse trains | Matsuo et al., *Appl. Phys. Lett.* 91, 093103 (2007); Fujii, Matsuo & Hatakenaka, *Int. J. Quantum Inf.* 14, 1650040 (2016); Bastrakova, Klenov & Satanin, *J. Phys.: Conf. Ser.* (2019); Denisenko, Klenov & Satanin, *JETP* (2019); McDermott & Vavilov, *Phys. Rev. Applied* 2, 014007 (2014) |
| Coupling two vortex qubits | **Theory only** (cavity-mediated vortex–vortex coupling). No coupled Josephson-vortex qubits found | Fistul & Ustinov, *Phys. Rev. B* 68, 132509 (2003) |
| Ballistic, reversible fluxon logic | **Classical** gates, including a reversible "CNOT" on fluxon bits | Osborn & Wustmann, arXiv:1711.04339; *IEEE Trans. Appl. Supercond.* (2021), doi:10.1109/TASC.2020.3035344; Frank et al. (Sandia), asynchronous ballistic reversible computing |
| Gate-voltage (Aharonov–Casher) control of flux tunnelling | Proposed and measured in other circuits; not used in QFX-1 | Friedman & Averin, *Phys. Rev. Lett.* (2002); Pop et al., *Phys. Rev. B* (2012); Bell et al., *Phys. Rev. Lett.* (2016) |

## 2. What QFX-1 adds

1. **A fluxon gating a fluxon.** Both the gate carrier and the qubit are Josephson vortices.
   - The qubit is a light, quantum fluxon in a 24-junction ring.
   - The carrier is a heavy, classical fluxon in an unbiased ballistic line (20 µA junctions on a low-inductance
     coplanar strip). Its rest energy is about 213 THz·h, against the qubit's 3.2 GHz splitting.
   - While the carrier is inside a 1.2 mm section of line, a flux transformer tilts the qubit's double well, and the
     qubit picks up a phase. Then the carrier leaves.

   Earlier fluxon-gate proposals target flux, phase or transmon qubits. Other fluxon–qubit work is about readout.
2. **The momentum rule.** A ballistic gate carrier learns which state the qubit was in: it is displaced by
   **δX = ħθ/p**. A carrier whose momentum is spread by σ_p therefore dephases the qubit by
   1 − exp(−θ²σ_p²/2p²); for a thermal launch this is ≈ θ²k_BT/(4·KE).
   - A clean gate needs a fast or heavy carrier; adiabaticity needs a slow one. QFX-1 runs at v = 0.05 c0 (c0 is the
     line's Swihart speed), where thermal dephasing is 9.7×10⁻⁴ per π/2 gate at 20 mK. Only that speed was run through
     the full dynamics.
   - Tapering the coupling (flared pickup ends, 200 µm ramps) keeps the gate adiabatic: non-adiabatic flips are
     8×10⁻⁷, against 4×10⁻³ with abrupt ends.
   - The displacement law is checked against a classical discrete sine-Gordon run of the line, with a relative error of
     0.4 %.

   Readout analyses (for example Averin et al.) treat the same back-action, but as the signal to maximise. Here it is
   the error to suppress. We did not find it stated as a design rule for fluxon gates.
3. **An adiabatic dispersive gate that leaves the carrier's energy intact.** The qubit is held at its sweet spot, and
   the gate is θ = 2πτ(√(f01² + ε²) − f01) in the two-level limit; the higher levels add to the shift. At v = 0.05 c0
   and transformer coupling κ = 2.55×10⁻³, a 24-level simulation gives:
   - phase 1.5706 rad (target π/2);
   - bit-flip probability 7.7×10⁻⁷;
   - leakage 3×10⁻¹².

   Only the DC/SFQ launcher and the SFQ/DC receiver dissipate. The line and the gate run without bias.
4. **Two quantum-fluxon qubits with a galvanic coupler on one die.** The shared inductor gives
   J = L_s·ΔI²/4 = 3.79 MHz per pH, where ΔI = 100 nA is the link-current difference between the two wells.
   - In the fluxon-position basis the coupling is ZZ; at the sweet spot it is transverse (XX) in the energy basis.
   - We found only a theory proposal for cavity-mediated vortex coupling, and no coupled Josephson-vortex qubit device.
5. **The array design point** (an implementation choice, not a claim of principle):
   - 24 small Al/AlOx/Al junctions (E_J/E_C ≈ 4.9) on granular-Al superinductor rails (Λ = 1, 4.1 nH per cell);
   - wells from two junctions at 0.3·E_J;
   - a barrier dc SQUID sized so that f01 = 3.21 GHz at zero SQUID flux. This is a double sweet spot: f01 is
     first-order insensitive to the barrier flux and to the tilt. Flux tunes f01 upward, to 27 GHz;
   - f12 = 17.19 GHz, which keeps leakage low;
   - ring and kick-line junctions come from one Al/AlOx/Al step (Jc = 1.665 µA/µm², 50 fF/µm²). The kick line's
     Josephson length (2.7 cells) is computed from the drawn coplanar strip, not assumed.

**Not claimed:** fluxon qubits themselves, fluxon readout, SFQ control of qubits, and the physics of soliton–qubit
scattering in general are all prior art (section 1).

## 3. How the search was done

| Tool | Used for |
|---|---|
| Undermind deep search | 93 ranked papers on four questions: vortex qubits, coupled vortex qubits, ballistic-fluxon gates and their back-action, and Aharonov–Casher control |
| Lune (peer-reviewed full text) | multi-angle sweep on single-vortex quantum dynamics, vortex qubits and fluxon–qubit coupling |
| alphaXiv | three arXiv discovery searches; PDF questions on Seidov & Fistul (2021) for circuit parameters |
| SciSpace | search; the full record of the KIT 2023 thesis |
| Valency | three semantic searches: fluxon readout and gates, granular-Al vortex qubits, moving-fluxon back-action |
| Paperguide | fluxon–qubit interaction search |
| Wolfram\|Alpha | unit checks: E_C = 8.07 GHz for 2.4 fF; E_J = 39.7 GHz for I_c = 80 nA |
| Web search | context on Vaire Computing and reversible computing |

**Not available in this session:**
- Consensus: the free monthly quota is used up.
- Scite: needs a paid plan or trial.
- Elicit: the plan has no API access.
- Scholar Gateway: access was denied.
- OpenAlex verification (reference lookup): blocked by the session's network policy.

**Coverage limits:**
- The screening is based on titles and abstracts plus a few full texts.
- Patents and paywalled full texts were not read.
- The KIT thesis is cited by title, institution and DOI because the tools did not return its author list.
