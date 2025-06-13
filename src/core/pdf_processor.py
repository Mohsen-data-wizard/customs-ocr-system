#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
پردازشکننده فایلهای PDF با OCR - نسخه بهبود یافته
"""

import fitz  # PyMuPDF
import numpy as np
from PIL import Image
import io
import logging
import json
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
from .ocr_engine import OCREngine
from .pattern_extractor import CustomsPatternExtractor  # اضافه شد
import time

logger = logging.getLogger(__name__)


class PDFProcessor:
    """پردازشکننده PDF با قابلیت OCR و استخراج الگوها"""

    def __init__(self, config):
        self.config = config
        self.default_dpi = config.get('processing.default_dpi', 350)

        # راه‌اندازی موتور OCR
        self.ocr_engine = OCREngine(config)

        # راه‌اندازی استخراج‌کننده الگوها (جدید)
        self.pattern_extractor = CustomsPatternExtractor()

        logger.info("📄 پردازشکننده PDF + OCR + الگوها راهاندازی شد")

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

    def extract_text_from_page(self, pdf_path: str, page_num: int = 0) -> Dict[str, Any]:
        """استخراج متن از یک صفحه PDF با OCR"""
        try:
            # تبدیل به تصویر
            image = self.convert_to_image(pdf_path, page_num)

            if image is None:
                return {'text': '', 'confidence': 0, 'error': 'تبدیل تصویر ناموفق'}

            # استخراج متن با OCR
            ocr_result = self.ocr_engine.extract_text(image)

            # اضافه کردن اطلاعات صفحه
            ocr_result['page_number'] = page_num + 1
            ocr_result['pdf_path'] = str(pdf_path)

            return ocr_result

        except Exception as e:
            logger.error(f"❌ خطا در استخراج متن صفحه {page_num + 1}: {e}")
            return {'text': '', 'confidence': 0, 'error': str(e)}

    def process_pdf_pages_individually(self, pdf_path: str, output_dir: str = None) -> List[Dict[str, Any]]:
        """پردازش هر صفحه PDF به صورت جداگانه و ایجاد JSON مجزا"""
        try:
            if output_dir is None:
                output_dir = Path(pdf_path).parent / "extracted_pages"

            output_dir = Path(output_dir)
            output_dir.mkdir(exist_ok=True)

            # دریافت تعداد صفحات
            doc = fitz.open(str(pdf_path))
            total_pages = len(doc)
            doc.close()

            if total_pages == 0:
                logger.error("❌ PDF خالی است")
                return []

            results = []
            pdf_name = Path(pdf_path).stem

            logger.info(f"📄 پردازش {total_pages} صفحه به صورت جداگانه...")

            for page_num in range(total_pages):
                try:
                    logger.info(f"🔄 پردازش صفحه {page_num + 1}/{total_pages}...")

                    # مرحله 1: تبدیل به تصویر
                    image = self.convert_to_image(pdf_path, page_num)
                    if image is None:
                        logger.warning(f"⚠️ صفحه {page_num + 1}: تبدیل تصویر ناموفق")
                        continue

                    # مرحله 2: استخراج متن با OCR
                    ocr_result = self.ocr_engine.extract_text(image)
                    page_text = ocr_result.get('text', '')

                    if not page_text.strip():
                        logger.warning(f"⚠️ صفحه {page_num + 1}: متن استخراج نشد")
                        continue

                    # مرحله 3: تبدیل به JSON ساختاریافته
                    structured_json = self.convert_text_to_structured_json(page_text, "وارداتی")

                    # مرحله 4: استخراج فیلدها با الگوها
                    extraction_result = self.pattern_extractor.create_structured_json(page_text, page_num + 1)

                    # ترکیب نتایج
                    final_result = {
                        "document_info": {
                            "type": "اظهارنامه_گمرکی_وارداتی",
                            "page_number": page_num + 1,
                            "total_pages": total_pages,
                            "processed_at": datetime.now().isoformat(),
                            "pdf_name": pdf_name,
                            "pdf_path": str(pdf_path)
                        },
                        "raw_text": page_text,
                        "structured_data": structured_json,
                        "customs_extraction": extraction_result,
                        "ocr_info": {
                            "confidence": ocr_result.get('confidence', 0),
                            "processing_time": ocr_result.get('processing_time', 0),
                            "method": ocr_result.get('method', 'unknown'),
                            "text_length": len(page_text)
                        }
                    }

                    # ذخیره JSON برای این صفحه
                    json_filename = f"{pdf_name}_page_{page_num + 1:02d}.json"
                    json_path = output_dir / json_filename

                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(final_result, f, ensure_ascii=False, indent=2)

                    logger.info(f"💾 صفحه {page_num + 1} ذخیره شد: {json_path}")

                    # اضافه کردن به نتایج
                    result_summary = {
                        "page_number": page_num + 1,
                        "json_file": str(json_path),
                        "extracted_fields_count": len([
                            k for k, v in extraction_result["customs_fields"].items()
                            if v.get("value") is not None
                        ]),
                        "text_length": len(page_text),
                        "confidence": ocr_result.get('confidence', 0),
                        "key_data": extraction_result["summary"]
                    }

                    results.append(result_summary)

                    # نمایش خلاصه استخراج
                    self._display_extraction_summary(extraction_result, page_num + 1)

                except Exception as e:
                    logger.error(f"❌ خطا در پردازش صفحه {page_num + 1}: {e}")
                    continue

            # ایجاد فایل خلاصه کل
            summary_data = {
                "pdf_info": {
                    "file_path": str(pdf_path),
                    "file_name": pdf_name,
                    "total_pages": total_pages,
                    "processed_pages": len(results),
                    "output_directory": str(output_dir)
                },
                "processing_summary": {
                    "total_extracted_fields": sum(r["extracted_fields_count"] for r in results),
                    "average_confidence": sum(r["confidence"] for r in results) / len(results) if results else 0,
                    "total_text_length": sum(r["text_length"] for r in results),
                    "processed_at": datetime.now().isoformat()
                },
                "pages": results
            }

            summary_path = output_dir / f"{pdf_name}_summary.json"
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, ensure_ascii=False, indent=2)

            logger.info(f"🎉 پردازش کامل: {len(results)} صفحه")
            logger.info(f"📁 فایل‌ها در: {output_dir}")
            logger.info(f"📋 خلاصه در: {summary_path}")

            return results

        except Exception as e:
            logger.error(f"❌ خطا در پردازش چند صفحه‌ای: {e}")
            return []

    def convert_text_to_structured_json(self, text: str, document_type: str) -> Dict[str, Any]:
        """مرحله 3: تبدیل متن به فرمت JSON ساختاریافته"""
        try:
            # تقسیم متن به خطوط
            lines = [line.strip() for line in text.split('\n') if line.strip()]

            # ساختار JSON اولیه
            structured_data = {
                "document_info": {
                    "type": document_type,
                    "processed_at": datetime.now().isoformat(),
                    "total_lines": len(lines),
                    "total_characters": len(text)
                },
                "raw_text": text,
                "text_lines": lines,
                "sections": {
                    "header": [],
                    "body": [],
                    "numbers": [],
                    "dates": [],
                    "amounts": []
                },
                "patterns": {
                    "phone_numbers": [],
                    "emails": [],
                    "urls": [],
                    "persian_text": [],
                    "english_text": []
                }
            }

            # تجزیه اولیه خطوط
            import re

            for i, line in enumerate(lines):
                # شناسایی اعداد
                numbers = re.findall(r'\d+[\d,\.]*', line)
                if numbers:
                    structured_data["sections"]["numbers"].extend([{
                        "line_number": i + 1,
                        "line_text": line,
                        "numbers": numbers
                    }])

                # شناسایی تاریخ‌ها
                date_patterns = [
                    r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
                    r'\d{1,2}[/-]\d{1,2}[/-]\d{4}',
                    r'\d{1,2}[/-]\d{1,2}[/-]\d{2}'
                ]

                for pattern in date_patterns:
                    dates = re.findall(pattern, line)
                    if dates:
                        structured_data["sections"]["dates"].extend([{
                            "line_number": i + 1,
                            "line_text": line,
                            "dates": dates
                        }])

                # تقسیم به header/body
                if i < len(lines) * 0.2:
                    structured_data["sections"]["header"].append({
                        "line_number": i + 1,
                        "text": line
                    })
                else:
                    structured_data["sections"]["body"].append({
                        "line_number": i + 1,
                        "text": line
                    })

            # شناسایی الگوها در کل متن
            persian_pattern = r'[\u0600-\u06FF\u200C\u200D]+'
            english_pattern = r'[A-Za-z]+'

            structured_data["patterns"]["persian_text"] = re.findall(persian_pattern, text)
            structured_data["patterns"]["english_text"] = re.findall(english_pattern, text)

            logger.info(f"✅ متن به JSON ساختاریافته تبدیل شد ({len(structured_data['text_lines'])} خط)")

            return structured_data

        except Exception as e:
            logger.error(f"❌ خطا در تبدیل به JSON: {e}")
            return {
                "error": str(e),
                "raw_text": text,
                "document_type": document_type
            }

    def _display_extraction_summary(self, structured_data: Dict[str, Any], page_num: int):
        """نمایش خلاصه استخراج برای هر صفحه"""
        try:
            print(f"\n{'=' * 60}")
            print(f"📄 خلاصه استخراج صفحه {page_num}")
            print('=' * 60)

            summary = structured_data["summary"]

            if summary["key_identifiers"]:
                print("🔑 شناسه‌های کلیدی:")
                for key, value in summary["key_identifiers"].items():
                    print(f"   • {key}: {value}")

            if summary["financial_data"]:
                print("\n💰 اطلاعات مالی:")
                for key, value in summary["financial_data"].items():
                    print(f"   • {key}: {value:,}" if isinstance(value, (int, float)) else f"   • {key}: {value}")

            if summary["goods_info"]:
                print("\n📦 اطلاعات کالا:")
                for key, value in summary["goods_info"].items():
                    print(f"   • {key}: {value}")

            if summary["administrative_data"]:
                print("\n📋 اطلاعات اداری:")
                for key, value in summary["administrative_data"].items():
                    print(f"   • {key}: {value}")

            stats = structured_data["extraction_stats"]
            print(f"\n📊 آمار استخراج:")
            print(f"   • کل فیلدها: {stats['total_fields']}")
            print(f"   • استخراج شده: {stats['extracted_fields']}")
            print(f"   • اعتماد بالا: {stats['high_confidence_fields']}")
            print(f"   • زمان پردازش: {stats['extraction_time']:.2f} ثانیه")

            print('=' * 60 + "\n")

        except Exception as e:
            logger.error(f"خطا در نمایش خلاصه: {e}")

    # متدهای قبلی باقی مانده برای سازگاری
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

    def validate_pdf(self, pdf_path: str) -> bool:
        """اعتبارسنجی فایل PDF"""
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                logger.error(f"❌ فایل وجود ندارد: {pdf_path}")
                return False

            if pdf_path.suffix.lower() != '.pdf':
                logger.error(f"❌ فرمت فایل نامعتبر: {pdf_path.suffix}")
                return False

            doc = fitz.open(str(pdf_path))
            if len(doc) == 0:
                logger.error("❌ PDF خالی است")
                doc.close()
                return False

            page = doc.load_page(0)
            pix = page.get_pixmap()
            doc.close()

            logger.info(f"✅ PDF معتبر است: {pdf_path.name}")
            return True

        except Exception as e:
            logger.error(f"❌ PDF نامعتبر: {e}")
            return False