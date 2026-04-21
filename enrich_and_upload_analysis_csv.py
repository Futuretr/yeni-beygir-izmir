from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Analiz CSV dosyasindaki atlari cikarir, opsiyonel olarak web kaynagindan "
            "(ornegin Yenibeygir) stil/bilgi toplar, ciktiyi CSV olarak yazar ve istenirse siteye yukler."
        )
    )
    p.add_argument("--input", required=True, help="Girdi analiz CSV yolu")
    p.add_argument("--output", required=True, help="Cikti CSV yolu")
    p.add_argument(
        "--source-url-template",
        default="https://www.yenibeygir.com/arama?q={horse_name}",
        help=(
            "At bilgisi cekmek icin URL template. Kullanilabilir alanlar: {horse_name}, {horse_slug}. "
            "Ornek: https://www.yenibeygir.com/arama?q={horse_name}"
        ),
    )
    p.add_argument(
        "--skip-source-fetch",
        action="store_true",
        help="Kaynak siteden bilgi cekme adimini atla.",
    )
    p.add_argument(
        "--upload-url",
        help="Opsiyonel: cikti CSV dosyasini yuklemek icin endpoint URL",
    )
    p.add_argument(
        "--upload-field-name",
        default="file",
        help="Upload icin multipart alan adi (varsayilan: file)",
    )
    p.add_argument(
        "--upload-token",
        help="Opsiyonel bearer token. Verilirse Authorization basligi eklenir.",
    )
    p.add_argument(
        "--styles-report",
        help="Opsiyonel: kaynak sayfadan yakalanan stil siniflarini JSON olarak kaydet.",
    )
    p.add_argument(
        "--meeting-date",
        help="Opsiyonel: YYYY-MM-DD formatinda yaris tarihi. Direkt stiller sayfalari icin kullanilir.",
    )
    p.add_argument(
        "--meeting-city",
        help="Opsiyonel: Yenibeygir sehir slug'i. Ornek: elazig, izmir, diyarbakir",
    )
    p.add_argument(
        "--direct-style-pages",
        action="store_true",
        help="Yenibeygir arama sayfasi yerine /tarih/sehir/kosu/stiller sayfalarindan cek.",
    )
    p.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="HTTP timeout saniye",
    )
    return p.parse_args()


@dataclass
class HorseRow:
    horse_name: str
    race_label: str
    score_raw: str
    score: float | None
    last_distance: int | None
    last_surface: str
    last_weight: float | None
    current_weight: float | None
    last_hipodrom: str
    source_status: str = "not_fetched"
    source_url: str = ""
    extracted_style: str = ""
    extracted_notes: str = ""
    style_bucket_1: str = ""
    style_bucket_2: str = ""
    style_bucket_3: str = ""
    style_bucket_4: str = ""
    style_sample_size: int | None = None
    dominant_style_bucket: str = ""


def to_float(v: str | None) -> float | None:
    if v is None:
        return None
    s = str(v).strip().replace(",", ".")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def to_int(v: str | None) -> int | None:
    n = to_float(v)
    if n is None:
        return None
    return int(round(n))


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return ascii_text


def clean_html_text(html: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(text or ""))
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    ascii_text = ascii_text.upper().replace("İ", "I")
    ascii_text = re.sub(r"[^A-Z0-9]+", " ", ascii_text)
    return re.sub(r"\s+", " ", ascii_text).strip()


def get_value(raw: dict[str, Any], *keys: str) -> str:
    for key in keys:
        if key in raw and raw.get(key) is not None:
            return str(raw.get(key)).strip()

    normalized_lookup = {normalize_text(k): v for k, v in raw.items()}
    for key in keys:
        normalized_key = normalize_text(key)
        if normalized_key in normalized_lookup and normalized_lookup[normalized_key] is not None:
            return str(normalized_lookup[normalized_key]).strip()

    return ""


def extract_style_label(html: str) -> str:
    text = clean_html_text(html)

    patterns = [
        r"(?:Kosu\s*Stili|Kosu\s*Tarzi|Stili|Stil|Running\s*Style)\s*[:\-]\s*([A-Za-zCcgiiIsuUnrto\u00c7\u00d6\u015e\u0130\u011f\u00fc\- ]{2,40})",
        r"\b(One\s*giden|Lider|On\s*grup|Oncu|Sprinter|Duzcu|Beklemeci|Stayer|Presci|Tempolu)\b",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.I)
        if m:
            return m.group(1).strip()
    return ""


def extract_style_classes(html: str) -> list[str]:
    classes: list[str] = []
    for m in re.finditer(r'class\s*=\s*"([^"]+)"', html, flags=re.I):
        values = [part.strip() for part in m.group(1).split() if part.strip()]
        for val in values:
            low = val.lower()
            if "style" in low or "stil" in low:
                classes.append(val)
    seen: set[str] = set()
    out: list[str] = []
    for val in classes:
        if val not in seen:
            out.append(val)
            seen.add(val)
    return out


def fetch_html(url: str, timeout: int) -> str:
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


def build_source_url(template: str, horse_name: str) -> str:
    return template.format(
        horse_name=quote_plus(horse_name),
        horse_slug=slugify(horse_name),
    )


def parse_input_rows(input_path: Path) -> list[HorseRow]:
    rows: list[HorseRow] = []
    current_race = ""

    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            horse_name = get_value(raw, "At İsmi", "At Ismi", "At Ä°smi")
            race_label = get_value(raw, "Koşu", "Kosu", "KoÅŸu")
            output_raw = get_value(raw, "Çıktı", "Cikti", "Ã‡Ä±ktÄ±")

            if race_label and not horse_name:
                current_race = race_label
                continue

            if not horse_name:
                continue

            if output_raw.lower() == "geçersiz":
                continue

            rows.append(
                HorseRow(
                    horse_name=horse_name,
                    race_label=current_race,
                    score_raw=output_raw,
                    score=to_float(output_raw),
                    last_distance=to_int(get_value(raw, "Son Mesafe")),
                    last_surface=get_value(raw, "Son Pist"),
                    last_weight=to_float(get_value(raw, "Son Kilo")),
                    current_weight=to_float(get_value(raw, "Kilo")),
                    last_hipodrom=get_value(raw, "Son Hipodrom"),
                )
            )

    return rows


def parse_race_number(race_label: str) -> int | None:
    match = re.search(r"(\d+)", race_label or "")
    if not match:
        return None
    return int(match.group(1))


def build_direct_style_url(meeting_date: str, meeting_city: str, race_number: int) -> str:
    year, month, day = meeting_date.split("-")
    return f"https://yenibeygir.com/{day}-{month}-{year}/{meeting_city}/{race_number}/stiller"


def parse_style_percentages(style_cell: Any) -> list[str]:
    percentages: list[str] = []
    style_container = style_cell.find("div", class_="AtStyle") or style_cell
    for block in style_container.find_all("div", recursive=False)[:4]:
        title = (block.get("title") or "").strip()
        match = re.search(r"\((\d+)%\)", title)
        percentages.append(match.group(1) if match else "")
    while len(percentages) < 4:
        percentages.append("")
    return percentages


def enrich_from_direct_style_pages(
    rows: list[HorseRow],
    meeting_date: str,
    meeting_city: str,
    timeout: int,
) -> dict[str, Any]:
    report: dict[str, Any] = {"pages": {}, "errors": {}}
    rows_by_race: dict[int, list[HorseRow]] = {}

    for row in rows:
        race_number = parse_race_number(row.race_label)
        if race_number is None:
            row.source_status = "error"
            row.extracted_notes = "race_number_not_found"
            report["errors"][row.horse_name] = row.extracted_notes
            continue
        rows_by_race.setdefault(race_number, []).append(row)

    for race_number, race_rows in rows_by_race.items():
        url = build_direct_style_url(meeting_date, meeting_city, race_number)
        report["pages"][str(race_number)] = url
        row_map = {(race_number, normalize_text(row.horse_name)): row for row in race_rows}

        try:
            html = fetch_html(url, timeout=timeout)
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("table")
            if table is None:
                raise ValueError("style_table_not_found")

            matched_keys: set[tuple[int, str]] = set()
            for tr in table.find_all("tr")[1:]:
                tds = tr.find_all("td")
                if len(tds) < 7:
                    continue

                horse_name = tds[1].get_text(" ", strip=True)
                style_key = (race_number, normalize_text(horse_name))
                row = row_map.get(style_key)
                if row is None:
                    report["errors"][f"{race_number}:{horse_name}"] = "horse_not_in_input_csv"
                    continue

                style_values = parse_style_percentages(tds[5])
                numeric_values = [(idx, int(value) if value else -1) for idx, value in enumerate(style_values, start=1)]
                dominant_index = max(numeric_values, key=lambda item: item[1])[0]

                row.source_status = "ok"
                row.source_url = url
                row.style_bucket_1 = style_values[0]
                row.style_bucket_2 = style_values[1]
                row.style_bucket_3 = style_values[2]
                row.style_bucket_4 = style_values[3]
                row.style_sample_size = to_int(tds[6].get_text(" ", strip=True))
                row.dominant_style_bucket = f"stil_{dominant_index}"
                row.extracted_style = " / ".join(
                    f"stil_{idx}:{value}%"
                    for idx, value in enumerate(style_values, start=1)
                    if value != ""
                )
                matched_keys.add(style_key)

            for style_key, row in row_map.items():
                if style_key in matched_keys:
                    continue
                row.source_status = "error"
                row.source_url = url
                row.extracted_notes = "horse_not_found_on_style_page"
                report["errors"][f"{race_number}:{row.horse_name}"] = row.extracted_notes

        except Exception as exc:
            for row in race_rows:
                row.source_status = "error"
                row.source_url = url
                row.extracted_notes = str(exc)[:250]
            report["errors"][f"race_{race_number}"] = str(exc)[:250]

    return report


def enrich_from_source(
    rows: list[HorseRow],
    source_template: str,
    timeout: int,
) -> dict[str, Any]:
    report: dict[str, Any] = {"classes_by_horse": {}, "errors": {}}

    for row in rows:
        source_url = build_source_url(source_template, row.horse_name)
        row.source_url = source_url

        try:
            html = fetch_html(source_url, timeout=timeout)
            row.source_status = "ok"
            row.extracted_style = extract_style_label(html)
            classes = extract_style_classes(html)
            report["classes_by_horse"][row.horse_name] = classes
            if not row.extracted_style and classes:
                row.extracted_notes = "style_class_found_but_label_missing"
        except Exception as exc:
            row.source_status = "error"
            row.extracted_notes = str(exc)[:250]
            report["errors"][row.horse_name] = row.extracted_notes

    return report


def save_output_csv(rows: list[HorseRow], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "at_ismi",
        "kosu",
        "cikti",
        "son_mesafe",
        "son_pist",
        "son_kilo",
        "kilo",
        "son_hipodrom",
        "kaynak_durum",
        "kaynak_url",
        "stil",
        "stil_1_yuzde",
        "stil_2_yuzde",
        "stil_3_yuzde",
        "stil_4_yuzde",
        "stil_veri_sayisi",
        "baskin_stil",
        "not",
    ]

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "at_ismi": row.horse_name,
                    "kosu": row.race_label,
                    "cikti": row.score_raw,
                    "son_mesafe": row.last_distance if row.last_distance is not None else "",
                    "son_pist": row.last_surface,
                    "son_kilo": row.last_weight if row.last_weight is not None else "",
                    "kilo": row.current_weight if row.current_weight is not None else "",
                    "son_hipodrom": row.last_hipodrom,
                    "kaynak_durum": row.source_status,
                    "kaynak_url": row.source_url,
                    "stil": row.extracted_style,
                    "stil_1_yuzde": row.style_bucket_1,
                    "stil_2_yuzde": row.style_bucket_2,
                    "stil_3_yuzde": row.style_bucket_3,
                    "stil_4_yuzde": row.style_bucket_4,
                    "stil_veri_sayisi": row.style_sample_size if row.style_sample_size is not None else "",
                    "baskin_stil": row.dominant_style_bucket,
                    "not": row.extracted_notes,
                }
            )


def upload_file(
    upload_url: str,
    output_path: Path,
    field_name: str,
    token: str | None,
    timeout: int,
) -> tuple[int, str]:
    boundary = "----HorseRacingBoundary7MA4YWxkTrZu0gW"
    file_name = output_path.name
    file_bytes = output_path.read_bytes()

    head = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"{field_name}\"; filename=\"{file_name}\"\r\n"
        "Content-Type: text/csv\r\n\r\n"
    ).encode("utf-8")
    tail = f"\r\n--{boundary}--\r\n".encode("utf-8")
    body = head + file_bytes + tail

    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Accept": "application/json, text/plain, */*",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = Request(upload_url, data=body, headers=headers, method="POST")
    with urlopen(req, timeout=timeout) as resp:
        text = resp.read().decode("utf-8", "ignore")
        return resp.status, text


def main() -> None:
    args = parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    horses = parse_input_rows(input_path)
    if not horses:
        raise SystemExit("Gecerli at satiri bulunamadi.")

    style_report: dict[str, Any] = {"classes_by_horse": {}, "errors": {}}
    if not args.skip_source_fetch:
        if args.direct_style_pages:
            if not args.meeting_date or not args.meeting_city:
                raise SystemExit("--direct-style-pages icin --meeting-date ve --meeting-city gerekli.")
            style_report = enrich_from_direct_style_pages(
                horses,
                args.meeting_date,
                args.meeting_city,
                args.timeout,
            )
        else:
            style_report = enrich_from_source(horses, args.source_url_template, args.timeout)

    save_output_csv(horses, output_path)
    print(f"CSV yazildi: {output_path} | satir: {len(horses)}")

    if args.styles_report:
        styles_report_path = Path(args.styles_report)
        styles_report_path.parent.mkdir(parents=True, exist_ok=True)
        styles_report_path.write_text(
            json.dumps(style_report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Stil raporu yazildi: {styles_report_path}")

    if args.upload_url:
        status, response_text = upload_file(
            args.upload_url,
            output_path,
            args.upload_field_name,
            args.upload_token,
            args.timeout,
        )
        print(f"Upload tamamlandi. HTTP {status}")
        print(response_text[:2000])


if __name__ == "__main__":
    main()
