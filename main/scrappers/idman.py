"""
İdman İstatistikleri Scraper
TJK'dan at idman bilgilerini çeker
"""
from bs4 import BeautifulSoup
import urllib.request
import urllib.parse
import time
from main.exception import PageDoesNotExist


class IdmanScrapper:
    """At idman istatistiklerini çeken scraper"""
    
    BASE_URL = "https://www.tjk.org/TR/YarisSever/Query/Page/IdmanIstatistikleri?QueryParameter_AtId={horse_id}"
    AJAX_URL = "https://www.tjk.org/TR/YarisSever/Query/DataRows/IdmanIstatistikleri"
    
    @classmethod
    def scrap_by_horse_id(cls, horse_id, max_pages=1):
        """
        Tek bir atın TÜM idman bilgilerini çek (ana sayfadan)
        
        Args:
            horse_id: At ID (int)
            max_pages: Kullanılmıyor (geriye uyumluluk için)
            
        Returns:
            dict: İdman verileri
        """
        all_records = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'tr-TR,tr;q=0.9'
        }
        
        try:
            # Ana sayfayı çek
            url = cls.BASE_URL.format(horse_id=horse_id)
            
            req = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(req, timeout=15)
            html = response.read().decode('utf-8')
            
            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Tbody içindeki satırları bul
            tbody = soup.find('tbody', {'id': 'tbody0'})
            
            if not tbody:
                # Tbody bulunamadı
                return {
                    'horse_id': horse_id,
                    'idman_count': 0,
                    'pages_scraped': 0,
                    'idman_records': [],
                    'url': url
                }
            
            # Tüm TR satırlarını al
            rows = tbody.find_all('tr')
            
            # Her satırı parse et
            for row in rows:
                # class="hidable" olan satırı atla (footer)
                if 'hidable' in row.get('class', []):
                    continue
                
                cells = row.find_all('td')
                if len(cells) >= 19:  # En az 19 hücre olmalı
                    # Hücre değerlerini al
                    row_data = {
                        'horse_id': horse_id,
                        'At Adı': cells[0].get_text(strip=True),
                        'Irk': cells[1].get_text(strip=True),
                        'Cins.': cells[2].get_text(strip=True),
                        'Yaş': cells[3].get_text(strip=True),
                        '1400m': cells[4].get_text(strip=True),
                        '1200m': cells[5].get_text(strip=True),
                        '1000m': cells[6].get_text(strip=True),
                        '800m': cells[7].get_text(strip=True),
                        '600m': cells[8].get_text(strip=True),
                        '400m': cells[9].get_text(strip=True),
                        '200m': cells[10].get_text(strip=True),
                        'Durum': cells[11].get_text(strip=True),
                        'İ. Tarihi': cells[12].get_text(strip=True),
                        'İ. Hip.': cells[13].get_text(strip=True),
                        'P.Dur': cells[14].get_text(strip=True),
                        'Pist': cells[15].get_text(strip=True),
                        'İ. Türü': cells[16].get_text(strip=True),
                        'İ. Jokeyi': cells[17].get_text(strip=True),
                        'Detay': cells[18].get_text(strip=True)
                    }
                    all_records.append(row_data)
                
                    all_records.append(row_data)
            
            return {
                'horse_id': horse_id,
                'idman_count': len(all_records),
                'pages_scraped': 1,
                'idman_records': all_records,
                'url': url
            }
                
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise PageDoesNotExist(f"İdman sayfası bulunamadı: {horse_id}")
            else:
                raise Exception(f"HTTP Error {e.code}: {str(e)}")
        except Exception as e:
            raise Exception(f"Scraping Error: {str(e)}")
