"""
E:\data\program klasöründeki tüm yarış programı JSON'larını tek Parquet/CSV'de birleştir
MASTER PROGRAM TABLE
"""
import pandas as pd
import json
import os
from pathlib import Path
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

PROGRAM_DIR = r"E:\data\program"
OUTPUT_PARQUET = r"E:\data\master_program.parquet"
OUTPUT_CSV = r"E:\data\master_program.csv"

def collect_all_programs():
    """Tüm program JSON dosyalarını topla ve birleştir"""
    all_records = []
    total_files = 0
    total_records = 0
    
    print("🔍 Program dosyaları toplanıyor...")
    
    # Tüm JSON dosyalarını bul
    program_path = Path(PROGRAM_DIR)
    json_files = list(program_path.rglob("*.json"))
    
    print(f"Toplam dosya: {len(json_files):,}")
    print("📦 Veri birleştiriliyor...\n")
    
    for i, json_file in enumerate(json_files, 1):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Yapı: {"02": {"0": [...], "1": [...]}, "15": {...}}
                for day_key, day_data in data.items():
                    if isinstance(day_data, dict):
                        # İç içe dict yapısı
                        for race_num, horses in day_data.items():
                            if isinstance(horses, list):
                                # Sadece dict olan kayıtları al
                                for horse in horses:
                                    if isinstance(horse, dict):
                                        all_records.append(horse)
                                        total_records += 1
                    elif isinstance(day_data, list):
                        # Direkt list yapısı (eski format)
                        for horse in day_data:
                            if isinstance(horse, dict):
                                all_records.append(horse)
                                total_records += 1
                
                total_files += 1
            
            # Progress
            if i % 100 == 0:
                print(f"İşlenen: {i:,}/{len(json_files):,} dosya | "
                      f"Toplam kayıt: {total_records:,}", flush=True)
                      
        except Exception as e:
            print(f"⚠️ Hata ({json_file.name}): {e}")
            continue
    
    print(f"\n✅ Toplam {total_files:,} dosyadan {total_records:,} kayıt toplandı")
    
    # DataFrame'e çevir
    print("\n📊 DataFrame oluşturuluyor...")
    df = pd.DataFrame(all_records)
    
    print(f"DataFrame boyutu: {df.shape[0]:,} satır × {df.shape[1]} sütun")
    print(f"Bellek kullanımı: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
    
    # Veri tipleri optimize et
    print("\n🔧 Veri tipleri optimize ediliyor...")
    
    # ID sütunları int'e çevir
    id_columns = ['race_id', 'horse_id', 'jockey_id', 'owner_id', 'trainer_id', 
                  'horse_father_id', 'horse_mother_id']
    for col in id_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
    
    # Mesafe int'e
    if 'distance' in df.columns:
        df['distance'] = pd.to_numeric(df['distance'], errors='coerce').astype('Int16')
    
    # Yarış numarası
    if 'race_number' in df.columns:
        df['race_number'] = pd.to_numeric(df['race_number'], errors='coerce').astype('Int8')
    
    # Tarih formatı
    if 'race_date' in df.columns:
        df['race_date'] = pd.to_datetime(df['race_date'], errors='coerce')
    
    # Kategorik sütunlar
    categorical_cols = ['city', 'race_category', 'age_group', 'track_type', 
                       'horse_equipment', 'start_no', 'Durum']
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].astype('category')
    
    print(f"Optimize edilmiş bellek: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
    
    # Parquet olarak kaydet
    print(f"\n💾 Parquet kaydediliyor: {OUTPUT_PARQUET}")
    df.to_parquet(OUTPUT_PARQUET, compression='snappy', index=False)
    parquet_size = os.path.getsize(OUTPUT_PARQUET) / 1024**2
    print(f"   Dosya boyutu: {parquet_size:.1f} MB")
    
    # CSV olarak kaydet
    print(f"\n💾 CSV kaydediliyor: {OUTPUT_CSV}")
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    csv_size = os.path.getsize(OUTPUT_CSV) / 1024**2
    print(f"   Dosya boyutu: {csv_size:.1f} MB")
    
    # Özet istatistikler
    print(f"\n{'='*80}")
    print(f"✅ MASTER PROGRAM TABLE OLUŞTURULDU!")
    print(f"Toplam kayıt: {len(df):,}")
    print(f"Unique yarışlar: {df['race_id'].nunique():,}")
    print(f"Unique atlar: {df['horse_id'].nunique():,}")
    print(f"Şehirler: {df['city'].nunique()} ({', '.join(df['city'].unique()[:5])}...)")
    print(f"Tarih aralığı: {df['race_date'].min()} → {df['race_date'].max()}")
    print(f"\nDosyalar:")
    print(f"  📄 Parquet: {OUTPUT_PARQUET} ({parquet_size:.1f} MB) ⚡ HIZLI")
    print(f"  📄 CSV: {OUTPUT_CSV} ({csv_size:.1f} MB) 📊 Excel uyumlu")
    print(f"{'='*80}")
    
    # İlk birkaç satırı göster
    print("\n🔍 İlk 5 kayıt:")
    print(df.head())
    
    return df

if __name__ == "__main__":
    df = collect_all_programs()
