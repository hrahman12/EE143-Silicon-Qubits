# Term Project: Quantum Biology (FMO energy transfer)

A quantum-biology counterpart to the EE118/218A computational-microscopy term project, with the same 3-page layout and 4-part structure.

| Microscopy project | Quantum biology project |
|---|---|
| 1. Recover the complex field from a hologram | 1. Diagonalize the FMO Hamiltonian: exciton states, delocalization |
| 2. Find a plane of focus (angular spectrum) | 2. Coherent Schrödinger dynamics: population beats vs exciton gaps |
| 3. Brightfield vs phase contrast: pick a feature that differs | 3. Lindblad dephasing + trap: environment-assisted transport, quantum vs classical (Haken–Strobl) rates |
| 4. Synthetic aperture (218A required) | 4. HEOM with a Drude–Lorentz bath at 77 K / 300 K (218A required) |

- `Quantum_Biology_Term_Project.pdf`: the handout
- `data/fmo_hamiltonian_cm-1.csv`: the student input file (7 × 7 Adolphs–Renger Hamiltonian, cm⁻¹)
- `solution/reference_solution.py`: **instructor only**, checks every task (`python3 solution/reference_solution.py --heom`, ~30 s)
- `src/`: figure script, handout HTML and PDF renderer

Rebuild: `pip install numpy scipy matplotlib && python3 src/make_figure.py && node src/render_pdf.js` (Playwright Chromium).

## Reference results (sanity checks)
- Exciton energies (cm⁻¹, rel. 12 210): −30, 82, 155, 245, 260, 368, 471. The lowest exciton sits on BChl 3/4, next to the RC.
- Coherent run from BChl 1: P₁(t) beats at about 200 cm⁻¹ (≈167 fs), matching the gap between the two BChl 1/2 excitons (368 − 155 = 212 cm⁻¹, within the 33 cm⁻¹ FFT resolution).
- Efficiency η (start BChl 1): 0.68 at γ = 0, ≈0.99 for γ ≈ 10–1000 cm⁻¹, 0.79 at 10⁴, 0.13 at 10⁵. Classical rates match the quantum result for γ ≳ 100 cm⁻¹ and fall well below it at γ = 1 cm⁻¹ (0.51 vs 0.79).
- HEOM converges between depth 3 and 4. The trace stays 1. Beats in P₁ damp much faster at 300 K than at 77 K. ħγ_c ≈ 106 cm⁻¹ vs k_BT ≈ 54 cm⁻¹ at 77 K, so the high-temperature approximation is questionable there (a good discussion point).
