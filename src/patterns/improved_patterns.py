#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
الگوهای بهبود یافته Regex برای استخراج دقیق‌تر
"""

import re
from typing import Dict, List, Any


class ImprovedRegexPatterns:
    """الگوهای بهبود یافته"""

    def __init__(self):
        self.patterns = {
            # شماره کوتاژ - الگوهای مختلف با اولویت
            "شماره_کوتاژ": [
                r"کوتاژ[اه]?\s*:?\s*(\d{8})",  # اولویت 1
                r"quotation\s*:?\s*(\d{8})",  # اولویت 2
                r"(\d{8})\s*(?:کوتاژ|quotation)",  # اولویت 3
                r"کد\s*کمرک.*?(\d{8})",  # اولویت 4
                r"شماره.*کوتاژ.*?(\d{8})"  # اولویت 5
            ],

            # مبلغ کل فاکتور - با شناسایی ارز
            "مبلغ_کل_فاکتور": [
                r"مبلغ\s*کل\s*فاکتور?\s*:?\s*([\d,\.]+)\s*(EUR|USD|ریال)?",
                r"حواله\s*ارزی\s*:?\s*([\d,\.]+)\s*(EUR|USD)",
                r"(\d+(?:[\d,]*)?(?:\.\d+)?)\s*(EUR|USD)\s*\)",
                r"total\s*amount\s*:?\s*([\d,\.]+)",
                r"فاکتور\s*:?\s*([\d,\.]+)"
            ],

            # شرح کالا - با حذف دقیق کلمات نامربوط
            "شرح_کالا": [
                r"شرح\s*کالا\s*:?\s*([^:]{20,200}?)(?=\s*(?:\d+\.|شرح|نرخ|کد|$))",
                r"توضیحات\s*کالا\s*:?\s*([^:]{20,200})",
                r"description\s*:?\s*([^:]{20,200})",
                # الگوی منفی - عدم شامل کلمات نامربوط
                r"(?!.*(?:اسناد|صمیمه|انبار|کد|شماره))([آ-ی\s]{20,200})"
            ],

            # نرخ ارز - تشخیص بهتر با context
            "نرخ_ارز": [
                r"نرخ\s*ارز\s*:?\s*([\d,\.]+)",
                r"exchange\s*rate\s*:?\s*([\d,\.]+)",
                r"23\.\s*نرخ\s*ارز\s*:?\s*([\d,\.]+)",
                r"rate\s*:?\s*([\d,\.]+)"
            ],

            # وزن - تفکیک دقیق خالص و ناخالص
            "وزن_خالص": [
                r"وزن\s+خالص\s*:?\s*([\d,\.]+)",
                r"net\s+weight\s*:?\s*([\d,\.]+)",
                r"38\.\s*وزن\s*:?\s*([\d,\.]+)",
                r"خالص\s*:?\s*([\d,\.]+)"
            ],

            "وزن_ناخالص": [
                r"وزن\s+ناخالص\s*:?\s*([\d,\.]+)",
                r"gross\s+weight\s*:?\s*([\d,\.]+)",
                r"ناخالص\s*:?\s*([\d,\.]+)"
            ],

            # کد کالا - با validation
            "کد_کالا": [
                r"کد\s*کالا\s*:?\s*(\d{8})",
                r"HS\s*code\s*:?\s*(\d{8})",
                r"(\d{8})\s*(?=.*کالا)",
                r"tariff\s*code\s*:?\s*(\d{8})"
            ],

            # کشور - با شناسایی context
            "کشور_طرف_معامله": [
                r"طرف\s*معامله\s*:?\s*([A-Z]{2})",
                r"صادرکننده\s*:?\s*([A-Z]{2})",
                r"country\s*:?\s*([A-Z]{2})",
                r"کشور\s*:?\s*([A-Z]{2})"
            ],

            # تعداد بسته - با واحد
            "تعداد_بسته": [
                r"تعداد\s*بسته\s*:?\s*(\d+)",
                r"بسته\s*:?\s*(\d+)\s*(?:عدد)?",
                r"packages\s*:?\s*(\d+)",
                r"(\d+)\s*(?:بسته|عدد.*بسته)"
            ],

            # مبالغ مالی - با شناسایی دقیق واحد
            "مبلغ_حقوق_ورودی": [
                r"حقوق\s*ورودی\s*:?\s*([\d,]+)\s*ریال",
                r"duty\s*:?\s*([\d,]+)",
                r"(\d{8,})\s*ریال"
            ],

            "مبلغ_مالیات_بر_ارزش_افزوده": [
                r"مالیات.*ارزش.*افزوده\s*:?\s*([\d,]+)",
                r"VAT\s*:?\s*([\d,]+)",
                r"(\d{8,})\s*(?=.*مالیات)"
            ]
        }

    def get_patterns_for_field(self, field_name: str) -> List[str]:
        """دریافت الگوهای یک فیلد خاص"""
        return self.patterns.get(field_name, [])

    def extract_with_priority(self, text: str, field_name: str) -> Dict[str, Any]:
        """استخراج با اولویت‌بندی الگوها"""
        patterns = self.get_patterns_for_field(field_name)
        results = []

        for i, pattern in enumerate(patterns):
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    # تعیین اعتماد بر اساس اولویت الگو
                    confidence = 1.0 - (i * 0.15)  # کاهش 15% برای هر الگوی بعدی

                    # تعیین مقدار
                    if match.groups():
                        value = match.group(1).strip()
                    else:
                        value = match.group(0).strip()

                    if value:
                        results.append({
                            "value": value,
                            "confidence": max(0.1, confidence),
                            "pattern_index": i,
                            "position": match.span(),
                            "matched_text": match.group(0)
                        })

            except Exception as e:
                continue

        # بازگشت بهترین نتیجه
        if results:
            best_result = max(results, key=lambda x: x["confidence"])
            return best_result

        return {"value": None, "confidence": 0, "pattern_index": -1}

    def validate_extracted_value(self, field_name: str, value: str) -> bool:
        """اعتبارسنجی مقدار استخراج شده"""
        if not value:
            return False

        try:
            if field_name == "شماره_کوتاژ":
                return re.match(r'^\d{8}$', value) is not None

            elif field_name == "کد_کالا":
                return re.match(r'^\d{8}$', value) is not None

            elif field_name == "کشور_طرف_معامله":
                return re.match(r'^[A-Z]{2}$', value) is not None

            elif field_name in ["وزن_خالص", "نرخ_ارز", "مبلغ_کل_فاکتور"]:
                return re.match(r'^\d+(\.\d+)?$', value.replace(',', '')) is not None

            elif field_name in ["تعداد_بسته", "مبلغ_حقوق_ورودی"]:
                return re.match(r'^\d+$', value.replace(',', '')) is not None

            else:
                return len(value.strip()) > 0

        except:
            return False