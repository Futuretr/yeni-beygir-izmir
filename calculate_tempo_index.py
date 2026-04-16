from __future__ import annotations

import argparse
import csv
import math
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


PACE_WEIGHTS = {
    "Önde Kaçan": 1.15,
    "Takipçi": 0.55,
    "Orta Grup": 0.00,
    "Sprinter": -0.85,
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
    last_surface: str


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
    race_surface: str = "Kum"
    tahmini_400m: float = 0.0

    @property
    def tempo_index(self) -> float:
        if self.horse_count == 0:
            return 0.0
        # keep scale around [0.8..1.4] with race-size stabilization
        return 1.0 + (self.total_tempo / max(8.0, self.horse_count * 3.2))


@dataclass
class SurfaceModel:
    min_sec: float
    max_sec: float
    mean_sec: float
    coeffs: dict[str, tuple[float, float]]


STYLE_SET = ["Önde Kaçan", "Takipçi", "Orta Grup", "Sprinter"]


def get_first(row: dict[str, str], *keys: str) -> str:
    for k in keys:
        v = row.get(k)
        if v is not None:
            return v
    return ""


def norm_text(s: str) -> str:
    return (
        (s or "")
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


def normalize_style(style_label: str) -> str:
    s = norm_text(style_label).casefold()
    s_ascii = "".join(
        ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch)
    )
    if ("onde" in s_ascii and "kacan" in s_ascii) or ("önde" in s and "kaçan" in s):
        return "Önde Kaçan"
    if "takip" in s_ascii:
        return "Takipçi"
    if "orta" in s_ascii:
        return "Orta Grup"
    if "sprint" in s_ascii:
        return "Sprinter"
    return ""


def normalize_surface(surface: str) -> str:
    s = norm_text(surface).casefold()
    if "cim" in s or "çim" in s:
        return "Cim"
    if "sent" in s:
        return "Sentetik"
    if "kum" in s:
        return "Kum"
    return "Kum"


def pace_weight(style_label: str) -> float:
    return PACE_WEIGHTS.get(normalize_style(style_label), 0.0)


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
    if idx < 0.92:
        return "Düşük Tempo"
    if idx <= 1.10:
        return "Orta Tempo"
    if idx <= 1.26:
        return "Yüksek Tempo"
    return "Çok Yüksek"


def classify_total_tempo(total_tempo: float) -> str:
    if total_tempo < 3.0:
        return "Düşük"
    if total_tempo <= 7.5:
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


def fit_weighted_line(points: list[tuple[float, float, float]]) -> tuple[float, float]:
    # y = a + b*x
    if not points:
        return 0.0, 0.0
    sw = sum(w for _, _, w in points)
    if sw <= 0:
        return 0.0, 0.0
    mx = sum(x * w for x, _, w in points) / sw
    my = sum(y * w for _, y, w in points) / sw
    num = sum(w * (x - mx) * (y - my) for x, y, w in points)
    den = sum(w * (x - mx) ** 2 for x, _, w in points)
    if den == 0:
        return my, 0.0
    b = num / den
    a = my - b * mx
    return a, b


def load_historical_models(summary_path: Path | None) -> dict[str, SurfaceModel]:
    if summary_path is None or not summary_path.exists():
        return {}

    by_surface = defaultdict(list)
    with summary_path.open("r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                b0 = float(row.get("bin_start_sec", "0") or 0)
                b1 = float(row.get("bin_end_sec", "0") or 0)
                race_count = int(float(row.get("race_count", "0") or 0))
            except ValueError:
                continue
            if race_count <= 0:
                continue

            center = (b0 + b1) / 2.0
            surface = normalize_surface(row.get("race_surface", ""))

            probs = {k: 0.0 for k in STYLE_SET}
            for i in (1, 2, 3, 4):
                sn = row.get(f"top_style_{i}", "")
                pn = row.get(f"top_style_{i}_probability_pct", "")
                s = normalize_style(sn)
                if not s:
                    continue
                try:
                    p = float(pn)
                except ValueError:
                    p = 0.0
                probs[s] = max(probs[s], p)

            by_surface[surface].append((center, race_count, probs))

    models: dict[str, SurfaceModel] = {}
    for surface, entries in by_surface.items():
        sec_vals = [e[0] for e in entries]
        min_sec = min(sec_vals)
        max_sec = max(sec_vals)
        mean_sec = sum(sec_vals) / len(sec_vals)

        coeffs: dict[str, tuple[float, float]] = {}
        for style in STYLE_SET:
            pts = [(sec, probs[style], w) for sec, w, probs in entries]
            coeffs[style] = fit_weighted_line(pts)

        models[surface] = SurfaceModel(
            min_sec=min_sec,
            max_sec=max_sec,
            mean_sec=mean_sec,
            coeffs=coeffs,
        )

    return models


def predict_style_probs(surface_model: SurfaceModel, sec: float) -> dict[str, float]:
    raw = {}
    for style, (a, b) in surface_model.coeffs.items():
        raw[style] = max(0.0, a + b * sec)
    s = sum(raw.values())
    if s <= 0:
        return {k: 25.0 for k in STYLE_SET}
    return {k: raw[k] * 100.0 / s for k in STYLE_SET}


def estimate_400m_sec(surface_model: SurfaceModel, pace_index: float) -> float:
    # pace_index > 1 => faster first400 => lower seconds
    sec_span = max(0.5, (surface_model.max_sec - surface_model.min_sec) / 2.0)
    sec = surface_model.mean_sec - (pace_index - 1.0) * sec_span * 2.1
    return min(surface_model.max_sec, max(surface_model.min_sec, sec))


def map_style_to_advantage(style: str) -> str:
    if style == "Önde Kaçan":
        return "Önde Kaçan"
    if style == "Takipçi":
        return "Takipçi"
    if style == "Orta Grup":
        return "Orta Grup"
    return "Sprinter"


def decision_matrix(
    tempo_tipi: str,
    siddet: str,
    leader_share: float,
    takip_share: float,
    orta_share: float,
    sprinter_share: float,
    unknown_share: float,
    hist_probs: dict[str, float],
) -> tuple[str, str]:
    tempo_bonus = {
        "Düşük Tempo": {"Önde Kaçan": 0.22, "Takipçi": 0.03, "Orta Grup": 0.04, "Sprinter": -0.08},
        "Orta Tempo": {"Önde Kaçan": 0.08, "Takipçi": 0.16, "Orta Grup": 0.12, "Sprinter": 0.03},
        "Yüksek Tempo": {"Önde Kaçan": -0.10, "Takipçi": 0.10, "Orta Grup": 0.06, "Sprinter": 0.20},
        "Çok Yüksek": {"Önde Kaçan": -0.20, "Takipçi": 0.04, "Orta Grup": 0.02, "Sprinter": 0.28},
    }

    style_scores = {
        "Önde Kaçan": leader_share * 2.00,
        "Takipçi": takip_share * 1.70,
        "Orta Grup": orta_share * 1.55,
        "Sprinter": sprinter_share * 1.95,
    }

    style_scores["Önde Kaçan"] += 0.08 if siddet == "Düşük" else 0.0
    style_scores["Sprinter"] += 0.05 if siddet == "Yüksek" else 0.0

    tbonus = tempo_bonus.get(tempo_tipi, tempo_bonus["Orta Tempo"])
    for st in STYLE_SET:
        style_scores[st] += tbonus.get(st, 0.0)

    # Tarihsel olasılıkları yumuşak katkı olarak ekle; tek başına karar vermesin.
    for st in STYLE_SET:
        hp = hist_probs.get(st, 25.0)
        style_scores[st] += ((hp - 25.0) / 100.0) * 0.22

    if tempo_tipi in {"Yüksek Tempo", "Çok Yüksek"}:
        style_scores["Sprinter"] += 0.10
        style_scores["Takipçi"] -= 0.03
    elif tempo_tipi == "Düşük Tempo":
        style_scores["Önde Kaçan"] += 0.07

    if unknown_share >= 0.35:
        mean_score = sum(style_scores.values()) / len(style_scores)
        for st in STYLE_SET:
            style_scores[st] = style_scores[st] * 0.65 + mean_score * 0.35

    ordered = sorted(style_scores.items(), key=lambda kv: kv[1], reverse=True)
    best_style, best_score = ordered[0]
    second_style, second_score = ordered[1]
    third_style, third_score = ordered[2]
    fourth_style, fourth_score = ordered[3]
    close_gap = best_score - second_score
    close_gap3 = best_score - third_score
    spread4 = best_score - fourth_score

    if tempo_tipi in {"Yüksek Tempo", "Çok Yüksek"}:
        base_result = "Tempolu yarış, sonlarda kırılma beklenir"
    elif tempo_tipi == "Düşük Tempo":
        base_result = "Kontrollü tempo, yer tutma kritik"
    else:
        base_result = "Dengeli yarış, pozisyon savaşı belirleyici"

    if unknown_share >= 0.35 and spread4 <= 0.11:
        adv = (
            f"{map_style_to_advantage(best_style)} / {map_style_to_advantage(second_style)} / "
            f"{map_style_to_advantage(third_style)} / {map_style_to_advantage(fourth_style)}"
        )
        result = (
            f"{base_result} | Stil verisi dağınık: {best_style} ≈ {second_style} ≈ "
            f"{third_style} ≈ {fourth_style}"
        )
        return result, adv

    if spread4 <= 0.08:
        adv = (
            f"{map_style_to_advantage(best_style)} / {map_style_to_advantage(second_style)} / "
            f"{map_style_to_advantage(third_style)} / {map_style_to_advantage(fourth_style)}"
        )
        result = (
            f"{base_result} | Stil dengesi: {best_style} ≈ {second_style} ≈ "
            f"{third_style} ≈ {fourth_style}"
        )
        return result, adv

    if close_gap3 <= 0.07:
        adv = (
            f"{map_style_to_advantage(best_style)} / {map_style_to_advantage(second_style)} / "
            f"{map_style_to_advantage(third_style)}"
        )
        result = f"{base_result} | Stil dengesi: {best_style} ≈ {second_style} ≈ {third_style}"
        return result, adv

    if close_gap <= 0.06:
        adv = f"{map_style_to_advantage(best_style)} / {map_style_to_advantage(second_style)}"
        result = f"{base_result} | Stil dengesi: {best_style} ≈ {second_style}"
        return result, adv

    if (
        tempo_tipi in {"Yüksek Tempo", "Çok Yüksek"}
        and best_style == "Takipçi"
        and close_gap <= 0.14
    ):
        adv = f"{map_style_to_advantage(best_style)} / {map_style_to_advantage(second_style)}"
        result = f"{base_result} | Yakın ikinci stil: {second_style}"
        return result, adv

    hist_best = max(hist_probs.items(), key=lambda kv: kv[1]) if hist_probs else ("", 0.0)
    if hist_best[0] and hist_best[1] >= 48.0:
        result = f"{base_result} | Tarihsel sinyal: {hist_best[0]} %{hist_best[1]:.1f}"
    else:
        result = base_result

    return result, map_style_to_advantage(best_style)


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
            last_surface = normalize_surface(get_first(row, "Son Pist", "Son Pist"))

            race_horses.setdefault(current_race, []).append(
                HorseRow(
                    race=current_race,
                    name=horse_name,
                    style_1=get_first(row, "Stil Etiketi").strip(),
                    style_2=get_first(row, "Stil Etiketi 2").strip(),
                    output_value=parse_output(output_raw),
                    over_5s=over_5s,
                    track_cond=track_cond,
                    last_surface=last_surface,
                )
            )

    return race_horses


def build_models(input_csv: Path, hist_models: dict[str, SurfaceModel]) -> tuple[list[RaceTempo], list[HorseModel]]:
    race_horses = parse_race_horses(input_csv)
    races: list[RaceTempo] = []
    horse_models: list[HorseModel] = []

    for race_name, horses in race_horses.items():
        if not horses:
            continue

        valid_outputs = [h.output_value for h in horses if h.output_value is not None]
        ortalama_cikti = (sum(valid_outputs) / len(valid_outputs)) if valid_outputs else 1.0

        surface_counter = Counter(h.last_surface for h in horses if h.last_surface)
        race_surface = surface_counter.most_common(1)[0][0] if surface_counter else "Kum"

        race = RaceTempo(race=race_name, horse_count=len(horses), ortalama_cikti=ortalama_cikti, race_surface=race_surface)

        temp_katkilar: list[float] = []
        leader_weight = takip_weight = orta_weight = sprinter_weight = unknown_weight = 0.0
        for h in horses:
            output_used = h.output_value if h.output_value is not None else ortalama_cikti
            guc = (ortalama_cikti / output_used) if output_used else 1.0

            pace = pace_weight(h.style_1) + 0.60 * pace_weight(h.style_2)
            tempo_katkisi = pace * (0.82 + 0.38 * guc)
            if h.over_5s:
                tempo_katkisi *= 0.86
            temp_katkilar.append(tempo_katkisi)

            s1 = normalize_style(h.style_1)
            s2 = normalize_style(h.style_2)
            if s1 == "Önde Kaçan":
                leader_weight += 1.0
            if s2 == "Önde Kaçan":
                leader_weight += 0.55
            if s1 == "Takipçi":
                takip_weight += 1.0
            if s2 == "Takipçi":
                takip_weight += 0.55
            if s1 == "Orta Grup":
                orta_weight += 1.0
            if s2 == "Orta Grup":
                orta_weight += 0.55
            if s1 == "Sprinter":
                sprinter_weight += 1.0
            if s2 == "Sprinter":
                sprinter_weight += 0.55
            if not s1:
                unknown_weight += 1.0
            if h.style_2.strip() and not s2:
                unknown_weight += 0.55

        race.total_tempo = sum(temp_katkilar)
        race.tempo_tipi = classify_tempo_index(race.tempo_index)
        race.siddet_seviyesi = classify_total_tempo(race.total_tempo)
        race.yaris_yapisi = classify_field_size(race.horse_count)

        denom = max(1.0, race.horse_count * 1.55)
        leader_share = leader_weight / denom
        takip_share = takip_weight / denom
        orta_share = orta_weight / denom
        sprinter_share = sprinter_weight / denom
        unknown_share = unknown_weight / denom

        hist_probs = {k: 25.0 for k in STYLE_SET}
        hist_fit = {k: 0.0 for k in STYLE_SET}
        sm = hist_models.get(race_surface)
        if sm is not None:
            race.tahmini_400m = estimate_400m_sec(sm, race.tempo_index)
            probs = predict_style_probs(sm, race.tahmini_400m)
            hist_probs = probs
            # convert history probs into fit bonus around neutral 25%
            hist_fit = {k: (probs[k] - 25.0) / 18.0 for k in STYLE_SET}
        else:
            race.tahmini_400m = 0.0

        race.karar_sonucu, race.avantajli_at_turu = decision_matrix(
            race.tempo_tipi,
            race.siddet_seviyesi,
            leader_share,
            takip_share,
            orta_share,
            sprinter_share,
            unknown_share,
            hist_probs,
        )

        for h in horses:
            output_used = h.output_value if h.output_value is not None else ortalama_cikti
            guc = (ortalama_cikti / output_used) if output_used else 1.0

            pace = pace_weight(h.style_1) + 0.60 * pace_weight(h.style_2)
            tempo_katkisi = pace * (0.82 + 0.38 * guc)
            if h.over_5s:
                tempo_katkisi *= 0.86

            s1 = normalize_style(h.style_1)
            s2 = normalize_style(h.style_2)
            fit = hist_fit.get(s1, 0.0) + 0.55 * hist_fit.get(s2, 0.0)

            base = 1.0 / output_used
            wet_adj = 0.08 if h.track_cond else 0.0
            penalty_5s = -0.10 if h.over_5s else 0.0
            kazanma_skoru = base * 0.62 + fit * 0.24 + tempo_katkisi * 0.10 + wet_adj + penalty_5s

            dayaniklilik = None
            if race.tempo_tipi in {"Yüksek Tempo", "Çok Yüksek"}:
                dayaniklilik = guc * 2.0 - max(0.0, pace) * 0.35

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
            sonuc = r.karar_sonucu
            if r.tahmini_400m > 0:
                sonuc = f"{sonuc} | Tahmini 400m: {r.tahmini_400m:.2f}"
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
                    "Karar Sonucu": sonuc,
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
    parser.add_argument(
        "--historical-summary",
        default=r"C:\Users\emir\Desktop\test\sonuçlar\tracus_400_last_year\first400_leader_tempo_vs_winner_style_prob_summary.csv",
        help="Tarihsel tempo-stil ozet CSV (model bu dosyadan öğrenir)",
    )
    args = parser.parse_args()

    input_csv = Path(args.input)
    output_csv = Path(args.output)
    hist_path = Path(args.historical_summary) if args.historical_summary else None

    hist_models = load_historical_models(hist_path)
    races, models = build_models(input_csv, hist_models)
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
