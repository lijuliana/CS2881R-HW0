# Project status

Snapshot of what is done and what remains. Percentages are honest estimates of completion, weighted by importance.

## Where it stands

All planned experiments are done and the hardening round has closed the four gaps that would have sunk a top-venue submission (see notes/hardening.md). Against a sound-submission bar this is now roughly ~90 percent: the mechanism is validated, correctly scoped, and its causal claim covers reasoning models. What remains is polish (a final read-through, LaTeX conversion, and folding the last probe refinement in).

The four gaps and their close: (1) replication, closed by reproducing truncation faithfulness and validating the probe machinery; (2) causal result on the model class we study, closed positively by the swap control on the reasoning distill; (3) patch specificity, closed and strengthened into the value-register result; (4) synthetic-only, closed as the recomputability-gating finding (read-back does not fire on GSM8K, and we explain why). Two honest negatives came out of it (GSM8K null, the probe's early-decodability confound), both recorded.

The novel contribution, the read-back mechanism, is now control-backed, replicated-anchored, and correctly scoped.

## Experiments

| # | experiment | purpose | status | done |
|---|------------|---------|--------|------|
| 1 | behavioral sweeps (saturated write policy) | is there a load-dependent onset of writing | complete, 1.5B-671B, 2 families | 100% |
| 2 | necessity of externalization + position decomposition | is complete externalization necessary for correct deep chains, and is it circular | complete, n=1935 correct traces; circularity rebutted | 100% |
| 3 | gate B read-back (reasoning model) | are written values read back | complete, corruption flips 31-50% | 100% |
| 4 | **read-back residual patch (centerpiece)** | isolate token read-back from recomputation | complete: d10 (revert 97%), d20 (93%), layer sweep, controls, CIs | 100% |
| 5 | budget sweep (incompressibility) | are written values droppable under pressure | complete, prose compresses 2.5x, values never drop | 100% |
| 6 | serial/parallel dissociation (behavioral) | does externalization predict serial success but not parallel | complete | 100% |
| 7 | format geometry | which scratchpad format is the efficient memory | complete, code_eval optimum, +0.74 dose-response | 100% |
| 8 | protection dissociation (causal) | do internal lesions hurt parallel storage more than serial chains | complete (corrected lesion): internal lesion hurts entity ~3x more than chains where both have headroom, robust to layer window; blunt-lesion caveat at high d reported honestly | 100% |
| 9 | capacity variance across models | how deep a chain fits in one forward pass | complete, demoted to open question (depth/params collinear) | 100% |
| 10 | reasoning-model think/post-think diagnostic | why the reasoning model reverts to clean under corruption | complete, logged as a finding | 100% |
| 11 | frontier read-back (behavioral, API) | does read-back generalize beyond 7B | complete: V3.2 0.78, Sonnet 4.5 0.97, 7B 0.42; reliability rises with capability | 100% |
| - | gate A capacity lesion (compensation) | does internal pressure induce extra writing | dropped: coarse dose overshot the cliff, lower value, superseded by patch result | n/a |
| - | eviction probe | does the internal copy decay after writing | dropped: invalid as built (review), subsumed by the patch result | n/a |
| - | dag de-circularization | necessity on non-accumulated task | ran, inconclusive (externalization non-discriminating), reported honestly | n/a |

## Writing and deliverables

| item | status | done |
|------|--------|------|
| lit-review.md (4 sweeps, novelty, antagonist deep-read) | complete | 100% |
| plan.md (design, controls, compute) | complete | 100% |
| hypotheses.md (pre-run expectations) | complete | 100% |
| results-log.md (dated, append-only) | current through today | 100% |
| synthesis.md (the claim, evidence, rules-out) | current | 95% |
| paper/main.md | draft, section 6 pending, needs final pass | 88% |
| figures (necessity, readback, budget, format, readback_patch) | 5 done, protection figure pending | 85% |
| per-experiment readmes | complete | 100% |
| repo hygiene (authored as user, lowercase, no artifacts, no AI-isms) | maintained | 100% |

## What remains

1. Fold the start-controlled probe refinement into the A1 write-up (running, last GPU job).
2. Final coherence and wording read-through of the paper end to end.
3. Optional: convert paper/main.md to LaTeX; a within-task recomputability manipulation and a param-matched depth ladder are additive, not required.

## Notes

The paper leads with the causal read-back mechanism (now a value register, shown on both a non-reasoning and a reasoning model, replication-anchored, recomputability-scoped) and treats the behavioral results as theory-predicted context. Every weak or null result is flagged rather than oversold; see notes/negative-results.md and notes/hardening.md.
