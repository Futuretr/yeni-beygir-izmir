# -*- coding: utf-8 -*-
"""
İdman Veri Kontrolü - Hangi yarışlarda idman var?
"""
import sys
import io
from test_with_idman import load_race_from_program_with_idman
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_city_races():
    """Farklı tarih/şehirlerde idman kapsamını kontrol et"""
    
    test_cases = [
        ("Istanbul", 2024, 1, 27, "İstanbul 2024 - Geçmiş yarış"),
        ("Izmir", 2026, 1, 30, "İzmir 2026 - Gelecek yarış"),
        ("Ankara", 2024, 6, 15, "Ankara 2024 - Geçmiş yarış"),
    ]
    
    print("=" * 100)
    print("İDMAN VERİSİ KAPSAM ANALİZİ")
    print("=" * 100)
    
    for city, year, month, day, description in test_cases:
        print(f"\n{description}")
        print("-" * 100)
        
        # İlk koşuyu kontrol et
        result = load_race_from_program_with_idman(city, year, month, day, 0)
        
        if not result:
            print(f"❌ Yarış bulunamadı: {city} {day}.{month}.{year}")
            continue
        
        horses, info = result
        idman_count = sum(1 for h in horses if h.get("last_idman"))
        
        print(f"📍 {city} - {day}.{month}.{year}")
        print(f"   Toplam At: {len(horses)}")
        print(f"   İdman Olan: {idman_count}/{len(horses)} ({idman_count*100//len(horses) if len(horses)>0 else 0}%)")
        
        if idman_count > 0:
            print(f"   ✓ İdman verileri mevcut!")
            # Örnek idman göster
            for h in horses:
                if h.get("last_idman"):
                    idman = h["last_idman"]
                    tarih = idman.get("İ. Tarihi") or idman.get("Ä°. Tarihi")
                    print(f"      {h['horse_name']}: İdman tarihi {tarih}")
                    break
        else:
            print(f"   ✗ Bu yarış için idman verisi yok")
            print(f"      Not: 2026 yarışları için idman verileri henüz toplanmamış olabilir")
    
    # İdman klasörü istatistikleri
    print("\n" + "=" * 100)
    print("İDMAN KLASÖRÜ İSTATİSTİKLERİ")
    print("=" * 100)
    
    idman_dir = Path("E:\\data\\idman")
    if idman_dir.exists():
        folders = list(idman_dir.iterdir())
        total_files = 0
        for folder in folders[:10]:  # İlk 10 klasör
            if folder.is_dir():
                files = list(folder.glob("*.json"))
                total_files += len(files)
        
        print(f"Toplam klasör: {len(folders)}")
        print(f"İlk 10 klasörde dosya: {total_files}")
        print(f"İlk klasör: {folders[0].name if folders else 'N/A'}")
        print(f"Son klasör: {folders[-1].name if folders else 'N/A'}")
    else:
        print("❌ İdman klasörü bulunamadı!")

if __name__ == "__main__":
    check_city_races()
