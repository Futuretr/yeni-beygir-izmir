"""
Gerçek sonuçlarla karşılaştırma - İzmir 29.01.2026
Tüm 8 yarış için detaylı analiz
"""
import sys
import io

# UTF-8 encoding zorla
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from predict_with_xgboost import XGBoostRacePredictor

# Gerçek sonuçlar
real_results = {
    1: ["KUZEYİN KRALI", "MİGRAKOM BEYİ", "CURLIN DRACARYS"],
    2: ["MOĞOL", "MOMENT SAVER", "RING RANG RONG"],
    3: ["EL CACİQUE", "LUCKY SPIRIT", "GÜRER KHAN"],
    4: ["ŞİMŞEKKIRAN", "TURBO KING", "ASLAN KILICI"],
    5: ["KIVILCIM ATEŞİ", "TAMERKIZ", "HÜKÜMDAR KIZ"],
    6: ["HOLİGAN", "SEREN RÜZGARI", "BASKINSOY"],
    7: ["JANN POLL", "ALFA ZEKA", "TATAR"],
    8: ["OBRADA", "OĞLUM FIRAT", "KAANER"]
}

# Race ID'ler
race_ids = {
    1: '222824',
    2: '222819',
    3: '222827',
    4: '222830',
    5: '222828',
    6: '222829',
    7: '222820',
    8: '222826'
}

def normalize_name(name):
    """İsim karşılaştırması için normalize et"""
    return name.upper().replace("(USA)", "").replace("(GB)", "").strip()

# Model yükle
print("Model yükleniyor...")
predictor = XGBoostRacePredictor()

total_winner_correct = 0
total_winner_in_top3 = 0
total_winner_in_top5 = 0
total_top3_correct = 0
total_top3_possible = 0

print("\n" + "="*100)
print("İZMİR 29.01.2026 - 8 YARIŞ ANALİZİ")
print("="*100)

for race_num in range(1, 9):
    print(f"\n{'='*100}")
    print(f"YARIŞ #{race_num}")
    print('='*100)
    
    # Tahmin yap
    result = predictor.predict_race('Izmir', '2026', race_ids[race_num])
    
    if 'error' in result:
        print(f"❌ Hata: {result['error']}")
        continue
    
    predictions = result['predictions']
    pred_top3 = [normalize_name(p['horse_name']) for p in predictions[:3]]
    pred_all = [normalize_name(p['horse_name']) for p in predictions]
    
    # Gerçek sonuçlar
    real_top3 = [normalize_name(name) for name in real_results[race_num]]
    real_winner = real_top3[0]
    
    print(f"\nKategori: {result['race_info']['category']}")
    print(f"Toplam At: {len(predictions)}")
    
    print(f"\n📊 GERÇEK TOP 3:")
    for i, name in enumerate(real_results[race_num], 1):
        print(f"  {i}. {name}")
    
    print(f"\n🔮 TAHMİN TOP 5:")
    for i, pred in enumerate(predictions[:5], 1):
        name = pred['horse_name']
        score = float(pred['combined_score'])
        pos = float(pred['predicted_position'])
        prob = float(pred['top3_probability']) * 100
        
        # Gerçek top 3'te mi?
        norm_name = normalize_name(name)
        is_real_top3 = norm_name in real_top3
        is_winner = norm_name == real_winner
        
        marker = ""
        if is_winner:
            marker = "🏆 KAZANAN"
        elif is_real_top3:
            marker = "✓ Top3"
        
        print(f"  {i}. {name:<35} Score:{score:6.2f} | Pos:{pos:5.2f} | Prob:{prob:5.1f}%  {marker}")
    
    # Kazanan nerede?
    try:
        winner_rank = pred_all.index(real_winner) + 1
        print(f"\n🎯 KAZANAN ({real_results[race_num][0]}) TAHMİN SIRASI: {winner_rank}")
        
        if winner_rank == 1:
            total_winner_correct += 1
            print("   ✓✓ KAZANAN DOĞRU TAHMİN EDİLDİ!")
        elif winner_rank <= 3:
            total_winner_in_top3 += 1
            print("   ✓ Kazanan top 3'te")
        elif winner_rank <= 5:
            total_winner_in_top5 += 1
            print("   ~ Kazanan top 5'te")
        else:
            print(f"   ✗ Kazanan {winner_rank}. sırada")
            
        # Kazananın skorları
        winner_pred = predictions[winner_rank - 1]
        print(f"   Score: {float(winner_pred['combined_score']):.2f}")
        print(f"   Predicted Position: {float(winner_pred['predicted_position']):.2f}")
        print(f"   Top3 Probability: {float(winner_pred['top3_probability'])*100:.1f}%")
        
    except ValueError:
        print(f"\n❌ KAZANAN ({real_results[race_num][0]}) TAHMİNLERDE YOK!")
        winner_rank = 999
    
    # Top 3 doğruluk
    top3_matches = len(set(pred_top3) & set(real_top3))
    total_top3_correct += top3_matches
    total_top3_possible += 3
    
    print(f"\n📈 TOP 3 BAŞARI: {top3_matches}/3 doğru")
    if top3_matches == 3:
        print("   ✓✓ Tüm top 3 doğru!")
    elif top3_matches == 2:
        print("   ✓ 2/3 doğru")
    elif top3_matches == 1:
        print("   ~ 1/3 doğru")
    else:
        print("   ✗ Hiçbiri doğru değil")

# Genel Özet
print("\n" + "="*100)
print("GENEL PERFORMANS ÖZETİ")
print("="*100)

print(f"\n🏆 KAZANAN TAHMİNİ:")
print(f"  • Tam Doğru: {total_winner_correct}/8 ({total_winner_correct/8*100:.1f}%)")
print(f"  • Top 3'te: {total_winner_in_top3}/8 ({total_winner_in_top3/8*100:.1f}%)")
print(f"  • Top 5'te: {total_winner_in_top5}/8 ({total_winner_in_top5/8*100:.1f}%)")

print(f"\n📊 TOP 3 TAHMİNİ:")
print(f"  • Doğru Atlar: {total_top3_correct}/{total_top3_possible} ({total_top3_correct/total_top3_possible*100:.1f}%)")
print(f"  • Ortalama Eşleşme: {total_top3_correct/8:.2f}/3 at per yarış")

print("\n" + "="*100)
