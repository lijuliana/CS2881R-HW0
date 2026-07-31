# internal vs external: how reasoning models allocate computation between latent workspace and written tokens

Research question: when does a reasoning model hold intermediate state in its activations, and when does it write that state into chain-of-thought tokens? Is there a predictable crossover, and what does the mechanism of the handoff look like?

The working hypothesis is that written reasoning functions as the slow tier of a memory hierarchy. The residual stream is a fast, high-bandwidth, but depth-limited workspace. The token stream is slow and low-bandwidth (one discrete token per step) but unbounded and durable. If that picture is right, models should keep intermediate values internal while the serial depth of the problem fits within their layer budget, and start externalizing when it does not. The interesting claims are the causal ones: that written tokens are actually read back (dereferenced) by downstream computation, that internal representations are released after externalization, and that restricting one tier shifts load onto the other.

## repo map

- `notes/lit-review.md` - synthesis of prior work across four areas: latent reasoning, CoT faithfulness and monitorability, interp methods, difficulty scaling. Includes an honest novelty assessment of where this project sits.
- `notes/plan.md` - the full experimental design: phases, controls, evaluation choices, compute plan.
- `notes/predictions.md` - written before running anything. What we expect from each experiment, why, and what the opposite result would look like.
- `src/` - task generators, model harness, probing and patching code (added as phases begin).
- `experiments/` - one directory per experiment, each with a config, a short readme, and analysis.
- `results/` - figures and summary tables. Raw activations stay out of git.

## status

Phase 0 (setup and task families) in progress. See `notes/plan.md` for the phase list.
