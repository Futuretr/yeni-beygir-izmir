from predict_with_xgboost import XGBoostRacePredictor

p = XGBoostRacePredictor()
result = p.predict_race('Izmir', '2026', '222824')

print("="*80)
print("YARIŞ 1 TAHMİNLERİ")
print("="*80)

for i, pred in enumerate(result['predictions'], 1):
    print(f"\n{i}. {pred['horse_name']:<30}")
    print(f"   Skor: {float(pred['combined_score']):.2f}")
    print(f"   Tahmini Derece: {float(pred['predicted_position']):.2f}")
    print(f"   Top3 Olasılığı: {float(pred['top3_probability'])*100:.1f}%")
    print(f"   Position Score: {float(pred['position_score']):.2f}")

print("\n" + "="*80)
print("GERÇEK KAZANAN: KUZEYİN KRALI")
print("="*80)

# KUZEYİN KRALI nerede?
for i, pred in enumerate(result['predictions'], 1):
    if "KUZEYİN KRALI" in pred['horse_name']:
        print(f"\nKUZEYİN KRALI {i}. sırada tahmin edilmiş")
        print(f"  Skor: {float(pred['combined_score']):.2f}")
        print(f"  Tahmini Derece: {float(pred['predicted_position']):.2f}")
        print(f"  Top3 Prob: {float(pred['top3_probability'])*100:.1f}%")
        break
