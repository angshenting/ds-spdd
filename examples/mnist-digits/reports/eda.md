# EDA — train split only

Produced by `pipeline/preprocess.py` (canvas O step 2). Validation and test
rows are counted, never inspected.

## Split sizes

train 1257, validation 270, test 270 (stratified by `digit`, seed 42).

## Class balance (train)

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| 124 | 127 | 123 | 128 | 127 | 128 | 127 | 125 | 122 | 126 |

## Mean ink per pixel (train, 0-16 scale)

| c0 | c1 | c2 | c3 | c4 | c5 | c6 | c7 |
|---|---|---|---|---|---|---|---|
| 0.0 | 0.3 | 5.1 | 11.8 | 11.9 | 5.9 | 1.4 | 0.1 |
| 0.0 | 2.0 | 10.4 | 12.0 | 10.3 | 8.3 | 1.9 | 0.1 |
| 0.0 | 2.6 | 10.0 | 7.0 | 7.1 | 7.9 | 1.8 | 0.1 |
| 0.0 | 2.4 | 9.2 | 8.9 | 9.9 | 7.6 | 2.3 | 0.0 |
| 0.0 | 2.3 | 7.6 | 9.1 | 10.3 | 8.8 | 2.9 | 0.0 |
| 0.0 | 1.6 | 6.9 | 7.1 | 7.6 | 8.3 | 3.4 | 0.0 |
| 0.0 | 0.7 | 7.6 | 9.6 | 9.5 | 8.9 | 3.8 | 0.2 |
| 0.0 | 0.3 | 5.5 | 12.1 | 11.8 | 6.8 | 2.1 | 0.4 |

Pixels constant on train: `pixel_0_0`, `pixel_4_0`, `pixel_4_7`. They are
kept: the canvas declares all 64 pixels as features, and a pixel that is the
same in every training image adds nothing to a distance between them.

## Quality rules (canvas E)

All passed on train: `unique` (image_id), `missing_at_most` 0.0 (image_id, digit),
`allowed_values` 0-9 (digit), `range` 0-16 (all 64 pixels).
