from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from pathlib import Path
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


STYLE_LABELS = {
    "stil_1": "Sprinter",
    "stil_2": "Orta Grup",
    "stil_3": "Takipci",
    "stil_4": "Onde Kacan",
}

GROUP_1_SARTLI = {1, 2, 3, 4, 19}
GROUP_1_HANDIKAP = {13, 14, 15, 16}
GROUP_1_SATIS = {1, 2, 3, 4}

GROUP_2_SARTLI = {5, 6, 7}
GROUP_2_HANDIKAP = {17, 21, 22, 24}
GROUP_2_GRUP = {1, 2, 3}
GROUP_2_KV = {8, 9, 10, 21, 22, 23, 24}
GROUP_2_ACIK = {2, 3}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def esc(text: str) -> str:
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def to_float(value: str) -> float:
    try:
        return float(str(value or "").replace(",", "."))
    except ValueError:
        return 9999.0


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(text or ""))
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    ascii_text = ascii_text.upper().replace("İ", "I")
    ascii_text = re.sub(r"[^A-Z0-9]+", " ", ascii_text)
    return re.sub(r"\s+", " ", ascii_text).strip()


def fetch_html(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "ignore")


def parse_weight_value(raw_text: str) -> str:
    text = str(raw_text or "").strip().replace(" ", "")
    if not text:
        return ""
    match = re.match(r"(\d+(?:[.,]\d+)?)", text)
    if not match:
        return ""
    return match.group(1).replace(",", ".")


def classify_race_group(raw_text: str) -> tuple[int | None, str]:
    text = normalize_text(raw_text)

    if "MAIDEN" in text:
        return 1, "Maiden"

    match = re.search(r"SATIS\s*(\d+)", text)
    if match:
        level = int(match.group(1))
        if level in GROUP_1_SATIS:
            return 1, f"Satis {level}"

    match = re.search(r"(?:SARTLI|SRT)\s*(\d+)", text)
    if match:
        level = int(match.group(1))
        if level in GROUP_1_SARTLI:
            return 1, f"Sartli {level}"
        if level in GROUP_2_SARTLI:
            return 2, f"Sartli {level}"

    match = re.search(r"(?:HANDIKAP|HND)\s*(\d+)", text)
    if match:
        level = int(match.group(1))
        if level in GROUP_1_HANDIKAP:
            return 1, f"Handikap {level}"
        if level in GROUP_2_HANDIKAP:
            return 2, f"Handikap {level}"

    match = re.search(r"\bGRUP\s*(\d+)", text)
    if match:
        level = int(match.group(1))
        if level in GROUP_2_GRUP:
            return 2, f"Grup {level}"

    match = re.search(r"\bKV\s*(\d+)", text)
    if match:
        level = int(match.group(1))
        if level in GROUP_2_KV:
            return 2, f"KV {level}"

    match = re.search(r"ACIK\s*(\d+)", text)
    if match:
        level = int(match.group(1))
        if level in GROUP_2_ACIK:
            return 2, f"Acik {level}"

    return None, raw_text.strip()


def extract_previous_race_info(horse_url: str) -> dict[str, str | int | None]:
    try:
        soup = BeautifulSoup(fetch_html(horse_url), "html.parser")
    except Exception:
        return {"previous_group": None, "previous_group_label": "", "previous_weight": ""}

    target_table = None
    for table in soup.find_all("table"):
        headers = [th.get_text(" ", strip=True) for th in table.find_all("th")]
        if "Tarih" in headers and "K. Cinsi" in headers:
            target_table = table
            break

    if target_table is None:
        return {"previous_group": None, "previous_group_label": "", "previous_weight": ""}

    headers = [th.get_text(" ", strip=True) for th in target_table.find_all("th")]
    kilo_idx = headers.index("Kilo") if "Kilo" in headers else -1

    for tr in target_table.find_all("tr")[1:]:
        tds = tr.find_all("td")
        if len(tds) < 3:
            continue
        date_text = tds[0].get_text(" ", strip=True)
        if not date_text or normalize_text(date_text) == "BUGUN":
            continue
        derece_text = tds[6].get_text(" ", strip=True) if len(tds) > 6 else ""
        if not derece_text:
            continue
        row_text = normalize_text(" ".join(td.get_text(" ", strip=True) for td in tds))
        if "KOSMAZ" in row_text:
            continue
        race_type = tds[2].get_text(" ", strip=True)
        previous_group, previous_group_label = classify_race_group(race_type)
        previous_weight = ""
        if kilo_idx >= 0 and kilo_idx < len(tds):
            previous_weight = parse_weight_value(tds[kilo_idx].get_text(" ", strip=True))
        return {
            "previous_group": previous_group,
            "previous_group_label": previous_group_label,
            "previous_weight": previous_weight,
        }

    return {"previous_group": None, "previous_group_label": "", "previous_weight": ""}


def build_style_context(
    city: str,
    date: str,
) -> tuple[dict[tuple[str, str], dict[str, str]], dict[str, tuple[int | None, str]]]:
    year, month, day = date.split("-")
    city_slug = normalize_text(city).lower().replace(" ", "")
    horse_map: dict[tuple[str, str], dict[str, str]] = {}
    race_group_map: dict[str, tuple[int | None, str]] = {}

    for race_no in range(1, 21):
        url = f"https://yenibeygir.com/{day}-{month}-{year}/{city_slug}/{race_no}/stiller"
        try:
            soup = BeautifulSoup(fetch_html(url), "html.parser")
        except Exception:
            continue

        table = soup.find("table")
        if table is None:
            continue

        race_label = f"{race_no}. Koşu"
        race_info = soup.find("h3")
        race_group_map[race_label] = classify_race_group(
            race_info.get_text(" ", strip=True) if race_info else ""
        )
        for tr in table.find_all("tr")[1:]:
            tds = tr.find_all("td")
            if len(tds) < 4:
                continue
            horse_no = tds[0].get_text(" ", strip=True)
            horse_link = tds[1].find("a", href=True)
            horse_name = tds[1].get_text(" ", strip=True)
            if horse_no and horse_name:
                horse_map[(race_label, normalize_text(horse_name))] = {
                    "no": horse_no,
                    "current_weight": parse_weight_value(tds[3].get_text(" ", strip=True)),
                    "url": (
                        f"https://yenibeygir.com{horse_link['href']}"
                        if horse_link and horse_link["href"].startswith("/")
                        else (horse_link["href"] if horse_link else "")
                    ),
                }

    return horse_map, race_group_map


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enriched analiz CSV'sinden tek sayfa yayin HTML'i olusturur."
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--city", required=True)
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    return parser.parse_args()


def build_style_summary(row: dict[str, str]) -> tuple[str, str]:
    values = []
    for key in ("stil_1_yuzde", "stil_2_yuzde", "stil_3_yuzde", "stil_4_yuzde"):
        raw = (row.get(key) or "").strip()
        try:
            num = int(raw)
        except ValueError:
            num = -1
        values.append((key.replace("_yuzde", ""), num))

    ranked = sorted(values, key=lambda item: item[1], reverse=True)
    first_key, first_val = ranked[0]
    first_label = STYLE_LABELS.get(first_key, first_key)

    second_label = ""
    if len(ranked) > 1:
        second_key, second_val = ranked[1]
        if second_val >= 30 or (first_val >= 0 and second_val >= 0 and first_val - second_val <= 12):
            second_label = STYLE_LABELS.get(second_key, second_key)
            if second_label == first_label:
                second_label = ""

    dist = " | ".join(
        f"{STYLE_LABELS[key.replace('_yuzde', '')]} %{row.get(key, '') or '0'}"
        for key in ("stil_1_yuzde", "stil_2_yuzde", "stil_3_yuzde", "stil_4_yuzde")
    )
    return first_label, second_label or dist


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    horse_map, race_group_map = build_style_context(args.city, args.date)
    previous_info_cache: dict[str, dict[str, str | int | None]] = {}

    races: dict[str, list[dict[str, str]]] = {}
    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            race_name = (row.get("kosu") or "").strip()
            if not race_name:
                continue
            primary_style, secondary_or_dist = build_style_summary(row)
            horse_ctx = horse_map.get((race_name, normalize_text(row.get("at_ismi", ""))), {})
            current_group, current_group_label = race_group_map.get(race_name, (None, ""))
            horse_url = horse_ctx.get("url", "")
            if horse_url and horse_url not in previous_info_cache:
                previous_info_cache[horse_url] = extract_previous_race_info(horse_url)
            previous_info = previous_info_cache.get(
                horse_url,
                {"previous_group": None, "previous_group_label": "", "previous_weight": ""},
            )
            previous_group = previous_info.get("previous_group")
            previous_group_label = str(previous_info.get("previous_group_label") or "")
            row["primary_style"] = primary_style
            row["secondary_or_dist"] = secondary_or_dist
            row["at_no"] = horse_ctx.get("no", "")
            row["site_current_weight"] = str(horse_ctx.get("current_weight", "") or "")
            row["site_previous_weight"] = str(previous_info.get("previous_weight", "") or "")
            row["group_transition"] = ""
            row["group_transition_note"] = ""
            row["group_transition_kind"] = "unknown"
            if current_group in {1, 2} and previous_group in {1, 2}:
                row["group_transition_note"] = f"{previous_group_label} -> {current_group_label}"
                if current_group != previous_group:
                    row["group_transition"] = f"{previous_group}. Grup -> {current_group}. Grup"
                    row["group_transition_kind"] = "changed"
                else:
                    row["group_transition"] = f"{current_group}. Grup (Ayni Grup)"
                    row["group_transition_kind"] = "same"
            elif current_group in {1, 2}:
                row["group_transition"] = "Onceki grup bilinmiyor"
                row["group_transition_note"] = current_group_label
                row["group_transition_kind"] = "unknown"
            races.setdefault(race_name, []).append(row)

    for race_rows in races.values():
        race_rows.sort(key=lambda item: to_float(item.get("cikti", "")))

    parts: list[str] = []
    parts.append("<!doctype html>")
    parts.append('<html lang="tr">')
    parts.append("<head>")
    parts.append('  <meta charset="utf-8" />')
    parts.append('  <meta name="viewport" content="width=device-width, initial-scale=1" />')
    parts.append(f"  <title>{esc(args.city)} {esc(args.date)} Analiz</title>")
    parts.append("  <style>")
    parts.append('    body{margin:0;font-family:"Segoe UI",Tahoma,sans-serif;background:linear-gradient(180deg,#f4f7fb 0%,#eef3fa 100%);color:#172331;}')
    parts.append("    .wrap{max-width:1100px;margin:24px auto 48px;padding:0 16px;}")
    parts.append("    .top{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;margin-bottom:18px;}")
    parts.append("    .back{display:inline-block;text-decoration:none;font-size:13px;color:#0f3d5e;border:1px solid #bfd0e1;padding:7px 12px;border-radius:999px;background:#eef4fb;}")
    parts.append("    h1{margin:0;font-size:30px;color:#102a43;}")
    parts.append("    .sub{margin:6px 0 0;color:#52667a;font-size:15px;}")
    parts.append("    .hero{background:#ffffff;border:1px solid #d8dee9;border-radius:18px;padding:18px 18px 14px;box-shadow:0 10px 28px rgba(16,42,67,.08);margin-bottom:18px;}")
    parts.append("    .legend{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:14px;}")
    parts.append("    .legend-card{background:#f8fbff;border:1px solid #dbe5ef;border-radius:12px;padding:10px;}")
    parts.append("    .legend-card strong{display:block;color:#0f3d5e;margin-bottom:4px;}")
    parts.append("    .race{background:#fff;border:1px solid #d8dee9;border-radius:16px;overflow:hidden;margin-bottom:18px;box-shadow:0 8px 20px rgba(16,42,67,.06);}")
    parts.append("    .race h2{margin:0;padding:14px 16px;background:#0f3d5e;color:#fff;font-size:18px;}")
    parts.append("    table{width:100%;border-collapse:collapse;}")
    parts.append("    th,td{padding:11px 12px;border-bottom:1px solid #edf1f5;text-align:left;vertical-align:top;font-size:14px;}")
    parts.append("    th{background:#f8fafc;color:#334155;font-weight:700;}")
    parts.append("    tr:last-child td{border-bottom:0;}")
    parts.append("    .score{font-weight:700;color:#0f3d5e;white-space:nowrap;}")
    parts.append("    .badge{display:inline-block;padding:3px 8px;border-radius:999px;background:#e8f1f8;color:#0f3d5e;font-size:12px;margin:0 6px 6px 0;}")
    parts.append("    .badge.alt{background:#eff6eb;color:#285430;}")
    parts.append("    .badge.warn{background:#fff3cd;color:#7a4b00;}")
    parts.append("    .badge.neutral{background:#eef2f7;color:#425466;}")
    parts.append("    .muted{color:#6b7c93;font-size:12px;line-height:1.45;}")
    parts.append("    .dist{font-size:12px;color:#52667a;line-height:1.5;}")
    parts.append("    .name{font-weight:700;}")
    parts.append("    @media (max-width: 860px){.legend{grid-template-columns:repeat(2,minmax(0,1fr));} th,td{padding:9px 8px;font-size:13px;} h1{font-size:24px;}}")
    parts.append("    @media (max-width: 620px){.top{flex-direction:column;align-items:flex-start;} .legend{grid-template-columns:1fr;} table{display:block;overflow:auto;}}")
    parts.append("  </style>")
    parts.append("</head>")
    parts.append("<body>")
    parts.append('  <div class="wrap">')
    parts.append('    <div class="hero">')
    parts.append('      <div class="top">')
    parts.append('        <div>')
    parts.append(f"          <h1>{esc(args.city)} {esc(args.date)} Analiz Sayfasi</h1>")
    parts.append('          <p class="sub">Yenibeygir stil dagilimi ile analiz CSV birlestirildi. Her kosuda atlar cikti skoruna gore siralandi.</p>')
    parts.append("        </div>")
    parts.append('        <a class="back" href="index.html">Geri Don ve Sehir Sec</a>')
    parts.append("      </div>")
    parts.append('      <div class="legend">')
    parts.append('        <div class="legend-card"><strong>Sprinter</strong><span class="muted">Geride bekleyip sonlarda gelen profil.</span></div>')
    parts.append('        <div class="legend-card"><strong>Orta Grup</strong><span class="muted">Yarisi orta blokta takip eden dengeli profil.</span></div>')
    parts.append('        <div class="legend-card"><strong>Takipci</strong><span class="muted">On grubun hemen arkasinda gidip baski kuran profil.</span></div>')
    parts.append('        <div class="legend-card"><strong>Onde Kacan</strong><span class="muted">Temposunu bastan kabul ettirmeye calisan lider profil.</span></div>')
    parts.append("      </div>")
    parts.append("    </div>")

    for race_name, rows in races.items():
        parts.append('    <section class="race">')
        parts.append(f"      <h2>{esc(race_name)}</h2>")
        parts.append("      <table>")
        parts.append("        <thead><tr><th>No</th><th>At Ismi</th><th>Cikti</th><th>Stil</th><th>Dagilim</th><th>Son Kosu</th></tr></thead>")
        parts.append("        <tbody>")
        for row in rows:
            secondary = row["secondary_or_dist"]
            secondary_html = ""
            if secondary in STYLE_LABELS.values():
                secondary_html = f'<span class="badge alt">{esc(secondary)}</span>'
                dist_html = esc(
                    " | ".join(
                        f"{STYLE_LABELS[key]} %{row.get(f'{key}_yuzde', '') or '0'}"
                        for key in ("stil_1", "stil_2", "stil_3", "stil_4")
                    )
                )
            else:
                dist_html = esc(secondary)

            last_race = (
                f"Son {esc(row.get('son_mesafe', '') or '-') }m {esc(row.get('son_pist', '') or '-')}"
                f"<br><span class='muted'>Son kilo: {esc(row.get('site_previous_weight', '') or '-')} | Simdiki kilo: {esc(row.get('site_current_weight', '') or '-')} | Hipodrom: {esc(row.get('son_hipodrom', '') or '-')}</span>"
            )
            sample_size = esc(row.get("stil_veri_sayisi", "") or "0")
            transition_html = ""
            if row.get("group_transition"):
                badge_class = "warn"
                if row.get("group_transition_kind") == "same":
                    badge_class = "alt"
                elif row.get("group_transition_kind") == "unknown":
                    badge_class = "neutral"
                transition_html = f"<div><span class='badge {badge_class}'>{esc(row['group_transition'])}</span></div>"
                if row.get("group_transition_note"):
                    transition_html += f"<div class='muted'>{esc(row.get('group_transition_note', ''))}</div>"
            parts.append(
                "          <tr>"
                f"<td class='score'>{esc(row.get('at_no', '') or '-')}</td>"
                f"<td><div class='name'>{esc(row.get('at_ismi', ''))}</div>{transition_html}<div class='muted'>Stil veri sayisi: {sample_size}</div></td>"
                f"<td class='score'>{esc(row.get('cikti', '') or '-')}</td>"
                f"<td><span class='badge'>{esc(row['primary_style'])}</span>{secondary_html}</td>"
                f"<td><div class='dist'>{dist_html}</div></td>"
                f"<td>{last_race}</td>"
                "</tr>"
            )
        parts.append("        </tbody>")
        parts.append("      </table>")
        parts.append("    </section>")

    parts.append("  </div>")
    parts.append("</body>")
    parts.append("</html>")

    output_path.write_text("\n".join(parts), encoding="utf-8")
    print(f"HTML yazildi: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
