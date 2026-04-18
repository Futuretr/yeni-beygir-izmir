"""
TIME DATA ML HAZIRLIK
E:\data\time klasöründeki tüm JSON dosyalarını birleştirip ML için hazırla
"""
import json
import os
from pathlib import Path

# E:\data\time klasörü
TIME_DIR = Path(r"E:\data\time")

# Çıktı dosyası
OUTPUT_FILE = r"E:\data\ml_time_data.json"

def process_time_files():
    """Tüm time JSON dosyalarını işle ve birleştir"""
    
    all_data = []
    stats = {
        'total_records': 0,
        'finished': 0,
        'did_not_finish': 0,
        'cities': {}
    }
    
    # E:\data\time klasöründeki tüm JSON dosyalarını bul
    json_files = list(TIME_DIR.glob('time_fark_*.json'))
    
    if not json_files:
        print(f"❌ {TIME_DIR} klasöründe time_fark_*.json dosyası bulunamadı!")
        return
    
    print(f"📁 {len(json_files)} dosya bulundu:")
    for f in json_files:
        print(f"   - {f.name}")
    
    print("\n" + "=" * 80)
    
    # Her dosyayı işle
    for json_file in json_files:
        city_name = json_file.stem.replace('time_fark_', '')
        print(f"\n🏇 {city_name} işleniyor...")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        city_stats = {
            'total': 0,
            'finished': 0,
            'did_not_finish': 0
        }
        
        for record in data:
            # Temiz kayıt oluştur
            clean_record = {
                'race_id': record['race_id'],
                'horse_id': record['horse_id'],
                'time': record['time'],
                'did_finish': bool(record['time'])  # time varsa True, yoksa False
            }
            
            all_data.append(clean_record)
            
            # İstatistikler
            stats['total_records'] += 1
            city_stats['total'] += 1
            
            if record['time']:
                stats['finished'] += 1
                city_stats['finished'] += 1
            else:
                stats['did_not_finish'] += 1
                city_stats['did_not_finish'] += 1
        
        stats['cities'][city_name] = city_stats
        
        print(f"   ✅ {city_stats['total']:,} kayıt")
        print(f"   🏁 Koştu: {city_stats['finished']:,}")
        print(f"   ❌ Koşmadı: {city_stats['did_not_finish']:,}")
    
    # Çıktı dosyasına yaz
    print("\n" + "=" * 80)
    print(f"\n💾 Kaydediliyor: {OUTPUT_FILE}")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    # Özet rapor
    print("\n" + "=" * 80)
    print("📊 ÖZET İSTATİSTİKLER")
    print("=" * 80)
    print(f"Toplam Kayıt: {stats['total_records']:,}")
    print(f"Koştu: {stats['finished']:,} (%{100*stats['finished']/stats['total_records']:.2f})")
    print(f"Koşmadı: {stats['did_not_finish']:,} (%{100*stats['did_not_finish']/stats['total_records']:.2f})")
    
    print("\n📍 ŞEHİR BAZINDA:")
    for city, city_data in sorted(stats['cities'].items()):
        finish_rate = 100 * city_data['finished'] / city_data['total'] if city_data['total'] > 0 else 0
        print(f"   {city:12} -> {city_data['total']:7,} kayıt | Tamamlama: %{finish_rate:.1f}")
    
    print("\n✅ TAMAMLANDI!")
    print(f"📁 Dosya: {OUTPUT_FILE}")
    
    # Örnek kayıt göster
    print("\n" + "=" * 80)
    print("📋 ÖRNEK KAYITLAR:")
    print("=" * 80)
    
    # Koşan bir örnek
    finished_example = next((r for r in all_data if r['did_finish']), None)
    if finished_example:
        print("\n✅ KOŞTU:")
        print(json.dumps(finished_example, ensure_ascii=False, indent=2))
    
    # Koşmayan bir örnek
    dnf_example = next((r for r in all_data if not r['did_finish']), None)
    if dnf_example:
        print("\n❌ KOŞMADI:")
        print(json.dumps(dnf_example, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    process_time_files()
