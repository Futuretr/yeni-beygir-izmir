"""
İdman verilerinin kapsama kontrolü
Program/Sonuçlardaki atlarla idman verilerini karşılaştır
"""
import pandas as pd
import json

print("=" * 80)
print("🔍 İDMAN VERİSİ KAPSAMA KONTROLÜ")
print("=" * 80)

# Veriyi yükle
print("\n📁 Veriler yükleniyor...")
program = pd.read_parquet(r"E:\data\master_program.parquet")
sonuclar = pd.read_parquet(r"E:\data\master_sonuclar.parquet")
idman = pd.read_parquet(r"E:\data\master_idman.parquet")

print(f"Program kayıtları: {len(program):,}")
print(f"Sonuç kayıtları: {len(sonuclar):,}")
print(f"İdman kayıtları: {len(idman):,}")

# Unique atlar
program_horses = set(program['horse_id'].unique())
sonuclar_horses = set(sonuclar['horse_id'].unique())
idman_horses = set(idman['horse_id'].unique())

print("\n" + "=" * 80)
print("🐴 UNIQUE ATLAR")
print("=" * 80)
print(f"Program'da unique atlar: {len(program_horses):,}")
print(f"Sonuçlarda unique atlar: {len(sonuclar_horses):,}")
print(f"İdman'da unique atlar: {len(idman_horses):,}")

# Birleşim - tüm atlar
all_horses = program_horses | sonuclar_horses
print(f"\nToplam unique at (program + sonuç): {len(all_horses):,}")

# İdmanı olmayan atlar
idmani_olmayan = all_horses - idman_horses
print(f"İdmanı OLMAYAN atlar: {len(idmani_olmayan):,} ({len(idmani_olmayan)/len(all_horses)*100:.1f}%)")

# all_horse_ids.json'u kontrol et
print("\n" + "=" * 80)
print("📊 SCRAPED HORSE IDS KONTROLÜ")
print("=" * 80)

try:
    with open(r"E:\data\all_horse_ids.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
        scraped_horses = set(data['horse_ids'])
    
    print(f"Scrape için toplanan horse_id: {len(scraped_horses):,}")
    print(f"Bu atlardan {len(scraped_horses & idman_horses):,} tanesinin idmanı var")
    print(f"Bu atlardan {len(scraped_horses - idman_horses):,} tanesinin idmanı yok/boş")
    
    # Program/sonuçta olan ama scrape listesinde olmayan
    eksik_scrape = all_horses - scraped_horses
    if len(eksik_scrape) > 0:
        print(f"\n⚠️  Program/sonuçta var ama scrape listesinde YOK: {len(eksik_scrape):,} at")
        print(f"   İlk 10: {list(eksik_scrape)[:10]}")
    
    # Scrape listesinde olan ama program/sonuçta olmayan
    fazla_scrape = scraped_horses - all_horses
    if len(fazla_scrape) > 0:
        print(f"\n⚠️  Scrape listesinde var ama program/sonuçta YOK: {len(fazla_scrape):,} at")
        print(f"   İlk 10: {list(fazla_scrape)[:10]}")
        
except FileNotFoundError:
    print("all_horse_ids.json bulunamadı")

# İdman kayıt sayısı dağılımı
print("\n" + "=" * 80)
print("📈 İDMAN KAYIT DAĞILIMI")
print("=" * 80)

idman_counts = idman.groupby('horse_id').size().sort_values(ascending=False)
print(f"Ortalama idman/at: {idman_counts.mean():.1f}")
print(f"Medyan idman/at: {idman_counts.median():.1f}")
print(f"Maksimum idman/at: {idman_counts.max()}")
print(f"Minimum idman/at: {idman_counts.min()}")

print(f"\nEn çok idmanı olan 5 at:")
for horse_id, count in idman_counts.head(5).items():
    print(f"  Horse {horse_id}: {count} idman")

# Yarıştaki performansa göre idman kontrolü
print("\n" + "=" * 80)
print("🏆 YARIŞ PERFORMANSI - İDMAN KARŞILAŞTIRMASI")
print("=" * 80)

# Sonuçlarda derece alan atlar
derece_alan = sonuclar[sonuclar['finish_position'].isin(['1', '2', '3'])]['horse_id'].unique()
print(f"Derece alan atlar: {len(derece_alan):,}")
derece_alan_idmanli = set(derece_alan) & idman_horses
print(f"Derece alan + idmanı var: {len(derece_alan_idmanli):,} ({len(derece_alan_idmanli)/len(derece_alan)*100:.1f}%)")
print(f"Derece alan + idmanı YOK: {len(derece_alan) - len(derece_alan_idmanli):,}")

print("\n" + "=" * 80)
print("✅ KONTROL TAMAMLANDI")
print("=" * 80)
