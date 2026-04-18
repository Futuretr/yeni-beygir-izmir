import json

# Yarış 1 - 222824.json
with open('E:/data/race_jsons/Izmir/2026/222824.json', encoding='utf-8') as f:
    data = json.load(f)[0]

print("="*80)
print(f"YARIŞ 1 - {data['race_category']}")
print(f"Tarih: {data['race_date']} - Yarış No: {data['race_number']}")
print("="*80)

print("\nAtlar:")
for i, horse in enumerate(data['horses'], 1):
    print(f"{i}. {horse['horse_name']:<30} (Start: {horse.get('start_no', '?')})")

print(f"\nToplam: {len(data['horses'])} at")

# Gerçek kazanan
print("\n" + "="*80)
print("GERÇEK KAZANAN: KUZEYİN KRALI")
print("="*80)

# At var mı kontrol
horse_names = [h['horse_name'] for h in data['horses']]
if 'KUZEYİN KRALI' in horse_names:
    print("✓ KUZEYİN KRALI programda VAR")
else:
    print("✗ KUZEYİN KRALI programda YOK!")
