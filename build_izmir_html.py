from __future__ import annotations

import argparse
import csv
from pathlib import Path


def esc(text: str) -> str:
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Birlesik CSV dosyasindan sade bir yayin HTML'i olusturur."
    )
    parser.add_argument("--input", default="izmir_tek_csv_12_04_2026.csv")
    parser.add_argument("--output", default="izmir_yayin.html")
    parser.add_argument("--city", default="Izmir")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    races: list[tuple[str, list[dict[str, str]]]] = []
    current_race = "Genel"
    current_rows: list[dict[str, str]] = []

    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            at_ismi = (row.get("At İsmi") or "").strip()
            kosu = (row.get("Koşu") or "").strip()

            if not at_ismi and kosu:
                if current_rows:
                    races.append((current_race, current_rows))
                    current_rows = []
                current_race = kosu
                continue

            if not at_ismi:
                continue

            current_rows.append(
                {
                    "at_no": (row.get("At No") or "").strip(),
                    "at_ismi": at_ismi,
                    "cikti": (row.get("Çıktı") or "").strip(),
                    "stil_etiketi": (row.get("Stil Etiketi") or "").strip(),
                    "stil_etiketi_2": (row.get("Stil Etiketi 2") or "").strip(),
                }
            )

    if current_rows:
        races.append((current_race, current_rows))

    parts: list[str] = []
    parts.append("<!doctype html>")
    parts.append("<html lang=\"tr\">")
    parts.append("<head>")
    parts.append("  <meta charset=\"utf-8\" />")
    parts.append("  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />")
    parts.append(f"  <title>{esc(args.city)} At Analiz Listesi</title>")
    parts.append("  <style>")
    parts.append("    :root { color-scheme: light; }")
    parts.append("    body { margin: 0; font-family: 'Segoe UI', Tahoma, sans-serif; background: #f6f7fb; color: #1f2a37; }")
    parts.append("    .wrap { max-width: 1000px; margin: 24px auto 40px; padding: 0 16px; }")
    parts.append("    h1 { margin: 0 0 8px; font-size: 28px; }")
    parts.append("    .sub { margin: 0 0 24px; color: #5c6b7a; }")
    parts.append("    .topbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }")
    parts.append("    .back { text-decoration: none; font-size: 13px; color: #0f3d5e; border: 1px solid #bfd0e1; padding: 6px 10px; border-radius: 999px; background: #eef4fb; }")
    parts.append("    .back:hover { background: #e2edf8; }")
    parts.append("    .role-note { margin: 0 0 10px; font-size: 13px; color: #334e68; font-weight: 600; }")
    parts.append("    .race { background: #fff; border: 1px solid #d8dee9; border-radius: 12px; margin-bottom: 18px; overflow: hidden; }")
    parts.append("    .race h2 { margin: 0; padding: 12px 14px; background: #0f3d5e; color: #fff; font-size: 18px; }")
    parts.append("    table { width: 100%; border-collapse: collapse; }")
    parts.append("    th, td { padding: 10px 12px; border-bottom: 1px solid #edf1f5; text-align: left; font-size: 14px; }")
    parts.append("    th { background: #f8fafc; color: #334155; font-weight: 700; }")
    parts.append("    tr:last-child td { border-bottom: 0; }")
    parts.append("    .num { width: 70px; font-weight: 700; color: #0f3d5e; }")
    parts.append("    .score { width: 90px; }")
    parts.append("    .badge { display: inline-block; padding: 2px 8px; border-radius: 999px; background: #e8f1f8; color: #0f3d5e; font-size: 12px; margin-right: 6px; }")
    parts.append("    @media (max-width: 700px) {")
    parts.append("      th, td { padding: 8px; font-size: 13px; }")
    parts.append("      h1 { font-size: 24px; }")
    parts.append("    }")
    parts.append("  </style>")
    parts.append("</head>")
    parts.append("<body>")
    parts.append("  <div class=\"wrap\">")
    parts.append("    <p class=\"role-note\">Profesör ve Yardımcı Profesör için</p>")
    parts.append("    <div class=\"topbar\"><a class=\"back\" href=\"index.html\">Geri Don ve Sehir Sec</a></div>")
    parts.append(f"    <h1>{esc(args.city)} Kosulari - At Listesi</h1>")
    parts.append("    <p class=\"sub\">Kosu kosu at numarasi, isim, cikti ve stil etiketleri</p>")

    for race_name, horses in races:
        parts.append("    <section class=\"race\">")
        parts.append(f"      <h2>{esc(race_name)}</h2>")
        parts.append("      <table>")
        parts.append("        <thead><tr><th class=\"num\">No</th><th>At Ismi</th><th class=\"score\">Cikti</th><th>Stil Etiketi</th><th>Stil Etiketi 2</th></tr></thead>")
        parts.append("        <tbody>")
        for horse in horses:
            se1 = esc(horse["stil_etiketi"])
            se2 = esc(horse["stil_etiketi_2"])
            se1_html = f"<span class=\"badge\">{se1}</span>" if se1 else ""
            se2_html = f"<span class=\"badge\">{se2}</span>" if se2 else ""
            parts.append(
                "          <tr>"
                f"<td class=\"num\">{esc(horse['at_no'])}</td>"
                f"<td>{esc(horse['at_ismi'])}</td>"
                f"<td class=\"score\">{esc(horse['cikti'])}</td>"
                f"<td>{se1_html}</td>"
                f"<td>{se2_html}</td>"
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
