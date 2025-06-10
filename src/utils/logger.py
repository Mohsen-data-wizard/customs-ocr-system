#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
سیستم لاگینگ برنامه
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger():
    """راه‌اندازی سیستم لاگینگ"""
    
    # ایجاد پوشه لاگ
    log_dir = Path("output/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # نام فایل لاگ با تاریخ
    log_file = log_dir / f"customs_ocr_{datetime.now().strftime('%Y%m%d')}.log"
    
    # تنظیم فرمت لاگ
    log_format = "[%(asctime)s] %(levelname)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # تنظیم لاگر اصلی
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # حذف لاگ‌های قدیمی (بیش از 7 روز)
    cleanup_old_logs(log_dir)

def cleanup_old_logs(log_dir: Path, days: int = 7):
    """حذف فایل‌های لاگ قدیمی"""
    try:
        cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
        
        for log_file in log_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                logging.info(f"🗑️ فایل لاگ قدیمی حذف شد: {log_file.name}")
                
    except Exception as e:
        logging.warning(f"⚠️ خطا در حذف لاگ‌های قدیمی: {e}")

def get_logger(name: str = __name__):
    """دریافت لاگر با نام مشخص"""
    return logging.getLogger(name)
