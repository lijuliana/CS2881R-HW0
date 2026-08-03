# internal vs external: how reasoning models allocate computation between latent workspace and written tokens

Research question: when does a reasoning model hold intermediate state in its activations, and when does it write that state into chain-of-thought tokens? Is there a predictable crossover, and what does the mechanism of the handoff look like?

The working hypothesis is that written reasoning functions as the slow tier of a memory hierarchy. The residual stream is a fast, high-bandwidth, but depth-limited workspace. The token stream is slow and low-bandwidth (one discrete token per step) but unbounded and durable. If that picture is right, models should keep intermediate values internal while the serial depth of the problem fits within their layer budget, and start externalizing when it does not. The interesting claims are the causal ones: that written tokens are actually read back (dereferenced) by downstream computation, that internal representations are released after externalization, and that restricting one tier shifts load onto the other.

## repo map

- `notes/lit-review.md` - synthesis of prior work across four areas: latent reasoning, CoT faithfulness and monitorability, interp methods, difficulty scaling. Includes an honest novelty assessment of where this project sits.
- `notes/plan.md` - the full experimental design: phases, controls, evaluation choices, compute plan.
- `notes/hypotheses.md` - initial hypotheses, written before running anything: what we expect from each experiment, why, and what the opposite result would look like.
- `notes/results-log.md` - dated, append-only record of findings as they landed.
- `notes/synthesis.md` - the claim, the evidence and what each result rules out, the capacity law, open questions, novelty position. Start here for the argument.
- `src/` - task generators (`tasks/`), model harness (`harness/`), analysis and figures (`analysis/`).
- `experiments/` - one directory per experiment: question, command, result.
- `results/figures/` - figures regenerated from raw by `src/analysis/figures.py`. Raw traces stay out of git.

## finding, in one paragraph

For serial reasoning past a shallow internal-capacity limit, chain-of-thought is not a spillover buffer models reach for under pressure; it is the medium the computation runs in. The residual stream is wide but shallow: it holds many values in parallel but cannot carry a chained result more than about one serial step without writing it down. So models write every intermediate of a serial chain (externalization among correct deep traces is exactly 1.0), read those written values back (corrupting one flips the answer), keep a short-lived internal copy that verifies the written one, and cannot compress the values away under token pressure. Parallel state, by contrast, stays internal. The tier is set by the type of memory demand, serial vs parallel, not its amount, and the one fittable boundary, how deep a chain fits in a single forward pass, tracks model depth rather than parameter count.

## status

Behavioral phases and two of three causal phases done. Gate A (capacity lesions), eviction probe, protection experiment, and the depth-ladder capacity fit running. See `notes/synthesis.md` for the current argument and `notes/results-log.md` for dated results.
