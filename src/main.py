#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 سیستم هوشمند استخراج داده‌های گمرکی
نقطه ورود اصلی برنامه

Author: Mohsen Data Wizard
Date: 2025-06-09
Version: 2.0.0
"""

import sys
import os
import logging
from pathlib import Path

# اضافه کردن مسیر src به Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from gui.main_window import CustomsOCRApp
from utils.logger import setup_logger
from utils.config import ConfigManager

def setup_environment():
    """راه‌اندازی محیط برنامه"""
    # ایجاد پوشه‌های ضروری
    required_dirs = [
        "data/input",
        "data/temp", 
        "output/excel",
        "output/logs",
        "output/debug"
    ]
    
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # راه‌اندازی لاگر
    setup_logger()
    
    logging.info("🚀 راه‌اندازی سیستم استخراج داده‌های گمرکی")
    logging.info(f"📍 مسیر اجرا: {current_dir}")

def main():
    """تابع اصلی برنامه"""
    try:
        # راه‌اندازی محیط
        setup_environment()
        
        # بارگذاری تنظیمات
        config = ConfigManager()
        
        # راه‌اندازی رابط گرافیکی
        app = CustomsOCRApp(config)
        app.run()
        
    except Exception as e:
        logging.error(f"❌ خطا در راه‌اندازی برنامه: {e}")
        print(f"خطا در اجرای برنامه: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
