from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


STYLE_SCORES = {
    "Önde Kaçan": 2,
    "Takipçi": 1,
    "Orta Grup": 0,
    "Sprinter": -1,
}

TEMPO_BONUS = {
    "Düşük": {
        "Önde Kaçan": 2,
        "Takipçi": 1,
        "Orta Grup": 0,
        "Sprinter": -2,
    },
    "Orta": {
        "Önde Kaçan": 0,
        "Takipçi": 2,
        "Orta Grup": 1,
        "Sprinter": 0,
    },
    "Yüksek": {
        "Önde Kaçan": -2,
        "Takipçi": 1,
        "Orta Grup": 0,
        "Sprinter": 2,
    },
}


@dataclass
class HorseRow:
    race: str
    name: str
    style_1: str
    style_2: str
    output_raw: str
    output_value: float | None


@dataclass
class HorseModel:
    race: str
    name: str
    style_1: str
    style_2: str
    output_used: float
    stil_skoru: int
    guc: float
    tempo_katkisi: float
    tempo_tipi: str
    kazanma_skoru: float
    dayaniklilik: float | None


@dataclass
class RaceTempo:
    race: str
    horse_count: int = 0
    total_tempo: float = 0.0
    catisma: float = 0.0
    ortalama_cikti: float = 0.0
    tempo_tipi: str = "Düşük"

    @property
    def tempo_index(self) -> float:
        if self.horse_count == 0:
            return 0.0
        return self.total_tempo / self.horse_count


def style_score(style_label: str) -> int:
    return STYLE_SCORES.get((style_label or "").strip(), 0)


def parse_output(raw_value: str) -> float | None:
    text = (raw_value or "").strip().replace(",", ".")
    if not text:
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    if value <= 0:
        return None
    return value


def is_onde_kacan(style_1: str, style_2: str) -> bool:
    return (style_1 == "Önde Kaçan") or (style_2 == "Önde Kaçan")


def is_takipci(style_1: str, style_2: str) -> bool:
    return (style_1 == "Takipçi") or (style_2 == "Takipçi")


def parse_race_horses(input_csv: Path) -> dict[str, list[HorseRow]]:
    race_horses: dict[str, list[HorseRow]] = {}
    current_race = "Genel"

    with input_csv.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            horse_name = (row.get("At İsmi") or "").strip()
            race_name = (row.get("Koşu") or "").strip()

            if not horse_name and race_name:
                current_race = race_name
                race_horses.setdefault(current_race, [])
                continue

            if not horse_name:
                continue

            race_horses.setdefault(current_race, []).append(
                HorseRow(
                    race=current_race,
                    name=horse_name,
                    style_1=(row.get("Stil Etiketi") or "").strip(),
                    style_2=(row.get("Stil Etiketi 2") or "").strip(),
                    output_raw=(row.get("Çıktı") or "").strip(),
                    output_value=parse_output(row.get("Çıktı", "")),
                )
            )

    return race_horses


def build_models(input_csv: Path) -> tuple[list[RaceTempo], list[HorseModel]]:
    race_horses = parse_race_horses(input_csv)
    races: list[RaceTempo] = []
    horse_models: list[HorseModel] = []

    for race_name, horses in race_horses.items():
        if not horses:
            continue

        valid_outputs = [h.output_value for h in horses if h.output_value is not None]
        if valid_outputs:
            ortalama_cikti = sum(valid_outputs) / len(valid_outputs)
        else:
            # Tum ciktilar gecersizse bolme hatasi olmamasi icin nobetci deger.
            ortalama_cikti = 1.0

        race = RaceTempo(race=race_name, horse_count=len(horses), ortalama_cikti=ortalama_cikti)

        # 1) Tempo katkisi ve tempo indeksini hesapla.
        temp_katkilar: list[float] = []
        for h in horses:
            stil_skoru = style_score(h.style_1) + style_score(h.style_2)
            output_used = h.output_value if h.output_value is not None else ortalama_cikti
            guc = output_used / ortalama_cikti if ortalama_cikti else 1.0

            if guc < 0.95:
                tempo_katkisi = stil_skoru * guc * 0.5
            else:
                tempo_katkisi = stil_skoru * guc

            temp_katkilar.append(tempo_katkisi)

        race.total_tempo = sum(temp_katkilar)

        # 2) Tempo catisma skoru.
        lider_sayisi = 0.0
        for h in horses:
            onde = is_onde_kacan(h.style_1, h.style_2)
            takip = is_takipci(h.style_1, h.style_2)
            if onde:
                lider_sayisi += 1.0
            if onde and takip:
                lider_sayisi += 0.5
        race.catisma = lider_sayisi

        # 3) Yaris tempo tipi.
        if race.catisma >= 3:
            race.tempo_tipi = "Yüksek"
        elif race.tempo_index >= 0.8:
            race.tempo_tipi = "Orta"
        else:
            race.tempo_tipi = "Düşük"

        # 4) At bazli kazanma skoru + ekstra dayanıklılık.
        for h in horses:
            stil_skoru = style_score(h.style_1) + style_score(h.style_2)
            output_used = h.output_value if h.output_value is not None else ortalama_cikti
            guc = output_used / ortalama_cikti if ortalama_cikti else 1.0

            if guc < 0.95:
                tempo_katkisi = stil_skoru * guc * 0.5
            else:
                tempo_katkisi = stil_skoru * guc

            bonus_1 = TEMPO_BONUS[race.tempo_tipi].get(h.style_1, 0)
            bonus_2 = TEMPO_BONUS[race.tempo_tipi].get(h.style_2, 0)

            kazanma_skoru = (1 / output_used) * 0.6 + bonus_1 * 0.25 + bonus_2 * 0.15

            dayaniklilik = None
            if race.tempo_tipi == "Yüksek":
                dayaniklilik = guc * 2 - stil_skoru * 0.3

            horse_models.append(
                HorseModel(
                    race=race_name,
                    name=h.name,
                    style_1=h.style_1,
                    style_2=h.style_2,
                    output_used=output_used,
                    stil_skoru=stil_skoru,
                    guc=guc,
                    tempo_katkisi=tempo_katkisi,
                    tempo_tipi=race.tempo_tipi,
                    kazanma_skoru=kazanma_skoru,
                    dayaniklilik=dayaniklilik,
                )
            )

        races.append(race)

    # Her kosu icinde kazanma skoruna gore sirala.
    ordered: list[HorseModel] = []
    by_race: dict[str, list[HorseModel]] = {}
    for hm in horse_models:
        by_race.setdefault(hm.race, []).append(hm)

    for race in races:
        items = by_race.get(race.race, [])
        items.sort(key=lambda x: x.kazanma_skoru, reverse=True)
        ordered.extend(items)

    return races, ordered


def write_summary(output_csv: Path, races: list[RaceTempo]) -> None:
    with output_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Kosu",
                "At Sayisi",
                "Ortalama Cikti",
                "Toplam Tempo",
                "Tempo Indeksi",
                "Catisma",
                "Yaris Tipi",
            ],
        )
        writer.writeheader()
        for r in races:
            writer.writerow(
                {
                    "Kosu": r.race,
                    "At Sayisi": r.horse_count,
                    "Ortalama Cikti": f"{r.ortalama_cikti:.3f}",
                    "Toplam Tempo": f"{r.total_tempo:.3f}",
                    "Tempo Indeksi": f"{r.tempo_index:.3f}",
                    "Catisma": f"{r.catisma:.2f}",
                    "Yaris Tipi": r.tempo_tipi,
                }
            )


def write_rankings(output_csv: Path, models: list[HorseModel]) -> None:
    with output_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Kosu",
                "Sira",
                "At",
                "Stil 1",
                "Stil 2",
                "Stil Skoru",
                "Cikti",
                "Guc",
                "Tempo Katkisi",
                "Tempo Tipi",
                "Kazanma Skoru",
                "Dayaniklilik",
            ],
        )
        writer.writeheader()

        current_race = ""
        rank = 0
        for hm in models:
            if hm.race != current_race:
                current_race = hm.race
                rank = 1
            else:
                rank += 1

            writer.writerow(
                {
                    "Kosu": hm.race,
                    "Sira": rank,
                    "At": hm.name,
                    "Stil 1": hm.style_1,
                    "Stil 2": hm.style_2,
                    "Stil Skoru": hm.stil_skoru,
                    "Cikti": f"{hm.output_used:.3f}",
                    "Guc": f"{hm.guc:.3f}",
                    "Tempo Katkisi": f"{hm.tempo_katkisi:.3f}",
                    "Tempo Tipi": hm.tempo_tipi,
                    "Kazanma Skoru": f"{hm.kazanma_skoru:.6f}",
                    "Dayaniklilik": "" if hm.dayaniklilik is None else f"{hm.dayaniklilik:.3f}",
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Birlesik CSV'den kosu bazli tempo indeksi ve yaris tipi hesaplar."
    )
    parser.add_argument("--input", required=True, help="Birlesik CSV dosya yolu")
    parser.add_argument("--output", required=True, help="Tempo ozet CSV dosya yolu")
    parser.add_argument("--ranking-output", default="", help="At bazli siralama CSV dosya yolu")
    args = parser.parse_args()

    input_csv = Path(args.input)
    output_csv = Path(args.output)

    races, models = build_models(input_csv)
    write_summary(output_csv, races)

    if args.ranking_output:
        write_rankings(Path(args.ranking_output), models)

    print(f"Tempo ozeti yazildi: {output_csv}")
    for r in races:
        print(
            f"- {r.race}: at={r.horse_count}, catisma={r.catisma:.2f}, toplam={r.total_tempo:.3f}, "
            f"indeks={r.tempo_index:.3f}, tip={r.tempo_tipi}"
        )

    if args.ranking_output:
        print(f"At siralama yazildi: {args.ranking_output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
