# Quantum Lean for QBF-X2

This is Lean 4 code that models the QBF-X2 flying-fluxon chip exactly and compiles quantum circuits
to its hardware operations. It uses core Lean only, with no Mathlib.

## Status

**The code is written, but it has not yet been compiled or run through the Lean kernel.** The Lean
toolchain could not be run in the environment where it was written, so treat every theorem below as
a stated claim until `lake build` passes.

## What is in it

| File | Contents |
|---|---|
| `QBFLean/ZOmega.lean` | Exact amplitudes in ℤ[ω], ω = e^{iπ/4}: ring operations, conjugation, `√2 = ω − ω³` |
| `QBFLean/Matrix.lean` | List vectors and matrices; scaled matrices `m / √2^k`; exact equality; concurrence of a two-qubit state |
| `QBFLean/Gates.lean` | I, X, Z, H, S, T, CZ, CS, CNOT |
| `QBFLean/Fluxon.lean` | The chip's three operations: `split` (the 50:50 beam splitter), `shift n` (rail phase nπ/4), `collide n` (phase nπ/4 on \|11⟩) |
| `QBFLean/Theorems.lean` | Exact statements, each proved with `by decide`. They cover: collide π = CZ, shift·split·shift = H, two splits = X, unitarity, maximal entanglement, the concurrence law for every Δ = nπ/4, and the Bell pair |
| `QBFLean/Compiler.lean` | Gate → operation compiler, with `compileGate_correct` for every gate and the Bell circuit end to end |

## Build

```bash
# needs Lean 4.33.0 (see lean-toolchain), e.g. via elan
lake build
```

## Not covered

- **Continuous physics.** The sweet spot, noise and leakage need real analysis; that is the next
  step, with Mathlib. They are covered numerically by the Python simulation in `../simulations`.
- **Composition of circuits.** Correctness for whole circuits is proved for specific circuits (the
  Bell circuit), not yet in general, which needs associativity of the matrix product.
