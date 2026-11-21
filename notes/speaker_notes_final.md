# Speaker notes: Atom-by-Atom Silicon (final deck, 33 slides)

Same text as the speaker notes inside atom_by_atom_silicon_final.pptx. Physics, EE and maths focus; derived numbers use standard constants and the values on the slides.

## 15-minute timing plan

Slides 1–29 are about 3,281 words, roughly 22 minutes read aloud. For 15 minutes, keep each slide's equation and its one worked number, and save the "Likely question" lines for Q&A.

| Slides | Block | Target |
|---|---|---|
| 1–2 | Title, the story in four acts | 0:45 |
| 3–8 | Act 1: why single atoms | 2:30 |
| 9–15 | Act 2: how it's built | 3:30 |
| 16–24 | Act 3: does it work? | 5:00 |
| 25–28 | Act 4: how it scales | 2:15 |
| 29 | Takeaways | 0:30 |
| 30–33 | Q&A equation sheets and backup (not presented) | – |
| **Total** | | **14:30** |

## Slide 1: Title

This talk is about a transistor-like device whose active region is one atom: a phosphorus or arsenic donor in silicon, placed with a scanning tunnelling microscope. Physically, the donor is a hydrogen atom embedded in a semiconductor: one extra electron bound by a screened Coulomb potential. In EE143 terms, every step is a process you know, a resist, lithography, gas-phase doping, an activation anneal, epitaxy, etch and metal, scaled down to a resist one atom thick and a dose of one molecule. The render behind me is the diamond-cubic lattice, a = 5.431 Å, with a 2×2 arsenic register. Likely question: is the image data? No, it's a render; every micrograph later is measured.

_114 words_

## Slide 2: The story in four acts

Three quantities run through the whole talk. Precision: one lattice site on Si(001) is 0.384 nm, and that is the placement error we can achieve. Yield: if each site works with probability p, an n-site array works with probability p to the n, so p must be very close to one. Speed: a tip writes about 100 atoms per second, which sets the throughput limit. Act one asks why a single donor is a good qubit, act two builds it, act three tests it, from conductance to entanglement, and act four confronts the write-speed problem. Keep the question in mind: how do you put exactly one atom exactly where you want it?

_112 words_

## Slide 3: A single donor atom is a natural qubit

Treat the donor as hydrogen in a dielectric. The effective Bohr radius is a_B = ε_r (m_e/m*) a_0, so silicon's large permittivity and small effective mass stretch hydrogen's 0.053 nm to about 2 nm. Two spins come for free: the electron and the phosphorus nucleus with I = 1/2, giving a 2 × 2 = 4-level system. Electron transitions are driven by ESR, nuclear ones by NMR. Readout converts spin to charge: a spin-up electron can tunnel into a nearby single-electron transistor, a spin-down one cannot, and the SET current changes. In isotopically purified ²⁸Si there are no stray nuclear spins, which is why ion-implanted donors there reach 35.6 s coherence and gates near 99.99%. Likely question: is it really hydrogen-like? To first order; silicon's six conduction-band valleys split the ground state.

_132 words_

## Slide 4: Why one site matters: wavefunction overlap

Two-qubit gates use exchange, J, which comes from wavefunction overlap. For hydrogenic envelopes, |ψ|² falls as e^(−2r/a_B), so overlap, and roughly J, decays exponentially with donor spacing R. A quick estimate: moving one donor by one lattice site, 0.384 nm, multiplies the envelope term by e^(−0.384), about 0.68, a 30% change in coupling from a single-site error, before any valley effects. Silicon's six conduction-band valleys add interference that makes J oscillate site to site, which is why precision matters even more. The map is drawn to scale: two donors 13 nm apart on the real surface lattice. Likely question: can't you tune J with gates? Yes, but only within a window set by placement.

_114 words_

## Slide 5: The problem: implantation can't place one atom

Ion implantation is a Poisson process. If the mean number of ions per site is λ, the probability of exactly one is λe^(−λ). Differentiate: the maximum is at λ = 1, where P(1) = 1/e ≈ 36.8%. So without counting ions, no choice of dose gives better than 37% single occupancy; the bars are that distribution. Even with near-perfect ion detection, 99.85% at 14 keV, the stopping position is random: straggle spreads each ion over nanometres. Placement is set by ion–solid scattering statistics, not by the crystal lattice. STM placement is lattice-registered, ±1 site, and arsenic windows give 97 ± 2% single occupancy. Likely question: what about lower energy? Straggle shrinks but never reaches one lattice site.

_117 words_

## Slide 6: The answer: write the device atom by atom

Here is the device as an EE spec sheet. Substrate: Si(001), isotopically enriched ²⁸Si for qubits. Dopants: P from phosphine or As from arsine. Placement: ±0.384 nm. Leads: δ-doped sheets near 10¹⁴ cm⁻², under 1 nm thick, which is a 2D degenerate electron gas. Activation: 100% of placed phosphorus. The Kane architecture on the right needs B ≈ 1 T and T ≈ 0.1 K so that the electron's Zeeman energy dwarfs kT and the spin is polarized, with A-gates tuning hyperfine and J-gates tuning exchange between donors about 10 nm apart. Likely question: why millikelvin? Thermal energy kT must sit far below the Zeeman splitting so the spin starts in a known state.

_114 words_

## Slide 7: 30 years: from one H atom to 11 qubits

Read the timeline as a sequence of solved physics problems. 1994: a tip removes hydrogen from silicon by inelastic electron excitation of the Si–H bond, which gives a lithography. 1998: the proposal that donor nuclear spins are qubits. 2003: single phosphorus atoms placed deliberately. 2012: a transistor whose channel is one atom, showing discrete atomic levels in transport. 2019: a fast exchange gate and three-dimensional stacking. 2020 to 2024: arsenic chemistry pushes single-atom yield to 97%, and photons replace the tip for coarse patterning. 2025: four- and eleven-qubit processors. Each step reused the same recipe: passivate, pattern, dose, anneal, cap. Likely question: why so slow? Each step needed a new measurement capability.

_112 words_

## Slide 8: The researcher: Neil J. Curson (UCL)

Neil Curson's group at UCL works on the materials physics underneath this platform. Three threads. Dopant chemistry: replacing phosphine with arsine, whose dissociation is about a thousand times faster. In Arrhenius terms that is like lowering the barrier by kT ln 1000 ≈ 0.18 eV at room temperature, assuming similar prefactors. Metrology: imaging buried layers non-destructively with X-ray fluorescence, and using photoemission to resolve sub-nanometre electron confinement. Scaling: showing that extreme-ultraviolet photons can strip the same hydrogen resist. Also arsenic in germanium, which incorporates at room temperature. The common theme is controlling a surface reaction one molecule at a time. Likely question: why arsenic? Faster dissociation needs fewer free sites, so smaller windows.

_113 words_

## Slide 9: The process: 11 steps, each an EE143 module

This is the process traveler, with the EE143 module for each step. The thermal history is the key design constraint: hot steps first, then everything at or below 500 °C. Steps one to three prepare and passivate the surface. Step four is the lithography. Steps five and six are gas-phase doping and activation, at 350 °C. Steps seven and eight bury the dopants by epitaxy at 250 °C. Steps nine to eleven are alignment, reactive ion etching, aluminium contacts and electrical test. The design rule is diffusion: with D = D₀ e^(−E_a/kT), every step after patterning keeps 2√(Dt) far below one lattice site. Likely question: which step limits throughput? Step four, the tip.

_113 words_

## Slide 10: Steps 1–3 · Clean surface, 1-atom resist

Surface preparation. An outgas above 8 hours at 600 °C and flashes to about 1200 °C desorb the native oxide and carbon and leave the 2×1 dimer reconstruction. All in ultra-high vacuum below 5×10⁻¹¹ mbar. Why so low? Kinetic theory: at 10⁻⁶ Torr a surface collects about a monolayer per second, so at 10⁻¹¹ mbar a monolayer takes on the order of a day. Then atomic hydrogen at 330 °C, 5×10⁻⁷ mbar for 5 minutes, terminates every dangling bond. That monolayer is the resist: chemically inert where present, reactive where removed. Its contrast ratio is set by chemistry, not by optics. Likely question: why 330 °C? Hot enough for ordered monohydride, below hydrogen desorption.

_114 words_

## Slide 11: Step 4 · Writing with the tip

STM lithography is controlled tunnelling. Current scales as I ∝ V e^(−2κd), with κ = √(2mφ)/ħ ≈ 1 Å⁻¹ for a barrier of a few eV, so each ångström of tip height changes current by roughly e², 7 to 8 times. That exponential sensitivity is why the tip resolves single atoms. Writing uses higher bias to break Si–H bonds by electron excitation. Check the line dose: current over speed, 10 nA ÷ 10 nm/s = 1 C/m, which is the quoted 10⁻² C/cm. Arsenic windows use 3.5 V and 3000 pA at 50 nm/s, two dimers each, on a 4.6 nm pitch, twelve lattice vectors. Likely question: e-beam analogy? Yes; here dose is charge per length, and the resist is one atom.

_122 words_

## Slide 12: Step 5 · Dosing: phosphine vs arsine

Dosing is gas-surface kinetics. The impingement flux is Φ = p/√(2πmkT). For arsine, mass 78 amu, at 5×10⁻⁹ mbar and 300 K, that gives about 9×10¹¹ molecules per cm² per second. Over 10 minutes, about 5×10¹⁴ arrivals per cm², roughly 0.8 per surface site. So every window sees order one molecule, and the hydrogen resist rejects the rest. Phosphine then loses hydrogens stepwise over minutes, needing free sites for each fragment; arsine dissociates about a thousand times faster, in tens of seconds. Saturated arsenic coverage is 0.24 ± 0.04 monolayer, a quarter of the sites. Likely question: why not a full monolayer? Coverage stops at 0.24 ML whatever the dose rate, so surface chemistry, not gas supply, sets the limit.

_120 words_

## Slide 13: Step 6 · Incorporation anneal

Incorporation is an activated process with a thermal window. At 350 °C, kT ≈ 54 meV: enough for the arsenic or phosphorus to exchange into the top silicon layer, but below the 380 °C onset where hydrogen starts desorbing and the resist fails. A 30-kelvin window separates working from failing. Each incorporated arsenic ejects exactly one silicon atom to the surface, so the reaction is a substitution, As in, Si out, and counting ejected silicon adatoms counts dopants. That is in-situ metrology at single-atom resolution. In EE143 terms this is the drive-in and activation anneal, with a diffusion length of essentially zero. Likely question: what limits the window? The Si–H bond desorption barrier.

_113 words_

## Slide 14: Steps 7–8 · Burying the dopants

Burying the dopants is a thermal-budget optimisation. Epitaxial quality wants higher temperature, dopant confinement wants lower. Phosphorus grown over at a constant 250 °C segregates about 5 nm toward the surface. For arsenic: 2 nm at room temperature to lock the atoms, a 500 °C, 15-second RTA that leaves a confined, electrically active layer, then 28 nm at 250 °C. At 0.003 nm/s, 28 nm takes 9333 seconds, about 2.6 hours. Bulk diffusion using the textbook Arrhenius parameters gives 2√(Dt) around 10⁻⁴ nm even for the RTA step, so any broadening comes from surface segregation during growth, not bulk diffusion. Likely question: why not grow everything cold? Below a critical thickness cold silicon grows epitaxially; beyond it, the film turns amorphous.

_121 words_

## Slide 15: Steps 9–11 · Back to the outside world

Connecting to the buried device is ordinary microfabrication with extreme alignment. Etched registration markers and a combined STM–SEM, or Kelvin-probe imaging of the buried pattern, let you overlay contacts with 95% yield across more than 150 devices. The layer itself is invisible to optics: it is a 2D electron sheet 30 nm down. Hall bars are 20 × 200 µm², defined by optical lithography and reactive ion etching, with aluminium deposited into holes etched through the δ-layer to make ohmic contact. Transport is measured at 1.8 K; qubits run at millikelvin. Likely question: why does aluminium make an ohmic contact? The δ-layer is degenerately doped, so the barrier is thin enough to tunnel through.

_114 words_

## Slide 16: Proof 1: the buried δ-layer conducts

Electrical proof uses sheet resistance. For a 2D sheet, R_s = 1/(q N_s μ). Measured: 1.6 kΩ per square and μ = 28 cm²/V·s. Solve: N_s = 1/(1.6×10⁻¹⁹ × 1600 × 28) ≈ 1.4×10¹⁴ cm⁻². Compare with the surface atom density, 6.78×10¹⁴ cm⁻²: that is about 0.24 monolayer, matching the saturation coverage measured by STM. Activation is 81%, or 88% after a 560 °C anneal. Photoemission shows the electrons confined to less than 1 nm, with arsenic confining better than phosphorus. X-ray fluorescence moves dopants less than 0.2 Å. Likely question: why is mobility low? At 10¹⁴ cm⁻² in one atomic plane, electrons scatter off the ionised dopants they came from.

_111 words_

## Slide 17: Proof 2: one atom, then one transistor

Two existence proofs. Left: single phosphorus atoms in desorption sites about 1 nm across, three dimers, written at 4 V and 1 nA, dosed and annealed at 350 °C, landing about 12 nm apart on one dimer row. Right: a transistor whose island is one phosphorus atom. Its transport shows Coulomb blockade: the charging energy e²/C of a single atom is large, so current flows only when a discrete atomic level aligns with the leads, giving sharp conductance peaks versus gate voltage at millikelvin. Likely question: why does it work at liquid helium? The single-atom charging energy is far above kT at 4 K.

_104 words_

## Slide 18: The catch: every site must work

Yield is a product of probabilities. If each site independently succeeds with probability p, an n-site array succeeds with p^n. Phosphorus in an ideal three-dimer window: 63 ± 10%, below 70% in six-site windows. Then 0.7¹⁶ is 0.33%, and for fifty donors 0.63⁵⁰ is about 10⁻¹⁰. Invert the formula: the largest array with 50% yield is n = ln 0.5 / ln p, about 2 sites for phosphorus and 23 for arsenic at 0.97. The uncertainty band shows the sensitivity: arsenic at 95 to 99% gives 44 to 85% for sixteen sites. Likely question: are failures independent? The formula assumes it; correlated failures would change the statistics.

_107 words_

## Slide 19: Curson's fix: arsenic in a 4-site window

The arsenic solution is a geometric design rule. Arsine's fast dissociation means one molecule needs fewer free sites, so a four-site window, two dimers, admits exactly one. Single-atom yield is 97 ± 2%. The window covers one in four lattice sites, about 0.6 nm², giving 33% better positional precision than phosphorus. With p = 0.97, a defect-free 2×2 array has probability 0.97⁴ ≈ 0.89, and it was achieved. Iterating lithography and dosing on failed sites raises the effective p toward one, because a second attempt only multiplies the failure probability. Likely question: why not three sites? Smaller windows let hydrogen recapture the site before arsine adsorbs.

_106 words_

## Slide 20: Beyond Si:P: new dopants, new hosts

The same chemistry generalises. On germanium, arsine incorporates at room temperature with no anneal, and hydrogen leaves by 330 °C. That removes a thermal step: if incorporation is spontaneous at 300 K, the activation barrier is low enough that kT ≈ 26 meV suffices. Bismuth is the other direction: a heavy donor with a large nucleus, delivered by triphenyl-bismuth, a molecule about 1 nm across. Its phenyl groups detach near 140 °C and bismuth incorporates near 360 °C, close to the 380 °C limit of the hydrogen resist. Different precursor, different host, same toolbox. Likely question: why germanium? Germanium donors have larger Bohr radii and a stronger Stark effect, but this talk stays with silicon.

_115 words_

## Slide 21: The payoff: from devices to processors

Now the qubits. 2019: an exchange gate between two donor electrons in about 800 ps, and a three-dimensional device with layers aligned better than 5 nm and 97.9% single-shot readout. 2025: a four-qubit processor, three phosphorus nuclei sharing one electron, under 45 nm of ²⁸Si at 1.45 T and 15 mK, with CZ fidelities 99.32 to 99.65%. And an eleven-qubit processor: four- and five-donor registers 13 nm apart, read by a transistor 17 nm away, with Bell fidelities 99.5% inside a register and 97.0% across. Compare carefully: 2019 used natural silicon and electron spins, 2025 used ²⁸Si and nuclear spins. Likely question: why nuclear spins? Their coherence is far longer.

_110 words_

## Slide 22: The qubit as a spin Hamiltonian, and its spectrum

The physics in one equation: H = γₑ B·S + Σ γₙ B·Iᵢ + Σ S·Aᵢ·Iᵢ, electron Zeeman, nuclear Zeeman, hyperfine. Three nuclei with A = 6, 68 and 103 MHz shift the electron resonance by ±A/2 each, so there are 2³ = 8 ESR lines. Check: the span is A₁ + A₂ + A₃ = 177 MHz, exactly 39.157 minus 38.980 GHz. So the electron frequency reads out the nuclear register. Thermal check: hf at 39 GHz is 162 µeV, kT at 15 mK is 1.3 µeV, ratio 125, so the electron is fully polarised. Coherence: electron T₂* 28 µs, nuclei 0.5 to 1.3 ms. Likely question: why does A depend on E? Gate fields reshape the wavefunction at the nucleus.

_122 words_

## Slide 23: Entanglement, measured by full state tomography

Entanglement is verified by quantum state tomography: measure in many bases and reconstruct the density matrix ρ. For a Bell state, ρ has four equal corner elements of ½ and nothing else; fidelity is F = ⟨ψ|ρ|ψ⟩. All three nuclear pairs reach 96.8 to 97.7%. The GHZ state (|000⟩ + |111⟩)/√2 entangles all three nuclei at 96.2%. Grover's search on three qubits: with sin θ = 1/√8, success after r iterations is sin²((2r+1)θ). For r = 2 that is 94.5%; the hardware measured 93.46%, which is 98.87% of ideal. Likely question: why two iterations? A third would rotate past the target and lower the probability.

_105 words_

## Slide 24: Same atoms, new job: a quantum simulator

Dopant arrays also simulate many-body physics. The Hubbard Hamiltonian, H = −t Σ c†c + U Σ n↑n↓, has two energies: hopping t, set by tunnelling between dots, and on-site repulsion U. Since t falls exponentially with spacing, changing a 3×3 lattice from 4.1 to 10.7 nm tunes U/t from small, metallic, to large, Mott-insulating, where repulsion freezes the electrons. A 10-dot chain with alternating couplings realises the SSH model: when intracell hopping is weaker than intercell hopping, the band is topological, with edge states pinned at zero energy, seen as 2 conductance peaks instead of 10. Likely question: why dopants? Lithographic precision sets t directly.

_106 words_

## Slide 25: The next wall: throughput

Throughput is an EE scaling problem. A tip in precise mode writes about 100 atoms per second. One square centimetre of Si(001) has 6.78×10¹⁴ surface sites, so writing it serially takes 6.8×10¹² seconds, about 215,000 years. Faster modes reach 1000 nm per second but lose atomic precision. EUV lithography exposes the equivalent of 10¹⁴ nm per second, eleven orders of magnitude faster, because every photon in the field exposes in parallel. Even ten million tips across a 300 mm wafer remain orders of magnitude too slow for chip volumes. The answer has to be parallel exposure for everything except the qubit cores. Likely question: can tips run faster? Speed trades directly against precision.

_113 words_

## Slide 26: Scaling: EUV photons instead of a tip

EUV can strip the same hydrogen resist. Photon energy E = hc/λ: industrial 13.5 nm light is 92 eV, and hydrogen removal was shown at 109 eV. The mechanism is indirect: photons are absorbed in the silicon, which emits secondary electrons, and those electrons break Si–H bonds, the same bond-breaking physics as under the STM tip. The cost is dose: up to 18,000 J/cm², several minutes per chip with a 300 W source. Resistless EUV gratings at 75 nm half-pitch show the photon route works without organic resist. The proposed flow: EUV for leads and wiring, STM for qubit cores. Likely question: resolution? Diffraction, R = k₁λ/NA, limits EUV to roughly ten nanometres.

_113 words_

## Slide 27: Our prototype: a 2×2 arsenic register

Our prototype applies the design rules quantitatively. Four arsenic atoms, one per four-site window, on a 4.6 nm pitch, twelve lattice vectors. A single-electron transistor 17 nm away for readout, two gates 146.6 nm apart, all as δ-doped arsenic in one plane, buried 30 nm deep under epitaxial silicon. Expected yield: the four-site register succeeds with 0.97⁴ ≈ 89%. Scale to sixteen sites and p^n gives 61% for arsenic against 0.3% for phosphorus. So the register size you can build is fixed by chemistry, through p, not by lithographic resolution. Likely question: what sets the 17 nm SET spacing? Capacitive sensitivity versus tunnel coupling, an exponential trade-off.

_107 words_

## Slide 28: Prototype traveler, mapped to EE143

The traveler, as numbers. Hot steps first: 1200 °C flash, 600 °C outgas. After patterning, the maximum is a 500 °C, 15-second RTA, then 350 °C incorporation and 250 °C overgrowth. Why that ordering works: diffusion length is 2√(Dt) with D = D₀ e^(−E_a/kT), and the exponential makes the brief 500 °C step dominate the post-pattern budget while still moving dopants only about 10⁻⁴ nm. Compare our own lab: a 1050 °C drive-in for about 40 minutes moves phosphorus hundreds of nanometres. Same physics, opposite goal. Every row maps onto an EE143 module. Likely question: where is the risk? The RTA: too hot or too long and the δ-layer broadens.

_110 words_

## Slide 29: Takeaways: one atom, exactly where you want it

Three takeaways, each with its equation. Precision: placement is set by the lattice, ±0.384 nm, and exchange depends exponentially on spacing, so precision is mandatory. Yield: arrays succeed with p^n; arsenic raised p to 0.97 ± 0.02, moving the 50% array size from about 2 sites to about 23. Throughput: serial writing at 100 atoms per second cannot cover a wafer; parallel photon exposure on the same hydrogen resist is the bridge. And the quantum test passed: an eight-line ESR spectrum, Bell states near 97%, and Grover's search at 98.9% of ideal. Thank you. Likely question: what comes next? Larger registers, which is exactly the p^n problem.

_107 words_

## Slide 30: References (1 of 2)

Not presented. Q&A equation sheet. Bohr radius a_B = ε_r (m_e/m*) a_0. Poisson single occupancy λe^(−λ), maximum 1/e at λ = 1. Exchange envelope ∝ e^(−2R/a_B). Tunnelling I ∝ V e^(−2κd), κ ≈ 1 Å⁻¹. Line dose = I/v. Gas flux Φ = p/√(2πmkT). Sheet resistance R_s = 1/(qN_sμ). Hall density N_s = IB/(qV_H). Diffusion length 2√(Dt), D = D₀e^(−E_a/kT). Array yield p^n; 50% size n = ln 0.5/ln p.

_70 words_

## Slide 31: References (2 of 2)

Not presented. Q&A equation sheet, continued. Spin Hamiltonian H = γₑB·S + Σγₙ B·Iᵢ + Σ S·Aᵢ·Iᵢ; ESR lines at f₀ ± A₁/2 ± A₂/2 ± A₃/2. Polarisation needs hf ≫ kT: 162 µeV versus 1.3 µeV. Conditional flip off resonance ≤ Ω²/(Ω² + Δ²). Bell fidelity F = ⟨ψ|ρ|ψ⟩. Grover success sin²((2r+1)θ), sin θ = 1/√N. Hubbard H = −tΣc†c + UΣn↑n↓; Mott regime U ≫ t. EUV photon energy E = hc/λ; resolution R = k₁λ/NA.

_78 words_

## Slide 32: Backup · Alternate titles

Backup. Alternate titles, plus the 4×4 arsenic array in the image. With non-ideal windows, 10 to 12 of the 15 checked sites held single atoms, up to 80%. That number is a useful check on the p^n argument: at p = 0.8, a perfect sixteen-site array would occur 0.8¹⁶ ≈ 3% of the time, which is why the defect-free result was the 2×2 array with ideal windows. Window geometry matters as much as precursor chemistry. Use this slide only if asked how the larger array performed.

_86 words_

## Slide 33: Backup · Monte Carlo of 4×4 arrays

Backup. Monte Carlo check of the p^n law. Each simulated array fills sixteen sites with independent Bernoulli trials at p = 0.7 or p = 0.97, repeated 100,000 times. The perfect-array fraction converges to 0.3% and 61.3%, matching 0.7¹⁶ and 0.97¹⁶. The binomial standard error at 100,000 trials is √(p(1−p)/N), under 0.2%, so the agreement is not luck. The model assumes independent site failures; spatially correlated defects, such as a contaminated region, would make large arrays fail more often than p^n predicts. Use this slide if someone questions the statistics.

_90 words_
