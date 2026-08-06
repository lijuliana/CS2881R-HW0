# J-space and the chain of thought: where reasoning state lives

## Question and predictions

When does a model's reasoning state live in J-space, the concept workspace read out by the Jacobian lens, and when does it live in the written chain of thought? We began from the natural hierarchy hypothesis, written down before any runs: the model reasons internally while a problem fits its workspace and starts externalizing when capacity is pressured, so writing should switch on at some difficulty, and ablating the workspace should hurt unwritten answers more than written ones. The data rejected the first half of this picture and complicated the second. There is no difficulty at which writing switches on, because models write everything from the easiest problems and cannot carry even short chains without writing; the written values turn out to be read back causally, through the residual at the written token; and the state that does stay internal is distinguished by being parallel rather than serial, or cheaply recomputable rather than genuinely sequential. The report defends that revised claim on the assignment model and datasets first, then with the synthetic-task mechanism experiments that explain the benchmark numbers, generalizing from J-space and CoT to internal and external memory in general.

## Setup

The assignment core uses Qwen3-4B (revision 1cfa9a720891) with the fitted public Jacobian lens for that model (neuronpedia/jacobian-lens revision a4114d7752d1, qwen3-4b artifact; library commit 581d398613e5). Datasets are GSM8K test (openai/grade-school-math, test.jsonl sha1 4a3eef48d603), MATH-500 (HuggingFaceH4/MATH-500 revision 6e4ed1a2a79a), and AIME 2024, by which we mean the 30 problems of AIME 2024 I and II as distributed in HuggingFaceH4/aime_2024 revision 2fe88a2f1091. The three sets are the difficulty ladder. The mechanism experiments use synthetic families where every intermediate value has exact ground truth and difficulty d (the number of dependent steps) is decoupled from output length: variable chains of signed 2-digit operations on a 3-digit start, modular arithmetic, box tracking, and DAG reachability, with seeded generators and replay tests validating the corruption arithmetic. Supporting models there: Qwen2.5-7B-Instruct (a09a35458c70, also lens-fitted), DeepSeek-R1-Distill-Qwen 1.5B/7B/14B (ad9f0ae0864d, 916b56a44061, 1df8507178af), and, behaviorally through APIs, DeepSeek V3.2, R1-671B, Llama 3.x up to 70B, and Claude Sonnet 4.5.

Sampling is temperature 0.6, top-p 0.95 for chain-of-thought and thinking, temperature 0 for direct answers, fixed in advance. Intervention doses are calibrated and frozen on neutral text before any task cell runs. Every generation cell logs token-cap hits and unparseable answers separately from wrong answers, and every direct cell logs its generated token count, so termination artifacts and channel closure are audited rather than assumed. Where a cell has meaningful cap contamination, tables show accuracy both overall and on non-capped items.

## Externalization and the difficulty ladder

The hierarchy hypothesis predicts a spill threshold, so the first measurements look for one. On the synthetic chains, externalization, the fraction of ground-truth intermediate values appearing in the trace, sits between 0.93 and 1.00 at every difficulty from one step to sixty-four, for every model from 1.5B to 671B. No model waits for difficulty before writing. Splitting by correctness sharpens this: among correct traces at sixteen or more steps, externalization is exactly 1.000 (n=1935 pooled across three model sizes), against roughly 0.5 among wrong ones, and the ceiling is uniform across early, middle, and late chain positions. A format explanation would concentrate the ceiling on the last steps, since early results could in principle be carried internally; they never are. We state the 1.000 as an association rather than necessity, because the trace format writes step results by construction; the causal footing comes two sections down.

If models write everything, the next question is what happens when they cannot write. Closing the token channel (answer-only prompts, closure verified by generated token counts) collapses accuracy after one or two dependent steps for nearly every model:

| Model | d=1 | d=2 | d=4 | d=8 | Channel verified |
|---|---|---|---|---|---|
| Qwen2.5-7B-it | 1.00 | 0.96 | 0.04 | 0.00 | Yes (4 tok) |
| Llama-3.1-8B | 1.00 | 0.47 | 0.00 | 0.00 | Yes (2-4 tok) |
| Llama-3.3-70B | 1.00 | 1.00 | 0.93 | 0.03 | Yes (2-4 tok) |
| V3.2 (671B) | 0.23 | 0.03 | 0.00 | 0.00 | Yes (2 tok) |
| R1 distills | - | - | - | - | No (74-89 percent cap) |

The R1 distills leak reasoning tokens in direct mode despite think-suppression, so their direct cells are excluded rather than reported as closed-channel evidence. Internal serial capacity is real, small, and model-dependent; whether depth or parameter count sets it we cannot resolve, since the two are collinear within families. And the ceiling is specifically about chains of unmemorizable random values: the same V3.2 that fails two synthetic steps answers 38 percent of GSM8K directly with one-word outputs, because natural problems are partly recomputable and memorizable. That contrast returns below as the boundary of the read-back mechanism.

The assignment ladder shows the same structure at benchmark scale. On Qwen3-4B, free (thinking) accuracy declines down the ladder while direct accuracy is near floor everywhere, and the cap-rate column carries an observation the termination logging surfaced: forbidden from writing, the model overruns its answer-only budget more and more often as problems harden (0.29 on GSM8K to 0.80 on AIME). It increasingly tries to write anyway. The cost of the written channel is the cleanest difficulty readout of all: median thinking length grows from 1952 tokens on GSM8K to 3503 on MATH-500 to 11819 on AIME.

| Dataset | Direct acc (non-cap) | Free acc (non-cap) | Direct cap rate | Free cap rate |
|---|---|---|---|---|
| GSM8K | 0.10 (0.12) | 0.84 (0.99) | 0.29 | 0.46 |
| MATH-500 | 0.11 (0.19) | 0.65 (0.76) | 0.47 | 0.23 |
| AIME 2024 | 0.00 (0.00) | 0.67 (0.90) | 0.80 | 0.30 |

Together these rule out the overflow picture. Writing is not what happens when a sufficient workspace fills, because the workspace never held a chain to begin with. But saturation alone cannot distinguish a trace that carries the computation from one that narrates it, which is what the corruption experiments were run to decide.

## Corruption, patch, and budget results: the trace as working memory

The direct test of narration versus computation is to edit a written value and watch what the model does with it. Corrupting the last written mention of a mid-chain value in a reasoning model's own trace flips the final answer 31 to 50 percent of the time, rising from four to sixteen steps, which already refutes a pure narration reading. But a flip is ambiguous in two ways: the corrupted token also feeds any recomputation, and a reasoning model re-solves the problem after its think block, returning to the clean answer from the prompt rather than from any internal copy. That re-solve behavior is worth recording in its own right, the think phase reads the trace while the answer phase re-derives, and it dictated the next design: run the causal version on a model that continues a worked trace straight to the answer.

The causal version overwrites the residual stream at the corrupted token while leaving the visible text corrupt. On Qwen2.5-7B-Instruct at ten steps (n=141), corruption flips the answer on 84 percent of items, and the items without an effect follow neither answer, so essentially nothing recomputes the value from the unchanged earlier steps still sitting in context.

| Measurement | Value |
|---|---|
| Patch to clean state, token still corrupt: follows clean | 0.97 [0.94, 0.99]; d=20: 0.93 |
| Patch to arbitrary third value: follows that value | 0.76 [0.70, 0.82]; follows clean 0.00 |
| Random-direction patch at matched norm: follows clean | 0.00 [0.00, 0.01] |
| Same on the reasoning model (R1-distill-7B): clean / third value | 1.00 / 0.74 [0.66, 0.82] |
| Layer-band sweep, early/mid/late revert | 0.96 / 0.97 / 0.94 |

Restoring the clean state reverts the answer; a matched-norm random perturbation does nothing. The third-value condition answers the objection that restoring clean state injects the answer: overwrite the residual with a value the model never wrote and the answer follows that value, so the residual at the written token is a readable value register that downstream computation dereferences. The same condition is what makes the reasoning-model result clean, because the post-think re-solve can produce the clean answer but never an arbitrary injected one; the elevated random arm there (0.29) is the re-solve, not the register. The register is carried redundantly across depth, since restoring an early, middle, or late band works about equally, so we claim robustness of the representation rather than a circuit. A start-controlled probe closes the loop on where the answer comes from: the computed part of the final answer is barely decodable two steps into a chain (0.27) and grows to 0.83 by the end, so the computation emerges as the steps are written rather than existing before them.

Read-back is not a small-model artifact, and it strengthens with capability. Running the behavioral corruption through API prefill:

| Model | Follows corruption |
|---|---|
| R1-distill-7B (d=8) | 0.42 |
| DeepSeek V3.2, 671B (d=10) | 0.78 |
| Claude Sonnet 4.5 (d=10) | 0.97 |

Stronger models depend on their written values more, not less, which matters for monitoring: the trace stays load-bearing at the frontier. What bounds the mechanism is not depth but recomputability. On synthetic chains the flip rate is high at every depth tested (0.80, 0.64, 0.78, 0.76, 0.70 at d=3 to 16), yet on GSM8K corrupting a written intermediate changes the answer only 0.10 of the time against a 0.05 resampling floor, because a GSM8K intermediate is a shallow function of the problem's givens that the model simply recomputes. Read-back carries genuinely serial, non-shortcuttable state and does not fire when recomputation is cheap; this is the same boundary that let V3.2 answer GSM8K directly, and it is the prediction the assignment-core corruption run tests on Qwen3-4B [result pending].

If written values are working memory, they should be the last thing a model gives up under output pressure, and they are. Under hard token budgets, V3.2 compresses prose while keeping every value, and once the budget cannot fit the values it fails outright rather than moving the computation inward:

| Budget, d=16 | Tokens | Accuracy | Externalization |
|---|---|---|---|
| Free | 466 | 1.00 | 1.00 |
| 256 | 184 | 0.93 | 0.98 |
| 128 | 128 (cap) | 0.00 | 0.72 |

The wall cells are genuine truncation (0 of 60 graded correct by accident), though the model is told its cap, so the floor conflates cannot-compress with does-not-plan. The format experiments say the same thing from the other side: a code-like format that writes each evaluated value solves 48-step chains at 555 tokens where prose needs 1105, a verbose full-state dump collapses (0.07 at d=48), and a format that writes operations without their values fails in proportion to how many values it omits, with per-instance externalization correlating with correctness at +0.74. The payload is the evaluated value, not the operation and not the prose around it, and the efficient external memory is also the most legible one.

## Serial versus parallel state, and the J-space tests

Everything so far concerns chains, where each value depends on the previous one. Box tracking, five boxes with repeatedly swapped contents, stresses storage without seriality, and it behaves differently: the model tracks sixteen swaps correctly while writing only about a fifth of the state, and externalization stops discriminating correct from wrong traces (0.20 versus 0.17). Serial state lives on the page; parallel state can live in activations. That split has a causal counterpart: an internal lesion at matched dose should hurt the internally-stored task more, and it does, dropping box-tracking accuracy by 0.34 against 0.11 for chains where both have headroom. The lesion is blunt, it also damages the re-reading of written values, which shows at longer chains, so the comparison is only clean at low to middle difficulty, and it motivated replacing the lesion with the targeted instrument the assignment is anchored on.

The J-space version ablates exactly the currently active concept directions: at each position, project out the orthonormalized preimages of the top-k concepts by lens logit, with a random orthonormal subspace at identical dose as control. The dose is chosen on neutral text by a rule frozen in advance (largest k and alpha keeping top-1 agreement at least 0.80 and perplexity ratio at most 1.30), which lands at k=16, alpha=0.5 on Qwen2.5-7B-Instruct (perplexity ratio 1.12, top-1 0.87; the random arm at the same dose is more damaging on neutral text, 1.29, the conservative direction for any targeted-effect claim). At that dose, on the synthetic chains, nothing moves: direct and cot accuracy match the clean arm at every difficulty, and cot externalization stays at ceiling under the squeeze. A targeted, coherence-safe ablation of the top of J-space neither impairs the chains nor induces more writing, consistent with the lesion-based null on write-policy adaptation but sharper, since this squeeze is provably gentle on neutral text. Either the write policy is not load-sensitive at inference time, or chain state is carried outside the top-k lens concepts. The assignment-core 2x2 on GSM8K, ablation by condition at the same frozen-dose discipline on Qwen3-4B, discriminates these on the benchmark where the anchor result was originally claimed [result pending], and a dose escalation with neutral-text damage reported alongside is the planned follow-up.

## Limitations and open questions

Recomputability bounds the central mechanism: read-back carries serial, non-recomputable state, and much of GSM8K is not that, so the footprint is narrower than all chain-of-thought. The synthetic families buy exact intermediate ground truth at the cost of ecological validity. White-box causal results are at 4B to 7B; the frontier evidence is behavioral. The patch overwrites the whole residual at a position, and although the third-value swap shows the value is the causal quantity, the value subspace itself is not isolated; decomposing the patch into its J-space projection and complement is the planned experiment that would say whether the register lives in the lens-readable workspace. The lesion cannot separate workspace damage from read-back damage. Depth versus parameter count for internal serial capacity is unresolved for lack of a param-matched depth-varying model set. Withdrawn along the way, for the record: a verification-regime reading and a persistent-internal-copy reading (both turned out to be re-derivation from the in-context prompt) and an early-decodability claim (start-value confound, corrected by the start-controlled probe). What would most change the picture: a within-task recomputability manipulation, the J-space patch decomposition, and the pending Qwen3-4B cells, which either replicate the anchor asymmetry on the intended benchmark or extend the null to it.

## Reproducibility

Revisions and sampling are in Setup. Dose rules were frozen before task cells ran. All cells log cap hits, unparseable answers, and direct-cell token counts. Raw data regenerate from src/harness; figures from src/analysis/figures.py; the dated evidence trail is notes/results-log.md.
