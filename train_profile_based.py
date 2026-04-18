"""
Profile-Based Similarity Matching Model
Her şehir + pist + mesafe kombinasyonu için kazanan atların profili oluşturulur
Test yarışında atlar bu profile en yakın olana göre sıralanır
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import euclidean_distances
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("🎯 PROFILE-BASED SIMILARITY MATCHING MODEL")
print("=" * 80)

# Veriyi yükle
print("\n📁 Veriler yükleniyor...")
program = pd.read_parquet(r"E:\data\ml_program.parquet")
sonuclar = pd.read_parquet(r"E:\data\ml_sonuclar.parquet")
time_data = pd.read_parquet(r"E:\data\ml_time.parquet")

print(f"Program: {len(program):,} kayıt")
print(f"Sonuç: {len(sonuclar):,} kayıt")
print(f"Time: {len(time_data):,} kayıt")

# Birleştir
data = program.merge(
    sonuclar[['race_id', 'horse_id', 'is_winner', 'is_top3', 'finish_position_clean']],
    on=['race_id', 'horse_id'],
    how='inner'
)

time_features = time_data[['race_id', 'horse_id', 'did_finish', 
                           'horse_avg_time', 'horse_min_time', 'horse_max_time',
                           'horse_std_time', 'horse_race_count',
                           'horse_capacity_usage', 'horse_time_consistency', 
                           'horse_best_vs_avg_ratio', 'horse_time_zscore',
                           'horse_vs_race_avg', 'horse_vs_race_best', 'experience_level']]

data = data.merge(time_features, on=['race_id', 'horse_id'], how='left')

# Hız hesapla
data['horse_avg_speed'] = data['distance'] / (data['horse_avg_time'] + 0.1)
data['horse_best_speed'] = data['distance'] / (data['horse_min_time'] + 0.1)
data['time_per_km'] = (data['horse_avg_time'] / (data['distance'] / 1000.0)).fillna(0)

# Sadece tamamlanmış yarışlar
data = data[data['finish_position_clean'].notna()].copy()
data['race_date'] = pd.to_datetime(data['race_date'])

print(f"Tamamlanmış yarışlar: {len(data):,} kayıt")

# TRAIN-TEST SPLIT (ZAMAN BAZLI)
train_data = data[data['race_date'] < '2026-01-01'].copy()
test_data = data[data['race_date'] >= '2026-01-01'].copy()

print(f"\n📚 EĞİTİM (2021-2025): {len(train_data):,} kayıt")
print(f"🧪 TEST (2026 Ocak): {len(test_data):,} kayıt")

# FEATURE COLUMNS - Atın karakteristikleri (yarış özellikleri DEĞİL!)
# SADECE NUMERİK FEATURE'LAR - kategorik değil!
profile_features = [
    # At özellikleri
    'horse_weight',
    'horse_age',
    'handicap_weight',      # Türkiye puanı (50-70)
    'kgs',
    
    # Jockey/Trainer/Owner başarı oranları
    'jockey_win_rate',
    'trainer_win_rate',
    'owner_win_rate',
    'jockey_races',
    'trainer_races',
    
    # Time features - Atın geçmiş performansı
    'horse_avg_time',
    'horse_min_time',
    'horse_std_time',
    'horse_race_count',
    'horse_capacity_usage',
    'horse_time_consistency',
    'horse_best_vs_avg_ratio',
    'experience_level',
    'horse_avg_speed',
    'horse_best_speed',
    'time_per_km',
]

# Sadece numerik sütunlar olduğundan emin ol
profile_features = [col for col in profile_features if col in data.select_dtypes(include=[np.number]).columns]

# YARIŞ TÜRÜ TANIMLAMA - Şehir + Pist + Mesafe
train_data['race_type'] = (
    train_data['city_code'].astype(str) + '_' + 
    train_data['track_code'].astype(str) + '_' + 
    train_data['distance'].astype(str)
)

test_data['race_type'] = (
    test_data['city_code'].astype(str) + '_' + 
    test_data['track_code'].astype(str) + '_' + 
    test_data['distance'].astype(str)
)

# ========== ADIM 1: HER YARIŞ TÜRÜ İÇİN KAZANAN ATLARIN PROFİLİNİ OLUŞTUR ==========
print("\n" + "=" * 80)
print("🏆 ADIM 1: KAZANAN AT PROFİLLERİ OLUŞTURULUYOR")
print("=" * 80)

# Sadece kazanan atları al
winners_only = train_data[train_data['is_winner'] == 1].copy()

print(f"\n📊 Toplam kazanan at: {len(winners_only):,}")
print(f"📊 Toplam yarış türü: {winners_only['race_type'].nunique():,}")

# Her yarış türü için kazanan atların ortalama profilini hesapla
winner_profiles = winners_only.groupby('race_type')[profile_features].mean()

print(f"\n✅ {len(winner_profiles)} farklı yarış türü için profil oluşturuldu")

# Örnek profiller göster
print("\n📋 ÖRNEK PROFİLLER:")
print("-" * 80)

# City ve track mapping'i oluştur (reverse engineering)
city_mapping = {
    0: 'Adana', 1: 'Ankara', 2: 'Antalya', 3: 'Bursa',
    4: 'Diyarbakir', 5: 'Elazig', 6: 'Istanbul', 7: 'Izmir',
    8: 'Kocaeli', 9: 'Urfa'
}

track_mapping = {
    0: 'Kum', 1: 'Çim', 2: 'Sentetik'
}

for i, (race_type, profile) in enumerate(winner_profiles.head(10).iterrows()):
    parts = race_type.split('_')
    city_code = int(parts[0]) if parts[0].isdigit() else -1
    track_code = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else -1
    distance = parts[2] if len(parts) > 2 else '?'
    
    city_name = city_mapping.get(city_code, f'City{city_code}')
    track_name = track_mapping.get(track_code, f'Track{track_code}')
    
    winner_count = len(winners_only[winners_only['race_type'] == race_type])
    print(f"\n{i+1}. {city_name} / {track_name} / {distance}m → {winner_count} kazanan at")
    
    # Sadece mevcut feature'ları göster
    if 'horse_weight' in profile.index:
        print(f"   Ağırlık: {profile['horse_weight']:.1f} kg")
    if 'horse_avg_speed' in profile.index:
        print(f"   Hız: {profile['horse_avg_speed']:.2f} m/s")
    if 'jockey_win_rate' in profile.index:
        print(f"   Jokey Win Rate: {profile['jockey_win_rate']:.3f}")
    if 'time_per_km' in profile.index:
        print(f"   Time/km: {profile['time_per_km']:.1f} s/km")

# ========== ADIM 2: NORMALİZASYON (SCALER) ==========
print("\n" + "=" * 80)
print("📏 ADIM 2: NORMALIZASYON")
print("=" * 80)

scaler = StandardScaler()
scaler.fit(train_data[profile_features].fillna(0))

print("✅ Scaler eğitildi")

# ========== ADIM 3: TEST YARIŞLARINDA BENZERLİK HESAPLA ==========
print("\n" + "=" * 80)
print("🎯 ADIM 3: TEST YARIŞLARINDA BENZERLİK HESAPLANIYOR")
print("=" * 80)

test_races = test_data['race_id'].unique()
print(f"\n📊 Test'te {len(test_races):,} yarış var")

predictions = []
top3_correct = 0
total_races = 0

for idx, race_id in enumerate(test_races):
    # Bu yarıştaki tüm atları al
    race_horses = test_data[test_data['race_id'] == race_id].copy()
    
    if len(race_horses) == 0:
        continue
    
    # Yarış türünü belirle
    race_type = race_horses['race_type'].iloc[0]
    
    # İdeal profil kaynağını belirle
    profile_source = ""
    if race_type not in winner_profiles.index:
        # Profil yoksa, genel ortalama kullan (fallback)
        ideal_profile = winners_only[profile_features].mean().values.reshape(1, -1)
        profile_source = "GENEL ORTALAMA (profil yok)"
        winner_count_for_profile = 0
    else:
        ideal_profile = winner_profiles.loc[race_type].values.reshape(1, -1)
        winner_count_for_profile = len(winners_only[winners_only['race_type'] == race_type])
        profile_source = f"{winner_count_for_profile} kazanan atın ortalaması"
    
    # Atların özelliklerini al ve normalize et
    horse_features = race_horses[profile_features].fillna(0).values
    
    # Normalize et
    ideal_profile_scaled = scaler.transform(ideal_profile)
    horse_features_scaled = scaler.transform(horse_features)
    
    # Euclidean distance hesapla (mesafe - küçük = daha benzer)
    distances = euclidean_distances(horse_features_scaled, ideal_profile_scaled).flatten()
    
    # En küçük mesafe = en benzer = 1. tahmin
    race_horses['similarity_distance'] = distances
    race_horses['predicted_rank'] = race_horses['similarity_distance'].rank(method='first')
    
    # Gerçek kazananı al
    actual_winner = race_horses[race_horses['is_winner'] == 1]
    actual_top3 = race_horses[race_horses['is_top3'] == 1]
    
    # İlk 3 yarışı DETAYLI göster
    if idx < 3:
        parts = race_type.split('_')
        city_code = int(parts[0]) if parts[0].isdigit() else -1
        track_code = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else -1
        distance = parts[2] if len(parts) > 2 else '?'
        
        city_mapping = {0: 'Adana', 1: 'Ankara', 2: 'Antalya', 3: 'Bursa',
                       4: 'Diyarbakir', 5: 'Elazig', 6: 'Istanbul', 7: 'Izmir',
                       8: 'Kocaeli', 9: 'Urfa'}
        track_mapping = {0: 'Kum', 1: 'Çim', 2: 'Sentetik'}
        
        city_name = city_mapping.get(city_code, f'City{city_code}')
        track_name = track_mapping.get(track_code, f'Track{track_code}')
        
        print(f"\n{'='*80}")
        print(f"YARIŞ #{idx+1}: {city_name} / {track_name} / {distance}m")
        print(f"İDEAL PROFİL: {profile_source}")
        print(f"{'='*80}")
        
        # HAYALİ İDEAL ATIN ÖZELLİKLERİNİ GÖSTER
        print(f"\n🎯 HAYALİ İDEAL ATIN ÖZELLİKLERİ ({city_name}/{track_name}/{distance}m için):")
        print("-" * 80)
        if race_type in winner_profiles.index:
            ideal_prof = winner_profiles.loc[race_type]
            print(f"Ağırlık: {ideal_prof.get('horse_weight', 0):.1f} kg")
            print(f"Hız: {ideal_prof.get('horse_avg_speed', 0):.2f} m/s")
            print(f"Time/km: {ideal_prof.get('time_per_km', 0):.1f} s/km")
            print(f"Jokey Win Rate: {ideal_prof.get('jockey_win_rate', 0):.3f}")
            print(f"Owner Win Rate: {ideal_prof.get('owner_win_rate', 0):.3f}")
            print(f"Handicap: {ideal_prof.get('handicap_weight', 0):.1f}")
            print(f"KGS: {ideal_prof.get('kgs', 0):.1f}")
        
        print(f"\n📊 BU YARIŞTAKİ ATLAR (en yakından en uzağa):")
        print("-" * 80)
        
        # Atları benzerliğe göre sırala ve göster
        race_horses_sorted = race_horses.sort_values('predicted_rank')
        for i, (_, horse) in enumerate(race_horses_sorted.head(5).iterrows()):
            winner_mark = "🏆 KAZANAN" if horse['is_winner'] == 1 else ""
            print(f"\n{int(horse['predicted_rank']):2d}. TAHMİN → Distance: {horse['similarity_distance']:.3f} {winner_mark}")
            print(f"   Ağırlık: {horse.get('horse_weight', 0):.1f} kg")
            print(f"   Hız: {horse.get('horse_avg_speed', 0):.2f} m/s")
            print(f"   Jokey Win Rate: {horse.get('jockey_win_rate', 0):.3f}")
            print(f"   Owner Win Rate: {horse.get('owner_win_rate', 0):.3f}")
    
    if len(actual_winner) > 0:
        winner_predicted_rank = race_horses[race_horses['is_winner'] == 1]['predicted_rank'].iloc[0]
        
        # TOP-3'e girdi mi?
        if winner_predicted_rank <= 3:
            top3_correct += 1
        
        total_races += 1
        
        predictions.append({
            'race_id': race_id,
            'race_type': race_type,
            'winner_predicted_rank': winner_predicted_rank,
            'top3_hit': winner_predicted_rank <= 3,
            'profile_source': profile_source
        })

# ========== SONUÇLAR ==========
print("\n" + "=" * 80)
print("📊 SONUÇLAR")
print("=" * 80)

top3_accuracy = (top3_correct / total_races) * 100 if total_races > 0 else 0

print(f"\n🎯 TOP-3 ACCURACY: {top3_accuracy:.2f}%")
print(f"   Toplam yarış: {total_races:,}")
print(f"   TOP-3'e giren: {top3_correct:,}")
print(f"   TOP-3'ü kaçıran: {total_races - top3_correct:,}")

# Detaylı istatistikler
predictions_df = pd.DataFrame(predictions)

if len(predictions_df) > 0:
    print(f"\n📈 TAHMİN DAĞILIMI:")
    rank_dist = predictions_df['winner_predicted_rank'].value_counts().sort_index()
    for rank, count in rank_dist.head(10).items():
        percentage = (count / len(predictions_df)) * 100
        bar = "█" * int(percentage / 2)
        print(f"   {int(rank):2d}. sıra: {count:4d} yarış ({percentage:5.2f}%) {bar}")

print("\n" + "=" * 80)
print("✅ TAMAMLANDI")
print("=" * 80)

# İlk 20 yarışın detayını göster
print("\n📋 İLK 20 YARIŞIN DETAYI:")
print("-" * 80)

city_mapping = {
    0: 'Adana', 1: 'Ankara', 2: 'Antalya', 3: 'Bursa',
    4: 'Diyarbakir', 5: 'Elazig', 6: 'Istanbul', 7: 'Izmir',
    8: 'Kocaeli', 9: 'Urfa'
}

track_mapping = {
    0: 'Kum', 1: 'Çim', 2: 'Sentetik'
}

for i, row in predictions_df.head(20).iterrows():
    parts = row['race_type'].split('_')
    city_code = int(parts[0]) if parts[0].isdigit() else -1
    track_code = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else -1
    distance = parts[2] if len(parts) > 2 else '?'
    
    city_name = city_mapping.get(city_code, f'City{city_code}')
    track_name = track_mapping.get(track_code, f'Track{track_code}')
    
    status = "✅" if row['top3_hit'] else "❌"
    race_display = f"{city_name}/{track_name}/{distance}m"
    print(f"{status} {race_display:30s} → Kazanan {int(row['winner_predicted_rank']):2d}. sırada")
