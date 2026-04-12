from __future__ import annotations

import argparse
import csv
import unicodedata
from pathlib import Path


def normalize_name(value: str) -> str:
    # Case-insensitive + accent-insensitive key for stable matching.
    text = unicodedata.normalize("NFKD", (value or "").strip())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.casefold()
    return " ".join(text.split())


def load_style_map(path: Path) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = normalize_name(row.get("at_adi", ""))
            if not key:
                continue
            out[key] = {
                "at_no": row.get("at_no", ""),
                "at_id": row.get("at_id", ""),
                "stil_etiketi": row.get("stil_etiketi", ""),
                "stil_etiketi_2": row.get("stil_etiketi_2", ""),
                "stil_aciklama": row.get("stil_aciklama", ""),
                "yaris_stili": row.get("yaris_stili", ""),
                "at_profili": row.get("at_profili", ""),
            }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analiz CSV ile Yenibeygir stil CSV'sini tek dosyada birlestirir."
    )
    parser.add_argument(
        "--analysis",
        default=r"c:\Users\emir\Downloads\izmir_analiz_20260412_115549_user1.csv",
        help="Analiz CSV dosya yolu",
    )
    parser.add_argument(
        "--styles",
        default="izmir_12_04_2026_atlar.csv",
        help="Yenibeygir stil CSV dosya yolu",
    )
    parser.add_argument(
        "--output",
        default="izmir_tek_csv_12_04_2026.csv",
        help="Birlesik CSV dosya yolu",
    )
    args = parser.parse_args()

    analysis_path = Path(args.analysis)
    styles_path = Path(args.styles)
    output_path = Path(args.output)

    style_map = load_style_map(styles_path)

    with analysis_path.open("r", encoding="utf-8-sig", newline="") as fin:
        reader = csv.DictReader(fin)
        base_fields = reader.fieldnames or []
        extra_fields = [
            "At No",
            "At ID",
            "Stil Etiketi",
            "Stil Etiketi 2",
            "Stil Aciklama",
            "Yaris Stili",
            "At Profili",
            "Eslesme",
        ]

        rows = []
        matched = 0
        total_horses = 0

        for row in reader:
            name = (row.get("At İsmi") or "").strip()
            if not name:
                # Kosu baslik satiri gibi bos at satirlarini oldugu gibi tut.
                merged = {**row}
                for f in extra_fields:
                    merged[f] = ""
                rows.append(merged)
                continue

            total_horses += 1
            key = normalize_name(name)
            style = style_map.get(key)

            merged = {**row}
            if style:
                matched += 1
                merged["At No"] = style["at_no"]
                merged["At ID"] = style["at_id"]
                merged["Stil Etiketi"] = style["stil_etiketi"]
                merged["Stil Etiketi 2"] = style["stil_etiketi_2"]
                merged["Stil Aciklama"] = style["stil_aciklama"]
                merged["Yaris Stili"] = style["yaris_stili"]
                merged["At Profili"] = style["at_profili"]
                merged["Eslesme"] = "bulundu"
            else:
                merged["At No"] = ""
                merged["At ID"] = ""
                merged["Stil Etiketi"] = ""
                merged["Stil Etiketi 2"] = ""
                merged["Stil Aciklama"] = ""
                merged["Yaris Stili"] = ""
                merged["At Profili"] = ""
                merged["Eslesme"] = "bulunamadi"

            rows.append(merged)

    with output_path.open("w", encoding="utf-8-sig", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=base_fields + extra_fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Yazildi: {output_path}")
    print(f"Eslesen at: {matched}/{total_horses}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
