import json
import os
import shutil
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
        # تشخیص مسیر اصلی پروژه (یک سطح بالاتر از src)
        self.project_root = Path(__file__).parent.parent.parent
        self.config_path = self.project_root / "config" / "app_config.json"
        self.config_dir = self.config_path.parent

        # تنظیمات پیش‌فرض
        self.default_config = {
            "app": {
                "name": "سامانه استخراج اطلاعات اسناد گمرکی",
                "version": "2.0.0",
                "author": "Mohsen-data-wizard",
                "debug": True,
                "language": "fa"
            },
            "ocr": {
                "easyocr": {
                    "languages": ["fa", "en", "ar"],
                    "gpu": True,
                    "model_storage_directory": str(self.project_root / "models"),
                    "download_enabled": True,
                    "recog_network": "standard",
                    "detector": True,
                    "recognizer": True,
                    "allowlist": None,
                    "blocklist": None
                },
                "tesseract": {
                    "path": "",  # پر شدن خودکار
                    "languages": ["fas", "eng", "ara"],
                    "config": "--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzآابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی",
                    "timeout": 30
                }
            },
            "processing": {
                "default_dpi": 350,
                "max_workers": 2,
                "timeout": 600,
                "save_temp_files": False,
                "temp_dir": str(self.project_root / "data" / "temp"),
                "supported_formats": [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"],
                "image_preprocessing": {
                    "denoise": True,
                    "enhance_contrast": True,
                    "sharpen": False,
                    "threshold": True
                }
            },
            "paths": {
                "project_root": str(self.project_root),
                "output_dir": str(self.project_root / "output"),
                "log_dir": str(self.project_root / "output" / "logs"),
                "data_dir": str(self.project_root / "data"),
                "input_dir": str(self.project_root / "data" / "input"),
                "temp_dir": str(self.project_root / "data" / "temp"),
                "excel_dir": str(self.project_root / "output" / "excel"),
                "debug_dir": str(self.project_root / "output" / "debug"),
                "templates_dir": str(self.project_root / "templates"),
                "assets_dir": str(self.project_root / "assets")
            },
            "patterns": {
                "import_patterns_file": "patterns/import_patterns.json",
                "export_patterns_file": "patterns/export_patterns.json",
                "confidence_threshold": 0.3,
                "voting_enabled": True,
                "pattern_weights": {
                    "position_based": 0.4,
                    "keyword_based": 0.3,
                    "format_based": 0.3
                }
            },
            "gui": {
                "theme": "clam",
                "window_size": "1800x1100",
                "font_family": "Tahoma",
                "font_size": 10,
                "rtl_support": True,
                "auto_save_results": True,
                "show_debug_info": False
            },
            "export": {
                "excel": {
                    "auto_format": True,
                    "include_metadata": True,
                    "sheet_name": "داده‌های استخراج شده",
                    "freeze_header": True
                },
                "csv": {
                    "encoding": "utf-8-sig",
                    "delimiter": ","
                }
            }
        }

        self.config = {}
        self._load_config()

    def _load_config(self):
        """بارگذاری تنظیمات از فایل"""
        try:
            # ایجاد پوشه config در صورت عدم وجود
            if not self.config_dir.exists():
                self.config_dir.mkdir(parents=True, exist_ok=True)
                logging.info(f"📁 پوشه تنظیمات ایجاد شد: {self.config_dir}")

            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)

                # ادغام تنظیمات بارگذاری شده با تنظیمات پیش‌فرض
                self.config = self._merge_configs(self.default_config, loaded_config)

                logging.info(f"✅ تنظیمات از مسیر {self.config_path} بارگذاری شد")
            else:
                # ذخیره پیکربندی پیش‌فرض
                self.config = self.default_config.copy()
                self._save_config()
                logging.info("📝 فایل تنظیمات پیش‌فرض ایجاد شد")

            # تشخیص مسیر Tesseract
            self._detect_tesseract_path()

            # ایجاد پوشه‌های ضروری
            self._create_required_directories()

        except Exception as e:
            logging.error(f"❌ خطا در بارگذاری تنظیمات: {str(e)}")
            self.config = self.default_config.copy()

    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """ادغام تنظیمات بارگذاری شده با پیش‌فرض"""
        result = default.copy()

        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def _save_config(self):
        """ذخیره تنظیمات در فایل"""
        try:
            # ایجاد backup از تنظیمات فعلی
            if self.config_path.exists():
                backup_path = self.config_path.with_suffix('.json.backup')
                shutil.copy2(self.config_path, backup_path)

            # ذخیره تنظیمات جدید
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)

            logging.info(f"💾 تنظیمات در مسیر {self.config_path} ذخیره شد")

        except Exception as e:
            logging.error(f"❌ خطا در ذخیره تنظیمات: {str(e)}")

    def _detect_tesseract_path(self):
        """تشخیص خودکار مسیر نصب Tesseract"""
        current_path = self.get('ocr.tesseract.path', '')

        # اگر مسیر از قبل تنظیم شده و معتبر است
        if current_path and Path(current_path).exists():
            return

        # تلاش برای یافتن tesseract در PATH
        tesseract_cmd = shutil.which('tesseract')
        if tesseract_cmd:
            self.set('ocr.tesseract.path', tesseract_cmd)
            logging.info(f"🔍 Tesseract در PATH یافت شد: {tesseract_cmd}")
            return

        # مسیرهای پیش‌فرض بر اساس سیستم‌عامل
        possible_paths = []

        if os.name == 'nt':  # Windows
            possible_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                r"C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe".format(os.getenv('USERNAME', '')),
                r"D:\Program Files\Tesseract-OCR\tesseract.exe"
            ]
        else:  # Linux/Mac
            possible_paths = [
                "/usr/bin/tesseract",
                "/usr/local/bin/tesseract",
                "/opt/homebrew/bin/tesseract",  # Mac M1
                "/snap/bin/tesseract"  # Ubuntu Snap
            ]

        for path in possible_paths:
            if os.path.exists(path):
                self.set('ocr.tesseract.path', path)
                logging.info(f"🎯 مسیر Tesseract شناسایی شد: {path}")
                return

        logging.warning("⚠️ Tesseract یافت نشد. لطفاً آن را نصب کنید یا مسیر را دستی تنظیم کنید.")

    def _create_required_directories(self):
        """ایجاد پوشه‌های ضروری"""
        required_dirs = [
            self.get('paths.output_dir'),
            self.get('paths.log_dir'),
            self.get('paths.data_dir'),
            self.get('paths.input_dir'),
            self.get('paths.temp_dir'),
            self.get('paths.excel_dir'),
            self.get('paths.debug_dir'),
            self.get('ocr.easyocr.model_storage_directory')
        ]

        for dir_path in required_dirs:
            if dir_path:
                Path(dir_path).mkdir(parents=True, exist_ok=True)

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
            logging.debug(f"کلید '{key_path}' یافت نشد، مقدار پیش‌فرض بازگردانده شد: {default}")
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
        logging.debug(f"تنظیم '{key_path}' به '{value}' تغییر یافت")

    def get_all(self) -> Dict:
        """دریافت کل تنظیمات"""
        return self.config.copy()

    def reset_to_default(self) -> None:
        """بازگردانی تنظیمات به حالت پیش‌فرض"""
        try:
            self.config = self.default_config.copy()
            self._save_config()
            logging.info("🔄 تنظیمات به حالت پیش‌فرض بازگردانده شد")
        except Exception as e:
            logging.error(f"❌ خطا در بازگردانی تنظیمات: {e}")

    def validate_config(self) -> bool:
        """اعتبارسنجی تنظیمات"""
        try:
            # بررسی وجود کلیدهای ضروری
            required_keys = [
                'app.name',
                'app.version',
                'ocr.easyocr.languages',
                'processing.default_dpi',
                'paths.output_dir'
            ]

            for key in required_keys:
                if self.get(key) is None:
                    logging.error(f"❌ کلید ضروری یافت نشد: {key}")
                    return False

            # بررسی معتبر بودن مسیرها
            paths_to_check = [
                'paths.output_dir',
                'paths.log_dir',
                'ocr.easyocr.model_storage_directory'
            ]

            for path_key in paths_to_check:
                path_value = self.get(path_key)
                if path_value and not Path(path_value).exists():
                    try:
                        Path(path_value).mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        logging.error(f"❌ نمی‌توان پوشه {path_key} را ایجاد کرد: {e}")
                        return False

            # بررسی نسخه Tesseract
            tesseract_path = self.get('ocr.tesseract.path')
            if tesseract_path and not Path(tesseract_path).exists():
                logging.warning(f"⚠️ مسیر Tesseract معتبر نیست: {tesseract_path}")

            logging.info("✅ تنظیمات معتبر است")
            return True

        except Exception as e:
            logging.error(f"❌ خطا در اعتبارسنجی تنظیمات: {e}")
            return False

    def get_project_root(self) -> Path:
        """دریافت مسیر اصلی پروژه"""
        return self.project_root

    def __str__(self) -> str:
        """نمایش تنظیمات به صورت رشته"""
        return json.dumps(self.config, ensure_ascii=False, indent=2)