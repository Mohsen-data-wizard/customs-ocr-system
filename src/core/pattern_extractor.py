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
        """تعریف الگوهای استخراج از JSON ساختاریافته"""
        return {
            # شماره کوتاژ - 8 رقم در ابتدای فهرست
            "شماره_کوتاژ": {
                "patterns": [
                    r'"کوتاژا",\s*"(\d{8})"',  # مستقیماً بعد از کوتاژا
                    r'"(\d{8})",\s*"[0-9/\s]*"',  # 8 رقم در ابتدای فهرست
                ],
                "type": "string"
            },

            # کد کالا - 8 رقم قبل از "032"
            "کد_کالا": {
                "patterns": [
                    r'"(\d{8})",\s*"032"',  # عدد 8 رقمی قبل از 032
                    r'"ك٧٧",\s*"(\d{8})"',  # بعد از ك77
                ],
                "type": "string"
            },

            # شماره ثبت سفارش
            "کد_ثبت_سفارش": {
                "patterns": [
                    r'"سفارشس",\s*"(\d{8})"',  # بعد از سفارشس
                    r'"(\d{8})",.*"سفارش"',  # 8 رقم قبل از کلمه سفارش
                ],
                "type": "string"
            },

            # وزن ناخالص - بین "38" و "س"
            "وزن_ناخالص": {
                "patterns": [
                    r'"38",\s*"وزن",\s*"(\d+)",.*?"س"',  # بین 38 و س
                    r'"(\d+)",\s*"38",\s*"وزن".*?"(\d+)",\s*"س"',  # دو عدد بین 38 و س
                ],
                "type": "float"
            },

            # نوع بسته - مستقیماً بعد از "نوع بسته"
            "نوع_بسته": {
                "patterns": [
                    r'"نوع",\s*"بسته",\s*"([^"]*)"',  # مستقیماً بعد از نوع بسته
                    r'"بسته",\s*"(نگله|رول|گونی|کارتن|عدد|جعبه|سایر|پالت)"',
                ],
                "type": "string",
                "valid_values": ["نگله", "رول", "گونی", "کارتن", "عدد", "جعبه", "سایر", "پالت"]
            },

            # نرخ ارز - فرمت 6رقم.0
            "نرخ_ارز": {
                "patterns": [
                    r'"نرخ",\s*"ازز",.*?"(\d{6}\.0)"',  # 6 رقم + .0
                    r'"(\d{6}\.0)"',  # هر جا که 6 رقم + .0 باشه
                ],
                "type": "float"
            },

            # نوع معامله - یکی از سه نوع
            "نوع_معامله": {
                "patterns": [
                    r'"(حواله)",\s*"ادزی"',  # اگر حواله دید -> حواله ارزی
                    r'"(پیله\s*وری)"',
                    r'"(برات)"',
                ],
                "type": "string",
                "valid_values": ["حواله ارزی", "پیله وری", "برات"],
                "mapping": {"حواله": "حواله ارزی"}
            },

            # نوع ارز
            "نوع_ارز": {
                "patterns": [
                    r'"(يورو)"',  # یورو در فهرست
                    r'"(EUR|USD|GBP)"',
                ],
                "type": "string"
            },

            # مبلغ کل فاکتور - عدد بالای "بىكيرى"
            "مبلغ_کل_فاکتور": {
                "patterns": [
                    r'"(\d+)",\s*"(\d+)",\s*"بىكيرى"',  # دو عدد بالای بىكيرى
                    r'"انبار",.*?"(\d+)",.*?"بىكيرى"',  # عدد بین انبار و بىكيرى
                ],
                "type": "float"
            },

            # تعداد واحد کالا - عدد قبل از "بىكيرى"
            "تعداد_واحد_کالا": {
                "patterns": [
                    r'"(\d+)",\s*"بىكيرى"',  # مستقیماً قبل از بىكيرى
                ],
                "type": "int"
            },

            # شرح کالا - از بعد "کالا" تا قبل "باقی"
            "شرح_کالا": {
                "patterns": [
                    r'"شرح",\s*"کالا",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)",.*?"باقی"',  # چندین کلمه
                    r'"کالا",\s*"([^"]+)",.*?"باقی"',  # یک کلمه
                ],
                "type": "string"
            },

            # بیمه - مقدار مشخص شده
            "بیمه": {
                "patterns": [
                    r'"نرخ",\s*"تعديل",\s*"نرخ",\s*"(\d+)"',  # بعد از نرخ تعدیل
                ],
                "type": "float"
            },

            # ارزش گمرکی قلم کالا - دو عدد ترکیبی
            "ارزش_گمرکی_قلم_کالا": {
                "patterns": [
                    r'"(\d+)",\s*"(\d+)",\s*"اسناد"',  # دو عدد قبل از اسناد
                ],
                "type": "float"
            },

            # جمع حقوق و عوارض - بعد از "مدسه"
            "جمع_حقوق_و_عوارض": {
                "patterns": [
                    r'"مدسه",\s*"(\d+)"',  # مستقیماً بعد از مدسه
                ],
                "type": "int"
            },

            # مبلغ مالیات بر ارزش افزوده - از کلمه "رسید"
            "مبلغ_مالیات_بر_ارزش_افزوده": {
                "patterns": [
                    r'"رسید",\s*"\d+",\s*"(\d+)"',  # عدد بعد از رسید
                ],
                "type": "int"
            },

            # جمع حقوق عوارض - زیر کلمه "تضمین"
            "مبلغ_حقوق_ورودی": {
                "patterns": [
                    r'"تضمین",\s*"(\d+)"',  # مستقیماً زیر تضمین
                ],
                "type": "int"
            }
        }
            # شماره کوتاژ - 8 رقم در ابتدای فهرست


    def extract_field(self, json_patterns: List[str], field_name: str) -> Dict[str, Any]:
        """استخراج یک فیلد از فهرست JSON patterns"""
        if field_name not in self.patterns:
            return {"value": None, "confidence": 0, "matched_pattern": None}

        field_config = self.patterns[field_name]
        patterns = field_config["patterns"]

        # تبدیل فهرست به متن قابل جستجو
        text = '"' + '", "'.join(json_patterns) + '"'

        best_match = None
        best_confidence = 0
        matched_pattern = None

        for pattern in patterns:
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    if match.groups():
                        # اگر چند گروه داریم (مثل مبلغ فاکتور)
                        if len(match.groups()) > 1:
                            # ترکیب اعداد با نقطه
                            raw_value = match.group(1) + "." + match.group(2)
                        else:
                            raw_value = match.group(1).strip()
                    else:
                        raw_value = match.group(0).strip()

                    # اعتبارسنجی بر اساس فیلد
                    if self._validate_field_value(field_name, raw_value, field_config):
                        confidence = 0.95  # اعتماد بالا چون از JSON ساختاریافته میاد

                        if confidence > best_confidence:
                            best_match = raw_value
                            best_confidence = confidence
                            matched_pattern = pattern

            except Exception as e:
                logger.debug(f"خطا در پردازش الگو {pattern}: {e}")
                continue

        # تبدیل نوع داده و mapping
        converted_value = self._convert_and_map_value(best_match, field_config)

        return {
            "value": converted_value,
            "confidence": best_confidence,
            "matched_pattern": matched_pattern,
            "raw_value": best_match
        }

    def _validate_field_value(self, field_name: str, value: str, field_config: dict) -> bool:
        """اعتبارسنجی مقدار بر اساس قوانین فیلد"""
        if not value:
            return False

        try:
            if field_name == "نرخ_ارز":
                # باید 6 رقم + .0 باشه
                return re.match(r'^\d{6}\.0$', value) is not None

            elif field_name in ["شماره_کوتاژ", "کد_کالا", "کد_ثبت_سفارش"]:
                # باید 8 رقم باشه
                return re.match(r'^\d{8}$', value) is not None

            elif field_name == "نوع_بسته":
                valid_values = field_config.get("valid_values", [])
                return value in valid_values

            elif field_name == "نوع_معامله":
                valid_values = field_config.get("valid_values", [])
                mapping = field_config.get("mapping", {})
                return value in valid_values or value in mapping

            return True

        except:
            return False

    def _convert_and_map_value(self, value: str, field_config: dict) -> Any:
        """تبدیل و نگاشت مقدار"""
        if value is None:
            return None

        try:
            # mapping اگر وجود دارد
            mapping = field_config.get("mapping", {})
            if value in mapping:
                value = mapping[value]

            field_type = field_config.get("type", "string")

            if field_type == "int":
                return int(value)
            elif field_type == "float":
                return float(value)
            elif field_type == "string":
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