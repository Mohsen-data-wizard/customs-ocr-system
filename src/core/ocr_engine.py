#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
موتور OCR ساده شده - فقط EasyOCR با DPI 600
"""

import easyocr
import numpy as np
import logging
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)


class OCREngine:
    """موتور OCR ساده شده با EasyOCR"""

    def __init__(self, config=None):
        self.config = config
        logger.info("🔍 راه‌اندازی EasyOCR...")

        try:
            # ساده‌سازی: فقط فارسی و انگلیسی
            self.reader = easyocr.Reader(['fa', 'en'], gpu=True)
            logger.info("✅ EasyOCR آماده است")
        except Exception as e:
            logger.error(f"❌ خطا در راه‌اندازی EasyOCR: {e}")
            raise

    def extract_text(self, image: np.ndarray) -> Dict[str, Any]:
        """استخراج متن از تصویر - ساده شده"""
        try:
            start_time = time.time()

            # استخراج متن
            results = self.reader.readtext(image)

            # ترکیب تمام متن‌ها
            text_parts = []
            total_confidence = 0

            for (bbox, text, confidence) in results:
                if confidence > 0.5:  # حد آستانه ثابت
                    text_parts.append(text)
                    total_confidence += confidence

            full_text = ' '.join(text_parts)
            avg_confidence = total_confidence / len(results) if results else 0
            processing_time = time.time() - start_time

            result = {
                'text': full_text,
                'confidence': avg_confidence,
                'processing_time': processing_time,
                'method': 'easyocr',
                'text_length': len(full_text)
            }

            logger.info(f"✅ OCR: {len(full_text)} کاراکتر، اعتماد: {avg_confidence:.2f}")
            return result

        except Exception as e:
            logger.error(f"❌ خطا در OCR: {e}")
            return {
                'text': '',
                'confidence': 0,
                'processing_time': 0,
                'method': 'easyocr',
                'error': str(e)
            }