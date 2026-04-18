"""
Gerçek sonuçlarla tahminleri karşılaştır ve analiz et
"""
import pandas as pd
import json
from pathlib import Path
from predict_with_xgboost import XGBoostRacePredictor

# CSV'yi oku
csv_path = r"c:\Users\emir\Downloads\29.01.2026-İzmir-GunlukYarisSonuclari-TR.csv"

# Manuel parse - CSV formatı karmaşık
results = {
    1: {"winner": "KUZEYİN KRALI", "top3": ["KUZEYİN KRALI", "MİGRAKOM BEYİ", "CURLIN DRACARYS"]},
    2: {"winner": "MOĞOL", "top3": ["MOĞOL", "MOMENT SAVER", "RING RANG RONG"]},
    3: {"winner": "EL CACİQUE", "top3": ["EL CACİQUE", "LOST TREASURE", "BAHİSÇİ"]},
    4: {"winner": "ŞİMŞEKKIRAN", "top3": ["ŞİMŞEKKIRAN", "TURBO KING", "ASLAN KILICI"]},
    5: {"winner": "KIVILCIM ATEŞİ", "top3": ["KIVILCIM ATEŞİ", "TAMERKIZ", "HÜKÜMDAR KIZ"]},
    6: {"winner": "HOLİGAN", "top3": ["HOLİGAN", "SERDAREFE", "BASKINSOY"]},
    7: {"winner": "JANN POLL", "top3": ["JANN POLL", "APOLLO MAXIMUS", "RÜZGARIN SESİ"]},
    8: {"winner": "OBRADA", "top3": ["OBRADA", "OĞLUM FIRAT", "KAANER"]}
}

def normalize_name(name):
    """At ismini normalize et"""
    # Parantez içindeki bilgileri temizle
    name = name.split('(')[0].strip()
    # Ekstra boşlukları temizle
    name = ' '.join(name.split())
    # Büyük harfe çevir
    return name.upper()

def compare_predictions(city, date):
    """Tahminleri gerçek sonuçlarla karşılaştır"""
    
    predictor = XGBoostRacePredictor()
    year = date.split('-')[0]
    
    # Tüm yarışlar için tahmin al
    result = predictor.predict_from_race_json_dir(city, year, date, None)
    
    if 'error' in result:
        print(f"❌ Hata: {result['error']}")
        return
    
    print("\n" + "="*120)
    print(f"🎯 TAHMİN DOĞRULUĞU ANALİZİ - {city.upper()} {date}")
    print("="*120)
    
    total_races = 0
    winner_correct = 0
    top3_correct = 0
    winner_in_top3 = 0
    winner_in_top5 = 0
    
    for race in result['races']:
        race_num = race.get('actual_race_number', race['race_number'] + 1)
        
        if race_num not in results:
            continue
        
        total_races += 1
        real_result = results[race_num]
        predictions = race['predictions']
        
        # At isimlerini normalize et
        real_winner = normalize_name(real_result['winner'])
        real_top3 = [normalize_name(name) for name in real_result['top3']]
        
        pred_winner = normalize_name(predictions[0]['horse_name'])
        pred_top3 = [normalize_name(p['horse_name']) for p in predictions[:3]]
        pred_top5 = [normalize_name(p['horse_name']) for p in predictions[:5]]
        
        # Kazanan doğru mu?
        winner_match = (real_winner == pred_winner)
        if winner_match:
            winner_correct += 1
        
        # Kazanan top 3'te mi?
        if real_winner in pred_top3:
            winner_in_top3 += 1
        
        # Kazanan top 5'te mi?
        if real_winner in pred_top5:
            winner_in_top5 += 1
        
        # Top 3 kesişimi
        top3_matches = len(set(real_top3) & set(pred_top3))
        if top3_matches > 0:
            top3_correct += top3_matches
        
        # Detaylı çıktı
        print(f"\n{'─'*120}")
        print(f"🏇 YARIŞ #{race_num} - {race['race_info']['category']}")
        print(f"{'─'*120}")
        
        print(f"\n✅ GERÇEK SONUÇ:")
        print(f"   1️⃣  {real_top3[0]}")
        print(f"   2️⃣  {real_top3[1]}")
        print(f"   3️⃣  {real_top3[2]}")
        
        print(f"\n🤖 MODEL TAHMİNİ:")
        for i, pred in enumerate(predictions[:5], 1):
            name = normalize_name(pred['horse_name'])
            score = pred['combined_score']
            pos = pred['predicted_position']
            prob = pred['top3_probability'] * 100
            
            # İşaret ekle
            marker = ""
            if name == real_winner:
                marker = " 🏆 KAZANAN!"
            elif name in real_top3:
                actual_pos = real_top3.index(name) + 1
                marker = f" ✓ (Gerçek: {actual_pos}.)"
            
            emoji = "1️⃣" if i == 1 else "2️⃣" if i == 2 else "3️⃣" if i == 3 else f"{i}."
            print(f"   {emoji}  {name:40} (Skor: {score:5.1f}, Pos: {pos:.1f}, Prob: {prob:.0f}%){marker}")
        
        # Analiz
        print(f"\n📊 ANALIZ:")
        if winner_match:
            print(f"   ✅ Kazanan doğru tahmin edildi!")
        else:
            print(f"   ❌ Kazanan yanlış")
            # Gerçek kazanan nerede?
            for i, pred in enumerate(predictions, 1):
                if normalize_name(pred['horse_name']) == real_winner:
                    print(f"   ℹ️  Gerçek kazanan modelimizde {i}. sırada")
                    print(f"      Skor: {pred['combined_score']:.1f}, Tahmin pos: {pred['predicted_position']:.2f}, Top3 prob: {pred['top3_probability']*100:.1f}%")
                    break
        
        print(f"   🎯 Top 3 kesişim: {top3_matches}/3")
    
    # ÖZET
    print("\n" + "="*120)
    print("📈 GENEL PERFORMANS ÖZETİ")
    print("="*120)
    print(f"\nToplam Yarış: {total_races}")
    print(f"\n🏆 Kazanan Doğruluğu:")
    print(f"   • Tam isabet: {winner_correct}/{total_races} ({winner_correct/total_races*100:.1f}%)")
    print(f"   • Kazanan top 3'te: {winner_in_top3}/{total_races} ({winner_in_top3/total_races*100:.1f}%)")
    print(f"   • Kazanan top 5'te: {winner_in_top5}/{total_races} ({winner_in_top5/total_races*100:.1f}%)")
    print(f"\n🎯 Top 3 Performansı:")
    print(f"   • Toplam doğru at: {top3_correct}/{total_races*3} ({top3_correct/(total_races*3)*100:.1f}%)")
    print(f"   • Ortalama kesişim: {top3_correct/total_races:.2f}/3 at")
    
    # ÖNERİLER
    print("\n" + "="*120)
    print("💡 İYİLEŞTİRME ÖNERİLERİ")
    print("="*120)
    
    if winner_in_top3 > winner_correct * 2:
        print("\n⚠️  Kazanan genelde top 3'te ama 1. sırada değil")
        print("   → Skorlama ağırlıklarını ayarla")
        print("   → Top 3 probability'yi daha fazla ağırlıklandır")
    
    if top3_correct / total_races < 1.5:
        print("\n⚠️  Top 3 kesişimi düşük")
        print("   → Feature engineering iyileştir")
        print("   → Son yarış performanslarını daha detaylı incele")
    
    print("\n")

if __name__ == "__main__":
    compare_predictions("Izmir", "2026-01-29")
