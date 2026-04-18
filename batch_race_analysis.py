"""
Toplu yarış analizi ve karşılaştırma scripti
Birden fazla yarışı analiz edip sonuçları karşılaştırır
"""

import json
import pandas as pd
from pathlib import Path
import numpy as np
from analyze_race_features import extract_horse_features, calculate_prediction_score


def analyze_multiple_races(race_files, output_dir=None):
    """Birden fazla yarışı analiz et"""
    
    all_results = []
    
    for race_file in race_files:
        print(f"Analiz ediliyor: {race_file.name}")
        
        # JSON dosyasını oku
        with open(race_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        race_data = data[0] if isinstance(data, list) else data
        
        # Yarış bilgileri
        race_info = {
            "race_id": race_data.get('race_id'),
            "race_date": race_data.get('race_date'),
            "race_number": race_data.get('race_number'),
            "city": race_data.get('city', ''),
            "track_type": race_data.get('track_type', ''),
            "distance": race_data.get('distance'),
            "race_category": race_data.get('race_category', ''),
        }
        
        # At feature'larını çıkar
        for horse in race_data.get('horses', []):
            features = extract_horse_features(
                horse, 
                race_info['track_type'], 
                race_info['distance']
            )
            
            # Yarış bilgilerini ekle
            features.update({
                "race_id": race_info['race_id'],
                "race_date": race_info['race_date'],
                "race_number": race_info['race_number'],
                "race_city": race_info['city'],
                "race_track_type": race_info['track_type'],
                "race_distance": race_info['distance'],
                "race_category": race_info['race_category'],
            })
            
            all_results.append(features)
    
    # DataFrame oluştur
    df = pd.DataFrame(all_results)
    
    # Tahmin skoru hesapla
    df['prediction_score'] = df.apply(calculate_prediction_score, axis=1)
    
    # Yarış bazında sıralama
    df['predicted_rank'] = df.groupby('race_id')['prediction_score'].rank(ascending=False, method='first').astype(int)
    
    # Kaydet
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / 'batch_race_analysis.csv'
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n✓ Toplu analiz kaydedildi: {output_file}")
        
        # Özet rapor
        summary_file = output_dir / 'analysis_summary.txt'
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("TOPLU YARIŞ ANALİZİ ÖZETİ\n")
            f.write("="*80 + "\n\n")
            f.write(f"Toplam Yarış: {df['race_id'].nunique()}\n")
            f.write(f"Toplam At: {len(df)}\n")
            f.write(f"Ortalama Yarış Başına At: {len(df) / df['race_id'].nunique():.1f}\n\n")
            
            f.write("Şehir Dağılımı:\n")
            f.write(df['race_city'].value_counts().to_string())
            f.write("\n\nPist Tipi Dağılımı:\n")
            f.write(df['race_track_type'].value_counts().to_string())
            f.write("\n\nMesafe Dağılımı:\n")
            f.write(df['race_distance'].value_counts().to_string())
        
        print(f"✓ Özet rapor kaydedildi: {summary_file}")
    
    return df


def filter_races_by_criteria(race_jsons_dir, city=None, track_type=None, distance=None, 
                               start_date=None, end_date=None, limit=10):
    """Kriterlere göre yarış dosyalarını filtrele"""
    
    race_jsons_dir = Path(race_jsons_dir)
    all_files = list(race_jsons_dir.glob("**/*.json"))
    
    filtered_files = []
    
    for file_path in all_files[:limit*5]:  # İlk N*5 dosyayı kontrol et
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            race_data = data[0] if isinstance(data, list) else data
            
            # Filtreler
            if city and race_data.get('city') != city:
                continue
            if track_type and race_data.get('track_type') != track_type:
                continue
            if distance and race_data.get('distance') != distance:
                continue
            if start_date and race_data.get('race_date', '') < start_date:
                continue
            if end_date and race_data.get('race_date', '') > end_date:
                continue
            
            filtered_files.append(file_path)
            
            if len(filtered_files) >= limit:
                break
                
        except Exception as e:
            continue
    
    return filtered_files


def get_top_performers(df, metric='prediction_score', top_n=20):
    """En iyi performans gösteren atları bul"""
    
    print(f"\n{'='*80}")
    print(f"EN İYİ PERFORMANS GÖSTEREN ATLAR ({metric.upper()})")
    print(f"{'='*80}\n")
    
    # At bazında gruplama
    horse_stats = df.groupby('horse_name').agg({
        'prediction_score': 'mean',
        'last_3_avg_finish': 'mean',
        'career_avg_finish': 'mean',
        'ganyan': 'mean',
        'kgs': 'max',
        'race_id': 'count',
        'predicted_rank': 'mean',
    }).round(2)
    
    horse_stats.columns = ['avg_score', 'avg_last_3_finish', 'career_avg_finish', 
                           'avg_ganyan', 'max_kgs', 'race_count', 'avg_predicted_rank']
    
    # Sırala
    horse_stats = horse_stats.sort_values('avg_score', ascending=False).head(top_n)
    
    print(horse_stats.to_string())
    print(f"\n{'='*80}\n")
    
    return horse_stats


def compare_jockeys(df, min_races=5):
    """Jokeyları karşılaştır"""
    
    print(f"\n{'='*80}")
    print(f"JOKEY KARŞILAŞTIRMASI (Min {min_races} yarış)")
    print(f"{'='*80}\n")
    
    jockey_stats = df.groupby('jockey_name').agg({
        'race_id': 'count',
        'prediction_score': 'mean',
        'last_3_avg_finish': 'mean',
        'predicted_rank': 'mean',
        'kgs': 'sum',
    }).round(2)
    
    jockey_stats.columns = ['race_count', 'avg_score', 'avg_last_3_finish', 
                           'avg_predicted_rank', 'total_kgs']
    
    # Min yarış filtresi
    jockey_stats = jockey_stats[jockey_stats['race_count'] >= min_races]
    jockey_stats = jockey_stats.sort_values('avg_score', ascending=False).head(20)
    
    print(jockey_stats.to_string())
    print(f"\n{'='*80}\n")
    
    return jockey_stats


def main():
    """Ana fonksiyon"""
    
    race_jsons_dir = Path(r"E:\data\race_jsons")
    output_dir = Path(r"C:\Users\emir\Desktop\HorseRacingAPI-master\analysis_results")
    output_dir.mkdir(exist_ok=True)
    
    print("TOPLU YARIŞ ANALİZİ")
    print("="*80)
    print()
    
    # Örnek: Tüm yarışlardan rastgele 20 tanesini al
    print("🔍 Yarışlar filtreleniyor...")
    print("   Limit: 20 yarış\n")
    
    race_files = filter_races_by_criteria(
        race_jsons_dir,
        limit=20
    )
    
    print(f"✓ {len(race_files)} yarış bulundu\n")
    
    if not race_files:
        print("❌ Kriterlere uygun yarış bulunamadı!")
        return
    
    # Analiz yap
    print("📊 Yarışlar analiz ediliyor...\n")
    df = analyze_multiple_races(race_files, output_dir=output_dir)
    
    print(f"\n{'='*80}")
    print(f"ANALİZ TAMAMLANDI")
    print(f"{'='*80}\n")
    print(f"Toplam Yarış: {df['race_id'].nunique()}")
    print(f"Toplam At: {len(df)}")
    print(f"Ortalama At/Yarış: {len(df) / df['race_id'].nunique():.1f}\n")
    
    # İstatistikler
    get_top_performers(df, top_n=20)
    compare_jockeys(df, min_races=5)
    
    # En iyi tahmin edilen atlar (her yarışta)
    print(f"\n{'='*80}")
    print("HER YARIŞTA TAHMİN EDİLEN FAVORİLER")
    print(f"{'='*80}\n")
    
    favorites = df[df['predicted_rank'] == 1][
        ['race_id', 'race_date', 'race_city', 'race_distance', 
         'horse_name', 'prediction_score', 'ganyan', 'agf', 'jockey_name']
    ].sort_values('race_date')
    
    print(favorites.to_string(index=False))
    
    print(f"\n\n✓ Tüm sonuçlar '{output_dir}' klasörüne kaydedildi\n")
    
    return df


if __name__ == "__main__":
    df = main()
