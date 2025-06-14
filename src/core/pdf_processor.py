#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
پردازشکننده PDF ساده شده - DPI ثابت 600
"""

import fitz  # PyMuPDF
import numpy as np
from PIL import Image
import io
import logging
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from .ocr_engine import OCREngine
from .pattern_extractor import CustomsPatternExtractor

logger = logging.getLogger(__name__)


class PDFProcessor:
    """پردازشکننده PDF ساده شده"""

    def __init__(self, config=None):
        self.config = config
        self.default_dpi = 600  # ثابت شده

        # فقط OCR و Pattern Extractor
        self.ocr_engine = OCREngine(config)
        self.pattern_extractor = CustomsPatternExtractor()

        logger.info("📄 PDF Processor ساده آماده است (DPI: 600)")

    def convert_to_image(self, pdf_path: str, page_num: int = 0) -> Optional[np.ndarray]:
        """تبدیل PDF به تصویر با DPI ثابت 600"""
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                logger.error(f"❌ فایل PDF یافت نشد: {pdf_path}")
                return None

            logger.info(f"🔄 تبدیل PDF به تصویر (صفحه {page_num + 1})")

            doc = fitz.open(str(pdf_path))
            if page_num >= len(doc):
                logger.error(f"❌ شماره صفحه نامعتبر: {page_num}")
                doc.close()
                return None

            page = doc.load_page(page_num)

            # DPI ثابت 600
            zoom = 600 / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            # تبدیل به PIL Image
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            doc.close()

            # تبدیل به NumPy array
            image_array = np.array(img)

            logger.info(f"✅ تصویر آماده: {image_array.shape}")
            return image_array

        except Exception as e:
            logger.error(f"❌ خطا در تبدیل PDF: {e}")
            return None

    def process_pdf_pages_individually(self, pdf_path: str, output_dir: str = None) -> List[Dict[str, Any]]:
        """پردازش ساده PDF - تولید JSON مطابق نمونه"""
        try:
            if output_dir is None:
                output_dir = Path("data")  # مسیر ثابت

            output_dir = Path(output_dir)
            output_dir.mkdir(exist_ok=True)

            doc = fitz.open(str(pdf_path))
            total_pages = len(doc)
            doc.close()

            if total_pages == 0:
                logger.error("❌ PDF خالی است")
                return []

            results = []
            pdf_name = Path(pdf_path).stem

            logger.info(f"📄 پردازش {total_pages} صفحه...")

            for page_num in range(total_pages):
                try:
                    logger.info(f"🔄 صفحه {page_num + 1}/{total_pages}")

                    # مرحله 1: تبدیل به تصویر
                    image = self.convert_to_image(pdf_path, page_num)
                    if image is None:
                        continue

                    # مرحله 2: OCR
                    ocr_result = self.ocr_engine.extract_text(image)
                    page_text = ocr_result.get('text', '')

                    if not page_text.strip():
                        logger.warning(f"⚠️ صفحه {page_num + 1}: متن استخراج نشد")
                        continue

                    # مرحله 3: تولید JSON مطابق نمونه
                    final_result = self._create_standard_json(
                        page_text, page_num + 1, total_pages,
                        pdf_name, pdf_path, ocr_result
                    )

                    # ذخیره JSON
                    json_filename = f"{pdf_name}_page_{page_num + 1:02d}.json"
                    json_path = output_dir / json_filename

                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(final_result, f, ensure_ascii=False, indent=2)

                    logger.info(f"💾 ذخیره شد: {json_path}")

                    # خلاصه نتیجه
                    result_summary = {
                        "page_number": page_num + 1,
                        "json_file": str(json_path),
                        "text_length": len(page_text),
                        "confidence": ocr_result.get('confidence', 0)
                    }

                    results.append(result_summary)

                except Exception as e:
                    logger.error(f"❌ خطا در صفحه {page_num + 1}: {e}")
                    continue

            logger.info(f"✅ پردازش کامل: {len(results)} صفحه")
            return results

        except Exception as e:
            logger.error(f"❌ خطا در پردازش PDF: {e}")
            return []

    def _create_standard_json(self, text: str, page_num: int, total_pages: int,
                              pdf_name: str, pdf_path: str, ocr_result: Dict) -> Dict[str, Any]:
        """تولید JSON استاندارد مطابق نمونه"""

        # تقسیم متن برای persian_text
        persian_words = self._extract_persian_words(text)
        english_words = self._extract_english_words(text)
        numbers = self._extract_numbers(text)

        # ساختار JSON استاندارد
        structured_json = {
            "document_info": {
                "type": "اظهارنامه_گمرکی_وارداتی",
                "page_number": page_num,
                "total_pages": total_pages,
                "processed_at": datetime.now().isoformat(),
                "pdf_name": pdf_name,
                "pdf_path": str(pdf_path)
            },
            "raw_text": text,
            "structured_data": {
                "document_info": {
                    "type": "وارداتی",
                    "processed_at": datetime.now().isoformat(),
                    "total_lines": len(text.split('\n')),
                    "total_characters": len(text)
                },
                "raw_text": text,
                "text_lines": [line.strip() for line in text.split('\n') if line.strip()],
                "sections": {
                    "header": [{"line_number": 1, "text": text}],
                    "body": [],
                    "numbers": [{"line_number": 1, "line_text": text, "numbers": numbers}],
                    "dates": [],
                    "amounts": []
                },
                "patterns": {
                    "phone_numbers": [],
                    "emails": [],
                    "urls": [],
                    "persian_text": persian_words,
                    "english_text": english_words
                }
            },
            "customs_extraction": self.pattern_extractor.create_structured_json(text, page_num),
            "ocr_info": {
                "confidence": ocr_result.get('confidence', 0),
                "processing_time": ocr_result.get('processing_time', 0),
                "method": "easyocr",
                "text_length": len(text)
            }
        }

        return structured_json

    def _extract_persian_words(self, text: str) -> List[str]:
        """استخراج کلمات فارسی"""
        import re
        persian_pattern = r'[\u0600-\u06FF\u200C\u200D]+'
        words = re.findall(persian_pattern, text)
        return list(set(words))  # حذف تکرار

    def _extract_english_words(self, text: str) -> List[str]:
        """استخراج کلمات انگلیسی"""
        import re
        english_pattern = r'[A-Za-z]+'
        words = re.findall(english_pattern, text)
        return list(set(words))

    def _extract_numbers(self, text: str) -> List[str]:
        """استخراج اعداد"""
        import re
        number_pattern = r'[\d\u06F0-\u06F9\u0660-\u0669]+(?:[,\.][\d\u06F0-\u06F9\u0660-\u0669]+)*'
        numbers = re.findall(number_pattern, text)
        return numbers