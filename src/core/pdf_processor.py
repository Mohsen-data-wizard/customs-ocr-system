#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
پردازشکننده فایلهای PDF
"""

import fitz  # PyMuPDF
import numpy as np
from PIL import Image
import io
import logging
from pathlib import Path
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

class PDFProcessor:
    """پردازشکننده PDF"""
    
    def __init__(self, config):
        self.config = config
        self.default_dpi = config.get('processing.default_dpi', 350)
        logger.info("📄 پردازشکننده PDF راهاندازی شد")
    
    def convert_to_image(self, pdf_path: str, page_num: int = 0, dpi: Optional[int] = None) -> Optional[np.ndarray]:
        """تبدیل صفحه PDF به تصویر"""
        try:
            if dpi is None:
                dpi = self.default_dpi
            
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                logger.error(f"❌ فایل PDF یافت نشد: {pdf_path}")
                return None
            
            logger.info(f"🔄 تبدیل PDF به تصویر (صفحه {page_num + 1}, DPI: {dpi})")
            
            # باز کردن PDF
            doc = fitz.open(str(pdf_path))
            
            if page_num >= len(doc):
                logger.error(f"❌ شماره صفحه نامعتبر: {page_num} (کل: {len(doc)})")
                doc.close()
                return None
            
            # بارگذاری صفحه
            page = doc.load_page(page_num)
            
            # تنظیم zoom بر اساس DPI
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            
            # تبدیل به تصویر
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # تبدیل به PIL Image
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            
            # بستن فایل
            doc.close()
            
            # تبدیل به NumPy array
            image_array = np.array(img)
            
            logger.info(f"✅ تصویر ایجاد شد: {image_array.shape}")
            return image_array
            
        except Exception as e:
            logger.error(f"❌ خطا در تبدیل PDF: {e}")
            return None
    
    def get_page_count(self, pdf_path: str) -> int:
        """تعداد صفحات PDF"""
        try:
            doc = fitz.open(str(pdf_path))
            count = len(doc)
            doc.close()
            return count
        except Exception as e:
            logger.error(f"❌ خطا در شمارش صفحات: {e}")
            return 0
    
    def get_pdf_info(self, pdf_path: str) -> dict:
        """اطلاعات PDF"""
        try:
            pdf_path = Path(pdf_path)
            doc = fitz.open(str(pdf_path))
            
            metadata = doc.metadata
            page_count = len(doc)
            
            # اندازه فایل
            file_size = pdf_path.stat().st_size / (1024 * 1024)  # MB
            
            doc.close()
            
            return {
                'file_name': pdf_path.name,
                'file_size_mb': round(file_size, 2),
                'page_count': page_count,
                'title': metadata.get('title', ''),
                'author': metadata.get('author', ''),
                'subject': metadata.get('subject', ''),
                'creator': metadata.get('creator', ''),
                'producer': metadata.get('producer', ''),
                'creation_date': metadata.get('creationDate', ''),
                'modification_date': metadata.get('modDate', ''),
            }
            
        except Exception as e:
            logger.error(f"❌ خطا در دریافت اطلاعات PDF: {e}")
            return {}
    
    def extract_all_pages(self, pdf_path: str, dpi: Optional[int] = None) -> List[np.ndarray]:
        """استخراج تمام صفحات PDF"""
        try:
            if dpi is None:
                dpi = self.default_dpi
            
            doc = fitz.open(str(pdf_path))
            pages = []
            
            logger.info(f"📚 استخراج {len(doc)} صفحه از PDF")
            
            for page_num in range(len(doc)):
                try:
                    page = doc.load_page(page_num)
                    zoom = dpi / 72.0
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    
                    img_data = pix.tobytes("ppm")
                    img = Image.open(io.BytesIO(img_data))
                    image_array = np.array(img)
                    
                    pages.append(image_array)
                    logger.debug(f"✅ صفحه {page_num + 1} استخراج شد")
                    
                except Exception as e:
                    logger.error(f"❌ خطا در استخراج صفحه {page_num + 1}: {e}")
                    continue
            
            doc.close()
            logger.info(f"✅ {len(pages)} صفحه با موفقیت استخراج شد")
            return pages
            
        except Exception as e:
            logger.error(f"❌ خطا در استخراج صفحات: {e}")
            return []
    
    def detect_document_type(self, pdf_path: str) -> str:
        """تشخیص نوع سند (تککالایی/چندکالایی)"""
        try:
            page_count = self.get_page_count(pdf_path)
            
            if page_count == 1:
                return "single_item"
            elif page_count > 1:
                # بررسی محتوای صفحه اول برای تشخیص دقیقتر
                first_page_image = self.convert_to_image(pdf_path, 0)
                if first_page_image is not None:
                    # اینجا میتوان الگوریتم پیچیدهتری برای تشخیص نوع اضافه کرد
                    return "multi_item"
                else:
                    return "multi_item"
            else:
                return "unknown"
                
        except Exception as e:
            logger.error(f"❌ خطا در تشخیص نوع سند: {e}")
            return "unknown"
    
    def validate_pdf(self, pdf_path: str) -> bool:
        """اعتبارسنجی فایل PDF"""
        try:
            pdf_path = Path(pdf_path)
            
            # بررسی وجود فایل
            if not pdf_path.exists():
                logger.error(f"❌ فایل وجود ندارد: {pdf_path}")
                return False
            
            # بررسی پسوند
            if pdf_path.suffix.lower() != '.pdf':
                logger.error(f"❌ فرمت فایل نامعتبر: {pdf_path.suffix}")
                return False
            
            # تست باز کردن PDF
            doc = fitz.open(str(pdf_path))
            
            if len(doc) == 0:
                logger.error("❌ PDF خالی است")
                doc.close()
                return False
            
            # تست تبدیل صفحه اول
            page = doc.load_page(0)
            pix = page.get_pixmap()
            
            doc.close()
            
            logger.info(f"✅ PDF معتبر است: {pdf_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ PDF نامعتبر: {e}")
            return False
