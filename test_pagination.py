"""
Test: TJK idman sayfasında pagination var mı kontrol et
"""
from bs4 import BeautifulSoup
import urllib.request
import sys

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

HORSE_ID = 80034
url = f"https://www.tjk.org/TR/YarisSever/Query/Page/IdmanIstatistikleri?QueryParameter_AtId={HORSE_ID}"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'tr-TR,tr;q=0.9',
    'Referer': 'https://www.tjk.org/'
}

req = urllib.request.Request(url, headers=headers)
response = urllib.request.urlopen(req, timeout=15)
html = response.read().decode('utf-8')

soup = BeautifulSoup(html, 'html.parser')

# Pagination bul
pagination = soup.find_all('a', class_='page-link')
print(f"Pagination link sayısı: {len(pagination)}")

# Pagination div/ul
pager = soup.find('ul', class_='pagination')
if pager:
    print("✅ Pagination bulundu!")
    print(f"Pagination HTML:\n{pager}")
else:
    print("❌ Pagination bulunamadı")

# Tablo satır sayısı
table = soup.find('table')
if table:
    rows = table.find_all('tr')
    print(f"\nTablo satır sayısı: {len(rows) - 1} (başlık hariç)")

# "Göster" dropdown veya "Daha Fazla" button
show_more = soup.find('button', string=lambda x: x and 'daha' in x.lower())
if show_more:
    print(f"✅ 'Daha Fazla' butonu bulundu: {show_more}")

# Select/dropdown (sayfa başına kayıt sayısı)
selects = soup.find_all('select')
for sel in selects:
    print(f"\nSelect bulundu: {sel.get('name', 'N/A')}")
    options = sel.find_all('option')
    print(f"Seçenekler: {[opt.get_text(strip=True) for opt in options]}")

# DataTables kullanımı (JavaScript)
if 'DataTable' in html or 'datatable' in html.lower():
    print("\n✅ DataTables kullanılıyor - JavaScript ile pagination")

# Toplam kayıt sayısı yazısı
total_text = soup.find(string=lambda x: x and 'toplam' in x.lower() or ('kayıt' in x.lower() and '199' in x))
if total_text:
    print(f"\n✅ Toplam kayıt yazısı: {total_text}")

# HTML'i kaydet (analiz için)
with open('idman_page.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f"\n💾 HTML kaydedildi: idman_page.html")
