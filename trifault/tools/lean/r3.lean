theorem group_order_two_mul_odd_prime_iso_cyclic_or_dihedral
    {G : Type*} [Group G] [Fintype G] (p : ℕ)
    (hp : Nat.Prime p) (hpodd : p % 2 = 1)
    (hcard : Fintype.card G = 2 * p) :
    Nonempty (G ≃* ZMod (2 * p)) ∨ Nonempty (G ≃* DihedralGroup p) := by
  sorry
