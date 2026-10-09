# Northern Vibe — Open Scoring Harness

This directory lets anyone independently reproduce the accuracy figures shown on [northernvibe.ca/accuracy](https://northernvibe.ca/accuracy) without installing the simulation model or accessing a database.

## Quick start

```bash
python scoring/evaluate.py
```

No dependencies beyond the Python standard library. No model imports.

## What's in here

| Path | Contents |
|------|----------|
| `fixtures/ge45_oos_backtest.json` | Frozen output of the out-of-sample backtest: each riding's predicted winner, the 2021 winner (the naive baseline), the national poll average the model was given, and the projected seat ranges. No model weights or parameters. |
| `data/ge45_certified_results.csv` | Elections Canada certified riding-level results for GE45. Source: [elections.ca](https://www.elections.ca). Terrebonne (fed_code 24073) is excluded — its result was nullified by the courts. |
| `evaluate.py` | Pure Python evaluator. Compares every predicted winner with the certified winner, and derives riding call accuracy, the naive baseline, vote share MAE, 80% seat band coverage and the list of missed ridings. |

## What the backtest is

The backtest predicts the 2025 (GE45) result in every riding using only what existed before election day: each riding's **2021** result as the baseline, plus the national poll average as of **April 27, 2025**, one day before voting. No 2025 result touches a prediction; the certified results are used only to score the calls.

It is **retrospective**: the model was run after the election, not before. What keeps it honest is the wall between inputs and results, which you can check in `simulation/backtest_ge45_oos.py`, not a pre-election timestamp. The fixture was generated with `python -m simulation.backtest_ge45_oos --export-fixture scoring/fixtures/ge45_oos_backtest.json`.

## Expected output

```
Northern Vibe — GE45 Out-of-Sample Scoring Report
Fixture : ge45_oos_backtest.json
Results : ge45_certified_results.csv
Inputs  : GE44 (2021) riding results + national polls as of 2025-04-27
------------------------------------------------------------
Riding call accuracy   : 88.0%  (301 / 342)
2021 winner holds      : 83.3%  (285 / 342)  [naive baseline]
Vote share MAE         : 0.87pp
80% seat bands hit     : 6 / 6
LPC majority (model)   : 72.6%  (actual: 168 seats)
------------------------------------------------------------
```

It then prints the vote share and seat detail per party and the 41 ridings the model called wrong, and ends with `All assertions passed.` The summary numbers match the `/accuracy` page. Vote shares are computed over the 342 eligible ridings — Terrebonne (24073) is excluded because its result was nullified by the courts, so the national percentages differ slightly from Elections Canada's official all-ridings totals.

## Future elections

For a forecast that can be checked against a pre-election timestamp, see `docs/snapshot_protocol.md` for the procedure to lock a snapshot before polls close.

## Metric definitions

**Riding call accuracy**: Fraction of the 342 eligible ridings where the model's most likely winner matched the certified winner. Terrebonne is excluded (nullified result).

**2021 winner holds**: The same score for a naive baseline that predicts every riding stays with its 2021 winner. The model's skill is its margin over this.

**Vote share MAE**: Mean absolute error across the six tracked parties (LPC, CPC, NDP, BQ, GPC, PPC) between the national poll average the model was given and the certified result. Lower is better.

**80% seat bands hit**: Number of parties (out of 6) whose certified seat count fell within the model's p10–p90 seat projection range.
