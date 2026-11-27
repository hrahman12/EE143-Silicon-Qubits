import QBFLean.Matrix

/-!
# Logical gates

These are the standard one- and two-qubit gates, written exactly. For a pair of qubits, qubit A is
the left tensor factor. The basis order is |00⟩, |01⟩, |10⟩, |11⟩, where the first digit is A.
-/

namespace QBFLean.G
open QBFLean QBFLean.ZOmega

def I2 : SMat := ⟨0, [[1, 0], [0, 1]]⟩
def X : SMat := ⟨0, [[0, 1], [1, 0]]⟩
def Z : SMat := ⟨0, [[1, 0], [0, -1]]⟩
def H : SMat := ⟨1, [[1, 1], [1, -1]]⟩
def S : SMat := ⟨0, [[1, 0], [0, i]]⟩
def T : SMat := ⟨0, [[1, 0], [0, ω]]⟩

def I4 : SMat := ⟨0, ident 4⟩
def CZ : SMat := ⟨0, diag [1, 1, 1, -1]⟩
def CS : SMat := ⟨0, diag [1, 1, 1, i]⟩
def CNOT : SMat := ⟨0, [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]]⟩

/-- `U` acting on qubit A. -/
def onA (U : SMat) : SMat := U.kron I2
/-- `U` acting on qubit B. -/
def onB (U : SMat) : SMat := I2.kron U

theorem H_mul_H : (H * H).Eqv I2 := by decide
theorem H_Z_H : (H * Z * H).Eqv X := by decide
theorem S_mul_S : (S * S).Eqv Z := by decide
theorem T_mul_T : (T * T).Eqv S := by decide

end QBFLean.G
