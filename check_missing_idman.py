"""
İdmanı olmayan atları detaylı kontrol et
Gerçekten idman yok mu yoksa scraping hatası mı?
"""
import pandas as pd
import json
import os

print("=" * 80)
print("🔍 İDMANI OLMAYAN ATLARI KONTROL ET")
print("=" * 80)

# Veriyi yükle
program = pd.read_parquet(r"E:\data\master_program.parquet")
idman = pd.read_parquet(r"E:\data\master_idman.parquet")

# İdmanı olmayan atlar
program_horses = set(program['horse_id'].unique())
idman_horses = set(idman['horse_id'].unique())
idmani_olmayan = program_horses - idman_horses

print(f"Program'daki atlar: {len(program_horses):,}")
print(f"İdmanı olan atlar: {len(idman_horses):,}")
print(f"İdmanı OLMAYAN atlar: {len(idmani_olmayan):,}")

# İdmanı olmayan atların dosyalarını kontrol et
idman_dir = r"E:\data\idman"
idmani_olmayan_list = list(idmani_olmayan)[:100]  # İlk 100 at

print("\n" + "=" * 80)
print("📂 İDMAN DOSYALARI KONTROLÜ (İlk 100 at)")
print("=" * 80)

dosya_var = 0
dosya_yok = 0
dosya_bos = 0
dosya_dolu = 0

for horse_id in idmani_olmayan_list:
    # Dosya yolunu bul
    folder_num = (horse_id // 100) * 100
    folder_path = os.path.join(idman_dir, f"{folder_num:06d}")
    filename = os.path.join(folder_path, f"{horse_id}.json")
    
    if os.path.exists(filename):
        dosya_var += 1
        # Dosyayı oku
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'idman_records' in data and len(data['idman_records']) > 0:
            dosya_dolu += 1
            print(f"✅ {horse_id}: {len(data['idman_records'])} idman VAR ama master'da YOK!")
        else:
            dosya_bos += 1
    else:
        dosya_yok += 1

print(f"\n📊 Sonuç (100 attan):")
print(f"  Dosya var: {dosya_var}")
print(f"  Dosya yok: {dosya_yok}")
print(f"  Dosya boş (idman_records=[]): {dosya_bos}")
print(f"  Dosya DOLU ama master'da yok: {dosya_dolu}")

# Tüm idman dosyalarını say
print("\n" + "=" * 80)
print("📁 TÜM İDMAN DOSYALARI")
print("=" * 80)

total_files = 0
for root, dirs, files in os.walk(idman_dir):
    total_files += len([f for f in files if f.endswith('.json')])

print(f"Toplam JSON dosya: {total_files:,}")
print(f"Master idman'da unique at: {len(idman_horses):,}")
print(f"Fark: {total_files - len(idman_horses):,} dosya fazla")

# Failed horses kontrol
print("\n" + "=" * 80)
print("❌ FAILED HORSES KONTROLÜ")
print("=" * 80)

failed_file = r"E:\data\failed_horses.json"
if os.path.exists(failed_file):
    with open(failed_file, 'r', encoding='utf-8') as f:
        failed_data = json.load(f)
    
    print(f"Failed horses: {len(failed_data)}")
    if len(failed_data) > 0:
        print("\nİlk 10 failed horse:")
        for item in failed_data[:10]:
            print(f"  Horse {item['horse_id']}: {item.get('error', 'Bilinmeyen hata')}")
else:
    print("failed_horses.json bulunamadı")

print("\n" + "=" * 80)
print("✅ KONTROL TAMAMLANDI")
print("=" * 80)
