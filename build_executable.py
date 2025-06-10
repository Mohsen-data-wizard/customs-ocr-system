#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اسکریپت ساخت فایل اجرایی
"""

import subprocess
import sys
import shutil
from pathlib import Path

def install_pyinstaller():
    """نصب PyInstaller"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller نصب شد")
    except subprocess.CalledProcessError:
        print("❌ خطا در نصب PyInstaller")
        sys.exit(1)

def create_spec_file():
    """ایجاد فایل spec"""
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('assets', 'assets'),
        ('src/patterns', 'patterns'),
        ('src/utils', 'utils'),
    ],
    hiddenimports=[
        'easyocr',
        'pytesseract', 
        'cv2',
        'numpy',
        'pandas',
        'openpyxl',
        'PIL',
        'fitz',
        'yaml',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CustomsOCR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/app_icon.ico'
)
'''
    
    with open('customs_ocr.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content.strip())
    
    print("✅ فایل spec ایجاد شد")

def build_executable():
    """ساخت فایل اجرایی"""
    try:
        # ایجاد آیکون (در صورت عدم وجود)
        icon_dir = Path("assets/icons")
        icon_dir.mkdir(parents=True, exist_ok=True)
        
        # اجرای PyInstaller
        cmd = [
            "pyinstaller",
            "--onefile",
            "--windowed", 
            "--name=CustomsOCR-v2.0",
            "--icon=assets/icons/app_icon.ico",
            "--add-data=config;config",
            "--add-data=assets;assets", 
            "--distpath=dist",
            "--workpath=build",
            "--specpath=build",
            "src/main.py"
        ]
        
        print("🔨 شروع ساخت فایل اجرایی...")
        subprocess.check_call(cmd)
        
        print("✅ فایل اجرایی با موفقیت ساخته شد!")
        print("📁 مسیر: dist/CustomsOCR-v2.0.exe")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ خطا در ساخت: {e}")
        sys.exit(1)

def create_installer():
    """ایجاد نصب کننده با NSIS"""
    nsis_script = '''
!define APP_NAME "سیستم استخراج دادههای گمرکی"
!define APP_VERSION "2.0.0"
!define APP_PUBLISHER "Mohsen Data Wizard"
!define APP_EXE "CustomsOCR-v2.0.exe"

Name "${APP_NAME}"
OutFile "CustomsOCR-Installer-v2.0.exe"
InstallDir "$PROGRAMFILES\\${APP_NAME}"
RequestExecutionLevel admin

Page directory
Page instfiles

Section "Main"
    SetOutPath "$INSTDIR"
    File "dist\\${APP_EXE}"
    File /r "config"
    File /r "assets"
    
    CreateDirectory "$SMPROGRAMS\\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk" "$INSTDIR\\${APP_EXE}"
    CreateShortCut "$DESKTOP\\${APP_NAME}.lnk" "$INSTDIR\\${APP_EXE}"
    
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "UninstallString" "$INSTDIR\\uninstall.exe"
    WriteUninstaller "$INSTDIR\\uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\\${APP_EXE}"
    Delete "$INSTDIR\\uninstall.exe"
    RMDir /r "$INSTDIR"
    
    Delete "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk"
    RMDir "$SMPROGRAMS\\${APP_NAME}"
    Delete "$DESKTOP\\${APP_NAME}.lnk"
    
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}"
SectionEnd
'''
    
    with open('installer.nsi', 'w', encoding='utf-8') as f:
        f.write(nsis_script.strip())
    
    print("✅ اسکریپت NSIS ایجاد شد")
    print("ℹ️ برای ساخت installer NSIS را نصب کنید و installer.nsi را اجرا کنید")

def main():
    print("🚀 ساخت فایل اجرایی سیستم گمرکی")
    print("=" * 50)
    
    # بررسی وجود فایلهای ضروری
    required_files = [
        "src/main.py",
        "requirements.txt",
        "config/settings.yaml"
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ فایل ضروری یافت نشد: {file_path}")
            sys.exit(1)
    
    # نصب PyInstaller
    install_pyinstaller()
    
    # ساخت فایل اجرایی
    build_executable()
    
    # ایجاد نصب کننده
    create_installer()
    
    print("\n🎉 فرآیند ساخت کامل شد!")
    print("\nفایلهای ایجاد شده:")
    print("📁 dist/CustomsOCR-v2.0.exe - فایل اجرایی")
    print("📁 installer.nsi - اسکریپت نصب کننده")

if __name__ == "__main__":
    main()
