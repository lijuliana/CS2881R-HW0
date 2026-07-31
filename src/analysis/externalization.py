"""Detect which ground-truth intermediate values appear in a reasoning trace.

Exact match with a normalization layer is the primary (surface) detector.
The causal definition (corrupt the written value, see if the answer moves)
lives in the intervention code; this module also emits the token spans the
corruption code needs.
"""

import re

_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20,
}


def normalize_number(s):
    s = s.strip().lower().replace(",", "")
    if s in _WORDS:
        return str(_WORDS[s])
    m = re.fullmatch(r"-?\d+(\.0+)?", s)
    if m:
        return str(int(float(s)))
    return s


def find_value_mentions(trace, value):
    """Return character spans in `trace` where `value` appears as a
    standalone numeric (or object-name) mention. Word-boundary matching so
    that 4 does not fire inside 42."""
    val = normalize_number(str(value))
    spans = []
    if re.fullmatch(r"-?\d+", val):
        # match the number, tolerating a leading minus already consumed
        # a trailing dot only disqualifies when it starts a decimal (19.5),
        # not when it ends a sentence (19.)
        pat = re.compile(r"(?<![\d\w-])(?<!\d\.)" + re.escape(val)
                         + r"(?!\d|\.\d|\w)")
    else:
        pat = re.compile(r"\b" + re.escape(str(value)) + r"\b", re.IGNORECASE)
    for m in pat.finditer(trace):
        spans.append((m.start(), m.end()))
    return spans


def externalization_record(trace, intermediates, prompt_values=None):
    """For each (name, value) intermediate, report whether it is written in
    the trace and where.

    prompt_values: values appearing in the prompt itself; a mention equal to
    a prompt value is ambiguous (could be a copy, not a computed result), so
    those intermediates are flagged and excluded from the clean fraction.
    """
    prompt_values = {normalize_number(str(v)) for v in (prompt_values or [])}
    records = []
    for name, value in intermediates:
        spans = find_value_mentions(trace, value)
        ambiguous = normalize_number(str(value)) in prompt_values
        records.append({
            "name": name,
            "value": str(value),
            "written": bool(spans),
            "spans": spans,
            "ambiguous": ambiguous,
        })
    clean = [r for r in records if not r["ambiguous"]]
    frac = (sum(r["written"] for r in clean) / len(clean)) if clean else None
    return {"records": records, "externalization_fraction": frac,
            "n_clean": len(clean)}
