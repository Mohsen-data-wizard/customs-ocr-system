#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
استخراجکننده دادهها
"""

import re
import logging
from typing import Dict, List, Optional, Any
from collections import Counter
from .pattern_extractor import CustomsPatternExtractor
from utils.text_preprocessor import AdvancedTextPreprocessor

logger = logging.getLogger(__name__)

class DataExtractor:
    """استخراجکننده دادهها"""
    
    def __init__(self, pattern_extractor: CustomsPatternExtractor, config):
        self.pattern_extractor = CustomsPatternExtractor
        self.config = config
        self.preprocessor = AdvancedTextPreprocessor()
        logger.info("🎯 استخراجکننده دادهها راهاندازی شد")

    def normalize_text(self, text: str) -> str:
        """نرمالسازی پیشرفته متن"""
        if not text:
            return ""

        try:
            # استفاده از پیش‌پردازشگر پیشرفته
            preprocessed = self.preprocessor.preprocess(text)
            text = preprocessed.get("normalized_text", text)

            # تنظیمات اضافی
            text = text.replace('ك', 'ک')
            text = text.replace('ة', 'ه')
            text = re.sub(r'[\u200c\u200d\ufeff\u200e\u200f]', '', text)
            text = re.sub(r'\s+', ' ', text)

            return text.strip()

        except Exception as e:
            logger.error(f"❌ خطا در نرمالسازی متن: {e}")
            return text

    def extract_from_structured_json(self, structured_data: dict) -> Dict[str, Any]:
        """استخراج از JSON ساختاریافته - بدون رای‌گیری"""
        try:
            logger.info("📝 استخراج از JSON ساختاریافته...")

            # استفاده از pattern extractor جدید
            pattern_extractor = CustomsPatternExtractor()
            result = pattern_extractor.extract_from_structured_json(structured_data)

            return result

        except Exception as e:
            logger.error(f"❌ خطا در استخراج: {e}")
            return {}

    def clean_extracted_value(self, field_name: str, value: str) -> str:
        """پاکسازی بهبود یافته مقادیر"""
        if not value:
            return ""

        value = str(value).strip()

        try:
            if field_name == "شرح_کالا":
                # حذف کلمات نامربوط
                unwanted_words = ['حقوق', 'برداخت', 'قانون', 'تنظیم', 'اظهار', 'مسنولیت', 'تاریخ']
                for word in unwanted_words:
                    value = value.replace(word, ' ')

                # حذف اعداد بزرگ و نشانه‌های اضافی
                value = re.sub(r'\d{5,}', '', value)
                value = re.sub(r'[:\.\+\-]{2,}', ' ', value)
                value = ' '.join(value.split())

                # اگر خیلی کوتاه شد، خالی برگردان
                if len(value) < 10:
                    return ""

            elif field_name == "مبلغ_کل_فاکتور":
                # نرمال‌سازی مبلغ
                value = self.preprocessor.normalize_digits(value)
                value = re.sub(r'[^\d\.]', '', value)

            elif field_name == "نرخ_ارز":
                # نرمال‌سازی نرخ ارز
                value = self.preprocessor.normalize_digits(value)
                value = re.sub(r'[^\d\.]', '', value)

                # اگر خیلی کوچک است، احتمالاً اشتباه است
                try:
                    if float(value) < 1000:
                        return ""
                except:
                    pass

            elif field_name in ["کد_کالا", "شماره_کوتاژ"]:
                # فقط 8 رقم
                value = re.sub(r'[^\d]', '', value)
                if len(value) != 8:
                    return ""

            elif field_name == "مبلغ_حقوق_ورودی":
                # نرمال‌سازی مبلغ حقوق
                value = self.preprocessor.normalize_digits(value)
                value = re.sub(r'[^\d]', '', value)

                # حداقل 8 رقم باشد
                if len(value) < 8:
                    return ""

            return value

        except Exception as e:
            logger.error(f"❌ خطا در پاکسازی {field_name}: {e}")
            return value
    
    def extract_from_text(self, text: str, document_type: str = "وارداتی") -> Dict[str, Any]:
        """استخراج دادهها از متن"""
        try:
            # نرمالسازی متن
            normalized_text = self.normalize_text(text)
            
            if not normalized_text:
                logger.warning("⚠️ متن خالی است")
                return {}
            
            logger.info(f"📝 استخراج از متن {len(normalized_text)} کاراکتری (نوع: {document_type})")
            logger.info(f"🔍 پیش‌نمایش متن استخراج شده (اول 500 کاراکتر):")
            logger.info(f"📄 {repr(normalized_text[:500])}")
            logger.info(f"🔍 پیش‌نمایش متن استخراج شده (آخر 500 کاراکتر):")
            logger.info(f"📄 {repr(normalized_text[-500:])}")
            # انتخاب الگوها
            patterns = self.CustomsPatternExtractor.get_patterns(document_type)
            
            # استخراج فیلدها
            extracted_data = {}
            extraction_stats = {
                'total_fields': len(patterns),
                'extracted_fields': 0,
                'failed_fields': 0,
                'high_confidence_fields': 0
            }
            
            for field_name, field_patterns in patterns.items():
                try:
                    result = self.extract_field_with_voting(field_name, field_patterns, normalized_text)
                    
                    if result:
                        extracted_data[field_name] = result
                        extraction_stats['extracted_fields'] += 1
                        
                        if result['confidence'] > 70:
                            extraction_stats['high_confidence_fields'] += 1
                    else:
                        extraction_stats['failed_fields'] += 1
                        
                except Exception as e:
                    logger.error(f"❌ خطا در استخراج {field_name}: {e}")
                    extraction_stats['failed_fields'] += 1
            
            # محاسبه نرخ موفقیت
            success_rate = (extraction_stats['extracted_fields'] / extraction_stats['total_fields']) * 100
            extraction_stats['success_rate'] = success_rate
            
            logger.info(f"📊 استخراج کامل: {extraction_stats['extracted_fields']}/{extraction_stats['total_fields']} فیلد ({success_rate:.1f}%)")
            
            return {
                'extracted_data': extracted_data,
                'stats': extraction_stats,
                'text_length': len(normalized_text),
                'document_type': document_type
            }
            
        except Exception as e:
            logger.error(f"❌ خطا در استخراج دادهها: {e}")
            return {}
    
    def detect_page_type(self, text: str) -> str:
        """تشخیص نوع صفحه"""
        try:
            # شمارش الگوهای مختلف
            table_31_count = len(re.findall(r'\b31\s+', text))
            description_count = len(re.findall(r'شرح\s*کالا', text))
            
            if table_31_count == 0:
                return "single_item"
            elif table_31_count == 1:
                return "last_page"
            elif table_31_count >= 2:
                return "middle_page"
            else:
                return "first_page"
                
        except Exception as e:
            logger.error(f"❌ خطا در تشخیص نوع صفحه: {e}")
            return "unknown"
    
    def validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """اعتبارسنجی دادههای استخراج شده"""
        validation_results = {
            'valid_fields': 0,
            'invalid_fields': 0,
            'warnings': [],
            'errors': []
        }
        
        try:
            extracted_data = data.get('extracted_data', {})
            
            for field_name, field_result in extracted_data.items():
                value = field_result.get('value', '')
                confidence = field_result.get('confidence', 0)
                
                # بررسی اعتماد
                if confidence < 30:
                    validation_results['warnings'].append(f"{field_name}: اعتماد پایین ({confidence:.1f}%)")
                
                # بررسیهای خاص هر فیلد
                if field_name == "کد_کالا" and value:
                    if not re.match(r'^\d{8}$', value):
                        validation_results['errors'].append(f"{field_name}: فرمت نامعتبر")
                        validation_results['invalid_fields'] += 1
                    else:
                        validation_results['valid_fields'] += 1
                        
                elif field_name == "شماره_کوتا" and value:
                    if not re.match(r'^\d{8}$', value):
                        validation_results['errors'].append(f"{field_name}: فرمت نامعتبر")
                        validation_results['invalid_fields'] += 1
                    else:
                        validation_results['valid_fields'] += 1
                        
                elif field_name in ["وزن_خالص", "مبلغ_کل_فاکتور"] and value:
                    if not re.match(r'^\d+(\.\d+)?$', value):
                        validation_results['warnings'].append(f"{field_name}: فرمت عددی مشکوک")
                    validation_results['valid_fields'] += 1
                    
                else:
                    validation_results['valid_fields'] += 1
            
            logger.info(f"✅ اعتبارسنجی: {validation_results['valid_fields']} معتبر, {validation_results['invalid_fields']} نامعتبر")
            
        except Exception as e:
            logger.error(f"❌ خطا در اعتبارسنجی: {e}")
            validation_results['errors'].append(f"خطا در اعتبارسنجی: {e}")
        
        return validation_results
