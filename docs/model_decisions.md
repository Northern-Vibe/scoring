# Model Decision Log

Changes to the Northern Vibe simulation model are recorded here in reverse-chronological order.
Parameters are never adjusted retroactively to improve past accuracy figures.

---

## 2026-04-29 — Post-GE45 recalibration

**Trigger:** Elections Canada released the certified GE45 results on April 29, 2026.

**Changes:**

- **`simulation/systematic_error_calibration.json` updated** — RMSE values recomputed against certified GE45 results (Elections Canada official national totals: LPC 43.95%, CPC 41.49%, NDP 6.31%, BQ 6.32%, GPC 1.22%, PPC 0.70%). CPC RMSE confirmed at 2.876pp, reflecting the final-week polling gap. Method: `uv run python -m simulation.calibrate_systematic_error`. Covers 6 elections: GE40, GE41, GE42, GE43, GE44, GE45. Note: `scoring/evaluate.py` computes slightly different national vote shares (e.g. CPC 41.56%) because it excludes Terrebonne (24073), whose result was nullified by the courts. The official EC figures above include all ridings.

- **`vote_transfer_matrix` DB table re-seeded** — 252 riding-level rows regenerated from certified GE45 results using `uv run python -m backend.etl.estimate_transfer_matrix`. Previous entries were based on unofficial night-of tallies.

**What did not change:** Model architecture, simulation parameters, regional correction constants (`_AB_CPC_FLOOR`, `_BC_NDP_INTERCEPT`, `_ATLANTIC_SIGMA_MULTIPLIER`), or PyMC trajectory priors. Only calibration artefacts derived deterministically from certified vote totals were updated.

**Reproducibility:** Run `uv run python -m simulation.calibrate_systematic_error` and `uv run python -m backend.etl.estimate_transfer_matrix` against any database containing the certified GE45 results to reproduce these artefacts identically.

---

## 2025-04-28 — GE45 pre-election snapshot locked

**Trigger:** GE45 voting day. Snapshot committed to `scoring/fixtures/ge45_prediction_2025-04-27.json` before polls closed.

**Details:** Model output frozen using poll average as of 2025-04-27. Git commit timestamp serves as the unforgeable pre-registration record. See `docs/snapshot_protocol.md` for the full procedure.

---

*Future entries: add above this line in reverse-chronological order.*
