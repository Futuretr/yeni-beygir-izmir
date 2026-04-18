"""
XGBoost ile Hızlı Tahmin - Komut Satırı Argümanları
Kullanım: python quick_predict.py <şehir> <yıl> [yarış_no]
"""
import sys
from predict_with_xgboost import XGBoostRacePredictor, display_predictions, normalize_city_name
def normalize_city_name(city):
    """Şehir ismini normalize et"""
    if not city:
        return None
    replacements = {
        'ı': 'i', 'İ': 'I',
        'ş': 's', 'Ş': 'S',
        'ğ': 'g', 'Ğ': 'G',
        'ü': 'u', 'Ü': 'U',
        'ö': 'o', 'Ö': 'O',
        'ç': 'c', 'Ç': 'C'
    }
    city_normalized = city
    for tr_char, en_char in replacements.items():
        city_normalized = city_normalized.replace(tr_char, en_char)
    return city_normalized.capitalize()

def normalize_date(date_str):
    """Tarih formatını YYYY-MM-DD'ye çevir"""
    date_str = date_str.replace('.', '-').replace('/', '-')
    parts = date_str.split('-')
    if len(parts) != 3:
        return date_str
    if len(parts[0]) == 4:
        return date_str
    else:
        day, month, year = parts
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
def main():
    if len(sys.argv) < 3:
        print("Kullanım: python quick_predict.py <şehir> <tarih> [yarış_no]")
        print("\nÖrnekler:")
        print("  python quick_predict.py Istanbul 29.01.2026")
        print("  python quick_predict.py Izmir 2026-01-29 2")
        print("  python quick_predict.py Ankara 30-01-2026 1")
        return
    
    city = normalize_city_name(sys.argv[1])
    date = normalize_date(sys.argv[2])
    year = date.split('-')[0]
    race_number = None
    
    if len(sys.argv) > 3:
        try:
            race_number = int(sys.argv[3]) - 1  # 0-indexed
        except ValueError:
            print(f"❌ Geçersiz yarış numarası: {sys.argv[3]}")
            return
    
    print("\n" + "="*100)
    print("🐎 XGBOOST MODEL İLE AT YARIŞI TAHMİNİ")
    print("="*100)
    
    # Model yükle
    try:
        predictor = XGBoostRacePredictor()
    except Exception as e:
        print(f"❌ Model yüklenemedi: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Tahmin yap
    print(f"\n⏳ {city} - {date} için tahmin yapılıyor...")
    result = predictor.predict_from_race_json_dir(city, year, date, race_number)
    
    # Tarihi result'a ekle
    if 'error' not in result:
        result['date'] = date
    
    # Sonuçları göster
    display_predictions(result)

if __name__ == "__main__":
    main()
