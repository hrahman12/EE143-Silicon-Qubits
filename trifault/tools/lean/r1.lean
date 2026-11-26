theorem nonsingular_matrix_prod_elementary {n : Type*} [Fintype n] [DecidableEq n]
    (A : Matrix n n ℝ) (hA : IsUnit A.det) :
    A ∈ Subsemigroup.closure ({E : Matrix n n ℝ | True} : Set (Matrix n n ℝ)) := by
  sorry
