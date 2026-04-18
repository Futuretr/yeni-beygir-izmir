import json

# Yarış 2 - 222819.json
with open('E:/data/race_jsons/Izmir/2026/222819.json', encoding='utf-8') as f:
    data = json.load(f)[0]

print("="*80)
print(f"YARIŞ 2 - {data['race_category']}")
print(f"Tarih: {data['race_date']} - Yarış No: {data['race_number']}")
print("="*80)

print("\nAtlar:")
for i, horse in enumerate(data['horses'], 1):
    print(f"{i}. {horse['horse_name']:<35} (Start: {horse.get('start_no', '?')})")

print(f"\nToplam: {len(data['horses'])} at")

# Gerçek kazanan
print("\n" + "="*80)
print("GERÇEK KAZANAN: MOĞOL")
print("="*80)

# At var mı kontrol
horse_names = [h['horse_name'] for h in data['horses']]
if 'MOĞOL' in horse_names:
    print("OK MOĞOL programda VAR")
    idx = horse_names.index('MOĞOL')
    print(f"Start No: {data['horses'][idx].get('start_no', '?')}")
elif 'MOGOL' in horse_names:
    print("OK MOGOL (Turkce karakter olmadan) programda VAR")
else:
    print("X MOGOL programda YOK!")
    print("\nBenzer isimler:")
    for name in horse_names:
        if 'MO' in name.upper() or 'OG' in name.upper():
            print(f"  - {name}")
