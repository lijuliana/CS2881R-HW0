# negative results, nulls, and things that did not work

Collected in one place so nothing is buried. Each entry: what we expected or tried, what happened, and where it is recorded. These are not failures of the project, they are the parts of the map that came back empty, and several of them are the most informative results we have.

## the big one: no externalization onset (an expected result did not appear)

We expected a difficulty threshold at which models switch from internal reasoning to writing. There is none. Externalization is at ceiling from the easiest problems, at every scale and family. This overturned the starting hypothesis (a memory hierarchy with a spill point) and became the paper's opening finding. Recorded: results-log 2026-08-01, synthesis section, paper section 4.

## experiments that came back inconclusive or null

- **Gate A (does internal pressure induce more writing).** Dropped. The write policy is already saturated, so there was no compensation headroom to detect, and a coarse dose sweep overshot the accuracy cliff. Superseded by the read-back patch. Recorded: experiments/gate_a_capacity/readme.md, review-response.md.
- **DAG de-circularization test.** Ran, inconclusive. Because every node label is already in the prompt and the model names many while searching, externalization does not discriminate correct from wrong traces there (both ~1.0). Cannot de-circularize the necessity result. Recorded: results-log 2026-08-02 (dag), paper section 4.
- **Protection at a gentle dose (alpha 0.05).** Null. The lesion at that dose (KL ~0.03) moved nothing in either family. Required a stronger dose and a lesion-symmetry fix to get a signal. Recorded: results-log 2026-08-02, 2026-08-03.
- **Protection dissociation, honestly partial.** At a dose that bites, the internal lesion hurts entity tracking about three times more than chains where both have headroom, but the effect is not clean everywhere: at the longest chains the blunt lesion also hurts chains (it damages the re-reading of written values), and the entity floor limits the high-difficulty comparison. Moderate support, not a clean confirmation. Recorded: results-log 2026-08-03, paper section 6.

## claims we made and then withdrew

- **"Verification regime" at d=32.** Withdrawn. Rested on one over-interpreted number with a char-window artifact. Recorded: results-log 2026-08-03 corrections, review-response.md.
- **"The internal copy persists / redundant storage."** Withdrawn. The full problem stays in context, so a return to the clean answer is re-derivation from the prompt, not evidence of a stored internal copy. Recorded: results-log 2026-08-03 corrections, paper section 5.
- **Depth-not-params capacity "law."** Downgraded from a claimed law to an open question. Within a family depth and parameters are collinear, and the one cross-family contrast is confounded, so five points cannot separate the axes. Recorded: results-log 2026-08-02, synthesis, paper section 8.

## experiment dropped as not worth the cost

- **Eviction probe.** Built, then found invalid as coded (no chat template, position misalignment, uninterpretable R^2 at 3584 dims / 320 samples). Not rebuilt: once the read-back patch landed cleanly it answered the same question, and the probe's issues were not worth the GPU time. Recorded: review-response.md.

## bugs we caught and fixed (recorded so the fixes are auditable)

- **Answer extraction missed boxed and comma-grouped answers**, understating Llama free-condition accuracy badly (70B at d=16 read as 0.00, actually 1.00). Fixed and all files rescored. Recorded: results-log 2026-08-02.
- **mod-97 externalization matcher false positives** up to 0.72 at high difficulty (long traces mention most residues by chance). Caught by a permutation control; mod-97 benched for externalization, variable chains made primary. Recorded: results-log 2026-08-01.
- **Protection lesion fired only on decode**, so the direct condition was barely lesioned and cot-vs-direct was not a fair comparison. Fixed to lesion during prefill too. Recorded: results-log 2026-08-03, paper section 6.
- **Reasoning-model teacher-forcing** for the read-back patch was off-distribution (the model re-solves after its think block). Moved the clean experiment to a non-reasoning model; the re-solve behavior itself became a logged finding. Recorded: results-log 2026-08-02.

## checks that could have been negative but were clean

- **Budget-wall accuracy of exactly zero** is genuine truncation, not lucky extraction matches (0 of 60 accidental matches). Recorded: results-log 2026-08-01 budget entry.
- **Necessity is an association, not proven by the 1.000 alone**; the causal footing is the read-back patch. Reframed accordingly. Recorded: synthesis, paper section 4.
