"""
Accurace Tracus checkpoint scraper.

Example:
  python scrape_accurace_tracus.py --url https://accurace.net/network/2026-03-16/BURSA/3 --distance 400 --csv out.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


NUXT_DATA_PATTERN = re.compile(
    r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>',
    re.S,
)


def fetch_html(url: str, timeout: int = 30) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        },
    )
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "ignore")


def decode_nuxt_payload(table: list[Any]) -> Any:
    memo: dict[int, Any] = {}

    def resolve_ref(value: Any) -> Any:
        if isinstance(value, int) and 0 <= value < len(table):
            return resolve_index(value)
        return value

    def resolve_index(index: int) -> Any:
        if index in memo:
            return memo[index]

        node = table[index]
        if isinstance(node, dict):
            out: dict[str, Any] = {}
            memo[index] = out
            for key, value in node.items():
                out[key] = resolve_ref(value)
            return out

        if isinstance(node, list):
            # Nuxt serialization wrappers.
            if (
                len(node) == 2
                and isinstance(node[0], str)
                and node[0] in ("Reactive", "ShallowReactive")
            ):
                out = resolve_ref(node[1])
                memo[index] = out
                return out
            if len(node) == 1 and node[0] == "Set":
                out: list[Any] = []
                memo[index] = out
                return out

            out_list: list[Any] = []
            memo[index] = out_list
            out_list.extend(resolve_ref(item) for item in node)
            return out_list

        memo[index] = node
        return node

    return resolve_index(1)


def extract_table_from_html(html: str) -> dict[str, Any]:
    match = NUXT_DATA_PATTERN.search(html)
    if not match:
        raise ValueError("__NUXT_DATA__ script tag bulunamadi.")

    payload_raw = match.group(1)
    payload = json.loads(payload_raw)
    decoded = decode_nuxt_payload(payload)

    try:
        return decoded["data"]["result"]["data"]["table"]
    except Exception as exc:  # pragma: no cover - defensive parse path
        raise ValueError("Beklenen veri yapisi bulunamadi.") from exc


def extract_distance_rows(table: dict[str, Any], distance: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for horse in table.get("horse", []):
        checkpoint_items = horse.get("checkpoint", [])
        point = next(
            (item for item in checkpoint_items if item.get("checkpoint") == distance),
            None,
        )
        if not point:
            continue

        rows.append(
            {
                "horse_name": horse.get("horse_name"),
                "horse_number": horse.get("horse_number"),
                "final_place": horse.get("place"),
                "checkpoint": distance,
                "checkpoint_place": point.get("place"),
                "time": point.get("time"),
                "time_format": point.get("time_format"),
            }
        )

    return sorted(
        rows,
        key=lambda row: (
            row["checkpoint_place"] is None,
            row["checkpoint_place"],
            row["horse_number"] is None,
            row["horse_number"],
        ),
    )


def build_network_url(date: str, city: str, race_no: int) -> str:
    return f"https://accurace.net/network/{date}/{city.upper()}/{race_no}"


def write_csv(rows: list[dict[str, Any]], csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "horse_name",
                "horse_number",
                "final_place",
                "checkpoint",
                "checkpoint_place",
                "time",
                "time_format",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Accurace network sayfasindan Tracus mesafe derecelerini cek."
    )
    parser.add_argument(
        "--url",
        help="Ornek: https://accurace.net/network/2026-03-16/BURSA/3",
    )
    parser.add_argument("--date", help="YYYY-MM-DD")
    parser.add_argument("--city", help="Ornek: BURSA")
    parser.add_argument("--race-no", type=int, help="Kosu numarasi")
    parser.add_argument("--distance", type=int, default=400, help="Mesafe (metre)")
    parser.add_argument("--csv", help="CSV cikis dosyasi yolu")
    parser.add_argument("--json", help="JSON cikis dosyasi yolu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.url:
        url = args.url
    else:
        missing = [k for k in ("date", "city", "race_no") if getattr(args, k) in (None, "")]
        if missing:
            raise SystemExit(
                "--url vermiyorsan --date --city --race-no parametreleri zorunlu."
            )
        url = build_network_url(args.date, args.city, args.race_no)

    html = fetch_html(url)
    table = extract_table_from_html(html)
    rows = extract_distance_rows(table, args.distance)

    race = table.get("race", {})
    summary = {
        "url": url,
        "race": race,
        "distance": args.distance,
        "rows_count": len(rows),
        "rows": rows,
    }

    if args.json:
        json_path = Path(args.json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"JSON yazildi: {json_path}")

    if args.csv:
        csv_path = Path(args.csv)
        write_csv(rows, csv_path)
        print(f"CSV yazildi: {csv_path}")

    if not args.csv and not args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
