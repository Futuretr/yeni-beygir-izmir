# -*- coding: utf-8 -*-
"""
İdman ana sayfasını çek ve doğru AJAX URL'sini bul
"""
import urllib.request
from bs4 import BeautifulSoup
import re

horse_id = 117124

# Ana sayfa URL
main_url = f"https://www.tjk.org/TR/YarisSever/Query/Page/IdmanIstatistikleri?QueryParameter_AtId={horse_id}"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'tr-TR,tr;q=0.9'
}

print(f"🔍 Ana sayfa çekiliyor...")
print(f"URL: {main_url}")
print("-" * 80)

try:
    req = urllib.request.Request(main_url, headers=headers)
    response = urllib.request.urlopen(req, timeout=15)
    html = response.read().decode('utf-8')
    
    print(f"\n✅ Sayfa çekildi!")
    print(f"HTML uzunluğu: {len(html)} karakter")
    
    # JavaScript içinde AJAX URL'lerini ara
    ajax_urls = re.findall(r'(https?://[^\s"\'<>]+(?:DataRows|Ajax)[^\s"\'<>]*)', html)
    
    if ajax_urls:
        print(f"\n📡 Bulunan AJAX URL'leri:")
        for url in set(ajax_urls):
            print(f"   {url}")
    
    # Table yapısını kontrol et
    soup = BeautifulSoup(html, 'html.parser')
    
    # Tablo bul
    tables = soup.find_all('table')
    print(f"\n📊 Bulunan table sayısı: {len(tables)}")
    
    # İdman tablosunu bul
    for i, table in enumerate(tables):
        rows = table.find_all('tr')
        if rows:
            print(f"\nTable {i+1}: {len(rows)} satır")
            # İlk satırın içeriğini göster
            if len(rows) > 0:
                cells = rows[0].find_all(['th', 'td'])
                if cells:
                    print(f"  İlk satır: {[c.get_text(strip=True)[:20] for c in cells[:5]]}")
    
    # Script etiketlerini kontrol et
    scripts = soup.find_all('script')
    print(f"\n📜 Script sayısı: {len(scripts)}")
    
    for script in scripts:
        script_text = script.string
        if script_text and 'IdmanIstatistikleri' in script_text:
            print(f"\nİdman ile ilgili script bulundu:")
            print(script_text[:500])
            break
    
    # HTML'in bir kısmını kaydet
    with open('idman_page_debug.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\n✅ HTML kaydedildi: idman_page_debug.html")
    
except Exception as e:
    print(f"\n❌ HATA: {e}")
    import traceback
    traceback.print_exc()
