from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


# Pace pressure contribution per style (higher => race likely runs faster early)
PACE_WEIGHTS = {
    "Önde Kaçan": 1.20,
    "Takipçi": 0.60,
    "Orta Grup": 0.00,
    "Sprinter": -0.90,
}

# Tempo-fit bonus used in horse ranking after race tempo is estimated
TEMPO_FIT = {
    "Düşük Tempo": {"Önde Kaçan": 1.4, "Takipçi": 1.0, "Orta Grup": 0.4, "Sprinter": -0.6},
    "Orta Tempo": {"Önde Kaçan": 0.5, "Takipçi": 1.2, "Orta Grup": 0.9, "Sprinter": 0.3},
    "Yüksek Tempo": {"Önde Kaçan": -0.7, "Takipçi": 0.9, "Orta Grup": 0.4, "Sprinter": 1.3},
    "Çok Yüksek": {"Önde Kaçan": -1.0, "Takipçi": 0.7, "Orta Grup": 0.3, "Sprinter": 1.6},
}


@dataclass
class HorseRow:
    race: str
    name: str
    style_1: str
    style_2: str
    output_value: float | None
    over_5s: bool
    track_cond: str


@dataclass
class HorseModel:
    race: str
    name: str
    style_1: str
    style_2: str
    output_used: float
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
    ortalama_cikti: float = 0.0
    tempo_tipi: str = "Düşük Tempo"
    siddet_seviyesi: str = "Düşük"
    yaris_yapisi: str = "Orta grup"
    karar_sonucu: str = "Klasik yarış"
    avantajli_at_turu: str = "Takipçi"

    @property
    def tempo_index(self) -> float:
        if self.horse_count == 0:
            return 0.0
        # Center index around 1.0 to reduce systematic low-tempo bias
        base = 1.0
        scaled = self.total_tempo / max(6.0, self.horse_count * 2.8)
        crowd_factor = max(0, self.horse_count - 10) * 0.015
        return base + scaled + crowd_factor


def get_first(row: dict[str, str], *keys: str) -> str:
    for k in keys:
        v = row.get(k)
        if v is not None:
            return v
    return ""


def pace_weight(style_label: str) -> float:
    return PACE_WEIGHTS.get((style_label or "").strip(), 0.0)


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


def classify_tempo_index(idx: float) -> str:
    if idx < 0.98:
        return "Düşük Tempo"
    if idx <= 1.10:
        return "Orta Tempo"
    if idx <= 1.22:
        return "Yüksek Tempo"
    return "Çok Yüksek"


def classify_total_tempo(total_tempo: float) -> str:
    # total_tempo is now pressure-like; use softer buckets
    if total_tempo < 4:
        return "Düşük"
    if total_tempo <= 8:
        return "Orta"
    return "Yüksek"


def classify_field_size(horse_count: int) -> str:
    if 3 <= horse_count <= 6:
        return "Küçük grup"
    if 7 <= horse_count <= 10:
        return "Orta grup"
    if horse_count >= 11:
        return "Kalabalık"
    return "Küçük grup"


def decision_matrix(
    tempo_tipi: str,
    siddet: str,
    leader_share: float,
    takip_share: float,
    sprinter_share: float,
) -> tuple[str, str]:
    # Dynamic decision: avoid collapsing all races into one advantage type.
    if tempo_tipi == "Düşük Tempo":
        if leader_share >= 0.34:
            return "Lider kontrollü gidiş", "Önde Kaçan"
        if takip_share >= 0.38:
            return "Dengeli ama takip odaklı", "Takipçi"
        return "Kontrollü tempo", "Önde Kaçan"

    if tempo_tipi == "Orta Tempo":
        if sprinter_share >= 0.30 and siddet in {"Orta", "Yüksek"}:
            return "Sonlarda hızlanan yarış", "Güçlü Takipçi / Sprinter"
        if leader_share >= 0.24 and sprinter_share < 0.24:
            return "Ön grup avantajlı orta tempo", "Önde Kaçan"
        if sprinter_share >= 0.20:
            return "Dengeli ama kapanışa açık", "Sprinter / Takipçi"
        return "Klasik denge yarışı", "Takipçi"

    if tempo_tipi == "Yüksek Tempo":
        if sprinter_share >= 0.24:
            return "Tempolu yarış, kapanış etkili", "Sprinter"
        if leader_share >= 0.28:
            return "Sert tempo ama lider direnebilir", "Lider / güçlü at"
        return "Tempolu yarış", "Güçlü Takipçi / Sprinter"

    # Çok Yüksek
    if sprinter_share >= 0.18:
        return "Kaos ve yıpranma", "En güçlü kapanış"
    return "Yıpratıcı yarış", "Sprinter / Güçlü kapanış"


def parse_race_horses(input_csv: Path) -> dict[str, list[HorseRow]]:
    race_horses: dict[str, list[HorseRow]] = {}
    current_race = "Genel"

    with input_csv.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            horse_name = get_first(row, "At İsmi", "At Ä°smi").strip()
            race_name = get_first(row, "Koşu", "KoÅŸu").strip()

            if not horse_name and race_name:
                current_race = race_name
                race_horses.setdefault(current_race, [])
                continue

            if not horse_name:
                continue

            output_raw = get_first(row, "Çıktı", "Ã‡Ä±ktÄ±")
            over_5s = get_first(row, "Birinciden 5sn+").strip().upper() == "X"
            track_cond = get_first(row, "Son Kosu Zemin Durumu").strip()

            race_horses.setdefault(current_race, []).append(
                HorseRow(
                    race=current_race,
                    name=horse_name,
                    style_1=get_first(row, "Stil Etiketi").strip(),
                    style_2=get_first(row, "Stil Etiketi 2").strip(),
                    output_value=parse_output(output_raw),
                    over_5s=over_5s,
                    track_cond=track_cond,
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
        ortalama_cikti = (sum(valid_outputs) / len(valid_outputs)) if valid_outputs else 1.0

        race = RaceTempo(race=race_name, horse_count=len(horses), ortalama_cikti=ortalama_cikti)

        # 1) Tempo pressure + race tempo index
        temp_katkilar: list[float] = []
        for h in horses:
            output_used = h.output_value if h.output_value is not None else ortalama_cikti
            guc = (ortalama_cikti / output_used) if output_used else 1.0

            pace = pace_weight(h.style_1) + 0.60 * pace_weight(h.style_2)
            # Stronger horse can enforce its style better
            tempo_katkisi = pace * (0.8 + 0.4 * guc)
            # If horse recently faded badly, reduce expected pace pressure
            if h.over_5s:
                tempo_katkisi *= 0.85

            temp_katkilar.append(tempo_katkisi)

        race.total_tempo = sum(temp_katkilar)

        race.tempo_tipi = classify_tempo_index(race.tempo_index)
        race.siddet_seviyesi = classify_total_tempo(race.total_tempo)
        race.yaris_yapisi = classify_field_size(race.horse_count)
        leader_weight = 0.0
        takip_weight = 0.0
        sprinter_weight = 0.0
        for h in horses:
            leader_weight += 1.0 if h.style_1 == "Önde Kaçan" else 0.0
            leader_weight += 0.55 if h.style_2 == "Önde Kaçan" else 0.0
            takip_weight += 1.0 if h.style_1 == "Takipçi" else 0.0
            takip_weight += 0.55 if h.style_2 == "Takipçi" else 0.0
            sprinter_weight += 1.0 if h.style_1 == "Sprinter" else 0.0
            sprinter_weight += 0.55 if h.style_2 == "Sprinter" else 0.0
        denom = max(1.0, race.horse_count * 1.55)
        leader_share = leader_weight / denom
        takip_share = takip_weight / denom
        sprinter_share = sprinter_weight / denom
        race.karar_sonucu, race.avantajli_at_turu = decision_matrix(
            race.tempo_tipi,
            race.siddet_seviyesi,
            leader_share,
            takip_share,
            sprinter_share,
        )

        # 2) Horse win score in estimated tempo scenario
        for h in horses:
            output_used = h.output_value if h.output_value is not None else ortalama_cikti
            guc = (ortalama_cikti / output_used) if output_used else 1.0

            pace = pace_weight(h.style_1) + 0.60 * pace_weight(h.style_2)
            tempo_katkisi = pace * (0.8 + 0.4 * guc)
            if h.over_5s:
                tempo_katkisi *= 0.85

            fit = TEMPO_FIT[race.tempo_tipi].get(h.style_1, 0.0) + 0.55 * TEMPO_FIT[race.tempo_tipi].get(h.style_2, 0.0)

            # Base from odds-like output (lower is better) + tempo fit + pace suitability
            base = (1.0 / output_used)
            wet_adj = 0.10 if h.track_cond else 0.0
            penalty_5s = -0.12 if h.over_5s else 0.0
            kazanma_skoru = base * 0.62 + fit * 0.24 + tempo_katkisi * 0.10 + wet_adj + penalty_5s

            dayaniklilik = None
            if race.tempo_tipi in {"Yüksek Tempo", "Çok Yüksek"}:
                dayaniklilik = guc * 2.0 - max(0.0, pace) * 0.4

            horse_models.append(
                HorseModel(
                    race=race_name,
                    name=h.name,
                    style_1=h.style_1,
                    style_2=h.style_2,
                    output_used=output_used,
                    guc=guc,
                    tempo_katkisi=tempo_katkisi,
                    tempo_tipi=race.tempo_tipi,
                    kazanma_skoru=kazanma_skoru,
                    dayaniklilik=dayaniklilik,
                )
            )

        races.append(race)

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
                "Siddet",
                "Yaris Tipi",
                "Yaris Yapisi",
                "Karar Sonucu",
                "Avantajli At Turu",
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
                    "Siddet": r.siddet_seviyesi,
                    "Yaris Tipi": r.tempo_tipi,
                    "Yaris Yapisi": r.yaris_yapisi,
                    "Karar Sonucu": r.karar_sonucu,
                    "Avantajli At Turu": r.avantajli_at_turu,
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
            f"- {r.race}: at={r.horse_count}, toplam={r.total_tempo:.3f}, indeks={r.tempo_index:.3f}, "
            f"tip={r.tempo_tipi}, siddet={r.siddet_seviyesi}, avantaj={r.avantajli_at_turu}"
        )

    if args.ranking_output:
        print(f"At siralama yazildi: {args.ranking_output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
