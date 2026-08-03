"""Isolate token read-back from internal recomputation.

Gate B alone cannot tell whether a corrupted written value changes the
answer because the model dereferenced the token or because it recomputed
and got perturbed. This experiment decomposes the effect with a residual
patch.

Setup, per instance (variable chain, teacher-forced worked trace):
  clean trace       : ... v_i = a op b = V ...      (correct value V)
  corrupted trace   : ... v_i = a op b = V'...       (V' = V + delta)
We continue generation from each and read the final answer. Then the key
condition:
  patched trace     : run the corrupted trace, but at the residual stream of
                      every position at and after the corrupted value token,
                      add (clean_state - corrupt_state) captured from the
                      clean run at matched positions, at a chosen layer band.
                      This restores the internal representation to its clean
                      value while leaving the visible token corrupted.

Logic:
  - if the answer is carried by the written token, the patched run (clean
    internal state, corrupt token) still follows the corruption.
  - if the answer is carried by internal state, the patched run reverts to
    the clean answer.
  - the fraction reverting is the internal-path share; one minus it, among
    items that followed the corruption in the plain corrupted run, is the
    token-path (read-back) share.

Controls:
  - patch magnitude control: add a random-direction vector of matched norm
    at the same positions/layers; should not revert (guards against "any
    perturbation reverts").
  - only analyze items where the plain corrupted run followed the
    corruption (so there is an effect to decompose).
Multiple continuation samples per item for a per-item revert probability.
"""

import argparse
import json
import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tasks.generators import variable_chain  # noqa: E402
from harness.generate import build_prompt, extract_answer  # noqa: E402
from harness.eviction_probe import build_trace  # reuse worked-trace builder


def value_token_positions(tok, full_ids, prompt_ids_len, value_str):
    """Token indices whose decoded text contains the target value digits,
    searching only past the prompt. Returns the last such run (the written
    mention we corrupted is the last one before continuation)."""
    matches = []
    for i in range(prompt_ids_len, len(full_ids)):
        piece = tok.decode(full_ids[i:i + 3])
        if value_str in piece:
            matches.append(i)
    return matches


class ResidualPatch:
    """Adds a per-position delta to residual stream at a layer band, for
    positions >= start_pos. Deltas indexed by absolute position."""

    def __init__(self, model, layers, deltas, start_pos):
        self.model = model
        self.layers = layers
        self.deltas = deltas  # dict layer -> tensor [seq, d] (clean-corrupt)
        self.start_pos = start_pos
        self.handles = []
        self.enabled = False

    def __enter__(self):
        for li in self.layers:
            layer = self.model.model.layers[li]
            self.handles.append(layer.register_forward_hook(self._hook(li)))
        return self

    def _hook(self, li):
        def hook(module, inputs, output):
            if not self.enabled:
                return output
            hs = output[0] if isinstance(output, tuple) else output
            seq = hs.shape[1]
            if seq == 1:
                return output  # decode steps past the patched region
            d = self.deltas.get(li)
            if d is None:
                return output
            add = torch.zeros_like(hs[0])
            n = min(seq, d.shape[0])
            add[:n] = d[:n].to(hs.dtype).to(hs.device)
            add[:self.start_pos] = 0
            hs = hs + add.unsqueeze(0)
            if isinstance(output, tuple):
                return (hs,) + output[1:]
            return hs
        return hook

    def __exit__(self, *a):
        for h in self.handles:
            h.remove()


@torch.no_grad()
def capture_states(model, ids, layers):
    out = model(ids, output_hidden_states=True)
    return {li: out.hidden_states[li + 1][0].float().cpu() for li in layers}


@torch.no_grad()
def continue_from(model, tok, ids, patch, max_new, n_samples):
    answers = []
    for _ in range(n_samples):
        if patch is not None:
            patch.enabled = True
        out = model.generate(ids, max_new_tokens=max_new, do_sample=True,
                             temperature=0.6, top_p=0.95,
                             pad_token_id=tok.eos_token_id)
        if patch is not None:
            patch.enabled = False
        txt = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)
        answers.append(extract_answer(txt, "cot"))
    return answers


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--depth", type=int, default=10)
    ap.add_argument("--n", type=int, default=120)
    ap.add_argument("--samples", type=int, default=5)
    ap.add_argument("--layers", default="10-19",
                    help="residual band to patch, inclusive")
    ap.add_argument("--delta", type=int, default=40)
    ap.add_argument("--max-new", type=int, default=400)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from transformers import AutoModelForCausalLM, AutoTokenizer

    device = "cuda"
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, dtype=torch.bfloat16, device_map=device)
    model.eval()
    a, b = args.layers.split("-")
    layers = list(range(int(a), int(b) + 1))

    def forward_answer(inst, idx, val):
        v = val
        for op, arg in inst.meta["ops"][idx:]:
            v = v + arg if op == "+" else v - arg
        return str(v)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    out = open(args.out, "w")
    kept = 0
    for s in range(args.n):
        inst = variable_chain(args.depth, 60_000 + s)
        tgt = len(inst.meta["ops"]) // 2
        clean_val = int(inst.intermediates[tgt + 1][1])
        corr_val = clean_val + args.delta
        # clean answer forward from the target intermediate
        clean_ans = forward_answer(inst, tgt + 1, clean_val)
        corr_ans = forward_answer(inst, tgt + 1, corr_val)
        if clean_ans == corr_ans:
            continue

        prompt = build_prompt(inst, "cot", tok, True)
        text, ends, _ = build_trace(inst, write_target=True)
        # locate and overwrite the target value's last written mention
        cut_char = ends[tgt]  # end of target step line
        prefix = text[:cut_char]
        clean_prefix_text = prompt + "\n" + prefix
        corr_prefix_text = clean_prefix_text.replace(
            f"= {clean_val}.", f"= {corr_val}.")
        if corr_prefix_text == clean_prefix_text:
            continue

        clean_ids = tok(clean_prefix_text, return_tensors="pt").to(device)
        corr_ids = tok(corr_prefix_text, return_tensors="pt").to(device)
        if clean_ids.input_ids.shape[1] != corr_ids.input_ids.shape[1]:
            continue  # keep alignment simple: same token length only

        plen = tok(prompt + "\n", return_tensors="pt").input_ids.shape[1]
        cs = capture_states(model, clean_ids.input_ids, layers)
        xs = capture_states(model, corr_ids.input_ids, layers)
        # patch positions: from the target value token onward
        vpos = value_token_positions(
            tok, corr_ids.input_ids[0].tolist(), plen, str(corr_val))
        start = vpos[-1] if vpos else plen
        deltas = {li: (cs[li] - xs[li]) for li in layers}
        rand = {li: torch.randn_like(cs[li]) for li in layers}
        for li in layers:  # match random norm to the true delta per position
            dn = deltas[li].norm(dim=-1, keepdim=True)
            rn = rand[li].norm(dim=-1, keepdim=True) + 1e-6
            rand[li] = rand[li] / rn * dn

        base_patch = ResidualPatch(model, layers, deltas, start)
        rand_patch = ResidualPatch(model, layers, rand, start)

        corr_ans_gen = continue_from(model, tok, corr_ids.input_ids, None,
                                     args.max_new, args.samples)
        with base_patch:
            patched = continue_from(model, tok, corr_ids.input_ids,
                                    base_patch, args.max_new, args.samples)
        with rand_patch:
            randed = continue_from(model, tok, corr_ids.input_ids,
                                   rand_patch, args.max_new, args.samples)

        def frac(ans_list, target):
            return sum(a == target for a in ans_list) / len(ans_list)

        out.write(json.dumps({
            "seed": inst.seed, "depth": args.depth, "target_step": tgt,
            "clean_val": clean_val, "corr_val": corr_val,
            "clean_ans": clean_ans, "corr_ans": corr_ans,
            "corr_follows_corruption": frac(corr_ans_gen, corr_ans),
            "corr_follows_clean": frac(corr_ans_gen, clean_ans),
            "patched_follows_clean": frac(patched, clean_ans),
            "patched_follows_corruption": frac(patched, corr_ans),
            "rand_follows_clean": frac(randed, clean_ans),
            "rand_follows_corruption": frac(randed, corr_ans),
        }) + "\n")
        out.flush()
        kept += 1
        if kept % 20 == 0:
            print(f"{kept} items", flush=True)
    out.close()
    print(f"done, {kept} items", flush=True)


if __name__ == "__main__":
    main()
