# results log

Append-only. Dated entries, newest last. Interpretations here are working notes, not conclusions.

## 2026-08-01, frontier behavioral sweeps (bedrock)

Models: DeepSeek R1-671B (us.deepseek.r1-v1:0), DeepSeek V3.2 (non-reasoning counterpart). Families: mod arithmetic (p=97), variable chains. n=30 per cell, free and direct conditions, full data in results/raw/p1_*_r1_671b.jsonl and p1_mod_v32.jsonl.

Accuracy: R1-671B free holds ~100 percent through d=48 (mod) and d=64 (var); V3.2 free the same through d=48 with traces roughly 40 percent shorter at matched d. V3.2 direct is near zero at every d including d=1 (23 percent). Raw inspection of d=1 direct outputs shows genuine failures, not harness artifacts: bare numeric answers, with errors like reporting -18 where the subtraction was done but the mod reduction skipped. One forward pass reliably executes one arithmetic op here but not two.

Externalization: at ceiling (fraction ~1.0) in free generation for both models at every difficulty measured. No load-dependent onset is visible in free generation on these families; the write policy is saturated from d=1. This was one of the anticipated outcome patterns (hypotheses.md, phase 1 outcome a). Consequences: the onset axis must come from constrained regimes (token budgets), interventions, and the habit-vs-necessity gap, defined as the distance between where models start writing (immediately) and where writing becomes necessary (the direct cliff, which for V3.2 is d=1).

Matcher calibration (permutation control, matching each trace against a different instance's intermediates at the same difficulty): variable chains are clean, false-positive fraction 0.00 to 0.08 across d=2 to 64 against a true fraction of 1.00. Mod-97 is not clean at high d: false-positive fraction climbs from 0.10 (d=1) to 0.72 (d=48) because long traces mention most of 0..96 by chance. Mod-97 externalization numbers therefore need chance-correction, and variable chains are the primary externalization family going forward. Candidate fix for future mod runs: larger modulus.

Caveat logged: the surface matcher says written; whether written values are read back is gate B's question, and the causal definition of externalization (corrupt the written value, see if the answer moves) remains the ground truth to reconcile against on a subsample.
