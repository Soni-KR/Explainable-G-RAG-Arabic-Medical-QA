# Empty-Context Dual QA Pilot

This targeted retrieval-only pilot evaluated 10 AHD-reference queries whose
frozen Step 11 context was empty. It reused cached Step 8 outputs, `final_v1`,
the 807,698-record held-out-safe AHD SQLite index, and multilingual E5.

## Results

| Mode | Non-empty | Strong direct | Selected items |
|---|---:|---:|---:|
| Frozen conditional FTS | 0/10 | 0/10 | 0 |
| Question only | 0/10 | 0/10 | 0 |
| Answer only | 3/10 | 0/10 | 5 |
| Dual without scenario | 2/10 | 0/10 | 2 |
| Dual with scenario | 2/10 | 0/10 | 2 |

The dual + scenario reference-answer similarity proxy was 0.8321 over the two
non-empty cases. This is a dataset-reference diagnostic, not independent gold.
Mean CPU latency was about 37.9 seconds per query.

Manual technical inspection found:

- `evalv1_008`: related liver-enlargement evidence, but it did not directly
  answer which tests were required.
- `evalv1_019`: a different pregnancy scenario about fetal movement, not the
  queried shortening of fetal limbs.

## Decision

Do not promote this branch and do not run generation from these contexts. The
full 200-query run was intentionally skipped because the pilot produced no
strong-direct rescue, had poor clinical-scenario precision, and was expensive
on CPU.

No graph data or embeddings were modified. The supplemental graph was not
used. Any future graph-expansion experiment should separately audit and reuse
the scripts under `aziza-trial`; that is outside this retrieval pilot.
