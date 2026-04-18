# -*- coding: utf-8 -*-
"""
117124 ID'li atın idmanını test et
"""
import sys
sys.path.append('c:\\Users\\emir\\Desktop\\HorseRacingAPI-master')

from main.scrappers.idman import IdmanScrapper
import json

horse_id = 117124

print(f"🔍 Horse {horse_id} idmanı çekiliyor...")
print(f"URL: https://www.tjk.org/TR/YarisSever/Query/Page/IdmanIstatistikleri?QueryParameter_AtId={horse_id}")
print("-" * 80)

try:
    data = IdmanScrapper.scrap_by_horse_id(horse_id)
    
    idman_records = data.get('idman_records', [])
    
    print(f"\n✅ Başarılı!")
    print(f"İdman kayıt sayısı: {len(idman_records)}")
    
    if idman_records:
        print(f"\nİlk 3 idman kaydı:")
        for i, record in enumerate(idman_records[:3], 1):
            print(f"\n{i}. İdman:")
            print(f"   Tarih: {record.get('İ. Tarihi')}")
            print(f"   Hipodrom: {record.get('İ. Hip.')}")
            print(f"   1000m: {record.get('1000m')}")
            print(f"   800m: {record.get('800m')}")
            print(f"   600m: {record.get('600m')}")
            print(f"   400m: {record.get('400m')}")
    else:
        print("\n⚠️ İdman kaydı yok!")
        print("Scraper çalıştı ama veri bulamadı.")
        print("\nHam veri:")
        print(json.dumps(data, ensure_ascii=False, indent=2)[:500])
    
except Exception as e:
    print(f"\n❌ HATA: {e}")
    import traceback
    traceback.print_exc()
