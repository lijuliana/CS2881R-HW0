# Findings summary

Research question: When does a model maintain intermediate reasoning state internally, in its activations, and when does it write that state into its chain of thought? Does this allocation change as problems become harder or as either channel is constrained?

Terms used throughout:

* **Internal workspace**: the model's activations during a forward pass. Always present, cannot be switched off; interventions can damage it (lesion) or overwrite parts of it (patch).
* **Token channel**: the chain-of-thought text written before the answer. Can be closed (force a bare answer), capped (token budget), or edited (corrupt a written value).
* **d**: difficulty, the number of dependent steps in a synthetic problem (chained arithmetic, variable chains, box tracking). Every intermediate value has known ground truth.
* **Externalization**: fraction of those ground-truth values that appear in the written trace.

Each finding states the manipulated variable, the measurement, and the result.

## Main findings

### 1. Externalization is saturated from the easiest problems onward

**Variable:** d from 1 to 64, model size 1.5B to 671B. **Measured:** externalization in free generation.

**Result:** 0.93 to 1.00 everywhere, including d=1. No model waits for difficulty before writing intermediate values; there is no spill threshold where internal reasoning gives way to writing. The write policy is saturated from the start.

### 2. Models cannot replace the token channel with internal computation

**Variable:** token channel open vs closed (closed = instructed to output only the final answer, zero reasoning tokens). **Measured:** accuracy vs serial depth.

**Result:** accuracy collapses past one dependent operation. DeepSeek V3.2 (671B) gets 23 percent at d=1 and near zero above. With finding 1, this rules out the overflow picture: writing is not what happens when a sufficient workspace fills up, because a single forward pass never fit a chain in the first place. Read behaviorally, not as proof of zero latent serial capacity; the direct condition also carries prompting and training-distribution effects.

### 3. Subsequent computation follows edited written values

**Variable:** one written intermediate value in a valid trace replaced with a counterfactual (417 to 457, say), model continues from the edit. **Measured:** whether the answer matches the clean value, the edited value, or neither.

**Result:** the answer follows the edit on 84 percent of items (Qwen2.5-7B-Instruct, d=10, n=141). Most of the rest follow neither (later arithmetic slips). Almost none recover the original from the unchanged earlier steps, which are still in context. The written value is not a record of computation done elsewhere; later computation depends on it.

### 4. Restoring clean internal state at the corrupted token restores the clean answer

**Variable:** token text stays corrupted, but the residual-stream state at that position is overwritten with the clean state from the uncorrupted run; control arm gets a matched-norm random perturbation. **Measured:** whether the continuation returns to the clean answer.

**Result:** restoration reverts the answer on 97 percent of affected items (CI 94 to 99); the random control reverts 0 percent; replicates at d=20 (93 percent). The value is read out of the residual state at the written token, causally and specifically. Caveat: the patch restores the full residual state at that position, so it does not isolate the numerical value from everything else represented there.

### 5. Reliance on written values increases with model capability

**Variable:** model, same corruption test via API prefill. **Measured:** fraction of answers following the edit.

**Result:** 42 percent (7B distill), 78 percent (DeepSeek V3.2), 97 percent (Claude Sonnet 4.5). One might expect stronger models to hold more in activations and depend less on the trace; the trend runs the other way, and the trace stays load-bearing at the frontier, which matters for monitoring. Not a causal effect of scale, since these models differ in architecture, training, and serving.

### 6. Under token budgets, models cut prose but keep every value

**Variable:** hard output budgets 64 to 512 tokens vs unrestricted. **Measured:** trace length, externalization, accuracy.

**Result:** V3.2 at d=16 compresses traces 466 to 184 tokens with accuracy intact (0.93 to 0.97) and externalization still 0.98 to 1.00. Below roughly twelve tokens per step the model does not drop values and hold them internally; it truncates and accuracy falls to zero. The values themselves are apparently incompressible; only the wording around them is negotiable. The floor is task- and model-specific, not a universal limit.

### 7. Serial and parallel memory demands externalize differently

**Variable:** task structure, serial (each value depends on the previous) vs parallel (five boxes, contents repeatedly swapped). **Measured:** externalization among correct traces.

**Result:** serial chains at d of 16 and up, externalization is exactly 1.00 in every correct trace (n=1935 pooled across three model sizes); box tracking, the model handles sixteen swaps correctly while writing about a fifth of the state. What stays internal is set by the structure of the memory demand, not the amount: serial state lives on the page, parallel state can live in activations. The families differ in more than seriality, so this is evidence for a structural split, not a separation theorem.

### 8. Activation lesions hurt the parallel task about three times more

**Variable:** matched-dose residual-stream lesion during generation, both task types, chain of thought available. **Measured:** accuracy drop.

**Result:** box tracking falls 0.34, variable chains 0.11 (d=2 to 4, n=40 per cell). The task whose state is less externalized is the one fragile to internal damage, the causal counterpart of finding 7. The lesion is blunt (it also disrupts re-reading of written values), so this is supporting evidence, not a clean separation of the two channels.

## Negative and null results

### N1. The starting hypothesis is not supported

The initial hypothesis was that models reason internally at low difficulty and start externalizing once capacity is exceeded. Findings 1 and 2 contradict it: writing is saturated at d=1, and closing the token channel reveals no low-difficulty internal regime to fall back on.

### N2. Damaging the workspace does not induce more writing

If externalization were an online response to internal scarcity, damaging the workspace should push the model to write more. It does not: as lesion strength crosses the accuracy cliff (0.99 clean to 0.01 lesioned), externalization falls and traces disintegrate. No sign the write policy adapts.

### N3. Restricting the token channel does not induce internalization

The mirror test of N2. Under hard budgets the model compresses prose while keeping every value; below the floor it truncates and fails rather than holding values internally. Together with N2: no evidence of adaptive movement of state between channels at inference time.

### N4. Naive corruption tests are confounded in reasoning models

Corrupt a value inside a think block and it propagates through the reasoning, but the answer section may then re-solve the problem from the prompt, so the final answer returns to clean even though the corrupted value was used. This masks read-back when only the answer is measured, and is why findings 3 and 4 use a non-reasoning model that continues a worked trace straight to the answer.

### N5. Returns to the clean answer do not establish a persistent internal copy

An earlier reading treated a 0.48 to 0.68 clean-return rate after corruption as evidence of an uncorrupted internal copy. Not identified: the full problem stays in context, so re-derivation from the prompt predicts the same behavior. Whether an internal copy survives writing remains undetermined, and no internal-copy claim is made.

## Known limitations

* Lesion result (finding 8): one model, one dose, n=40 per cell; the lesion also damages re-reading of written values, so the comparison is only clean at low-to-mid difficulty.
* Budget result (finding 6): one model family, and the model is told the cap, so failure conflates cannot-compress with does-not-plan-for-the-cap.
* Frontier read-back (finding 5) is behavioral only; the residual patch needs white-box access and is 7B-scale.
* The patch (finding 4) restores full residual state, not the isolated value, so value-specificity is not yet shown.
* Synthetic tasks buy exact ground truth and controlled depth at the cost of generality; nothing here establishes the same allocation pattern for open-ended math, planning, or safety-relevant reasoning.
