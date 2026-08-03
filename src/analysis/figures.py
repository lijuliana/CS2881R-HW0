"""Regenerate all paper figures from results/raw. One function per figure,
each self-contained so a figure can be rebuilt when its data changes.
Everything writes to results/figures/."""

import json
import os
from collections import defaultdict

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RAW = "results/raw"
OUT = "results/figures"
os.makedirs(OUT, exist_ok=True)


def load(name):
    path = os.path.join(RAW, name)
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path) if '"error"' not in l]


def _acc_ext_by_d(rows, cond="free"):
    by = defaultdict(lambda: {"acc": [], "ext": []})
    for r in rows:
        if r.get("condition") != cond:
            continue
        by[r["difficulty"]]["acc"].append(r["correct"])
        e = (r.get("externalization") or {}).get("externalization_fraction")
        if e is not None:
            by[r["difficulty"]]["ext"].append(e)
    ds = sorted(by)
    acc = [np.mean(by[d]["acc"]) for d in ds]
    ext = [np.mean(by[d]["ext"]) if by[d]["ext"] else np.nan for d in ds]
    return ds, acc, ext


def fig_necessity():
    """Externalization among correct vs wrong traces, ladder, variable
    chains. The necessity result."""
    fig, ax = plt.subplots(figsize=(6, 4))
    for m, color in [("1.5b", "C0"), ("7b", "C1"), ("14b", "C2")]:
        rows = load(f"p1_var_{m}.jsonl")
        by = defaultdict(lambda: {"ok": [], "bad": []})
        for r in rows:
            if r.get("condition") != "free":
                continue
            e = (r.get("externalization") or {}).get(
                "externalization_fraction")
            if e is None:
                continue
            by[r["difficulty"]]["ok" if r["correct"] else "bad"].append(e)
        ds = sorted(by)
        ok = [np.mean(by[d]["ok"]) if by[d]["ok"] else np.nan for d in ds]
        bad = [np.mean(by[d]["bad"]) if by[d]["bad"] else np.nan for d in ds]
        ax.plot(ds, ok, "-o", color=color, label=f"{m} correct")
        ax.plot(ds, bad, "--x", color=color, alpha=0.6,
                label=f"{m} wrong")
    ax.set_xlabel("chain depth d")
    ax.set_ylabel("externalization fraction")
    ax.set_title("complete externalization is necessary for correct "
                 "deep chains")
    ax.set_xscale("log", base=2)
    ax.legend(fontsize=7, ncol=3)
    fig.tight_layout()
    fig.savefig(f"{OUT}/necessity.png", dpi=150)
    plt.close(fig)


def fig_readback():
    """Gate B corruption-following vs difficulty, variable chains."""
    rows = load("gate_b_var_7b.jsonl")
    by = defaultdict(lambda: {"corr": [], "clean": [], "restate": []})
    for r in rows:
        by[r["difficulty"]]["corr"].append(r["follows_corruption"])
        by[r["difficulty"]]["clean"].append(r["follows_clean"])
        by[r["difficulty"]]["restate"].append(r["restates_clean_early"])
    ds = sorted(by)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(ds, [np.mean(by[d]["corr"]) for d in ds], "-o",
            label="follows corruption (read-back)")
    ax.plot(ds, [np.mean(by[d]["clean"]) for d in ds], "-s",
            label="follows clean (internal copy)")
    ax.plot(ds, [np.mean(by[d]["restate"]) for d in ds], "--^",
            label="restates clean early (verification)")
    ax.set_xlabel("chain depth d")
    ax.set_ylabel("fraction of corrupted continuations")
    ax.set_title("written values are read back, internal copy verifies")
    ax.set_xscale("log", base=2)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(f"{OUT}/readback.png", dpi=150)
    plt.close(fig)


def fig_budget():
    """Budget sweep: accuracy and externalization vs budget, by difficulty."""
    rows = load("budget_var_v32.jsonl")
    by = defaultdict(lambda: {"acc": [], "ext": []})
    for r in rows:
        c = r.get("condition", "")
        b = int(c.split(":")[1]) if c.startswith("budget") else 9999
        by[(b, r["difficulty"])]["acc"].append(r["correct"])
        e = (r.get("externalization") or {}).get("externalization_fraction")
        if e is not None:
            by[(b, r["difficulty"])]["ext"].append(e)
    budgets = sorted({b for b, _ in by})
    diffs = sorted({d for _, d in by})
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for d in diffs:
        acc = [np.mean(by[(b, d)]["acc"]) if by[(b, d)]["acc"] else np.nan
               for b in budgets]
        ext = [np.mean(by[(b, d)]["ext"]) if by[(b, d)]["ext"] else np.nan
               for b in budgets]
        axes[0].plot(budgets, acc, "-o", label=f"d={d}")
        axes[1].plot(budgets, ext, "-o", label=f"d={d}")
    for ax, t in zip(axes, ["accuracy", "externalization fraction"]):
        ax.set_xlabel("token budget")
        ax.set_ylabel(t)
        ax.set_xscale("log", base=2)
        ax.legend(fontsize=8)
    axes[0].set_title("prose compresses, values do not")
    fig.tight_layout()
    fig.savefig(f"{OUT}/budget.png", dpi=150)
    plt.close(fig)


def fig_format():
    """Accuracy per token by format, variable chains. Efficient value-store
    (code_eval) vs prose vs verbose (state) vs value-suppressed (code)."""
    import json as _json
    rows = [_json.loads(l) for l in open(f"{RAW}/format_var_v32.jsonl")
            if '"error"' not in l]
    from collections import defaultdict as _dd
    by = _dd(lambda: _dd(list))
    for r in rows:
        by[r["format"]][r["difficulty"]].append(r)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for fmt in ["code_eval", "prose", "state", "code"]:
        ds = sorted(by[fmt])
        acc = [np.mean([r["correct"] for r in by[fmt][d]]) for d in ds]
        eff = [100 * np.mean([r["correct"] for r in by[fmt][d]])
               / np.mean([r["trace_tokens"] for r in by[fmt][d]]) for d in ds]
        axes[0].plot(ds, acc, "-o", label=fmt)
        axes[1].plot(ds, eff, "-o", label=fmt)
    axes[0].set_ylabel("accuracy")
    axes[1].set_ylabel("accuracy per 100 tokens")
    for ax in axes:
        ax.set_xlabel("chain depth d")
        ax.set_xscale("log", base=2)
        ax.legend(fontsize=8)
    axes[0].set_title("compact value store is the efficient scratchpad")
    fig.tight_layout()
    fig.savefig(f"{OUT}/format.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    for fn in [fig_necessity, fig_readback, fig_budget, fig_format]:
        try:
            fn()
            print(f"{fn.__name__} ok")
        except Exception as e:
            print(f"{fn.__name__} FAILED: {e}")
