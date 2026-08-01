# results log

Append-only. Dated entries, newest last. Interpretations here are working notes, not conclusions.

## 2026-08-01, frontier behavioral sweeps (bedrock)

Models: DeepSeek R1-671B (us.deepseek.r1-v1:0), DeepSeek V3.2 (non-reasoning counterpart). Families: mod arithmetic (p=97), variable chains. n=30 per cell, free and direct conditions, full data in results/raw/p1_*_r1_671b.jsonl and p1_mod_v32.jsonl.

Accuracy: R1-671B free holds ~100 percent through d=48 (mod) and d=64 (var); V3.2 free the same through d=48 with traces roughly 40 percent shorter at matched d. V3.2 direct is near zero at every d including d=1 (23 percent). Raw inspection of d=1 direct outputs shows genuine failures, not harness artifacts: bare numeric answers, with errors like reporting -18 where the subtraction was done but the mod reduction skipped. One forward pass reliably executes one arithmetic op here but not two.

Externalization: at ceiling (fraction ~1.0) in free generation for both models at every difficulty measured. No load-dependent onset is visible in free generation on these families; the write policy is saturated from d=1. This was one of the anticipated outcome patterns (hypotheses.md, phase 1 outcome a). Consequences: the onset axis must come from constrained regimes (token budgets), interventions, and the habit-vs-necessity gap, defined as the distance between where models start writing (immediately) and where writing becomes necessary (the direct cliff, which for V3.2 is d=1).

Matcher calibration (permutation control, matching each trace against a different instance's intermediates at the same difficulty): variable chains are clean, false-positive fraction 0.00 to 0.08 across d=2 to 64 against a true fraction of 1.00. Mod-97 is not clean at high d: false-positive fraction climbs from 0.10 (d=1) to 0.72 (d=48) because long traces mention most of 0..96 by chance. Mod-97 externalization numbers therefore need chance-correction, and variable chains are the primary externalization family going forward. Candidate fix for future mod runs: larger modulus.

Caveat logged: the surface matcher says written; whether written values are read back is gate B's question, and the causal definition of externalization (corrupt the written value, see if the answer moves) remains the ground truth to reconcile against on a subsample.

## 2026-08-01, gate b (read-back) and phase 1 on r1-distill-7b

Gate B, variable chains (the collision-free family), n=128 to 149 per difficulty: corrupting the last written mention of a mid-chain value flips the final answer in 31 percent of continuations at d=4, 42 at d=8, 50 at d=16, 36 at d=32. At d=32 the drop coincides with restates_clean jumping to 0.45: the model increasingly notices the edit and reasserts the clean value early in the continuation. Reading: written values are causally live (the CoT-as-projection position predicts near zero and is refuted at this scale), but the internal copy persists alongside (follows_clean 0.48 to 0.68 throughout), and at high d an active cross-check between tiers appears. The picture so far is redundant storage with verification, not strict write-then-evict. The eviction probe (2b) now has a sharper question: not whether the internal copy disappears, but whether its precision degrades once the written copy exists.

Gate B, mod-97: follows_corruption collapses from 0.44 (d=6) to 0.01 (d=12). Not interpreted: the matcher's false-positive rate at these difficulties means many corruptions likely hit coincidental number mentions rather than the step value. Mod-97 gate B needs collision-validated targeting before it counts.

Phase 1, 7B, free condition: mod arithmetic externalization runs 0.78 to 0.91 below d=6 and reaches 0.99 by d=12 (chance-correction pending given the mod-97 matcher issue); variable chains sit at 0.93 to 1.00 everywhere. Direct condition collapses by d=2 on all families (7B cannot do two serial ops without writing, matching the frontier result). Entity tracking gives the best difficulty cliff in free generation (0.97 at d=1 down to 0.18 at d=24) and is the designated family for the protection experiment; its externalization fraction is unmeasurable with the current matcher because every object name also appears in the prompt, so it needs a pattern-based measure (planned fix, not blocking).

Interim reading across the day: the write policy looks saturated at every scale measured in free generation, while read-back is substantial and difficulty-dependent. The load-sensitivity axis, if it exists, lives in constrained regimes and interventions, which is where the design now concentrates: gate A (capacity lesions) and the 1.5B/14B ladder are running, and a token-budget sweep on V3.2 is filling in the forced-selectivity axis.
