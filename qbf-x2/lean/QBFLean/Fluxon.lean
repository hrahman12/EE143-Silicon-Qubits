import QBFLean.Gates

/-!
# The QBF-X2 primitives

There are two dual-rail flying qubits:
- qubit A is one fluxon on rails A0 and A1;
- qubit B is one fluxon on rails B0 and B1.

|0⟩ means the fluxon is on rail 0, and |1⟩ that it is on rail 1. For the pair, the basis order is
A0B0, A0B1, A1B0, A1B1.

Topological charge is conserved, so there is one fluxon per qubit (milestone A of the simulation
suite), and the pair stays in this four-dimensional space. Leakage, a fluxon reflected or lost, lies
outside this model. The simulation puts it at 6×10⁻⁸ for pure wavepackets (`results/C_gate.json`).

Three hardware operations exist, and nothing else:
- `split`: a pass through a 50:50 beam splitter;
- `shift`: a relative phase between the two rails of one qubit;
- `collide`: a pass through the collision coupler.
-/

namespace QBFLean.Fluxon
open QBFLean QBFLean.ZOmega

/-- The 50:50 beam splitter. A moving fluxon hops coherently between its two rails through the
middle-rail phase-slip junctions. Run to the half-transfer point, this is `exp(−iπσₓ/4)`. -/
def split : SMat := ⟨1, [[1, -i], [-i, 1]]⟩

/-- A relative phase `e^{inπ/4}` on rail 1. It comes from a difference in rail length or rail
inductance, or from the Aharonov–Casher phase set by a beam-splitter gate voltage. -/
def shift (n : Nat) : SMat := ⟨0, [[1, 0], [0, ω ^ n]]⟩

/-- The collision coupler. Only rails A1 and B1 are coupled, so only the |11⟩ branch (both fluxons on
rail 1) picks up the collision phase `Δ = nπ/4`. The design point is `n = 4`, that is `Δ = π`. -/
def collide (n : Nat) : SMat := ⟨0, diag [1, 1, 1, ω ^ n]⟩

/-- Both fluxons launched on rail 0: the state |00⟩. -/
def launch : SVec := ⟨0, [1, 0, 0, 0]⟩

end QBFLean.Fluxon
