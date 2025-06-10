#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
موتور OCR ترکیبی
"""

import cv2
import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

logger = logging.getLogger(__name__)

class OCREngine:
    """موتور OCR ترکیبی با پشتیبانی از EasyOCR و Tesseract"""
    
    def __init__(self, config):
        self.config = config
        self.easyocr_reader = None
        self.tesseract_ready = False
        
        # راهاندازی موتورها
        self._setup_easyocr()
        self._setup_tesseract()
        
        logger.info(f"🔍 OCR Engine راهاندازی شد - EasyOCR: {self.easyocr_reader is not None}, Tesseract: {self.tesseract_ready}")
    
    def _setup_easyocr(self):
        """راهاندازی EasyOCR"""
        if not EASYOCR_AVAILABLE:
            logger.warning("⚠️ EasyOCR در دسترس نیست")
            return
        
        try:
            gpu_enabled = self.config.get('ocr.easyocr.gpu', True)
            languages = self.config.get('ocr.easyocr.languages', ['fa', 'en', 'ar'])
            
            logger.info(f"🚀 راهاندازی EasyOCR - GPU: {gpu_enabled}, زبانها: {languages}")
            
            self.easyocr_reader = easyocr.Reader(
                languages, 
                gpu=gpu_enabled, 
                verbose=False,
                download_enabled=True
            )
            
            logger.info("✅ EasyOCR آماده شد")
            
        except Exception as e:
            logger.error(f"❌ خطا در راهاندازی EasyOCR: {e}")
            self.easyocr_reader = None
    
    def _setup_tesseract(self):
        """راهاندازی Tesseract"""
        if not TESSERACT_AVAILABLE:
            logger.warning("⚠️ Tesseract در دسترس نیست")
            return
        
        try:
            # تست Tesseract
            version = pytesseract.get_tesseract_version()
            logger.info(f"✅ Tesseract آماده شد - نسخه: {version}")
            self.tesseract_ready = True
            
        except Exception as e:
            logger.error(f"❌ خطا در راهاندازی Tesseract: {e}")
            self.tesseract_ready = False
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """پیشپردازش تصویر"""
        try:
            # تبدیل به grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image.copy()
            
            # بهبود کنتراست
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # کاهش نویز
            denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
            
            # تیزسازی
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(denoised, -1, kernel)
            
            return sharpened
            
        except Exception as e:
            logger.error(f"❌ خطا در پیشپردازش تصویر: {e}")
            return image
    
    def extract_text_easyocr(self, image: np.ndarray) -> str:
        """استخراج متن با EasyOCR"""
        if not self.easyocr_reader:
            return ""
        
        try:
            width_ths = self.config.get('ocr.easyocr.width_ths', 0.8)
            height_ths = self.config.get('ocr.easyocr.height_ths', 0.8)
            
            results = self.easyocr_reader.readtext(
                image, 
                detail=0, 
                paragraph=False,
                width_ths=width_ths,
                height_ths=height_ths
            )
            
            text = " ".join(results) if results else ""
            logger.debug(f"📝 EasyOCR استخراج کرد: {len(text)} کاراکتر")
            
            return text
            
        except Exception as e:
            logger.error(f"❌ خطا در EasyOCR: {e}")
            return ""
    
    def extract_text_tesseract(self, image: np.ndarray) -> str:
        """استخراج متن با Tesseract"""
        if not self.tesseract_ready:
            return ""
        
        try:
            primary_config = self.config.get('ocr.tesseract.config', '--psm 6 -l eng+fas')
            backup_configs = self.config.get('ocr.tesseract.backup_configs', [
                '--psm 4 -l eng+fas',
                '--psm 3 -l eng+fas'
            ])
            
            # تست تنظیم اصلی
            try:
                text = pytesseract.image_to_string(image, config=primary_config)
                if text.strip():
                    logger.debug(f"📝 Tesseract (اصلی) استخراج کرد: {len(text)} کاراکتر")
                    return text
            except:
                pass
            
            # تست تنظیمات پشتیبان
            for config in backup_configs:
                try:
                    text = pytesseract.image_to_string(image, config=config)
                    if text.strip():
                        logger.debug(f"📝 Tesseract (پشتیبان) استخراج کرد: {len(text)} کاراکتر")
                        return text
                except:
                    continue
            
            return ""
            
        except Exception as e:
            logger.error(f"❌ خطا در Tesseract: {e}")
            return ""
    
    def extract_text_hybrid(self, image: np.ndarray) -> str:
        """استخراج ترکیبی از هر دو موتور"""
        try:
            # پیشپردازش
            processed_image = self.preprocess_image(image)
            
            texts = []
            
            # EasyOCR
            easyocr_text = self.extract_text_easyocr(processed_image)
            if easyocr_text:
                texts.append(easyocr_text)
            
            # Tesseract
            tesseract_text = self.extract_text_tesseract(processed_image)
            if tesseract_text:
                texts.append(tesseract_text)
            
            # ترکیب نتایج
            combined_text = " ".join(texts)
            normalized_text = self.normalize_text(combined_text)
            
            logger.info(f"🔍 استخراج کامل - طول نهایی: {len(normalized_text)} کاراکتر")
            
            return normalized_text
            
        except Exception as e:
            logger.error(f"❌ خطا در استخراج ترکیبی: {e}")
            return ""
    
    def normalize_text(self, text: str) -> str:
        """نرمالسازی متن"""
        if not text:
            return ""
        
        import re
        
        # تبدیل ارقام فارسی/عربی به انگلیسی
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        arabic_digits = '٠١٢٣٤٥٦٧٨٩'
        english_digits = '0123456789'
        
        for p_digit, e_digit in zip(persian_digits, english_digits):
            text = text.replace(p_digit, e_digit)
        for a_digit, e_digit in zip(arabic_digits, english_digits):
            text = text.replace(a_digit, e_digit)
        
        # یکسانسازی کاراکترها
        text = text.replace('', 'ی').replace('ك', 'ک')
        text = text.replace('ة', 'ه').replace('ء', '')
        
        # حذف کاراکترهای غیرضروری
        text = re.sub(r'[\u200c\u200d\ufeff\u200e\u200f]', '', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def get_status(self) -> Dict[str, Any]:
        """وضعیت موتورهای OCR"""
        return {
            'easyocr_available': self.easyocr_reader is not None,
            'tesseract_available': self.tesseract_ready,
            'easyocr_gpu': self.config.get('ocr.easyocr.gpu', False) if self.easyocr_reader else False,
            'languages': self.config.get('ocr.easyocr.languages', [])
        }
