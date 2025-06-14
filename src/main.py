#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 سیستم ساده استخراج داده‌های گمرکی
نسخه ساده شده - حذف پیچیدگی‌ها
"""

import sys
import os
import logging
from pathlib import Path

# اضافه کردن مسیر src
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from gui.main_window import CustomsOCRApp
    from utils.logger import setup_logger
    from utils.config import ConfigManager
except ImportError as e:
    print(f"خطا در import: {e}")
    sys.exit(1)


def setup_environment():
    """راه‌اندازی محیط ساده"""
    base_dir = Path(__file__).parent.parent

    # فقط پوشه‌های ضروری
    required_dirs = [
        base_dir / "data",
        base_dir / "output"
    ]

    for dir_path in required_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)

    # لاگر ساده
    setup_logger()
    logging.info("🚀 سیستم ساده راه‌اندازی شد")


def main():
    """تابع اصلی ساده"""
    try:
        setup_environment()

        # کانفیگ ساده
        config = ConfigManager()

        # رابط گرافیکی ساده
        app = CustomsOCRApp(config)
        app.run()

    except Exception as e:
        logging.error(f"❌ خطا: {e}")
        print(f"خطا: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()