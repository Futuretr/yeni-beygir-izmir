from group_wins_by_category import load_idman_for_horse, get_last_idman_before_race
from datetime import datetime

# Test: ISO format tarih
idman = load_idman_for_horse(100453)
print(f'Horse 100453 idman records: {len(idman)}')

if idman:
    print(f'\nFirst idman keys: {list(idman[0].keys())[:10]}')
    print(f'First idman date field: {idman[0].get("İ. Tarihi")} or {idman[0].get("Ä°. Tarihi")}')
    
    # Manuel test
    race_date = datetime.fromisoformat('2024-01-27T00:00:00Z'.replace('Z', '+00:00'))
    print(f'\nRace date parsed: {race_date}')
    
    for i, rec in enumerate(idman[:3]):
        date_str = rec.get('İ. Tarihi') or rec.get('Ä°. Tarihi')
        print(f'Idman {i}: date_str = {date_str}')
        if date_str:
            try:
                idman_date = datetime.strptime(date_str, "%d.%m.%Y")
                print(f'  Parsed: {idman_date}, Before race: {idman_date < race_date}')
            except Exception as e:
                print(f'  Parse error: {e}')
    
    # ISO format tarih testi
    result = get_last_idman_before_race(idman, '2024-01-27T00:00:00Z')
    if result:
        print(f'\nLast idman before 2024-01-27: {result.get("İ. Tarihi") or result.get("Ä°. Tarihi")}')
    else:
        print('\nNo idman found')
