"""
TJK sitesinden canlı bir sonuç sayfası çekip HTML yapısını incele
"""
import requests
from bs4 import BeautifulSoup

# 10 Ocak 2026 İstanbul sonuçları
url = "https://www.tjk.org/TR/YarisSever/Info/Sehir/GunlukYarisSonuclari?SehirId=3&QueryParameter_Tarih=10%2F01%2F2026&SehirAdi=Istanbul"

print(f"🔍 URL: {url}\n")
print("📥 Sayfa indiriliyor...")

try:
    response = requests.get(url, timeout=30)
    print(f"Status: {response.status_code}")
    response.raise_for_status()
    
    # HTML'i kaydet
    with open('tjk_result_page.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("✅ HTML kaydedildi: tjk_result_page.html\n")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # İlk yarışı bul
    race_divs = soup.find_all("div", class_="races-pane")
    
    if race_divs:
        print(f"✅ {len(race_divs)} yarış bulundu\n")
        
        # İlk yarışın tablosunu al
        first_race = race_divs[0]
        table = first_race.find("tbody")
        
        if table:
            # İlk satırı al (1. atı)
            first_row = table.find("tr")
            
            if first_row:
                # Tüm sütunları listele
                columns = first_row.find_all("td")
                
                print("📊 TÜM SÜTUNLAR:")
                print("=" * 80)
                for i, col in enumerate(columns, 1):
                    class_name = col.get('class', [''])[0] if col.get('class') else 'no-class'
                    content = col.get_text(strip=True)[:50]  # İlk 50 karakter
                    print(f"{i:2d}. {class_name:50s} = {content}")
                
                print("\n🔍 DERECE/FARK/TIME ARAYIN:")
                for i, col in enumerate(columns, 1):
                    class_name = col.get('class', [''])[0] if col.get('class') else ''
                    if any(word in class_name.lower() for word in ['derece', 'fark', 'time', 'zaman', 'sure']):
                        print(f"  ✅ Sütun {i}: {class_name} = {col.get_text(strip=True)}")
    else:
        print("❌ Yarış bulunamadı")
        
except Exception as e:
    print(f"❌ HATA: {e}")
