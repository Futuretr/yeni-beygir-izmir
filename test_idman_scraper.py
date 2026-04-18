"""
Test: İdman scraper'ı dene
"""
import sys
sys.path.append('c:\\Users\\emir\\Desktop\\HorseRacingAPI-master')

from main.scrappers.idman import IdmanScrapper
import json

# Test horse ID (all_horse_ids.json'dan)
TEST_HORSE_ID = 80034

print(f"🐴 Test: horse_id = {TEST_HORSE_ID}\n")

try:
    data = IdmanScrapper.scrap_by_horse_id(TEST_HORSE_ID)
    
    print("✅ Başarılı!")
    print(f"İdman kayıt sayısı: {data['idman_count']}")
    print(f"URL: {data['url']}\n")
    
    if data['idman_records']:
        print("İlk 3 kayıt:")
        for i, record in enumerate(data['idman_records'][:3], 1):
            print(f"\n{i}. Kayıt:")
            print(json.dumps(record, ensure_ascii=False, indent=2))
    
    # Tüm veriyi kaydet
    with open('test_idman_output.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Tüm veri kaydedildi: test_idman_output.json")
    
except Exception as e:
    print(f"❌ Hata: {e}")
    import traceback
    traceback.print_exc()
