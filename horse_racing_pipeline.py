"""
Modern Horse Racing ML Pipeline
Katmanlı Feature Engineering + Ranking Model (XGBRanker)
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import pairwise_distances
from xgboost import XGBRanker

# 1. LOAD: Parquet dosyalarını oku
program = pd.read_parquet(r"E:/data/ml_program.parquet")
results = pd.read_parquet(r"E:/data/ml_sonuclar.parquet")

# 2. SORT: horse_id ve race_date'e göre sırala
program = program.sort_values(['horse_id', 'race_date'])
program['race_date'] = pd.to_datetime(program['race_date'])

# 3. ENGINEER: Rolling Window ve EMA ile form puanı
# Son 3 ve 5 yarış ortalaması
for window in [3, 5]:
    program[f'form_mean_{window}'] = (
        program.groupby('horse_id')['horse_avg_time']
        .rolling(window=window, min_periods=1).mean().reset_index(level=0, drop=True)
    )
# EMA: Son yarışa %50, bir öncekine %30, daha öncekine %20 ağırlık
ema_weights = np.array([0.5, 0.3, 0.2])
def calc_ema(times):
    times = times[-3:][::-1]  # Son 3 yarış, en yeni başta
    if len(times) < 3:
        times = np.pad(times, (0, 3-len(times)), constant_values=np.nan)
    return np.nansum(times * ema_weights)
program['form_ema'] = (
    program.groupby('horse_id')['horse_avg_time']
    .apply(lambda x: x.rolling(window=3, min_periods=1).apply(calc_ema, raw=True))
    .reset_index(level=0, drop=True)
)
# KGS (dinlenme süresi) performans çarpanı
program['kgs_effect'] = program['kgs'].apply(
    lambda x: 1.0 if 15 <= x <= 30 else (0.7 if x < 15 else 0.5 if x < 200 else 0.2)
)
# 4. Hız ve Derece Normalizasyonu
program['speed'] = program['distance'] / program['horse_avg_time']
# Pist varyantı: Aynı gün, aynı pistteki ortalama derece
program['track_variant'] = program.groupby(['race_date', 'track_code'])['horse_avg_time'].transform('mean') / program['horse_avg_time']
# Z-Score: Rakiplere göre hız
program['zscore_speed'] = (
    program['horse_avg_time'] / program.groupby(['race_id'])['horse_avg_time'].transform('mean')
)
# 5. İnsan Faktörü
# Jokey ROI: AGF ile win rate farkı
program['jockey_roi'] = program['jockey_win_rate'] - program['agf']
# Jokey-at uyumu
def jockey_horse_win(row):
    mask = (program['horse_id'] == row['horse_id']) & (program['jockey_id'] == row['jockey_id'])
    return program.loc[mask, 'is_winner'].mean() if mask.any() else np.nan
program['jockey_horse_win'] = program.apply(jockey_horse_win, axis=1)
# 6. SPLIT: Train/Test
train = program[program['race_date'] < '2026-01-01']
test = program[program['race_date'] >= '2026-01-01']

# 7. TRAIN: XGBRanker
features = [
    'form_mean_3', 'form_mean_5', 'form_ema', 'kgs_effect', 'speed', 'track_variant',
    'zscore_speed', 'jockey_roi', 'jockey_horse_win', 'jockey_win_rate', 'trainer_win_rate', 'owner_win_rate'
]
X_train = train[features].fillna(0)
y_train = train['is_winner']
group_train = train.groupby('race_id').size().to_list()
ranker = XGBRanker(objective='rank:pairwise', n_estimators=100, learning_rate=0.1)
ranker.fit(X_train, y_train, group_train)

# 8. EVALUATE: Top-1 ve Top-3 Hit Rate
X_test = test[features].fillna(0)
test['pred'] = ranker.predict(X_test)
def hit_rate(df, top_n=1):
    hits = 0
    for _, group in df.groupby('race_id'):
        top = group.nlargest(top_n, 'pred')
        hits += top['is_winner'].sum()
    return hits / df['race_id'].nunique()
print('Top-1 Hit Rate:', hit_rate(test, 1))
print('Top-3 Hit Rate:', hit_rate(test, 3))

# 9. Value Betting (Kelly Kriteri)
test['kelly_value'] = (test['pred'] * test['ganyan'] - 1) / (test['ganyan'] - 1)
print(test[['race_id', 'horse_id', 'pred', 'ganyan', 'kelly_value']].head())
