/-!
# Exact amplitudes: the ring ℤ[ω], with ω = e^{iπ/4}

Every amplitude of the QBF-X2 primitives at their design settings, and of the Clifford+T gate
set, has the form `x / √2^k` with `x` in `ℤ[ω]`. Computing in `ℤ[ω]` makes every gate identity
in this package an exact, decidable equation that the Lean kernel checks. There is no floating
point anywhere in the proofs.
-/

namespace QBFLean

/-- The element `a + b·ω + c·ω² + d·ω³` of `ℤ[ω]`, where `ω = e^{iπ/4}` and so `ω⁴ = -1`. -/
structure ZOmega where
  (a b c d : Int)
  deriving DecidableEq, Repr, Inhabited

namespace ZOmega

/-- An integer, as an element of `ℤ[ω]`. -/
def ofInt (n : Int) : ZOmega := ⟨n, 0, 0, 0⟩

instance {n : Nat} : OfNat ZOmega n := ⟨ofInt (Int.ofNat n)⟩

instance : Add ZOmega := ⟨fun x y => ⟨x.a + y.a, x.b + y.b, x.c + y.c, x.d + y.d⟩⟩
instance : Neg ZOmega := ⟨fun x => ⟨-x.a, -x.b, -x.c, -x.d⟩⟩
instance : Sub ZOmega := ⟨fun x y => ⟨x.a - y.a, x.b - y.b, x.c - y.c, x.d - y.d⟩⟩

/-- Multiplication, reducing with `ω⁴ = -1`. -/
instance : Mul ZOmega := ⟨fun x y =>
  ⟨x.a * y.a - x.b * y.d - x.c * y.c - x.d * y.b,
   x.a * y.b + x.b * y.a - x.c * y.d - x.d * y.c,
   x.a * y.c + x.b * y.b + x.c * y.a - x.d * y.d,
   x.a * y.d + x.b * y.c + x.c * y.b + x.d * y.a⟩⟩

/-- `x ^ n` by repeated multiplication. -/
def pow (x : ZOmega) : Nat → ZOmega
  | 0 => 1
  | n + 1 => x * pow x n

instance : Pow ZOmega Nat := ⟨pow⟩

/-- `ω = e^{iπ/4}`. -/
def ω : ZOmega := ⟨0, 1, 0, 0⟩

/-- `i = ω²`. -/
def i : ZOmega := ⟨0, 0, 1, 0⟩

/-- `√2 = ω − ω³`. -/
def sqrt2 : ZOmega := ⟨0, 1, 0, -1⟩

/-- Complex conjugation: `ω ↦ ω⁻¹ = −ω³`. -/
def conj (x : ZOmega) : ZOmega := ⟨x.a, -x.d, -x.c, -x.b⟩

/-- `|x|² = x · x̄`. It is real, and lies in `ℤ[√2]`. -/
def normSq (x : ZOmega) : ZOmega := x * conj x

theorem ω_pow_four : ω ^ 4 = -1 := by decide
theorem ω_pow_eight : ω ^ 8 = 1 := by decide
theorem i_eq_ω_sq : ω ^ 2 = i := by decide
theorem i_mul_i : i * i = -1 := by decide
theorem sqrt2_mul_sqrt2 : sqrt2 * sqrt2 = 2 := by decide
theorem sqrt2_is_real : conj sqrt2 = sqrt2 := by decide
theorem ω_unit_modulus : normSq ω = 1 := by decide

end ZOmega
end QBFLean
