#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
پیش‌پردازشگر پیشرفته متن برای OCR بهتر
"""

import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class AdvancedTextPreprocessor:
    """پیش‌پردازشگر پیشرفته متن"""

    def __init__(self):
        # نقشه تبدیل اعداد
        self.digit_map = {
            # اعداد فارسی
            '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
            '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
            # اعداد عربی
            '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
            '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
        }

        # نقشه تصحیح کاراکترها
        self.char_corrections = {
            'ك': 'ک', 'ي': 'ی', 'ء': 'ئ',
            'أ': 'ا', 'إ': 'ا', 'آ': 'ا',
            'ة': 'ه', 'ى': 'ی'
        }

        logger.info("✅ پیش‌پردازشگر پیشرفته آماده شد")

    def normalize_digits(self, text: str) -> str:
        """تبدیل تمام اعداد به انگلیسی"""
        for persian, english in self.digit_map.items():
            text = text.replace(persian, english)
        return text

    def fix_characters(self, text: str) -> str:
        """تصحیح کاراکترهای مشکل‌دار"""
        for wrong, correct in self.char_corrections.items():
            text = text.replace(wrong, correct)
        return text

    def segment_text(self, text: str) -> List[str]:
        """تقسیم متن به خطوط منطقی"""
        try:
            # الگوهای تقسیم‌بندی
            field_markers = [
                r'(\d{1,2}\.\s*[آ-ی\s]{5,50})',  # فیلدهای شماره‌دار
                r'(کد\s*[آ-ی\s]*\s*:)',  # فیلدهای کد
                r'(شماره\s*[آ-ی\s]*\s*:)',  # فیلدهای شماره
                r'(مبلغ\s*[آ-ی\s]*\s*:)',  # فیلدهای مبلغ
                r'(تاریخ\s*[آ-ی\s]*\s*:)'  # فیلدهای تاریخ
            ]

            # تقسیم بر اساس نشانه‌گرها
            lines = []
            current_pos = 0

            for pattern in field_markers:
                matches = list(re.finditer(pattern, text))
                for match in matches:
                    start, end = match.span()
                    if start > current_pos:
                        segment = text[current_pos:start].strip()
                        if len(segment) > 10:
                            lines.append(segment)
                    current_pos = start

            # اضافه کردن بقیه متن
            if current_pos < len(text):
                remaining = text[current_pos:].strip()
                if len(remaining) > 10:
                    lines.append(remaining)

            # اگر تقسیم‌بندی موفق نبود، کل متن را برگردان
            if not lines:
                lines = [text]

            logger.debug(f"📝 متن به {len(lines)} خط تقسیم شد")
            return lines

        except Exception as e:
            logger.error(f"❌ خطا در تقسیم‌بندی متن: {e}")
            return [text]

    def extract_structure(self, lines: List[str]) -> Dict:
        """استخراج ساختار منطقی متن"""
        structure = {
            "header": [],
            "body": [],
            "numbers": [],
            "dates": [],
            "amounts": []
        }

        try:
            for i, line in enumerate(lines):
                line_info = {
                    "line_number": i + 1,
                    "text": line
                }

                # شناسایی اعداد
                numbers = re.findall(r'\d+(?:\.\d+)?', line)
                if numbers:
                    line_info["numbers"] = numbers
                    structure["numbers"].append(line_info)

                # شناسایی تاریخ‌ها
                date_patterns = [
                    r'\d{4}/\d{1,2}/\d{1,2}',
                    r'\d{1,2}/\d{1,2}/\d{4}',
                    r'\d{4}-\d{1,2}-\d{1,2}'
                ]
                for pattern in date_patterns:
                    if re.search(pattern, line):
                        structure["dates"].append(line_info)
                        break

                # شناسایی مبالغ
                amount_patterns = [
                    r'\d+[\d,]*\s*ریال',
                    r'\d+[\d,]*\s*(EUR|USD|GBP)',
                    r'\d+[\d,]*\.\d{2}'
                ]
                for pattern in amount_patterns:
                    if re.search(pattern, line):
                        structure["amounts"].append(line_info)
                        break

                # تقسیم‌بندی header/body
                if i < len(lines) // 3:
                    structure["header"].append(line_info)
                else:
                    structure["body"].append(line_info)

            return structure

        except Exception as e:
            logger.error(f"❌ خطا در استخراج ساختار: {e}")
            return structure

    def preprocess(self, raw_text: str) -> Dict:
        """پیش‌پردازش کامل متن"""
        try:
            logger.info("🔄 شروع پیش‌پردازش پیشرفته...")

            # مرحله 1: نرمال‌سازی اولیه
            text = self.normalize_digits(raw_text)
            text = self.fix_characters(text)

            # مرحله 2: پاکسازی
            text = re.sub(r'[\u200c\u200d\ufeff\u200e\u200f]', '', text)  # کاراکترهای کنترلی
            text = re.sub(r'\s+', ' ', text)  # فاصله‌های اضافی

            # مرحله 3: تقسیم‌بندی
            lines = self.segment_text(text)

            # مرحله 4: استخراج ساختار
            structure = self.extract_structure(lines)

            # مرحله 5: شناسایی الگوها
            patterns = self.identify_patterns(text)

            result = {
                "original_text": raw_text,
                "normalized_text": text,
                "text_lines": lines,
                "structure": structure,
                "patterns": patterns,
                "preprocessing_stats": {
                    "original_length": len(raw_text),
                    "normalized_length": len(text),
                    "line_count": len(lines),
                    "digit_conversions": sum(1 for c in raw_text if c in self.digit_map),
                    "char_corrections": sum(1 for c in raw_text if c in self.char_corrections)
                }
            }

            logger.info(f"✅ پیش‌پردازش کامل - {len(lines)} خط، {len(text)} کاراکتر")
            return result

        except Exception as e:
            logger.error(f"❌ خطا در پیش‌پردازش: {e}")
            return {"error": str(e), "original_text": raw_text}

    def identify_patterns(self, text: str) -> Dict:
        """شناسایی الگوهای موجود در متن"""
        patterns = {
            "phone_numbers": re.findall(r'\b\d{4}-\d{4}\b|\b\d{11}\b', text),
            "emails": re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text),
            "urls": re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                               text),
            "persian_text": re.findall(r'[آ-ی]+', text),
            "english_text": re.findall(r'[A-Za-z]+', text),
        }
        return patterns