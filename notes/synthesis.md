# synthesis: what the experiments say

Living document. The claim, the evidence, the alternatives ruled out, and what is left to nail down. Updated as results land; numbers cite results-log.md entries by date.

## the claim

For serial reasoning past a shallow internal-capacity limit, chain-of-thought is not a spillover buffer that models use under pressure. It is the medium the computation runs in. The residual stream is a wide but shallow workspace: it holds many values in parallel but cannot carry a chained result more than about one serial step without writing it down. So models write every intermediate of a serial chain, read those written values back to compute the next step, and keep a short-lived internal copy that verifies the written one. The token stream is the durable serial memory; the residual stream is a fast parallel register file and a verifier.

This is sharper than the memory-hierarchy framing we started with, and in one respect it contradicts it. The starting hypothesis was that models externalize *when internal capacity is pressured*, implying a load-triggered onset. We do not find an onset. Externalization is saturated from the easiest problems at every scale and family we measured. The trade-off is not "internal until full, then external." It is "external for anything serial, internal for parallel storage and verification." The dividing line runs along the type of memory demand, not its amount.

## the evidence, and what each rules out

1. **Externalization is necessary for serial depth, not incidental.** Across the 1.5B/7B/14B distill ladder, externalization fraction among correct traces at difficulty 16 and up is exactly 1.000 (n=1935 correct traces, 2026-08-02). Among wrong traces it is ~0.5. No correct deep chain omits a value. Rules out: CoT as post-hoc narration on these tasks (a narration would not need to be complete to be correct).

2. **Written values are read back.** Corrupting the last written mention of a mid-chain value flips the answer 31 to 50 percent of the time on variable chains, rising with difficulty (gate B, 2026-08-01). Rules out: the antagonist position that reasoning is latent and the trace is a projection (arXiv:2604.15726), which predicts near-zero flips. Refuted at 7B scale.

3. **The internal copy persists and verifies.** Under the same corruption, the answer follows the clean value 48 to 68 percent of the time, and at high difficulty the model increasingly notices the edit and restates the clean value early (restates_clean 0.45 at d=32). Rules out: strict write-then-evict. The two tiers hold the value at once; the internal one checks the external one.

4. **Written values are incompressible.** Under token budgets, prose compresses up to 2.5x with accuracy intact, but externalization fraction stays at 0.98 to 1.00; below ~12 tokens per step the model truncates and fails rather than dropping values or moving computation inward (budget sweep, 2026-08-01). Rules out: values as optional verbosity. They behave like load-bearing cargo.

5. **The internal ceiling is serial, and shallow.** Direct-answer accuracy (no writing) collapses after one arithmetic step for every model except the largest, which reaches ~4 steps (Llama-70B, 2026-08-02). Rules out: a wide internal serial capacity. One forward pass does roughly one serial op here.

6. **The demand type, not amount, sets the tier.** Externalization predicts success on serial chains (ext|correct = 1.0) but is uninformative on entity tracking, where models succeed at 16-move tracking while writing a fifth of the state (2026-08-02). Rules out: a single scalar "capacity" account. Parallel storage lives internally; serial chaining does not. This is the transformer-expressivity prediction (fixed depth bounds serial computation, not parallel width) appearing behaviorally within one model at matched task surface.

## the law

Because externalization has no onset, the fittable quantity is the internal serial capacity itself: d_int, the depth a model completes without writing. Early evidence (capacity_law.py, variable chains) is that d_int tracks layer count, not parameters (corr with depth positive, with log-params null), consistent with depth being the serial-step budget. The Llama depth ladder (1B to 70B, one architecture) is running to turn this from an ordinal observation into a within-family fit. If d_int scales with depth and not width across a clean ladder, that is the paper's quantitative law and it is the theory-predicted one.

## what would still change the picture

- Gate A (running): if sub-cliff internal lesions *do* shift writing, clause "no load-triggered onset" needs qualifying: the onset may exist but sit below the easiest task we used. If lesions only degrade, the saturation picture holds.
- Eviction probe (running): clause 3 predicts written-value decodability at current position stays at or above the suppressed variant (redundant cache). A negative gap would revive eviction and complicate the verifier story.
- Protection experiment (running): the differential prediction is that internal lesions hurt entity tracking more than variable chains, and CoT protects chains more than boxes. That is the causal test of clause 6, the strongest single claim.

## novelty position

The correlational premise (activations carry reasoning state, CoT is sometimes unfaithful) is established by the 2025-26 wave and we do not re-claim it. The contribution is the causal chain, write then read-back then verify, measured with token corruption and teacher-forced probing; the incompressibility result; and the reframe of the onset question into an internal-serial-capacity law that comes out on the depth axis the theory predicts. None of the four nearest papers (2604.15726, 2605.30343, Kudo 2024, Lanham 2023) run the corruption-following, eviction, or capacity-ladder experiments; the first explicitly calls for the corruption design it never runs.
