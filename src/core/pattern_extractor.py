#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
استخراج‌کننده الگوها - مطابق کد تست ارائه شده
"""

import re
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class CustomsPatternExtractor:
    """استخراج‌کننده الگوهای گمرکی - ساده شده"""

    def __init__(self):
        self.setup_patterns()
        logger.info("🎯 Pattern Extractor آماده است")

    def setup_patterns(self):
        """تنظیم الگوهای استخراج - مطابق کد تست"""
        self.patterns = {
            "کد_کالا": {
                "patterns": [
                    r'"ك٧٧"[^"]*"(\d{8})"',
                    r'"(\d{8})"[^"]*"٠٣٢"',
                    r'ك٧٧.*?"(\d{8})"'
                ],
                "type": "string",
                "description": "کد 8 رقمی کالا که معمولاً قبل از '٠٣٢' یا بعد از 'ك٧٧' قرار دارد"
            },
            "کد_ثبت_سفارش": {
                "patterns": [
                    r'"سفارشس"[^"]*"(\d{8})"',
                    r'سفارشس.*?"(\d{8})"',
                    r'ثبت.*?سفارش.*?"(\d{8})"'
                ],
                "type": "string",
                "description": "کد 8 رقمی ثبت سفارش که معمولاً بعد از 'سفارشس' قرار دارد"
            },
            "وزن_ناخالص": {
                "patterns": [
                    r'"(\d+)"[^"]*"س"[^"]*"(\d+)"[^"]*"٣٨"',
                    r'وزن.*?"(\d+)"',
                    r'"(\d+)"\s*"٣٨"'
                ],
                "type": "float",
                "description": "وزن ناخالص کالا که معمولاً قبل از '٣٨' قرار دارد"
            },
            "نوع_بسته": {
                "patterns": [
                    r'"نوع"\s*"بسته"\s*"(\w+)"',
                    r'بسته.*?"(نگله|رول|گونی|کارتن|عدد|جعبه|سایر|پالت|نکله)"',
                    r'نوع.*?بسته.*?"(\w+)"'
                ],
                "type": "string",
                "valid_values": ["نگله", "رول", "گونی", "کارتن", "عدد", "جعبه", "سایر", "پالت", "نکله"],
                "description": "نوع بسته بندی کالا از مقادیر مشخص شده"
            },
            "نرخ_ارز": {
                "patterns": [
                    r'"(\d{6}\.0)"',
                    r'نرخ.*?ارز.*?"(\d{6}\.0)"',
                    r'ارز.*?"(\d{6}\.0)"'
                ],
                "type": "float",
                "description": "نرخ ارز به صورت عدد 6 رقمی با .0 در انتها"
            },
            "نوع_معامله": {
                "patterns": [
                    r'"(حواله\s*ارزی|حواله)"[^"]*"ادزی"',
                    r'نوع.*?معامله.*?"(پیله\s*وری|حواله\s*ارزی|برات)"',
                    r'معامله.*?"(\w+\s*\w+)"'
                ],
                "type": "string",
                "mapping": {"حواله": "حواله ارزی"},
                "description": "نوع معامله که می‌تواند پیله وری، حواله ارزی یا برات باشد"
            },
            "نوع_ارز": {
                "patterns": [
                    r'"(يورو|EUR|USD|GBP)"',
                    r'ارز.*?"(\w+)"',
                    r'"(يورو)"[^"]*"بانکی"'
                ],
                "type": "string",
                "description": "نوع ارز مورد استفاده در معامله"
            },
            "مبلغ_کل_فاکتور": {
                "patterns": [
                    r'"انبار"[^"]*"(\d+,\d+)"[^"]*"(\d+)"[^"]*"بىكيرى"',
                    r'فاكتور.*?"(\d+(?:,\d+)*)"',
                    r'مبلغ.*?كل.*?"(\d+(?:,\d+)*)"'
                ],
                "type": "float",
                "description": "مبلغ کل فاکتور که معمولاً به صورت عدد با ممیز است"
            },
            "تعداد_واحد_کالا": {
                "patterns": [
                    r'"(\d+)"[^"]*"بىكيرى"',
                    r'تعداد.*?واحد.*?"(\d+)"',
                    r'واحد.*?كالا.*?"(\d+)"'
                ],
                "type": "int",
                "description": "تعداد واحدهای کالا"
            },
            "شرح_کالا": {
                "patterns": [
                    r'"شرح"\s*"کالا"\s*"([^"]+)"\s*"([^"]+)"\s*"([^"]+)"[^"]*"باقی"',
                    r'کالا.*?"([^"]+)"\s*"([^"]+)"\s*"([^"]+)".*?باقی'
                ],
                "type": "string",
                "description": "شرح کامل کالا که معمولاً بین 'کالا' و 'باقی' قرار دارد"
            },
            "بیمه": {
                "patterns": [
                    r'بیمه.*?"(\d+)"',
                    r'نرخ.*?تعديل.*?نرخ.*?"(\d+)"',
                    r'"(\d+)"[^"]*"بیمه"'
                ],
                "type": "float",
                "description": "مبلغ بیمه کالا"
            },
            "ارزش_گمرکی_قلم_کالا": {
                "patterns": [
                    r'"(\d+,\d+)"[^"]*"اسناد"',
                    r'ارزش.*?گمركى.*?"(\d+(?:,\d+)*)"',
                    r'قلم.*?كالا.*?"(\d+(?:,\d+)*)"'
                ],
                "type": "float",
                "description": "ارزش گمرکی قلم کالا"
            },
            "جمع_حقوق_و_عوارض": {
                "patterns": [
                    r'مدسه.*?"(\d+)"',
                    r'جمع.*?حقوق.*?"(\d+)"',
                    r'"(\d+)"[^"]*"مدسه"'
                ],
                "type": "int",
                "description": "جمع حقوق و عوارض گمرکی"
            },
            "مبلغ_مالیات_بر_ارزش_افزوده": {
                "patterns": [
                    r'رسید.*?"(\d+)"',
                    r'مالیات.*?ارزش.*?"(\d+(?:,\d+)*)"',
                    r'"(\d+)"[^"]*"رسید"'
                ],
                "type": "int",
                "description": "مبلغ مالیات بر ارزش افزوده"
            },
            "مبلغ_حقوق_ورودی": {
                "patterns": [
                    r'تضمین.*?"(\d+)"',
                    r'حقوق.*?ورودی.*?"(\d+(?:,\d+)*)"',
                    r'"(\d+)"[^"]*"تضمین"'
                ],
                "type": "int",
                "description": "مبلغ حقوق ورودی"
            }
        }

    def create_structured_json(self, text: str, page_number: int) -> Dict[str, Any]:
        """ایجاد JSON ساختاریافته - مطابق کد تست"""

        # تبدیل متن به فرمت قابل جستجو (مطابق کد تست)
        persian_words = self._extract_persian_text(text)
        search_text = '"' + '", "'.join(persian_words) + '"'

        # استخراج تمام فیلدها
        customs_fields = {}
        extraction_stats = {
            "total_fields": len(self.patterns),
            "extracted_fields": 0,
            "failed_fields": 0,
            "high_confidence_fields": 0,
            "extraction_time": 0
        }

        start_time = datetime.now()

        for field_name in self.patterns:
            result = self._extract_field(search_text, field_name)
            customs_fields[field_name] = result

            if result.get('value') is not None:
                extraction_stats["extracted_fields"] += 1
                if result.get('confidence', 0) > 0.8:
                    extraction_stats["high_confidence_fields"] += 1
            else:
                extraction_stats["failed_fields"] += 1

        end_time = datetime.now()
        extraction_stats["extraction_time"] = (end_time - start_time).total_seconds()

        # محاسبه نرخ موفقیت
        success_rate = (extraction_stats["extracted_fields"] / extraction_stats["total_fields"]) * 100 if \
        extraction_stats["total_fields"] > 0 else 0
        extraction_stats["success_rate"] = success_rate

        # ایجاد خلاصه
        summary = self._create_summary(customs_fields)

        return {
            "document_info": {
                "type": "اظهارنامه_گمرکی_وارداتی",
                "page_number": page_number,
                "processed_at": datetime.now().isoformat(),
                "extraction_method": "regex_patterns"
            },
            "raw_text": text[:500] + "..." if len(text) > 500 else text,
            "customs_fields": customs_fields,
            "extraction_stats": extraction_stats,
            "summary": summary
        }

    def _extract_persian_text(self, text: str) -> List[str]:
        """استخراج persian_text مطابق نمونه JSON"""
        import re
        persian_pattern = r'[\u0600-\u06FF\u200C\u200D\u06F0-\u06F9\u0660-\u0669]+'
        words = re.findall(persian_pattern, text)
        return [word.strip() for word in words if word.strip()]

    def _extract_field(self, text: str, field_name: str) -> Dict[str, Any]:
        """استخراج یک فیلد خاص - مطابق کد تست"""
        if field_name not in self.patterns:
            return {"value": None, "matched_pattern": None, "confidence": 0, "raw_value": None}

        field_config = self.patterns[field_name]
        patterns = field_config["patterns"]

        best_match = None
        matched_pattern = None
        confidence = 0

        for pattern in patterns:
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    if match.groups():
                        groups = match.groups()
                        if not best_match:
                            best_match = groups[0]
                            matched_pattern = pattern
                            confidence = 0.6  # اعتماد پایه
                    else:
                        if not best_match:
                            best_match = match.group(0)
                            matched_pattern = pattern
                            confidence = 0.5
            except Exception as e:
                logger.error(f"خطا در الگو {pattern}: {e}")
                continue

        # تبدیل مقدار
        converted_value = self._convert_value(best_match, field_config)

        return {
            "value": converted_value,
            "confidence": confidence,
            "matched_pattern": matched_pattern,
            "raw_value": best_match
        }

    def _convert_value(self, value: str, field_config: Dict[str, Any]) -> Any:
        """تبدیل مقدار به نوع مناسب"""
        if value is None:
            return None

        field_type = field_config.get("type", "string")

        try:
            # تبدیل اعداد فارسی به انگلیسی
            if isinstance(value, str):
                value = self._persian_to_english(value)

            if field_type == "int":
                cleaned = re.sub(r'\D', '', value)
                return int(cleaned) if cleaned else None
            elif field_type == "float":
                cleaned = re.sub(r'[^\d.,]', '', value)
                cleaned = cleaned.replace(',', '.')
                return float(cleaned) if cleaned else None
            else:
                return str(value).strip()
        except (ValueError, TypeError):
            return value

    def _persian_to_english(self, text: str) -> str:
        """تبدیل اعداد فارسی به انگلیسی"""
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        english_digits = '0123456789'
        translation_table = str.maketrans(persian_digits, english_digits)
        return text.translate(translation_table)

    def _create_summary(self, customs_fields: Dict[str, Any]) -> Dict[str, Any]:
        """ایجاد خلاصه - مطابق نمونه JSON"""
        summary = {
            "key_identifiers": {},
            "financial_data": {},
            "goods_info": {},
            "administrative_data": {}
        }

        # دسته‌بندی فیلدها
        key_fields = ["شماره_کوتاژ", "کد_ثبت_سفارش", "کد_کالا"]
        financial_fields = ["مبلغ_کل_فاکتور", "مبلغ_حقوق_ورودی", "مبلغ_مالیات_بر_ارزش_افزوده", "ارزش_گمرکی_قلم_کالا"]
        goods_fields = ["شرح_کالا", "وزن_ناخالص", "نوع_بسته", "تعداد_واحد_کالا"]
        admin_fields = ["نوع_معامله", "نوع_ارز", "نرخ_ارز"]

        for field_name, field_data in customs_fields.items():
            value = field_data.get('value')
            if value is not None:
                if field_name in key_fields:
                    summary["key_identifiers"][field_name] = value
                elif field_name in financial_fields:
                    summary["financial_data"][field_name] = value
                elif field_name in goods_fields:
                    summary["goods_info"][field_name] = value
                elif field_name in admin_fields:
                    summary["administrative_data"][field_name] = value

        return summary