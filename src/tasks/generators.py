"""Task generators for the four difficulty-controlled families.

Every instance carries its ground-truth intermediate values so that probing,
trace matching, and corruption experiments have exact targets. Difficulty is
a scalar (or small tuple) that changes required computation without changing
required output length: the answer is always a single value.
"""

import random
from dataclasses import dataclass, field, asdict


@dataclass
class Instance:
    family: str
    difficulty: int
    seed: int
    prompt: str
    answer: str
    # ordered list of (name, value) for every intermediate the canonical
    # solution computes; used for externalization matching and probe targets
    intermediates: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


def mod_arithmetic(depth, seed, modulus=97):
    """Chain of k operations mod p. Serial depth knob: depth."""
    rng = random.Random(seed)
    ops = []
    val = rng.randrange(modulus)
    start = val
    inters = []
    for i in range(depth):
        op = rng.choice(["+", "-", "*"])
        arg = rng.randrange(2, modulus)
        if op == "+":
            val = (val + arg) % modulus
        elif op == "-":
            val = (val - arg) % modulus
        else:
            val = (val * arg) % modulus
        ops.append(f"{op} {arg}")
        inters.append((f"step_{i+1}", str(val)))
    expr = f"{start} " + " ".join(ops)
    prompt = (
        f"Compute ({expr}) mod {modulus}. "
        f"Apply the operations left to right, reducing mod {modulus} after each step."
    )
    return Instance("mod_arithmetic", depth, seed, prompt, str(val), inters,
                    {"modulus": modulus, "start": start})


def variable_chain(depth, seed, n_distractors=0, lo=1, hi=9):
    """LEGO-style chain: a=5; b=a+2; ... query the last variable.

    depth = chain length (serial knob). n_distractors adds independent
    variables that are never queried (parallel-load knob, varied separately).
    """
    rng = random.Random(seed)
    names = _var_names(rng, depth + n_distractors)
    chain_names = names[:depth]
    lines = []
    inters = []
    val = rng.randint(lo, hi)
    lines.append(f"{chain_names[0]} = {val}")
    inters.append((chain_names[0], str(val)))
    for i in range(1, depth):
        op = rng.choice(["+", "-"])
        arg = rng.randint(lo, hi)
        val = val + arg if op == "+" else val - arg
        lines.append(f"{chain_names[i]} = {chain_names[i-1]} {op} {arg}")
        inters.append((chain_names[i], str(val)))
    # distractors: short independent assignments interleaved at random slots
    for name in names[depth:]:
        lines.insert(rng.randrange(len(lines) + 1), f"{name} = {rng.randint(lo, hi)}")
    prompt = "Given these assignments:\n" + "\n".join(lines) + \
             f"\nWhat is the value of {chain_names[-1]}?"
    return Instance("variable_chain", depth, seed, prompt, str(val), inters,
                    {"n_distractors": n_distractors, "query": chain_names[-1]})


def entity_tracking(n_boxes, n_moves, seed):
    """n boxes with objects, m swap/move operations, query one box.

    Parallel-storage knob: n_boxes. Serial knob: n_moves. Difficulty
    reported as n_moves; n_boxes kept in meta.
    """
    rng = random.Random(seed)
    objects = rng.sample(_OBJECTS, n_boxes)
    boxes = {i: objects[i] for i in range(n_boxes)}
    lines = [f"Box {i+1} contains the {boxes[i]}." for i in range(n_boxes)]
    inters = []
    for step in range(n_moves):
        a, b = rng.sample(range(n_boxes), 2)
        boxes[a], boxes[b] = boxes[b], boxes[a]
        lines.append(f"Swap the contents of Box {a+1} and Box {b+1}.")
        state = ", ".join(f"box{i+1}={boxes[i]}" for i in range(n_boxes))
        inters.append((f"state_after_{step+1}", state))
    q = rng.randrange(n_boxes)
    prompt = "\n".join(lines) + f"\nWhat is in Box {q+1} at the end?"
    return Instance("entity_tracking", n_moves, seed, prompt, boxes[q], inters,
                    {"n_boxes": n_boxes, "query_box": q + 1})


def dag_reachability(hops, seed, width=3, n_noise_edges=6):
    """k-hop reachability on a layered DAG. One true path of length `hops`
    from source to target; noise edges never create a shorter route."""
    rng = random.Random(seed)
    layers = [[f"N{l}{w}" for w in range(width)] for l in range(hops + 1)]
    path = [rng.choice(layer) for layer in layers]
    edges = set(zip(path, path[1:]))
    # noise edges within adjacent layers, avoiding alternative full paths:
    # any noise edge must not start on the true path
    tries = 0
    while len(edges) < hops + n_noise_edges and tries < 200:
        tries += 1
        l = rng.randrange(hops)
        a, b = rng.choice(layers[l]), rng.choice(layers[l + 1])
        if a not in path and (a, b) not in edges:
            edges.add((a, b))
    edge_list = sorted(edges)
    rng.shuffle(edge_list)
    inters = [(f"hop_{i+1}", node) for i, node in enumerate(path[1:])]
    prompt = ("A directed graph has edges: " +
              ", ".join(f"{a}->{b}" for a, b in edge_list) +
              f". Starting from {path[0]} and following edges, "
              f"which node do you reach after exactly {hops} steps "
              f"if you stay on the path leading to a node in the final layer?")
    return Instance("dag_reachability", hops, seed, prompt, path[-1], inters,
                    {"width": width, "path": path})


def _var_names(rng, n):
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    if n <= 26:
        return rng.sample(alphabet, n)
    names = [a + b for a in alphabet for b in alphabet]
    return rng.sample(names, n)


_OBJECTS = [
    "apple", "book", "candle", "doll", "envelope", "feather", "glove",
    "hammer", "ink", "jar", "key", "lamp", "mirror", "needle", "orange",
    "pencil", "quilt", "ribbon", "spoon", "ticket", "umbrella", "vase",
    "whistle", "yarn", "zipper", "coin", "dice", "eraser", "fork", "guitar",
]

FAMILIES = {
    "mod_arithmetic": mod_arithmetic,
    "variable_chain": variable_chain,
    "entity_tracking": lambda d, seed: entity_tracking(5, d, seed),
    "dag_reachability": dag_reachability,
}
