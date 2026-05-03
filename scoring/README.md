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
| `fixtures/ge45_prediction_2025-04-27.json` | Frozen model output — predicted national vote shares and seat distributions as of April 27, 2025 (one day before GE45 voting). No model weights or parameters. |
| `data/ge45_certified_results.csv` | Elections Canada certified riding-level results for GE45. Source: [elections.ca](https://www.elections.ca). Terrebonne (fed_code 24073) is excluded — its result was nullified by the courts. |
| `evaluate.py` | Pure Python evaluator. Loads the fixture + the certified CSV and derives MAE, riding call accuracy, 80% seat band coverage, and a missed-riding list. |

## Expected output

```
Northern Vibe — GE45 Scoring Report
Fixture : ge45_prediction_2025-04-27.json
Results : ge45_certified_results.csv
-------------------------------------------------------
Riding call accuracy : 97.7%  (334 / 342)
Vote share MAE       : 0.87pp
80% seat bands hit   : 6 / 6
-------------------------------------------------------

Vote share detail:
  Party   Predicted     Actual     Error
  --------------------------------------
  LPC        43.37%     43.97%  +  0.60pp
  CPC        39.11%     41.56%  +  2.45pp
  NDP         7.65%      6.33%   -1.32pp
  BQ          6.18%      6.22%  +  0.04pp
  GPC         1.45%      1.22%   -0.23pp
  PPC         1.27%      0.70%   -0.57pp

Seat projection detail (80% range = p10–p90):
  Party   Median     80% range  Actual  In range?
  -----------------------------------------------
  LPC        182    156–212            168        YES
  CPC        129    101–155            144        YES
  NDP          8      5–12               7        YES
  BQ          22     17–27              22        YES
  GPC          1      0–2                1        YES
  PPC          0      0–0                0        YES

Missed ridings (model called wrong winner):
  35118  Windsor—Tecumseh—Lakeshore                ON  predicted=LPC
  62001  Nunavut                                   NU  predicted=LPC
  12001  Acadie—Annapolis                          NS  predicted=LPC
  35058  Markham—Unionville                        ON  predicted=LPC
  59020  New Westminster—Burnaby—Maillardville     BC  predicted=NDP
  59010  Cowichan—Malahat—Langford                 BC  predicted=NDP
  48020  Edmonton Riverbend                        AB  predicted=LPC
  59021  North Island—Powell River                 BC  predicted=NDP

All assertions passed.
```

The summary numbers match the `/accuracy` page exactly. Note: vote shares are computed over the 342 eligible ridings — Terrebonne (24073) is excluded because its result was nullified by the courts, so the national percentages differ slightly from Elections Canada's official all-ridings totals.

## Pre-registration note

The fixture file is committed to this repository with a Git timestamp prior to any post-election analysis. The Git commit hash is an unforgeable record that these predictions existed before polls closed on April 28, 2025.

For future elections, see `docs/snapshot_protocol.md` for the procedure to lock a pre-election snapshot.

## Metric definitions

**Vote share MAE** — Mean absolute error across the six tracked parties (LPC, CPC, NDP, BQ, GPC, PPC) between the model's predicted national vote share and the certified result. Lower is better.

**Riding call accuracy** — Fraction of the 342 eligible ridings where the party with the highest simulated win probability matched the certified winner. Terrebonne is excluded (nullified result).

**80% seat bands hit** — Number of parties (out of 6) whose certified seat count fell within the model's p10–p90 seat projection range.
