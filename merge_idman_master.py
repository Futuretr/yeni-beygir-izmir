"""
Tüm idman JSON dosyalarını tek bir Parquet/CSV dosyasında birleştir
MASTER TABLE oluştur - AI için optimize edilmiş
"""
import pandas as pd
import json
import os
from pathlib import Path
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

IDMAN_DIR = r"E:\data\idman"
OUTPUT_PARQUET = r"E:\data\master_idman.parquet"
OUTPUT_CSV = r"E:\data\master_idman.csv"

def collect_all_idman():
    """Tüm idman JSON dosyalarını topla ve birleştir"""
    all_records = []
    total_files = 0
    total_records = 0
    
    print("🔍 İdman dosyaları toplanıyor...")
    
    # Tüm JSON dosyalarını bul
    idman_path = Path(IDMAN_DIR)
    json_files = list(idman_path.rglob("*.json"))
    
    print(f"Toplam dosya: {len(json_files):,}")
    print("📦 Veri birleştiriliyor...\n")
    
    for i, json_file in enumerate(json_files, 1):
        try:
            # failed_horses.json'u atla
            if json_file.name == 'failed_horses.json':
                continue
                
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # idman_records listesini al
                if 'idman_records' in data and data['idman_records']:
                    records = data['idman_records']
                    all_records.extend(records)
                    total_records += len(records)
                    total_files += 1
            
            # Progress
            if i % 500 == 0:
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
    
    # horse_id int'e çevir
    if 'horse_id' in df.columns:
        df['horse_id'] = pd.to_numeric(df['horse_id'], errors='coerce').astype('Int64')
    
    # Yaş int'e çevir
    if 'Yaş' in df.columns:
        df['Yaş'] = pd.to_numeric(df['Yaş'].str.extract(r'(\d+)', expand=False), errors='coerce').astype('Int16')
    
    # Tarih formatı
    if 'İ. Tarihi' in df.columns:
        df['İ. Tarihi'] = pd.to_datetime(df['İ. Tarihi'], format='%d.%m.%Y', errors='coerce')
    
    # Kategorik sütunlar (bellek tasarrufu)
    categorical_cols = ['Irk', 'Cins.', 'Durum', 'İ. Hip.', 'Pist', 'İ. Türü']
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].astype('category')
    
    print(f"Optimize edilmiş bellek: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
    
    # Parquet olarak kaydet (hızlı, küçük)
    print(f"\n💾 Parquet kaydediliyor: {OUTPUT_PARQUET}")
    df.to_parquet(OUTPUT_PARQUET, compression='snappy', index=False)
    parquet_size = os.path.getsize(OUTPUT_PARQUET) / 1024**2
    print(f"   Dosya boyutu: {parquet_size:.1f} MB")
    
    # CSV olarak kaydet (opsiyonel - Excel için)
    print(f"\n💾 CSV kaydediliyor: {OUTPUT_CSV}")
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    csv_size = os.path.getsize(OUTPUT_CSV) / 1024**2
    print(f"   Dosya boyutu: {csv_size:.1f} MB")
    
    # Özet istatistikler
    print(f"\n{'='*80}")
    print(f"✅ MASTER TABLE OLUŞTURULDU!")
    print(f"Toplam kayıt: {len(df):,}")
    print(f"Unique atlar: {df['horse_id'].nunique():,}")
    print(f"Tarih aralığı: {df['İ. Tarihi'].min()} → {df['İ. Tarihi'].max()}")
    print(f"\nDosyalar:")
    print(f"  📄 Parquet: {OUTPUT_PARQUET} ({parquet_size:.1f} MB) ⚡ HIZLI")
    print(f"  📄 CSV: {OUTPUT_CSV} ({csv_size:.1f} MB) 📊 Excel uyumlu")
    print(f"{'='*80}")
    
    # İlk birkaç satırı göster
    print("\n🔍 İlk 5 kayıt:")
    print(df.head())
    
    return df

if __name__ == "__main__":
    df = collect_all_idman()
