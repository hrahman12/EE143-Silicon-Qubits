theorem holomorphic_maps_disk_abs_le_abs
    (f : {z : ℂ // ‖z‖ < 1} → {z : ℂ // ‖z‖ < 1})
    (hf : Differentiable ℂ fun z : ℂ => (f ⟨z, by
      sorry⟩ : ℂ))
    (h0 : (f ⟨0, by simp⟩ : ℂ) = 0) :
    ∀ z : {z : ℂ // ‖z‖ < 1}, ‖(f z : ℂ)‖ ≤ ‖(z : ℂ)‖ := by
  sorry
