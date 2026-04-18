"""
Program ve Sonuç verileri arasındaki farkı analiz et
"""
import pandas as pd
from datetime import datetime

print("=" * 80)
print("📊 PROGRAM VE SONUÇ VERİSİ KARŞILAŞTIRMASI")
print("=" * 80)

# Veriyi yükle
print("\n📁 Veriler yükleniyor...")
program = pd.read_parquet(r"E:\data\master_program.parquet")
sonuclar = pd.read_parquet(r"E:\data\master_sonuclar.parquet")

print(f"Program kayıtları: {len(program):,}")
print(f"Sonuç kayıtları: {len(sonuclar):,}")
print(f"Fark: {len(program) - len(sonuclar):,} kayıt eksik")

# Tarih sütunlarını datetime'a çevir
program['race_date'] = pd.to_datetime(program['race_date'], errors='coerce')
sonuclar['race_date'] = pd.to_datetime(sonuclar['race_date'], errors='coerce')

# Bugünün tarihi
bugun = pd.Timestamp('2026-01-31', tz='UTC')

# Geçmiş ve gelecek yarışları ayır
program_gecmis = program[program['race_date'] < bugun]
program_gelecek = program[program['race_date'] >= bugun]

print("\n" + "=" * 80)
print("📅 TARİH ANALİZİ")
print("=" * 80)
print(f"Program - Geçmiş yarışlar: {len(program_gecmis):,}")
print(f"Program - Gelecek yarışlar: {len(program_gelecek):,}")
print(f"Sonuç - Toplam: {len(sonuclar):,}")
print(f"\nGeçmiş yarışlardan eksik sonuç: {len(program_gecmis) - len(sonuclar):,}")

# Şehir bazında karşılaştırma
print("\n" + "=" * 80)
print("🏙️  ŞEHİR BAZINDA KARŞILAŞTIRMA")
print("=" * 80)
print(f"{'Şehir':<15} {'Program':<12} {'Sonuç':<12} {'Fark':<12}")
print("-" * 80)

program_city = program['city'].value_counts().sort_index()
sonuclar_city = sonuclar['city'].value_counts().sort_index()

all_cities = sorted(set(list(program_city.index) + list(sonuclar_city.index)))

for city in all_cities:
    p_count = program_city.get(city, 0)
    s_count = sonuclar_city.get(city, 0)
    diff = p_count - s_count
    print(f"{city:<15} {p_count:<12,} {s_count:<12,} {diff:<12,}")

# Yıl bazında karşılaştırma
print("\n" + "=" * 80)
print("📆 YIL BAZINDA KARŞILAŞTIRMA")
print("=" * 80)
print(f"{'Yıl':<8} {'Program':<12} {'Sonuç':<12} {'Fark':<12}")
print("-" * 80)

program['yil'] = program['race_date'].dt.year
sonuclar['yil'] = sonuclar['race_date'].dt.year

program_year = program['yil'].value_counts().sort_index()
sonuclar_year = sonuclar['yil'].value_counts().sort_index()

all_years = sorted(set(list(program_year.index) + list(sonuclar_year.index)))

for year in all_years:
    if pd.notna(year):
        p_count = program_year.get(year, 0)
        s_count = sonuclar_year.get(year, 0)
        diff = p_count - s_count
        print(f"{int(year):<8} {p_count:<12,} {s_count:<12,} {diff:<12,}")

# Yarış ID bazında kontrol
print("\n" + "=" * 80)
print("🔍 YARIŞ ID KARŞILAŞTIRMASI")
print("=" * 80)

# Program ve sonuçta unique yarış sayısı
program_races = program['race_id'].nunique()
sonuclar_races = sonuclar['race_id'].nunique()

print(f"Program - Unique yarış sayısı: {program_races:,}")
print(f"Sonuç - Unique yarış sayısı: {sonuclar_races:,}")
print(f"Fark: {program_races - sonuclar_races:,} yarış")

# Hangi yarışların sonucu yok?
program_race_ids = set(program['race_id'].unique())
sonuclar_race_ids = set(sonuclar['race_id'].unique())
eksik_yarislar = program_race_ids - sonuclar_race_ids

print(f"\nSonucu olmayan yarış sayısı: {len(eksik_yarislar):,}")

if len(eksik_yarislar) > 0:
    # Eksik yarışları analiz et
    eksik_df = program[program['race_id'].isin(eksik_yarislar)]
    eksik_df_gecmis = eksik_df[eksik_df['race_date'] < bugun]
    eksik_df_gelecek = eksik_df[eksik_df['race_date'] >= bugun]
    
    print(f"\n  - Geçmiş tarihli ama sonucu yok: {len(eksik_df_gecmis['race_id'].unique()):,} yarış ({len(eksik_df_gecmis):,} at)")
    print(f"  - Gelecek tarihli (normal): {len(eksik_df_gelecek['race_id'].unique()):,} yarış ({len(eksik_df_gelecek):,} at)")
    
    # Geçmiş tarihli eksiklerin şehir dağılımı
    if len(eksik_df_gecmis) > 0:
        print("\n  Geçmiş eksiklerin şehir dağılımı:")
        for city, count in eksik_df_gecmis['city'].value_counts().items():
            print(f"    {city}: {count:,} kayıt")

print("\n" + "=" * 80)
print("✅ ANALİZ TAMAMLANDI")
print("=" * 80)
