
import os, json, zipfile
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np

def _iter_zip_json(zip_path: str):
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            if name.endswith(".json"):
                try:
                    yield name, json.loads(zf.read(name))
                except Exception as e:
                    raise RuntimeError(f"Failed reading {name} from {zip_path}: {e}")

def load_sonuclar_table(sonuclar_zip: str) -> pd.DataFrame:
    """Explodes nested daily->race structure into a flat participation table."""
    rows: List[Dict[str, Any]] = []
    for name, data in _iter_zip_json(sonuclar_zip):
        # data: {day: {race_index: [horse_rows...]}}
        if not isinstance(data, dict):
            continue
        for day_key, day_val in data.items():
            if not isinstance(day_val, dict):
                continue
            for race_key, horse_list in day_val.items():
                if not isinstance(horse_list, list):
                    continue
                for r in horse_list:
                    if not isinstance(r, dict):
                        continue
                    rows.append(r)
    df = pd.DataFrame(rows)

    # Normalize types
    if "race_date" in df.columns:
        df["race_date"] = pd.to_datetime(df["race_date"], utc=True, errors="coerce").dt.tz_convert(None)
    for c in ["race_id","horse_id","jockey_id","trainer_id","start_no","race_number","distance"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    if "finish_position" in df.columns:
        df["finish_position"] = pd.to_numeric(df["finish_position"], errors="coerce")
    for c in ["handicap_weight","horse_weight","ganyan","agf"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Convenience labels
    if "finish_position" in df.columns:
        df["is_win"] = (df["finish_position"] == 1).astype("Int64")
        df["is_top3"] = (df["finish_position"].between(1,3)).astype("Int64")

    return df

def load_horse_profile_features(horse_profiles_zip: str) -> pd.DataFrame:
    """Creates leakage-free rolling features per (horse_id, race_id) using profile race history.
    Output rows correspond to races that appear in horse profiles; feature values are computed using ONLY races strictly before that race (shifted).
    """
    out_frames: List[pd.DataFrame] = []
    with zipfile.ZipFile(horse_profiles_zip, "r") as zf:
        for name in zf.namelist():
            if not name.endswith(".json"):
                continue
            d = json.loads(zf.read(name))
            horse_id = d.get("horse_id")
            races = d.get("races") or []
            if not horse_id or not isinstance(races, list) or len(races) == 0:
                continue

            hdf = pd.DataFrame(races)
            if hdf.empty:
                continue

            hdf["horse_id"] = horse_id
            hdf["date"] = pd.to_datetime(hdf["date"], errors="coerce")
            hdf = hdf.dropna(subset=["date","race_id"]).sort_values(["date","race_id"]).reset_index(drop=True)

            # Basic numeric clean
            for c in ["race_id","distance","finish_position","time_sec","horse_weight","jockey_id","trainer_id","class_level"]:
                if c in hdf.columns:
                    hdf[c] = pd.to_numeric(hdf[c], errors="coerce")
            hdf["pace_sec_per_m"] = hdf["time_sec"] / hdf["distance"]

            # Leakage-free rolling using shift
            fp = hdf["finish_position"].astype(float)
            pace = hdf["pace_sec_per_m"].astype(float)

            hdf["prev_date"] = hdf["date"].shift(1)
            hdf["days_since_last"] = (hdf["date"] - hdf["prev_date"]).dt.days

            hdf["last_finish"] = fp.shift(1)
            hdf["avg_finish_last3"] = fp.shift(1).rolling(3, min_periods=1).mean()
            hdf["avg_finish_prev3"] = fp.shift(4).rolling(3, min_periods=1).mean()
            hdf["form_trend"] = hdf["avg_finish_prev3"] - hdf["avg_finish_last3"]  # + means improving

            hdf["win_rate_last10"] = (fp.shift(1).eq(1)).rolling(10, min_periods=1).mean()
            hdf["top3_rate_last10"] = (fp.shift(1).between(1,3)).rolling(10, min_periods=1).mean()

            hdf["pace_last"] = pace.shift(1)
            hdf["pace_best_last5"] = pace.shift(1).rolling(5, min_periods=1).min()

            # Track & distance fit (expanding means), shifted to avoid leakage
            if "track_type" in hdf.columns:
                hdf["avg_finish_same_track"] = (
                    hdf.groupby(["horse_id","track_type"])["finish_position"]
                       .apply(lambda s: s.shift(1).expanding(min_periods=1).mean())
                       .reset_index(level=[0,1], drop=True)
                )
            else:
                hdf["avg_finish_same_track"] = np.nan

            if "distance" in hdf.columns:
                hdf["dist_bin"] = (np.round(hdf["distance"] / 200) * 200).astype("Int64")
                hdf["avg_finish_same_distbin"] = (
                    hdf.groupby(["horse_id","dist_bin"])["finish_position"]
                       .apply(lambda s: s.shift(1).expanding(min_periods=1).mean())
                       .reset_index(level=[0,1], drop=True)
                )
            else:
                hdf["dist_bin"] = np.nan
                hdf["avg_finish_same_distbin"] = np.nan

            # Class change proxy
            if "class_level" in hdf.columns:
                hdf["last_class"] = hdf["class_level"].shift(1)
                hdf["class_delta"] = hdf["class_level"] - hdf["last_class"]
            else:
                hdf["class_delta"] = np.nan

            keep_cols = [
                "horse_id","race_id","date","city","track_type","distance","dist_bin",
                "days_since_last",
                "last_finish","avg_finish_last3","form_trend","win_rate_last10","top3_rate_last10",
                "pace_last","pace_best_last5",
                "avg_finish_same_track","avg_finish_same_distbin",
                "class_delta",
            ]
            out_frames.append(hdf[keep_cols])

    if not out_frames:
        return pd.DataFrame()
    feats = pd.concat(out_frames, ignore_index=True)
    # For joining later: date aligns with profile race date; we'll merge primarily on (horse_id, race_id)
    return feats

def add_leakage_free_jockey_trainer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Rolling stats computed from results, shifted so a row never uses same-race outcome."""
    df = df.sort_values(["race_date","race_id","race_number","horse_id"]).reset_index(drop=True)

    # Use last N rides (simple and robust). Time-window rolling is possible but heavier.
    def _rolling_rate(group, col_is_win, window):
        s = group[col_is_win].astype(float)
        return s.shift(1).rolling(window, min_periods=10).mean()

    if "jockey_id" in df.columns and "is_win" in df.columns:
        df["jockey_win_rate_last50"] = df.groupby("jockey_id", dropna=False).apply(
            lambda g: _rolling_rate(g, "is_win", 50)
        ).reset_index(level=0, drop=True)

        df["jockey_top3_rate_last50"] = df.groupby("jockey_id", dropna=False).apply(
            lambda g: g["is_top3"].astype(float).shift(1).rolling(50, min_periods=10).mean()
        ).reset_index(level=0, drop=True)

    if "trainer_id" in df.columns and "is_win" in df.columns:
        df["trainer_win_rate_last50"] = df.groupby("trainer_id", dropna=False).apply(
            lambda g: _rolling_rate(g, "is_win", 50)
        ).reset_index(level=0, drop=True)

        df["trainer_top3_rate_last50"] = df.groupby("trainer_id", dropna=False).apply(
            lambda g: g["is_top3"].astype(float).shift(1).rolling(50, min_periods=10).mean()
        ).reset_index(level=0, drop=True)

    return df

def add_startno_bias(df: pd.DataFrame) -> pd.DataFrame:
    """Start number historical win-rate by (track_type, dist_bin, start_no), leakage-free (shifted)."""
    if not set(["track_type","distance","start_no","is_win"]).issubset(df.columns):
        return df
    df = df.copy()
    df["dist_bin"] = (np.round(df["distance"].astype(float) / 200) * 200).astype("Int64")
    df = df.sort_values(["race_date","race_id","horse_id"]).reset_index(drop=True)

    key = ["track_type","dist_bin","start_no"]
    df["startno_win_rate_hist"] = (
        df.groupby(key, dropna=False)["is_win"]
          .apply(lambda s: s.astype(float).shift(1).expanding(min_periods=100).mean())
          .reset_index(level=key, drop=True)
    )
    return df

def build_feature_dataset(sonuclar_zip: str, horse_profiles_zip: str) -> pd.DataFrame:
    # 1) Base participation & labels from results
    base = load_sonuclar_table(sonuclar_zip)

    # 2) Horse history features from profiles (per race_id)
    hfeats = load_horse_profile_features(horse_profiles_zip)
    if not hfeats.empty:
        # Merge on horse_id + race_id
        base = base.merge(
            hfeats.drop(columns=["date"], errors="ignore"),
            on=["horse_id","race_id"],
            how="left",
            suffixes=("","_hp")
        )

    # 3) Leakage-free jockey/trainer rolling features from results history
    base = add_leakage_free_jockey_trainer_features(base)

    # 4) Start number bias
    base = add_startno_bias(base)

    # 5) Final cleanup
    # Drop rows with missing critical keys
    base = base.dropna(subset=["race_id","horse_id","race_date"])

    return base

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--sonuclar_zip", required=True)
    ap.add_argument("--horse_profiles_zip", required=True)
    ap.add_argument("--out_parquet", default="features.parquet")
    args = ap.parse_args()

    df = build_feature_dataset(args.sonuclar_zip, args.horse_profiles_zip)
    df.to_parquet(args.out_parquet, index=False)
    print("Wrote", args.out_parquet, "rows", len(df), "cols", df.shape[1])
