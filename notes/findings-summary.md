# Findings summary

Question: when does a model hold intermediate reasoning state internally (in its activations) vs write it into chain of thought, and does the split change as problems get harder?

Terms used throughout:

- **Internal workspace**: the model's activations during a forward pass. Always present; cannot be switched off. Interventions can damage it (lesion) or overwrite parts of it (patch).
- **Token channel**: the chain-of-thought text the model writes before its answer. This can be switched off (force a bare answer), capped (token budget), or edited (corrupt a written value).
- **d**: difficulty, the number of dependent steps in a synthetic puzzle (chained arithmetic, variable chains, box tracking). Every intermediate value has known ground truth.
- **Externalization**: fraction of those ground-truth intermediate values that appear in the written trace.

Each finding below states what was varied, what was measured, and the result.

## Findings

**1. Writing is saturated from the easiest problems; there is no spill threshold.**
Varied: d from 1 to 64, model size 1.5B to 671B. Measured: externalization in free generation.
Result: 0.93 to 1.00 everywhere, including d=1. Models never wait for difficulty to start writing.

**2. With the token channel closed, models fail after one dependent step.**
Varied: token channel on vs off (same problems; "off" = instructed to output only the final answer, think block closed so zero reasoning tokens are generated). Measured: accuracy.
Result: every model collapses past one serial operation. DeepSeek V3.2 (671B) gets 23 percent at d=1 and near zero above. Together with finding 1: writing is not overflow from a full workspace; a single forward pass never fits a chain in the first place, so everything is written from the start.

**3. The model reads its written values back; the answer follows them.**
Varied: one written intermediate value edited mid-trace (e.g. 417 to 457), model continues from the edit. Measured: which answer the continuation reaches.
Result: the final answer follows the edited value on 84 percent of items (Qwen2.5-7B-Instruct, d=10, n=141). The remainder follow neither answer (arithmetic slips). Essentially none recompute the value from the earlier steps, which are still in context.

**4. The read-back runs through the internal state at the written token (causal isolation).**
Varied: with the text still corrupted, the internal representation at that token position is restored to the clean state; control arm gets a random perturbation of the same size instead.
Result: restoring the clean state reverts the answer to correct on 97 percent of affected items (CI 94 to 99); the random control reverts 0 percent. Replicates at d=20 (93 percent). So the effect is specific: the model reads the value from that token's internal state, and generic disturbance does nothing.

**5. Bigger models rely on written values more, not less.**
Varied: model scale, same corruption test as finding 3 run behaviorally through API prefill. Measured: fraction of answers following the edit.
Result: 42 percent (7B) to 78 percent (V3.2 671B) to 97 percent (Claude Sonnet 4.5).

**6. Written values are the one thing the model will not cut.**
Varied: hard token budgets (64 to 512) vs unlimited. Measured: trace length, externalization, accuracy.
Result: V3.2 compresses prose up to 2.5x (466 to 184 tokens at d=16) with accuracy intact (0.93 to 0.97) and externalization still 0.98 to 1.00. Below about 12 tokens per step it does not summarize or shift the work internally; it truncates and accuracy drops to zero.

**7. What stays internal depends on the kind of memory a task needs, not the amount.**
Varied: task structure, serial (chains, each value depends on the previous) vs parallel (5 boxes, contents swapped repeatedly). Measured: externalization among correct traces.
Result: chains, exactly 1.00 at d>=16 for every correct trace (n=1935); box tracking, the model tracks 16 swaps correctly while writing only about a fifth of the state. Serial state lives on the page; parallel state can live in activations.

**8. Damaging the workspace confirms the split causally.**
Varied: a lesion added to the workspace activations at matched dose, on both task types. Measured: accuracy drop with chain of thought allowed.
Result: box tracking drops 0.34, chains drop 0.11 (d=2 to 4, n=40 per cell). The task whose state lives internally is about 3x more fragile to internal damage.

## Negative and null results

**N1. The starting hypothesis is refuted.** The initial hypothesis, written down before any runs, was that models reason internally until workspace capacity runs out, then start externalizing. Findings 1 and 2 are the refutation: writing is saturated from d=1, and the workspace never held a chain to begin with. N2 and N3 rule out the adaptive version of the hypothesis as well.

**N2. Damaging the workspace does not make the model write more.** If externalization were a response to internal scarcity, induced scarcity should induce writing. It does not: at doses past the accuracy cliff (0.99 clean to 0.01 lesioned), externalization falls and traces disintegrate. The write policy shows no sign of adapting online.

**N3. Squeezing the token channel does not push computation inward.** The mirror-image test of N2. Under hard token budgets the model never holds values internally to save space; below the ~12 tokens-per-step floor it truncates and fails (finding 6). Together with N2: the allocation is static in both directions.

**N4. No onset law to fit.** A planned phase was fitting the externalization-onset difficulty d* against model size and depth, and comparing candidate scaling laws. Finding 1 shows no onset exists at any scale, so there was nothing to fit.

**N5. The original CoT-protection asymmetry was not cleanly reproduced.** The assignment's anchor result (internal ablation hurts direct answering more than CoT answering) was scheduled as a direct experiment. The lesion proved too blunt to run it as designed: it damages the re-reading of written values as well as the workspace, and the direct condition floors at one step (finding 2), leaving no room for a protection gap. The experiment was repurposed into the serial/parallel comparison of finding 8, which supports the substitution idea by a different route.

**N6. Naive corruption tests break on reasoning models.** The corrupted value propagates inside the think block, but the answer section then re-solves the problem from the prompt, masking the read-back. This is why findings 3 and 4 use a non-reasoning model.

**N7. One earlier reading withdrawn.** A 0.48 to 0.68 rate of answers returning to the clean value was first read as a persistent internal copy; it is equally consistent with re-deriving from the prompt, which stays in context. No internal-copy claim is made.

## Known limitations

- Lesion result (finding 8): n=40 per cell, one model, one dose; the lesion also damages re-reading of written values, so the comparison is only clean at low-to-mid d.
- Budget result (finding 6): one model, one family, and the model is told the cap, so failure conflates cannot-compress with does-not-plan-for-the-cap.
- Frontier read-back (finding 5) is behavioral only; the internal-state patch needs white-box access and is 7B-scale.
