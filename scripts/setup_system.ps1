# اسکریپت راهاندازی کامل سیستم
param(
    [switch]$InstallGPU,
    [switch]$InstallTesseract,
    [switch]$CreateDesktopShortcut
)

Write-Host "🚀 راهاندازی سیستم استخراج دادههای گمرکی" -ForegroundColor Green
Write-Host "=" * 60

# بررسی Python
try {
    $pythonVersion = python --version
    Write-Host "✅ Python یافت شد: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python نصب نیست! لطفا ابتدا Python 3.8+ نصب کنید" -ForegroundColor Red
    exit 1
}

# ایجاد محیط مجازی
Write-Host "📦 ایجاد محیط مجازی..." -ForegroundColor Yellow
python -m venv venv

# فعالسازی محیط مجازی
Write-Host "🔧 فعالسازی محیط مجازی..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# بروزرسانی pip
Write-Host "⬆️ بروزرسانی pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# نصب پکیجهای پایه
Write-Host "📚 نصب وابستگیهای پایه..." -ForegroundColor Yellow
pip install -r requirements.txt

# نصب پکیجهای GPU (در صورت درخواست)
if ($InstallGPU) {
    Write-Host "🎮 نصب پشتیبانی GPU..." -ForegroundColor Cyan
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
}

# راهاندازی Tesseract (در صورت درخواست)
if ($InstallTesseract) {
    Write-Host "📝 دانلود Tesseract..." -ForegroundColor Cyan
    $tesseractUrl = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.0.20221214/tesseract-ocr-w64-setup-5.3.0.20221214.exe"
    $tesseractInstaller = "tesseract-installer.exe"
    
    Invoke-WebRequest -Uri $tesseractUrl -OutFile $tesseractInstaller
    
    Write-Host "📝 نصب Tesseract..." -ForegroundColor Cyan
    Start-Process -FilePath $tesseractInstaller -ArgumentList "/S" -Wait
    
    # اضافه کردن به PATH
    $tesseractPath = "C:\Program Files\Tesseract-OCR"
    if (Test-Path $tesseractPath) {
        $env:PATH += ";$tesseractPath"
        [Environment]::SetEnvironmentVariable("PATH", $env:PATH, [EnvironmentVariableTarget]::User)
        Write-Host "✅ Tesseract نصب شد" -ForegroundColor Green
    }
    
    Remove-Item $tesseractInstaller -Force
}

# ایجاد پوشههای ضروری
Write-Host "📁 ایجاد ساختار پوشهها..." -ForegroundColor Yellow
$directories = @(
    "data\input",
    "data\temp", 
    "output\excel",
    "output\logs",
    "output\debug",
    "assets\icons",
    "assets\fonts"
)

foreach ($dir in $directories) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}

# کپی فایلهای نمونه
Write-Host "📄 کپی فایلهای پیکربندی..." -ForegroundColor Yellow
if (!(Test-Path "config\settings.yaml")) {
    Copy-Item "config\settings.yaml.example" "config\settings.yaml" -ErrorAction SilentlyContinue
}

# ایجاد shortcut روی دسکتاپ
if ($CreateDesktopShortcut) {
    Write-Host "🔗 ایجاد shortcut روی دسکتاپ..." -ForegroundColor Cyan
    
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\سیستم گمرکی.lnk")
    $Shortcut.TargetPath = "python"
    $Shortcut.Arguments = "src\main.py"
    $Shortcut.WorkingDirectory = (Get-Location).Path
    $Shortcut.IconLocation = "assets\icons\app_icon.ico"
    $Shortcut.Description = "سیستم هوشمند استخراج دادههای گمرکی"
    $Shortcut.Save()
}

# تست اولیه
Write-Host "🧪 تست اولیه سیستم..." -ForegroundColor Yellow
try {
    python -c "
import sys
sys.path.insert(0, 'src')
from utils.config import ConfigManager
from patterns.regex_patterns import PatternManager

config = ConfigManager()
patterns = PatternManager()

print('✅ تمام ماولها بارگذاری شدند')
print(f'📊 تعداد الگوهای وارداتی: {len(patterns.import_patterns)}')
print(f'📊 تعداد الگوهای صادراتی: {len(patterns.export_patterns)}')
"
    Write-Host "✅ تست اولیه موفق بود!" -ForegroundColor Green
} catch {
    Write-Host "❌ خطا در تست اولیه: $_" -ForegroundColor Red
}

# نمایش راهنمای استفاده
Write-Host "`n📋 راهنمای استفاده:" -ForegroundColor Cyan
Write-Host "1️⃣ اجرای برنامه: python src\main.py" -ForegroundColor White
Write-Host "2️⃣ ساخت فایل اجرایی: python build_executable.py" -ForegroundColor White
Write-Host "3️⃣ مسیر لاگها: output\logs\" -ForegroundColor White
Write-Host "4️⃣ مسیر خروجی: output\excel\" -ForegroundColor White

Write-Host "`n🎉 راهاندازی کامل شد!" -ForegroundColor Green
Write-Host "برای اجرای برنامه دستور زیر را وارد کنید:" -ForegroundColor Yellow
Write-Host "python src\main.py" -ForegroundColor White

# پاکسازی
Write-Host "`n🧹 پاکسازی فایلهای موقت..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Name "__pycache__" -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Recurse -Name "*.pyc" -File | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host "✨ تمام!" -ForegroundColor Green
