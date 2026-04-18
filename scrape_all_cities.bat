@echo off
echo ================================================================================
echo TÜM ŞEHİRLER İÇİN TIME VE FARK ÇEKME (100 WORKER)
echo ================================================================================
echo.

set PYTHON=C:\Users\emir\Desktop\HorseRacingAPI-master\.venv\Scripts\python.exe
set SCRIPT=C:\Users\emir\Desktop\HorseRacingAPI-master\scrape_time_fark_only.py

echo 1/9 - Istanbul...
"%PYTHON%" "%SCRIPT%" Istanbul
if errorlevel 1 echo [HATA] Istanbul

echo.
echo 2/9 - Ankara...
"%PYTHON%" "%SCRIPT%" Ankara
if errorlevel 1 echo [HATA] Ankara

echo.
echo 3/9 - Izmir...
"%PYTHON%" "%SCRIPT%" Izmir
if errorlevel 1 echo [HATA] Izmir

echo.
echo 4/9 - Bursa...
"%PYTHON%" "%SCRIPT%" Bursa
if errorlevel 1 echo [HATA] Bursa

echo.
echo 5/9 - Adana...
"%PYTHON%" "%SCRIPT%" Adana
if errorlevel 1 echo [HATA] Adana

echo.
echo 6/9 - Antalya...
"%PYTHON%" "%SCRIPT%" Antalya
if errorlevel 1 echo [HATA] Antalya

echo.
echo 7/9 - Kocaeli...
"%PYTHON%" "%SCRIPT%" Kocaeli
if errorlevel 1 echo [HATA] Kocaeli

echo.
echo 8/9 - Elazig...
"%PYTHON%" "%SCRIPT%" Elazig
if errorlevel 1 echo [HATA] Elazig

echo.
echo 9/9 - Urfa...
"%PYTHON%" "%SCRIPT%" Urfa
if errorlevel 1 echo [HATA] Urfa

echo.
echo ================================================================================
echo TÜMÜ TAMAMLANDI!
echo ================================================================================
pause
