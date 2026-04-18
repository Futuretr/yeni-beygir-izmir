"""
Test: Bir at için idman istatistiklerini çek
Örnek: horse_id = 80034
"""
import requests
import json

# Test horse ID
HORSE_ID = 80034

# TJK API endpoint denemeleri
urls_to_try = [
    f"https://www.tjk.org/TR/YarisSever/Query/Page/IdmanIstatistikleri?QueryParameter_AtId={HORSE_ID}",
    f"https://www.tjk.org/api/IdmanIstatistikleri/{HORSE_ID}",
    f"https://www.tjk.org/api/v1/IdmanIstatistikleri?atId={HORSE_ID}",
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/html',
    'Accept-Language': 'tr-TR,tr;q=0.9',
    'Referer': 'https://www.tjk.org/'
}

print(f"🐴 Test Horse ID: {HORSE_ID}\n")

for url in urls_to_try:
    print(f"🔍 Deneniyor: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            # JSON mi?
            try:
                data = response.json()
                print(f"   ✅ JSON response!")
                print(f"   Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                print(f"   Sample: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
                break
            except:
                # HTML mi?
                content = response.text[:1000]
                print(f"   ⚠️  HTML/Text response (first 500 chars):")
                print(f"   {content[:500]}")
                
                # İçinde "IdmanIstatistikleri" var mı?
                if 'idman' in content.lower():
                    print("   ⚠️  İdman kelimesi bulundu, sayfa doğru ama parse gerekli")
        
        print()
    except Exception as e:
        print(f"   ❌ Hata: {e}\n")

print("\n💡 Django API endpoint'ine bakalım...")
print("Django views.py dosyasında IdmanIstatistikleri endpoint var mı?")
