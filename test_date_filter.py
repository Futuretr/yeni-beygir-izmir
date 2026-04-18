"""
Tarih filtrelemenin doğru çalıştığını test eder
Programdaki yarış tarihinden ÖNCE olan son yarışı bulmalı
"""
import json
from pathlib import Path
from datetime import datetime

def test_date_filtering():
    """Tarih filtrelemenin doğru çalışıp çalışmadığını test et"""
    
    # Test atı: DERKO
    horse_id = 99966
    horse_file = Path(f"E:\\data\\horses\\{horse_id}\\{horse_id}.json")
    
    print("=" * 80)
    print("TARİH FİLTRELEME TESTİ")
    print("=" * 80)
    
    if not horse_file.exists():
        print(f"Hata: {horse_file} bulunamadı!")
        return
    
    with open(horse_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    races = data.get('races', [])
    print(f"\nAt: DERKO (ID: {horse_id})")
    print(f"Toplam Yarış Sayısı: {len(races)}")
    
    # Programdaki yarış tarihi
    program_date_str = "2024-01-27T00:00:00Z"
    program_date = datetime.fromisoformat(program_date_str.replace('Z', '+00:00'))
    
    print(f"\nProgramdaki Yarış Tarihi: {program_date.strftime('%d.%m.%Y')}")
    print("\n" + "-" * 80)
    print("TÜM YARIŞLAR (Tarih Sıralı):")
    print("-" * 80)
    
    # Tarihe göre sırala
    sorted_races = sorted(races, key=lambda r: r.get('race_date', ''))
    
    previous_races = []
    future_races = []
    
    for i, race in enumerate(sorted_races, 1):
        race_date_str = race.get('race_date', '')
        race_dt = datetime.fromisoformat(race_date_str.replace('Z', '+00:00'))
        
        status = ""
        if race_dt < program_date:
            status = "[ÖNCE] ✓"
            previous_races.append(race)
        elif race_dt == program_date:
            status = "[AYNI GÜN]"
        else:
            status = "[SONRA] ✗"
            future_races.append(race)
        
        print(f"{i}. {race_dt.strftime('%d.%m.%Y')} - {race.get('city'):10s} "
              f"{race.get('distance'):4d}m - Sıra: {race.get('finish_position'):2s} "
              f"- Derece: {race.get('time'):8s} {status}")
    
    print("\n" + "=" * 80)
    print("FİLTRELEME SONUCU:")
    print("=" * 80)
    print(f"Programdan ÖNCE olan yarışlar: {len(previous_races)}")
    print(f"Programdan SONRA olan yarışlar: {len(future_races)}")
    
    if previous_races:
        # En son olanı bul
        last_race = max(previous_races, key=lambda r: r.get('race_date', ''))
        last_date = datetime.fromisoformat(last_race.get('race_date').replace('Z', '+00:00'))
        
        print(f"\n★ SEÇİLEN SON YARIŞ (Programdan Önce):")
        print(f"  Tarih: {last_date.strftime('%d.%m.%Y')}")
        print(f"  Şehir: {last_race.get('city')}")
        print(f"  Pist: {last_race.get('track_type')}")
        print(f"  Mesafe: {last_race.get('distance')}m")
        print(f"  Derece: {last_race.get('time')}")
        print(f"  Sıra: {last_race.get('finish_position')}")
        print(f"  Fark (gün): {(program_date - last_date).days} gün önce")
        
        # DOĞRULAMA: Bu yarış gerçekten programdan önce mi?
        if last_date >= program_date:
            print("\n❌ HATA! Seçilen yarış programdan sonra veya aynı gün!")
        else:
            print("\n✓ DOĞRU! Seçilen yarış programdan önce.")
    else:
        print("\n⚠️ Programdan önce yarış bulunamadı!")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_date_filtering()
