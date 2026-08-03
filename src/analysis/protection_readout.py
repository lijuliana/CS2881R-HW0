"""Read out the protection experiment: for each (family, difficulty),
accuracy in the cot vs direct condition under clean / target-lesion /
control-lesion, and the protection gap (cot minus direct) in each arm.

Differential prediction from the serial/parallel dissociation: internal
lesions should hurt entity tracking (internally stored) more than variable
chains (externally stored), and cot should protect variable chains more
than boxes. The control arm at matched dose separates targeted effect from
generic damage.
"""

import argparse
import json
from collections import defaultdict

import numpy as np


def ci(flags, n_boot=2000, seed=0):
    v = np.asarray(flags, dtype=float)
    if len(v) == 0:
        return (float("nan"), float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    m = rng.choice(v, (n_boot, len(v))).mean(axis=1)
    return (v.mean(), *np.percentile(m, [2.5, 97.5]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    args = ap.parse_args()

    rows = []
    for p in args.inputs:
        rows += [json.loads(l) for l in open(p)]

    cells = defaultdict(list)
    kls = {}
    for r in rows:
        cells[(r["arm"], r["difficulty"], r["condition"])].append(r["correct"])
        kls[r["arm"]] = r.get("kl", 0.0)

    arms = ["clean", "target", "control"]
    diffs = sorted({d for _, d, _ in cells})
    print("kl by arm:", {a: round(kls.get(a, 0), 2) for a in arms}, "\n")
    print(f"{'d':>3} {'arm':>8} {'acc_cot':>8} {'acc_dir':>8} "
          f"{'protection':>11}")
    for d in diffs:
        for arm in arms:
            cot = cells.get((arm, d, "cot"), [])
            dr = cells.get((arm, d, "direct"), [])
            if not cot or not dr:
                continue
            pc, pd = np.mean(cot), np.mean(dr)
            print(f"{d:>3} {arm:>8} {pc:>8.2f} {pd:>8.2f} {pc - pd:>11.2f}")
        print()

    # headline: does target lesion collapse cot accuracy less than it should
    # if cot state were internal? compare cot-accuracy drop target vs control
    print("cot accuracy drop from clean, target vs control arm:")
    for d in diffs:
        base = np.mean(cells.get(("clean", d, "cot"), [0]))
        t = np.mean(cells.get(("target", d, "cot"), [0]))
        c = np.mean(cells.get(("control", d, "cot"), [0]))
        print(f"  d={d:>3} clean={base:.2f} target_drop={base - t:+.2f} "
              f"control_drop={base - c:+.2f}")


if __name__ == "__main__":
    main()
