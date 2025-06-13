#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
پیش‌پردازشگر پیشرفته متن
"""

import re
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class AdvancedTextPreprocessor:
    """پیش‌پردازشگر پیشرفته متن"""

    def __init__(self):
        # نقشه تبدیل اعداد
        self.digit_map = {
            '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
            '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
            '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
            '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
        }

        logger.info("✅ پیش‌پردازشگر پیشرفته آماده شد")

    def normalize_digits(self, text: str) -> str:
        """تبدیل تمام اعداد به انگلیسی"""
        for persian, english in self.digit_map.items():
            text = text.replace(persian, english)
        return text

    def preprocess(self, raw_text: str) -> Dict:
        """پیش‌پردازش کامل متن"""
        try:
            text = self.normalize_digits(raw_text)
            return {
                "normalized_text": text,
                "preprocessing_stats": {
                    "original_length": len(raw_text),
                    "normalized_length": len(text)
                }
            }
        except Exception as e:
            logger.error(f"❌ خطا در پیش‌پردازش: {e}")
            return {"error": str(e), "original_text": raw_text}