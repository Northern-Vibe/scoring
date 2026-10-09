# Model Decision Log

Changes to the Northern Vibe simulation model are recorded here in reverse-chronological order.
Parameters are never adjusted retroactively to improve past accuracy figures.

---

## 2026-10-08 — Scoring harness moved to the out-of-sample backtest

**Trigger:** The published headline is the out-of-sample backtest (88.0%), but the harness still reproduced the in-sample check (97.7%), and the site no longer shows the in-sample figure.

**Changes:** `scoring/fixtures/ge45_oos_backtest.json` replaces `ge45_prediction_2025-04-27.json`. It holds every riding's predicted winner from `simulation/backtest_ge45_oos.py` (2021 baseline plus the 2025-04-27 national poll average), and `scoring/evaluate.py` now derives riding call accuracy from those predictions instead of counting a list of misses. The backtest's poll input for 2025-04-27 is now a frozen constant: `poll_aggregate` is recomputed over its whole history when the aggregator changes, and reading it had drifted the result to 300/342 and a 0.78pp vote error. The frozen values reproduce the published 301/342 and 0.87pp.

**What did not change:** The model, and the published out-of-sample figures.

---

## 2026-04-29 — Post-GE45 recalibration

**Trigger:** Elections Canada released the certified GE45 results on April 29, 2026.

**Changes:**

- **`simulation/systematic_error_calibration.json` updated** — RMSE values recomputed against certified GE45 results (Elections Canada official national totals: LPC 43.95%, CPC 41.49%, NDP 6.31%, BQ 6.32%, GPC 1.22%, PPC 0.70%). CPC RMSE confirmed at 2.876pp, reflecting the final-week polling gap. Method: `uv run python -m simulation.calibrate_systematic_error`. Covers 6 elections: GE40, GE41, GE42, GE43, GE44, GE45. Note: `scoring/evaluate.py` computes slightly different national vote shares (e.g. CPC 41.56%) because it excludes Terrebonne (24073), whose result was nullified by the courts. The official EC figures above include all ridings.

- **`vote_transfer_matrix` DB table re-seeded** — 252 riding-level rows regenerated from certified GE45 results using `uv run python -m backend.etl.estimate_transfer_matrix`. Previous entries were based on unofficial night-of tallies.

**What did not change:** Model architecture, simulation parameters, regional correction constants (`_AB_CPC_FLOOR`, `_BC_NDP_INTERCEPT`, `_ATLANTIC_SIGMA_MULTIPLIER`), or PyMC trajectory priors. Only calibration artefacts derived deterministically from certified vote totals were updated.

**Reproducibility:** Run `uv run python -m simulation.calibrate_systematic_error` and `uv run python -m backend.etl.estimate_transfer_matrix` against any database containing the certified GE45 results to reproduce these artefacts identically.

---

## 2026-05-02 — GE45 scoring fixture added (corrected 2026-10-08)

**Correction:** An earlier version of this entry, dated 2025-04-28, said the fixture was committed before polls closed and that its Git timestamp was a pre-registration record. It was not: `scoring/fixtures/ge45_prediction_2025-04-27.json` was first committed on 2026-05-02 (a43b2ba), after the election. It recorded the national poll average as of 2025-04-27 and the in-sample reproduction's seat ranges and missed ridings. It was replaced on 2026-10-08 (above). `docs/snapshot_protocol.md` describes how to lock a snapshot before polls close for future elections.

---

*Future entries: add above this line in reverse-chronological order.*
