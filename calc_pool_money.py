#!/usr/bin/env python3
"""
HKJC pool money calculator.

Reads a neutral pool snapshot JSON and estimates per-horse WIN/PLA investment
using the standard pari-mutuel formula. No live data fetching.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_TAKEOUT = 0.175


def net_pool(total: float, takeout_rate: float = DEFAULT_TAKEOUT) -> float:
    return total * (1.0 - takeout_rate)


def horse_investments(
    total: float,
    horses: List[dict],
    takeout_rate: float = DEFAULT_TAKEOUT,
) -> List[dict]:
    """Estimate or pass through per-horse pool shares."""
    if total <= 0 or not horses:
        return []

    has_direct = any(h.get("investment") is not None for h in horses)
    weights: Dict[str, float] = {}
    for horse in horses:
        no = str(horse.get("no", "")).strip()
        try:
            odds = float(horse.get("odds") or 0)
        except (TypeError, ValueError):
            odds = 0.0
        if no and odds > 1:
            weights[no] = 1.0 / odds

    denom = sum(weights.values())
    rows: List[dict] = []
    for horse in horses:
        no = str(horse.get("no", "")).strip()
        name = str(horse.get("name") or f"Horse {no}")
        try:
            odds = float(horse.get("odds") or 0)
        except (TypeError, ValueError):
            odds = 0.0

        inv = horse.get("investment")
        estimated = False
        if inv is None and not has_direct and no in weights and denom > 0:
            inv = total * weights[no] / denom
            estimated = True
        elif inv is not None:
            try:
                inv = float(inv)
            except (TypeError, ValueError):
                inv = 0.0
        else:
            inv = 0.0

        share = (float(inv) / total * 100.0) if total > 0 else 0.0
        rows.append(
            {
                "no": horse.get("no"),
                "name": name,
                "odds": odds,
                "investment": float(inv or 0.0),
                "share_pct": share,
                "estimated": estimated,
            }
        )

    rows.sort(key=lambda r: r["investment"], reverse=True)
    return rows


def format_money(amount: float) -> str:
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.2f}M"
    if amount >= 1_000:
        return f"${amount / 1_000:,.0f}K"
    return f"${amount:,.0f}"


def print_pool_block(
    title: str,
    total: float,
    takeout_rate: float,
    rows: List[dict],
) -> None:
    estimated = any(r.get("estimated") for r in rows)
    net = net_pool(total, takeout_rate)

    print(f"\n  +-- {title} " + "-" * (44 - len(title)))
    print(f"  | Total pool : {format_money(total)}")
    print(f"  | Net pool   : {format_money(net)}  (takeout {takeout_rate * 100:.1f}%)")
    if estimated:
        print("  | Per-horse  : estimated from odds (pari-mutuel)")
    print("  |")

    if not rows:
        print("  | No horse rows in snapshot")
        print("  +--" + "-" * 48)
        return

    max_inv = max(r["investment"] for r in rows) or 1.0
    for row in rows:
        bar_len = int((row["investment"] / max_inv) * 30) if max_inv > 0 else 0
        bar = "#" * bar_len
        print(
            f"  | {str(row['no']):>2}. {row['name']:<18} "
            f"{format_money(row['investment']):>10} ({row['share_pct']:>4.1f}%) "
            f"@{row['odds']:.1f} {bar}"
        )
    print("  +--" + "-" * 48)


def load_snapshot(path: Optional[Path]) -> dict:
    if path:
        text = path.read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Snapshot must be a JSON object")
    return data


def calc_report(snapshot: dict) -> dict:
    pools = snapshot.get("pools") or {}
    report: Dict[str, Any] = {
        "date": snapshot.get("date"),
        "venue": snapshot.get("venue"),
        "race_no": snapshot.get("race_no"),
        "pools": {},
    }

    for pool_type in ("WIN", "PLA"):
        pool = pools.get(pool_type) or {}
        total = float(pool.get("total_investment") or 0)
        takeout = float(pool.get("takeout_rate", DEFAULT_TAKEOUT))
        horses = pool.get("horses") or []
        rows = horse_investments(total, horses, takeout_rate=takeout)
        report["pools"][pool_type] = {
            "total_investment": total,
            "net_pool": net_pool(total, takeout),
            "takeout_rate": takeout,
            "horses": rows,
        }
    return report


def print_report(snapshot: dict) -> None:
    report = calc_report(snapshot)
    print("=" * 60)
    print("  HKJC Pool Money Calculator")
    print(
        f"  {report.get('date')} | {report.get('venue')} | "
        f"Race {report.get('race_no')}"
    )
    print("=" * 60)

    print_pool_block(
        "WIN (獨贏)",
        report["pools"]["WIN"]["total_investment"],
        report["pools"]["WIN"]["takeout_rate"],
        report["pools"]["WIN"]["horses"],
    )
    print_pool_block(
        "PLA (位置)",
        report["pools"]["PLA"]["total_investment"],
        report["pools"]["PLA"]["takeout_rate"],
        report["pools"]["PLA"]["horses"],
    )
    print("\n" + "=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calculate per-horse pool money from a snapshot JSON file",
    )
    parser.add_argument(
        "snapshot",
        nargs="?",
        help="Path to pool snapshot JSON (default: stdin)",
    )
    parser.add_argument("--json", action="store_true", help="Print calculated JSON report")
    args = parser.parse_args()

    try:
        snapshot = load_snapshot(Path(args.snapshot) if args.snapshot else None)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(calc_report(snapshot), indent=2, ensure_ascii=False))
        return

    print_report(snapshot)


if __name__ == "__main__":
    main()
