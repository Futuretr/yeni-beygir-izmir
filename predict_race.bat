@echo off
chcp 65001 > nul
echo ════════════════════════════════════════════════════════════════════════
echo 🎯 AT YARIŞI TAHMİNİ
echo ════════════════════════════════════════════════════════════════════════
echo.
echo Bu script yeni yarışlar için tahmin yapar.
echo.
echo ⚠️  Önce modeli eğitmiş olmalısınız!
echo    (run_ml_system.bat çalıştırın)
echo.
pause

cd /d C:\Users\emir\Desktop\HorseRacingAPI-master

echo.
echo ▶️  Python ortamı aktifleştiriliyor...
call .venv\Scripts\activate.bat

echo.
echo ════════════════════════════════════════════════════════════════════════
echo ▶️  Tahmin yapılıyor...
echo ════════════════════════════════════════════════════════════════════════
python E:\data\ml\predict_race.py

echo.
echo ════════════════════════════════════════════════════════════════════════
echo ✅ TAHMİN TAMAMLANDI
echo ════════════════════════════════════════════════════════════════════════
echo.
echo 💡 Farklı yarış için tahmin yapmak için:
echo    E:\data\ml\predict_race.py dosyasını düzenleyin
echo    (Satır 158-163: city, year, month, day, race_number)
echo.
pause
