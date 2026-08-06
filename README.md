# J-space and the chain of thought: where reasoning state lives

CS 2881R HW0. The report is `report.pdf` in this directory (source: `paper/main.md`).

We ask where a model keeps intermediate results during multi-step reasoning: in J-space, the internal concept workspace read out by the Jacobian lens, or in the written chain of thought. The assignment core runs on Qwen3-4B across GSM8K, MATH-500, and AIME 2024 (the 30 problems of AIME 2024 I and II, `HuggingFaceH4/aime_2024`), with mechanism experiments on synthetic tasks where every intermediate value has exact ground truth.

## Main findings

- **There is no difficulty threshold where writing switches on.** Models write nearly every intermediate value even on one-step problems, at every scale tested (1.5B to 671B). The planned onset scaling law had nothing to fit.
- **Forbidden from writing, models fail after one or two dependent steps** (verified closed-channel; Llama-70B reaches about five). On Qwen3-4B the same shows as a huge thinking-vs-bare-answer gap on all three benchmarks, and the model increasingly overruns its answer-only budget as problems harden (0.29 of GSM8K attempts to 0.80 of AIME attempts): told not to write, it tries anyway.
- **The written values are causally load-bearing, and the internal state at a written token acts like a memory slot.** Editing one written value flips the final answer; overwriting the internal state at that token makes the answer follow whatever value we write in, including values the model never wrote (0.76 of items), while a same-size random perturbation does nothing.
- **Stronger models follow their written values more, not less** (0.42 at 7B, 0.78 at 671B, 0.97 for Claude Sonnet 4.5), so the trace stays load-bearing at the frontier.
- **Written values only matter when the model cannot recompute them.** The edit test is near its noise floor on GSM8K because those intermediates are one step from the given numbers; on synthetic chains, where values cannot be reconstructed, edits dominate at every depth.
- **A J-space ablation at a dose verified harmless on neutral text changes nothing** on these tasks, in accuracy or in how much the model writes, against a random-directions control at identical dose.
- Under token budgets models shorten wording but never drop values (failure floor near 12 tokens per step); tasks with parallel state (box tracking) live in activations while chained state lives on the page, and an internal lesion hurts the internally-stored task about 3x more.

## Repository structure

- `report.pdf`, `paper/main.md`: the report and its markdown source.
- `notes/`: research process. `findings.md` (assignment-scoped findings summary), `plan.md` (design and part-2 plan), `hypotheses.md` (predictions written before running, with what the opposite result would look like), `results-log.md` (dated lab notebook, includes interim readings later revised), `lit-review.md`.
- `src/tasks/`: synthetic task generators (`generators.py`) with self-tests (`test_generators.py`) and deterministic worked-trace builder (`traces.py`).
- `src/harness/`: experiment code. Prompts and experimental settings are in these files. Key ones: `qwen3_bench.py` (Qwen3-4B benchmark sweep and GSM8K edit test), `jspace_ablate.py` (J-space ablation with neutral-text dose calibration), `jspace_patch.py` (J-space patch decomposition, planned), `readback_patch.py` (residual patch and third-value swap), `gate_b_corruption.py` (trace edits), `protection.py` (residual lesion), `api_sweep.py` / `api_readback.py` / `truncation_faithfulness.py` / `gsm8k_readback.py` (API experiments), `precot_decode.py` (answer decodability probe).
- `src/analysis/`: readouts and figures. `figures.py` regenerates all figures; `q3_readout.py`, `jspace_readout.py`, `readback_patch_readout.py`, `gate_b_readout.py`, `protection_readout.py`, `curves.py`, `capacity_law.py`.
- `results/raw/`: key result files (jsonl, one row per generation or item) for every table in the report. `results/figures/`: generated figures. `results/*.csv`: summary tables.
- `experiments/`: one directory per experiment with the exact command and result summary.
- `data/` (gitignored, fetched by instructions below): GSM8K, MATH-500, AIME 2024 local copies.

## Setup

```
python3 -m venv .venv && .venv/bin/pip install vllm transformers accelerate torch numpy pandas matplotlib huggingface_hub boto3
git clone https://github.com/anthropics/jacobian-lens && pip install -e jacobian-lens   # lens library
```

GPU experiments ran on single NVIDIA A10G/L40S instances (24-48 GB). API experiments used AWS Bedrock (DeepSeek V3.2, R1-671B, Llama 3.x) and the Anthropic API (Claude Sonnet 4.5); set credentials in the environment or `.env`.

Datasets:

```
curl -sL https://raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data/test.jsonl -o data/gsm8k_test.jsonl
python -c "from huggingface_hub import hf_hub_download; hf_hub_download('HuggingFaceH4/MATH-500','test.jsonl',repo_type='dataset',revision='6e4ed1a2a79a',local_dir='data')"
# AIME 2024: HuggingFaceH4/aime_2024 revision 2fe88a2f1091, converted to data/aime2024.jsonl (see src/harness/qwen3_bench.py header)
```

Pinned revisions (models, lens, datasets) are listed in the report's Reproducibility section.

## Reproducing the principal tables and figures

Assignment core (Qwen3-4B):

```
python src/harness/qwen3_bench.py --mode sweep --out results/raw/q3_sweep.jsonl        # benchmark ladder table
python src/harness/qwen3_bench.py --mode readback --out results/raw/q3_readback.jsonl  # GSM8K edit test
python src/harness/jspace_ablate.py --model Qwen/Qwen3-4B --calibrate --out results/raw/q3_jcal.jsonl
python src/harness/jspace_ablate.py --model Qwen/Qwen3-4B --family gsm8k --k <K> --alpha <A> --out results/raw/q3_jspace_2x2.jsonl
python src/analysis/q3_readout.py --sweep results/raw/q3_sweep.jsonl --readback results/raw/q3_readback.jsonl
python src/analysis/jspace_readout.py results/raw/q3_jspace_2x2.jsonl
```

Mechanism experiments (tables in the report, in order of appearance): closed-channel table from `src/harness/generate.py` + `api_sweep.py` outputs via `src/analysis/curves.py` and `capacity_law.py`; edit/patch table from `gate_b_corruption.py` and `readback_patch.py` via `readback_patch_readout.py`; cross-model edit table from `api_readback.py`; budget table from `api_sweep.py --conditions budget:N` via `format_readout.py`-style summaries; format table from `format_sweep.py` via `format_readout.py`; lesion comparison from `protection.py` via `protection_readout.py`; J-space calibration and ablation from `jspace_ablate.py` via `jspace_readout.py`.

All figures: `python src/analysis/figures.py` (reads `results/raw/`, writes `results/figures/`).

Report PDF: `pandoc paper/main.md -s --css=<any simple css> -o report.html` then print to PDF (we used headless Chrome).

## External links

- Jacobian lens library: https://github.com/anthropics/jacobian-lens
- Fitted lens artifacts: https://huggingface.co/neuronpedia/jacobian-lens (interactive: https://www.neuronpedia.org/jlens)
- Qwen3-4B: https://huggingface.co/Qwen/Qwen3-4B
- GSM8K: https://github.com/openai/grade-school-math
- MATH-500: https://huggingface.co/datasets/HuggingFaceH4/MATH-500
- AIME 2024: https://huggingface.co/datasets/HuggingFaceH4/aime_2024
- Qwen2.5-7B-Instruct: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct
- DeepSeek-R1 distills: https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B
