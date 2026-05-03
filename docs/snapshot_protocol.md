# Pre-Election Snapshot Protocol

This document describes the procedure for committing a frozen prediction snapshot before polls close on a federal election night. The Git commit timestamp is an unforgeable pre-registration record that the predictions existed before results were known.

---

## When to run

Lock the snapshot on the **morning of election day**, after the final poll average has been computed but before any riding results are called (i.e., before ~21:30 ET on election night).

---

## Steps

### 1. Verify poll aggregate is current

Confirm the poll aggregate reflects the final pre-election day average:

```bash
uv run python -m backend.etl.aggregate_polls
```

Check the output — the most recent `aggregate_date` should be election day minus 1 (i.e., the last day polls were published).

### 2. Run the calibration ETL to capture model predictions

```bash
SNAPSHOT_DATE="YYYY-MM-DD"   # replace with the poll aggregate date (day before election)
uv run python -m backend.etl.compute_ge45_calibration   # or the equivalent for the next election
```

This writes the model output to `forecast_model_cache`.

### 3. Export the snapshot fixture

Run the following to export the predictions to a fixture file:

```bash
uv run python - <<'EOF'
import json
from backend.database import engine
import sqlalchemy as sa

ELECTION_TAG = "ge46"   # update for each election
SNAPSHOT_DATE = "YYYY-MM-DD"  # same date used above

with engine.connect() as conn:
    row = conn.execute(sa.text(
        f"SELECT payload FROM forecast_model_cache WHERE endpoint = 'calibration-{ELECTION_TAG}' LIMIT 1"
    )).fetchone()

data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
fixture = {
    "model": "northern-vibe-vX.Y.Z",   # update version
    "as_of_date": SNAPSHOT_DATE,
    "description": f"Northern Vibe pre-election forecast — poll average as of {SNAPSHOT_DATE}.",
    "ridings_excluded": ["24073"],      # update if any ridings are excluded for this election
    "predicted_vote_share": data["predicted_vote_share"],
    "predicted_seats": data["predicted_seats"],
    "missed_ridings": [],               # leave empty — filled in post-certification
}

out_path = f"scoring/fixtures/{ELECTION_TAG}_prediction_{SNAPSHOT_DATE}.json"
with open(out_path, "w") as f:
    json.dump(fixture, f, indent=2, ensure_ascii=False)

print(f"Written: {out_path}")
EOF
```

### 4. Commit the fixture immediately

```bash
git add scoring/fixtures/
git commit -m "snapshot: lock pre-election prediction fixture for GE46 (as of YYYY-MM-DD)"
git push origin main   # or the appropriate branch
```

The commit must be pushed **before polls close** in the earliest time zone (Newfoundland polls close at 19:30 NT = 21:00 ET). Do not push after that point.

### 5. Record the commit hash

Note the commit hash and add it to `docs/model_decisions.md` under a new entry:

```markdown
## YYYY-MM-DD — GE46 pre-election snapshot locked

**Trigger:** GE46 voting day.

**Details:** Model output frozen using poll average as of YYYY-MM-DD.
Git commit: `<hash>`
```

---

## After certification

Once Elections Canada releases certified results:

1. Add the certified results to `scoring/data/ge{N}_certified_results.csv` (export from the `election_results` table).
2. Update `scoring/fixtures/ge{N}_prediction_YYYY-MM-DD.json` — fill in `missed_ridings` from the computed calibration.
3. Run `python scoring/evaluate.py` to verify the metrics match the `/accuracy` page.
4. Update `docs/model_decisions.md` with the post-certification recalibration entry.

---

## Why this matters

Committing predictions before polls close makes retroactive adjustment detectable. Anyone can check that the fixture file predates the certified results by comparing Git commit timestamps.
