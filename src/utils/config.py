#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
مدیریت تنظیمات برنامه
"""

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
        return json.dumps(self.config, ensure_ascii=False, indent=2)
