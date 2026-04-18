import argparse
import csv
import datetime as dt
import json
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape

import requests
from bs4 import BeautifulSoup


if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)


CITIES = {
    1: "Adana",
    2: "Izmir",
    3: "Istanbul",
    4: "Bursa",
    5: "Ankara",
    6: "Urfa",
    7: "Elazig",
    8: "Diyarbakir",
    9: "Kocaeli",
    10: "Antalya",
}

BASE_URL = "https://www.tjk.org/TR/YarisSever/Info/Sehir/GunlukYarisSonuclari"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)

_thread_local = threading.local()


def get_session() -> requests.Session:
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        _thread_local.session = session
    return session


def format_duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}s {minutes}d {sec}sn"
    return f"{minutes}d {sec}sn"


def parse_money(text: str):
    if not text:
        return None

    cleaned = unescape(text)
    cleaned = cleaned.replace("₺", "").replace("TL", "")
    cleaned = cleaned.replace("â‚º", "")
    cleaned = cleaned.replace("\xa0", " ").strip()
    cleaned = cleaned.replace(" ", "")
    cleaned = cleaned.replace(".", "").replace(",", ".")
    cleaned = re.sub(r"[^0-9.]", "", cleaned)

    if not cleaned:
        return None

    try:
        return float(cleaned)
    except ValueError:
        return None


def is_altili_label(label: str) -> bool:
    normalized = unescape(label).upper().replace("İ", "I").replace("Ä°", "I")
    normalized = re.sub(r"\s+", " ", normalized)
    return "6" in normalized and "GANYAN" in normalized


def extract_race_summaries(soup: BeautifulSoup):
    races = []
    race_divs = soup.select("div.races-panes > div[id]")
    for idx, race_div in enumerate(race_divs, start=1):
        race_id = race_div.get("id", "")
        cfg = race_div.select_one("h3.race-config")
        cfg_text = cfg.get_text(" ", strip=True) if cfg else ""

        winner_name = ""
        winner_ganyan = ""

        for row in race_div.select("tbody tr"):
            pos_cell = row.select_one("td[class*='-SONUCNO']")
            pos = pos_cell.get_text(" ", strip=True) if pos_cell else ""
            if pos != "1":
                continue

            horse_cell = row.select_one("td[class*='-AtAdi3'] a")
            gny_cell = row.select_one("td[class*='-Gny']")
            if horse_cell:
                winner_name = horse_cell.get_text(" ", strip=True).split("(")[0].strip()
            if gny_cell:
                winner_ganyan = gny_cell.get_text(" ", strip=True)
            break

        races.append(
            {
                "race_index": idx,
                "race_id": race_id,
                "config": cfg_text,
                "winner": winner_name,
                "winner_ganyan": winner_ganyan,
            }
        )

    return races


def extract_altili_cards(soup: BeautifulSoup):
    cards = []
    for h4 in soup.select("div.bahisSonucCard h4"):
        spans = [span.get_text(" ", strip=True) for span in h4.select("span")]
        if not spans:
            continue

        label = spans[0]
        if not is_altili_label(label):
            continue

        combination = spans[1] if len(spans) > 1 else ""
        amount_text = spans[-1] if len(spans) > 1 else ""

        cards.append(
            {
                "label": unescape(label),
                "combination": unescape(combination),
                "amount_text": unescape(amount_text),
                "amount": parse_money(amount_text),
            }
        )

    return cards


def fetch_city_day(city_id: int, city_name: str, date_obj: dt.date):
    params = {
        "SehirId": city_id,
        "QueryParameter_Tarih": date_obj.strftime("%d/%m/%Y"),
        "SehirAdi": city_name,
    }

    session = get_session()

    try:
        response = session.get(BASE_URL, params=params, timeout=30)
    except requests.RequestException:
        return None

    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "lxml")
    if not soup.select_one("div.races-panes"):
        return None

    altili_cards = extract_altili_cards(soup)
    if not altili_cards:
        return None

    return {
        "date": date_obj.isoformat(),
        "city": city_name,
        "city_id": city_id,
        "altili": altili_cards,
        "races": extract_race_summaries(soup),
        "url": response.url,
    }


def date_range(start_date: dt.date, end_date: dt.date):
    current = start_date
    one_day = dt.timedelta(days=1)
    while current <= end_date:
        yield current
        current += one_day


def main():
    parser = argparse.ArgumentParser(
        description="Belirli tarih araliginda max tutara gore altili ganyanlari listeler"
    )
    parser.add_argument("--start", default="2026-01-07", help="Baslangic tarihi (YYYY-MM-DD)")
    parser.add_argument("--end", default=dt.date.today().isoformat(), help="Bitis tarihi (YYYY-MM-DD)")
    parser.add_argument("--max", type=float, default=1250.0, help="Maksimum altili tutari")
    parser.add_argument("--out-json", default="altili_1250_ve_alti_6ocak_sonrasi.json")
    parser.add_argument("--out-csv", default="altili_1250_ve_alti_6ocak_sonrasi.csv")
    parser.add_argument("--log-every", type=int, default=1, help="Kac gunde bir ilerleme logu basilsin")
    parser.add_argument("--workers", type=int, default=16, help="Paralel istek sayisi")
    parser.add_argument("--verbose", action="store_true", help="Eslesmeleri anlik logla")
    args = parser.parse_args()

    start_date = dt.date.fromisoformat(args.start)
    end_date = dt.date.fromisoformat(args.end)
    if end_date < start_date:
        raise ValueError("Bitis tarihi baslangic tarihinden kucuk olamaz")

    total_days = (end_date - start_date).days + 1
    total_requests = total_days * len(CITIES)

    print("=" * 70, flush=True)
    print(f"Tarih araligi: {start_date} -> {end_date}", flush=True)
    print(f"Sehir sayisi: {len(CITIES)} | Tahmini toplam istek: {total_requests}", flush=True)
    print(f"Filtre: altili <= {args.max} TL | Workers: {args.workers}", flush=True)
    print("=" * 70, flush=True)

    tasks = []
    for day in date_range(start_date, end_date):
        for city_id, city_name in CITIES.items():
            tasks.append((day, city_id, city_name))

    results = []
    completed = 0
    start_ts = time.time()
    log_every_requests = max(1, args.log_every * len(CITIES))

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(fetch_city_day, city_id, city_name, day): (day, city_name)
            for day, city_id, city_name in tasks
        }

        for future in as_completed(futures):
            completed += 1
            payload = future.result()
            day, _ = futures[future]

            if payload:
                matching = [
                    x for x in payload["altili"] if x["amount"] is not None and x["amount"] <= args.max
                ]

                for match in matching:
                    row = {
                        "date": payload["date"],
                        "city": payload["city"],
                        "city_id": payload["city_id"],
                        "label": match["label"],
                        "combination": match["combination"],
                        "amount": match["amount"],
                        "amount_text": match["amount_text"],
                        "race_count": len(payload["races"]),
                        "races": payload["races"],
                        "url": payload["url"],
                    }
                    results.append(row)

                    if args.verbose:
                        print(
                            f"[ESLESME] {row['date']} {row['city']} | {row['amount_text']} | "
                            f"Kombinasyon: {row['combination']} | Kosu: {row['race_count']}",
                            flush=True,
                        )

            if completed % log_every_requests == 0 or completed == total_requests:
                elapsed = time.time() - start_ts
                done_ratio = completed / total_requests if total_requests else 1.0
                eta_seconds = (elapsed / done_ratio - elapsed) if done_ratio > 0 else 0
                approx_day = min(total_days, int((completed / len(CITIES))))
                print(
                    f"[ILERLEME] Gun ~{approx_day}/{total_days} ({day.isoformat()}) | "
                    f"Istek {completed}/{total_requests} ({done_ratio * 100:.1f}%) | "
                    f"Toplam eslesme: {len(results)} | "
                    f"Sure: {format_duration(elapsed)} | ETA: {format_duration(eta_seconds)}",
                    flush=True,
                )

    results.sort(key=lambda item: (item["date"], item["city"], item["label"]))

    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with open(args.out_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "date",
                "city",
                "city_id",
                "label",
                "combination",
                "amount",
                "amount_text",
                "race_count",
                "url",
                "races_json",
            ],
        )
        writer.writeheader()
        for row in results:
            writer.writerow(
                {
                    "date": row["date"],
                    "city": row["city"],
                    "city_id": row["city_id"],
                    "label": row["label"],
                    "combination": row["combination"],
                    "amount": row["amount"],
                    "amount_text": row["amount_text"],
                    "race_count": row["race_count"],
                    "url": row["url"],
                    "races_json": json.dumps(row["races"], ensure_ascii=False),
                }
            )

    elapsed = time.time() - start_ts
    print("=" * 70, flush=True)
    print(f"Tarih araligi: {start_date} -> {end_date}", flush=True)
    print(f"Maks tutar: {args.max} TL", flush=True)
    print(f"Bulunan altili sayisi: {len(results)}", flush=True)
    print(f"JSON: {args.out_json}", flush=True)
    print(f"CSV : {args.out_csv}", flush=True)
    print(f"Sure: {elapsed:.1f} sn", flush=True)
    print("=" * 70, flush=True)

    for row in results[:20]:
        print(
            f"{row['date']} | {row['city']:<10} | {row['label']:<16} | "
            f"{row['amount_text']:<12} | Kombinasyon: {row['combination']} | Kosu: {row['race_count']}",
            flush=True,
        )


if __name__ == "__main__":
    main()
