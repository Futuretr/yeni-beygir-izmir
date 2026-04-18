import requests
import re

url = "https://www.tjk.org/TR/YarisSever/Info/Sehir/GunlukYarisSonuclari?SehirId=3&QueryParameter_Tarih=10%2F01%2F2026&SehirAdi=Istanbul"

response = requests.get(url, timeout=10)
html = response.text

# Race ID bul
race_ids = re.findall(r'<div[^>]+id="(\d+)"', html)
print(f"All IDs found: {len(race_ids)}")
print(f"First 5 Race IDs: {race_ids[:5]}")

if race_ids:
    race_id = race_ids[0]
    
    # İlk race'i izole et
    race_match = re.search(rf'<div[^>]*id="{race_id}".*?(?=<div[^>]*class="races-pane|$)', html, re.DOTALL)
    
    if race_match:
        race_html = race_match.group(0)
        
        # Save to file for inspection
        with open('race_html_sample.html', 'w', encoding='utf-8') as f:
            f.write(race_html[:5000])
        
        # Horse ID pattern
        horse_ids = re.findall(r'QueryParameter_AtId=(\d+)', race_html)
        print(f"\nHorse IDs: {horse_ids[:5]}")
        
        # Time pattern  
        times = re.findall(r'GunlukYarisSonuclari-Derece[^>]*>\s*([^<]+)', race_html)
        print(f"\nTimes: {times[:5]}")
        
        # Fark pattern
        farks = re.findall(r'GunlukYarisSonuclari-Fark[^>]*>\s*([^<]*)</td', race_html)
        print(f"\nFarks: {farks[:5]}")

print("\n✅ race_html_sample.html kaydedildi")
