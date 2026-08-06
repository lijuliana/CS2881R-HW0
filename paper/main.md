# J-space and the chain of thought: where reasoning state lives

Technical report. Figures in results/figures; dated evidence trail in notes/results-log.md.

## 1. Question, hypothesis, and design

**Research question.** When does a model's reasoning state live in J-space, the concept workspace read out by the Jacobian lens, and when does it live in the written chain of thought? Does the split move as problems get harder or as either side is constrained?

**Hypothesis as written before running.** A memory hierarchy with a threshold: the model reasons internally while the problem fits its workspace and begins externalizing when capacity is pressured, so writing should switch on at some difficulty. The data rejected this; the revised claim the report defends is that for serial computation the written trace is the medium the computation runs in, J-space and the wider residual stream hold parallel state and roughly one dependent step, and read-back of written values is the mechanism connecting the two.

**What we varied and measured.** Difficulty (dataset ladder and synthetic step count), the token channel (open, closed, capped, edited), and the internal side (J-space ablation at a calibrated dose, residual lesion, residual patch). Measured: accuracy, externalization (fraction of ground-truth intermediate values appearing in the trace), corruption-follow rates, and per-cell bookkeeping (token-cap hits and unparseable answers logged separately from wrong answers; generated token counts in every direct cell to verify the channel was closed).

**Models.** Assignment core: Qwen3-4B (rev 1cfa9a720891) with the fitted public Jacobian lens (neuronpedia/jacobian-lens rev a4114d7752d1, qwen3-4b artifact; library commit 581d398613e5). Mechanism supplement: Qwen2.5-7B-Instruct (a09a35458c70, also lens-fitted), DeepSeek-R1-Distill-Qwen 1.5B/7B/14B (ad9f0ae0864d / 916b56a44061 / 1df8507178af), DeepSeek V3.2, R1-671B, Llama 3.x 1B to 70B, Claude Sonnet 4.5 (behavioral, via API).

**Datasets and tasks.** GSM8K test (openai/grade-school-math, test.jsonl sha1 4a3eef48d603); MATH-500 (HuggingFaceH4/MATH-500 rev 6e4ed1a2a79a); AIME 2024, meaning the 30 problems of AIME 2024 I and II as distributed in HuggingFaceH4/aime_2024 rev 2fe88a2f1091. These three are the difficulty ladder. Synthetic families for mechanism work, where every intermediate value has exact ground truth and difficulty d (number of dependent steps) is decoupled from output length: variable chains (3-digit start, 2-digit signed ops), modular arithmetic, box tracking, DAG reachability. Generators seeded; corruption arithmetic validated against the generators by replay tests.

**Sampling.** Temperature 0.6, top-p 0.95 for chain-of-thought and thinking; temperature 0 for direct cells; fixed in advance. Ablation doses calibrated and frozen on neutral text before any task cell (Section 3.2).

## 2. Part I: assignment core (Qwen3-4B, GSM8K / MATH-500 / AIME 2024)

### 2.1 Free vs direct accuracy across the ladder

**Question.** How much does accuracy depend on the written channel, and how does that dependence scale with difficulty?

**Design.** Varied: condition (free = thinking enabled; direct = no-think, answer only, 32-token cap) x dataset. Measured: accuracy, cap-hit rate, unparseable rate, generated tokens. n = 150 GSM8K, 150 MATH-500, 30 AIME.

**Result.** [FINAL TABLE PENDING AIME FREE CELL; partial:]

| dataset | direct acc (non-cap) | free acc (non-cap) | direct cap rate | free cap rate |
|---|---|---|---|---|
| GSM8K | 0.10 (0.12) | 0.84 (0.99) | 0.29 | 0.46 |
| MATH-500 | 0.11 (0.19) | 0.65 (0.76) | 0.47 | 0.23 |
| AIME 2024 | 0.00 (0.00) | [pending] | 0.80 | [pending] |

**Interpretation.** The free-direct gap is large at every rung and widens with difficulty. The direct cap-rate column is a finding of its own: forbidden from writing, the model increasingly overruns the answer-only budget as problems harden (0.29 GSM8K to 0.80 AIME), that is, it tries to write anyway. Channel closure is verified by median direct token counts (5 to 32).

### 2.2 J-space ablation 2x2 (ablation x condition), GSM8K

**Question.** Does ablating the active J-space hurt direct answering more than chain-of-thought answering, the signature of written tokens substituting for workspace state?

**Design.** Varied: arm (clean / J-space ablation / random-subspace control at the same frozen dose) x condition (direct / cot). Measured: accuracy plus bookkeeping. Dose frozen on neutral text before task cells by the pre-stated rule (largest k, alpha with top-1 agreement at least 0.80 and perplexity ratio at most 1.30). n=30 per cell.

**Result.** [PENDING TONIGHT'S RUN]

**Interpretation.** [PENDING]

### 2.3 Corrupting written intermediates in GSM8K worked solutions

**Question.** Are written intermediate values causally read back on a benchmark dataset?

**Design.** Varied: one computed mid-solution value (not a given of the problem) edited by +7; model continues from the corrupted prefix. Control: no-corruption resample from the same clean prefix (the sampling noise floor). Measured: answer-change rate. n=80 corrupted solutions.

**Result.** [PENDING TONIGHT'S RUN]

**Interpretation.** [PENDING; the synthetic prediction from Section 3.5 is that GSM8K intermediates are largely recomputable, so the change rate should sit near the noise floor except on deeper problems]

## 3. Part II: mechanism on synthetic families

The benchmark datasets cannot supply exact ground truth for every intermediate value or a difficulty knob decoupled from output length. The synthetic families supply both, and the results below explain the Part I numbers. Coarse residual-level instruments (lesion, full-residual patch) appear as precursors and robustness checks for the J-space versions.

### 3.1 Externalization vs difficulty

**Question.** Is there a difficulty threshold where writing switches on?

**Design.** Varied: d 1 to 64, model 1.5B to 671B, free generation. Measured: externalization fraction; detector calibrated by a permutation control (false positives 0.00 to 0.08 on variable chains; mod-97 benched at 0.72 and excluded).

**Result.** Externalization 0.93 to 1.00 everywhere including d=1, every model. Split by correctness at d of 16 and up: exactly 1.000 among correct traces (n=1935 pooled over three distill sizes), about 0.5 among wrong ones. Uniform across chain position (early, middle, late all 1.00).

**Interpretation.** No spill threshold exists; the write policy is saturated from the start. The 1.000 is stated as association, not necessity (the trace format writes step results by construction); its causal footing is Section 3.3. Position-uniformity and the closed-channel results below argue against a format artifact.

### 3.2 Closed-channel (direct) results and internal serial capacity

**Question.** How much serial computation fits in a forward pass with no writing?

**Design.** Varied: model, d; direct condition. Channel closure verified by token counts. Measured: accuracy; d_int = deepest d with direct accuracy at least 0.5.

**Result.**

| model | d=1 | d=2 | d=4 | d=8 | d_int | channel verified |
|---|---|---|---|---|---|---|
| Qwen2.5-7B-it | 1.00 | 0.96 | 0.04 | 0.00 | ~2-3 | yes (4 tok) |
| Llama-3.1-8B | 1.00 | 0.47 | 0.00 | 0.00 | ~2 | yes (2-4 tok) |
| Llama-3.3-70B | 1.00 | 1.00 | 0.93 | 0.03 | ~5 | yes (2-4 tok) |
| V3.2 (671B) | 0.23 | 0.03 | 0.00 | 0.00 | ~1 | yes (2 tok) |
| R1 distills | leaked | leaked | leaked | leaked | n/a | no (74-89 percent cap) |

**Interpretation.** Internal serial capacity is real, small, and model-dependent. Whether depth or parameter count sets it is unresolved (collinear within families). Two scope notes stated once here: the R1 distills leak reasoning tokens in direct mode, so their direct cells are excluded; and the ceiling is about chains of unmemorizable random values, since the same V3.2 answers 38 percent of GSM8K directly with one-word outputs (natural-problem structure is partly recomputable and memorizable). This is the same recomputability boundary as Section 3.5.

### 3.3 Corruption and patch results (the read-back mechanism)

**Question.** Are written values read back into the computation, and through what representation?

**Design.** Three levels. Behavioral: corrupt the last written mention of a mid-chain value, continue, see which answer results (gate B). Causal: teacher-forced worked trace, corrupt the value, overwrite the residual at that token with chosen states (clean / arbitrary third value / matched-norm random), continue. Replication anchor: truncation faithfulness reproduced (accuracy monotonic in the fraction of own CoT kept, V3.2 near 0 to 0.97, Sonnet 0.32 to 1.00), and probes validated (answer decodable at R-squared 0.96, control at chance).

**Result.**

| measurement | value |
|---|---|
| gate B flip rate, d=4/8/16/32 (reasoning 7B) | 0.31 / 0.42 / 0.50 / 0.36 |
| patch: corrupt flips answer (Qwen2.5-7B-it, d=10, n=141) | 0.84 |
| patch to clean state, token still corrupt: follows clean | 0.97 [0.94, 0.99]; d=20: 0.93 |
| patch to arbitrary third value: follows that value | 0.76 [0.70, 0.82]; clean 0.00 |
| random-direction patch: follows clean | 0.00 [0.00, 0.01] |
| same on reasoning model (R1-distill-7B): clean / third value | 1.00 / 0.74 [0.66, 0.82] |
| layer-band sweep (early/mid/late) revert | 0.96 / 0.97 / 0.94 |

**Interpretation.** The residual at the written token is a readable value register: set it to any value and the downstream computation reads and propagates that value, which also rules out answer injection (the injected quantity is a mid-chain intermediate the model never wrote). On the reasoning model the random arm is elevated (0.29) because the post-think phase re-solves from the prompt; the third-value condition is immune to that confound (re-solving yields clean, never the injected value). Returns to the clean answer under corruption are re-derivation from the in-context prompt, not evidence of an internal copy; no internal-copy claim is made. The register is carried redundantly across depth (no single-circuit localization claimed). The start-controlled probe adds that the computed part of the answer is not decodable early (0.27 two steps in, 0.83 at the end): the computation emerges as the steps are written.

### 3.4 Reliance on written values across models

**Design.** Varied: model; same behavioral corruption via API prefill. Measured: fraction of answers following the edit.

**Result.**

| model | follows corruption |
|---|---|
| R1-distill-7B (d=8) | 0.42 |
| DeepSeek V3.2, 671B (d=10) | 0.78 |
| Claude Sonnet 4.5 (d=10) | 0.97 |

**Interpretation.** Reliance rises with capability rather than falling; the trace stays load-bearing at the frontier. Observational across architectures, not a causal scale claim.

### 3.5 Recomputability gates read-back

**Design.** Varied: task type at matched corruption protocol. Synthetic chains (intermediate = running total, unrecomputable without re-deriving the chain) vs GSM8K (intermediate = shallow function of the givens). Depth sweep on chains rules out depth as the gate.

**Result.** Chains: flip rate 0.80 / 0.64 / 0.78 / 0.76 / 0.70 at d = 3/5/8/12/16. GSM8K: answer changes 0.10 vs a 0.05 resample floor (deep subset, n=63).

**Interpretation.** Read-back fires when a value cannot be cheaply recomputed from context and not otherwise; the model recomputes shallow intermediates and ignores edits. This bounds the mechanism's footprint (it carries genuinely serial, non-shortcuttable state) and predicts the Part I GSM8K corruption result. Shown by cross-task contrast, not a within-task manipulation.

### 3.6 Token-budget results

**Design.** Varied: hard output budgets 64 to 512 vs unrestricted (V3.2, chains). Measured: trace length, externalization, accuracy; truncation logged separately (0 of 60 wall cells were lucky-match artifacts).

**Result.**

| budget, d=16 | tokens | accuracy | externalization |
|---|---|---|---|
| free | 466 | 1.00 | 1.00 |
| 256 | 184 | 0.93 | 0.98 |
| 128 | 128 (cap) | 0.00 | 0.72 |

**Interpretation.** Prose compresses up to 2.5x; values are never dropped. Below roughly 12 tokens per step the model truncates and fails rather than holding values internally. One caveat: the model is told the cap, so the floor conflates cannot-compress with does-not-plan.

### 3.7 Scratchpad format results

**Design.** Varied: requested format at matched difficulty (prose / running state dump / code without evaluated values / code with values). Measured: accuracy, tokens, externalization.

**Result.**

| format, d=48 | accuracy | tokens |
|---|---|---|
| code with values | 1.00 | 555 |
| prose | 1.00 | 1105 |
| state dump | 0.07 | 3848 |
| code without values | 0.97 | 440 |

Within the no-values code format, per-instance externalization correlates with correctness at +0.74 (accuracy 0.58 when under half the values get written, 1.00 when nearly all do).

**Interpretation.** The payload is the evaluated value, not the operation or the prose; a format that suppresses value-writing fails in proportion to compliance, and over-writing (state dumps) hurts like under-writing. Compact value-carrying scratchpads are both the efficient and the most monitorable external memory.

### 3.8 Serial vs parallel memory demands

**Design.** Varied: task structure (chains vs 5-box tracking) x internal intervention. Behavioral: externalization among correct traces. Causal: residual lesion at matched dose (prefill and decode; neutral-text and on-task KL both reported since neither is clean alone), and the J-space version on chains (below).

**Result.** Boxes: correct at 16 swaps while writing about 0.2 of the state; externalization does not discriminate correct from wrong (0.20 vs 0.17). Chains: 1.00 among correct. Lesion accuracy drops where both families have headroom (d=2 to 4): boxes 0.34 (target) / 0.33 (control window), chains 0.11 / 0.04.

**Interpretation.** Serial state lives on the page; parallel state can live in activations, and the task holding state internally is about 3x more fragile to internal damage. The lesion is blunt (it also damages re-reading of written values, visible at d=8 where chains drop 0.38), so the family comparison is only clean at low-to-mid d.

### 3.9 J-space instruments on the synthetic tasks

**Design.** Calibration on neutral text with the frozen rule; ablation = project out preimages of the top-k active lens concepts at a mid-layer band, all positions; random orthonormal subspace at identical (k, alpha) as control.

**Result.** Qwen2.5-7B-it frozen dose k=16, alpha=0.5 (perplexity ratio 1.12, top-1 agreement 0.87, KL 0.196; random arm at the same dose is more damaging on neutral text, 1.29 / 0.27). Partial 2x2 on chains (clean and jlens arms complete, random arm 60 percent): at this dose neither the direct nor the cot channel moves (clean vs jlens within noise at every d), and cot externalization stays at ceiling under the squeeze.

**Interpretation.** At a dose that provably spares neutral-text behavior, ablating the top of J-space moves nothing on these tasks, and induced scarcity does not induce writing (consistent with the earlier lesion-based null, now with a targeted instrument). Two readings compete: the write policy is not load-sensitive at inference time, or arithmetic state is carried outside the top-k lens concepts. The Part I 2x2 on GSM8K and the planned dose escalation discriminate these.

## 4. Related work

Expressivity theory says fixed-depth transformers are limited to parallel computation in one pass and that CoT length buys serial power (Merrill and Sabharwal 2023, 2024; Li et al. 2024; Feng et al. 2023); it predicts our behavioral results and motivates the mechanism work, which it does not describe. Faithfulness work (Turpin 2023; Lanham 2023; Bentham 2024) and the 2025-26 activations-carry-state wave (2603.05488, 2603.01437, 2604.18307, 2606.13603) establish the correlational premise we build on. The two nearest papers stop short of the causal test: 2604.15726 calls for the token-corruption experiment it never runs; 2605.30343 engineers latent memory blocks but never manipulates capacity or measures read-back. The J-space construct and lens are from Gurnee et al. 2026.

## 5. Negative results and withdrawn claims

Each stated once, with its result.

- No externalization onset exists to fit a scaling law to; the planned onset-law phase became the d_int table of 3.2, where depth vs parameters is unresolved (collinear).
- Damaging the workspace does not induce writing (lesion past the cliff: externalization falls; J-space ablation at the frozen dose: no change).
- Restricting the token channel does not induce internalization (3.6).
- GSM8K read-back is null for recomputability reasons (3.5); the DAG de-circularization task was uninformative (all node labels in the prompt); mod-97 was benched by its matcher false-positive rate.
- Withdrawn on review: a claimed verification regime and a persistent-internal-copy reading (both explained by re-derivation from the in-context prompt); an early-decodability claim (start-value confound, corrected by the start-controlled probe).
- The original protection attempt was invalid as first coded (the lesion fired only on decode, so the direct condition was barely lesioned); fixed version reported in 3.8, J-space version in Part I.

## 6. Limitations

Recomputability bounds the read-back mechanism's footprint (3.5). Synthetic tasks trade ecological validity for exact ground truth. White-box causal results are on 4B to 7B models; frontier evidence is behavioral. The lesion cannot cleanly separate workspace damage from read-back damage. The patch overwrites the whole residual at a position; value-specificity is shown by the third-value swap, not by isolating the value subspace (the J-space patch decomposition is planned). Single seeds on some causal cells; ns are stated per table.

## 7. Reproducibility

Model, dataset, and artifact revisions in Section 1. Dose rules frozen before task runs and stated in 3.9 and 2.2. All cells log cap hits, unparseable answers, and direct-cell token counts. Raw data regenerable from src/harness; figures from src/analysis/figures.py.
