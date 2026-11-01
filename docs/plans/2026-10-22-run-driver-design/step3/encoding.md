Round-0 task files read: 1,236 (44,101 blocks, 36 per section); answer entries read: 44,101.

## Task (input) per section, three encodings

| Encoding | Bytes per section | Estimated tokens per section | Share of A |
|---|---|---|---|
| A: current indented JSON file, read with the Read tool | 12,967 | 4,135 | 100% |
| B: compact JSON, one line per block, short keys, inline in the prompt | 10,591 | 3,079 | 82% |
| C: tab-separated lines, inline in the prompt | 9,936 | 2,888 | 77% |

## Answer (output) per section, two encodings

| Encoding | Bytes per section | Estimated tokens per section | Share of A |
|---|---|---|---|
| A: current JSON, i, label, n, conf, note on every entry | 2,429 | 1,264 | 100% |
| B: compact JSON, i and l always; n only on numbered labels; c and note only on low confidence, drop and unknown | 1,230 | 698 | 51% |

Notes on high-confidence entries that encoding B drops: 5,149 (they explain a label the checks accept, such as 'opens with (1) on the same line'); notes kept: 914.

The token estimate applies the measured bytes-per-token rate of the current encoding to the leaner ones. The bytes removed are mostly ASCII scaffolding (keys, indentation, line numbers), which the tokenizer packs less densely than it packs the Bulgarian text, so the token share saved is at least the byte share shown.
