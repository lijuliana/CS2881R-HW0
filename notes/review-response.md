# response to internal review (2026-08-02)

An adversarial read of the synthesis and code came back with six substantive criticisms. Most are right. This file records what I accept, what I push back on, and the resulting change of plan. The short version: the behavioral results confirm known expressivity theory and cannot lead; the causal read-back mechanism, done cleanly, is the only new thing, so the project reorients around it.

## accepted, changing the work

1. **The necessity result is close to circular.** On variable chains the only algorithm is running the arithmetic, and the trace format writes each step as `x = y op z = value`, so the penultimate value is on the page whenever the answer is. "Every correct deep trace contains every value" is largely forced by task and format, not a memory mechanism. Fixes now planned: (a) lead with the causal externalization measure (corrupt the value, does the answer move), not surface match; (b) run the necessity test on dag_reachability, where the answer is a node label and intermediates are not accumulated into the answer, so the format does not force them onto the page; (c) decompose the surface fraction by intermediate position, since a format-forced result should be carried by the last one or two steps.

2. **Gate B does not yet isolate token read-back.** Corrupting the token also feeds the recomputation, so following the corruption is consistent with either dereferencing the token or being perturbed while recomputing internally. The discriminator, already in the plan, is to patch the clean value back into the residual stream of the corrupted continuation: revert means the effect went through activations, no revert means through the token. Building this now as the headline causal experiment. Also: report the three-way outcome with bootstrap CIs, and take multiple samples per corrupted item, since single-sample labels make the d-curve noisy.

3. **The verification regime is one over-interpreted number.** restates_clean at d=32 rests on a 200-character window (denser steps make the clean value recur sooner in char space, an artifact) and a single sample per item. Demoting it from a claim to a flagged observation until it is a smooth, CI'd function of d across the ladder with multiple samples and a token-based (not char-based) detector.

4. **The eviction probe as written is not valid.** It tokenizes without the chat template (off the distribution the model was measured in), its char-to-token mapping can misalign the probed position, the written and suppressed variants diverge in length so distances are matched in steps but not tokens, and absolute R^2 is uninterpretable with 3584 dims and 320 samples. Killed the running job. The one defense the review understates: the written-minus-suppressed gap does control for operand-readout, since both variants expose the same operands, so the baseline arithmetic-readout is present in both and cancels. Rebuilding the probe around that gap, with the chat template, content-anchored positions common to both variants, a value-break control, and nested-CV R^2 with CIs. Lower priority than the patch-back.

5. **The capacity law is unsupportable on five collinear points.** Already downgraded to an open question in synthesis and results-log after the Llama ladder showed depth and log-params collinear. Keeping it demoted; it does not lead.

## partially pushed back

6. **Novelty ceiling vs Merrill-Sabharwal.** Fair that the behavioral claims (one forward pass is roughly one serial op; serial needs writing, parallel does not) are the shadow of known theory. But the theory says CoT *can* provide serial steps; it does not say a trained reasoning model *does* route computation through the written token at value granularity, nor that it keeps a redundant internal copy, nor that written state is incompressible. Those are mechanistic facts about a specific trained system, not corollaries of an expressivity bound. The review agrees the causal read-back mechanism is new if executed cleanly. So the reorientation is not a retreat, it is putting the new thing in front and the confirmatory behavior behind it as context.

## revised priority order

1. residual patch-back on gate B corrupted continuations: token-path vs internal-path decomposition, multi-sample, CIs. This is the paper.
2. necessity on dag_reachability plus position decomposition, to kill the circularity.
3. protection experiment (running): causal test of the serial/parallel split.
4. eviction probe rebuilt around the written-minus-suppressed gap.
5. everything else is context.

## what actually happened (2026-08-04, closing the loop)

The reorientation held, and the priority order mostly ran as written, with a few honest departures worth recording.

1. The residual patch-back became the centerpiece, but on a non-reasoning model (Qwen2.5-7B-Instruct), not on the reasoning distill. The teacher-forcing diagnostic showed the reasoning model re-solves after its think block, so the corrupted trace is re-derived rather than continued, which the patch cannot cleanly probe. On the instruct model it is clean: corrupt flips the answer 84 percent of items, restoring the residual reverts 97 percent, random control 0 percent. Later replicated behaviorally at frontier scale via API assistant-prefill (V3.2 0.78, Sonnet 4.5 0.97), where read-back reliability rises with capability.

2. The DAG de-circularization was run and came back inconclusive: every node is in the prompt and the model names many while searching, so externalization does not discriminate. Dropped. The circularity is instead answered by the read-back result (the written value is causally used) plus the position decomposition.

3. Protection ran, and a second review caught a real bug first: the lesion fired only on decode, so the direct condition was barely touched. Fixed to lesion during prefill, metered damage on neutral text against a control arm, reran at a dose that bites. Result is moderate support (internal lesion hurts entity ~3x more than chains where both have headroom, robust to layer window), reported with the blunt-lesion caveat.

4. The eviction probe was not rebuilt. Once the patch-back landed cleanly it subsumed the coexistence question, and the probe's validity problems were not worth the GPU time. Dropped rather than rebuilt.

5. The "verification regime" and "internal copy persists" readings were withdrawn entirely after a later review pointed out that follows_clean is re-derivation from the in-context prompt, not evidence of a stored internal copy.

Net: the paper leads with the causal read-back mechanism and its frontier generality, with the behavioral results as theory-predicted context, exactly the reorientation this file proposed.
