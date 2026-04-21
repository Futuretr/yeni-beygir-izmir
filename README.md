# At Yaris Listesi

Bu depo iki parcayi bir arada tutar:

- GitHub Pages uzerinden yayinlanan gunluk yaris sayfalari ve birlesik CSV ciktilari
- TJK verisi cekmek icin kullanilan Python tabanli scraper/API araclari

## Yayin Sayfalari

- Ana secim sayfasi: `index.html`
- Ornek yayin sayfalari: `izmir_yayin.html`, `adana_yayin.html`, `sanliurfa_20_04_2026.html`

## Veri ve Zenginlestirme

- Analiz CSV birlestirme araci: `enrich_and_upload_analysis_csv.py`
- Bu arac artik Yenibeygir direkt stil sayfalarindan da veri cekebilir.

Elazig 21 Nisan 2026 icin uretilen ciktilar:

- `outputs/elazig_analiz_enriched.csv`
- `outputs/elazig_style_report.json`

## API Notu

Temel scraper/API altyapisi TJK yaris gunu verilerini cekmek icin korunmustur. Lokal calistirmak icin:

```bash
pip install -r requirements.txt
python manage.py runserver
```
