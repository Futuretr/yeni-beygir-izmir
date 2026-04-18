"""
Time ve Fark verilerini master_sonuclar ile birleştir
"""
import pandas as pd
import json

print("=" * 80)
print("🔗 TIME VE FARK VERİLERİNİ MASTER İLE BİRLEŞTİRME")
print("=" * 80)

# 1. Time/Fark verilerini yükle
print("\n📁 Time/Fark verileri yükleniyor...")
with open(r'E:\data\time_fark_data.json', 'r', encoding='utf-8') as f:
    time_fark_list = json.load(f)

print(f"   {len(time_fark_list):,} kayıt")

# DataFrame'e çevir
df_time_fark = pd.DataFrame(time_fark_list)
print(f"   Sütunlar: {df_time_fark.columns.tolist()}")

# 2. Master sonuçları yükle
print("\n📁 Master sonuçlar yükleniyor...")
df_master = pd.read_parquet(r'E:\data\master_sonuclar.parquet')
print(f"   {len(df_master):,} kayıt")
print(f"   Mevcut sütunlar: {df_master.columns.tolist()[:10]}...")

# 3. Merge et (race_id + horse_id üzerinden)
print("\n🔗 Birleştirme yapılıyor...")
print(f"   Master'da 'time' var mı: {'time' in df_master.columns}")
print(f"   Master'da 'fark' var mı: {'fark' in df_master.columns}")

# Eğer time/fark varsa sil, yoksa uyarı verme
if 'time' in df_master.columns:
    df_master = df_master.drop(columns=['time'])
    print("   ⚠️  Eski 'time' sütunu silindi")

if 'fark' in df_master.columns:
    df_master = df_master.drop(columns=['fark'])
    print("   ⚠️  Eski 'fark' sütunu silindi")

# Left merge - master'daki tüm kayıtları koru, time/fark ekle
df_merged = df_master.merge(
    df_time_fark[['race_id', 'horse_id', 'time', 'fark']],
    on=['race_id', 'horse_id'],
    how='left'
)

print(f"\n✅ Birleştirildi: {len(df_merged):,} kayıt")

# 4. İstatistikler
print("\n📊 İSTATİSTİKLER:")
print(f"   time dolu:  {df_merged['time'].notna().sum():,} ({df_merged['time'].notna().sum()/len(df_merged)*100:.1f}%)")
print(f"   time boş:   {df_merged['time'].isna().sum():,} ({df_merged['time'].isna().sum()/len(df_merged)*100:.1f}%)")
print(f"   fark dolu:  {df_merged['fark'].notna().sum():,} ({df_merged['fark'].notna().sum()/len(df_merged)*100:.1f}%)")
print(f"   fark boş:   {df_merged['fark'].isna().sum():,} ({df_merged['fark'].isna().sum()/len(df_merged)*100:.1f}%)")

# Boş olanları göster
if df_merged['time'].isna().sum() > 0:
    print(f"\n⚠️  Time boş olanlardan örnek:")
    print(df_merged[df_merged['time'].isna()][['race_id', 'horse_id', 'race_date', 'city']].head())

# 5. Kaydet
print("\n💾 Yeni master_sonuclar.parquet kaydediliyor...")
df_merged.to_parquet(r'E:\data\master_sonuclar.parquet', index=False)

print("\n✅ TAMAMLANDI!")
print(f"   Dosya: E:\\data\\master_sonuclar.parquet")
print(f"   Toplam kayıt: {len(df_merged):,}")
print(f"   Toplam sütun: {len(df_merged.columns)}")
print(f"   Yeni sütunlar: time, fark")
