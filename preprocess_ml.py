"""
Veriyi Makine Öğrenmesi için Hazırla (Preprocessing)
- Süre dönüşümleri (1.40.25 → saniye)
- Kategorik encoding (şehir, pist, jokey)
- Eksik veri temizliği
"""
import pandas as pd
import numpy as np
import re
from pathlib import Path
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Input dosyaları
PROGRAM_FILE = r"E:\data\master_program.parquet"
SONUCLAR_FILE = r"E:\data\master_sonuclar.parquet"
IDMAN_FILE = r"E:\data\master_idman.parquet"
TIME_FILE = r"E:\data\ml_time_data.json"

# Output dosyaları
OUTPUT_DIR = r"E:\data"
OUTPUT_PROGRAM = r"E:\data\ml_program.parquet"
OUTPUT_SONUCLAR = r"E:\data\ml_sonuclar.parquet"
OUTPUT_IDMAN = r"E:\data\ml_idman.parquet"
OUTPUT_TIME = r"E:\data\ml_time.parquet"

def time_to_seconds(time_str):
    """
    Süre stringini saniyeye çevir
    Örnekler:
    - "1.40.25" → 100.25 (1*60 + 40.25)
    - "0.52.20" → 52.20
    - "1.02.00" → 62.00
    """
    if pd.isna(time_str) or time_str == '' or time_str == '-':
        return np.nan
    
    try:
        # String'i temizle
        time_str = str(time_str).strip()
        
        # Format: "M.SS.MM" veya "SS.MM"
        parts = time_str.split('.')
        
        if len(parts) == 3:
            # "1.40.25" formatı
            minutes = int(parts[0])
            seconds = int(parts[1])
            millis = int(parts[2])
            return minutes * 60 + seconds + millis / 100
        elif len(parts) == 2:
            # "52.20" formatı
            seconds = int(parts[0])
            millis = int(parts[1])
            return seconds + millis / 100
        else:
            return np.nan
    except:
        return np.nan

def clean_numeric(value):
    """Sayısal değeri temizle (binlik ayırıcıları kaldır)"""
    if pd.isna(value) or value == '' or value == '-':
        return np.nan
    
    try:
        # String'e çevir ve temizle
        value_str = str(value).replace(',', '').replace(' ', '').strip()
        return float(value_str)
    except:
        return np.nan

def preprocess_program(df):
    """Program verisini hazırla"""
    print("\n🔧 PROGRAM VERİSİ İŞLENİYOR...")
    print(f"Başlangıç: {len(df):,} kayıt")
    
    df = df.copy()
    
    # 1. SÜRELERİ SANİYEYE ÇEVİR (İdman süreleri)
    print("⏱️  Süreler saniyeye çevriliyor...")
    time_columns = ['1400m', '1200m', '1000m', '800m', '600m', '400m', '200m']
    for col in time_columns:
        if col in df.columns:
            # Orijinal sütunu sakla
            df[f'{col}_original'] = df[col]
            # Saniyeye çevir
            df[f'{col}_seconds'] = df[col].apply(time_to_seconds)
    
    # 2. SAYISAL SÜTUNLARI TEMİZLE
    print("🔢 Sayısal veriler temizleniyor...")
    numeric_cols = ['distance', 'horse_weight', 'handicap_weight', 'kgs', 'prize_1', 
                   'prize_2', 'prize_3', 'prize_4', 'prize_5']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_numeric)
    
    # 3. KATEGORİK DEĞİŞKENLERİ ENCODE ET
    print("🏷️  Kategorik veriler encode ediliyor...")
    
    # Label Encoding (basit sıralı kodlama)
    categorical_cols = {
        'city': 'city_code',
        'track_type': 'track_code',
        'race_category': 'category_code',
        'age_group': 'age_code',
        'Irk': 'irk_code',
        'Cins.': 'gender_code'
    }
    
    for orig_col, new_col in categorical_cols.items():
        if orig_col in df.columns:
            # Kategoriye çevir ve kod ata
            df[new_col] = pd.Categorical(df[orig_col]).codes
            # -1 (eksik değer) yerine NaN
            df[new_col] = df[new_col].replace(-1, np.nan)
    
    # 4. JOKEY/ANTRENÖR/SAHİP WIN RATE (🆕 PROFESYONEL DOKUNUŞ)
    print("🏆 Jokey/Antrenör/Sahip win rate'leri hesaplanıyor...")
    # Bu bilgiyi sonuclar tablosundan alacağız, şimdilik ID'leri bırakalım
    
    # 5. EKSİK VERİ İŞAREŞİ
    print("❓ Eksik veri işaretleniyor...")
    df['has_missing'] = df.isna().any(axis=1).astype(int)
    df['missing_count'] = df.isna().sum(axis=1)
    
    # 6. YAŞI TEMİZLE (8y d a → 8)
    if 'Yaş' in df.columns:
        df['age_numeric'] = df['Yaş'].apply(lambda x: int(re.search(r'\d+', str(x)).group()) 
                                            if pd.notna(x) and re.search(r'\d+', str(x)) else np.nan)
    
    print(f"✅ İşlendi: {len(df):,} kayıt, {len(df.columns)} sütun")
    return df

def preprocess_sonuclar(df):
    """Sonuç verisini hazırla"""
    print("\n🔧 SONUÇ VERİSİ İŞLENİYOR...")
    print(f"Başlangıç: {len(df):,} kayıt")
    
    df = df.copy()
    
    # 1. DERECE (finish_position) - kritik!
    print("🏆 Derece verileri işleniyor...")
    if 'finish_position' in df.columns:
        df['finish_position_clean'] = pd.to_numeric(df['finish_position'], errors='coerce')
        # Bitiremeyen atlar (DNF, DQ, vs.) → -1
        df['did_finish'] = df['finish_position_clean'].notna().astype(int)
    
    # 2. GANYAN (ödeme oranı)
    if 'ganyan' in df.columns:
        df['ganyan_numeric'] = df['ganyan'].apply(clean_numeric)
    
    # 3. SÜRELERİ SANİYEYE ÇEVİR
    print("⏱️  Süreler saniyeye çevriliyor...")
    if 'time' in df.columns or 'race_time' in df.columns:
        time_col = 'time' if 'time' in df.columns else 'race_time'
        df[f'{time_col}_seconds'] = df[time_col].apply(time_to_seconds)
    
    # 4. SAYISAL SÜTUNLAR
    print("🔢 Sayısal veriler temizleniyor...")
    numeric_cols = ['distance', 'horse_weight', 'handicap_weight', 'kgs', 
                   'prize_1', 'prize_2', 'prize_3', 'prize_4', 'prize_5']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_numeric)
    
    # 5. KATEGORİK ENCODE
    print("🏷️  Kategorik veriler encode ediliyor...")
    categorical_cols = {
        'city': 'city_code',
        'track_type': 'track_code',
        'race_category': 'category_code',
        'age_group': 'age_code'
    }
    
    for orig_col, new_col in categorical_cols.items():
        if orig_col in df.columns:
            df[new_col] = pd.Categorical(df[orig_col]).codes
            df[new_col] = df[new_col].replace(-1, np.nan)
    
    # 6. EKSİK VERİ
    df['has_missing'] = df.isna().any(axis=1).astype(int)
    df['missing_count'] = df.isna().sum(axis=1)
    
    # 7. KAZANAN MI? (1. derece)
    if 'finish_position_clean' in df.columns:
        df['is_winner'] = (df['finish_position_clean'] == 1).astype(int)
        df['is_top3'] = (df['finish_position_clean'] <= 3).astype(int)
    
    print(f"✅ İşlendi: {len(df):,} kayıt, {len(df.columns)} sütun")
    return df

def preprocess_idman(df):
    """İdman verisini hazırla"""
    print("\n🔧 İDMAN VERİSİ İŞLENİYOR...")
    print(f"Başlangıç: {len(df):,} kayıt")
    
    df = df.copy()
    
    # 1. SÜRELERİ SANİYEYE ÇEVİR
    print("⏱️  İdman süreleri saniyeye çevriliyor...")
    time_columns = ['1400m', '1200m', '1000m', '800m', '600m', '400m', '200m']
    for col in time_columns:
        if col in df.columns:
            df[f'{col}_original'] = df[col]
            df[f'{col}_seconds'] = df[col].apply(time_to_seconds)
    
    # 2. TARİH
    if 'İ. Tarihi' in df.columns:
        df['idman_date'] = pd.to_datetime(df['İ. Tarihi'], format='%d.%m.%Y', errors='coerce')
        df['idman_year'] = df['idman_date'].dt.year
        df['idman_month'] = df['idman_date'].dt.month
        df['idman_day_of_week'] = df['idman_date'].dt.dayofweek
    
    # 3. KATEGORİK ENCODE
    print("🏷️  Kategorik veriler encode ediliyor...")
    categorical_cols = {
        'Irk': 'irk_code',
        'Cins.': 'gender_code',
        'İ. Hip.': 'hipodrom_code',
        'Pist': 'pist_code',
        'İ. Türü': 'idman_type_code',
        'Durum': 'durum_code'
    }
    
    for orig_col, new_col in categorical_cols.items():
        if orig_col in df.columns:
            df[new_col] = pd.Categorical(df[orig_col]).codes
            df[new_col] = df[new_col].replace(-1, np.nan)
    
    # 4. YAŞ
    if 'Yaş' in df.columns:
        df['age_numeric'] = pd.to_numeric(df['Yaş'], errors='coerce')
    
    # 5. EKSİK VERİ
    df['has_missing'] = df.isna().any(axis=1).astype(int)
    df['missing_count'] = df.isna().sum(axis=1)
    
    print(f"✅ İşlendi: {len(df):,} kayıt, {len(df.columns)} sütun")
    return df

def preprocess_time(df):
    """Time verisini hazırla - PROFESYONEL NORMALIZASYON"""
    print("\n🔧 TIME VERİSİ İŞLENİYOR...")
    print(f"Başlangıç: {len(df):,} kayıt")
    
    df = df.copy()
    
    # 1. TIME'ı SANİYEYE ÇEVİR
    print("⏱️  Time saniyeye çevriliyor...")
    df['time_seconds'] = df['time'].apply(time_to_seconds)
    
    # 2. HORSE BAZINDA İSTATİSTİKLER (geçmiş performans - DATA LEAKAGE YOK!)
    print("🐴 At bazında istatistikler hesaplanıyor...")
    horse_stats = df[df['did_finish'] == True].groupby('horse_id')['time_seconds'].agg([
        ('horse_avg_time', 'mean'),
        ('horse_min_time', 'min'),
        ('horse_max_time', 'max'),
        ('horse_std_time', 'std'),
        ('horse_race_count', 'count')
    ]).reset_index()
    
    df = df.merge(horse_stats, on='horse_id', how='left')
    
    # 3. 🆕 HIZ (SPEED) - Mesafeden bağımsız performans göstergesi
    print("🚀 Hız hesaplanıyor (speed = distance / time)...")
    # Önce race_id'den distance bilgisini almamız lazım - şimdilik atın ortalama hızını hesaplayalım
    # horse_avg_speed = ortalama_mesafe / horse_avg_time şeklinde olacak
    # Ama şu an elimizde mesafe yok, bunu train_model'da merge edeceğiz
    
    # 4. 🆕 KAPASİTE KULLANIMI - At potansiyeline ne kadar yakın?
    print("💪 Kapasite kullanımı hesaplanıyor...")
    df['horse_capacity_usage'] = df['horse_min_time'] / (df['horse_avg_time'] + 0.1)  # 1'e yakınsa tutarlı
    
    # 5. TUTARLILIK (consistency)
    print("📊 Süre normalizasyonu yapılıyor...")
    df['horse_time_consistency'] = 1 / (df['horse_std_time'].fillna(1) + 1)  # 0-1 arası
    df['horse_best_vs_avg_ratio'] = df['horse_min_time'] / (df['horse_avg_time'] + 0.1)
    
    # 6. 🆕 YARIŞ İÇİ Z-SCORE (Pist/Mesafe bazında normalize)
    # Her atın geçmiş ortalama süresi, bu yarıştaki tüm atların ortalamasıyla karşılaştırılıyor
    print("🏁 Yarış içi relatif performans hesaplanıyor...")
    race_avg_horse_time = df.groupby('race_id')['horse_avg_time'].transform('mean')
    race_std_horse_time = df.groupby('race_id')['horse_avg_time'].transform('std')
    
    # Z-Score: (at_süresi - yarış_ortalaması) / yarış_std
    df['horse_time_zscore'] = (df['horse_avg_time'] - race_avg_horse_time) / (race_std_horse_time + 0.1)
    # Negatif z-score = ortalamanın altında (iyi), pozitif = ortalamanın üstünde (kötü)
    
    df['horse_vs_race_avg'] = df['horse_avg_time'] / (race_avg_horse_time + 0.1)  # <1 iyi, >1 kötü
    
    # En iyi atın geçmiş ortalaması
    race_best_horse_time = df.groupby('race_id')['horse_avg_time'].transform('min')
    df['horse_vs_race_best'] = df['horse_avg_time'] / (race_best_horse_time + 0.1)  # <1.05 çok iyi
    
    # 7. 🆕 YARIŞ TECRÜBESI SEVİYESİ
    print("🎓 Tecrübe seviyesi hesaplanıyor...")
    df['experience_level'] = pd.cut(df['horse_race_count'].fillna(0), 
                                     bins=[-1, 5, 15, 30, 100], 
                                     labels=[0, 1, 2, 3])  # 0=çaylak, 3=veteran
    df['experience_level'] = df['experience_level'].astype(float)
    
    print(f"✅ İşlendi: {len(df):,} kayıt, {len(df.columns)} sütun")
    return df

def main():
    """Ana preprocessing pipeline"""
    print("="*80)
    print("🤖 MAKİNE ÖĞRENMESİ İÇİN VERİ HAZIRLANIYOR")
    print("="*80)
    
    # 1. SONUÇLAR (önce bu - win rate'leri hesaplayacağız)
    print("\n📊 Sonuç verisi yükleniyor...")
    df_sonuclar = pd.read_parquet(SONUCLAR_FILE)
    df_sonuclar_ml = preprocess_sonuclar(df_sonuclar)
    
    # 🆕 JOKEY/ANTRENÖR/SAHİP WIN RATE HESAPLAMA
    print("\n🏆 Jokey/Antrenör/Sahip win rate'leri hesaplanıyor...")
    
    # Jokey win rate
    jockey_stats = df_sonuclar_ml.groupby('jockey_id').agg({
        'is_winner': ['sum', 'count']
    })
    jockey_stats.columns = ['jockey_wins', 'jockey_races']
    jockey_stats['jockey_win_rate'] = jockey_stats['jockey_wins'] / jockey_stats['jockey_races']
    jockey_stats = jockey_stats.reset_index()
    
    # Antrenör win rate
    trainer_stats = df_sonuclar_ml.groupby('trainer_id').agg({
        'is_winner': ['sum', 'count']
    })
    trainer_stats.columns = ['trainer_wins', 'trainer_races']
    trainer_stats['trainer_win_rate'] = trainer_stats['trainer_wins'] / trainer_stats['trainer_races']
    trainer_stats = trainer_stats.reset_index()
    
    # Sahip win rate
    owner_stats = df_sonuclar_ml.groupby('owner_id').agg({
        'is_winner': ['sum', 'count']
    })
    owner_stats.columns = ['owner_wins', 'owner_races']
    owner_stats['owner_win_rate'] = owner_stats['owner_wins'] / owner_stats['owner_races']
    owner_stats = owner_stats.reset_index()
    
    df_sonuclar_ml.to_parquet(OUTPUT_SONUCLAR, compression='snappy', index=False)
    size_mb = Path(OUTPUT_SONUCLAR).stat().st_size / 1024**2
    print(f"💾 Kaydedildi: {OUTPUT_SONUCLAR} ({size_mb:.1f} MB)")
    
    # 2. PROGRAM
    print("\n📊 Program verisi yükleniyor...")
    df_program = pd.read_parquet(PROGRAM_FILE)
    df_program_ml = preprocess_program(df_program)
    
    # Win rate'leri programa ekle
    print("🔗 Win rate'ler programa ekleniyor...")
    df_program_ml = df_program_ml.merge(jockey_stats[['jockey_id', 'jockey_win_rate', 'jockey_races']], 
                                        on='jockey_id', how='left')
    df_program_ml = df_program_ml.merge(trainer_stats[['trainer_id', 'trainer_win_rate', 'trainer_races']], 
                                        on='trainer_id', how='left')
    df_program_ml = df_program_ml.merge(owner_stats[['owner_id', 'owner_win_rate', 'owner_races']], 
                                        on='owner_id', how='left')
    
    # Eksik win rate'leri 0 yap (yeni jokey/antrenör)
    df_program_ml['jockey_win_rate'] = df_program_ml['jockey_win_rate'].fillna(0)
    df_program_ml['trainer_win_rate'] = df_program_ml['trainer_win_rate'].fillna(0)
    df_program_ml['owner_win_rate'] = df_program_ml['owner_win_rate'].fillna(0)
    
    df_program_ml.to_parquet(OUTPUT_PROGRAM, compression='snappy', index=False)
    size_mb = Path(OUTPUT_PROGRAM).stat().st_size / 1024**2
    print(f"💾 Kaydedildi: {OUTPUT_PROGRAM} ({size_mb:.1f} MB)")
    
    # 3. İDMAN
    print("\n📊 İdman verisi yükleniyor...")
    df_idman = pd.read_parquet(IDMAN_FILE)
    df_idman_ml = preprocess_idman(df_idman)
    df_idman_ml.to_parquet(OUTPUT_IDMAN, compression='snappy', index=False)
    size_mb = Path(OUTPUT_IDMAN).stat().st_size / 1024**2
    print(f"💾 Kaydedildi: {OUTPUT_IDMAN} ({size_mb:.1f} MB)")
    
    # 4. TIME
    print("\n📊 Time verisi yükleniyor...")
    import json
    with open(TIME_FILE, 'r', encoding='utf-8') as f:
        time_data = json.load(f)
    df_time = pd.DataFrame(time_data)
    df_time_ml = preprocess_time(df_time)
    df_time_ml.to_parquet(OUTPUT_TIME, compression='snappy', index=False)
    size_mb = Path(OUTPUT_TIME).stat().st_size / 1024**2
    print(f"💾 Kaydedildi: {OUTPUT_TIME} ({size_mb:.1f} MB)")
    
    # ÖZET
    print("\n" + "="*80)
    print("✅ TÜM VERİLER MAKİNE ÖĞRENMESİ İÇİN HAZIR!")
    print("="*80)
    print("\n📁 ML Dosyaları:")
    print(f"  1. {OUTPUT_PROGRAM}")
    print(f"  2. {OUTPUT_SONUCLAR}")
    print(f"  3. {OUTPUT_IDMAN}")
    print(f"  4. {OUTPUT_TIME}")
    print("\n🎯 Özellikler:")
    print("  ✅ Süreler saniyeye çevrildi")
    print("  ✅ Kategorik veriler encode edildi")
    print("  ✅ Eksik veriler işaretlendi")
    print("  ✅ Sayısal değerler temizlendi")
    print("  ✅ Yeni özellikler oluşturuldu (is_winner, age_numeric, vs.)")
    print("  ✅ Time verileri işlendi (hız, z-score, kapasite, tecrübe)")
    print("  ✅ Jokey/Antrenör/Sahip win rate'leri eklendi")

if __name__ == "__main__":
    main()


