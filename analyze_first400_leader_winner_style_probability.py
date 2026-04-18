from __future__ import annotations

import argparse
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Ilk 400'de lider gecen atin temposuna gore, "
            "yaris galibinin stil olasiligini hesaplar."
        )
    )
    p.add_argument("--input", required=True, help="tracus_400m_detailed_with_style.csv yolu")
    p.add_argument("--output", required=True, help="Detayli olasilik cikti CSV")
    p.add_argument("--summary-output", required=True, help="Her bant icin en olasi stil ozeti CSV")
    p.add_argument("--bin-size", type=float, default=0.5, help="Saniye bant genisligi (varsayilan 0.5)")
    p.add_argument("--min-races", type=int, default=8, help="Bandi raporlamak icin minimum kosu")
    p.add_argument(
        "--include-unknown-style",
        action="store_true",
        help="Verilirse Bilinmiyor stil etiketlerini de olasiliga dahil eder.",
    )
    return p.parse_args()


def to_int(v: str | None) -> int | None:
    if v is None or v == "":
        return None
    try:
        return int(v)
    except ValueError:
        return None


def to_float(v: str | None) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def normalize_style(style: str | None) -> str:
    s = (style or "").strip()
    if not s:
        return "Bilinmiyor"
    return s


def main() -> None:
    args = parse_args()
    in_path = Path(args.input)

    # Race-level aggregation
    # key -> {"leader_time_ms": int|None, "winner_style": str, "breed": str, "surface": str}
    races: dict[tuple[str, str, str, str], dict] = {}

    with in_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (
                row.get("date", ""),
                row.get("city", ""),
                row.get("race_no", ""),
                row.get("network_url", ""),
            )
            rec = races.setdefault(
                key,
                {
                    "leader_time_ms": None,
                    "winner_style": None,
                    "breed": row.get("horse_breed", "") or "Bilinmiyor",
                    "surface": row.get("race_surface", "") or "Bilinmiyor",
                },
            )

            checkpoint_place = to_int(row.get("checkpoint_place"))
            final_place = to_int(row.get("final_place"))
            time_ms = to_int(row.get("time_ms"))

            if checkpoint_place == 1 and time_ms is not None:
                # If duplicate occurs, keep fastest one.
                if rec["leader_time_ms"] is None or time_ms < rec["leader_time_ms"]:
                    rec["leader_time_ms"] = time_ms

            if final_place == 1:
                rec["winner_style"] = normalize_style(row.get("stil_etiketi"))
                # keep winner row breed/surface as authoritative
                rec["breed"] = row.get("horse_breed", "") or rec["breed"]
                rec["surface"] = row.get("race_surface", "") or rec["surface"]

    # Group by breed + surface + tempo bin
    grouped_styles: dict[tuple[str, str, float, float], Counter] = defaultdict(Counter)
    race_counts: Counter = Counter()

    for rec in races.values():
        leader_ms = rec.get("leader_time_ms")
        winner_style = rec.get("winner_style")
        if leader_ms is None or not winner_style:
            continue
        if (not args.include_unknown_style) and winner_style == "Bilinmiyor":
            continue

        sec = leader_ms / 1000.0
        bin_start = math.floor(sec / args.bin_size) * args.bin_size
        bin_end = bin_start + args.bin_size

        breed = rec.get("breed") or "Bilinmiyor"
        surface = rec.get("surface") or "Bilinmiyor"
        gkey = (breed, surface, round(bin_start, 3), round(bin_end, 3))

        grouped_styles[gkey][winner_style] += 1
        race_counts[gkey] += 1

    # Detailed long-format output (one row per style probability)
    detailed_rows = []
    summary_rows = []

    for gkey in sorted(grouped_styles.keys(), key=lambda x: (x[0], x[1], x[2])):
        breed, surface, bstart, bend = gkey
        total = race_counts[gkey]
        if total < args.min_races:
            continue

        style_counter = grouped_styles[gkey]
        # top 2 styles for summary
        top_items = style_counter.most_common(2)
        top_style_1, top_count_1 = top_items[0]
        top_prob_1 = (top_count_1 / total) * 100.0
        if len(top_items) > 1:
            top_style_2, top_count_2 = top_items[1]
            top_prob_2 = (top_count_2 / total) * 100.0
        else:
            top_style_2, top_count_2, top_prob_2 = "", 0, 0.0
        summary_rows.append(
            {
                "horse_breed": breed,
                "race_surface": surface,
                "bin_start_sec": f"{bstart:.3f}",
                "bin_end_sec": f"{bend:.3f}",
                "race_count": total,
                "top_style_1": top_style_1,
                "top_style_1_count": top_count_1,
                "top_style_1_probability_pct": round(top_prob_1, 2),
                "top_style_2": top_style_2,
                "top_style_2_count": top_count_2,
                "top_style_2_probability_pct": round(top_prob_2, 2),
            }
        )

        for style, count in style_counter.most_common():
            prob = (count / total) * 100.0
            detailed_rows.append(
                {
                    "horse_breed": breed,
                    "race_surface": surface,
                    "bin_start_sec": f"{bstart:.3f}",
                    "bin_end_sec": f"{bend:.3f}",
                    "race_count": total,
                    "winner_style": style,
                    "style_count": count,
                    "style_probability_pct": round(prob, 2),
                }
            )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "horse_breed",
                "race_surface",
                "bin_start_sec",
                "bin_end_sec",
                "race_count",
                "winner_style",
                "style_count",
                "style_probability_pct",
            ],
        )
        writer.writeheader()
        writer.writerows(detailed_rows)

    summary_path = Path(args.summary_output)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "horse_breed",
                "race_surface",
                "bin_start_sec",
                "bin_end_sec",
                "race_count",
                "top_style_1",
                "top_style_1_count",
                "top_style_1_probability_pct",
                "top_style_2",
                "top_style_2_count",
                "top_style_2_probability_pct",
            ],
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"Detay yazildi: {out_path}")
    print(f"Ozet yazildi: {summary_path}")
    print(f"Detay satir: {len(detailed_rows)} | Ozet satir: {len(summary_rows)}")


if __name__ == "__main__":
    main()
