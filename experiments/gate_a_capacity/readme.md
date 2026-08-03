# does internal pressure change writing

Question: lesion a mid-stack layer window during generation (resample ablation), vs a matched-damage control window. Does externalization move?

Command:
```
python src/harness/gate_a_lesion.py --model <M> --family variable_chain --difficulty 8 \
  --n 150 --alphas <doses> --target-layers 12-17 --control-layers 4-9 --out ...
```
KL to the clean model is logged per arm as the damage meter. Coarse doses overshot the accuracy cliff; a fine low-dose sweep resolves the sub-cliff regime.

Read: arm x dose table of acc / ext / kl.
