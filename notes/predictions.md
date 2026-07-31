# predictions

Written before running anything. Each entry: what we expect, why, and what the opposite result looks like in the same measurement. If a result cannot show us the opposite, the experiment is redesigned before it runs. Updates to this file only ever append; nothing gets edited after its experiment starts.

## phase 1, externalization curves

Expected: for each model, externalization fraction stays near zero up to some d*, then rises steeply; d* grows with model size; CoT length grows superlinearly past d*. Why: theory says single-pass serial capacity scales with depth, so bigger models can hold longer chains internally; Lanham-style inverse scaling of CoT reliance points the same way.

Opposite results that would be visible: (a) externalization fraction is high at all d, including trivially easy problems, meaning reasoning-trained models write everything down by habit and there is no load-dependent onset, only a trained policy. This is a live possibility given the overthinking literature, and it would push the project toward "the policy is miscalibrated relative to the capacity boundary," measured as the gap between d* and the direct-answer failure point. (b) No dependence on model size, which would undercut the capacity account entirely. (c) Externalization tracks output-format habits per family rather than difficulty, which the cross-family comparisons will expose.

Also expected: the direct-answer accuracy cliff sits above d* for reasoning models (they write before they must). If instead d* coincides exactly with the cliff, the cost-benefit story is cleaner than we assumed; if d* sits far below the cliff, habit dominates capacity.

## phase 2b, eviction

Expected: probe decodability of an intermediate value at current-position residual streams drops faster after the value is written to tokens than in matched unwritten cases at equal distance from computation. Why: keeping a copy is expensive under superposition interference; a written value is retrievable by attention, so the workspace should reclaim the space. Effect size guess: modest, 10 to 30 relative percent drop, not to zero, since breadcrumbs persist.

Opposite visible: decodability equal or higher after writing (broadcast copy, redundant cache, no eviction). That result would be worth publishing on its own since it says the "hierarchy" has no writeback discipline, and it would predict that CoT corruption fails to change answers on those traces, a cross-check we run either way.

## phase 2c, read-back

Expected: corrupting a written value flips downstream computation increasingly often as d rises; attention knockout to the value's tokens reproduces most of the corruption effect; a small set of heads carries most of it. Why: at high d the internal copy is gone (2b) so the token is the live copy; receiver-head concentration matches thought-anchors findings at sentence level.

Opposite visible: answers track the internal value under token corruption (patching the clean internal state back has no effect, corrupted token ignored), meaning CoT is a write-only log, decorative at value level even when accurate. Also possible and visible: read-back fraction high at low d and lower at high d, which would invert the hierarchy story.

## phase 3a, squeeze internal

Expected: workspace-subspace ablation at moderate dose increases CoT length and externalization fraction and partially restores accuracy relative to random-subspace controls at matched KL; control tasks flat. Why: if writing is a response to workspace scarcity, induced scarcity should induce writing. This is the riskiest prediction in the project and the one we care most about. Honest prior: maybe 40 percent it works as stated, because the write policy may be fixed by training rather than load-sensitive at inference time.

Opposite visible: ablation degrades accuracy with no change in externalization (policy is static; the trade-off is set during training, not adapted online), or externalization rises equally under random-subspace damage of matched KL (the response is generic distress, not memory management). Both are distinguishable in the design because we log externalization against the damage meter for targeted and random interventions separately.

## phase 3b, squeeze external

Expected: under token budgets, probe decodability of intermediate values at late positions rises (the model holds more internally) and accuracy holds until a d-dependent ceiling, then breaks; paraphrase hurts little (semantic memory) while filler substitution hurts a lot at high d (content matters, not just slots). Why: Pfau et al. show fillers only buy parallel compute; our high-d tasks are serial.

Opposite visible: filler tokens rescue performance as well as real CoT at high d, meaning the channel is compute slots and the memory framing is wrong for that family; or internal decodability does not rise under budgets, meaning there is no compensatory internal storage and the two tiers do not trade.

## phase 4, onset law

Expected: d* approximately linear in effective depth within a family (serial budget), with reasoning-trained models showing lower d* than matched base models at equal size (RL teaches earlier writing). Cross-family transfer of the fitted law: genuinely uncertain, no confident prediction, and we say so; a family-specific intercept with shared slope is our weak guess.

Opposite visible: log-depth fits better (parallel-scan regime), or d* tracks parameters rather than depth (capacity is width/superposition, not serial), or no stable d* exists across seeds (onset is stochastic, fit distributions instead, per the random-emergence literature). The model comparison is set up before fitting so any of these outcomes is a result rather than a failure.

## phase 5, formats

Expected: structured formats raise accuracy per written token and raise d* at matched budgets; read-back heads transfer across formats (addressing is general). Opposite visible: prose wins (models read their own prose better than tables, training distribution dominates), or format effects vanish at scale.
