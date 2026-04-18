"""
Manuel olarak 4. sayfayı kontrol et
"""
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

HORSE_ID = 80034
BASE_URL = "https://www.tjk.org/TR/YarisSever/Query/DataRows/IdmanIstatistikleri"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'tr-TR,tr;q=0.9',
    'Referer': f'https://www.tjk.org/TR/YarisSever/Query/Page/IdmanIstatistikleri?QueryParameter_AtId={HORSE_ID}',
    'X-Requested-With': 'XMLHttpRequest'
}

for page in [1, 2, 3, 4, 5]:
    params = {
        'QueryParameter_AtId': HORSE_ID,
        'PageNumber': page,
        'Sort': 'IDMANTARIH Desc'
    }
    
    param_str = urllib.parse.urlencode(params)
    url = f"{BASE_URL}?{param_str}"
    
    print(f"\n{'='*60}")
    print(f"Sayfa {page}")
    print(f"URL: {url}")
    
    try:
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req, timeout=15)
        html = response.read().decode('utf-8')
        
        soup = BeautifulSoup(html, 'html.parser')
        rows = soup.find_all('tr')
        
        print(f"Satır sayısı: {len(rows)}")
        
        if rows:
            print("İlk satır:")
            cells = rows[0].find_all(['td', 'th'])
            print(f"  Hücre sayısı: {len(cells)}")
            if cells:
                print(f"  İlk 3 hücre: {[c.get_text(strip=True)[:20] for c in cells[:3]]}")
        else:
            print("❌ Satır bulunamadı")
            break
            
    except Exception as e:
        print(f"❌ Hata: {e}")
        break
