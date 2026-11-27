import QBFLean.Theorems

/-!
# A compiler from logical circuits to QBF-X2 operations

Logical two-qubit gates compile to the chip's only three operations: `split`, `shift` and `collide`.
For every gate, `compileGate_correct` states that the compiled program equals the gate's matrix.
Status: written; not yet run through the Lean kernel (see `../README.md`).
-/

namespace QBFLean.Compiler
open QBFLean QBFLean.ZOmega QBFLean.G

inductive Qubit where
  | A | B
  deriving DecidableEq, Repr

/-- Logical two-qubit gates. -/
inductive Gate where
  | h (q : Qubit) | s (q : Qubit) | t (q : Qubit) | z (q : Qubit) | x (q : Qubit)
  | cz | cnot
  deriving Repr

/-- QBF-X2 hardware operations. -/
inductive Op where
  | split (q : Qubit)
  | shift (q : Qubit) (n : Nat)
  | collide (n : Nat)
  deriving Repr

def onQ : Qubit → SMat → SMat
  | .A, U => onA U
  | .B, U => onB U

def Gate.sem : Gate → SMat
  | .h q => onQ q H
  | .s q => onQ q S
  | .t q => onQ q T
  | .z q => onQ q Z
  | .x q => onQ q X
  | .cz => CZ
  | .cnot => CNOT

def Op.sem : Op → SMat
  | .split q => onQ q Fluxon.split
  | .shift q n => onQ q (Fluxon.shift n)
  | .collide n => Fluxon.collide n

/-- The matrix of a hardware program, with its operations in time order. -/
def run (ops : List Op) : SMat := ops.foldl (fun acc o => o.sem * acc) I4

/-- Compile one logical gate. -/
def compileGate : Gate → List Op
  | .h q => [.shift q 2, .split q, .shift q 2]
  | .s q => [.shift q 2]
  | .t q => [.shift q 1]
  | .z q => [.shift q 4]
  | .x q => [.shift q 2, .split q, .split q, .shift q 2]
  | .cz => [.collide 4]
  | .cnot => [.shift .B 2, .split .B, .shift .B 2, .collide 4, .shift .B 2, .split .B, .shift .B 2]

/-- Every logical gate compiles to a QBF-X2 program that implements it exactly. -/
theorem compileGate_correct : ∀ g : Gate, (run (compileGate g)).Eqv g.sem
  | .h .A => by decide
  | .h .B => by decide
  | .s .A => by decide
  | .s .B => by decide
  | .t .A => by decide
  | .t .B => by decide
  | .z .A => by decide
  | .z .B => by decide
  | .x .A => by decide
  | .x .B => by decide
  | .cz => by decide
  | .cnot => by decide

/-- A logical circuit: gates in time order. -/
abbrev Circuit := List Gate

def Circuit.sem (c : Circuit) : SMat := c.foldl (fun acc g => g.sem * acc) I4
def Circuit.compile (c : Circuit) : List Op := c.flatMap compileGate

def bell : Circuit := [.h .A, .h .B, .cz, .h .B]

theorem bell_compiles_exactly : (run bell.compile).Eqv bell.sem := by decide

theorem bell_makes_bell_pair : (bell.sem.apply Fluxon.launch).Eqv ⟨1, [1, 0, 0, 1]⟩ := by decide

end QBFLean.Compiler
