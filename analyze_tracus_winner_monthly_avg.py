"""
Tracus 400m detay CSV'sinden sadece Tracus 400m gecisinde birinci olan
atlarin aylik ortalama 400m derecelerini cikarir.

Kirilim:
- horse_breed (Arap/Ingiliz/Bilinmiyor)
- race_surface (Kum/Cim/Sentetik/Bilinmiyor)
- month (YYYY-MM)
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Sadece Tracus 400m'de birinci gecenlerden aylik 400m ortalama cikarir "
            "(cins + pist kirilimi)."
        )
    )
    p.add_argument("--input", required=True, help="tracus_400m_detailed.csv yolu")
    p.add_argument(
        "--output",
        required=True,
        help="Aylik ozet CSV cikis yolu",
    )
    return p.parse_args()


def month_from_date(date_str: str) -> str:
    # Beklenen format: YYYY-MM-DD
    return date_str[:7]


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    groups: dict[tuple[str, str, str], dict[str, float]] = defaultdict(
        lambda: {
            "count": 0,
            "sum_ms": 0.0,
            "best_ms": float("inf"),
            "worst_ms": float("-inf"),
        }
    )

    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("checkpoint_place") != "1":
                continue

            time_ms_raw = row.get("time_ms", "")
            if not time_ms_raw:
                continue
            try:
                time_ms = float(time_ms_raw)
            except ValueError:
                continue

            date_str = row.get("date", "")
            if len(date_str) < 7:
                continue

            month = month_from_date(date_str)
            breed = row.get("horse_breed", "") or "Bilinmiyor"
            surface = row.get("race_surface", "") or "Bilinmiyor"
            key = (month, breed, surface)

            groups[key]["count"] += 1
            groups[key]["sum_ms"] += time_ms
            if time_ms < groups[key]["best_ms"]:
                groups[key]["best_ms"] = time_ms
            if time_ms > groups[key]["worst_ms"]:
                groups[key]["worst_ms"] = time_ms

    output_rows = []
    for (month, breed, surface), agg in sorted(groups.items()):
        count = int(agg["count"])
        avg_ms = agg["sum_ms"] / count if count else 0.0
        output_rows.append(
            {
                "month": month,
                "horse_breed": breed,
                "race_surface": surface,
                "first400_leader_count": count,
                "avg_400m_ms": round(avg_ms, 2),
                "avg_400m_sec": round(avg_ms / 1000.0, 3),
                "best_400m_ms": int(agg["best_ms"]) if count else "",
                "best_400m_sec": round((agg["best_ms"] / 1000.0), 3) if count else "",
                "worst_400m_ms": int(agg["worst_ms"]) if count else "",
                "worst_400m_sec": round((agg["worst_ms"] / 1000.0), 3) if count else "",
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "month",
                "horse_breed",
                "race_surface",
                "first400_leader_count",
                "avg_400m_ms",
                "avg_400m_sec",
                "best_400m_ms",
                "best_400m_sec",
                "worst_400m_ms",
                "worst_400m_sec",
            ],
        )
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Yazildi: {output_path}")
    print(f"Toplam grup: {len(output_rows)}")


if __name__ == "__main__":
    main()
