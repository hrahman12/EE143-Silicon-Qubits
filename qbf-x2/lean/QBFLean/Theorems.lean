import QBFLean.Fluxon

/-!
# What the QBF-X2 gate does, stated exactly

Each theorem is an exact equation over `ℤ[ω]`, proved with `decide`: the Lean kernel evaluates both
sides and compares them. Status: written; not yet run through the Lean kernel (see `../README.md`).
-/

namespace QBFLean.Theorems
open QBFLean QBFLean.ZOmega QBFLean.G QBFLean.Fluxon

/-- At the design point (Δ = π) the collision is exactly a CZ gate. -/
theorem collide_pi_eq_CZ : (collide 4).Eqv CZ := by decide

/-- With the coupler off (Δ = 0) nothing happens, as in the simulation's control run. -/
theorem collide_zero_eq_id : (collide 0).Eqv I4 := by decide

/-- Half the coupling (Δ = π/2) gives a controlled-S. -/
theorem collide_half_eq_CS : (collide 2).Eqv CS := by decide

/-- Two passes through the coupler at Δ = π undo each other. -/
theorem collide_pi_twice : (collide 4 * collide 4).Eqv I4 := by decide

/-- The beam splitter is unitary. -/
theorem split_unitary : (split * split.adjoint).Eqv I2 := by decide

/-- A beam splitter between two rail phases of π/2 is exactly a Hadamard gate. -/
theorem hadamard_from_split : (shift 2 * split * shift 2).Eqv H := by decide

/-- Two beam-splitter passes move the fluxon to the other rail: with the phases, exactly X. -/
theorem x_from_two_splits : (shift 2 * split * split * shift 2).Eqv X := by decide

/-- Both fluxons through Hadamard-tuned beam splitters: the state |+⟩|+⟩. -/
def plusPlus : SVec := (onA H * onB H).apply launch

/-- The pair after one pass through the coupler at phase Δ = nπ/4. -/
def afterCollision (n : Nat) : SVec := (collide n).apply plusPlus

theorem plusPlus_normalised : plusPlus.Normalised := by decide

/-- Before the collision the qubits are not entangled: concurrence 0. -/
theorem plusPlus_product : plusPlus.concNum = 0 := by decide

/-- After the collision at Δ = π the qubits are maximally entangled: concurrence exactly 1. -/
theorem collision_max_entangled :
    (afterCollision 4).concNum = (afterCollision 4).concDen := by decide

/-- With the coupler off there is no entanglement. -/
theorem collision_off_unentangled : (afterCollision 0).concNum = 0 := by decide

/-- For every coupler phase Δ = nπ/4: C² = (1 − cos Δ)/2, where cos Δ = (ωⁿ + ω̄ⁿ)/2.
Written without division: `4 · C² · 2^(2k) = (2 − (ωⁿ + ω̄ⁿ)) · 2^(2k)`. -/
theorem concurrence_law : ∀ n, n < 8 →
    4 * (afterCollision n).concNum = (2 - (ω ^ n + conj (ω ^ n))) * (afterCollision n).concDen := by
  decide

/-- The Bell-pair program written with hardware operations only. Both fluxons are tuned to |+⟩,
collide at Δ = π, and B is tuned once more. The result is (|00⟩ + |11⟩)/√2. -/
def bellProgram : SMat :=
  onB (shift 2 * split * shift 2) * collide 4 * onA (shift 2 * split * shift 2) *
    onB (shift 2 * split * shift 2)

theorem bell_pair : (bellProgram.apply launch).Eqv ⟨1, [1, 0, 0, 1]⟩ := by decide

end QBFLean.Theorems
