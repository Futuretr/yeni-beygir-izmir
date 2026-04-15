from __future__ import annotations

import argparse
import csv
import html
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from typing import List
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


@dataclass
class HorseRow:
    number: str
    name: str
    horse_url: str
    horse_id: str


@dataclass
class HorseStyle:
    style_text: str
    style_1: str
    style_2: str
    style_3: str
    style_4: str
    prev_track_condition: str
    prev_over_5s: str
    prev_time_diff_sec: str


RESULT_CACHE: dict[str, tuple[float | None, dict[str, float]]] = {}
RESULT_CACHE_LOCK = threading.Lock()


def parse_percent_from_style(title_text: str) -> float:
    match = re.search(r"\(([\d.,]+)%\)", title_text or "")
    if not match:
        return 0.0
    raw = match.group(1).replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return 0.0


def bucket_to_label(idx: int) -> str:
    # Tooltip'e gore: 0=arkada, 1=arka grup, 2=on grup, 3=onde
    if idx == 0:
        return "Sprinter"
    if idx == 1:
        return "Orta Grup"
    if idx == 2:
        return "Takipçi"
    return "Önde Kaçan"


def classify_style(style: HorseStyle) -> tuple[str, str, str]:
    # Tooltip'e gore soldan saga:
    # 1) en arkada, 2) arka grup, 3) on grup, 4) en onde
    p = [
        parse_percent_from_style(style.style_1),
        parse_percent_from_style(style.style_2),
        parse_percent_from_style(style.style_3),
        parse_percent_from_style(style.style_4),
    ]

    if sum(p) == 0:
        return "Bilinmiyor", "", "Yaris stili verisi bulunamadi."

    sorted_idx = sorted(range(4), key=lambda i: p[i], reverse=True)
    top1, top2 = sorted_idx[0], sorted_idx[1]

    # Sadece 4 kutucuk da birbirine cok yakin ise karakter net degil.
    top_vals = sorted(p, reverse=True)
    max_p = top_vals[0]
    close_to_max = sum(1 for v in p if max_p - v <= 12 and v >= 20)
    if close_to_max == 4:
        dist = (
            f"Dagilim: arkada %{p[0]:.0f}, arka-grup %{p[1]:.0f}, "
            f"on-grup %{p[2]:.0f}, onde %{p[3]:.0f}."
        )
        return "Karakteri Belli Değil", "", f"4 stil kutucugu birbirine cok yakin. {dist}"

    label_1 = bucket_to_label(top1)
    label_2 = ""

    # Duruma gore ikinci stil:
    # - ilk iki oran birbirine yakin ise (fark <= 12 puan), veya
    # - ikinci oranin etkisi yuksekse (>= %30)
    if (p[top1] - p[top2] <= 12) or (p[top2] >= 30):
        cand = bucket_to_label(top2)
        if cand != label_1:
            label_2 = cand

    desc = "Genel olarak baskin stiline gore siniflandirildi."
    if label_2:
        desc = "Karma stil: iki farkli kosu profili belirgin gorunuyor."

    dist = f"Dagilim: arkada %{p[0]:.0f}, arka-grup %{p[1]:.0f}, on-grup %{p[2]:.0f}, onde %{p[3]:.0f}."
    return label_1, label_2, f"{desc} {dist}"


def fetch_html(url: str, timeout: int = 25) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as resp:
        data = resp.read().decode("utf-8", "ignore")
    return data


def parse_race_time_to_sec(value: str) -> float | None:
    text = (value or "").strip()
    if not text:
        return None
    m = re.search(r"(\d+)\.(\d{1,2})\.(\d{1,2})", text)
    if m:
        minute = int(m.group(1))
        second = int(m.group(2))
        centi = int(m.group(3))
        return minute * 60 + second + centi / 100.0
    return None


def parse_result_page_times(result_url: str) -> tuple[float | None, dict[str, float]]:
    with RESULT_CACHE_LOCK:
        cached = RESULT_CACHE.get(result_url)
    if cached is not None:
        return cached

    html_text = fetch_html(result_url)
    soup = BeautifulSoup(html_text, "lxml")

    winner_time: float | None = None
    horse_times: dict[str, float] = {}

    table = None
    for t in soup.select("table"):
        headers = [th.get_text(" ", strip=True) for th in t.select("th")]
        if "Derece" in headers and "At İsmi" in headers:
            table = t
            break
    if table is None:
        out = (None, {})
        with RESULT_CACHE_LOCK:
            RESULT_CACHE[result_url] = out
        return out

    headers = [th.get_text(" ", strip=True) for th in table.select("thead th")]
    derece_idx = headers.index("Derece")

    first_row = table.select_one("tbody tr")
    if first_row:
        tds = first_row.select("td")
        if derece_idx < len(tds):
            winner_time = parse_race_time_to_sec(tds[derece_idx].get_text(" ", strip=True))

    for tr in table.select("tbody tr"):
        a = tr.select_one('a[href*="/at/"]')
        if not a:
            continue
        m = re.search(r"/at/(\d+)/", a.get("href", ""))
        if not m:
            continue
        horse_id = m.group(1)
        tds = tr.select("td")
        if derece_idx >= len(tds):
            continue
        t = parse_race_time_to_sec(tds[derece_idx].get_text(" ", strip=True))
        if t is not None:
            horse_times[horse_id] = t

    out = (winner_time, horse_times)
    with RESULT_CACHE_LOCK:
        RESULT_CACHE[result_url] = out
    return out


def extract_prev_race_info(soup: BeautifulSoup, horse_url: str, horse_id: str) -> tuple[str, str, str]:
    rows = soup.select("table.at_Yarislar tbody tr")
    if not rows:
        return "", "", ""

    prev_row = None
    prev_date = None
    for tr in rows:
        first_cell = tr.select_one("td")
        date_text = first_cell.get_text(" ", strip=True) if first_cell else ""
        if not date_text or date_text.lower() == "bugün":
            continue

        mdate = re.match(r"(\d{2}\.\d{2}\.\d{4})", date_text)
        if not mdate:
            continue
        try:
            race_date = datetime.strptime(mdate.group(1), "%d.%m.%Y").date()
        except ValueError:
            continue

        tds = tr.select("td")
        if len(tds) < 7:
            continue

        derece_text = tds[6].get_text(" ", strip=True)
        if parse_race_time_to_sec(derece_text) is None:
            # Kosmaz / derece yok satirlarini ele.
            continue

        # En yeni tamamlanmis kosuyu sec.
        if prev_row is None or (prev_date is not None and race_date > prev_date):
            prev_row = tr
            prev_date = race_date

    if prev_row is None:
        return "", "", ""

    tds = prev_row.select("td")
    if len(tds) < 7:
        return "", "", ""

    msf_pist = tds[4].get_text(" ", strip=True)
    cond_parts: list[str] = []
    paren_parts = re.findall(r"\(([^)]+)\)", msf_pist)
    keep_tokens = (
        "nem",
        "sulu",
        "isl",
        "ısl",
        "hafif",
        "agir",
        "ağır",
        "yumusak",
        "yumuşak",
    )
    for p in paren_parts:
        pl = p.lower()
        if any(tok in pl for tok in keep_tokens):
            cond_parts.append(p.strip())
    # Cim pistte sayisal deger (or. 5,3) geciyorsa agir/hafif yorumla.
    if "çim" in msf_pist.lower() or "cim" in msf_pist.lower():
        for p in paren_parts:
            mnum = re.search(r"(\d+[.,]\d+)", p)
            if not mnum:
                continue
            val = float(mnum.group(1).replace(",", "."))
            if val >= 5.0:
                cond_parts.append(f"Ağır Çim ({mnum.group(1)})")
            elif val <= 3.7:
                cond_parts.append(f"Hafif Çim ({mnum.group(1)})")
            break
    # Bazi satirlarda kosul parantezsiz geciyor olabilir.
    msf_low = msf_pist.lower()
    for direct in ("ağır", "agir", "hafif", "yumuşak", "yumusak", "nem", "sulu", "ısl", "islak"):
        if direct in msf_low and all(direct not in x.lower() for x in cond_parts):
            cond_parts.append(direct.title())
    # Tekrar eden etiketleri temizle.
    seen = set()
    uniq_parts = []
    for x in cond_parts:
        k = x.lower()
        if k in seen:
            continue
        seen.add(k)
        uniq_parts.append(x)
    cond = " / ".join(uniq_parts)

    horse_time = parse_race_time_to_sec(tds[6].get_text(" ", strip=True))
    a = tds[0].select_one('a[href*="sonuclar"]')
    if not a:
        return cond, "", ""

    result_url = urljoin(horse_url, a.get("href", ""))
    winner_time, horse_times = parse_result_page_times(result_url)
    my_time = horse_times.get(horse_id, horse_time)

    if winner_time is None or my_time is None:
        return cond, "", ""

    diff = my_time - winner_time
    over_5 = "X" if diff >= 5.0 else ""
    return cond, over_5, f"{diff:.2f}"


def parse_horses_from_race_page(race_url: str) -> List[HorseRow]:
    page = fetch_html(race_url)
    soup = BeautifulSoup(page, "lxml")

    rows: List[HorseRow] = []
    seen_ids = set()

    for tr in soup.select("tr"):
        no_cell = tr.select_one("td.atno")
        name_link = tr.select_one('a.atisimlink[href^="/at/"]')
        if not no_cell or not name_link:
            continue

        horse_rel = name_link.get("href", "").strip()
        horse_url = urljoin(race_url, horse_rel)

        match = re.search(r"/at/(\d+)/", horse_rel)
        if not match:
            continue
        horse_id = match.group(1)

        if horse_id in seen_ids:
            continue
        seen_ids.add(horse_id)

        rows.append(
            HorseRow(
                number=no_cell.get_text(" ", strip=True),
                name=html.unescape(name_link.get_text(" ", strip=True)),
                horse_url=horse_url,
                horse_id=horse_id,
            )
        )

    return rows


def parse_style_from_horse_page(horse_url: str) -> HorseStyle:
    page = fetch_html(horse_url)
    soup = BeautifulSoup(page, "lxml")

    style_box = soup.select_one("div.AtStyle")
    horse_id_match = re.search(r"/at/(\d+)/", horse_url)
    horse_id = horse_id_match.group(1) if horse_id_match else ""
    prev_cond, prev_over_5s, prev_diff_sec = extract_prev_race_info(soup, horse_url, horse_id)

    if style_box is None:
        return HorseStyle(
            style_text="",
            style_1="",
            style_2="",
            style_3="",
            style_4="",
            prev_track_condition=prev_cond,
            prev_over_5s=prev_over_5s,
            prev_time_diff_sec=prev_diff_sec,
        )

    titles = []
    for div in style_box.select(":scope > div"):
        title = (div.get("title") or "").strip()
        titles.append(title)

    while len(titles) < 4:
        titles.append("")

    style_text = " | ".join([t for t in titles if t])
    return HorseStyle(
        style_text=style_text,
        style_1=titles[0],
        style_2=titles[1],
        style_3=titles[2],
        style_4=titles[3],
        prev_track_condition=prev_cond,
        prev_over_5s=prev_over_5s,
        prev_time_diff_sec=prev_diff_sec,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Yenibeygir genel sayfasından at no, isim ve yarış stili bilgilerini çeker."
    )
    parser.add_argument(
        "--race-url",
        default="https://yenibeygir.com/12-04-2026/adana",
        help="Genel yarış sayfası URL'si",
    )
    parser.add_argument(
        "--output",
        default="yenibeygir_atlar.csv",
        help="Çıktı CSV dosya yolu",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=10,
        help="At detay sayfaları için paralel worker sayısı",
    )
    args = parser.parse_args()

    print(f"[1/3] Genel sayfa okunuyor: {args.race_url}")
    horses = parse_horses_from_race_page(args.race_url)

    if not horses:
        print("At bulunamadı. URL'i kontrol et.")
        return 1

    print(f"[2/3] {len(horses)} at bulundu. Yarış stili bilgileri çekiliyor...")
    styles_by_id = {}

    with ThreadPoolExecutor(max_workers=max(1, args.max_workers)) as ex:
        future_map = {ex.submit(parse_style_from_horse_page, h.horse_url): h for h in horses}

        done_count = 0
        for fut in as_completed(future_map):
            horse = future_map[fut]
            try:
                styles_by_id[horse.horse_id] = fut.result()
            except Exception as exc:
                print(f"Uyarı: {horse.name} için stil alınamadı: {exc}")
                styles_by_id[horse.horse_id] = HorseStyle("", "", "", "", "", "", "", "")

            done_count += 1
            if done_count % 20 == 0 or done_count == len(horses):
                print(f"  - Tamamlanan: {done_count}/{len(horses)}")

    print(f"[3/3] CSV yazılıyor: {args.output}")
    with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "at_no",
                "at_adi",
                "stil_etiketi",
                "stil_etiketi_2",
                "stil_aciklama",
                "yaris_stili",
                "yaris_stili_1",
                "yaris_stili_2",
                "yaris_stili_3",
                "yaris_stili_4",
                "son_kosu_zemin_durumu",
                "birinciden_5sn_fazla",
                "birinciden_fark_sn",
                "at_profili",
                "at_id",
            ],
        )
        writer.writeheader()

        for h in horses:
            st = styles_by_id.get(h.horse_id, HorseStyle("", "", "", "", "", "", "", ""))
            style_label, style_label_2, style_desc = classify_style(st)
            writer.writerow(
                {
                    "at_no": h.number,
                    "at_adi": h.name,
                    "stil_etiketi": style_label,
                    "stil_etiketi_2": style_label_2,
                    "stil_aciklama": style_desc,
                    "yaris_stili": st.style_text,
                    "yaris_stili_1": st.style_1,
                    "yaris_stili_2": st.style_2,
                    "yaris_stili_3": st.style_3,
                    "yaris_stili_4": st.style_4,
                    "son_kosu_zemin_durumu": st.prev_track_condition,
                    "birinciden_5sn_fazla": st.prev_over_5s,
                    "birinciden_fark_sn": st.prev_time_diff_sec,
                    "at_profili": h.horse_url,
                    "at_id": h.horse_id,
                }
            )

    print("Bitti.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
