# J-space and the chain of thought: where reasoning state lives

## Question and predictions

When does a model's reasoning state live in J-space, the concept workspace read out by the Jacobian lens, and when does it live in the written chain of thought? We began from the natural hierarchy hypothesis, written down before any runs: the model reasons internally while a problem fits its workspace and starts externalizing when capacity is pressured, so writing should switch on at some difficulty, and ablating the workspace should hurt unwritten answers more than written ones.

**Both predictions failed, in informative ways.** There is no difficulty at which writing switches on: models write everything from the easiest problems and cannot carry even short chains without writing. The written values are read back causally, through the residual at the written token. And the state that does stay internal is distinguished by being parallel rather than serial, or cheaply recomputable rather than genuinely sequential. The report defends that revised claim on the assignment model and datasets first, then with the synthetic-task mechanism experiments that explain the benchmark numbers, generalizing from J-space and CoT to internal and external memory.

## Setup

- **Assignment core**: Qwen3-4B with the fitted public Jacobian lens for that model (neuronpedia/jacobian-lens, qwen3-4b artifact). Datasets: GSM8K test; MATH-500; AIME 2024, by which we mean the 30 problems of AIME 2024 I and II as distributed in HuggingFaceH4/aime_2024. The three sets are the difficulty ladder. All revisions pinned in Reproducibility.
- **Synthetic families** for mechanism work, where every intermediate value has exact ground truth and difficulty d (number of dependent steps) is decoupled from output length: variable chains (signed 2-digit ops on a 3-digit start), modular arithmetic, box tracking (5 boxes, swapped contents), DAG reachability. Seeded generators; replay tests validate the corruption arithmetic against the generators.
- **Supporting models**: Qwen2.5-7B-Instruct (also lens-fitted), DeepSeek-R1-Distill-Qwen 1.5B/7B/14B (white-box); DeepSeek V3.2, R1-671B, Llama 3.x up to 70B, Claude Sonnet 4.5 (behavioral, via API).
- **Sampling**: temperature 0.6, top-p 0.95 for chain-of-thought and thinking; temperature 0 for direct answers; fixed in advance.
- **Dose discipline**: intervention strengths are calibrated and frozen on neutral text before any task cell runs, by rules stated before the calibration data existed.
- **Bookkeeping**: every cell logs token-cap hits and unparseable answers separately from wrong answers; every direct cell logs generated token counts so channel closure is audited, not assumed. Tables show accuracy overall and on non-capped items where cap contamination matters.
- **Externalization detector**: exact match of ground-truth values with numeral normalization, calibrated by a permutation control (score each trace against a different instance's values). False positives 0.00 to 0.08 on variable chains; mod-97 reached 0.72 at high difficulty and was benched for externalization measurement.
- **Replication anchors, run before extending**: truncation faithfulness reproduces on our tasks (forcing an answer after a fraction of the model's own CoT gives accuracy monotonic in that fraction, V3.2 near 0 to 0.97, Sonnet 4.5 0.32 to 1.00, collapsing when late steps are removed), and a linear probe reads the final answer from the residual at R-squared 0.96 with a control probe at chance, validating the probing machinery the patch experiments rely on.

## How much models write, and what happens when they cannot

**Models write nearly every intermediate value even on the easiest problems.** On the synthetic chains, the fraction of intermediate values that appear in the written trace (externalization) sits between 0.93 and 1.00 at every difficulty from one step to sixty-four, for every model from 1.5B to 671B. Splitting by correctness sharpens this: among correct traces at sixteen or more steps, externalization is exactly 1.000 (n=1935 pooled across three model sizes) against roughly 0.5 among wrong ones, and the ceiling is uniform across early, middle, and late chain positions. A format explanation would concentrate the ceiling on the last steps, since early results could in principle be carried internally; they never are. We state the 1.000 as an association rather than necessity, because the trace format writes step results by construction; the causal footing comes in the next section.

**Forced to answer with no written reasoning at all, models fail after one or two dependent steps.** If models write everything, the next question is what they can do when they cannot write. We prompt for the bare answer and verify from token counts that the model really wrote nothing:

| Model | d=1 | d=2 | d=4 | d=8 | Channel verified |
|---|---|---|---|---|---|
| Qwen2.5-7B-it | 1.00 | 0.96 | 0.04 | 0.00 | Yes (median 4 tok) |
| Llama-3.1-8B | 1.00 | 0.47 | 0.00 | 0.00 | Yes (2-4 tok) |
| Llama-3.3-70B | 1.00 | 1.00 | 0.93 | 0.03 | Yes (2-4 tok) |
| V3.2 (671B) | 0.23 | 0.03 | 0.00 | 0.00 | Yes (2 tok) |
| R1 distills | - | - | - | - | No (74-89 percent hit cap) |

The R1 distills leak reasoning tokens in direct mode despite think-suppression, so their direct cells are excluded (the channel was not actually closed). Internal serial capacity is real, small, and model-dependent (d_int, the deepest reliably-direct depth, is 1 to 2 for most models and about 5 for Llama-70B); whether depth or parameter count sets it is unresolved, since the two are collinear within families. The ceiling is specifically about chains of unmemorizable random values: the same V3.2 that fails two synthetic steps answers 38 percent of GSM8K directly with one-word outputs, because natural problems are partly recomputable and memorizable. That contrast returns below as the boundary of when written values matter.

**Qwen3-4B shows the same pattern on GSM8K, MATH-500, and AIME.** On Qwen3-4B, the free-direct gap is large at every rung, and the termination logging shows the model failing to comply with the no-writing instruction more often as problems harden: 0.29 of GSM8K direct attempts overrun the 32-token answer budget, rising to 0.80 on AIME. The harder the problem, the more the model tries to write even when told not to. The cost of the written channel is the cleanest difficulty readout of all: median thinking length grows 1952 to 3503 to 11819 tokens down the ladder.

| Dataset | Direct acc (non-cap) | Free acc (non-cap) | Direct cap rate | Free cap rate |
|---|---|---|---|---|
| GSM8K (n=150) | 0.10 (0.12) | 0.84 (0.99) | 0.29 | 0.46 |
| MATH-500 (n=150) | 0.11 (0.19) | 0.65 (0.76) | 0.47 | 0.23 |
| AIME 2024 (n=30) | 0.00 (0.00) | 0.67 (0.90) | 0.80 | 0.30 |

Together these rule out the overflow picture: writing is not what happens when a workspace fills up, because the workspace never held a chain to begin with. But writing everything is compatible with two readings, a trace the model actually computes with, or a commentary produced alongside computation happening elsewhere. The corruption experiments decide between them.

## Corruption, patch, and budget results

**Editing one written value usually changes the final answer.** Corrupting the last written mention of a mid-chain value in a reasoning model's own trace flips the final answer 31, 42, 50, and 36 percent of the time at d = 4, 8, 16, 32 (n = 149, 146, 138, 128 corruptible items of 150; yield falls with d because only correct traces are corrupted, selecting harder cells toward easier instances). A pure narration reading predicts near zero. But a flip is ambiguous in two ways: the corrupted token also feeds any recomputation, and a reasoning model re-solves the problem after its think block, returning to the clean answer from the prompt rather than from any internal copy. The re-solve is a finding in itself (the think phase reads the trace, the answer phase re-derives from scratch), and it dictated the next design: run the causal version on a model that continues a worked trace straight to the answer.

**The answer follows whatever value we write into the internal state at that token.** The causal version overwrites the residual stream at the corrupted token (a band of middle layers, from that token to the end of the prefix) while leaving the visible text corrupt. On Qwen2.5-7B-Instruct at ten steps (n=141, 119 with a corruption effect), corruption flips the answer on 84 percent of items, and the items without an effect follow neither answer, so essentially nothing recomputes the value from the unchanged earlier steps still in context.

| Measurement | Value |
|---|---|
| Patch to clean state, token still corrupt: follows clean | 0.97 [0.94, 0.99]; replicates at d=20: 0.93 [0.88, 0.97] |
| Patch to arbitrary third value: follows that value | 0.76 [0.70, 0.82]; follows clean 0.00 |
| Random-direction patch at matched norm: follows clean | 0.00 [0.00, 0.01] |
| Reasoning model (R1-distill-7B, n=91): clean / third value | 1.00 / 0.74 [0.66, 0.82] |
| Layer-band sweep, early/mid/late revert | 0.96 / 0.97 / 0.94 |

The third-value condition answers the objection that restoring clean state injects the answer: overwrite the residual with a value the model never wrote and the answer follows that value, forward-computed through the remaining steps. The same condition makes the reasoning-model result clean, because the post-think re-solve can produce the clean answer but never an arbitrary injected one; the elevated random arm there (0.29 versus 0.00 on the instruct model) is the re-solve, not the register. Restoring an early, middle, or late layer band works about equally, so the value is represented redundantly across depth and we claim no specific circuit. A start-controlled probe closes the loop on where the answer comes from: decoding the computed part of the answer (start value regressed out, since it inflates naive early decodability) rises from 0.27 two steps into a twelve-step chain to 0.83 at the end, control at chance, so the computation emerges as the steps are written rather than existing before them.

**Stronger models follow the edited value more often, not less.** Running the behavioral corruption through API prefill:

| Model | Follows corruption |
|---|---|
| R1-distill-7B (d=8) | 0.42 |
| DeepSeek V3.2, 671B (d=10) | 0.78 |
| Claude Sonnet 4.5 (d=10) | 0.97 |

Stronger models depend on their written values more, not less, which matters for monitoring: the trace stays load-bearing at the frontier. Observational across architectures, not a causal scale claim.

**A written value only matters when the model cannot recompute it from the problem statement.** On synthetic chains the flip rate is high at every depth tested (0.80, 0.64, 0.78, 0.76, 0.70 at d = 3, 5, 8, 12, 16), yet on GSM8K corrupting a written intermediate changes the answer only 0.10 of the time against a 0.05 resampling floor (deep subset, five or more calculation steps, n=63): a GSM8K intermediate is a shallow function of the problem's givens that the model simply recomputes. Read-back carries genuinely serial, non-shortcuttable state and does not fire when recomputation is cheap. This is the same boundary that lets V3.2 answer GSM8K directly, and it is the prediction the assignment-core corruption run tests on Qwen3-4B [result pending].

**Under token budgets, models shorten their wording but keep writing every value.** Hard token budgets on V3.2 (chains, d=16) compress traces up to 2.5x with accuracy intact, then fail outright once the budget cannot fit the values, rather than moving the computation inward:

| Budget, d=16 | Tokens | Accuracy | Externalization |
|---|---|---|---|
| Free | 466 | 1.00 | 1.00 |
| 256 | 184 | 0.93 | 0.98 |
| 128 | 128 (cap) | 0.00 | 0.72 |

The failure floor sits near 12 tokens per step, below which externalization tracks budget over need (0.72, 0.36, 0.17 down the difficulty column at budget 128). Wall cells are genuine truncation (0 of 60 graded correct by accident), though the model is told its cap, so the floor conflates cannot-compress with does-not-plan.

**What matters in the trace is the computed values themselves.** Requesting the same chains in different scratchpad formats:

| Format, d=48 | Accuracy | Tokens |
|---|---|---|
| Code with evaluated values | 1.00 | 555 |
| Prose | 1.00 | 1105 |
| Code without values | 0.97 | 440 |
| Full-state dump | 0.07 | 3848 |

The no-values code format succeeds only to the degree the model disobeys it and writes values anyway: per-instance externalization correlates with correctness at +0.74 (accuracy 0.58 when under half the values get written, 1.00 when nearly all do), and at low difficulty, where compliance is high, accuracy drops to 0.70. Over-writing hurts like under-writing (the state dump collapses at depth). A compact value-carrying scratchpad is both the efficient external memory and the most legible one.

## Serial versus parallel state, and the J-space tests

**Tasks that need many values at once can be done in the head; tasks where each value depends on the previous one cannot.** Box tracking stresses storage without seriality, and it behaves differently from chains: the model tracks sixteen swaps correctly while writing only about a fifth of the state, and externalization stops discriminating correct from wrong traces (0.20 versus 0.17, where chains sit at 1.00 versus 0.5). The causal counterpart: a residual lesion at matched dose (fired during prompt processing and decode, with dose parity reported on both neutral-text and on-task KL since neither meter alone is clean) drops box-tracking accuracy by 0.34 under the target window and 0.33 under the control window, against 0.11 and 0.04 for chains, where both families have headroom (d=2 to 4). The internally-stored task is about 3x more fragile to internal damage, robustly to which window is lesioned. The lesion is blunt, it also damages the re-reading of written values, which shows at longer chains (chains drop 0.38 at d=8), so the family comparison is only clean at low to middle difficulty. That bluntness motivated the targeted instrument the assignment is anchored on.

**J-space ablation at a dose that leaves normal text generation intact changes nothing on these tasks.** The J-space ablation projects out, at every position, the orthonormalized preimages of the top-k concepts by lens logit, with a random orthonormal subspace at identical dose as control. The dose rule was frozen in advance: the largest k and alpha keeping neutral-text top-1 agreement at least 0.80 and perplexity ratio at most 1.30. On Qwen2.5-7B-Instruct this lands at k=16, alpha=0.5 (perplexity ratio 1.12, top-1 0.87, KL 0.20 per token; the random arm at the same dose is more damaging on neutral text, perplexity ratio 1.29, KL 0.27, which is the conservative direction for any targeted-effect claim). At that dose, direct and cot accuracy match the clean arm at every difficulty, and cot externalization stays at ceiling under the squeeze. So a targeted ablation of the top of J-space neither impairs the chains nor induces more writing, consistent with the lesion-based null on write-policy adaptation but sharper, since this squeeze is provably gentle on neutral text. Either the write policy is not load-sensitive at inference time, or chain state is carried outside the top-k lens concepts. The assignment-core 2x2 on GSM8K, ablation by condition under the same frozen-dose discipline on Qwen3-4B, discriminates these on the benchmark where the anchor result was originally claimed [result pending]; a dose escalation with neutral-text damage reported alongside is the planned follow-up.

## Positioning

Expressivity theory says fixed-depth transformers are limited to parallel computation in one pass and that CoT length buys serial power (Merrill and Sabharwal 2023, 2024; Li et al. 2024; Feng et al. 2023); it predicts the behavioral results above and motivates the mechanism work, which it does not describe. Faithfulness studies (Turpin 2023; Lanham 2023; Bentham 2024) and the recent activations-carry-state literature (2603.05488, 2603.01437, 2604.18307, 2606.13603) establish the correlational premise. The two nearest papers stop short of the causal test: 2604.15726 calls for the token-corruption experiment it never runs, and 2605.30343 engineers latent memory blocks without manipulating capacity or measuring read-back. The J-space construct and lens are from Gurnee et al. 2026.

## Null results, withdrawn claims, and limitations

Nulls and negatives, each detailed where its result lives above:

- No externalization onset exists, so the planned onset-scaling-law phase had nothing to fit; the measurable boundary became d_int, where depth versus parameters is collinear and unresolved.
- Damaging the workspace does not induce writing, whether by blunt lesion past its cliff (externalization falls, traces disintegrate) or by calibrated J-space ablation at the frozen dose (no change).
- Restricting the token channel does not induce internalization (the budget wall is truncation, not compression into activations).
- GSM8K read-back is null for recomputability reasons; the DAG task was uninformative for externalization (every node label already in the prompt); mod-97 was benched by its matcher false-positive rate.
- Withdrawn on review: a verification-regime reading and a persistent-internal-copy reading (both explained by re-derivation from the in-context prompt still being available), and an early-decodability claim (start-value confound, corrected by the start-controlled probe).
- The first protection attempt was invalid as coded: the lesion fired only on generated tokens, so the direct condition was barely lesioned and the comparison was not a protection test. The corrected version is the lesion result above.

Limitations. Recomputability bounds the central mechanism's footprint to genuinely serial, non-shortcuttable state. Synthetic families trade ecological validity for exact ground truth. White-box causal results are at 4B to 7B; frontier evidence is behavioral. The patch overwrites the whole residual at a position; the third-value swap shows the value is the causal quantity, but the value subspace is not isolated, and decomposing the patch into its J-space projection and complement is the planned experiment that would locate the register relative to the lens-readable workspace. The lesion cannot separate workspace damage from read-back damage. The budget floor conflates cannot-compress with does-not-plan. What would most change the picture: a within-task recomputability manipulation, the J-space patch decomposition, and the pending Qwen3-4B cells, which either replicate the anchor asymmetry on the intended benchmark or extend the null to it.

## Reproducibility

Pinned revisions, kept out of the main text:

- Qwen/Qwen3-4B 1cfa9a720891; Qwen/Qwen2.5-7B-Instruct a09a35458c70
- DeepSeek-R1-Distill-Qwen-1.5B ad9f0ae0864d; 7B 916b56a44061; 14B 1df8507178af
- neuronpedia/jacobian-lens a4114d7752d1 (qwen3-4b and qwen2.5-7b-it artifacts); lens library commit 581d398613e5
- GSM8K test.jsonl sha1 4a3eef48d603; HuggingFaceH4/MATH-500 6e4ed1a2a79a; HuggingFaceH4/aime_2024 2fe88a2f1091

Dose rules were frozen before task cells ran. All cells log cap hits, unparseable answers, and direct-cell token counts. Raw data regenerate from src/harness; figures from src/analysis/figures.py; the dated evidence trail is notes/results-log.md.
