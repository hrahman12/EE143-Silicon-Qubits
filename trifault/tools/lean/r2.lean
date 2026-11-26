theorem geometric_series_not_tendsto_uniformly_on_Ioo :
    ¬ TendstoUniformly (fun n : ℕ => fun x : ℝ => (Finset.range n).sum (fun k => x ^ k))
        (fun x : ℝ => ∑' k : ℕ, x ^ k) Filter.atTop := by
  sorry
