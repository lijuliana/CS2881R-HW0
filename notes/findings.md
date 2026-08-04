# Findings summary

## Research question

When does a model maintain intermediate reasoning state internally, in its activations, and when does it write that state into its chain of thought? Does this allocation change as problems become harder or as either channel is constrained?

## Terms

* **Internal workspace:** The model’s activations during a forward pass. This workspace is always present and cannot be disabled directly. It can, however, be damaged through a lesion or partially overwritten through activation patching.
* **Token channel:** The chain-of-thought text generated before the final answer. This channel can be closed by requiring a bare answer, constrained with a token budget, or edited by corrupting a written intermediate value.
* **Difficulty (d):** The number of dependent steps in a synthetic reasoning problem, including chained arithmetic, variable chains, and box tracking. The ground-truth intermediate state is known at every step.
* **Externalization:** The fraction of ground-truth intermediate values that appear explicitly in the generated trace.

# Main findings

## 1. Externalization is saturated from the easiest problems onward

**Varied:** Difficulty from (d=1) to (d=64), and model size from 1.5B to 671B parameters.

**Measured:** The fraction of ground-truth intermediate values written during free generation.

**Result:** Externalization remains between 0.93 and 1.00 across the full difficulty range, including at (d=1). No model waits for the problem to become difficult before beginning to write intermediate values.

**Interpretation:** We find no evidence for a spill threshold at which a model initially reasons internally and begins externalizing only after its internal workspace is exhausted. The default write policy is already near saturation at the lowest tested difficulty.

## 2. Models do not successfully replace the token channel with internal computation

**Varied:** Token channel available versus closed. In the closed condition, the model is instructed to produce only the final answer, with no reasoning tokens generated.

**Measured:** Final-answer accuracy as serial depth increases.

**Result:** Accuracy collapses rapidly once problems require more than one dependent operation. DeepSeek V3.2 achieves 23% accuracy at (d=1) and approaches zero at greater depths.

**Interpretation:** Under the tested direct-answer condition, the models do not preserve performance by moving the serial computation into a single forward pass. Together with Finding 1, this argues against a simple overflow account in which the model writes only after an initially sufficient internal workspace fills up.

This result should be interpreted behaviorally rather than as a strict proof that the model has no latent serial capacity. The direct-answer condition may also reflect prompting, training-distribution, or answer-production effects.

## 3. Subsequent computation follows edited written values

**Varied:** One intermediate value in an otherwise valid worked trace is replaced with a counterfactual value—for example, changing 417 to 457—after which the model continues from the edited trace.

**Measured:** Whether the final answer is consistent with the clean trace, the edited value, or neither.

**Result:** On Qwen2.5-7B-Instruct at (d=10), the final answer follows the edited value on 84% of 141 items. Most remaining examples follow neither answer because of subsequent arithmetic errors. Almost none recover the original value from the unchanged earlier steps.

**Interpretation:** The written intermediate value is not merely a record of an independently completed computation. Later computation causally depends on the state introduced at that point in the trace.

## 4. Clean internal state at the corrupted token position restores the clean continuation

**Varied:** The written value remains visibly corrupted, but the residual-stream state at that token position is replaced with the clean state recorded from the uncorrupted run. A control condition applies a random perturbation with matched norm.

**Measured:** Whether the continuation returns to the clean answer.

**Result:** Among examples whose answers were changed by the corruption, restoring the clean residual state returns the answer to the clean value on 97% of items, with a 95% confidence interval of 94–99%. The matched random perturbation restores 0%. At (d=20), clean-state restoration succeeds on 93% of affected items.

**Interpretation:** Causally relevant information is represented at the written value’s token position and is reused by later computation. The effect is specific to restoring the clean state rather than to perturbing the model generically.

Because the intervention restores the full residual state at that position, it does not yet isolate the numerical value from all other contextual information represented there.

## 5. Behavioral read-back persists in larger and more capable models

**Varied:** Model, using the same behavioral corruption test through API prefill.

**Measured:** The fraction of final answers that follow the edited intermediate value.

**Result:**

* 7B reasoning distill: 42%
* DeepSeek V3.2: 78%
* Claude Sonnet 4.5: 97%

**Interpretation:** Dependence on written intermediate state is not confined to the white-box 7B model. Strong corruption-following behavior also appears in the tested frontier systems.

These comparisons do not establish a causal effect of scale, because the models differ in architecture, training, family, and serving setup.

## 6. Under token pressure, models remove prose before intermediate values

**Varied:** Hard output budgets from 64 to 512 tokens, compared with unrestricted generation.

**Measured:** Trace length, externalization, and accuracy.

**Result:** On DeepSeek V3.2 at (d=16), the model compresses traces from approximately 466 tokens to 184 tokens while preserving accuracy between 0.93 and 0.97. Externalization remains between 0.98 and 1.00. Below approximately twelve tokens per reasoning step, traces truncate and accuracy falls to zero.

**Interpretation:** Intermediate values are more resistant to compression than the surrounding prose. When the token budget becomes too small, the model does not preserve performance by omitting written values and maintaining them internally. Instead, the trace breaks down.

The observed floor is specific to the tested task and model and should not be treated as a universal information-theoretic limit.

## 7. Externalization differs between serial and parallel memory demands

**Varied:** Task structure.

* **Serial:** Each intermediate value depends on the preceding value.
* **Parallel:** The model tracks the contents of five boxes while their contents are repeatedly swapped.

**Measured:** Externalization among correct traces.

**Result:** On serial variable chains at (d \geq 16), externalization is exactly 1.00 for every correct trace across the three tested distill models, with (n=1{,}935) pooled examples. On box tracking, the model can correctly process sixteen swaps while explicitly writing only about one fifth of the task state.

**Interpretation:** Serial dependency chains rely heavily on explicitly written intermediate state, whereas substantial parallel state can remain implicit in activations. The relevant distinction appears to be the structure of the memory demand rather than simply the total amount of information involved.

Because the task families differ in more than seriality alone, this should be treated as evidence for a structural distinction rather than as a complete separation theorem.

## 8. Activation lesions affect the parallel task more strongly

**Varied:** A matched-dose lesion applied to the residual stream during generation on both serial chains and box tracking.

**Measured:** Accuracy reduction with chain of thought available.

**Result:** At (d=2) to (d=4), box-tracking accuracy falls by 0.34, while variable-chain accuracy falls by 0.11, with (n=40) per cell.

**Interpretation:** The task whose state is less fully externalized is approximately three times more sensitive to activation damage. This is consistent with box tracking depending more heavily on internally maintained state, while serial chains retain some robustness because their intermediate values are also available in the written trace.

The lesion is blunt and also disrupts the processing and re-reading of written values. This result is therefore supporting evidence for the serial–parallel distinction rather than a clean causal separation of the two memory channels.

# Negative and null results

## N1. The original spill-threshold hypothesis is not supported

The preregistered or initial hypothesis was that models would reason internally at low difficulty and begin externalizing once internal capacity was exceeded.

Findings 1 and 2 contradict that account. Externalization is already saturated at (d=1), while closing the token channel produces poor serial performance rather than revealing a substantial low-difficulty internal regime.

## N2. Damaging the internal workspace does not induce additional writing

If externalization were an online response to internal scarcity, damaging the activation workspace should cause the model to write more state into the trace.

This does not occur. As lesion strength increases from a regime with approximately 0.99 clean accuracy to one with approximately 0.01 lesioned accuracy, externalization falls and traces become disorganized. The model shows no evidence of compensating for activation damage by increasing its use of the token channel.

## N3. Restricting the token channel does not induce successful internalization

The mirror prediction is that limiting available reasoning tokens should cause the model to retain more intermediate state internally.

This also does not occur. Under hard token limits, the model first compresses prose while preserving intermediate values. Below the observed budget floor, it truncates and fails rather than omitting values while preserving the computation internally.

Together, N2 and N3 provide no evidence for adaptive movement of reasoning state between the two channels during inference.

## N4. Naive final-answer corruption tests are confounded in reasoning models

When a written value is corrupted inside a reasoning model’s think block, the corrupted value propagates through the remaining reasoning. However, the final answer section may then solve the original problem again from the prompt.

As a result, the final answer can return to the clean value even though the corrupted value was used during the reasoning trace. This masks read-back when only the final answer is measured.

This confound motivates the use of Qwen2.5-7B-Instruct for Findings 3 and 4: it continues a worked trace directly to the answer without a separate post-reasoning re-derivation phase.

## N5. Returns to the clean answer do not establish a persistent internal copy

An earlier interpretation treated a 0.48–0.68 rate of returning to the clean answer after corruption as evidence that the model retained an uncorrupted internal copy.

That interpretation is not identified. Because the complete original problem remains in context, the model can instead re-derive the answer from the prompt. The current results therefore make no claim that a persistent clean internal copy survives after the written value is corrupted.

# Known limitations

## Residual lesion

Finding 8 currently uses one model, one lesion dose, and (n=40) examples per cell. The lesion also interferes with re-reading written values, so the comparison is most interpretable at low-to-moderate difficulty, before either task reaches an accuracy floor.

## Token-budget experiment

Finding 6 currently covers one model family. The model is informed of the output cap, so failure under tight budgets may combine two effects: an inability to compress the required state and a failure to plan an adequate compressed trace.

## Frontier-model corruption

Finding 5 is behavioral only. Residual-state patching requires white-box model access and has so far been performed at 7B scale.

## Value specificity of the patch

The clean intervention restores the complete residual state at the corrupted token position. It establishes that causally relevant state is stored and reused there, but does not yet show that the isolated numerical value is sufficient independently of the surrounding contextual representation.

## Synthetic-task generality

The synthetic tasks provide exact intermediate-state ground truth and controlled serial depth, which makes the causal interventions possible. The results do not by themselves establish that the same allocation pattern holds for open-ended mathematical, linguistic, planning, or safety-relevant reasoning.
