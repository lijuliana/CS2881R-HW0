# hardening: weaknesses, the plan to close them, and status

Honest self-critique plus the plan and current status, in one place. The goal of the hardening round was to turn the read-back result from "real but under-validated" into "validated and correctly scoped." Replication ran first on purpose: if the harness could not reproduce a known result, we would stop and fix the harness before trusting anything else.

## status at a glance (2026-08-04)

- Weakness 1, no replication: CLOSED. Truncation faithfulness reproduces Lanham (behavioral, API), and the A1 probe validates the probing machinery (white-box). See below.
- Weakness 2, causal result on a non-reasoning model: RESOLVING. Reasoning-model patch attempt (D) ran; if not clean we rescope to "language models" honestly.
- Weakness 3, patch specificity: CLOSED, with a stronger result than before. The residual is a readable value register (patch to an arbitrary value, the answer follows that value 0.76).
- Weakness 4, only synthetic tasks: CLOSED AS A NEGATIVE. Read-back does not fire on GSM8K because its intermediates are recomputable; read-back is recomputability-gated, not universal.

## the four crucial weaknesses, the fix, and where it landed

**1. No replication of any prior result.** We never reproduced an established finding on our own setup before extending it, so the harness had no validated anchor and the "we refute view X" claims rested on our framing of X.
- Fix A2 (behavioral, API): Lanham truncation faithfulness. Forcing an answer after a fraction f of the model's own CoT gives accuracy monotonic in f, collapsing when the late steps are removed (V3.2 0 to 0.97, Sonnet 0.32 to 1.00). Reproduces the load-bearing-CoT result on our tasks.
- Fix A1 (white-box, GPU): a ridge probe reads the answer out of the residual at R^2 up to 0.96 with the control at chance, validating the extraction and probing machinery the patch relies on. Caveat recorded: early decodability is inflated by the start-value confound, so we make no early-computation claim from the raw curve; a start-controlled probe (answer minus start) is running to isolate the computed part.

**2. The clean causal result is on a non-reasoning model.** The residual-patch centerpiece runs on Qwen2.5-7B-Instruct, chosen because the reasoning model re-solves after its think block, so the causal isolation is off the model class the paper is about.
- Fix D (GPU): attempt the patch on a reasoning distill, reading the value the think trace commits to before the post-think re-solve. Result pending. If it does not come out clean, rescope the paper from "reasoning models" to "language models," keeping the frontier behavioral read-back (V3.2, Sonnet, both reasoning-capable) and gate B (R1-distill) as the reasoning-model evidence.

**3. The patch needed a specificity control.** Restoring the value token's residual to clean and getting the clean answer invited "you injected the answer."
- Fix B (GPU): the swap control. Patch the residual to an arbitrary third value and the answer follows that value 0.76 [0.70, 0.82] (follows clean 0.00); patch to clean, follows clean 0.97; random patch, 0.00. The residual is a readable value register you can set to any value, not an injected answer. Stronger than the original restore-to-clean framing.

**4. Only synthetic toy tasks.** No real reasoning benchmark, so generality was asserted.
- Fix C (API): read-back on GSM8K. Negative: corrupting a written intermediate changes the answer 0.10 vs a 0.05 floor. Explained: a depth sweep shows read-back is 0.64 to 0.80 across d=3 to 16, so it is not depth; GSM8K intermediates are shallow functions of the givens and the model recomputes them. Finding: read-back is recomputability-gated. It carries genuinely serial, non-recomputable state, and does not fire when the model can just recompute. This scopes the central claim honestly.

## important, not fatal (open)

5. Corruption may measure local arithmetic-checking, not memory read-back. We did not fully separate corrupting a value on its own computation line from corrupting a later re-reference. The swap control (weakness 3) mitigates this, since a value the model never wrote is injected and read, but a per-line split would still sharpen it.
6. Thin statistics on some causal results. Protection is n=40 per cell, one model, one dose. The patch results now have CIs and a control battery but are still single-model; seeds and a second model would harden them.
7. Lesion validity is fuzzy. The resample ablation blends toward a bank that is off-distribution for neutral text (neutral KL 1.3 vs task KL 0.15), so what it removes is not fully characterized. A mean-ablation of a probe-identified direction, or DAS with an illusion check, would sharpen it.
8. The no-onset result leans on the externalization detector. Calibrated by permutation (false positive 0.00 to 0.08 on variable chains), but the causal definition should be reported on a larger subsample, not just spot-checked.

## process lesson

The root cause of weakness 1 was going straight to novel experiments without a replication step. The right order is reproduce a known result to validate the harness, then extend. Doing that first would also have caught the boxed-answer extraction bug and the mod-97 matcher issue early, rather than late by luck and review.

## compute

White-box work (A1, B, D) runs on a GPU instance; A2 and C run through Bedrock and Anthropic in parallel. Negative results are recorded in negative-results.md as they land, and the paper, synthesis, and findings-summary are updated at the end of the round.
