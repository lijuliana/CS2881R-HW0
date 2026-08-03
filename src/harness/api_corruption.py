"""Gate-B-style corruption at frontier scale via assistant prefill.

Anthropic models accept a partial assistant turn and continue it, which is
exactly the continuation-after-corruption operation gate B needs.