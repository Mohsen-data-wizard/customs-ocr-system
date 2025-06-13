import easyocr
import pytesseract
import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
import logging
from typing import Optional, List, Dict, Any
import time

# حل مشکل PIL ANTIALIAS
try:
    # نسخه جدید PIL
    ANTIALIAS = Image.Resampling.LANCZOS
except AttributeError:
    # نسخه قدیمی PIL
    ANTIALIAS = Image.ANTIALIAS

logger = logging.getLogger(__name__)


class OCREngine:
    """موتور تشخیص نوشتار"""

    def __init__(self, config):

        self.config = config
        self.easyocr_reader = None
        self.tesseract_config = '--oem 3 --psm 6 -l eng+ara+fas'

        # تنظیمات OCR
        self.ocr_method = 'tesseract'
        self.ocr_method = config.get('ocr.method', 'easyocr')
        self.confidence_threshold = config.get('ocr.confidence_threshold', 0.5)

        # راه‌اندازی موتور انتخاب شده
        self._initialize_ocr_engine()

        logger.info(f"🔍 موتور OCR راه‌اندازی شد (روش: {self.ocr_method})")

    def _initialize_ocr_engine(self):
        """راه‌اندازی موتور OCR"""
        try:
            if self.ocr_method in ['easyocr', 'hybrid']:
                logger.info("📚 بارگذاری EasyOCR...")
                # بارگذاری مدل‌های فارسی و انگلیسی
                self.easyocr_reader = easyocr.Reader(['en', 'fa'], gpu=False, verbose=False)
                logger.info("✅ EasyOCR آماده است")

            if self.ocr_method in ['tesseract', 'hybrid']:
                # تست Tesseract
                try:
                    pytesseract.get_tesseract_version()
                    logger.info("✅ Tesseract آماده است")
                except Exception as e:
                    logger.warning(f"⚠️ Tesseract در دسترس نیست: {e}")
                    if self.ocr_method == 'tesseract':
                        self.ocr_method = 'easyocr'

        except Exception as e:
            logger.error(f"❌ خطا در راه‌اندازی OCR: {e}")
            raise

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """پیش‌پردازش تصویر برای OCR بهتر"""
        try:
            logger.debug("🔧 شروع پیش‌پردازش تصویر...")

            # تبدیل به grayscale اگر رنگی است
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image.copy()

            # کاهش سایز اگر خیلی بزرگ است
            height, width = gray.shape
            if height > 3000 or width > 3000:
                scale_factor = min(3000 / height, 3000 / width)
                new_height = int(height * scale_factor)
                new_width = int(width * scale_factor)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_AREA)
                logger.debug(f"📏 تصویر کوچک شد: {width}x{height} -> {new_width}x{new_height}")

            # افزایش کنتراست
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # کاهش نویز
            denoised = cv2.medianBlur(enhanced, 3)

            # threshold کردن
            _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            logger.debug("✅ پیش‌پردازش تصویر انجام شد")
            return binary

        except Exception as e:
            logger.error(f"❌ خطا در پیش‌پردازش: {e}")
            return image

    def extract_text_easyocr(self, image: np.ndarray) -> Dict[str, Any]:
        """استخراج متن با EasyOCR - بهبود یافته"""
        try:
            start_time = time.time()
            logger.debug("🔍 شروع EasyOCR...")

            # پیش‌پردازش
            processed_image = self.preprocess_image(image)

            # تشخیص متن
            logger.debug("📖 اجرای تشخیص متن...")
            results = self.easyocr_reader.readtext(processed_image, detail=1, paragraph=False)

            # پردازش نتایج
            full_text = ""
            detected_boxes = []
            total_confidence = 0
            valid_detections = 0

            for (bbox, text, confidence) in results:
                if confidence >= self.confidence_threshold and text.strip():
                    full_text += text + " "
                    detected_boxes.append({
                        'text': text,
                        'confidence': confidence,
                        'bbox': bbox
                    })
                    total_confidence += confidence
                    valid_detections += 1
                    logger.debug(f"📝 متن: '{text}' (اعتماد: {confidence:.2f})")

            avg_confidence = total_confidence / valid_detections if valid_detections > 0 else 0
            processing_time = time.time() - start_time

            logger.info(f"🔍 EasyOCR: {valid_detections} قطعه متن در {processing_time:.2f}ثانیه")

            return {
                'text': full_text.strip(),
                'confidence': avg_confidence,
                'boxes': detected_boxes,
                'method': 'easyocr',
                'processing_time': processing_time,
                'detections_count': valid_detections
            }

        except Exception as e:
            logger.error(f"❌ خطا در EasyOCR: {e}")
            return {
                'text': '',
                'confidence': 0,
                'method': 'easyocr',
                'error': str(e)
            }

    def extract_text_tesseract(self, image: np.ndarray) -> Dict[str, Any]:
        """استخراج متن با Tesseract"""
        try:
            start_time = time.time()

            # پیش‌پردازش
            processed_image = self.preprocess_image(image)

            # تشخیص متن
            text = pytesseract.image_to_string(processed_image, config=self.tesseract_config)

            # دریافت اعتماد
            try:
                data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT,
                                                 config=self.tesseract_config)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            except:
                avg_confidence = 50  # پیش‌فرض

            processing_time = time.time() - start_time

            logger.info(f"🔍 Tesseract: متن استخراج شد در {processing_time:.2f}ثانیه")

            return {
                'text': text.strip(),
                'confidence': avg_confidence / 100,  # تبدیل به 0-1
                'method': 'tesseract',
                'processing_time': processing_time,
                'detections_count': len([w for w in text.split() if w])
            }

        except Exception as e:
            logger.error(f"❌ خطا در Tesseract: {e}")
            return {'text': '', 'confidence': 0, 'method': 'tesseract', 'error': str(e)}

    def extract_text_hybrid(self, image: np.ndarray) -> Dict[str, Any]:
        """استخراج متن با روش ترکیبی"""
        try:
            logger.info("🔄 شروع استخراج ترکیبی...")

            # اجرای هر دو موتور
            easyocr_result = self.extract_text_easyocr(image)

            # اگر EasyOCR موفق بود، از Tesseract هم استفاده کن
            if easyocr_result.get('text'):
                tesseract_result = self.extract_text_tesseract(image)

                # ترکیب نتایج
                combined_text = easyocr_result['text']
                if tesseract_result.get('text'):
                    # اضافه کردن متن‌های یکتا از Tesseract
                    tesseract_words = set(tesseract_result['text'].split())
                    easyocr_words = set(easyocr_result['text'].split())
                    unique_words = tesseract_words - easyocr_words
                    if unique_words:
                        combined_text += " " + " ".join(unique_words)

                # انتخاب بهترین confidence
                best_confidence = max(
                    easyocr_result.get('confidence', 0),
                    tesseract_result.get('confidence', 0)
                )

                result = easyocr_result.copy()
                result['text'] = combined_text
                result['confidence'] = best_confidence
                result['method'] = 'hybrid'
                result['easyocr_confidence'] = easyocr_result.get('confidence', 0)
                result['tesseract_confidence'] = tesseract_result.get('confidence', 0)

                logger.info(
                    f"🏆 ترکیب موفق - EasyOCR: {easyocr_result.get('confidence', 0):.2f}, Tesseract: {tesseract_result.get('confidence', 0):.2f}")
                return result
            else:
                # اگر EasyOCR ناموفق بود، فقط Tesseract
                tesseract_result = self.extract_text_tesseract(image)
                tesseract_result['method'] = 'hybrid_tesseract_only'
                return tesseract_result

        except Exception as e:
            logger.error(f"❌ خطا در روش ترکیبی: {e}")
            return {'text': '', 'confidence': 0, 'method': 'hybrid', 'error': str(e)}

    def extract_text_multi_engine(self, image: np.ndarray) -> Dict[str, Any]:
        """استخراج با چندین engine و تأیید متقابل"""
        try:
            logger.info("🔄 شروع استخراج چند موتوری...")

            results = {}

            # اجرای EasyOCR
            if self.easyocr_reader:
                results['easyocr'] = self.extract_text_easyocr(image)

            # اجرای Tesseract
            try:
                results['tesseract'] = self.extract_text_tesseract(image)
            except:
                logger.warning("⚠️ Tesseract در دسترس نیست")

            # ترکیب هوشمند نتایج
            final_result = self._smart_combine_results(results)
            final_result['method'] = 'multi_engine'

            return final_result

        except Exception as e:
            logger.error(f"❌ خطا در روش چند موتوری: {e}")
            return {'text': '', 'confidence': 0, 'method': 'multi_engine', 'error': str(e)}

    def _smart_combine_results(self, results: Dict) -> Dict[str, Any]:
        """ترکیب هوشمند نتایج OCR"""
        try:
            if not results:
                return {'text': '', 'confidence': 0}

            # انتخاب بهترین نتیجه بر اساس confidence و طول متن
            best_result = None
            best_score = 0

            for engine, result in results.items():
                if result.get('text'):
                    # محاسبه امتیاز ترکیبی
                    confidence = result.get('confidence', 0)
                    text_length = len(result.get('text', ''))
                    score = confidence * 0.7 + min(text_length / 1000, 1) * 0.3

                    if score > best_score:
                        best_score = score
                        best_result = result

            if best_result:
                # اضافه کردن متن‌های یکتا از سایر engines
                main_text = best_result.get('text', '')
                for engine, result in results.items():
                    other_text = result.get('text', '')
                    if other_text and other_text != main_text:
                        # اضافه کردن کلمات یکتا
                        main_words = set(main_text.split())
                        other_words = set(other_text.split())
                        unique_words = other_words - main_words
                        if unique_words:
                            main_text += " " + " ".join(unique_words)

                combined_result = best_result.copy()
                combined_result['text'] = main_text
                combined_result['combined_from'] = list(results.keys())
                return combined_result

            return {'text': '', 'confidence': 0}

        except Exception as e:
            logger.error(f"❌ خطا در ترکیب نتایج: {e}")
            return {'text': '', 'confidence': 0}

    def extract_text(self, image: np.ndarray) -> Dict[str, Any]:
        """استخراج متن اصلی"""
        try:
            if image is None or image.size == 0:
                logger.error("❌ تصویر خالی است")
                return {'text': '', 'confidence': 0, 'error': 'تصویر خالی'}

            logger.info(f"🔍 شروع OCR با روش {self.ocr_method}")
            logger.debug(f"📏 اندازه تصویر: {image.shape}")

            # انتخاب روش OCR
            if self.ocr_method == 'easyocr':
                result = self.extract_text_easyocr(image)
            elif self.ocr_method == 'tesseract':
                result = self.extract_text_tesseract(image)
            elif self.ocr_method == 'hybrid':
                result = self.extract_text_hybrid(image)
            else:
                logger.error(f"❌ روش OCR نامعتبر: {self.ocr_method}")
                return {'text': '', 'confidence': 0, 'error': f'روش نامعتبر: {self.ocr_method}'}

            # لاگ نتیجه
            text_length = len(result.get('text', ''))
            confidence = result.get('confidence', 0)

            if text_length > 0:
                logger.info(f"✅ متن استخراج شد: {text_length} کاراکتر، اعتماد: {confidence:.2f}")
                # نمایش قسمتی از متن برای دیباگ
                preview = result.get('text', '')[:100]
                logger.debug(f"📝 پیش‌نمایش متن: {preview}...")
            else:
                logger.warning(f"⚠️ هیچ متنی استخراج نشد - خطا: {result.get('error', 'نامشخص')}")

            return result

        except Exception as e:
            logger.error(f"❌ خطا در استخراج متن: {e}")
            return {'text': '', 'confidence': 0, 'error': str(e)}

    def process_multiple_images(self, images: List[np.ndarray]) -> List[Dict[str, Any]]:
        """پردازش چندین تصویر"""
        results = []

        logger.info(f"📚 پردازش {len(images)} تصویر...")

        for i, image in enumerate(images):
            logger.info(f"🔄 پردازش تصویر {i + 1}/{len(images)}")
            result = self.extract_text(image)
            result['page_number'] = i + 1
            results.append(result)

        # آمار کلی
        successful_pages = sum(1 for r in results if r.get('text'))
        total_chars = sum(len(r.get('text', '')) for r in results)
        avg_confidence = sum(r.get('confidence', 0) for r in results) / len(results) if results else 0

        logger.info(f"✅ پردازش {len(images)} تصویر کامل شد")
        logger.info(
            f"📊 موفق: {successful_pages}/{len(images)}, کل کاراکتر: {total_chars}, میانگین اعتماد: {avg_confidence:.2f}")

        return results