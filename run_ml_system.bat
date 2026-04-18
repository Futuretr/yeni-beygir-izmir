@echo off
chcp 65001 > nul
echo ════════════════════════════════════════════════════════════════════════
echo 🏇 AT YARIŞI XGBOOST RANKING SİSTEMİ
echo ════════════════════════════════════════════════════════════════════════
echo.
echo Bu script tüm süreci otomatik çalıştırır:
echo   1️⃣  Veri hazırlama
echo   2️⃣  Model eğitimi
echo   3️⃣  Test değerlendirmesi
echo.
echo Klasörler:
echo   📁 Sonuçlar: E:\data\sonuclar
echo   📁 Program:  E:\data\program
echo   📁 İdman:    E:\data\idman
echo   📁 Çıktı:    E:\data\ml
echo.
pause

cd /d C:\Users\emir\Desktop\HorseRacingAPI-master

echo.
echo ════════════════════════════════════════════════════════════════════════
echo ▶️  Python ortamı aktifleştiriliyor...
echo ════════════════════════════════════════════════════════════════════════
call .venv\Scripts\activate.bat

echo.
echo ════════════════════════════════════════════════════════════════════════
echo ▶️  Ana script çalıştırılıyor...
echo ════════════════════════════════════════════════════════════════════════
python E:\data\ml\run_all.py

echo.
echo ════════════════════════════════════════════════════════════════════════
echo ✅ İŞLEM TAMAMLANDI
echo ════════════════════════════════════════════════════════════════════════
echo.
echo 📊 Sonuçları görmek için:
echo    E:\data\ml klasörünü kontrol edin
echo.
pause
