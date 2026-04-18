import json

data = json.load(open('E:/data/program/Antalya/2026/01.json', encoding='utf-8'))
first_date = list(data.keys())[0]
print(f'First date: {first_date}')

races = data[first_date].get('races', [])
print(f'Races: {len(races)}')

if races:
    print(f'First race keys: {list(races[0].keys())}')
    horses = races[0].get('horses', [])
    print(f'Horses in first race: {len(horses)}')
    if horses:
        print(f'First horse: {horses[0].get("horse_name")}')
        print(f'Horse keys: {list(horses[0].keys())}')
