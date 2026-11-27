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
- `solution/reference_solution.py`: **instructor only**. Every quantum calculation goes through QuTiP 5 (`Qobj.eigenstates`, `sesolve`, `mesolve`, `HEOMSolver`); `solution/requirements.txt` lists the packages
- `src/`: figure script, handout HTML and PDF renderer

Run the solution: `pip install -r solution/requirements.txt && python3 solution/reference_solution.py` runs Parts 1–3 (~10 s). Use `--parts 1 2 3 4` to include HEOM, or `--parts 4` for HEOM alone (~2 min; the depth is raised automatically until the populations change by < 10⁻³, or pass fixed `--depths`). `--hamiltonian`, `--trap` and `--starts` take any N × N file.
Rebuild the handout: `python3 src/make_figure.py && node src/render_pdf.js` (Playwright Chromium).

## Quantum toolkit
The handout requires QuTiP ≥ 5.2 for every quantum calculation and names the functions per part. The reference was checked against QuTiP 5.3.1 and 5.2.0 (identical output). Alternatives looked at: dynamiqs (Parts 2–3 only, no HEOM), OQuPy (exact bath only, needs NumPy < 2), QuantumToolbox.jl + HierarchicalEOM.jl (Julia). qiskit-dynamics is unmaintained. Only QuTiP covers all four parts in Python.

Grading pitfall: QuTiP's `DrudeLorentzBath` / `DrudeLorentzEnvironment` with `Nk=0` uses the exact coefficient λγ_c cot(ħγ_c/2k_BT), not the high-temperature 2λk_BT. A student who uses it gets P₁(1 ps) ≈ 0.68 at 77 K instead of 0.54 (300 K agrees to ~0.003). The handout tells students to build the bath with `BosonicBath(Q, ck_real=[2λkT], vk_real=[γc], ck_imag=[-λγc], vk_imag=[γc])`.

## Reference results (sanity checks)
- Exciton energies (cm⁻¹, rel. 12 210): −30, 82, 155, 245, 260, 368, 471. Participation numbers 1.55, 2.68, 1.59, 1.73, 3.25, 1.61, 1.64. The lowest exciton sits on BChl 3/4, next to the RC.
- Coherent run from BChl 1: P₁(t) beats at about 200 cm⁻¹ (≈167 fs), matching the gap between the two BChl 1/2 excitons (368 − 155 = 212 cm⁻¹, within the 33 cm⁻¹ FFT resolution). BChl 3 never exceeds 5 % population.
- Efficiency η, read when < 10⁻³ is left on the sites (up to 7 ns):
  - Start BChl 1: 0.91 at γ = 0 and 0.1 cm⁻¹, 0.94 at 1 cm⁻¹, 0.99 for γ ≈ 30–300 cm⁻¹, 0.94 at 10⁴, 0.64 at 10⁵.
  - Start BChl 6: 0.25 at γ = 0, 0.83 at 0.1 cm⁻¹, 0.95 at 1 cm⁻¹, and within 0.03 of start BChl 1 for γ ≥ 1 cm⁻¹.
  - So the small-γ drop is mild from BChl 1 and large from BChl 6, which is what the Part 3 question asks about. Stopping at a fixed 100 ps instead gives 0.68 / 0.79 / 0.13 at γ = 0 / 1 / 10⁵ (start BChl 1), so the stopping rule matters.
  - The script checks η against the t → ∞ limit from QuTiP's Liouvillian: η ≤ η∞ ≤ η + 10⁻³ in every run.
- Classical Haken–Strobl rates match the quantum η for γ ≳ 10 cm⁻¹ and fall well below it at small γ (0.44 vs 0.91 at 0.1 cm⁻¹, 0.89 vs 0.94 at 1 cm⁻¹, start BChl 1).
- HEOM, high-T bath, start BChl 1, P₁ at 0/100/200/400/600/1000 fs:
  - 77 K: 1.000, 0.529, 0.640, 0.630, 0.658, 0.542. Converged by depth 4–5 (depth 4 → 5 changes populations by 9 × 10⁻⁵).
  - 300 K: 1.000, 0.514, 0.539, 0.462, 0.397, 0.298. Converges more slowly: depth 3 → 4 changes populations by 1.4 × 10⁻², and depth 6 → 7 by 3 × 10⁻⁴.
  - Beats in P₁ damp much faster at 300 K than at 77 K. The trace stays 1.
- The high-T approximation fails at 77 K (ħγ_c ≈ 106 cm⁻¹ > k_BT ≈ 54 cm⁻¹):
  - The populations of BChl 5–7 go negative from about 380 fs, down to −0.0096 on BChl 6 at 1 ps, and ρ has an eigenvalue as low as −0.15. This is depth-converged, so it comes from the model, not a bug. Students who see it are right.
  - Exact Padé coefficients plus a terminator stay positive and give P₁(1 ps) = 0.438 at 77 K (depth 3 vs 4 within 5 × 10⁻⁴).
  - At 300 K, the same benchmark gives 0.296 at depth 4 vs 0.298 for high-T. It is not fully converged in depth, but the gap is small.
  - This is the answer to the Part 4 hint.
