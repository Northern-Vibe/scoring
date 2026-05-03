"""
Northern Vibe - GE45 scoring harness

Reproduces the accuracy figures on northernvibe.ca/accuracy from two flat files:

  - scoring/fixtures/ge45_prediction_2025-04-27.json   (frozen pre-election predictions)
  - scoring/data/ge45_certified_results.csv             (Elections Canada certified results)

No simulation imports, no database. Just csv + json from the stdlib.

Run with:
    python scoring/evaluate.py
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys

# Paths

_HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE_PATH = os.path.join(_HERE, "fixtures", "ge45_prediction_2025-04-27.json")
RESULTS_PATH = os.path.join(_HERE, "data", "ge45_certified_results.csv")

PARTIES = ["LPC", "CPC", "NDP", "BQ", "GPC", "PPC"]


# Load data

def load_fixture(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_certified_results(path: str) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append({
                "fed_code":    row["fed_code"],
                "riding_name": row["riding_name"],
                "province":    row["province"],
                "party":       row["party"],
                "vote_share":  float(row["vote_share"]),
                "votes":       int(row["votes"]) if row["votes"] else 0,
                "certified":   row["certified"].lower() == "true",
            })
    return rows


# Derived metrics

def compute_actual_vote_shares(results: list[dict], excluded: set[str]) -> dict[str, float]:
    """National vote share = sum(party_votes) / sum(all_votes) per party."""
    total_votes: dict[str, int] = {}
    grand_total = 0
    for row in results:
        if row["fed_code"] in excluded:
            continue
        p = row["party"]
        v = row["votes"]
        total_votes[p] = total_votes.get(p, 0) + v
        grand_total += v
    if grand_total == 0:
        return {}  # only happens if the CSV is empty or every riding was excluded
    return {p: round(v / grand_total * 100, 2) for p, v in total_votes.items()}


def compute_actual_seats(results: list[dict], excluded: set[str]) -> dict[str, int]:
    """Winner per riding = party with highest vote_share."""
    best: dict[str, tuple[str, float]] = {}  # fed_code -> (party, vote_share)
    for row in results:
        if row["fed_code"] in excluded:
            continue
        fc = row["fed_code"]
        if fc not in best or row["vote_share"] > best[fc][1]:
            best[fc] = (row["party"], row["vote_share"])

    seats: dict[str, int] = {}
    for party, _ in best.values():
        seats[party] = seats.get(party, 0) + 1
    return seats


def compute_mae(predicted: dict[str, float], actual: dict[str, float]) -> float:
    shared = [p for p in PARTIES if p in predicted and p in actual]
    if not shared:
        return float("nan")
    return sum(abs(predicted[p] - actual[p]) for p in shared) / len(shared)


def compute_80_band_coverage(
    predicted_seats: dict[str, dict],
    actual_seats: dict[str, int],
) -> tuple[int, int]:
    # nb: parties absent from actual_seats won 0 seats — PPC in GE45 being the obvious case
    hit = 0
    total = 0
    for party in PARTIES:
        proj = predicted_seats.get(party)
        if proj is None:
            continue
        actual = actual_seats.get(party, 0)
        total += 1
        if proj["p10"] <= actual <= proj["p90"]:
            hit += 1
    return hit, total


# Self-check

def _guard_no_sim_imports() -> None:
    # paranoid check — easy to accidentally pull in a backend import during dev
    bad = [m for m in sys.modules if m.startswith("simulation") or m.startswith("backend")]
    if bad:
        raise RuntimeError(
            f"evaluate.py must not import simulation/ or backend/. Found: {bad}"
        )


# Main

def main() -> None:
    _guard_no_sim_imports()

    fixture  = load_fixture(FIXTURE_PATH)
    results  = load_certified_results(RESULTS_PATH)
    excluded = set(fixture.get("ridings_excluded", []))

    predicted_vote_share = fixture["predicted_vote_share"]
    predicted_seats = fixture["predicted_seats"]
    # missed_ridings is populated in the fixture post-certification, not recomputed here
    missed_ridings = fixture.get("missed_ridings", [])

    actual_vote_share = compute_actual_vote_shares(results, excluded)
    actual_seats      = compute_actual_seats(results, excluded)

    # Ridings total = all non-excluded ridings that have a certified winner
    best: dict[str, tuple[str, float]] = {}
    for row in results:
        if row["fed_code"] in excluded:
            continue
        fc = row["fed_code"]
        if fc not in best or row["vote_share"] > best[fc][1]:
            best[fc] = (row["party"], row["vote_share"])
    ridings_total   = len(best)
    ridings_missed  = len(missed_ridings)
    ridings_correct = ridings_total - ridings_missed
    riding_accuracy = ridings_correct / ridings_total * 100 if ridings_total else 0.0

    mae = compute_mae(predicted_vote_share, actual_vote_share)
    bands_hit, bands_n = compute_80_band_coverage(predicted_seats, actual_seats)

    # Print results

    sep = "-" * 55
    print()
    print("Northern Vibe \u2014 GE45 Scoring Report")
    print(f"Fixture : {os.path.basename(FIXTURE_PATH)}")
    print(f"Results : {os.path.basename(RESULTS_PATH)}")
    print(sep)
    print(f"Riding call accuracy : {riding_accuracy:.1f}%  ({ridings_correct} / {ridings_total})")
    print(f"Vote share MAE       : {mae:.2f}pp")
    print(f"80% seat bands hit   : {bands_hit} / {bands_n}")
    print(sep)
    print()
    print("Vote share detail:")
    header = f"  {'Party':<6}  {'Predicted':>9}  {'Actual':>9}  {'Error':>8}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for party in PARTIES:
        pred   = predicted_vote_share.get(party)
        actual = actual_vote_share.get(party)
        if pred is None or actual is None:
            continue
        err  = actual - pred
        sign = "+" if err >= 0 else ""
        print(f"  {party:<6}  {pred:>8.2f}%  {actual:>8.2f}%  {sign}{err:>6.2f}pp")
    print()
    print("Seat projection detail (80% range = p10\u2013p90):")
    header2 = f"  {'Party':<6}  {'Median':>6}  {'80% range':>12}  {'Actual':>6}  {'In range?':>9}"
    print(header2)
    print("  " + "-" * (len(header2) - 2))
    for party in PARTIES:
        proj = predicted_seats.get(party)
        if proj is None:
            continue
        p50 = proj["p50"]
        p10 = proj["p10"]
        p90 = proj["p90"]
        actual = actual_seats.get(party, 0)
        in_range = "YES" if p10 <= actual <= p90 else "NO"
        print(f"  {party:<6}  {p50:>6}  {p10:>5}\u2013{p90:<5}       {actual:>6}  {in_range:>9}")
    print()
    print("Missed ridings (model called wrong winner):")
    if missed_ridings:
        for r in missed_ridings:
            print(f"  {r['fed_code']}  {r['name'][:40]:<40}  {r['province']}  predicted={r['predicted_winner']}")
    else:
        print("  (none)")
    print()

    # Validation assertions
    assert math.isclose(riding_accuracy, 97.7, abs_tol=0.15), \
        f"Riding accuracy mismatch: got {riding_accuracy:.1f}% (expected ~97.7%)"
    assert math.isclose(mae, 0.87, abs_tol=0.05), \
        f"MAE mismatch: got {mae:.3f}pp (expected ~0.87pp)"
    assert bands_hit >= 5, f"80% band coverage mismatch: got {bands_hit}/{bands_n}"

    print("All assertions passed.")
    print()


if __name__ == "__main__":
    main()
