#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
استخراج‌کننده الگوهای گمرکی با Regex
"""

import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CustomsPatternExtractor:
    """استخراج‌کننده اطلاعات گمرکی با الگوهای regex"""

    def __init__(self):
        self.patterns = self._initialize_patterns()
        logger.info("🔍 الگوهای استخراج گمرکی آماده شد")

    def _initialize_patterns(self) -> Dict[str, Dict[str, Any]]:
        """تعریف الگوهای بهبود یافته"""
        from patterns.improved_patterns import ImprovedRegexPatterns

        # استفاده از الگوهای بهبود یافته
        improved_patterns = ImprovedRegexPatterns()

        enhanced_patterns = {}
        for field_name, patterns in improved_patterns.patterns.items():
            enhanced_patterns[field_name] = {
                "patterns": patterns,
                "type": "string",
                "description": f"فیلد {field_name} با الگوهای بهبود یافته"
            }

        return enhanced_patterns

    def extract_field(self, text: str, field_name: str) -> Dict[str, Any]:
        """استخراج یک فیلد خاص از متن"""
        if field_name not in self.patterns:
            return {"value": None, "confidence": 0, "matched_pattern": None}

        field_config = self.patterns[field_name]
        patterns = field_config["patterns"]
        field_type = field_config["type"]

        best_match = None
        best_confidence = 0
        matched_pattern = None

        for pattern in patterns:
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    if match.groups():
                        raw_value = match.group(1).strip()
                    else:
                        raw_value = match.group(0).strip()

                    # محاسبه confidence بر اساس موقعیت و طول
                    confidence = min(0.9, 0.5 + (len(raw_value) / 100))

                    if confidence > best_confidence:
                        best_match = raw_value
                        best_confidence = confidence
                        matched_pattern = pattern

            except Exception as e:
                logger.debug(f"خطا در پردازش الگو {pattern}: {e}")
                continue

        # تبدیل نوع داده
        converted_value = self._convert_value(best_match, field_type)

        return {
            "value": converted_value,
            "confidence": best_confidence,
            "matched_pattern": matched_pattern,
            "raw_value": best_match
        }

    def _convert_value(self, value: str, target_type: str) -> Any:
        """تبدیل مقدار به نوع مناسب"""
        if value is None:
            return None

        try:
            if target_type == "int":
                # حذف کاما و تبدیل به int
                cleaned = re.sub(r'[,،]', '', str(value))
                return int(float(cleaned))

            elif target_type == "float":
                # حذف کاما و تبدیل به float
                cleaned = re.sub(r'[,،]', '', str(value))
                return float(cleaned)

            elif target_type == "string":
                return str(value).strip()

            else:
                return value

        except (ValueError, TypeError):
            return value

    def extract_all_fields(self, text: str) -> Dict[str, Any]:
        """استخراج تمام فیلدهای گمرکی از متن"""
        logger.info("🔄 شروع استخراج تمام فیلدهای گمرکی...")

        extracted_data = {}
        extraction_stats = {
            "total_fields": len(self.patterns),
            "extracted_fields": 0,
            "failed_fields": 0,
            "high_confidence_fields": 0,
            "extraction_time": 0
        }

        start_time = datetime.now()

        for field_name in self.patterns:
            try:
                result = self.extract_field(text, field_name)
                extracted_data[field_name] = result

                if result["value"] is not None:
                    extraction_stats["extracted_fields"] += 1
                    if result["confidence"] > 0.7:
                        extraction_stats["high_confidence_fields"] += 1
                else:
                    extraction_stats["failed_fields"] += 1

                logger.debug(f"✅ {field_name}: {result['value']} (اعتماد: {result['confidence']:.2f})")

            except Exception as e:
                logger.error(f"❌ خطا در استخراج {field_name}: {e}")
                extracted_data[field_name] = {
                    "value": None,
                    "confidence": 0,
                    "error": str(e)
                }
                extraction_stats["failed_fields"] += 1

        extraction_stats["extraction_time"] = (datetime.now() - start_time).total_seconds()

        logger.info(f"🎯 استخراج کامل: {extraction_stats['extracted_fields']}/{extraction_stats['total_fields']} فیلد")

        return {
            "customs_data": extracted_data,
            "extraction_stats": extraction_stats,
            "document_type": "وارداتی_تک_کالایی"
        }

    def create_structured_json(self, text: str, page_number: int = 1) -> Dict[str, Any]:
        """ایجاد JSON ساختاریافته برای یک صفحه"""
        extraction_result = self.extract_all_fields(text)

        structured_json = {
            "document_info": {
                "type": "اظهارنامه_گمرکی_وارداتی",
                "page_number": page_number,
                "processed_at": datetime.now().isoformat(),
                "extraction_method": "regex_patterns"
            },
            "raw_text": text,
            "customs_fields": extraction_result["customs_data"],
            "extraction_stats": extraction_result["extraction_stats"],
            "summary": self._create_summary(extraction_result["customs_data"])
        }

        return structured_json

    def _create_summary(self, customs_data: Dict[str, Any]) -> Dict[str, Any]:
        """ایجاد خلاصه داده‌های استخراج شده"""
        summary = {
            "key_identifiers": {},
            "financial_data": {},
            "goods_info": {},
            "administrative_data": {}
        }

        # شناسه‌های کلیدی
        key_fields = ["شماره_کوتاژ", "کد_کالا", "کد_ثبت_سفارش"]
        for field in key_fields:
            if field in customs_data and customs_data[field]["value"]:
                summary["key_identifiers"][field] = customs_data[field]["value"]

        # اطلاعات مالی
        financial_fields = ["مبلغ_کل_فاکتور", "ارزش_گمرکی_قلم_کالا", "مبلغ_حقوق_ورودی",
                            "مبلغ_مالیات_بر_ارزش_افزوده", "جمع_حقوق_و_عوارض"]
        for field in financial_fields:
            if field in customs_data and customs_data[field]["value"]:
                summary["financial_data"][field] = customs_data[field]["value"]

        # اطلاعات کالا
        goods_fields = ["شرح_کالا", "وزن_خالص", "تعداد_واحد_کالا", "تعداد_بسته", "نوع_بسته"]
        for field in goods_fields:
            if field in customs_data and customs_data[field]["value"]:
                summary["goods_info"][field] = customs_data[field]["value"]

        # اطلاعات اداری
        admin_fields = ["کشور_طرف_معامله", "نوع_معامله", "نوع_ارز", "نرخ_ارز"]
        for field in admin_fields:
            if field in customs_data and customs_data[field]["value"]:
                summary["administrative_data"][field] = customs_data[field]["value"]

        return summary