"""
Her yarış türü (şehir/pist/mesafe) için kazanan atların ortalamasını (ideal profil) bulur,
her at için bu profile olan euclidean mesafeyi hesaplar ve yeni bir feature olarak ekler.
Çıktı: E:\data\ml_program_profile.parquet
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import euclidean_distances

print("\n📁 Veriler yükleniyor...")
program = pd.read_parquet(r"E:\data\ml_program.parquet")

# Profil feature'ları (sadece sayısal ve önemli olanlar)
profile_features = [
    'horse_weight', 'horse_age', 'handicap_weight', 'kgs',
    'jockey_win_rate', 'trainer_win_rate', 'owner_win_rate',
    'jockey_races', 'trainer_races',
    'horse_avg_time', 'horse_min_time', 'horse_std_time', 'horse_race_count',
    'horse_capacity_usage', 'horse_time_consistency', 'horse_best_vs_avg_ratio',
    'experience_level', 'horse_avg_speed', 'horse_best_speed', 'time_per_km'
]

# Yarış türü tanımı
program['race_type'] = (
    program['city_code'].astype(str) + '_' +
    program['track_code'].astype(str) + '_' +
    program['distance'].astype(str)
)

# Sadece numerik feature'lar
profile_features = [col for col in profile_features if col in program.select_dtypes(include=[np.number]).columns]

# Eğitim seti: 2021-2025 (test seti hariç)
program['race_date'] = pd.to_datetime(program['race_date'])
train_program = program[program['race_date'] < '2026-01-01'].copy()

# Her yarış türü için ideal profil (kazananların ortalaması)
sonuclar = pd.read_parquet(r"E:\data\ml_sonuclar.parquet")
winners = sonuclar[sonuclar['is_winner'] == 1][['race_id', 'horse_id']]
train_program = train_program.merge(winners, on=['race_id', 'horse_id'], how='inner')
profile_means = train_program.groupby('race_type')[profile_features].mean()

# Tüm program için scaler (feature'lar normalize edilecek)
scaler = StandardScaler()
scaler.fit(train_program[profile_features].fillna(0))

# Her at için ideal profile olan mesafeyi hesapla
profile_distance = []
for idx, row in program.iterrows():

    race_type = row['race_type']
    if race_type in profile_means.index:
        ideal_profile_vec = profile_means.loc[race_type].fillna(0).astype(float)
    else:
        ideal_profile_vec = profile_means.mean().fillna(0).astype(float)
    # Atın feature'larını eksiksiz al (eksik sütunları da sıfırla)
    at_features_vec = row.reindex(profile_features).fillna(0).astype(float)
    # DataFrame olarak feature isimleriyle birlikte scaler'a ver
    ideal_profile_df = pd.DataFrame([ideal_profile_vec], columns=profile_features)
    at_features_df = pd.DataFrame([at_features_vec], columns=profile_features)
    # Normalize et
    ideal_profile_scaled = scaler.transform(ideal_profile_df)
    at_features_scaled = scaler.transform(at_features_df)
    # Mesafe
    dist = euclidean_distances(at_features_scaled, ideal_profile_scaled).flatten()[0]
    profile_distance.append(dist)

program['profile_distance'] = profile_distance

# Kaydet
program.to_parquet(r"E:\data\ml_program_profile.parquet", compression='snappy', index=False)
print("✅ profile_distance feature eklendi ve kaydedildi: E\\data\\ml_program_profile.parquet")
