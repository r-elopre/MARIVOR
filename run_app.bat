@echo off
echo 🇵🇭 Starting Marivor Flask Application...
echo =======================================

cd /d "c:\Users\ri\OneDrive\Marivor"
call venv\Scripts\activate.bat
echo ✅ Virtual environment activated
echo 🚀 Starting Flask app...
python app.py

pause