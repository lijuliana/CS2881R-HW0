# known weaknesses and what to do about them

Honest self-critique, ranked by how much a reviewer (or a careful re-read) could use it against the paper. The first four are the ones that matter.

## crucial

1. **No replication of any prior result.** We never reproduced an established finding on our own setup before extending it, so our harness has no validated anchor and our "we refute view X" claims rest on our framing of X, not on reproducing X and breaking it. Fix: reproduce one concrete result on our models and tasks, for example pre-CoT answer decodability (Reasoning Theater / 2603.01437) or a Lanham-style truncation faithfulness curve. If we recover their number, the setup is trustworthy. Needs white-box (GPU) for the decoding version; the faithfulness version is API-doable.

2. **The clean causal result is on a non-reasoning model.** The residual-patch centerpiece runs on Qwen2.5-7B-Instruct, chosen because the reasoning model re-solves after its think block. So the causal isolation is off the model class the paper is about; only the behavioral read-back is on reasoning models. Fix: either run a clean causal patch on a reasoning distill (patch inside the think segment and read the value the think trace commits to, before the post-think re-solve) or rescope the paper to language models rather than reasoning models. Needs GPU.

3. **The patch needs a position-specificity control.** Overwriting the value token's residual to clean and getting the clean answer invites the objection that we injected the answer. We ran a random-direction control and a layer sweep, but never patched a non-value position or the operand tokens. Adding a patch at operand positions (should not revert to clean via the value) and at a neutral token (should do nothing) would show the effect is specific to the written value's representation. Cheap, needs GPU.

4. **Only synthetic toy tasks.** Variable chains, mod arithmetic, entity tracking, DAG. No real reasoning benchmark, so generalization to actual reasoning is asserted. Fix: run the behavioral read-back corruption on a GSM8K subset (write the numeric intermediates, corrupt one, continue). API-doable.

## important, not fatal

5. **Corruption may measure local arithmetic-checking, not memory read-back.** We did not separate corrupting a value on its own computation line (which partly probes local consistency) from corrupting a later re-reference of it (cleaner read-back). Log the two cases per item and split the flip rate.

6. **Thin statistics on the causal results.** Protection is n=40 per cell, one model, one dose. Read-back patch is one model, one run, no seed variation. Add seeds and at least one more model per causal result before claiming robustness.

7. **Lesion validity is fuzzy.** The resample ablation blends toward a bank of reasoning-state vectors that is off-distribution for neutral text (neutral KL 1.3 vs task KL 0.15), so what the lesion actually removes is not well characterized. A cleaner ablation (mean-ablation of a probe-identified workspace direction, or a subspace found by DAS with an illusion check) would sharpen it.

8. **The no-onset result leans on the externalization detector.** Calibrated by a permutation control (false positive 0.00 to 0.08 on variable chains), but short numeric strings recur, so the saturation ceiling could be slightly inflated. The causal definition (corrupt the value, does the answer move) is the fallback and should be reported on a larger subsample, not just as a spot check.

## process lesson

The root cause of weakness 1 is that we went straight to novel experiments without a replication step. The right order is reproduce a known result to validate the harness, then extend. Doing that first would also have caught detector and extraction issues earlier (we found the boxed-answer extraction bug and the mod-97 matcher issue late, by luck and by review, not by a baseline that would have flagged them).

## priority if we continue

1. reproduce one prior result (weakness 1) to anchor the setup.
2. patch position-specificity controls (weakness 3), cheap and high-value.
3. read-back on a reasoning model or an honest rescope (weakness 2).
4. read-back on a real benchmark (weakness 4).
Everything else is polish.
