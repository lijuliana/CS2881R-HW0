# hardening plan: close the four crucial gaps

Goal: turn the read-back result from "real but under-validated" into "validated and correctly scoped." Order is chosen so the load-bearing check (replication) runs first: if the harness does not reproduce a known result, we stop and fix the harness before trusting anything else.

## phase A: replication, to anchor the harness (runs first)

The project never reproduced a prior result on our own models and tasks. Two anchors, one white-box and one behavioral:

- **A1, pre-CoT answer decodability (white-box, GPU).** Prior work (Reasoning Theater 2603.05488, pre-CoT decoding 2603.01437) reports that a linear probe can read the final answer out of hidden states before the model writes it. We reproduce it on our variable chains: extract residual states at pre-answer positions, train a linear probe to predict the final answer, report decodability vs position and layer, with a permutation/control-task baseline. Success = answer decodable above chance well before the answer token. This validates our activation extraction and probing, the exact machinery the read-back patch relies on.
- **A2, truncation faithfulness (behavioral, API).** Lanham et al. 2023: truncating CoT at increasing fractions degrades accuracy in a characteristic way if the CoT is load-bearing. We reproduce the curve on our tasks. Success = accuracy rises monotonically with the fraction of CoT kept, and truncation before the key steps collapses it.

If A1 or A2 fail to reproduce the known qualitative shape, that is itself the most important finding and everything downstream is suspect.

## phase B: patch position-specificity control (GPU)

The read-back patch overwrites the value token's residual to clean and gets the clean answer, inviting "you injected the answer." Add patch conditions at (a) the operand tokens of the target step, (b) a neutral token (punctuation) near the value, (c) the value token (the real condition), all at matched norm. The value-token patch should revert the answer; operand and neutral patches should not (or much less). This shows the effect is specific to the written value's representation, not to perturbing that region.

## phase C: read-back on a real benchmark (API)

All tasks are synthetic. Run the behavioral read-back corruption on a GSM8K subset: elicit a worked solution with numeric intermediates, corrupt one written intermediate, continue via assistant prefill, measure whether the answer follows. Success = a corruption-follow rate clearly above zero on real problems, matching the synthetic result qualitatively.

## phase D: reasoning-model causal read-back, or honest rescope (GPU)

The clean patch is on a non-reasoning instruct model. Attempt the patch on a reasoning distill by patching inside the think segment and reading the answer the think trace commits to (before the post-think re-solve masks it). If it works, the causal claim covers reasoning models. If it does not work cleanly, rescope the paper from "reasoning models" to "language models" and say why, keeping the frontier behavioral read-back (which is on reasoning-capable models) as the reasoning-model evidence.

## compute plan

Restart the g6e instance for A1, B, D (white-box). Run A2 and C through Bedrock/Anthropic locally in parallel. Record negative results honestly in notes/negative-results.md as they land. Update findings-summary, synthesis, paper, known-weaknesses, and status at the end.
