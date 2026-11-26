# Does Lean say that? · speaker notes

TriFault · SF Lean Meetup · 60 minutes (50 talk + 10 Q&A). Generated from the `<aside class="notes">` in index.html.

## 1. Does Lean say that?

**Time:** 00:00–00:45

Hi, I'm Hanah, I founded TriFault. Tonight is a talk and a game. TriFault is a Lean game in front and a probabilistic-trit sampler behind it. The question in the title is the whole company: when Lean says a theorem is proved, does the Lean statement say what the English says? The crystal on the right is niobium dioxide. It will come back near the end, when we go from a verdict down to the atoms.

## 2. Hook: round 3's Lean

**Time:** 00:45–02:30

Read the English out loud first: a group of order 2p, p an odd prime, is cyclic or dihedral. Now the Lean. It compiles, modulo the sorry. Give the room twenty seconds. Click: Gemini-2.5-Pro, used as a judge in the Beyond Compilation study, gave it 10 out of 10. Click: two of the three human expert reviewers also gave it 10 out of 10. Click: it's false. Don't explain why yet. This exact statement comes back as the boss round, round 3, and by then you'll have the tools to see it. If someone in the room already sees it, ask them to hold it until round 3.

## 3. Lean checks the proof, not the meaning.

**Time:** 02:30–03:30

Everyone here knows the right half of this picture. The kernel checks that the proof proves the Lean statement, and it is very good at that. The left arrow is the one nobody checks mechanically: does the Lean statement mean what the English means? Today that check is a person reading carefully, or a model acting as a judge. If the formal statement is wrong, a perfect proof of it is a perfect proof of the wrong thing. Everything else in this talk is about that left arrow.

## 4. Compiling isn't the same as faithful.

**Time:** 03:30–04:45

This is the Beyond Compilation study, Zhang et al., 2026. They gave a tool-augmented GPT-5.2 agent 227 graduate-level textbook statements to formalize. 87.2 percent compile: 198 of 227. Only 57.7 percent are faithful to the English: 131 of 227. So about 30 points of "it compiles" is not "it means the same thing". This is not one bad model. All 8 systems they tested have a gap, from 1.3 to 29.5 points. And this isn't judge noise: human review confirms at least 23.8 of those 29.5 points are real translation errors.

## 5. Benchmarks have the same problem.

**Time:** 04:45–05:45

It's not just one study. miniF2F, the benchmark everyone reports on: Ospanov et al., 2025, found the formal and informal statements disagree on more than half the problems. And when you chain formalize-then-prove end to end you get about 36 percent, versus the 97 and 69 percent reported for the two steps separately. ProofNet#: Poiroux et al. found 31.8 percent of entries in the Lean 4 ports had formalization errors. Formal Conjectures has 2,615 Lean statements, 1,029 of them open problems. For the Erdős problem that Alexeev and Mixon resolved in 2025, the repo's Lean statement allowed modulus v equal to 0. These are careful teams. The problem is the task, not the people.

## 6. The judges disagree too.

**Time:** 05:45–07:15

These are counts I pulled from the Beyond Compilation released files. First: 18 of the 54 compiling outputs that humans confirmed don't say what the English says got a perfect 10 out of 10 from Gemini-2.5-Pro. A perfect score on a wrong statement. Second: in the random audit, 15 of 53 items, 28 percent, the human reviewers didn't all agree. Experts disagree on meaning. Third: on those same 53 items, the two AI judges split on 5. So you can't just pick one judge, human or model, and call it ground truth. You need something that weighs judges against each other and knows how far to trust each one. Pause here for questions about the data if people want them.

## 7. AI writes formal math faster than we can read it.

**Time:** 07:15–08:15

Why now. The volume is exploding. On 6 October 2026, OpenAI released 722 manuscripts in 372 result families from an unreleased model. Meta and NYU's ATLAS produced more than 45,000 Lean declarations from 26 textbooks. Goedel-Pset-v1 has 1.64 million autoformalized statements. Math Inc's Gauss produced about 200,000 lines for sphere packing in dimensions 8 and 24. The kernel can check every proof in all of that. Nobody can read every statement in all of that.

## 8. Human review is the bottleneck.

**Time:** 08:15–09:00

Mathlib had 308,129 declarations in February 2026. The Lean Pool paper shows it grows linearly, and the reason is good: strict human review. That review is exactly what keeps Mathlib trustworthy, and it doesn't scale to the volume on the last slide. In September 2025 Jason Rute asked on the Lean Zulip, in the machine learning for theorem proving stream, how anyone knows a large AI-generated project's statement means what it seems to mean. That thread is linked on the sources slide. That's the question we're building for. Note: paraphrase only, not a quote.

## 9. Today's tools are for experts.

**Time:** 09:00–10:30

Who else is working on this, and they're good. Lean Atlas, 2026, builds a dependency graph for human meaning review. It cuts the nodes you have to check by 94 to 99 percent on proof-heavy projects, and 27.3 percent on a definition-heavy one. Numina Fuse, 2026: agents formalize, then reviewer agents and people check meaning. Automatic judges: LeanScorer reaches kappa 0.766 against human labels, versus 0.603 for a plain LLM judge. AWS Automated Reasoning checks turn natural-language policies into logic and can return a TRANSLATION_AMBIGUOUS finding. The gap column is my read of where each stops. All of these assume an expert, or one judge, is the last word. Bottom line: no game, and nothing that learns whom to trust. That's the space we take. Spend the extra time here on questions about these tools.

## 10. A Lean game in front. A p-trit sampler behind.

**Time:** 10:30–12:00

The company in one picture. The front end is a game built on lean4game: people and AI judges vote on whether a Lean statement says what the English says. Every vote is a trit: 0 says it, 1 can't tell, 2 doesn't. The engine treats every statement as a probabilistic trit, a p-trit, and the whole thing as one energy function, Bayesian Dawid–Skene, which it samples with block Gibbs. The back end is the sampler. Today it runs in software. The plan is an FPGA p-computer next, and p-trit hardware after that, which is the second half of this talk. Be explicit: we have no hardware today. First, the game.

## 11. Let's play.

**Time:** 12:00–12:45

Here's the game. I show you an English statement and the Lean an AI agent wrote for it. You vote three ways. Says it: the Lean means what the English means. Can't tell: the English is ambiguous or you can't decide. Doesn't say it: the Lean means something else. Hands up for each option when I ask. In the product you also tap the exact span of Lean that's wrong and pick a reason, so a vote carries where and why, not just a verdict. Four rounds: a warm-up, round 2, a bonus, and the boss.

## 12. Round 1 · warm-up

**Time:** 12:45–13:45

Warm-up. English: any nonsingular n by n real matrix can be written as a product of elementary matrices. Here's the Lean the GPT-5.2 agent wrote, case A-002 in the study. Read it for thirty seconds. Then: hands up for says it. Can't tell. Doesn't say it. Hint if the room is stuck: look at the set inside the closure.

## 13. Round 1: the set is every matrix.

**Time:** 13:45–14:30

The graders mostly caught this one. AI judges: GPT-5.2 gave it 2, Gemini-2.5-Pro 4, Sonnet 5 gave 1. The three human reviewers: 4, 2, 2. Click: the set {E | True} is every matrix, not the elementary ones, so the closure is everything and the statement is trivially true. It doesn't even use hA. It holds for the zero matrix, which is certainly not a product of elementary matrices. Click: the p-trit engine says doesn't say it, with confidence 1.00. Easy one. They get harder.

## 14. Round 2

**Time:** 14:30–15:30

Round 2. English: the geometric series, sum of x to the k, does not converge uniformly on the open interval minus 1 to 1. Here's the Lean, case A-049. Thirty seconds. Hint if needed: read the theorem name, then look for where the interval shows up in the statement. Hands up: says it, can't tell, doesn't say it.

## 15. Round 2: the interval never appears.

**Time:** 15:30–16:30

Grades: GPT-5.2 gave 4, Gemini-2.5-Pro 5, Sonnet 5 [__]. Humans 2, 4 and 5. Everyone was unsure, nobody was confident it was right. Click: the theorem name says Ioo, but x ranges over all of ℝ. At x = 1 the partial sums are n, which go to infinity, while Mathlib's tsum of a non-summable series is defined to be 0. So the convergence fails at x = 1 alone, and the statement says nothing about the hard part of the exercise, which is behaviour near 1 inside the interval. Click: p-trit says doesn't say it, 1.00. This is a classic Lean trap: junk values for tsum.

## 16. Bonus · spot the sorry

**Time:** 16:30–17:15

Bonus round, quick. This is the Schwarz lemma, case A-011. There is a sorry that is not at the end of the proof. Find it and say what it does. Hands up when you see it, then vote.

## 17. Bonus: a sorry inside a hypothesis.

**Time:** 17:15–18:00

Grades: GPT-5.2 5, Gemini-2.5-Pro 6. Humans 1, 7 and 4, so the humans were all over the place. Click: the sorry sits inside the hypothesis hf, where it proves that ‖z‖ < 1 for every complex z, including z = 2. That's false, but sorry doesn't care. And hf asks for f to be differentiable on all of ℂ, which is not what holomorphic on the disk means. Click: p-trit says doesn't say it, 0.98. Point for the room: a sorry in a statement is not the same as a sorry in a proof, and a "no sorry in proofs" check won't catch it.

## 18. Round 3 · boss

**Time:** 18:00–19:30

The boss round, the statement from the start of the talk. Groups of order 2p, p an odd prime, are cyclic or dihedral. Case A-094. Take a full minute. Hint if needed: what does ≃* mean, and what is the multiplication on ZMod (2 * p)? Vote: says it, can't tell, doesn't say it. Count roughly and say the split out loud; it matters on the next slide.

## 19. Round 3: ZMod's multiplication is the ring's.

**Time:** 19:30–21:30

Grades. Gemini-2.5-Pro: 10. GPT-5.2: 5. Sonnet 5: 3. Human reviewers: 10, 10 and 4. So the human majority said "says it". Click: ≃* ZMod (2 * p) is a multiplicative equivalence with ZMod's ring multiplication, not with the cyclic group of order 2p. In that monoid 0 has no inverse, so no group can be multiplicatively isomorphic to it. The left disjunct is always impossible, and the statement really claims every group of order 2p is dihedral. That's false: the cyclic group of order 6 is abelian, and D_3 isn't. The study's own two-stage model review flagged it; the human majority missed it. Click: with only the AI judges, the p-trit engine says doesn't say it at 0.99. Add the human scores and it refuses to decide: 0.51 doesn't, 0.43 can't tell, 0.06 says it. That's the behaviour we want: when trusted raters disagree, don't guess, send it to more players. And note what this means for our own numbers: our "truth" is the human majority, and here the majority is wrong. That comes back on the caveats slide.

## 20. Lean can't check meaning. It can check a witness.

**Time:** 21:30–22:15

Here's how Lean comes back in. Lean can't check meaning. But a player who votes "doesn't say it" can often settle the question with a Lean proof: that the statement is false, or trivially true, or true in a case where the English says it isn't. The kernel checks that proof, so it's gold. For round 3 the witness is the cyclic group of order 6: plug it in and both disjuncts fail. For round 1 it's the one-line proof that the statement holds without hA. Note for Hanah: the Witness.lean file in deck/lean has not been compiled yet, so the slide shows only the sentence.

## 21. The verdict engine.

**Time:** 22:15–23:30

The verdict engine. Every vote is a trit: 0 means says it, 1 can't tell, 2 doesn't. Every statement j is a p-trit whose energy for state z is minus log of the prior pi z, minus the sum over raters i of log theta i at row z, column v i j, where v i j is rater i's vote on statement j. Theta i is rater i's 3 by 3 confusion matrix: how likely they are to vote each way given the true answer. Block Gibbs sampling alternates: sample every statement given the raters, then every rater's confusion matrix given the statements. Statisticians will recognise this: it's Bayesian Dawid–Skene from 1979, written as p-trit physics. Judge and human scores out of 10 become trits by the study's own rubric: 9 to 10 says it, 7 to 8 can't tell, 0 to 6 doesn't.

## 22. 120 real statements, 655 real votes.

**Time:** 23:30–24:15

This is the engine run on real data: the 120 statements in the study's human-audited set, and 655 real votes on them. Using the AI judges only, the engine says 51 say it, 29 can't tell, 40 don't. Everything here is real data from the released files; nothing is simulated. You can rotate it; I'll show it live in Q&A if there's time.

## 23. It decides 3 in 4 and flags the hard ones.

**Time:** 24:15–25:30

Results, using only the two AI judges as inputs, with 5-fold cross-validation. The engine decides 91 of the 120 statements at confidence 0.9 or more. That's the "3 in 4". On those 91 it agrees with the human majority on 87, 95.6 percent. The simple fixed rule, call it faithful only if both judges give 9 or more, gets 84 of the same 91, 92.3 percent. So the gain on the decided items is small and I won't oversell it. The more useful part is the other 29, the ones the engine refuses to decide and sends to players. On those, the fixed rule is right only 18 times, 62 percent, and the humans themselves split on 19 of the 29. So the engine is flagging exactly the items where people disagree. For reference, on all 120: the GPT-5.2 judge alone matches the human majority 87.5 percent of the time, Gemini-2.5-Pro 75.0 percent, the two-judge rule 85.0 percent.

## 24. It learns whom to trust.

**Time:** 25:30–26:15

This is the part a fixed rule can't do. From the confusion matrices, here's how often each rater votes "says it" when the statement doesn't say it. Gemini-2.5-Pro: 21 percent. Human reviewer R2: 13.5 percent. GPT-5.2: 4.5 percent. Human R3: 4.4. Human R4: 3.1. Sonnet 5: 2.6. Two things. First, these were learned with all raters together and no labels at all: the engine never saw the answers. Second, it matches what we saw in round 3: Gemini gave the false statement a 10. The engine learns that and discounts it, and it does the same for people. In the game, that's how a new player earns weight.

## 25. What this doesn't show yet.

**Time:** 26:15–26:45

Before anyone asks, the caveats. 120 statements is small, and half of them are a hard subset the study picked with its own check, so they are not a random sample. Our "truth" is the human majority, and round 3 just showed you the majority can be wrong. The 0.9 confidence threshold is a choice: other thresholds give other numbers. And none of this has been tested on new data or with real players. Next step: tonight's votes, then a public pilot.

## 26. The back end, down to the atom

**Time:** 26:45–27:00

Part 2. The verdict engine is a sampler. Here is the hardware path for that sampler, from the algorithm down to a single niobium bond. Every number from here on has a paper behind it, and I'll say which results are preprints, simulations or abstract-only.

## 27. A p-bit is a Gibbs sampler in one device.

**Time:** 27:00–28:30

A p-bit is a binary unit that is randomly plus or minus 1, with its bias set by an input current. Camsari, Faria, Sutton and Datta, Physical Review X 2017: m_i equals the sign of tanh of I_i minus a uniform random number, and I_i is a weighted sum of the neighbours plus a bias, scaled by I_0, which acts as an inverse temperature. If you update the p-bits one at a time, the network samples the Boltzmann distribution of the energy. That is exactly Gibbs sampling. The catch, in their words: updating the p-bits in parallel leads to incorrect results. The fix, from the full-stack review by Chowdhury et al. 2023: colour the graph, and update all p-bits of one colour together. That is exact. Our verdict model is bipartite: statements only touch raters' confusion matrices, and raters only touch statements. So two colours suffice: sample all statements, then all raters. That's the block Gibbs I described earlier.

## 28. Dedicated samplers beat GPUs on flips per second.

**Time:** 28:30–29:45

Why build hardware at all? Because sampling is the bottleneck, and dedicated samplers are much faster. Aadit et al., Nature Electronics 2022, Table I: flips per nanosecond for Ising sampling. A V100 GPU does 11.37, a TPU 12.88, the best GPU entry 29.85. Their sparse FPGA p-computer does 143.8, on irregular graphs, and the rate grows linearly with problem size because of graph colouring. A 2026 preprint from the same group runs a million p-bits on 18 FPGAs at 10 to the 12 updates per second: 17 times faster and 3.6 times less energy than an RTX 6000 Ada, at the same decay rate as exact Gibbs. Caveat, in their words: their fastest stale-boundary mode "does not establish convergence or unbiased sampling". For our label model today, software is fast enough at 120 statements. The hardware matters at the scale of slide 7: millions of statements and votes.

## 29. Physical randomness is cheap. NbOₓ isn’t there yet.

**Time:** 29:45–30:45

Energy per random bit. Singh et al., Nature Communications 2024, synthesised p-bits in a 7 nanometre design kit. A stochastic magnetic tunnel junction p-bit: about 2 femtojoules and 4 transistors; that 2 fJ figure is from an earlier paper. A digital p-bit with an LFSR random source: 145 femtojoules, 5,150 transistors. With a good generator, Xoshiro: 293 femtojoules, 11,546 transistors. And quality matters: they show LFSR p-bits get the Boltzmann distribution wrong in inference, not just optimisation. Now the honest line. The NbOx devices are much worse today: the 2023 KAIST NbOx p-bit is 128 picojoules per bit, and the 2026 p-trit is 2.4 nanojoules per trit for the oscillator alone. That's the gap a hardware roadmap has to close, and it's why our next step is an FPGA, not a chip.

## 30. Our votes are trits, so the sampler should be ternary.

**Time:** 30:45–31:45

Our variables have three values, so binary p-bits are the wrong shape. Encoding a trit in binary means one-hot, three p-bits with invalid states, or two bits with a wasted state. Duffee et al., Physical Review Applied 2025, built native multi-state p-dits on a 130 nanometre chip. For 3-partition of 14 numbers, 14 three-state p-dits needed about 34 times fewer trials to solution than 42 one-hot p-bits. And Whitehead et al., Nature Electronics 2023, sampled Potts models in hardware using single-photon avalanche diodes: 4 Potts nodes with 4 states each, 5 million samples, KL divergence 0.01 from the Boltzmann distribution. The cost of Potts: (q minus 1) squared weights per pair instead of 1. For us q is 3. A one-hot encoding of a trit in three bits uses 3 of 8 states; that's the 5 wasted states on the slide.

## 31. KAIST’s p-trit: a NbOₓ switch in an oscillator.

**Time:** 31:45–33:00

The device. Rhee and colleagues at KAIST, Advanced Science 2026, "NbOx Mott memristor-based oscillatory p-trit for ternary Potts machine". Bottom electrode: a 150 nanometre titanium nitride via in a planarized substrate from a commercial foundry. Switching layer: 20 nanometres of NbOx, reactively sputtered at 100 degrees C from a niobium target, argon to oxygen 50 to 4. Top: 50 nanometres of TiN, sputtered at room temperature. Then a rapid thermal anneal at 750 degrees for 2 minutes to crystallize the NbOx. The device sits in a Pearson–Anson oscillator: an 800 ohm series load resistor and a parallel capacitor. The model on the right is that stack; the paper doesn't report the substrate material or the via depth, so those parts are not to scale.

## 32. Two negative-resistance regions give three states.

**Time:** 33:00–34:15

Why three states. A current-swept I–V of this switch shows two negative differential resistance regions. The authors attribute the low-current one to "field-triggered thermal runaway", from Joule heating, and the high-current one to "a Mott-transition-related insulator–metal transition". In the oscillator circuit that gives five regimes as you raise the voltage. At 1.290 volts it stays off. At 1.340 it randomly either stays off or starts oscillating. At 1.500 it always oscillates. At 1.785 it randomly oscillates or latches on. At 1.850 it's on. Off, oscillating and on are the three states of the trit, and the two probabilistic boundaries are where the randomness lives. They attribute it to electrical and thermal noise. Note the path is ordinal: off to oscillating to on. There's no direct off-to-on transition, which comes back as a limitation.

## 33. One trit every 2.5 µs: first time to oscillate.

**Time:** 34:15–35:15

How you read a trit without counting peaks. The metric is first-time-to-oscillate: from the start of the voltage pulse to the first oscillation peak. The readout only asks whether that first peak lands inside a monitoring window, t_mtr, which they set to 2.5 microseconds. Comparator 1 against a 1.5 volt reference says whether the base state is on or off; comparator 2 against 0.8 volts clocks a D flip-flop on the first oscillation edge. Two bits: 00 is off, 01 or 11 is oscillating, 10 is on, mapped to Potts angles 0, 2π/3 and 4π/3. The probability follows 1 minus e to the minus lambda t, where lambda is the transition rate at that bias. Voltage sets the odds; a longer window gives a wider probabilistic voltage range. 2.5 microseconds per trit, 2.4 nanojoules for the oscillator, and the statistics hold with plus or minus 0.2 microseconds of timing jitter. Their circuit was a breadboard prototype with discrete comparators and a microcontroller.

## 34. What the p-trit paper shows, and what it doesn’t.

**Time:** 35:15–36:30

What the paper shows. A ternary Potts machine solving Max-3-Cut: on 20 random graphs with 14 vertices and 50 percent connectivity, the mean squared error against brute force was 4.35, versus 6.05 for a greedy p-bit Boltzmann machine that has to do three successive 2-cuts. Their abstract summarises it as about 30 percent higher accuracy at about 33 percent of the computational overhead. They also simulate ternary number partitioning with 50 numbers. What it does not show, and this room will ask. One: the Potts machine ran on microcontroller-emulated p-trits, because packaging and integration of the discrete NbOx devices aren't available yet; only the single p-trit was a real measured device. Two: their sampling rule, segmented probabilistic sampling, gives non-zero probability only to the two neighbouring states and sets the farthest to zero. That's an approximation to Gibbs, and the main text has no convergence proof for the ternary case. Three: the off-oscillate-on path is ordinal; there's no direct on-to-off transition, which they say slows convergence. Four: the main text reports no endurance or NIST randomness tests; those may be in the supplement, which I couldn't access.

## 35. NbO₂ is a distorted rutile with a 0.85 eV gap.

**Time:** 36:30–37:30

Down into the material. NbO2 at room temperature is body-centred tetragonal, space group I4_1/a, a = 13.70 and c = 5.98 angstroms: Cheetham and Rao 1976 by neutron powder diffraction, Bolzan et al. 1994 by Rietveld. It's a 2√2 by 2√2 by 2 superstructure of rutile. The conventional cell has 96 atoms; the primitive cell has 48. Above the transition it's plain rutile, P4_2/mnm; Bolzan measured a = 4.846 and c = 3.032 angstroms at 1300 K. The transition is at about 1081 K, 810 degrees C. Pynn and Wahila describe it as second order, with the distortion fading gradually over hundreds of degrees. The insulating phase has an indirect gap of about 0.85 to 0.88 eV, Berman et al. 2023's reading of optical and transport data; 0.85 eV is the 4 K optical onset. Note: the COD entries behind our models couldn't be opened from where this deck was built; the published papers above give these cells.

## 36. Down at the atoms: Nb–Nb pairs.

**Time:** 37:30–38:30

One chain of niobium atoms along c. In rutile they're evenly spaced: the Nb–Nb distance along the chain equals c, 3.03 angstroms. In the insulating phase they pair up. Our model has 2.74 angstrom pairs and 3.26 angstrom gaps; the measured room-temperature values in Berman et al. 2023 are 2.71 and 3.30, and Eyert quotes 2.7 and 3.3. I've kept both so nobody catches a mismatch: our model's numbers need checking against the CIF. The same zigzag spreads the niobium–oxygen bonds from 2.00 to 2.08 angstroms in rutile to 1.91 to 2.25. Wahila's EXAFS shows the short bond lengthening only slightly with temperature, about 2.71 to 2.75 angstroms from 0 to 400 degrees C.

## 37. The gap is mostly Peierls, partly correlation.

**Time:** 38:30–39:30

Why does pairing make an insulator? There's a real debate. Peierls: niobium has one d electron per atom; pairing along the chain splits the d-parallel band into bonding and antibonding halves and opens a gap. Eyert showed that plain DFT already opens one; Wahila et al. 2019 with hard X-ray photoemission and EXAFS conclude a second-order Peierls transition "with little to no contribution from electron correlations". On the other side, Brito, Aguiar, Haule and Kotliar, PRB 2017, with cluster DMFT: "not a purely Peierls-type insulator"; non-local correlations inside the dimers help open the gap, but correlations are weaker than in VO2. Berman et al. 2023 sit in the middle. The gap numbers show why it's contested: LDA 0.35 eV, DMFT 0.73, optical 0.85, tunnelling 1.05 plus or minus 0.29, HSE 1.48. The device papers, including KAIST's, call the switch Mott-related. For the hardware it doesn't change much; for this room it's a nice example of a statement whose meaning depends on who's saying it.

## 38. Inside the device, heat does the switching.

**Time:** 39:30–40:30

What happens inside a NbOx switch. Kumar et al., Nature Communications 2017, imaged devices while they operated, with X-ray microscopy at under 30 nanometre resolution. Both negative-resistance regions are driven by Joule heating, with temperature as the state variable. The first sets in around 400 K, a thermal runaway in Poole–Frenkel conduction through traps. The second is near 1000 K, the insulator–metal transition, which they model at 1070 K. Under voltage drive a hot spot above 1200 K forms and leaves a conducting channel roughly 100 nanometres across, while the rest of the device sits near 400 K. Endurance: Zhang et al., Nature Communications 2020, report over 10 to the 12 cycles for a NbOx neuron device. Pickett and Williams 2012 report sub-nanosecond switching, but I've only seen that abstract, so it's not on the slide.

## 39. From a verdict to an atom.

**Time:** 40:30–41:15

One picture of the whole stack. On the left, the verdict network, which is software today. A p-trit in hardware would be this TiN, NbOx, TiN device: a 150-nanometre via and a 20-nanometre film. The film is NbO2, whose crystal has a 13.70 by 13.70 by 5.98 angstrom cell with 96 atoms in the conventional cell. And inside the crystal, one niobium chain: paired when insulating, 3.03 angstroms evenly spaced when metallic. That was the last ten slides in one strip. From a verdict about a Lean statement down to an atom. We're at the left end today.

## 40. Open problem: prove the sampler samples.

**Time:** 41:15–42:45

An open problem for this room, because hardware samplers make claims nobody has formally checked. One: block Gibbs with a valid graph colouring leaves the Boltzmann distribution invariant. It's textbook, but I don't know of a Mathlib statement of it for finite Markov chains; if you do, tell me. Two: the KAIST p-trit rule gives zero probability to the farthest state. What distribution does that chain actually converge to, and how far is it from Boltzmann? Three: the million-p-bit FPGA system runs with stale boundary information, and its own authors say the empirical agreement "does not establish convergence or unbiased sampling". Four: we already have fault-tolerance proofs in Lean, vote5_two_faults and vote5_error_bound. The game checks that statements mean what they say; we'd like the sampler under it to be checked too. If that interests you, come talk to me afterwards.

## 41. The game is the data engine.

**Time:** 42:45–43:45

The product loop. One: you play. A three-way vote, you tap the span of Lean that's wrong, and you pick a reason tag. Two: the p-trit engine turns all votes into a verdict with a confidence. Three: anything with low confidence goes to more players, like round 3 did. Four: Lean witnesses, which the kernel checks, and expert-confirmed items become gold items. Gold items score everyone, players and AI judges alike, and that's what the trust on the last slide is learned against. Every round played makes the dataset bigger and the trust estimates sharper.

## 42. Every area, everywhere.

**Time:** 43:45–44:30

The game has worlds, like the Natural Number Game. Number theory, algebra, analysis, topology, combinatorics, probability, physics using Physlib, quantum, CS and crypto specs. Then, beyond formal math, plain-English policies. Levels go from competition math to undergrad, grad, and research level, using Formal Conjectures. We build on lean4game by Bentkamp and Eugster, which already runs the Natural Number Game and already supports translations, so "everywhere" means other languages too.

## 43. Who pays.

**Time:** 44:30–45:15

This is a plan, not traction. Four groups. AI-for-math labs and formalization companies: they need labels, audits of their outputs, and a benchmark for their own judges. Verification teams in industry: the same question in a different setting, does the spec say what the requirement says. Universities: teaching formalization, where the game is the course material. And grants: the AI for Math Fund has committed 35.1 million dollars; its 2026 round gave 17.1 million to 22 projects out of more than 470 applications.

## 44. Labs pay a lot for human judgment.

**Time:** 45:15–46:15

Business model. Players play free. Customers pay per audited statement, and pay subscriptions for labels and for the judge benchmark. Top players earn bounties. Prices: [__]. Why we think labs pay: they already pay a lot for human judgment. Mercor reached about 2 billion dollars in annualized gross revenue by June 2026, after a 350 million Series C at a 10 billion valuation in October 2025. LMArena raised a 150 million Series A at 1.7 billion in January 2026. In formal math specifically, Harmonic raised a 120 million Series C at 1.45 billion in November 2025, and Axiom Math a 200 million Series A at 1.6 billion in March 2026. These are comparables, not customers. The AI provers make the meaning check more urgent: a proof of the wrong statement is worth nothing to them. We see them as partners and potential customers, not competitors.

## 45. What compounds.

**Time:** 46:15–47:00

What compounds, as a plan. The labeled set of real misformalizations. The reason tags, which say why each one is wrong. Every rater's learned trust, human and AI. And Lean-witnessed gold items, which the kernel has checked. Two lessons from earlier science games. Foldit, 2011: players solved the structure of a retroviral protease that had stumped scientists for over a decade, in three weeks. But DARPA's Verigames, which tried to turn software verification into games, got smaller audiences and more one-time players than regular games, per a 2014 Naval Postgraduate School study. So we don't design for the mass market. We design for power players: people like this room.

## 46. What I've built.

**Time:** 47:00–48:00

What exists today. TriFault itself: a p-trit engine behind a Lean tactic called trifault. The p-trits propose, the kernel checks. It has found certificates for Schur S(3) at least 13, van der Waerden W(3,3) at least 27, and linear_combination certificates. Its fault tolerance is proved in Lean, in vote5_two_faults and vote5_error_bound. The verdict engine you just saw, and its run on the real study data. A quantum error correction library in Lean: 40 theorems, no sorry. My background: I benchmarked Ising models on quantum annealers at MIT Lincoln Lab. Team: [__].

## 47. The plan and the ask.

**Time:** 48:00–50:00

The plan, in order, no dates. One: tonight's live round, which you've just played. Two: a public beta on lean4game. Then the p-trit engine as an open library, and paid audits for [__] design partners. On the back end: move the sampler from software to an FPGA p-computer, then to NbOx p-trits with a hardware partner, [__]. And worlds beyond math, starting with plain-English policies. The ask. We're raising $[__]. We're looking for [__] design partners, especially AI-for-math labs and formalization teams. [__] Lean engineers. Hardware collaborators, for the open problem a few slides ago. And players: if you enjoyed tonight, you're who we're building for.

## 48. Close and questions

**Time:** 50:00–60:00

Close: Lean checks the proof. We check the meaning. Thank you. Ten minutes of questions. If there's time, demo the live 3D page: open slide 22 and rotate the verdict network, slide 31 for the device, or slides 35–36 for the crystal and chains. Backup slides: 49 and 50 are sources, 51 is short answers to likely questions. Likely questions: Isn't this just LLM-as-judge? The judges are inputs; the engine learns how far to trust each from gold items and flags disagreement. Gemini-2.5-Pro alone matches the human majority 75.0 percent on the 120. Why p-trits? It is Bayesian Dawid–Skene; p-trits give the same sampler TriFault runs, which runs natively on p-trit hardware. Who labels gold? Lean witnesses plus expert-confirmed mismatches. Gaming? Gold items score every player; trust is learned per player. Bad English? That's what can't tell is for. Why would AI provers pay? Their outputs only count if the statements mean what they say.

## 49. Sources: problem and game

**Time:** backup, not timed

All sources. Every number on a slide has a short source line on that slide; the full links are here. Show only if asked.

## 50. Sources: hardware and materials

**Time:** backup, not timed

Hardware and materials sources. Preprints: Aadit et al. 2026. Licence of the KAIST 2026 figures not yet confirmed, so none of their figures are reproduced; the device model is ours.

## 51. Short answers

**Time:** backup, not timed

Short answers to the six questions I expect. Use the line on the slide, then expand from the slide it points back to: judges and trust are slides 23 and 24; p-trits are slides 21 and 27–34; gold items are slides 20 and 41. On "runs natively on p-trit hardware": be precise. KAIST's p-trit rule is an approximation to Gibbs and their Potts machine was emulated (slide 34).
