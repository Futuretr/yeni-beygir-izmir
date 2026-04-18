# -*- coding: utf-8 -*-
"""
At Yarışı Tahmin Sistemi - İnteraktif Kullanım
Herhangi bir günün herhangi bir şehrindeki yarışları tahmin et
"""
import sys
import io
from test_with_idman import load_race_from_program_with_idman
from predict_race import predict_race

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def show_race_predictions(city, year, month, day, race_number):
    """Tek bir koşuyu göster"""
    result = load_race_from_program_with_idman(city, year, month, day, race_number)
    
    if not result:
        print(f"❌ Koşu bulunamadı!")
        return False
    
    race_horses, race_info = result
    res = predict_race(race_horses, race_info)
    
    if 'error' in res:
        print(f"❌ HATA: {res['error']}")
        return False
    
    print(f"\n{'='*100}")
    print(f"KOŞU #{race_number + 1} - {race_info['category']}")
    print(f"{'='*100}")
    print(f"Pist: {race_info['track_type']} {race_info['distance']}m")
    print(f"Yaş Grubu: {race_info.get('age_group', 'N/A')}")
    print(f"Toplam At: {len(race_horses)}")
    
    idman_count = sum(1 for h in race_horses if h.get('last_idman'))
    idman_percentage = (idman_count * 100 // len(race_horses)) if len(race_horses) > 0 else 0
    
    if idman_count == 0:
        print(f"⚠️  İdman Verisi: YOK ({year} yılı için idman verileri mevcut değil)")
        print(f"    Tahmin sadece DERECE + KİLO + HANDİKAP ile yapılıyor")
    else:
        print(f"✓ İdman Verisi: {idman_count}/{len(race_horses)} at ({idman_percentage}%)")
    
    dream = res['dream_horse']
    print(f"Dream Horse: {dream['total_wins_analyzed']} galibiyet analizi")
    
    print(f"\n{'─'*100}")
    print("TAHMİN SONUÇLARI:")
    print(f"{'─'*100}")
    
    for i, p in enumerate(res['predictions'][:5], 1):
        print(f"\n{i}. {p['horse_name']:25s} (#{p['start_no']})")
        print(f"   ⭐ SKOR: {p['score']:6.2f}  [Derece: {p['derece_score']:+.2f} | İdman: {p['idman_score']:+.2f}]")
        
        # Derece detay
        if p['derece_time_diff'] is not None:
            print(f"   • Derece Fark: {p['derece_time_diff']:+.2f}sn (100m bazlı)")
        
        print(f"   • Jokey: {p['jockey']}")
        
        # İdman detayları
        if p['idman_comparison']:
            details = []
            for dist, comp in p['idman_comparison'].items():
                if comp['bonus'] != 0:
                    symbol = "✓" if comp['bonus'] > 0 else "✗"
                    details.append(f"{symbol} {dist}({comp['time_diff']:+.1f}sn={comp['bonus']:+.1f}p)")
            if details:
                print(f"   • İdman: {', '.join(details)}")
    
    print(f"\n{'='*100}")
    print(f"🏆 ÖNERİ: {res['predictions'][0]['horse_name']} - {res['predictions'][0]['score']:.2f}/100")
    print(f"{'='*100}")
    
    return True

def main():
    """Ana program"""
    print("=" * 100)
    print("AT YARIŞI TAHMİN SİSTEMİ")
    print("=" * 100)
    
    while True:
        print("\n" + "─" * 100)
        
        # Şehir seçimi
        city = input("\nŞehir (örn: Istanbul, Izmir, Ankara) [çıkmak için 'q']: ").strip()
        if city.lower() == 'q':
            print("\nGörüşürüz!")
            break
        
        if not city:
            print("❌ Şehir giriniz!")
            continue
        
        # Tarih girişi
        date_input = input("Tarih (GG.AA.YYYY veya GG/AA/YYYY) [örn: 30.01.2026]: ").strip()
        if not date_input:
            print("❌ Tarih giriniz!")
            continue
        
        try:
            # Tarihi parse et
            if '.' in date_input:
                parts = date_input.split('.')
            elif '/' in date_input:
                parts = date_input.split('/')
            else:
                print("❌ Geçersiz tarih formatı! (GG.AA.YYYY kullanın)")
                continue
            
            day = int(parts[0])
            month = int(parts[1])
            year = int(parts[2])
            
            if not (1 <= day <= 31 and 1 <= month <= 12 and 2020 <= year <= 2030):
                print("❌ Geçersiz tarih!")
                continue
        
        except (ValueError, IndexError):
            print("❌ Geçersiz tarih formatı!")
            continue
        
        # Önce kaç koşu var kontrol et
        race_count = 0
        for i in range(20):  # Max 20 koşu kontrol et
            result = load_race_from_program_with_idman(city, year, month, day, i)
            if result:
                race_count = i + 1
            else:
                break
        
        if race_count == 0:
            print(f"\n❌ {day}.{month}.{year} tarihinde {city} için yarış bulunamadı!")
            continue
        
        print(f"\n✓ {day}.{month}.{year} - {city}: {race_count} koşu bulundu")
        
        while True:
            race_input = input(f"\nKoşu numarası (1-{race_count}) [tümü için 'hepsi', geri için 'g']: ").strip().lower()
            
            if race_input == 'g':
                break
            
            if race_input == 'hepsi':
                # Tüm koşuları göster
                for i in range(race_count):
                    show_race_predictions(city, year, month, day, i)
                    if i < race_count - 1:
                        input("\n[ENTER] ile devam...")
                break
            
            try:
                race_num = int(race_input)
                if 1 <= race_num <= race_count:
                    show_race_predictions(city, year, month, day, race_num - 1)
                else:
                    print(f"❌ Geçersiz koşu numarası! (1-{race_count} arası)")
            except ValueError:
                print("❌ Geçersiz giriş!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram sonlandırıldı.")
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        import traceback
        traceback.print_exc()
