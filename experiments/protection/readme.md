# protection

Question: does CoT shield accuracy against internal lesions, and does it shield serial chains (external storage) more than entity tracking (internal storage)?

Command:
```
python src/harness/protection.py --model <M> --family {entity_tracking,variable_chain} \
  --difficulties 2,4,8,16 --n 80 --alpha <sub-cliff dose> --out ...
```
Arms: clean / target lesion / matched-damage control. Read: `python src/analysis/protection_readout.py <files>`.
