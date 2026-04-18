"""
================================================================================
AT YARIŞI TAHMİN SİSTEMİ - TEKNİK DOKÜMANTASYON
================================================================================

GENEL BAKIŞ:
-----------
Sistem, geçmiş kazanan atların ortalamasından oluşan "Dream Horse" profilleri 
ile yarışa katılacak atları karşılaştırarak 0-100 arası bir "Kazanma Uyumu" 
skoru hesaplıyor.

================================================================================
1. VERİ YAPISI
================================================================================

A) DREAM HORSE PROFİLLERİ:
   Lokasyon: E:\data\stats\dream_horse\
   Yapı: {kategori}/{şehir}/{breed}/{pist}_{mesafe}m.json
   
   Örnek: E:\data\stats\dream_horse\Maiden\Istanbul\İngiliz\Sentetik_1200m.json
   
   İçerik:
   - Ortalama yaş (horse_age)
   - Ortalama ağırlık (horse_weight)
   - Ortalama handicap (handicap_weight)
   - Ortalama start no (start_no)
   - En çok kazandıran jokey/antrenör/sahip
   - En çok kazanan baba/anne
   - Ortalama ganyan, agf, kgs
   - İDMAN ORTALAMALARI (normalize edilmiş):
     * idman_400m: "0.24.30"
     * idman_600m: "0.37.06"
     * idman_800m: "0.49.78"
     * idman_1000m: "1.02.95"
     * idman_1200m: ""
   - Metadata: Kaç at analiz edildi, her mesafede kaç atın idmanı var

B) YARIŞ VERİLERİ:
   Lokasyon: E:\data\program\{şehir}\{yıl}\{ay}.json
   
   İçerik:
   - Her at için: horse_id, horse_name, age, weight, jockey, trainer, vb.
   - Yarış bilgileri: kategori, pist, mesafe, şehir
   - İdman verileri: Sistem otomatik olarak E:\data\idman\ klasöründen yüklüyor

================================================================================
2. HESAPLAMA YÖNTEMLERİ
================================================================================

A) EUCLIDEAN DISTANCE (Öklid Mesafesi):
   ----------------------------------------
   Formül: √[(x₁-x₂)² + (y₁-y₂)² + (z₁-z₂)² + ...]
   
   Karşılaştırılan Özellikler:
   1. Yaş farkı: (at_yaşı - dream_yaşı)²
   2. Ağırlık farkı: (at_kilosu - dream_kilosu)²
   3. Handicap farkı: (at_handicap - dream_handicap)²
   4. Start no farkı: ((at_start - dream_start) / 20)² [normalize edilmiş]
   
   Örnek Hesaplama:
   - At: 3 yaş, 57kg, handicap yok, start #3
   - Dream: 2 yaş, 56.7kg, handicap yok, start #5
   - Farklar: (3-2)² + (57-56.7)² + 0 + ((3-5)/20)²
   - Distance = √(1 + 0.09 + 0 + 0.01) = √1.1 = 1.05
   
   Skor Dönüşümü:
   - Temel Skor = max(0, 100 - (distance × 10))
   - Distance 1.05 → Skor = 100 - 10.5 = 89.5/100

B) PİST NORMALIZASYONU (Katsayılar):
   ----------------------------------
   Her şehir+pist kombinasyonu için ortalama hız (m/s):
   
   Ankara Çim: 15.72 m/s  (HIZLI)
   İstanbul Sentetik: 15.51 m/s
   İstanbul Kum: 14.91 m/s
   Şanlıurfa Kum: 13.93 m/s  (YAVAŞ)
   
   Normalizasyon Formülü:
   normalized_time = idman_süresi × (idman_pist_hızı / yarış_pist_hızı)
   
   Örnek:
   - At Ankara Çim'de 400m'yi 0.23.00'te koştu
   - Yarış İstanbul Sentetik'te olacak
   - Normalize süre = 23.00 × (15.72 / 15.51) = 23.31 saniye
   
   Neden Önemli:
   Aynı at farklı pistlerde farklı hızlarda koşar. Bu katsayılar sayesinde
   tüm idmanları aynı pistte yapılmış gibi karşılaştırabiliyoruz.

C) İDMAN BONUSU:
   --------------
   At'ın idman süresi Dream Horse'tan daha hızlıysa bonus puan verilir.
   
   Hesaplama:
   - Fark = dream_süre - at_süresi (saniye cinsinden)
   - Bonus = min(fark × 2, 10)  [Her mesafe için max 10 puan]
   
   Örnek:
   400m için:
   - Dream: 24.30 saniye
   - At: 21.40 saniye (normalize edilmiş)
   - Fark: 24.30 - 21.40 = 2.90 saniye
   - Bonus: 2.90 × 2 = 5.80 puan ✓
   
   600m için:
   - Dream: 37.06 saniye
   - At: 36.40 saniye
   - Fark: 37.06 - 36.40 = 0.66 saniye
   - Bonus: 0.66 × 2 = 1.32 puan ✓
   
   Toplam İdman Bonusu: 5.80 + 1.32 = 7.12 puan (max 50)

D) FİNAL SKOR:
   ------------
   Kazanma Uyumu = min(100, temel_skor + idman_bonusu)
   
   Örnek:
   - Temel Skor (Euclidean): 83.57/100
   - İdman Bonusu: +5.80
   - Final Skor: 89.37/100 ★

================================================================================
3. ADIM ADIM ÇALIŞMA PRENSİBİ
================================================================================

ADIM 1: Dream Horse Bulma
   - Yarış kategorisi: "Maiden"
   - Şehir: "Istanbul"
   - Breed: "İngiliz" (age_group'tan çıkarılır)
   - Pist: "Sentetik"
   - Mesafe: "1200m"
   → Dosya: dream_horse/Maiden/Istanbul/İngiliz/Sentetik_1200m.json

ADIM 2: Her At İçin İdman Yükleme
   - At ID: 100453
   - Yarış tarihi: 27.01.2024
   → E:\data\idman\100400\100453.json dosyasından idman kayıtları yüklenir
   → 27.01.2024'ten ÖNCE olan en son idman bulunur
   → Örnek: 25.01.2024 tarihli idman

ADIM 3: Euclidean Distance Hesaplama
   At özellikleri:
   - Yaş: 3 yaş
   - Kilo: 57.0 kg
   - Handicap: -
   - Start: #3
   
   Dream özellikleri:
   - Yaş: 2 yaş
   - Kilo: 56.7 kg
   - Handicap: -
   - Start: #5
   
   Distance = √[(3-2)² + (57-56.7)² + ((3-5)/20)²] = 1.64
   Temel Skor = 100 - (1.64 × 10) = 83.6/100

ADIM 4: İdman Karşılaştırma ve Normalizasyon
   At'ın idmanı: 25.01.2024, İstanbul Kum
   - 400m: 0.23.30
   
   Yarış: 27.01.2024, İstanbul Sentetik
   
   Normalizasyon:
   - İstanbul Kum hızı: 14.91 m/s
   - İstanbul Sentetik hızı: 15.51 m/s
   - 23.30 × (14.91 / 15.51) = 22.40 saniye (normalize edilmiş)
   
   Dream'in 400m ortalaması: 24.30 saniye
   Fark: 24.30 - 22.40 = 1.90 saniye → HIZLI! ✓
   Bonus: 1.90 × 2 = 3.80 puan

ADIM 5: Final Skor
   Temel Skor: 83.6
   İdman Bonusu: +3.80
   → Final: 87.40/100

ADIM 6: Sıralama
   Tüm atlar skorlarına göre büyükten küçüğe sıralanır.
   En yüksek skora sahip at = En yüksek kazanma uyumu

================================================================================
4. KULLANIM ÖRNEĞİ
================================================================================

from predict_race import predict_race
from test_with_idman import load_race_from_program_with_idman

# 1. Yarış verilerini yükle (idman ile)
race_horses, race_info = load_race_from_program_with_idman(
    city="Istanbul",
    year=2024,
    month=1,
    day=27,
    race_number=1
)

# 2. Tahmin yap
results = predict_race(race_horses, race_info)

# 3. Sonuçları görüntüle
for pred in results['predictions']:
    print(f"{pred['horse_name']}: {pred['score']}/100")
    if pred['idman_comparison']:
        for dist, comp in pred['idman_comparison'].items():
            if comp['faster']:
                print(f"  ✓ {dist}: HIZLI (+{comp['bonus']} puan)")

================================================================================
5. AVANTAJLAR
================================================================================

✓ Objektif Veri: Dream Horse 46 gerçek galibiyetten oluşuyor
✓ Pist Farklılıkları: Ankara-Şanlıurfa arası hız farkı otomatik hesaplanıyor
✓ İdman Bonusu: Formdaki atlar ekstra puan alıyor
✓ Matematiksel: Euclidean distance bilimsel bir yöntem
✓ Normalize Edilmiş: 0-100 arası skor kolay anlaşılır

================================================================================
6. GELİŞTİRME POTANSİYELİ
================================================================================

İleride eklenebilecekler:
- Jokey/antrenör başarı oranları
- Son yarış sonuçları (last_6_races analizi)
- Baba/anne performans geçmişi
- Hava durumu etkisi
- Günün saati etkisi
- Rakip sayısı faktörü

================================================================================
ÖZET: Sistem, geçmiş verileri kullanarak ideal at profilini (Dream Horse) 
oluşturuyor ve yarıştaki her atı bu profille Euclidean distance, pist 
normalizasyonu ve idman bonusu kullanarak karşılaştırıp 0-100 arası bir 
kazanma uyumu skoru veriyor.
================================================================================
"""

print(__doc__)
