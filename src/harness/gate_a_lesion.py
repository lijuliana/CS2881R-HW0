"""Gate A: does the write policy respond to internal capacity pressure online?

Crudest squeeze from plan.md: during generation, interpolate the hidden state
at a window of layers toward hidden states resampled from other instances of
the same family at the same layer (resample-style, stays on-distribution),
applied only at generated (reasoning) positions. Compare against a
different, randomly placed layer window at the same dose, and against no
intervention. The only question at gate stage: does externalization fraction
move under the targeted window relative to the random window at matched
damage (accuracy drop / mean KL)?

Plain transformers generation with forward hooks; slow but the gate needs
only ~200 instances x 3 arms.
"""

import argparse
import json
import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tasks.generators import FAMILIES  # noqa: E402
from analysis.externalization import externalization_record  # noqa: E402
from harness.generate import build_prompt, extract_answer, prompt_values  # noqa: E402


class WindowLesion:
    """Forward hooks on a window of decoder layers. At each generation step,
    blends the layer output toward a resample bank vector: h <- (1-a)h + a r.
    Only positions past the prompt are touched."""

    def __init__(self, model, layers, alpha, bank):
        self.model = model
        self.layers = layers
        self.alpha = alpha
        self.bank = bank  # dict layer -> tensor [n_bank, d]
        self.prompt_len = None
        self.handles = []
        self.enabled = False

    def __enter__(self):
        for li in self.layers:
            layer = self.model.model.layers[li]
            self.handles.append(
                layer.register_forward_hook(self._make_hook(li)))
        return self

    def _make_hook(self, li):
        def hook(module, inputs, output):
            if not self.enabled:
                return output
            hs = output[0] if isinstance(output, tuple) else output
            # during decode, seq len 1: everything past prompt is reasoning
            if hs.shape[1] == 1:
                r = self.bank[li][torch.randint(len(self.bank[li]), (hs.shape[0],))]
                r = r.to(hs.dtype).to(hs.device).unsqueeze(1)
                mixed = (1 - self.alpha) * hs + self.alpha * r
                if isinstance(output, tuple):
                    return (mixed,) + output[1:]
                return mixed
            return output
        return hook

    def __exit__(self, *a):
        for h in self.handles:
            h.remove()


@torch.no_grad()
def build_bank(model, tok, prompts, layers, device, per_prompt=8):
    """Collect residual-stream vectors at the given layers from reasoning
    positions of unrelated instances (prompt-only forward pass, last
    per_prompt positions)."""
    bank = {li: [] for li in layers}
    for p in prompts:
        ids = tok(p, return_tensors="pt").to(device)
        out = model(**ids, output_hidden_states=True)
        for li in layers:
            hs = out.hidden_states[li + 1][0]  # [seq, d]
            bank[li].append(hs[-per_prompt:].float().cpu())
    return {li: torch.cat(v) for li, v in bank.items()}


@torch.no_grad()
def generate_with_lesion(model, tok, prompt, lesion, max_new, device):
    ids = tok(prompt, return_tensors="pt").to(device)
    lesion.enabled = True
    out = model.generate(
        **ids, max_new_tokens=max_new, do_sample=True, temperature=0.6,
        top_p=0.95, pad_token_id=tok.eos_token_id)
    lesion.enabled = False
    return tok.decode(out[0][ids["input_ids"].shape[1]:],
                      skip_special_tokens=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--family", default="variable_chain")
    ap.add_argument("--difficulty", type=int, default=8)
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--alpha", type=float, default=0.35)
    ap.add_argument("--target-layers", default="12-17",
                    help="mid-stack window, inclusive range")
    ap.add_argument("--control-layers", default="4-9",
                    help="random-placement control window, same width")
    ap.add_argument("--max-new", type=int, default=3072)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from transformers import AutoModelForCausalLM, AutoTokenizer

    device = "cuda"
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map=device)
    model.eval()

    def parse_win(s):
        a, b = s.split("-")
        return list(range(int(a), int(b) + 1))

    arms = {
        "clean": None,
        "target": parse_win(args.target_layers),
        "control": parse_win(args.control_layers),
    }
    gen = FAMILIES[args.family]
    insts = [gen(args.difficulty, s) for s in range(args.n)]
    bank_prompts = [build_prompt(gen(args.difficulty, 10_000 + s), "cot",
                                 tok, True) for s in range(16)]
    all_layers = sorted(set(arms["target"] + arms["control"]))
    bank = build_bank(model, tok, bank_prompts, all_layers, device)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        for arm, layers in arms.items():
            for inst in insts:
                prompt = build_prompt(inst, "cot", tok, True)
                if layers is None:
                    lesion = WindowLesion(model, [], 0.0, bank)
                else:
                    lesion = WindowLesion(model, layers, args.alpha, bank)
                with lesion:
                    trace = generate_with_lesion(
                        model, tok, prompt, lesion, args.max_new, device)
                pred = extract_answer(trace, "cot")
                ext = externalization_record(trace, inst.intermediates,
                                             prompt_values(inst))
                f.write(json.dumps({
                    "arm": arm, "alpha": args.alpha if layers else 0.0,
                    "difficulty": args.difficulty, "seed": inst.seed,
                    "correct": pred.strip().lower()
                        == inst.answer.strip().lower(),
                    "trace_tokens": len(tok(trace)["input_ids"]),
                    "ext_frac": ext["externalization_fraction"],
                    "trace": trace[:3000],
                }) + "\n")
                f.flush()
            print(f"arm {arm} done", flush=True)


if __name__ == "__main__":
    main()
