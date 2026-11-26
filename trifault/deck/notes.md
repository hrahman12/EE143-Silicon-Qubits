# Does Lean say that? · speaker notes

TriFault · SF Lean Meetup · 60 minutes (50 talk + 10 Q&A). Generated from the `<aside class="notes">` in index.html.

## 1. Does Lean say that?

**Time:** 00:00–00:45

Hi, I'm Hanah, I founded TriFault. Tonight is a talk and a game. The question in the title is the whole company: when Lean says a theorem is proved, does the Lean statement say what the English says? The crystal on the right is niobium dioxide. It will come back near the end, when we go from a verdict down to the atoms.

## 2. Hook: round 3's Lean

**Time:** 00:45–03:00

Read the English out loud first: a group of order 2p, p an odd prime, is cyclic or dihedral. Now the Lean. It compiles, modulo the sorry. Give the room twenty seconds. Click: Gemini-2.5-Pro, used as a judge in the Beyond Compilation study, gave it 10 out of 10. Click: two of the three human expert reviewers also gave it 10 out of 10. Click: it's false. Don't explain why yet. This exact statement comes back as the boss round, round 3, and by then you'll have the tools to see it. If someone in the room already sees it, ask them to hold it until round 3.

## 3. Lean checks the proof, not the meaning.

**Time:** 03:00–04:30

Everyone here knows the right half of this picture. The kernel checks that the proof proves the Lean statement, and it is very good at that. The left arrow is the one nobody checks mechanically: does the Lean statement mean what the English means? Today that check is a person reading carefully, or a model acting as a judge. If the formal statement is wrong, a perfect proof of it is a perfect proof of the wrong thing. Everything else in this talk is about that left arrow.

## 4. Compiling isn't the same as faithful.

**Time:** 04:30–06:00

This is the Beyond Compilation study, Zhang et al., 2026. They gave a tool-augmented GPT-5.2 agent 227 graduate-level textbook statements to formalize. 87.2 percent compile: 198 of 227. Only 57.7 percent are faithful to the English: 131 of 227. So about 30 points of "it compiles" is not "it means the same thing". This is not one bad model. All 8 systems they tested have a gap, from 1.3 to 29.5 points. And this isn't judge noise: human review confirms at least 23.8 of those 29.5 points are real translation errors.

## 5. Benchmarks have the same problem.

**Time:** 06:00–07:30

It's not just one study. miniF2F, the benchmark everyone reports on: Ospanov et al., 2025, found the formal and informal statements disagree on more than half the problems. And when you chain formalize-then-prove end to end you get about 36 percent, versus the 97 and 69 percent reported for the two steps separately. ProofNet#: Poiroux et al. found 31.8 percent of entries in the Lean 4 ports had formalization errors. Formal Conjectures has 2,615 Lean statements, 1,029 of them open problems. For the Erdős problem that Alexeev and Mixon resolved in 2025, the repo's Lean statement allowed modulus v equal to 0. These are careful teams. The problem is the task, not the people.

## 6. The judges disagree too.

**Time:** 07:30–10:00

These are counts I pulled from the Beyond Compilation released files. First: 18 of the 54 compiling outputs that humans confirmed don't say what the English says got a perfect 10 out of 10 from Gemini-2.5-Pro. A perfect score on a wrong statement. Second: in the random audit, 15 of 53 items, 28 percent, the human reviewers didn't all agree. Experts disagree on meaning. Third: on those same 53 items, the two AI judges split on 5. So you can't just pick one judge, human or model, and call it ground truth. You need something that weighs judges against each other and knows how far to trust each one. Pause here for questions about the data if people want them.

## 7. AI writes formal math faster than we can read it.

**Time:** 10:00–12:00

Why now. The volume is exploding. On 6 October 2026, OpenAI released 722 manuscripts in 372 result families from an unreleased model. Meta and NYU's ATLAS produced more than 45,000 Lean declarations from 26 textbooks. Goedel-Pset-v1 has 1.64 million autoformalized statements. Math Inc's Gauss produced about 200,000 lines for sphere packing in dimensions 8 and 24. The kernel can check every proof in all of that. Nobody can read every statement in all of that.

## 8. Human review is the bottleneck.

**Time:** 12:00–14:00

Mathlib had 308,129 declarations in February 2026. The Lean Pool paper shows it grows linearly, and the reason is good: strict human review. That review is exactly what keeps Mathlib trustworthy, and it doesn't scale to the volume on the last slide. In September 2025 Jason Rute asked on the Lean Zulip, in the machine learning for theorem proving stream, how anyone knows a large AI-generated project's statement means what it seems to mean. That thread is linked on the sources slide. That's the question we're building for. Note: paraphrase only, not a quote.

## 9. Today's tools are for experts.

**Time:** 14:00–17:00

Who else is working on this, and they're good. Lean Atlas, 2026, builds a dependency graph for human meaning review. It cuts the nodes you have to check by 94 to 99 percent on proof-heavy projects, and 27.3 percent on a definition-heavy one. Numina Fuse, 2026: agents formalize, then reviewer agents and people check meaning. Automatic judges: LeanScorer reaches kappa 0.766 against human labels, versus 0.603 for a plain LLM judge. AWS Automated Reasoning checks turn natural-language policies into logic and can return a TRANSLATION_AMBIGUOUS finding. The gap column is my read of where each stops. All of these assume an expert, or one judge, is the last word. Bottom line: no game, and nothing that learns whom to trust. That's the space we take. Spend the extra time here on questions about these tools.

## 10. Let's play.

**Time:** 17:00–18:00

Here's the game. I show you an English statement and the Lean an AI agent wrote for it. You vote three ways. Says it: the Lean means what the English means. Can't tell: the English is ambiguous or you can't decide. Doesn't say it: the Lean means something else. Hands up for each option when I ask. In the product you also tap the exact span of Lean that's wrong and pick a reason, so a vote carries where and why, not just a verdict. Four rounds: a warm-up, round 2, a bonus, and the boss.

## 11. Round 1 · warm-up

**Time:** 18:00–19:30

Warm-up. English: any nonsingular n by n real matrix can be written as a product of elementary matrices. Here's the Lean the GPT-5.2 agent wrote, case A-002 in the study. Read it for thirty seconds. Then: hands up for says it. Can't tell. Doesn't say it. Hint if the room is stuck: look at the set inside the closure.

## 12. Round 1: the set is every matrix.

**Time:** 19:30–20:30

The graders mostly caught this one. AI judges: GPT-5.2 gave it 2, Gemini-2.5-Pro 4, Sonnet 5 gave 1. The three human reviewers: 4, 2, 2. Click: the set {E | True} is every matrix, not the elementary ones, so the closure is everything and the statement is trivially true. It doesn't even use hA. It holds for the zero matrix, which is certainly not a product of elementary matrices. Click: the p-trit engine says doesn't say it, with confidence 1.00. Easy one. They get harder.

## 13. Round 2

**Time:** 20:30–22:00

Round 2. English: the geometric series, sum of x to the k, does not converge uniformly on the open interval minus 1 to 1. Here's the Lean, case A-049. Thirty seconds. Hint if needed: read the theorem name, then look for where the interval shows up in the statement. Hands up: says it, can't tell, doesn't say it.

## 14. Round 2: the interval never appears.

**Time:** 22:00–23:30

Grades: GPT-5.2 gave 4, Gemini-2.5-Pro 5, Sonnet 5 [__]. Humans 2, 4 and 5. Everyone was unsure, nobody was confident it was right. Click: the theorem name says Ioo, but x ranges over all of ℝ. At x = 1 the partial sums are n, which go to infinity, while Mathlib's tsum of a non-summable series is defined to be 0. So the convergence fails at x = 1 alone, and the statement says nothing about the hard part of the exercise, which is behaviour near 1 inside the interval. Click: p-trit says doesn't say it, 1.00. This is a classic Lean trap: junk values for tsum.

## 15. Bonus · spot the sorry

**Time:** 23:30–24:30

Bonus round, quick. This is the Schwarz lemma, case A-011. There is a sorry that is not at the end of the proof. Find it and say what it does. Hands up when you see it, then vote.

## 16. Bonus: a sorry inside a hypothesis.

**Time:** 24:30–25:30

Grades: GPT-5.2 5, Gemini-2.5-Pro 6. Humans 1, 7 and 4, so the humans were all over the place. Click: the sorry sits inside the hypothesis hf, where it proves that ‖z‖ < 1 for every complex z, including z = 2. That's false, but sorry doesn't care. And hf asks for f to be differentiable on all of ℂ, which is not what holomorphic on the disk means. Click: p-trit says doesn't say it, 0.98. Point for the room: a sorry in a statement is not the same as a sorry in a proof, and a "no sorry in proofs" check won't catch it.

## 17. Round 3 · boss

**Time:** 25:30–27:30

The boss round, the statement from the start of the talk. Groups of order 2p, p an odd prime, are cyclic or dihedral. Case A-094. Take a full minute. Hint if needed: what does ≃* mean, and what is the multiplication on ZMod (2 * p)? Vote: says it, can't tell, doesn't say it. Count roughly and say the split out loud; it matters on the next slide.

## 18. Round 3: ZMod's multiplication is the ring's.

**Time:** 27:30–30:00

Grades. Gemini-2.5-Pro: 10. GPT-5.2: 5. Sonnet 5: 3. Human reviewers: 10, 10 and 4. So the human majority said "says it". Click: ≃* ZMod (2 * p) is a multiplicative equivalence with ZMod's ring multiplication, not with the cyclic group of order 2p. In that monoid 0 has no inverse, so no group can be multiplicatively isomorphic to it. The left disjunct is always impossible, and the statement really claims every group of order 2p is dihedral. That's false: the cyclic group of order 6 is abelian, and D_3 isn't. The study's own two-stage model review flagged it; the human majority missed it. Click: with only the AI judges, the p-trit engine says doesn't say it at 0.99. Add the human scores and it refuses to decide: 0.51 doesn't, 0.43 can't tell, 0.06 says it. That's the behaviour we want: when trusted raters disagree, don't guess, send it to more players. And note what this means for our own numbers: our "truth" is the human majority, and here the majority is wrong. That comes back on the caveats slide.

## 19. Lean can't check meaning. It can check a witness.

**Time:** 30:00–31:00

Here's how Lean comes back in. Lean can't check meaning. But a player who votes "doesn't say it" can often settle the question with a Lean proof: that the statement is false, or trivially true, or true in a case where the English says it isn't. The kernel checks that proof, so it's gold. For round 3 the witness is the cyclic group of order 6: plug it in and both disjuncts fail. For round 1 it's the one-line proof that the statement holds without hA. Note for Hanah: the Witness.lean file in deck/lean has not been compiled yet, so the slide shows only the sentence.

## 20. A p-trit: three states, Boltzmann odds.

**Time:** 31:00–32:30

How the engine works. A p-trit is a probabilistic trit: three states, 0, 1, 2, each with Boltzmann odds, P of z equals e to the minus E of z over the sum over u of e to the minus E of u. Change the energies and you change the odds. This isn't only math. A KAIST team, Rhee et al. in Advanced Science 2026, built NbOx p-trits and a ternary Potts machine out of them. The device: a titanium nitride via 150 nanometres wide, 20 nanometres of NbOx, and a 50-nanometre titanium nitride top electrode. The model on the right is that stack. The paper didn't report the substrate material or the via depth, so those parts of the model are not to scale. To be clear: we run p-trits in software today. We don't have hardware.

## 21. Down at the atoms.

**Time:** 32:30–33:30

Down at the atoms, because this room likes to know what's underneath. NbO2 has chains of niobium atoms. In the insulating phase they pair up: 2.74 angstrom pairs with 3.26 angstrom gaps. In the metallic phase they're evenly spaced at 3.03 angstroms. The structures come from the Crystallography Open Database, entries 2106754, Cheetham and Rao 1976, and 1548821. The KAIST paper attributes the device's high-current switching to a Mott-related insulator–metal transition. Bulk NbO2 makes that transition at 1081 kelvin. Thirty seconds of fun; move on.

## 22. The verdict engine.

**Time:** 33:30–35:00

The verdict engine. Every vote is a trit: 0 means says it, 1 can't tell, 2 doesn't. Every statement j is a p-trit whose energy for state z is minus log of the prior pi z, minus the sum over raters i of log theta i at row z, column v i j, where v i j is rater i's vote on statement j. Theta i is rater i's 3 by 3 confusion matrix: how likely they are to vote each way given the true answer. Block Gibbs sampling alternates: sample every statement given the raters, then every rater's confusion matrix given the statements. Statisticians will recognise this: it's Bayesian Dawid–Skene from 1979, written as p-trit physics. Judge and human scores out of 10 become trits by the study's own rubric: 9 to 10 says it, 7 to 8 can't tell, 0 to 6 doesn't.

## 23. 120 real statements, 655 real votes.

**Time:** 35:00–36:00

This is the engine run on real data: the 120 statements in the study's human-audited set, and 655 real votes on them. Using the AI judges only, the engine says 51 say it, 29 can't tell, 40 don't. Everything here is real data from the released files; nothing is simulated. You can rotate it; I'll show it live in Q&A if there's time.

## 24. It decides 3 in 4 and flags the hard ones.

**Time:** 36:00–37:30

Results, using only the two AI judges as inputs, with 5-fold cross-validation. The engine decides 91 of the 120 statements at confidence 0.9 or more. That's the "3 in 4". On those 91 it agrees with the human majority on 87, 95.6 percent. The simple fixed rule, call it faithful only if both judges give 9 or more, gets 84 of the same 91, 92.3 percent. So the gain on the decided items is small and I won't oversell it. The more useful part is the other 29, the ones the engine refuses to decide and sends to players. On those, the fixed rule is right only 18 times, 62 percent, and the humans themselves split on 19 of the 29. So the engine is flagging exactly the items where people disagree. For reference, on all 120: the GPT-5.2 judge alone matches the human majority 87.5 percent of the time, Gemini-2.5-Pro 75.0 percent, the two-judge rule 85.0 percent.

## 25. It learns whom to trust.

**Time:** 37:30–38:30

This is the part a fixed rule can't do. From the confusion matrices, here's how often each rater votes "says it" when the statement doesn't say it. Gemini-2.5-Pro: 21 percent. Human reviewer R2: 13.5 percent. GPT-5.2: 4.5 percent. Human R3: 4.4. Human R4: 3.1. Sonnet 5: 2.6. Two things. First, these were learned with all raters together and no labels at all: the engine never saw the answers. Second, it matches what we saw in round 3: Gemini gave the false statement a 10. The engine learns that and discounts it, and it does the same for people. In the game, that's how a new player earns weight.

## 26. What this doesn't show yet.

**Time:** 38:30–39:00

Before anyone asks, the caveats. 120 statements is small, and half of them are a hard subset the study picked with its own check, so they are not a random sample. Our "truth" is the human majority, and round 3 just showed you the majority can be wrong. The 0.9 confidence threshold is a choice: other thresholds give other numbers. And none of this has been tested on new data or with real players. Next step: tonight's votes, then a public pilot.

## 27. The game is the data engine.

**Time:** 39:00–40:30

The product loop. One: you play. A three-way vote, you tap the span of Lean that's wrong, and you pick a reason tag. Two: the p-trit engine turns all votes into a verdict with a confidence. Three: anything with low confidence goes to more players, like round 3 did. Four: Lean witnesses, which the kernel checks, and expert-confirmed items become gold items. Gold items score everyone, players and AI judges alike, and that's what the trust on the last slide is learned against. Every round played makes the dataset bigger and the trust estimates sharper.

## 28. Every area, everywhere.

**Time:** 40:30–42:00

The game has worlds, like the Natural Number Game. Number theory, algebra, analysis, topology, combinatorics, probability, physics using Physlib, quantum, CS and crypto specs. Then, beyond formal math, plain-English policies. Levels go from competition math to undergrad, grad, and research level, using Formal Conjectures. We build on lean4game by Bentkamp and Eugster, which already runs the Natural Number Game and already supports translations, so "everywhere" means other languages too.

## 29. From a verdict to an atom.

**Time:** 42:00–43:00

One picture of the whole stack. On the left, the verdict network, which is software today. A p-trit in hardware would be this TiN, NbOx, TiN device: a 150-nanometre via and a 20-nanometre film. The film is NbO2, whose crystal has a 13.70 by 13.70 by 5.98 angstrom cell with 96 atoms. And inside the crystal, one niobium chain: 2.74 angstrom pairs when insulating, 3.03 angstroms evenly spaced when metallic. From a verdict about a Lean statement down to an atom. We're at the left end today.

## 30. Who pays.

**Time:** 43:00–44:30

This is a plan, not traction. Four groups. AI-for-math labs and formalization companies: they need labels, audits of their outputs, and a benchmark for their own judges. Verification teams in industry: the same question in a different setting, does the spec say what the requirement says. Universities: teaching formalization, where the game is the course material. And grants: the AI for Math Fund has committed 35.1 million dollars; its 2026 round gave 17.1 million to 22 projects out of more than 470 applications.

## 31. Labs pay a lot for human judgment.

**Time:** 44:30–46:00

Business model. Players play free. Customers pay per audited statement, and pay subscriptions for labels and for the judge benchmark. Top players earn bounties. Prices: [__]. Why we think labs pay: they already pay a lot for human judgment. Mercor reached about 2 billion dollars in annualized gross revenue by June 2026, after a 350 million Series C at a 10 billion valuation in October 2025. LMArena raised a 150 million Series A at 1.7 billion in January 2026. In formal math specifically, Harmonic raised a 120 million Series C at 1.45 billion in November 2025, and Axiom Math a 200 million Series A at 1.6 billion in March 2026. These are comparables, not customers. The AI provers make the meaning check more urgent: a proof of the wrong statement is worth nothing to them. We see them as partners and potential customers, not competitors.

## 32. What compounds.

**Time:** 46:00–47:30

What compounds, as a plan. The labeled set of real misformalizations. The reason tags, which say why each one is wrong. Every rater's learned trust, human and AI. And Lean-witnessed gold items, which the kernel has checked. Two lessons from earlier science games. Foldit, 2011: players solved the structure of a retroviral protease that had stumped scientists for over a decade, in three weeks. But DARPA's Verigames, which tried to turn software verification into games, got smaller audiences and more one-time players than regular games, per a 2014 Naval Postgraduate School study. So we don't design for the mass market. We design for power players: people like this room.

## 33. What I've built.

**Time:** 47:30–48:30

What exists today. TriFault itself: a p-trit engine behind a Lean tactic called trifault. The p-trits propose, the kernel checks. It has found certificates for Schur S(3) at least 13, van der Waerden W(3,3) at least 27, and linear_combination certificates. Its fault tolerance is proved in Lean, in vote5_two_faults and vote5_error_bound. The verdict engine you just saw, and its run on the real study data. A quantum error correction library in Lean: 40 theorems, no sorry. My background: I benchmarked Ising models on quantum annealers at MIT Lincoln Lab. Team: [__].

## 34. The plan and the ask.

**Time:** 48:30–50:00

The plan, in order, no dates. One: tonight's live round, which you've just played. Two: a public beta on lean4game. Three: release the p-trit engine as an open library. Four: paid audits for [__] design partners. Five: worlds beyond math, starting with plain-English policies. The ask. We're raising $[__]. We're looking for [__] design partners, especially AI-for-math labs and formalization teams. [__] Lean engineers. And players: if you enjoyed tonight, you're who we're building for.

## 35. Close and questions

**Time:** 50:00–60:00

Close: Lean checks the proof. We check the meaning. Thank you. Ten minutes of questions. If there's time, demo the live 3D page: open slide 23 and rotate the verdict network, or slide 20 for the device. Backup slides: 36 is sources, 37 is short answers to likely questions. Likely questions: Isn't this just LLM-as-judge? The judges are inputs; the engine learns how far to trust each from gold items and flags disagreement. Gemini-2.5-Pro alone matches the human majority 75.0 percent on the 120. Why p-trits? It is Bayesian Dawid–Skene; p-trits give the same sampler TriFault runs, which runs natively on p-trit hardware. Who labels gold? Lean witnesses plus expert-confirmed mismatches. Gaming? Gold items score every player; trust is learned per player. Bad English? That's what can't tell is for. Why would AI provers pay? Their outputs only count if the statements mean what they say.

## 36. Sources

**Time:** backup, not timed

All sources. Every number on a slide has a short source line on that slide; the full links are here. Show only if asked.

## 37. Short answers

**Time:** backup, not timed

Short answers to the six questions I expect. Use the line on the slide, then expand from the slide it points back to: judges and trust are slides 24 and 25; p-trits are slides 20 and 22; gold items are slides 19 and 27.
