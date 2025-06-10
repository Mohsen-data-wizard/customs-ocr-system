import json
import os
from pathlib import Path
import logging
from typing import Any, Dict, Optional, Union


class ConfigManager:
    """مدیریت تنظیمات برنامه"""

    _instance = None  # Singleton pattern

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._init_config()
        return cls._instance

    def _init_config(self):
        """مقداردهی اولیه تنظیمات"""
        self.config_path = Path("config/app_config.json")
        self.config_dir = self.config_path.parent

        # تنظیمات پیش‌فرض
        self.default_config = {
            "app": {
                "name": "سامانه استخراج اطلاعات اسناد گمرکی",
                "version": "1.0.0",
                "author": "Mohsen-data-wizard",
                "debug": True
            },
            "ocr": {
                "easyocr": {
                    "languages": ["fa", "en"],
                    "gpu": True,
                    "model_storage_directory": "models",
                    "download_enabled": True
                },
                "tesseract": {
                    "path": "",  # پر شدن خودکار
                    "languages": ["fas", "eng"]
                }
            },
            "processing": {
                "default_dpi": 350,
                "max_workers": 2,
                "timeout": 600,
                "save_temp_files": False,
                "temp_dir": "temp"
            },
            "paths": {
                "output_dir": "output",
                "log_dir": "logs",
                "templates_dir": "templates"
            },
            "patterns": {
                "import": "patterns/import_patterns.json",
                "export": "patterns/export_patterns.json"
            }
        }

        self.config = {}
        self._load_config()

    def _load_config(self):
        """بارگذاری تنظیمات از فایل"""
        try:
            if not self.config_dir.exists():
                self.config_dir.mkdir(parents=True, exist_ok=True)

            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                    logging.info(f"تنظیمات از مسیر {self.config_path} بارگذاری شد")
            else:
                # ذخیره پیکربندی پیش‌فرض
                self.config = self.default_config
                self._save_config()
                logging.info("فایل تنظیمات پیش‌فرض ایجاد شد")

            # تشخیص مسیر Tesseract
            self._detect_tesseract_path()

        except Exception as e:
            logging.error(f"خطا در بارگذاری تنظیمات: {str(e)}")
            self.config = self.default_config

    def _save_config(self):
        """ذخیره تنظیمات در فایل"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            logging.info(f"تنظیمات در مسیر {self.config_path} ذخیره شد")
        except Exception as e:
            logging.error(f"خطا در ذخیره تنظیمات: {str(e)}")

    def _detect_tesseract_path(self):
        """تشخیص خودکار مسیر نصب Tesseract"""
        if self.config["ocr"]["tesseract"]["path"]:
            return

        # مسیرهای پیش‌فرض بر اساس سیستم‌عامل
        possible_paths = []

        if os.name == 'nt':  # Windows
            possible_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
            ]
        else:  # Linux/Mac
            possible_paths = [
                "/usr/bin/tesseract",
                "/usr/local/bin/tesseract"
            ]

        for path in possible_paths:
            if os.path.exists(path):
                self.config["ocr"]["tesseract"]["path"] = path
                self._save_config()
                logging.info(f"مسیر Tesseract به صورت خودکار شناسایی شد: {path}")
                break

    def get(self, key_path: str, default: Any = None) -> Any:
        """دریافت مقدار از تنظیمات

        Args:
            key_path: مسیر کلید با جداکننده نقطه مثل app.name
            default: مقدار پیش‌فرض در صورت پیدا نشدن کلید
        """
        keys = key_path.split('.')
        result = self.config

        try:
            for key in keys:
                result = result[key]
            return result
        except (KeyError, TypeError):
            return default

    def set(self, key_path: str, value: Any) -> None:
        """تنظیم مقدار در پیکربندی

        Args:
            key_path: مسیر کلید با جداکننده نقطه مثل app.name
            value: مقداری که باید تنظیم شود
        """
        keys = key_path.split('.')
        config = self.config

        # رسیدن به آخرین سطح کلید
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # تنظیم مقدار
        config[keys[-1]] = value
        self._save_config()

    def get_all(self) -> Dict:
        """دریافت کل تنظیمات"""
        return self.config