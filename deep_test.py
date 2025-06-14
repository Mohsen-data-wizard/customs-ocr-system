#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import re
from typing import Dict, Any, List


class CustomsPatternTester:
    def __init__(self, root):
        self.root = root
        self.root.title("تست الگوهای استخراج گمرکی - نسخه بهبود یافته")
        self.root.geometry("900x700")

        # تنظیم فونت برای پشتیبانی از فارسی
        self.font = ("Tahoma", 10)

        self.create_widgets()
        self.setup_patterns()

    def create_widgets(self):
        # فریم اصلی
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # بخش انتخاب فایل
        file_frame = ttk.LabelFrame(main_frame, text="مرحله 1: انتخاب فایل JSON", padding="10")
        file_frame.pack(fill=tk.X, pady=5)

        self.file_path = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path, width=70, font=self.font).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="انتخاب فایل", command=self.browse_file).pack(side=tk.LEFT)

        # بخش انتخاب فیلد
        field_frame = ttk.LabelFrame(main_frame, text="مرحله 2: انتخاب فیلد برای تست", padding="10")
        field_frame.pack(fill=tk.X, pady=5)

        self.field_var = tk.StringVar()
        self.field_combo = ttk.Combobox(field_frame, textvariable=self.field_var, state="readonly", font=self.font)
        self.field_combo.pack(fill=tk.X, padx=5)

        # بخش الگوها
        pattern_frame = ttk.LabelFrame(main_frame, text="مرحله 3: الگوهای موجود", padding="10")
        pattern_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.pattern_text = tk.Text(pattern_frame, height=10, font=self.font)
        self.pattern_text.pack(fill=tk.BOTH, expand=True)

        # بخش تست و نتایج
        test_frame = ttk.Frame(main_frame)
        test_frame.pack(fill=tk.X, pady=5)

        ttk.Button(test_frame, text="تست الگو", command=self.test_pattern).pack(side=tk.LEFT, padx=5)
        ttk.Button(test_frame, text="تست همه فیلدها", command=self.test_all_fields).pack(side=tk.LEFT, padx=5)

        result_frame = ttk.LabelFrame(main_frame, text="نتایج استخراج", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.result_text = tk.Text(result_frame, height=15, font=self.font)
        self.result_text.pack(fill=tk.BOTH, expand=True)

    def setup_patterns(self):
        """تنظیم الگوهای استخراج بهبود یافته"""
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

        # پر کردن Combobox با نام فیلدها
        self.field_combo['values'] = list(self.patterns.keys())
        if len(self.patterns) > 0:
            self.field_combo.current(0)
            self.update_pattern_display()

        # اتصال رویداد تغییر فیلد
        self.field_combo.bind("<<ComboboxSelected>>", lambda e: self.update_pattern_display())

    def update_pattern_display(self):
        """به روزرسانی نمایش الگوها برای فیلد انتخاب شده"""
        field_name = self.field_var.get()
        if field_name in self.patterns:
            field_config = self.patterns[field_name]
            patterns = field_config["patterns"]

            self.pattern_text.delete(1.0, tk.END)
            self.pattern_text.insert(tk.END, f"توضیحات: {field_config.get('description', 'بدون توضیح')}\n\n")

            for i, pattern in enumerate(patterns, 1):
                self.pattern_text.insert(tk.END, f"الگوی {i}:\n{pattern}\n\n")

    def browse_file(self):
        """انتخاب فایل JSON"""
        file_path = filedialog.askopenfilename(
            title="انتخاب فایل JSON",
            filetypes = (("JSON files", "*.json"), ("All files", "*.*"))
            )
        if file_path:
            self.file_path.set(file_path),
        self.result_text.delete(1.0, tk.END),
        self.result_text.insert(tk.END, f"فایل انتخاب شده: {file_path}\n")

    def test_pattern(self):
        """تست الگوهای انتخاب شده روی فایل JSON"""
        file_path = self.file_path.get()
        field_name = self.field_var.get()

        if not file_path:
            messagebox.showerror("خطا", "لطفاً یک فایل JSON انتخاب کنید")
            return

        if not field_name:
            messagebox.showerror("خطا", "لطفاً یک فیلد برای تست انتخاب کنید")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # استخراج persian_text از ساختار JSON
            persian_text = self._extract_persian_text(data)

            if not persian_text:
                messagebox.showerror("خطا", "فایل JSON حاوی بخش persian_text نیست")
                return

            # تبدیل به متن قابل جستجو
            search_text = '"' + '", "'.join(persian_text) + '"'

            # استخراج فیلد مورد نظر
            result = self._extract_field(search_text, field_name)

            # نمایش نتایج
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"نتایج استخراج برای فیلد '{field_name}':\n")
            self.result_text.insert(tk.END, f"مقدار استخراج شده: {result.get('value', 'یافت نشد')}\n")
            self.result_text.insert(tk.END, f"الگوی مطابق: {result.get('matched_pattern', 'یافت نشد')}\n")
            self.result_text.insert(tk.END, f"\nمقادیر خام:\n{result.get('all_matches', [])}\n")

        except Exception as e:
            messagebox.showerror("خطا", f"خطا در پردازش فایل:\n{str(e)}")

    def test_all_fields(self):
        """تست همه فیلدها به صورت یکجا"""
        file_path = self.file_path.get()

        if not file_path:
            messagebox.showerror("خطا", "لطفاً یک فایل JSON انتخاب کنید")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # استخراج persian_text از ساختار JSON
            persian_text = self._extract_persian_text(data)

            if not persian_text:
                messagebox.showerror("خطا", "فایل JSON حاوی بخش persian_text نیست")
                return

            # تبدیل به متن قابل جستجو
            search_text = '"' + '", "'.join(persian_text) + '"'

            # استخراج تمام فیلدها
            results = {}
            for field_name in self.patterns:
                results[field_name] = self._extract_field(search_text, field_name)

            # نمایش نتایج
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "نتایج استخراج تمام فیلدها:\n\n")

            for field_name, result in results.items():
                self.result_text.insert(tk.END, f"{field_name}: {result.get('value', 'یافت نشد')}\n")

            # نمایش آماری
            total_fields = len(results)
            extracted_fields = sum(1 for r in results.values() if r.get('value') is not None)

            self.result_text.insert(tk.END,
                                    f"\nآمار:\nتعداد فیلدها: {total_fields}\nموفق: {extracted_fields}\nناموفق: {total_fields - extracted_fields}\n")

        except Exception as e:
            messagebox.showerror("خطا", f"خطا در پردازش فایل:\n{str(e)}")

    def _extract_persian_text(self, data: Dict[str, Any]) -> List[str]:
        """استخراج persian_text از ساختار JSON"""
        try:
            # بررسی مسیرهای مختلف برای یافتن persian_text
            paths_to_check = [
                ["patterns", "persian_text"],
                ["structured_data", "patterns", "persian_text"],
                ["customs_extraction", "patterns", "persian_text"]
            ]

            for path in paths_to_check:
                current = data
                for key in path:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        current = None
                        break

                if current and isinstance(current, list):
                    return current

            return []
        except Exception as e:
            print(f"خطا در استخراج persian_text: {e}")
            return []

    def _extract_field(self, text: str, field_name: str) -> Dict[str, Any]:
        """استخراج یک فیلد خاص از متن"""
        if field_name not in self.patterns:
            return {"value": None, "matched_pattern": None, "all_matches": []}

        field_config = self.patterns[field_name]
        patterns = field_config["patterns"]

        best_match = None
        matched_pattern = None
        all_matches = []

        for pattern in patterns:
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    if match.groups():
                        groups = match.groups()
                        all_matches.extend(groups)

                        if not best_match:
                            best_match = groups[0]
                            matched_pattern = pattern
                    else:
                        all_matches.append(match.group(0))

                        if not best_match:
                            best_match = match.group(0)
                            matched_pattern = pattern
            except Exception as e:
                print(f"خطا در پردازش الگو {pattern}: {e}")
                continue

        # تبدیل مقدار به نوع داده مناسب
        converted_value = self._convert_value(best_match, field_config)

        return {
            "value": converted_value,
            "matched_pattern": matched_pattern,
            "all_matches": all_matches[:10]  # حداکثر 10 نتیجه
        }

    def _convert_value(self, value: str, field_config: Dict[str, Any]) -> Any:
        """تبدیل مقدار استخراج شده به نوع داده مناسب"""
        if value is None:
            return None

        field_type = field_config.get("type", "string")

        try:
            # تبدیل اعداد فارسی به انگلیسی
            if isinstance(value, str):
                value = self._persian_to_english(value)

            if field_type == "int":
                # حذف تمام کاراکترهای غیرعددی
                cleaned = re.sub(r'\D', '', value)
                return int(cleaned) if cleaned else None
            elif field_type == "float":
                # حذف تمام کاراکترهای غیرعددی به جز نقطه و ممیز
                cleaned = re.sub(r'[^\d.,]', '', value)
                # جایگزینی ممیز فارسی با نقطه
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


if __name__ == "__main__":
    root = tk.Tk()
    app = CustomsPatternTester(root)
    root.mainloop()