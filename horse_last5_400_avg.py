"""
Verilen at ID'si icin son 5 kayittan 400m ortalamasi hesaplar.
Zemin bazinda (Kum/Cim/Sentetik) filtrelenebilir.

Ornek:
  python horse_last5_400_avg.py --horse-id 110685 --surface kum
  python horse_last5_400_avg.py --horse-id 110685 --surface kum,cim
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Atin son 5 adet 400m kaydi ortalamasini bulur.")
    p.add_argument("--horse-id", type=int, help="At ID")
    p.add_argument(
        "--input",
        default=r"C:\Users\emir\Desktop\test\sonuçlar\tracus_400_last_year\tracus_400m_detailed.csv",
        help="Girdi CSV yolu",
    )
    p.add_argument(
        "--surface",
        default="kum,cim",
        help="Zemin(ler): kum,cim,sentetik (virgulle)",
    )
    p.add_argument("--last", type=int, default=5, help="Kac son kayit alinacak")
    return p.parse_args()


def norm_surface(s: str) -> str:
    s = s.strip().lower()
    if s in ("kum",):
        return "Kum"
    if s in ("cim", "çim"):
        return "Cim"
    if s in ("sentetik",):
        return "Sentetik"
    return s


def parse_int(v: str) -> int | None:
    try:
        return int(v)
    except Exception:
        return None


def main() -> None:
    args = parse_args()
    # Interactive fallback: arg verilmezse sor.
    horse_id = args.horse_id
    surface_arg = args.surface
    last_n = args.last

    if horse_id is None:
        raw = input("At ID gir: ").strip()
        horse_id = int(raw)

    if not surface_arg:
        raw = input("Zemin gir (kum/cim/sentetik veya kum,cim): ").strip()
        surface_arg = raw or "kum,cim"

    raw_last = input(f"Kac son kayit? (varsayilan {last_n}): ").strip()
    if raw_last:
        last_n = int(raw_last)

    in_path = Path(args.input)
    wanted_surfaces = [norm_surface(x) for x in surface_arg.split(",") if x.strip()]

    rows = []
    with in_path.open("r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            if parse_int(row.get("horse_id", "")) != horse_id:
                continue
            surface = (row.get("race_surface") or "").strip()
            if surface not in wanted_surfaces:
                continue
            time_ms = parse_int(row.get("time_ms", ""))
            if time_ms is None:
                continue
            rows.append(
                {
                    "date": row.get("date"),
                    "city": row.get("city"),
                    "race_no": parse_int(row.get("race_no", "")) or 0,
                    "race_surface": surface,
                    "time_ms": time_ms,
                    "time": row.get("time"),
                    "horse_name": row.get("horse_name"),
                }
            )

    if not rows:
        print("Kayit bulunamadi.")
        return

    rows.sort(key=lambda x: (x["date"], x["race_no"]))

    for surface in wanted_surfaces:
        s_rows = [x for x in rows if x["race_surface"] == surface]
        if not s_rows:
            print(f"{surface}: kayit yok")
            continue

        last_rows = s_rows[-last_n:]
        avg_ms = sum(x["time_ms"] for x in last_rows) / len(last_rows)

        print(f"\nAt ID: {horse_id} | Zemin: {surface} | Kayit: {len(last_rows)}")
        print(f"Ortalama 400m: {avg_ms:.2f} ms ({avg_ms/1000:.3f} sn)")
        print("Kullanilan son kayitlar:")
        for x in last_rows:
            print(
                f"- {x['date']} {x['city']} K{x['race_no']} | {x['time']} ({x['time_ms']} ms) | {x['horse_name']}"
            )


if __name__ == "__main__":
    main()
