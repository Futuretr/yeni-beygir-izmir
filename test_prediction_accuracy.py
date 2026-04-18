"""
Tahmin doğruluğunu test et - Gerçek sonuçlarla karşılaştır
"""
import json
from pathlib import Path
from predict_with_xgboost import XGBoostRacePredictor

def test_single_race(city, year, race_id):
    """Tek bir yarışı test et"""
    
    # Race verisini yükle
    race_path = Path(f"E:/data/race_jsons/{city}/{year}/{race_id}.json")
    
    if not race_path.exists():
        print(f"Yarış bulunamadı: {race_id}")
        return
    
    with open(race_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, list):
            race_data = data[0]
        else:
            race_data = data
    
    # Gerçek sonuçlar
    horses_with_results = [h for h in race_data.get('horses', []) 
                           if h.get('finish_position')]
    
    if not horses_with_results:
        print("❌ Bu yarışta sonuç yok")
        return
    
    horses_with_results.sort(key=lambda x: int(x['finish_position']))
    
    print("\n" + "="*100)
    print(f"🏇 TEST: {race_data.get('race_category', 'N/A')} - {race_data.get('distance', 'N/A')}m")
    print(f"📅 Tarih: {race_data.get('race_date', 'N/A')}")
    print("="*100)
    
    # Gerçek sonuçları göster
    print("\n📊 GERÇEK SONUÇLAR:")
    print("─"*100)
    for i, horse in enumerate(horses_with_results[:10], 1):
        print(f"{horse['finish_position']:2} - {horse['horse_name']:30} (#{horse.get('start_no', 'N/A')})")
    
    # Tahminleri al
    predictor = XGBoostRacePredictor()
    result = predictor.predict_race(city, year, race_id)
    
    if 'error' in result:
        print(f"❌ Tahmin hatası: {result['error']}")
        return
    
    predictions = result['predictions']
    
    print("\n🤖 MODEL TAHMİNLERİ:")
    print("─"*100)
    for i, pred in enumerate(predictions[:10], 1):
        print(f"{i:2} - {pred['horse_name']:30} (#{pred['start_no']}) - Skor: {pred['combined_score']:.1f}")
    
    # Doğruluk analizi
    print("\n📈 DOĞRULUK ANALİZİ:")
    print("─"*100)
    
    # Top 3 doğruluğu
    real_top3 = set(h['horse_name'] for h in horses_with_results[:3])
    pred_top3 = set(p['horse_name'] for p in predictions[:3])
    
    correct_top3 = real_top3 & pred_top3
    
    print(f"✓ Top 3'te doğru: {len(correct_top3)}/3")
    if correct_top3:
        print(f"  Doğru atlar: {', '.join(correct_top3)}")
    
    # Kazananı buldu mu?
    winner = horses_with_results[0]['horse_name']
    pred_winner = predictions[0]['horse_name']
    
    if winner == pred_winner:
        print(f"🏆 KAZANAN DOĞRU TAHMİN EDİLDİ: {winner}")
    else:
        print(f"❌ Kazanan yanlış:")
        print(f"   Gerçek kazanan: {winner}")
        print(f"   Tahmin edilen: {pred_winner}")
        
        # Gerçek kazanan kaçıncı sırada tahmin edilmiş?
        for i, pred in enumerate(predictions, 1):
            if pred['horse_name'] == winner:
                print(f"   Gerçek kazanan modelimizde {i}. sırada (Skor: {pred['combined_score']:.1f})")
                break
    
    # Detaylı feature analizi - kazanan için
    print("\n🔍 KAZANANIN FEATURE'LARI:")
    print("─"*100)
    winner_data = next((h for h in race_data['horses'] if h['horse_name'] == winner), None)
    if winner_data:
        print(f"At: {winner}")
        print(f"Son 3 yarış: {winner_data.get('last_races', [])[:3]}")
        print(f"Jokey: {winner_data.get('jockey', 'N/A')}")
        print(f"Kilo: {winner_data.get('weight', {}).get('total', 'N/A')}")
        print(f"Handikap: {winner_data.get('weight', {}).get('handicap', 'N/A')}")
        print(f"Ganyan: {winner_data.get('ganyan', 'N/A')}")
    
    print("\n")

def main():
    """Ana test"""
    
    print("\n" + "="*100)
    print("🎯 TAHMIN DOĞRULUĞU TEST SİSTEMİ")
    print("="*100)
    
    # İzmir 29.01.2026 - 2. yarış (Maiden)
    test_single_race("Izmir", "2026", "222819")
    
    # İzmir 29.01.2026 - 5. yarış (Handikap - BERRANUR kazandı)
    test_single_race("Izmir", "2026", "222828")
    
    # İzmir 29.01.2026 - 8. yarış (SATIŞ 1)
    test_single_race("Izmir", "2026", "222826")

if __name__ == "__main__":
    main()
