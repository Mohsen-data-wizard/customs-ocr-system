#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
استخراجکننده دادهها
"""

import re
import logging
from typing import Dict, List, Optional, Any
from collections import Counter
from patterns.regex_patterns import PatternManager

logger = logging.getLogger(__name__)

class DataExtractor:
    """استخراجکننده دادهها"""
    
    def __init__(self, pattern_manager: PatternManager, config):
        self.pattern_manager = pattern_manager
        self.config = config
        logger.info("🎯 استخراجکننده دادهها راهاندازی شد")
    
    def normalize_text(self, text: str) -> str:
        """نرمالسازی متن"""
        if not text:
            return ""
        
        try:
            # تبدیل ارقام فارسی و عربی به انگلیسی
            persian_digits = '۰۱۲۳۴۵۶۷۸۹'
            arabic_digits = '٠١٢٣٤٥٦٧٨٩'
            english_digits = '0123456789'
            
            for p_digit, e_digit in zip(persian_digits, english_digits):
                text = text.replace(p_digit, e_digit)
            for a_digit, e_digit in zip(arabic_digits, english_digits):
                text = text.replace(a_digit, e_digit)
            
            # یکسانسازی کاراکترها
            text = text.replace('', 'ی')
            text = text.replace('ك', 'ک')
            text = text.replace('ة', 'ه')
            text = text.replace('ء', '')
            
            # حذف کاراکترهای کنترلی
            text = re.sub(r'[\u200c\u200d\ufeff\u200e\u200f]', '', text)
            
            # تنظیم فاصلهها
            text = re.sub(r'\s+', ' ', text)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"❌ خطا در نرمالسازی متن: {e}")
            return text
    
    def extract_field_with_voting(self, field_name: str, patterns: List[str], text: str) -> Optional[Dict[str, Any]]:
        """استخراج فیلد با سیستم رایگیری"""
        candidates = []
        pattern_results = {}
        
        logger.debug(f"🔍 استخراج {field_name} با {len(patterns)} الگو")
        
        for i, pattern in enumerate(patterns):
            try:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                
                if matches:
                    pattern_matches = []
                    for match in matches:
                        if isinstance(match, tuple):
                            # انتخاب اولین گروه غیرخالی
                            match_value = next((m for m in match if m), "")
                        else:
                            match_value = match
                        
                        if match_value and str(match_value).strip():
                            clean_match = str(match_value).strip()
                            candidates.append(clean_match)
                            pattern_matches.append(clean_match)
                    
                    if pattern_matches:
                        pattern_results[f"pattern_{i+1}"] = pattern_matches
                        logger.debug(f"   الگو {i+1}: {len(pattern_matches)} نتیجه")
                
            except Exception as e:
                logger.warning(f"   الگو {i+1}: خطا - {e}")
                continue
        
        if not candidates:
            logger.debug(f"❌ {field_name}: هیچ نتیجهای یافت نشد")
            return None
        
        # رایگیری
        vote_counter = Counter(candidates)
        winner, votes = vote_counter.most_common(1)[0]
        
        # محاسبه اعتماد
        confidence = (votes / len(candidates)) * 100
        
        # پاکسازی نهایی
        cleaned_winner = self.clean_extracted_value(field_name, winner)
        
        result = {
            'value': cleaned_winner,
            'confidence': confidence,
            'votes': votes,
            'total_candidates': len(candidates),
            'all_candidates': list(set(candidates)),
            'pattern_results': pattern_results
        }
        
        logger.info(f"✅ {field_name}: '{cleaned_winner}' ({votes}/{len(candidates)} رای, {confidence:.1f}%)")
        return result
    
    def clean_extracted_value(self, field_name: str, value: str) -> str:
        """پاکسازی مقادیر استخراج شده"""
        if not value:
            return ""
        
        value = str(value).strip()
        
        try:
            if field_name == "شرح_کالا":
                # حذف اعداد بزرگ
                value = re.sub(r'\d{5,}', '', value)
                # حذف نشانههای تکراری
                value = re.sub(r'[:\.\+\-]{2,}', ' ', value)
                # تنظیم فاصلهها
                value = ' '.join(value.split())
                
            elif field_name == "نوع_بسته":
                # فقط انواع معتبر
                valid_types = ['عدد', 'پالت', 'نگله', 'سایر', 'رول', 'کارتن', 'گونی', 'جعبه']
                if value not in valid_types:
                    # تلاش برای تطبیق تقریبی
                    for valid_type in valid_types:
                        if valid_type in value:
                            return valid_type
                    return ""
                    
            elif field_name in ["وزن_خالص", "مبلغ_کل_فاکتور", "ارزش_گمرکی_قلم_کالا", 
                               "نرخ_ارز", "بیمه", "کرایه"]:
                # فقط اعداد و نقطه
                value = re.sub(r'[^\d\.]', '', value)
                # حذف نقطههای اضافی
                if value.count('.') > 1:
                    parts = value.split('.')
                    value = parts[0] + '.' + ''.join(parts[1:])
                
            elif field_name == "کد_کالا":
                # فقط 8 رقم
                value = re.sub(r'[^\d]', '', value)
                if len(value) != 8:
                    return ""
                    
            elif field_name == "شماره_کوتا":
                # فقط 8 رقم
                value = re.sub(r'[^\d]', '', value)
                if len(value) != 8:
                    return ""
                    
            elif field_name in ["کشور_طرف_معامله", "نوع_ارز"]:
                # حروف بزرگ
                value = value.upper()
                
            elif field_name in ["تعداد_بسته", "تعداد_واحد_کالا"]:
                # فقط اعداد
                value = re.sub(r'[^\d]', '', value)
                if not value:
                    return "1"  # مقدار پیشفرض
            
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
            
            # انتخاب الگوها
            patterns = self.pattern_manager.get_patterns(document_type)
            
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
