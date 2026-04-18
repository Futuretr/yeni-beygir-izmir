"""
Program ve sonuç dosyalarını karşılaştır ve eksik sonuçları belirle
"""
import pandas as pd
import json

print("=" * 80)
print("🔍 EKSİK SONUÇLARI BELİRLEME")
print("=" * 80)

# Veriyi yükle
print("\n📁 Veriler yükleniyor...")
program = pd.read_parquet(r"E:\data\master_program.parquet")
sonuclar = pd.read_parquet(r"E:\data\master_sonuclar.parquet")

print(f"Program kayıtları: {len(program):,}")
print(f"Sonuç kayıtları: {len(sonuclar):,}")

# Tarih sütununu datetime'a çevir
program['race_date'] = pd.to_datetime(program['race_date'], errors='coerce')
sonuclar['race_date'] = pd.to_datetime(sonuclar['race_date'], errors='coerce')

# Geçmiş tarihli program kayıtlarını filtrele (bugünden önceki)
bugun = pd.Timestamp('2026-01-31', tz='UTC')
program_gecmis = program[program['race_date'] < bugun].copy()

print(f"\nGeçmiş tarihli program kayıtları: {len(program_gecmis):,}")

# Hangi yarışların sonucu yok?
program_race_ids = set(program_gecmis['race_id'].unique())
sonuclar_race_ids = set(sonuclar['race_id'].unique())
eksik_race_ids = program_race_ids - sonuclar_race_ids

print(f"\nSonucu olmayan yarış sayısı: {len(eksik_race_ids):,}")

# Eksik yarışları detaylı analiz et
eksik_yarislar = program_gecmis[program_gecmis['race_id'].isin(eksik_race_ids)].copy()

# Her yarış için bir örnek al (aynı race_id'den sadece bir satır)
eksik_yarislar_unique = eksik_yarislar.groupby('race_id').first().reset_index()

print(f"Eksik kayıt sayısı: {len(eksik_yarislar):,}")
print(f"Eksik unique yarış sayısı: {len(eksik_yarislar_unique):,}")

# Tarih formatını düzenle (timezone kaldır)
eksik_yarislar_unique['race_date'] = eksik_yarislar_unique['race_date'].dt.tz_localize(None)

# Şehir ve tarih bazında grupla
print("\n" + "=" * 80)
print("📊 ŞEHİR VE TARİH BAZINDA ÖZET")
print("=" * 80)

# Şehir bazında
city_summary = eksik_yarislar_unique.groupby('city').agg({
    'race_id': 'count',
    'race_date': ['min', 'max']
}).reset_index()
city_summary.columns = ['city', 'race_count', 'first_date', 'last_date']
city_summary = city_summary.sort_values('race_count', ascending=False)

print(f"\n{'Şehir':<15} {'Yarış':<10} {'İlk Tarih':<15} {'Son Tarih':<15}")
print("-" * 80)
for _, row in city_summary.iterrows():
    print(f"{row['city']:<15} {row['race_count']:<10} {str(row['first_date'])[:10]:<15} {str(row['last_date'])[:10]:<15}")

# Tarih bazında detay - her şehir için hangi tarihlerde eksik var
print("\n" + "=" * 80)
print("📅 ŞEHİR BAZINDA EKSİK TARİHLER")
print("=" * 80)

eksik_detay = {}
for city in sorted(eksik_yarislar_unique['city'].unique()):
    city_data = eksik_yarislar_unique[eksik_yarislar_unique['city'] == city]
    
    # Tarihlere göre grupla
    date_groups = city_data.groupby(city_data['race_date'].dt.date).size().reset_index()
    date_groups.columns = ['date', 'race_count']
    date_groups = date_groups.sort_values('date')
    
    eksik_detay[city] = []
    for _, row in date_groups.iterrows():
        eksik_detay[city].append({
            'date': str(row['date']),
            'race_count': int(row['race_count'])
        })
    
    print(f"\n{city}: {len(date_groups)} gün eksik, toplam {city_data.shape[0]} yarış")
    print(f"  Tarih aralığı: {date_groups['date'].min()} - {date_groups['date'].max()}")
    print(f"  İlk 5 tarih: {', '.join([str(d) for d in date_groups['date'].head(5)])}")

# JSON olarak kaydet
output_file = r"E:\data\eksik_sonuclar.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(eksik_detay, f, indent=2, ensure_ascii=False)

print("\n" + "=" * 80)
print(f"✅ Eksik sonuçlar kaydedildi: {output_file}")
print("=" * 80)

# Özet istatistik
total_dates = sum(len(dates) for dates in eksik_detay.values())
total_races = sum(item['race_count'] for dates in eksik_detay.values() for item in dates)

print(f"\n📊 ÖZET:")
print(f"  - Toplam {len(eksik_detay)} şehir")
print(f"  - Toplam {total_dates} gün eksik")
print(f"  - Toplam {total_races} yarış eksik")
print(f"\nBu tarihleri nokta atışı çekmek için kullanabilirsin!")
