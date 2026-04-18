# -*- coding: utf-8 -*-
"""
İdman HTML'ini direkt çek ve incele
"""
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

horse_id = 117124
page_num = 1

AJAX_URL = "https://www.tjk.org/TR/YarisSever/Query/DataRows/IdmanIstatistikleri"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'tr-TR,tr;q=0.9',
    'Referer': f'https://www.tjk.org/TR/YarisSever/Query/Page/IdmanIstatistikleri?QueryParameter_AtId={horse_id}',
    'X-Requested-With': 'XMLHttpRequest'
}

params = {
    'QueryParameter_AtId': horse_id,
    'PageNumber': page_num,
    'Sort': 'IDMANTARIH Desc'
}

param_str = urllib.parse.urlencode(params)
url = f"{AJAX_URL}?{param_str}"

print(f"🔍 İdman HTML çekiliyor...")
print(f"URL: {url}")
print("-" * 80)

try:
    req = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(req, timeout=15)
    html = response.read().decode('utf-8')
    
    print(f"\n✅ HTML çekildi!")
    print(f"HTML uzunluğu: {len(html)} karakter")
    print(f"\nİlk 1000 karakter:")
    print("-" * 80)
    print(html[:1000])
    print("-" * 80)
    
    # Parse et
    soup = BeautifulSoup(html, 'html.parser')
    rows = soup.find_all('tr')
    
    print(f"\n📊 Bulunan TR sayısı: {len(rows)}")
    
    if rows:
        print(f"\nİlk satır içeriği:")
        print(rows[0].prettify()[:500])
    else:
        print("\n⚠️ TR elementi bulunamadı!")
        print("\nTüm HTML:")
        print(html)
    
except Exception as e:
    print(f"\n❌ HATA: {e}")
    import traceback
    traceback.print_exc()
