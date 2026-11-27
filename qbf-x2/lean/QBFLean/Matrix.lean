import QBFLean.ZOmega

/-!
# Exact vectors and matrices

Vectors and matrices are lists over `ℤ[ω]`, so equality is decidable by computation. A scaled
matrix `SMat` stands for `m / √2^k`. Two scaled matrices are compared exactly by cross-multiplying
with powers of `√2`, which is itself an element of `ℤ[ω]`.
-/

namespace QBFLean
open ZOmega

abbrev Vec := List ZOmega
abbrev Mat := List (List ZOmega)

def dot (u v : Vec) : ZOmega := (List.zipWith (· * ·) u v).foldl (· + ·) 0

def width (A : Mat) : Nat := (A.headD []).length
def col (A : Mat) (j : Nat) : Vec := A.map fun r => r.getD j 0
def transpose (A : Mat) : Mat := (List.range (width A)).map (col A)

def mmul (A B : Mat) : Mat :=
  let Bt := transpose B
  A.map fun row => Bt.map fun c => dot row c

def mapply (A : Mat) (v : Vec) : Vec := A.map fun row => dot row v

/-- Kronecker product; the left factor is the more significant index. -/
def kron (A B : Mat) : Mat :=
  A.flatMap fun ra => B.map fun rb => ra.flatMap fun x => rb.map fun y => x * y

def smul (s : ZOmega) (A : Mat) : Mat := A.map (·.map (s * ·))
def smulV (s : ZOmega) (v : Vec) : Vec := v.map (s * ·)
def adjoint (A : Mat) : Mat := (transpose A).map (·.map conj)

def ident (n : Nat) : Mat :=
  (List.range n).map fun r => (List.range n).map fun c => if r = c then 1 else 0

def diag (xs : Vec) : Mat :=
  (List.range xs.length).map fun r =>
    (List.range xs.length).map fun c => if r = c then xs.getD r 0 else 0

/-- The matrix `m / √2^k`. -/
structure SMat where
  k : Nat
  m : Mat
  deriving Repr

/-- The vector `v / √2^k`. -/
structure SVec where
  k : Nat
  v : Vec
  deriving Repr

namespace SMat
def mul (A B : SMat) : SMat := ⟨A.k + B.k, mmul A.m B.m⟩
instance : Mul SMat := ⟨mul⟩
def kron (A B : SMat) : SMat := ⟨A.k + B.k, QBFLean.kron A.m B.m⟩
def adjoint (A : SMat) : SMat := ⟨A.k, QBFLean.adjoint A.m⟩
def apply (A : SMat) (ψ : SVec) : SVec := ⟨A.k + ψ.k, mapply A.m ψ.v⟩

/-- `A` and `B` represent the same matrix: `A.m / √2^A.k = B.m / √2^B.k`. -/
abbrev Eqv (A B : SMat) : Prop := smul (sqrt2 ^ B.k) A.m = smul (sqrt2 ^ A.k) B.m
end SMat

namespace SVec
/-- `x` and `y` represent the same vector. -/
abbrev Eqv (x y : SVec) : Prop := smulV (sqrt2 ^ y.k) x.v = smulV (sqrt2 ^ x.k) y.v

/-- `Σ |vᵢ|²`, which must equal `2^k` for a normalised state. -/
def normNum (ψ : SVec) : ZOmega := (ψ.v.map normSq).foldl (· + ·) 0
abbrev Normalised (ψ : SVec) : Prop := normNum ψ = ofInt ((2 : Int) ^ ψ.k)

/-- For a normalised two-qubit state `ψ = v / √2^k`, its concurrence satisfies
`C(ψ)² · 2^(2k) = 4 · |v₀v₃ − v₁v₂|²`. `concNum` is the right-hand side and `concDen` is `2^(2k)`. -/
def concNum (ψ : SVec) : ZOmega :=
  4 * normSq (ψ.v.getD 0 0 * ψ.v.getD 3 0 - ψ.v.getD 1 0 * ψ.v.getD 2 0)
def concDen (ψ : SVec) : ZOmega := ofInt ((2 : Int) ^ (2 * ψ.k))
end SVec

end QBFLean
