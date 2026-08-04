# Full findings

Everything the project found, in one place: the assignment-relevant core, the applied and methodological results around it, and the negatives. The companion doc findings.md is the short version scoped to the assignment question.

Research question: When does a model maintain intermediate reasoning state internally, in its activations, and when does it write that state into its chain of thought? Does this allocation change as problems become harder or as either channel is constrained?

Terms used throughout:

* **Internal workspace**: the model's activations during a forward pass. Always present, cannot be switched off; interventions can damage it (lesion) or overwrite parts of it (patch).
* **Token channel**: the chain-of-thought text written before the answer. Can be closed (force a bare answer), capped (token budget), or edited (corrupt a written value).
* **d**: difficulty, the number of dependent steps in a synthetic problem (chained arithmetic, variable chains, box tracking). Every intermediate value has known ground truth.
* **Externalization**: fraction of those ground-truth values that appear in the written trace.

The claim the findings add up to: for serial reasoning, chain of thought is not a spillover buffer the model uses under pressure. It is the medium the computation runs in. The residual stream is wide but shallow, holding parallel state well and carrying a chained result about one step; anything serial must live on the page and is read back from there.

## Core findings

### 1. Externalization is saturated from the easiest problems onward

**Variable:** d from 1 to 64, model size 1.5B to 671B. **Measured:** externalization in free generation.

**Result:** 0.93 to 1.00 everywhere, including d=1. No model waits for difficulty before writing intermediate values; there is no spill threshold where internal reasoning gives way to writing.

### 2. Models cannot replace the token channel with internal computation

**Variable:** token channel open vs closed (closed = instructed to output only the final answer, zero reasoning tokens). **Measured:** accuracy vs serial depth.

**Result:** accuracy collapses past one dependent operation for nearly every model. DeepSeek V3.2 (671B) gets 23 percent at d=1 and near zero above. With finding 1, this rules out the overflow picture: a single forward pass never fit a chain in the first place. Read behaviorally, not as proof of zero latent serial capacity; the direct condition also carries prompting and training-distribution effects.

### 3. Subsequent computation follows edited written values

**Variable:** one written intermediate value in a valid trace replaced with a counterfactual (417 to 457, say), model continues from the edit. **Measured:** whether the answer matches the clean value, the edited value, or neither.

**Result:** the answer follows the edit on 84 percent of items (Qwen2.5-7B-Instruct, d=10, n=141). Most of the rest follow neither (later arithmetic slips). Almost none recover the original from the unchanged earlier steps, which are still in context. Later computation depends on the written value.

### 4. Restoring clean internal state at the corrupted token restores the clean answer

**Variable:** token text stays corrupted, but the residual-stream state at that position is overwritten with the clean state from the uncorrupted run; control arm gets a matched-norm random perturbation. **Measured:** whether the continuation returns to the clean answer.

**Result:** restoration reverts the answer on 97 percent of affected items (CI 94 to 99); the random control reverts 0 percent; replicates at d=20 (93 percent). The value is read out of the residual state at the written token, causally and specifically. Caveat: the patch restores the full residual state at that position, so it does not isolate the numerical value from everything else represented there.

### 5. Reliance on written values increases with model capability

**Variable:** model, same corruption test via API prefill. **Measured:** fraction of answers following the edit.

**Result:** 42 percent (7B distill), 78 percent (DeepSeek V3.2), 97 percent (Claude Sonnet 4.5). One might expect stronger models to hold more in activations and depend less on the trace; the trend runs the other way, and the trace stays load-bearing at the frontier, which matters for monitoring. Not a causal effect of scale, since these models differ in architecture, training, and serving.

### 6. Read-back also increases with difficulty

**Variable:** d from 4 to 32, corruption test on the reasoning model (7B distill), variable chains. **Measured:** fraction of answers following the edit.

**Result:** 31 percent at d=4, 42 at d=8, 50 at d=16 (n=128 to 149 per cell). Deeper chains lean harder on the written copy. The d=32 cell (36 percent) is depressed by the post-think re-solve behavior of finding 8 and by selection toward easier instances, so the rise is read from d=4 to 16.

### 7. Under token budgets, models cut prose but keep every value

**Variable:** hard output budgets 64 to 512 tokens vs unrestricted. **Measured:** trace length, externalization, accuracy.

**Result:** V3.2 at d=16 compresses traces 466 to 184 tokens with accuracy intact (0.93 to 0.97) and externalization still 0.98 to 1.00. Below roughly twelve tokens per step the model does not drop values and hold them internally; it truncates and accuracy falls to zero. The values themselves are apparently incompressible; only the wording around them is negotiable. The floor is task- and model-specific, not a universal limit.

### 8. Reasoning models run two phases that treat the trace differently

**Variable:** a corrupted worked trace fed to a reasoning model as its own prior output. **Measured:** whether the think block and the final answer section follow the corruption.

**Result:** inside the think block the corrupted value propagates and reaches the corruption-consistent result; the answer section then re-solves the problem from the prompt and often lands on the clean value. The think block reads its own trace; the answer phase re-derives. Found as a confound (it masks read-back if only the final answer is scored) but it stands as an observation about reasoning-model structure, and it is why findings 3 and 4 use a non-reasoning model.

### 9. Serial and parallel memory demands externalize differently

**Variable:** task structure, serial (each value depends on the previous) vs parallel (five boxes, contents repeatedly swapped). **Measured:** externalization among correct traces.

**Result:** serial chains at d of 16 and up, externalization is exactly 1.00 in every correct trace (n=1935 pooled across three model sizes); box tracking, the model handles sixteen swaps correctly while writing about a fifth of the state. What stays internal is set by the structure of the memory demand, not the amount. The families differ in more than seriality, so this is evidence for a structural split, not a separation theorem.

### 10. Activation lesions hurt the parallel task about three times more

**Variable:** matched-dose residual-stream lesion during generation, both task types, chain of thought available. **Measured:** accuracy drop.

**Result:** box tracking falls 0.34, variable chains 0.11 (d=2 to 4, n=40 per cell). The task whose state is less externalized is the one fragile to internal damage, the causal counterpart of finding 9. The lesion is blunt (it also disrupts re-reading of written values), so this is supporting evidence, not a clean separation of the two channels.

### 11. The payload is the evaluated value, not the operation or the prose

**Variable:** scratchpad format at matched difficulty: free prose, code that writes each evaluated value, code that writes operations without values, verbose full-state dumps. **Measured:** accuracy and accuracy per written token.

**Result:** the value-writing code format is the optimum, holding 100 percent through d=48 at 2 to 10 times the accuracy per token of prose. The same format minus evaluated values fails in proportion to how many values it omits (within-format correlation of externalization and correctness +0.74; accuracy 0.58 when under half the values are written, 1.00 when nearly all are). Verbose state dumps collapse at depth (0.07 at d=48); writing too much hurts like writing too little. Rules out generic more-tokens or more-compute explanations for why writing helps, and it is the direct design lever: a compact value-carrying format raises effective external capacity several fold.

### 12. Internal serial capacity is real, small, and model-dependent

**Variable:** model (distill ladder, DeepSeek pair, Llama family to 70B), direct-answer condition. **Measured:** d_int, the deepest chain answered without writing.

**Result:** most models sit at 1 to 2 steps; Llama-70B reaches about 4 to 5. Whether depth or parameter count sets d_int is unresolved: within a family the two are collinear (both correlate about 0.85 to 0.90 with d_int), and the one contrast favoring depth (80-layer Llama-70B over 61-layer DeepSeek 671B) is confounded by family and training. Filed as an open question, not a law.

## Negative and null results

### N1. The starting hypothesis is not supported

The initial hypothesis, written down before any runs, was that models reason internally at low difficulty and start externalizing once capacity is exceeded. Findings 1 and 2 contradict it: writing is saturated at d=1, and closing the token channel reveals no low-difficulty internal regime to fall back on.

### N2. Damaging the workspace does not induce more writing

If externalization were an online response to internal scarcity, damaging the workspace should push the model to write more. It does not: as lesion strength crosses the accuracy cliff (0.99 clean to 0.01 lesioned), externalization falls and traces disintegrate. No sign the write policy adapts.

### N3. Restricting the token channel does not induce internalization

The mirror test of N2. Under hard budgets the model compresses prose while keeping every value; below the floor it truncates and fails rather than holding values internally. Together with N2: no evidence of adaptive movement of state between channels at inference time.

### N4. The planned externalization-onset law had nothing to fit

A phase was budgeted for fitting the onset difficulty d* against model size and depth and comparing candidate scaling laws. Finding 1 shows no onset exists at any scale, so the fittable quantity became d_int (finding 12), where the depth-vs-params question is open for lack of a param-matched depth-varying model set.

### N5. The original CoT-protection asymmetry could not be run as designed

The anchor result behind the project (internal ablation hurts direct answering more than answering with chain of thought) was scheduled as a direct experiment. The lesion proved too blunt (it damages re-reading of written values as well as the workspace) and the direct condition floors at one step, leaving no protection gap to measure. The design was repurposed into the serial/parallel comparison of finding 10, which tests the substitution idea by a different route.

### N6. Neither intervention localizes by layer

The lesion produces the same task dissociation from a mid-stack window and a shallow control window, and the patch reverts the answer about equally from an early, middle, or late layer band (0.96 / 0.97 / 0.94, random control 0.00 throughout). The written value is carried redundantly across the stack at its token position. Robustness of the representation, no circuit-level localization claim.

### N7. Returns to the clean answer do not establish a persistent internal copy

An earlier reading treated a 0.48 to 0.68 clean-return rate after corruption as evidence of an uncorrupted internal copy. Not identified: the full problem stays in context, so re-derivation from the prompt predicts the same behavior. Whether an internal copy survives writing remains undetermined, and no internal-copy claim is made.

### N8. Two task families failed as measurement instruments

Mod-97 arithmetic: a permutation control (scoring each trace against a different instance's values) shows false-positive match rates up to 0.72 at d=48, since long traces mention most residues by chance; benched for externalization measurement (variable chains: 0.00 to 0.08). DAG reachability: every node label appears in the prompt and the model names many while searching, so hop-node mentions sit at 1.00 regardless of correctness; uninformative for the necessity question. Logged because both shaped which numbers can be trusted.

## Known limitations

* Lesion result (finding 10): one model, one dose, n=40 per cell; the lesion also damages re-reading of written values, so the comparison is only clean at low-to-mid difficulty.
* Budget result (finding 7): one model family, and the model is told the cap, so failure conflates cannot-compress with does-not-plan-for-the-cap.
* Frontier read-back (finding 5) is behavioral only; the residual patch needs white-box access and is 7B-scale.
* The patch (finding 4) restores full residual state, not the isolated value, so value-specificity is not yet shown.
* Format results (finding 11) are behavioral; whether the read-back circuitry differs by format was not tested.
* Synthetic tasks buy exact ground truth and controlled depth at the cost of generality; nothing here establishes the same allocation pattern for open-ended math, planning, or safety-relevant reasoning.
