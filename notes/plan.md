# experimental plan

Question: when does a reasoning model hold intermediate state in activations vs write it into tokens, what mechanism performs the handoff, and is the crossover predictable?

The memory hierarchy hypothesis, stated so it can fail: the residual stream is a fast workspace whose serial capacity is bounded by depth and whose parallel capacity is bounded by superposition interference; the token stream is a slow, durable store written one discrete symbol at a time. Models allocate intermediate state between the two tiers based on load, write values out when internal capacity is pressured, release the internal copy afterward, and read values back through attention when needed. Each clause of that sentence is a separately testable claim, and several could be false while others hold. The design below tests them separately.

Terminology: "workspace" means the task-relevant subspace of the residual stream at reasoning-time positions, located empirically (phase 2), not assumed.

## models

- primary ladder: DeepSeek-R1-Distill-Qwen 1.5B / 7B / 14B / 32B. Actual reasoning models, one family, four sizes. All white-box work here.
- counterparts: Qwen2.5-Math / Qwen2.5-Instruct at matched sizes, to separate "reasoning-trained" from "big".
- generalization check: Llama-3.1-8B / 70B (and R1-Distill-Llama-8B/70B), second architecture family.
- Gemma-2-9B with Gemma Scope SAEs for cheap feature-level discovery passes, since public SAEs exist.
- API models (Bedrock, Anthropic) for behavioral sweeps only.

## task families

Requirements: a scalar difficulty knob d, difficulty decoupled from required output length, low-d instances solvable with no CoT, intermediate values that are exactly specifiable so probes and corruptions have ground truth.

1. modular arithmetic chains: k operations mod p. d = k.
2. variable chains (LEGO style): a=5; b=a+2; c=b*3; ... query a late variable. d = chain length; distractor variables control parallel load separately from serial depth.
3. entity tracking: n boxes, m moves, query final contents. d = (n, m); this knob stresses parallel storage more than serial depth, deliberately complementary to family 2.
4. k-hop reachability on random DAGs. d = hop count. Theory (log-depth results) makes a quantitative prediction here.

Two knobs on purpose: serial depth (families 1, 2, 4) vs parallel storage load (family 3 and distractor count). The hierarchy hypothesis says both create pressure; the depth-only alternative (running out of layers) says only serial depth does. This is one of the places the design can distinguish hypotheses.

All generators seeded, instance-deduplicated, with held-out difficulty levels for extrapolation tests.

## phase 1: establish the phenomenon (behavioral, cheap, mostly API + small GPU)

For each model and task family, sweep d and measure under three conditions: forced direct answer (no CoT), free generation, forced CoT. Record accuracy, CoT length, and which intermediate values appear verbatim in the trace (exact matching against ground truth, which our synthetic tasks make possible).

Key quantity: the externalization curve, fraction of ground-truth intermediate values written down, as a function of d. The hypothesis predicts a characteristic shape: near zero below some d*, rising afterward, with d* increasing in model size. See predictions.md before any run.

Design point: also measure direct-answer accuracy at each d. If externalization onset simply tracks the point where direct answering fails, that is consistent with the hypothesis, but if models externalize far below that point (as overthinking work suggests) or far above it, the simple cost-benefit story is wrong and we need to say so.

## phase 2: locate the workspace and the write/read operations (white-box, R1-distill 7B and 14B)

2a. probes for intermediate values. Train linear probes for each intermediate value v_i at each layer and token position, with Hewitt-style control tasks (shuffled-label probes) and selectivity reporting. This gives a map of where and when each value is represented internally. Establish the probe baseline before any SAE work; SAEs (Gemma Scope on Gemma-2, Goodfire on R1 if usable) are discovery aids only.

2b. eviction test. Track probe decodability of v_i across the trace timeline. Hypothesis: decodability of v_i at current-position residual streams drops after the token where v_i is written out, relative to matched traces where it is not written out (comparison at equal distance-from-computation, since decay with time alone is the obvious confound). Opposite result is fully visible: decodability persists or rises after writing, which would mean tokens are a broadcast copy, not an eviction target, and the "hierarchy" is really a redundant cache.

2c. read-back test. Corrupt a written intermediate value in the trace (edit the token, continue generation). If downstream computation dereferences external memory, the final answer should track the corrupted value. Then the mechanistic version: attention knockout from later positions to the tokens holding v_i, and path patching to find which heads carry it (receiver-head analysis in the style of thought anchors, at value granularity). Cross-check against internal state: patch the corrupted trace's residual stream with the clean value and see if the answer reverts. The interesting quantitative output is the read-back fraction, how much of the causal effect on the answer flows through the written token vs the internal path, as a function of d. The hypothesis predicts this fraction rises with d. Flat or falling is visible and would refute the load-shifting story.

2d. workspace identification. Use DAS-style interchange interventions to find the subspace carrying v_i at reasoning positions, with the Makelov illusion check. This subspace is what "workspace" means operationally in later phases.

## phase 3: causal capacity interventions (the core contribution)

Two directions, because the hypothesis is about a two-way trade.

3a. squeeze internal, watch external. Interventions of increasing specificity:
   - layer-window lesions at reasoning positions (resample ablation from matched control prompts)
   - workspace-subspace ablation (the phase 2d subspace), dose-controlled by rank and by interpolation strength
   - attention knockout to recent non-CoT context (shrinks effective internal carry)
Measure: CoT length, externalization fraction, read-back fraction, accuracy. Hypothesis predicts a compensatory signature: externalization rises and accuracy partially recovers relative to matched-damage controls.

Controls that separate targeted effect from generic degradation, all reported in every figure:
   - random subspaces of matched rank and norm, same layers, same positions
   - control tasks matched for output format that do not use the workspace content (e.g., copy tasks, single-step lookups); these must stay flat
   - dose-response: effects should scale smoothly with intervention strength; a targeted mechanism gives a different dose curve on task vs control than uniform damage does
   - KL to the clean model on neutral text as a global damage meter; report effect per unit KL
   - the discriminating signature: broad degradation makes everything worse everywhere; a memory hierarchy under pressure makes the model write more and lean on what it wrote. Increased externalization plus increased read-back fraction plus flat controls is not producible by uniform damage, and if we do not see that conjunction we say so.

3b. squeeze external, watch internal. Constrain the token channel: hard token budgets, filler-token replacement of the trace (Pfau-style, separating compute-slots from content), paraphrase rewriting (destroys steganographic content, keeps semantics), structured truncation. Measure internal load: probe decodability of intermediate values at late positions, dimensionality of the phase 2d subspace occupancy. Hypothesis predicts internal representations work harder (more values decodable internally, longer persistence) when writing is blocked, up to a capacity ceiling where accuracy breaks. The filler condition is the sharpest control: if filler tokens rescue performance as well as content tokens, the channel is compute, not memory, and the memory hierarchy framing is wrong for that task.

## phase 4: the onset law

Fit the externalization onset d* (from phase 1 curves, defined by a fixed threshold on externalization fraction, with sensitivity analysis over threshold choice) as a function of model size, layer count, and task family, across the R1-distill ladder plus Llama family. Candidate laws to compare, chosen before fitting: d* linear in depth (serial budget story), d* logarithmic (parallel-scan story, per graph-connectivity theory), d* tracking direct-answer failure point (cost-benefit story). Model comparison by held-out difficulty levels and held-out model sizes, not fit quality alone. Check whether one law spans families or each family gets its own, and whether reasoning-trained models shift d* relative to matched base models (RL moving the write threshold is itself a finding, either direction).

Also look for a mechanistic transition marker near d*: does anything discontinuous happen in the phase 2 maps (probe decodability, read-back fraction, receiver-head attention mass) as d crosses d*, or is the behavioral crossover smooth underneath, Schaeffer-style? Both outcomes are informative and both are visible in the design; claim a phase transition only with a continuous-metric discontinuity, not a thresholded-metric one.

## phase 5: format geometry (time permitting, or as the applied payoff)

Compare scratchpad formats at matched d: free prose, structured state dumps (explicit variable tables), code-like traces. Measure externalization efficiency (accuracy per written token), read-back fraction, and whether the phase 2c receiver circuitry differs by format. The hierarchy view predicts formats that make values easy to address (structured, code-like) raise the effective external capacity and shift d* upward. This is the section with direct design implications: if structured external memory measurably beats prose at equal token cost, that is actionable for reasoning-model training, and it connects to monitorability since a well-used external memory is a readable one.

## evaluation choices

- exact-match on synthetic tasks; no LLM judging anywhere a program can grade
- every causal claim gets: resample ablation primary, zero/mean as robustness, logit-diff and prob metrics both reported
- seeds: 3 minimum per cell for generation-based numbers; probe results with train/val/test splits across instances, never positions of the same instance
- effect sizes with bootstrap CIs over instances; no bare p-values

## compute plan and limitations

- phase 1: mostly API (Bedrock) plus 1x A100/H100 node for open models with vLLM. Cheap.
- phase 2 and 3: the bottleneck. Activation caching and patching on 7B/14B needs 1 to 2 H100s (or A100 80GB); 32B needs 4x for comfortable patching runs. Attribution patching screens first, exact patching on the shortlist.
- 70B Llama runs: 8x A100/H100 node, reserved for the final cross-family check only.
- known limitations to state up front: R1-distills are distilled, not RL-trained from scratch, so RL-specific claims are limited (mitigated partly by the base-model comparison); DAS subspaces are optimization products and inherit the illusion risk even with checks; synthetic tasks trade ecological validity for ground truth, which is the right trade for causal work but caps the generality claims; probing establishes representation, not use, which is why every probe result that matters is paired with a patching result.

## order of operations

Phase 1 starts immediately (behavioral, cheap, and its curves are needed to pick the d ranges for everything else). Phase 2 in parallel on 7B once GPUs are up. Phases 3 and 4 depend on 1 and 2. Phase 5 floats.
