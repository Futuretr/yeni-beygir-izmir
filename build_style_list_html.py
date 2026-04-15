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
    p = argparse.ArgumentParser(description="Site'den cekilen stil CSV'sini basit HTML tabloya cevirir.")
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--title", required=True)
    args = p.parse_args()

    rows = []
    with Path(args.input).open("r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(
                {
                    "no": (row.get("at_no") or "").strip(),
                    "ad": (row.get("at_adi") or "").strip(),
                    "s1": (row.get("stil_etiketi") or "").strip(),
                    "s2": (row.get("stil_etiketi_2") or "").strip(),
                }
            )

    html = [
        "<!doctype html>",
        "<html lang='tr'>",
        "<head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>",
        f"<title>{esc(args.title)}</title>",
        "<style>body{font-family:Segoe UI,Tahoma,sans-serif;background:#f6f7fb;color:#1f2a37;margin:0}"
        ".wrap{max-width:980px;margin:24px auto;padding:0 16px}.card{background:#fff;border:1px solid #d8dee9;border-radius:12px;overflow:hidden}"
        "h1{font-size:26px}.sub{color:#5c6b7a}.back{display:inline-block;margin:8px 0 14px;text-decoration:none;color:#0f3d5e;border:1px solid #bfd0e1;padding:6px 10px;border-radius:999px;background:#eef4fb}"
        "table{width:100%;border-collapse:collapse}th,td{padding:10px 12px;border-bottom:1px solid #edf1f5;text-align:left}th{background:#f8fafc}"
        ".badge{display:inline-block;padding:2px 8px;border-radius:999px;background:#e8f1f8;color:#0f3d5e;font-size:12px;margin-right:6px}</style></head>",
        "<body><div class='wrap'>",
        "<a class='back' href='index.html'>Geri Don</a>",
        f"<h1>{esc(args.title)}</h1>",
        "<p class='sub'>Bu tablo dogrudan Yenibeygir'den cekilen stil etiketlerini gosterir.</p>",
        "<div class='card'><table><thead><tr><th>No</th><th>At</th><th>Stil 1</th><th>Stil 2</th></tr></thead><tbody>",
    ]

    for row in rows:
        s1 = f"<span class='badge'>{esc(row['s1'])}</span>" if row["s1"] else ""
        s2 = f"<span class='badge'>{esc(row['s2'])}</span>" if row["s2"] else ""
        html.append(
            f"<tr><td>{esc(row['no'])}</td><td>{esc(row['ad'])}</td><td>{s1}</td><td>{s2}</td></tr>"
        )

    html.append("</tbody></table></div></div></body></html>")
    Path(args.output).write_text("".join(html), encoding="utf-8")
    print(f"HTML yazildi: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

