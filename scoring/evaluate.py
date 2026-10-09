"""
Northern Vibe - GE45 scoring harness

Reproduces the out-of-sample accuracy figures on northernvibe.ca/accuracy from
two flat files:

  - scoring/fixtures/ge45_oos_backtest.json   (frozen backtest predictions)
  - scoring/data/ge45_certified_results.csv   (Elections Canada certified results)

Every number is derived here: the fixture holds each riding's predicted winner,
and this script compares it with the certified winner. No simulation imports,
no database. Just csv + json from the stdlib.

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
FIXTURE_PATH = os.path.join(_HERE, "fixtures", "ge45_oos_backtest.json")
RESULTS_PATH = os.path.join(_HERE, "data", "ge45_certified_results.csv")

PARTIES = ["LPC", "CPC", "NDP", "BQ", "GPC", "PPC"]

# The figures published on /accuracy. The assertions at the end check that
# the files in this directory reproduce them.
PUBLISHED = {
    "riding_accuracy": 88.0,      # 301 / 342
    "ridings_correct": 301,
    "persistence_accuracy": 83.3,  # 285 / 342, "2021 winner holds"
    "vote_mae": 0.87,
}


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

def certified_winners(results: list[dict], excluded: set[str]) -> dict[str, dict]:
    """Winner per riding = party with the highest vote share."""
    best: dict[str, dict] = {}
    for row in results:
        if row["fed_code"] in excluded:
            continue
        fc = row["fed_code"]
        if fc not in best or row["vote_share"] > best[fc]["vote_share"]:
            best[fc] = row
    return best


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


def score_calls(predicted: dict[str, str], winners: dict[str, dict]) -> tuple[int, int, list[dict]]:
    """(correct, total, misses) for one set of riding calls."""
    correct = total = 0
    misses = []
    for fc, row in sorted(winners.items()):
        pred = predicted.get(fc)
        if pred is None:
            continue
        total += 1
        if pred == row["party"]:
            correct += 1
        else:
            misses.append({**row, "predicted": pred})
    return correct, total, misses


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

    winners = certified_winners(results, excluded)
    correct, total, misses = score_calls(fixture["predicted_winners"], winners)
    p_correct, p_total, _ = score_calls(fixture["persistence_winners"], winners)
    riding_accuracy = correct / total * 100 if total else 0.0
    persistence_accuracy = p_correct / p_total * 100 if p_total else 0.0

    actual_vote_share = compute_actual_vote_shares(results, excluded)
    actual_seats: dict[str, int] = {}
    for row in winners.values():
        actual_seats[row["party"]] = actual_seats.get(row["party"], 0) + 1

    predicted_vote_share = fixture["predicted_vote_share"]
    predicted_seats = fixture["predicted_seats"]
    mae = compute_mae(predicted_vote_share, actual_vote_share)
    bands_hit, bands_n = compute_80_band_coverage(predicted_seats, actual_seats)

    # Print results

    sep = "-" * 60
    print()
    print("Northern Vibe — GE45 Out-of-Sample Scoring Report")
    print(f"Fixture : {os.path.basename(FIXTURE_PATH)}")
    print(f"Results : {os.path.basename(RESULTS_PATH)}")
    print(f"Inputs  : {fixture['baseline']} riding results + national polls as of {fixture['holdout_date']}")
    print(sep)
    print(f"Riding call accuracy   : {riding_accuracy:.1f}%  ({correct} / {total})")
    print(f"2021 winner holds      : {persistence_accuracy:.1f}%  ({p_correct} / {p_total})  [naive baseline]")
    print(f"Vote share MAE         : {mae:.2f}pp")
    print(f"80% seat bands hit     : {bands_hit} / {bands_n}")
    print(f"LPC majority (model)   : {fixture['lpc_majority_prob']:.1f}%  (actual: {actual_seats.get('LPC', 0)} seats)")
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
    print("Seat projection detail (80% range = p10–p90):")
    header2 = f"  {'Party':<6}  {'Median':>6}  {'80% range':>12}  {'Actual':>6}  {'In range?':>9}"
    print(header2)
    print("  " + "-" * (len(header2) - 2))
    for party in PARTIES:
        proj = predicted_seats.get(party)
        if proj is None:
            continue
        actual = actual_seats.get(party, 0)
        in_range = "YES" if proj["p10"] <= actual <= proj["p90"] else "NO"
        print(f"  {party:<6}  {proj['p50']:>6}  {proj['p10']:>5}–{proj['p90']:<5}       {actual:>6}  {in_range:>9}")
    print()
    print(f"Missed ridings ({len(misses)}, model called the wrong winner):")
    for r in misses:
        print(f"  {r['fed_code']}  {r['riding_name'][:40]:<40}  {r['province']:<2}  "
              f"predicted={r['predicted']:<3}  winner={r['party']}")
    print()

    # Validation assertions: the files reproduce the published figures.
    assert correct == PUBLISHED["ridings_correct"] and math.isclose(
        riding_accuracy, PUBLISHED["riding_accuracy"], abs_tol=0.05), \
        f"Riding accuracy mismatch: got {riding_accuracy:.1f}% ({correct}/{total})"
    assert math.isclose(persistence_accuracy, PUBLISHED["persistence_accuracy"], abs_tol=0.05), \
        f"Persistence baseline mismatch: got {persistence_accuracy:.1f}%"
    assert math.isclose(mae, PUBLISHED["vote_mae"], abs_tol=0.01), \
        f"MAE mismatch: got {mae:.3f}pp (expected ~{PUBLISHED['vote_mae']}pp)"

    print("All assertions passed.")
    print()


if __name__ == "__main__":
    main()
