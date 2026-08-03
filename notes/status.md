# project status

Snapshot of what is done and what remains. Percentages are honest estimates of completion, weighted by importance.

## overall: ~96 percent

The novel causal contribution (read-back mechanism) is complete and defensible, and the protection dissociation is now in with a corrected lesion and an honest moderate-support result. All experiments are done; the paper has all sections filled and needs only a final coherence and wording pass.

## experiments

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
| - | gate A capacity lesion (compensation) | does internal pressure induce extra writing | dropped: coarse dose overshot the cliff, lower value, superseded by patch result | n/a |
| - | eviction probe | does the internal copy decay after writing | dropped: invalid as built (review), subsumed by the patch result | n/a |
| - | dag de-circularization | necessity on non-accumulated task | ran, inconclusive (externalization non-discriminating), reported honestly | n/a |

## writing and deliverables

| item | status | done |
|------|--------|------|
| lit-review.md (4 sweeps, novelty, antagonist deep-read) | complete | 100% |
| plan.md (design, controls, compute) | complete | 100% |
| hypotheses.md (pre-run expectations) | complete | 100% |
| results-log.md (dated, append-only) | current through today | 100% |
| synthesis.md (the claim, evidence, rules-out) | current | 95% |
| review-response.md (adversarial self-review acted on) | complete | 100% |
| paper/main.md | draft, section 6 pending, needs final pass | 88% |
| figures (necessity, readback, budget, format, readback_patch) | 5 done, protection figure pending | 85% |
| per-experiment readmes | complete | 100% |
| repo hygiene (authored as user, lowercase, no artifacts, no AI-isms) | maintained | 100% |

## what remains

1. entity-tracking protection completes (running now) then analyze the dissociation. If the gentle lesion (KL 0.03) does not bite entity tracking either, launch the staged higher-alpha (0.10) pass. This decides whether section 6 makes a positive dissociation claim or reports the lesion as too weak to conclude.
2. fill paper section 6 with the protection result, add the protection figure.
3. remove the paper draft header, final coherence and wording pass end to end.
4. optional stretch: frontier-scale read-back (corruption on an API model via assistant prefill), and a param-matched depth ladder for the capacity question. Both are additive, not required.

## risk notes

- Protection is the one place a clean positive result is not yet in hand. The variable-chain arm behaved as the thesis predicts (internal lesion does not hurt externally-stored chains), but a dissociation needs entity tracking to be hurt by the same lesion. If neither is hurt at any safe dose, section 6 becomes "consistent with but not a clean causal confirmation of" the dissociation, and the paper still stands on experiments 1-7 and 9-10.
