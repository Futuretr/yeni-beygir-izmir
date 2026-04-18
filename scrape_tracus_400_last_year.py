"""
Tum sehirler icin son 1 yilin Tracus 400m verisini toplar.

Cikti:
  1) tracus_400m_detailed.csv
  2) tracus_400m_by_horse.csv
  3) tracus_400m_by_city_day.csv

Ornek:
  python scrape_tracus_400_last_year.py
  python scrape_tracus_400_last_year.py --workers 24 --outdir C:\\data\\tracus_400
"""

from __future__ import annotations

import argparse
import csv
import re
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

from bs4 import BeautifulSoup

from scrape_accurace_tracus import (
    extract_distance_rows,
    extract_table_from_html,
    fetch_html,
)


CITIES = [
    ("Adana", 1),
    ("Izmir", 2),
    ("Istanbul", 3),
    ("Bursa", 4),
    ("Ankara", 5),
    ("Urfa", 6),
    ("Elazig", 7),
    ("Diyarbakir", 8),
    ("Kocaeli", 9),
    ("Antalya", 10),
]

NETWORK_RE = re.compile(r"https://accurace\.net/network/\d{4}-\d{2}-\d{2}/[A-Z]+/\d+")
NETWORK_PARTS_RE = re.compile(
    r"https://accurace\.net/network/(?P<date>\d{4}-\d{2}-\d{2})/(?P<city>[A-Z]+)/(?P<race>\d+)"
)
HORSE_ID_RE = re.compile(r"(?:AtId|Id)=(\d+)")


@dataclass(frozen=True)
class DayCityTask:
    race_date: date
    city_name: str
    city_id: int


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Son 1 yildaki tum sehirlerden Tracus 400m verisini toplar."
    )
    p.add_argument("--workers", type=int, default=32, help="Paralel worker sayisi")
    p.add_argument("--distance", type=int, default=400, help="Checkpoint mesafesi")
    p.add_argument(
        "--outdir",
        default="tracus_400_last_year",
        help="Cikti klasoru",
    )
    p.add_argument(
        "--start-date",
        help="Opsiyonel baslangic tarihi YYYY-MM-DD (verilmezse bugunden 365 gun geri)",
    )
    p.add_argument(
        "--end-date",
        help="Opsiyonel bitis tarihi YYYY-MM-DD (verilmezse bugun)",
    )
    return p.parse_args()


def date_range(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def tjk_result_url(task: DayCityTask) -> str:
    d = task.race_date.strftime("%d%%2F%m%%2F%Y")
    return (
        "https://www.tjk.org/TR/YarisSever/Info/Sehir/GunlukYarisSonuclari"
        f"?SehirId={task.city_id}&QueryParameter_Tarih={d}&SehirAdi={task.city_name}"
    )


def fetch_with_retry(url: str, retries: int = 2, timeout: int = 25) -> str | None:
    for attempt in range(retries + 1):
        try:
            return fetch_html(url, timeout=timeout)
        except Exception:
            if attempt == retries:
                return None
            time.sleep(0.4 * (attempt + 1))
    return None


def normalize_text(value: str) -> str:
    return (
        value.lower()
        .replace("i̇", "i")
        .replace("ı", "i")
        .replace("ş", "s")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ö", "o")
        .replace("ç", "c")
    )


def detect_breed_from_race_config(config_text: str) -> str:
    txt = normalize_text(config_text)
    if "arap" in txt:
        return "Arap"
    if "ingiliz" in txt:
        return "Ingiliz"
    return "Bilinmiyor"


def detect_surface_from_race_config(config_text: str) -> str:
    txt = normalize_text(config_text)
    if "sentetik" in txt:
        return "Sentetik"
    if "cim" in txt:
        return "Cim"
    if "kum" in txt:
        return "Kum"
    return "Bilinmiyor"


def normalize_horse_name(value: str | None) -> str:
    if not value:
        return ""
    text = value.strip()
    text = re.sub(r"\(.*?\)", "", text).strip()
    return normalize_text(text)


def parse_horse_number(raw_text: str) -> int | None:
    m = re.search(r"\((\d+)\)", raw_text or "")
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


def parse_horse_id_from_href(href: str | None) -> int | None:
    if not href:
        return None
    m = HORSE_ID_RE.search(href)
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


def collect_network_metadata(task: DayCityTask) -> dict[str, dict]:
    html = fetch_with_retry(tjk_result_url(task), retries=1, timeout=20)
    if not html:
        return {}

    soup = BeautifulSoup(html, "html.parser")
    race_div = soup.find("div", class_="races-panes")
    if not race_div:
        urls = set(NETWORK_RE.findall(html))
        return {
            url: {
                "horse_breed": "Bilinmiyor",
                "race_surface": "Bilinmiyor",
                "horse_ids_by_name": {},
                "horse_ids_by_number": {},
            }
            for url in urls
        }

    result: dict[str, dict] = {}
    for race_block in race_div.find_all("div", recursive=False):
        config_el = race_block.find("h3", class_="race-config")
        config_text = config_el.get_text(" ", strip=True) if config_el else ""
        breed = detect_breed_from_race_config(config_text)
        surface = detect_surface_from_race_config(config_text)
        horse_ids_by_name: dict[str, int] = {}
        horse_ids_by_number: dict[int, int] = {}

        for tr in race_block.find_all("tr"):
            horse_cell = tr.find("td", class_=re.compile(r"AtAdi3$|AtAdi$"))
            if not horse_cell:
                continue
            a = horse_cell.find("a", href=True)
            if not a:
                continue

            raw_name = a.get_text(" ", strip=True) or horse_cell.get_text(" ", strip=True)
            horse_name_key = normalize_horse_name(raw_name)
            horse_number = parse_horse_number(horse_cell.get_text(" ", strip=True))
            horse_id = parse_horse_id_from_href(a.get("href"))

            if horse_id is None:
                continue
            if horse_name_key:
                horse_ids_by_name[horse_name_key] = horse_id
            if horse_number is not None:
                horse_ids_by_number[horse_number] = horse_id

        for a in race_block.find_all("a", href=True):
            href = a["href"]
            if "/summary" in href:
                continue
            m = NETWORK_RE.search(href)
            if not m:
                continue
            result[m.group(0)] = {
                "horse_breed": breed,
                "race_surface": surface,
                "horse_ids_by_name": horse_ids_by_name,
                "horse_ids_by_number": horse_ids_by_number,
            }
    return result


def parse_time_to_ms(time_str: str | None) -> int | None:
    if not time_str:
        return None
    try:
        parts = time_str.split(":")
        if len(parts) == 2:
            hh = 0
            mm = int(parts[0])
            sec_ms = float(parts[1])
        elif len(parts) == 3:
            hh = int(parts[0])
            mm = int(parts[1])
            sec_ms = float(parts[2])
        else:
            return None
        total_ms = int((hh * 3600 + mm * 60 + sec_ms) * 1000)
        return total_ms
    except Exception:
        return None


def resolve_horse_id(
    horse_name: str | None,
    horse_number: int | None,
    horse_ids_by_name: dict[str, int],
    horse_ids_by_number: dict[int, int],
) -> int | None:
    if horse_number is not None and horse_number in horse_ids_by_number:
        return horse_ids_by_number[horse_number]
    key = normalize_horse_name(horse_name)
    if key and key in horse_ids_by_name:
        return horse_ids_by_name[key]
    return None


def scrape_network_distance(
    network_url: str,
    distance: int,
    horse_breed: str,
    race_surface: str,
    horse_ids_by_name: dict[str, int],
    horse_ids_by_number: dict[int, int],
) -> list[dict]:
    html = fetch_with_retry(network_url, retries=2, timeout=25)
    if not html:
        return []

    try:
        table = extract_table_from_html(html)
        rows = extract_distance_rows(table, distance)
    except Exception:
        return []

    m = NETWORK_PARTS_RE.match(network_url)
    if not m:
        return []

    race_date = m.group("date")
    city = m.group("city")
    race_no = int(m.group("race"))

    result: list[dict] = []
    for row in rows:
        result.append(
            {
                "date": race_date,
                "city": city,
                "race_no": race_no,
                "network_url": network_url,
                "horse_breed": horse_breed,
                "race_surface": race_surface,
                "horse_name": row.get("horse_name"),
                "horse_id": resolve_horse_id(
                    row.get("horse_name"),
                    row.get("horse_number"),
                    horse_ids_by_name,
                    horse_ids_by_number,
                ),
                "horse_number": row.get("horse_number"),
                "final_place": row.get("final_place"),
                "checkpoint_place": row.get("checkpoint_place"),
                "time": row.get("time"),
                "time_format": row.get("time_format"),
                "time_ms": parse_time_to_ms(row.get("time")),
            }
        )
    return result


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    end_date = date.fromisoformat(args.end_date) if args.end_date else date.today()
    start_date = (
        date.fromisoformat(args.start_date)
        if args.start_date
        else end_date - timedelta(days=365)
    )

    tasks = [
        DayCityTask(race_date=d, city_name=city_name, city_id=city_id)
        for d in date_range(start_date, end_date)
        for city_name, city_id in CITIES
    ]

    print(
        f"Tarih araligi: {start_date.isoformat()} -> {end_date.isoformat()} | "
        f"Sehir: {len(CITIES)} | Gun*Sehir gorev: {len(tasks)}"
    )

    network_meta_map: dict[str, dict] = {}
    lock = threading.Lock()
    processed = 0
    start_ts = time.time()

    print("1/3 TJK sonuc sayfalarindan Accurace linkleri toplaniyor...")
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(collect_network_metadata, task): task for task in tasks}
        for fut in as_completed(futures):
            day_map = fut.result()
            with lock:
                network_meta_map.update(day_map)
                processed += 1
                if processed % 300 == 0 or processed == len(tasks):
                    elapsed = time.time() - start_ts
                    rate = processed / elapsed if elapsed else 0
                    eta_sec = (len(tasks) - processed) / rate if rate > 0 else 0
                    print(
                        f"  ilerleme: {processed}/{len(tasks)} | hiz: {rate:.1f}/sn | "
                        f"kalan: {eta_sec/60:.1f} dk | bulunan network link: {len(network_meta_map)}"
                    )

    network_list = sorted(network_meta_map.keys())
    print(f"Toplam benzersiz Accurace network linki: {len(network_list)}")

    print("2/3 Network sayfalarindan 400m verisi toplaniyor...")
    all_rows: list[dict] = []
    done_network = 0
    network_start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {
            ex.submit(
                scrape_network_distance,
                url,
                args.distance,
                network_meta_map.get(url, {}).get("horse_breed", "Bilinmiyor"),
                network_meta_map.get(url, {}).get("race_surface", "Bilinmiyor"),
                network_meta_map.get(url, {}).get("horse_ids_by_name", {}),
                network_meta_map.get(url, {}).get("horse_ids_by_number", {}),
            ): url
            for url in network_list
        }
        for fut in as_completed(futures):
            rows = fut.result()
            if rows:
                all_rows.extend(rows)
            done_network += 1
            if done_network % 300 == 0 or done_network == len(network_list):
                elapsed = time.time() - network_start
                rate = done_network / elapsed if elapsed else 0
                eta_sec = (len(network_list) - done_network) / rate if rate > 0 else 0
                print(
                    f"  ilerleme: {done_network}/{len(network_list)} | hiz: {rate:.1f}/sn | "
                    f"kalan: {eta_sec/60:.1f} dk | toplanan kayit: {len(all_rows)}"
                )

    all_rows.sort(
        key=lambda r: (
            r["date"],
            r["city"],
            r["race_no"],
            r["checkpoint_place"] if r["checkpoint_place"] is not None else 999,
            r["horse_number"] if r["horse_number"] is not None else 999,
        )
    )

    detailed_path = outdir / "tracus_400m_detailed.csv"
    write_csv(
        detailed_path,
        all_rows,
        [
            "date",
            "city",
            "race_no",
            "network_url",
            "horse_breed",
            "race_surface",
            "horse_name",
            "horse_id",
            "horse_number",
            "final_place",
            "checkpoint_place",
            "time",
            "time_format",
            "time_ms",
        ],
    )

    by_horse_rows = sorted(
        all_rows,
        key=lambda r: (
            (r.get("horse_name") or "").upper(),
            r.get("horse_breed") or "",
            r["date"],
            r["city"],
            r["race_no"],
        ),
    )
    by_horse_path = outdir / "tracus_400m_by_horse.csv"
    write_csv(
        by_horse_path,
        by_horse_rows,
        [
            "horse_name",
            "date",
            "city",
            "race_no",
            "network_url",
            "horse_breed",
            "race_surface",
            "horse_id",
            "horse_number",
            "checkpoint_place",
            "time",
            "time_format",
            "time_ms",
            "final_place",
        ],
    )

    group: dict[tuple[str, str], dict] = defaultdict(
        lambda: {
            "races": set(),
            "record_count": 0,
            "unique_horses": set(),
            "sum_time_ms": 0,
            "time_count": 0,
        }
    )
    for row in all_rows:
        key = (row["date"], row["city"])
        item = group[key]
        item["races"].add(row["race_no"])
        item["record_count"] += 1
        if row.get("horse_name"):
            item["unique_horses"].add(row["horse_name"])
        if row.get("time_ms") is not None:
            item["sum_time_ms"] += row["time_ms"]
            item["time_count"] += 1

    by_city_day_rows = []
    for (d, c), item in sorted(group.items()):
        avg_ms = (
            round(item["sum_time_ms"] / item["time_count"], 2)
            if item["time_count"] > 0
            else None
        )
        by_city_day_rows.append(
            {
                "date": d,
                "city": c,
                "race_count": len(item["races"]),
                "record_count": item["record_count"],
                "unique_horse_count": len(item["unique_horses"]),
                "avg_400m_ms": avg_ms,
            }
        )

    arap_rows = [r for r in all_rows if r.get("horse_breed") == "Arap"]
    ingiliz_rows = [r for r in all_rows if r.get("horse_breed") == "Ingiliz"]
    bilinmiyor_rows = [r for r in all_rows if r.get("horse_breed") not in ("Arap", "Ingiliz")]

    common_fields = [
        "date",
        "city",
        "race_no",
        "network_url",
        "horse_breed",
        "race_surface",
        "horse_name",
        "horse_id",
        "horse_number",
        "final_place",
        "checkpoint_place",
        "time",
        "time_format",
        "time_ms",
    ]
    write_csv(outdir / "tracus_400m_arap.csv", arap_rows, common_fields)
    write_csv(outdir / "tracus_400m_ingiliz.csv", ingiliz_rows, common_fields)
    write_csv(outdir / "tracus_400m_bilinmiyor.csv", bilinmiyor_rows, common_fields)

    kum_rows = [r for r in all_rows if r.get("race_surface") == "Kum"]
    cim_rows = [r for r in all_rows if r.get("race_surface") == "Cim"]
    sentetik_rows = [r for r in all_rows if r.get("race_surface") == "Sentetik"]
    surface_bilinmiyor_rows = [
        r for r in all_rows if r.get("race_surface") not in ("Kum", "Cim", "Sentetik")
    ]
    write_csv(outdir / "tracus_400m_kum.csv", kum_rows, common_fields)
    write_csv(outdir / "tracus_400m_cim.csv", cim_rows, common_fields)
    write_csv(outdir / "tracus_400m_sentetik.csv", sentetik_rows, common_fields)
    write_csv(
        outdir / "tracus_400m_surface_bilinmiyor.csv",
        surface_bilinmiyor_rows,
        common_fields,
    )

    by_city_day_path = outdir / "tracus_400m_by_city_day.csv"
    write_csv(
        by_city_day_path,
        by_city_day_rows,
        [
            "date",
            "city",
            "race_count",
            "record_count",
            "unique_horse_count",
            "avg_400m_ms",
        ],
    )

    print("3/3 CSV ciktilari yazildi:")
    print(f"  - {detailed_path}")
    print(f"  - {by_horse_path}")
    print(f"  - {by_city_day_path}")
    print(f"  - {outdir / 'tracus_400m_arap.csv'}")
    print(f"  - {outdir / 'tracus_400m_ingiliz.csv'}")
    print(f"  - {outdir / 'tracus_400m_bilinmiyor.csv'}")
    print(f"  - {outdir / 'tracus_400m_kum.csv'}")
    print(f"  - {outdir / 'tracus_400m_cim.csv'}")
    print(f"  - {outdir / 'tracus_400m_sentetik.csv'}")
    print(f"  - {outdir / 'tracus_400m_surface_bilinmiyor.csv'}")
    print(f"Toplam 400m kaydi: {len(all_rows)}")
    total_minutes = (time.time() - start_ts) / 60
    print(f"Toplam sure: {total_minutes:.1f} dk")


if __name__ == "__main__":
    main()
