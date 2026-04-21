from __future__ import annotations

import argparse
import csv
from pathlib import Path


def norm_text(s: str) -> str:
    text = (s or "")
    # Try to repair common UTF-8 -> latin1/cp1252 mojibake sequences.
    for _ in range(2):
        if any(ch in text for ch in ("Ã", "Å", "Ä")):
            try:
                text = text.encode("latin1", errors="strict").decode("utf-8", errors="strict")
                continue
            except Exception:
                pass
        break
    return (
        text
        .replace("Ä°", "İ")
        .replace("Ã‡", "Ç")
        .replace("Ã–", "Ö")
        .replace("Åž", "Ş")
        .replace("ÄŸ", "ğ")
        .replace("Ä±", "ı")
        .replace("Ã¼", "ü")
        .replace("Ã§", "ç")
        .replace("Ã¶", "ö")
        .replace("ÅŸ", "ş")
        .strip()
    )


def esc(text: str) -> str:
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def get_first(row: dict[str, str], *keys: str) -> str:
    for k in keys:
        v = row.get(k)
        if v is not None:
            return v
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Birlesik CSV dosyasindan sade bir yayin HTML'i olusturur."
    )
    parser.add_argument("--input", default="izmir_tek_csv_12_04_2026.csv")
    parser.add_argument("--output", default="izmir_yayin.html")
    parser.add_argument("--city", default="Izmir")
    parser.add_argument("--tempo-summary", default="")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    tempo_map: dict[str, dict[str, str]] = {}

    if args.tempo_summary:
        tempo_path = Path(args.tempo_summary)
        if tempo_path.exists():
            with tempo_path.open("r", encoding="utf-8-sig", newline="") as tf:
                treader = csv.DictReader(tf)
                for row in treader:
                    race_name = norm_text(row.get("Kosu") or "")
                    if not race_name:
                        continue
                    tempo_map[race_name] = {
                        "at_sayisi": norm_text(row.get("At Sayisi") or ""),
                        "toplam_tempo": norm_text(row.get("Toplam Tempo") or ""),
                        "tempo_indeksi": norm_text(row.get("Tempo Indeksi") or ""),
                        "siddet": norm_text(row.get("Siddet") or ""),
                        "yaris_tipi": norm_text(row.get("Yaris Tipi") or ""),
                        "yaris_yapisi": norm_text(row.get("Yaris Yapisi") or ""),
                        "karar_sonucu": norm_text(row.get("Karar Sonucu") or ""),
                        "avantajli_at_turu": norm_text(row.get("Avantajli At Turu") or ""),
                    }

    races: list[tuple[str, list[dict[str, str]]]] = []
    current_race = "Genel"
    current_rows: list[dict[str, str]] = []

    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            at_ismi = norm_text(get_first(row, "At İsmi", "At Ä°smi", "At Ismi", "At Ã„Â°smi"))
            kosu = norm_text(get_first(row, "Koşu", "KoÅŸu"))

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
                    "cikti": norm_text(get_first(row, "Çıktı", "Ã‡Ä±ktÄ±")),
                    "stil_etiketi": norm_text(row.get("Stil Etiketi") or ""),
                    "stil_etiketi_2": norm_text(row.get("Stil Etiketi 2") or ""),
                    "zemin": norm_text(row.get("Son Kosu Zemin Durumu") or ""),
                    "slow5": (row.get("Birinciden 5sn+") or "").strip(),
                    "fark_sn": norm_text(row.get("Birinciden Fark Sn") or ""),
                }
            )

    if current_rows:
        races.append((current_race, current_rows))

    parts: list[str] = []
    parts.append("<!doctype html>")
    parts.append('<html lang="tr">')
    parts.append("<head>")
    parts.append('  <meta charset="utf-8" />')
    parts.append('  <meta name="viewport" content="width=device-width, initial-scale=1" />')
    parts.append(f"  <title>{esc(norm_text(args.city))} At Analiz Listesi</title>")
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
    parts.append("    .tempo { margin: 10px 14px 2px; display: flex; flex-wrap: wrap; gap: 8px; }")
    parts.append("    .tempo-chip { display: inline-block; border-radius: 999px; background: #f1f5f9; border: 1px solid #d5e0eb; color: #102a43; padding: 4px 10px; font-size: 12px; font-weight: 600; }")
    parts.append("    table { width: 100%; border-collapse: collapse; }")
    parts.append("    th, td { padding: 10px 12px; border-bottom: 1px solid #edf1f5; text-align: left; font-size: 14px; }")
    parts.append("    th { background: #f8fafc; color: #334155; font-weight: 700; }")
    parts.append("    tr:last-child td { border-bottom: 0; }")
    parts.append("    .num { width: 70px; font-weight: 700; color: #0f3d5e; }")
    parts.append("    .score { width: 90px; }")
    parts.append("    .badge { display: inline-block; padding: 2px 8px; border-radius: 999px; background: #e8f1f8; color: #0f3d5e; font-size: 12px; margin-right: 6px; }")
    parts.append("    @media (max-width: 700px) { th, td { padding: 8px; font-size: 13px; } h1 { font-size: 24px; } }")
    parts.append("  </style>")
    parts.append("</head>")
    parts.append("<body>")
    parts.append('  <div class="wrap">')
    parts.append('    <p class="role-note">Profesor ve Yardimci Profesor icin</p>')
    parts.append('    <div class="topbar"><a class="back" href="index.html">Geri Don ve Sehir Sec</a></div>')
    parts.append(f"    <h1>{esc(norm_text(args.city))} Kosulari - At Listesi</h1>")
    parts.append('    <p class="sub">Kosu kosu at numarasi, isim, cikti ve stil etiketleri</p>')

    for race_name, horses in races:
        parts.append('    <section class="race">')
        parts.append(f"      <h2>{esc(race_name)}</h2>")
        tempo = tempo_map.get(race_name)
        if tempo:
            parts.append('      <div class="tempo">')
            parts.append(f"        <span class=\"tempo-chip\">Tempo Indeksi: {esc(tempo['tempo_indeksi'])}</span>")
            parts.append(f"        <span class=\"tempo-chip\">Yaris Tipi: {esc(tempo['yaris_tipi'])}</span>")
            parts.append(f"        <span class=\"tempo-chip\">Siddet: {esc(tempo['siddet'])}</span>")
            parts.append(f"        <span class=\"tempo-chip\">At: {esc(tempo['at_sayisi'])}</span>")
            parts.append(f"        <span class=\"tempo-chip\">Toplam Tempo: {esc(tempo['toplam_tempo'])}</span>")
            parts.append(f"        <span class=\"tempo-chip\">Yapi: {esc(tempo['yaris_yapisi'])}</span>")
            parts.append(f"        <span class=\"tempo-chip\">Sonuc: {esc(tempo['karar_sonucu'])}</span>")
            parts.append(f"        <span class=\"tempo-chip\">En Avantajli: {esc(tempo['avantajli_at_turu'])}</span>")
            parts.append("      </div>")
        parts.append("      <table>")
        parts.append('        <thead><tr><th class="num">No</th><th>At Ismi</th><th class="score">Cikti</th><th>Stil Etiketi</th><th>Stil Etiketi 2</th><th>Uyari</th></tr></thead>')
        parts.append("        <tbody>")
        for horse in horses:
            se1 = esc(horse["stil_etiketi"])
            se2 = esc(horse["stil_etiketi_2"])
            se1_html = f'<span class="badge">{se1}</span>' if se1 else ""
            se2_html = f'<span class="badge">{se2}</span>' if se2 else ""
            warn_bits = []
            if (horse.get("slow5") or "").strip().upper() == "X":
                fark = (horse.get("fark_sn") or "").strip()
                label = f"X (>{fark} sn)" if fark else "X (>5 sn)"
                warn_bits.append(f'<span class="badge">{esc(label)}</span>')
            zemin = (horse.get("zemin") or "").strip()
            if zemin:
                warn_bits.append(f'<span class="badge">{esc(zemin)}</span>')
            warn_html = "".join(warn_bits)
            parts.append(
                "          <tr>"
                f"<td class=\"num\">{esc(horse['at_no'])}</td>"
                f"<td>{esc(horse['at_ismi'])}</td>"
                f"<td class=\"score\">{esc(horse['cikti'])}</td>"
                f"<td>{se1_html}</td>"
                f"<td>{se2_html}</td>"
                f"<td>{warn_html}</td>"
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
