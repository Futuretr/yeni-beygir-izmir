"""
Yarış JSON dosyalarından feature çıkarma ve analiz scripti
"""

import json
import pandas as pd
from pathlib import Path
import numpy as np


def extract_horse_features(horse, race_track_type, race_distance):
    """Bir at için tüm feature'ları çıkar"""
    profile = horse.get('profile', {})
    career = profile.get('career_summary', {})
    track_stats = profile.get('track_stats', {})
    distance_stats = profile.get('distance_stats', {})
    city_stats = profile.get('city_stats', {})
    past_races = horse.get('past_races', [])
    
    # Son 3, 5 yarış performansı
    last_3_races = past_races[-3:] if len(past_races) >= 3 else past_races
    last_5_races = past_races[-5:] if len(past_races) >= 5 else past_races
    
    last_3_avg_finish = np.mean([r.get('finish_position', 999) for r in last_3_races]) if last_3_races else None
    last_5_avg_finish = np.mean([r.get('finish_position', 999) for r in last_5_races]) if last_5_races else None
    
    last_3_avg_time = np.mean([r.get('time_sec', 0) for r in last_3_races if r.get('time_sec')]) if last_3_races else None
    last_5_avg_time = np.mean([r.get('time_sec', 0) for r in last_5_races if r.get('time_sec')]) if last_5_races else None
    
    # Pist tipi uyumu
    track_match = track_stats.get(race_track_type, {})
    track_races = track_match.get('races', 0) if isinstance(track_match, dict) else 0
    track_avg_time = track_match.get('avg_time', None) if isinstance(track_match, dict) else None
    
    # Mesafe uyumu
    distance_match = distance_stats.get(str(race_distance), {})
    distance_races = distance_match.get('races', 0) if isinstance(distance_match, dict) else 0
    distance_avg_finish = distance_match.get('avg_finish', None) if isinstance(distance_match, dict) else None
    distance_avg_time = distance_match.get('avg_time', None) if isinstance(distance_match, dict) else None
    
    # Ganyan ve AGF parse
    ganyan_str = str(horse.get('ganyan', '')).replace(',', '.')
    try:
        ganyan = float(ganyan_str) if ganyan_str else None
    except:
        ganyan = None
    
    agf_str = str(horse.get('agf', '')).replace('%', '').strip()
    try:
        agf = float(agf_str) if agf_str else None
    except:
        agf = None
    
    # KGS (Koşu Galibiyet Sayısı)
    kgs = horse.get('kgs')
    try:
        kgs = int(kgs) if kgs else 0
    except:
        kgs = 0
    
    # Handicap weight
    handicap_weight = horse.get('handicap_weight')
    try:
        handicap_weight = int(handicap_weight) if handicap_weight else 0
    except:
        handicap_weight = 0
    
    # Son yarıştan kaç gün geçti
    last_race_days_ago = career.get('last_race_days_ago', 999)
    
    # Form (son 6 yarış)
    last_6_races = horse.get('last_6_races', '')
    
    # Feature dictionary
    features = {
        "horse_id": horse.get('horse_id'),
        "horse_name": horse.get('horse_name', ''),
        "horse_age": horse.get('horse_age', ''),
        "start_no": horse.get('start_no', ''),
        "horse_weight": horse.get('horse_weight'),
        "handicap_weight": handicap_weight,
        
        # Kariyer istatistikleri
        "career_total_races": career.get('total_races', 0),
        "career_avg_finish": career.get('avg_finish_position', None),
        "career_avg_time": career.get('avg_time_sec', None),
        "last_race_days_ago": last_race_days_ago,
        
        # Son yarış performansları
        "last_3_avg_finish": last_3_avg_finish,
        "last_5_avg_finish": last_5_avg_finish,
        "last_3_avg_time": last_3_avg_time,
        "last_5_avg_time": last_5_avg_time,
        "last_6_races": last_6_races,
        
        # Pist ve mesafe uyumu
        "track_type_races": track_races,
        "track_type_avg_time": track_avg_time,
        "distance_races": distance_races,
        "distance_avg_finish": distance_avg_finish,
        "distance_avg_time": distance_avg_time,
        
        # Bahis verileri
        "ganyan": ganyan,
        "agf": agf,
        "kgs": kgs,
        
        # Jokey ve antrenör
        "jockey_id": horse.get('jockey_id'),
        "jockey_name": horse.get('jockey_name', ''),
        "trainer_id": horse.get('trainer_id'),
        "trainer_name": horse.get('trainer_name', ''),
        
        # Owner
        "owner_id": horse.get('owner_id'),
        "owner_name": horse.get('owner_name', ''),
        
        # Baba ve anne
        "father_id": horse.get('father_id'),
        "father_name": horse.get('father_name', ''),
        "mother_id": horse.get('mother_id'),
        "mother_name": horse.get('mother_name', ''),
    }
    
    return features


def calculate_prediction_score(row):
    """Basit bir tahmin skoru hesapla"""
    score = 0
    
    # Son 3 yarış performansı (düşük derece = yüksek skor)
    if pd.notna(row['last_3_avg_finish']):
        score += (15 - row['last_3_avg_finish']) * 10
    
    # Kariyer ortalaması
    if pd.notna(row['career_avg_finish']):
        score += (15 - row['career_avg_finish']) * 5
    
    # AGF (düşük AGF = favori)
    if pd.notna(row['agf']):
        score += (100 - row['agf']) * 0.5
    
    # Pist tipi deneyimi
    if row['track_type_races'] > 0:
        score += row['track_type_races'] * 2
    
    # Mesafe deneyimi
    if row['distance_races'] > 0:
        score += row['distance_races'] * 3
    
    # Mesafe performansı
    if pd.notna(row['distance_avg_finish']):
        score += (15 - row['distance_avg_finish']) * 8
    
    # KGS (galibiyet sayısı)
    score += row['kgs'] * 5
    
    # Son yarıştan geçen süre (çok uzun olmasın)
    if row['last_race_days_ago'] < 30:
        score += 10
    elif row['last_race_days_ago'] < 60:
        score += 5
    
    return score


def analyze_race(race_json_path):
    """Bir yarış dosyasını analiz et"""
    
    print(f"\n{'='*80}")
    print(f"Yarış Analizi: {race_json_path}")
    print(f"{'='*80}\n")
    
    # JSON dosyasını oku
    with open(race_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # İlk elementi al (liste içinde)
    race_data = data[0] if isinstance(data, list) else data
    
    # Yarış bilgileri
    race_info = {
        "race_id": race_data.get('race_id'),
        "race_date": race_data.get('race_date'),
        "race_number": race_data.get('race_number'),
        "race_category": race_data.get('race_category', ''),
        "age_group": race_data.get('age_group', ''),
        "city": race_data.get('city', ''),
        "track_type": race_data.get('track_type', ''),
        "distance": race_data.get('distance'),
    }
    
    print(f"📍 Şehir: {race_info['city']}")
    print(f"📅 Tarih: {race_info['race_date']}")
    print(f"🏁 Yarış No: {race_info['race_number']}")
    print(f"📊 Kategori: {race_info['race_category']}")
    print(f"🏇 Yaş Grubu: {race_info['age_group']}")
    print(f"🛤️  Pist: {race_info['track_type']}")
    print(f"📏 Mesafe: {race_info['distance']}m")
    print(f"\n{'='*80}\n")
    
    # At feature'larını çıkar
    horses_features = []
    for horse in race_data.get('horses', []):
        features = extract_horse_features(
            horse, 
            race_info['track_type'], 
            race_info['distance']
        )
        horses_features.append(features)
    
    # DataFrame oluştur
    df = pd.DataFrame(horses_features)
    
    # Tahmin skoru hesapla
    df['prediction_score'] = df.apply(calculate_prediction_score, axis=1)
    
    # Sıralama
    df_sorted = df.sort_values('prediction_score', ascending=False).reset_index(drop=True)
    df_sorted['predicted_rank'] = range(1, len(df_sorted) + 1)
    
    return race_info, df_sorted


def display_predictions(df, top_n=10):
    """Tahminleri görsel olarak göster"""
    
    print(f"🏆 TAHMİN SIRALAMA (Top {top_n})")
    print(f"{'='*80}\n")
    
    # Gösterilecek sütunlar
    display_cols = [
        'predicted_rank',
        'start_no',
        'horse_name',
        'prediction_score',
        'last_3_avg_finish',
        'career_avg_finish',
        'ganyan',
        'agf',
        'kgs',
        'distance_avg_finish',
        'jockey_name',
    ]
    
    # Mevcut sütunları filtrele
    available_cols = [col for col in display_cols if col in df.columns]
    
    # Top N'i göster
    df_display = df[available_cols].head(top_n)
    
    # Formatla
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 30)
    
    print(df_display.to_string(index=False))
    print(f"\n{'='*80}\n")
    
    # Detaylı top 3
    print("📌 DETAYLI TOP 3 ANALİZ\n")
    for idx, row in df.head(3).iterrows():
        print(f"{row['predicted_rank']}. {row['horse_name']} (#{row['start_no']})")
        print(f"   Skor: {row['prediction_score']:.1f}")
        print(f"   Son 3 yarış ort: {row['last_3_avg_finish']:.2f}" if pd.notna(row['last_3_avg_finish']) else "   Son 3 yarış ort: N/A")
        print(f"   Kariyer ort: {row['career_avg_finish']:.2f}" if pd.notna(row['career_avg_finish']) else "   Kariyer ort: N/A")
        print(f"   Bu mesafede ort: {row['distance_avg_finish']:.2f}" if pd.notna(row['distance_avg_finish']) else "   Bu mesafede ort: N/A")
        print(f"   Ganyan: {row['ganyan']}" if pd.notna(row['ganyan']) else "   Ganyan: N/A")
        print(f"   AGF: %{row['agf']}" if pd.notna(row['agf']) else "   AGF: N/A")
        print(f"   KGS: {row['kgs']}")
        print(f"   Jokey: {row['jockey_name']}")
        print(f"   Antrenör: {row['trainer_name']}")
        print()


def main():
    """Ana fonksiyon"""
    
    # Test için örnek bir yarış dosyası
    race_file = Path(r"E:\data\race_jsons\Antalya\2026\222832.json")
    
    if not race_file.exists():
        print(f"❌ Dosya bulunamadı: {race_file}")
        print("\nMevcut dosyaları kontrol ediyorum...")
        
        # İlk bulduğu dosyayı kullan
        race_jsons_dir = Path(r"E:\data\race_jsons")
        all_files = list(race_jsons_dir.glob("**/*.json"))
        
        if all_files:
            race_file = all_files[0]
            print(f"✓ İlk bulunan dosya kullanılıyor: {race_file}")
        else:
            print("❌ Hiç JSON dosyası bulunamadı!")
            return
    
    # Analiz yap
    race_info, df = analyze_race(race_file)
    
    # Tahminleri göster
    display_predictions(df, top_n=10)
    
    # DataFrame'i kaydet
    output_file = Path("race_analysis_output.csv")
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✓ Detaylı analiz kaydedildi: {output_file}\n")
    
    return df


if __name__ == "__main__":
    df = main()
