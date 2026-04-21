from __future__ import annotations

import argparse
import csv
import difflib
import re
import unicodedata
from pathlib import Path


def get_first(row: dict[str, str], *keys: str) -> str:
    for k in keys:
        val = row.get(k)
        if val is not None:
            return val
    return ""


def normalize_name(value: str) -> str:
    # Case-insensitive + accent-insensitive key for stable matching.
    text = unicodedata.normalize("NFKD", (value or "").strip())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.casefold()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def compact_key(value: str) -> str:
    return normalize_name(value).replace(" ", "")


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
                "son_kosu_zemin_durumu": row.get("son_kosu_zemin_durumu", ""),
                "birinciden_5sn_fazla": row.get("birinciden_5sn_fazla", ""),
                "birinciden_fark_sn": row.get("birinciden_fark_sn", ""),
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
    compact_style_map = {compact_key(k): v for k, v in style_map.items()}
    compact_style_keys = list(compact_style_map.keys())

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
            "Son Kosu Zemin Durumu",
            "Birinciden 5sn+",
            "Birinciden Fark Sn",
            "At Profili",
            "Eslesme",
        ]

        rows = []
        matched = 0
        total_horses = 0

        for row in reader:
            name = get_first(row, "At İsmi", "At Ismi", "At Ä°smi").strip()
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
            if not style:
                ckey = compact_key(name)
                style = compact_style_map.get(ckey)
                if not style and ckey:
                    close = difflib.get_close_matches(ckey, compact_style_keys, n=1, cutoff=0.90)
                    if close:
                        style = compact_style_map.get(close[0])

            merged = {**row}
            if style:
                matched += 1
                merged["At No"] = style["at_no"]
                merged["At ID"] = style["at_id"]
                merged["Stil Etiketi"] = style["stil_etiketi"]
                merged["Stil Etiketi 2"] = style["stil_etiketi_2"]
                merged["Stil Aciklama"] = style["stil_aciklama"]
                merged["Yaris Stili"] = style["yaris_stili"]
                merged["Son Kosu Zemin Durumu"] = style["son_kosu_zemin_durumu"]
                merged["Birinciden 5sn+"] = style["birinciden_5sn_fazla"]
                merged["Birinciden Fark Sn"] = style["birinciden_fark_sn"]
                merged["At Profili"] = style["at_profili"]
                merged["Eslesme"] = "bulundu"
            else:
                merged["At No"] = ""
                merged["At ID"] = ""
                merged["Stil Etiketi"] = "Bilinmiyor"
                merged["Stil Etiketi 2"] = ""
                merged["Stil Aciklama"] = "At ismi stil verisiyle eslesmedi."
                merged["Yaris Stili"] = ""
                merged["Son Kosu Zemin Durumu"] = ""
                merged["Birinciden 5sn+"] = ""
                merged["Birinciden Fark Sn"] = ""
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
