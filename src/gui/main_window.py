#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
رابط گرافیکی ساده شده - حفظ ظاهر، حذف پیچیدگی‌ها
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import logging
import datetime
import json
import csv
from pathlib import Path
from typing import List, Dict, Any

from core.ocr_engine import OCREngine
from core.pdf_processor import PDFProcessor
from utils.logger import get_logger
from utils.config import ConfigManager

logger = get_logger(__name__)


class LogHandler(logging.Handler):
    """Handler برای نمایش لاگ در GUI"""

    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        if self.text_widget:
            msg = self.format(record)
            tag = "ERROR" if record.levelno >= logging.ERROR else "INFO"

            try:
                self.text_widget.config(state='normal')
                self.text_widget.insert(tk.END, f"{msg}\n", tag)
                self.text_widget.see(tk.END)
                self.text_widget.config(state='disabled')
                self.text_widget.update_idletasks()
            except:
                pass


class CustomsOCRApp:
    """کلاس اصلی رابط گرافیکی - ساده شده"""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.root = tk.Tk()

        # تنظیمات اولیه
        self.setup_window()
        self.setup_variables()
        self.setup_components()
        self.create_widgets()
        self.setup_logging()

        logger.info("🎨 رابط گرافیکی ساده آماده است")

    def setup_window(self):
        """تنظیمات پنجره اصلی"""
        self.root.title(f"🚀 سیستم استخراج گمرکی v2.0 - ساده شده")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2c3e50')
        self.root.state('zoomed')

    def setup_variables(self):
        """راه‌اندازی متغیرها - ساده شده"""
        self.selected_files = []
        self.document_type = tk.StringVar(value="وارداتی")
        self.current_results = []
        self.processing_active = False
        self.processing_thread = None

        # تنظیمات ثابت
        self.dpi_var = tk.IntVar(value=600)  # ثابت
        self.use_gpu = tk.BooleanVar(value=True)  # ثابت

    def setup_components(self):
        """راه‌اندازی کامپوننت‌های ساده"""
        try:
            self.ocr_engine = OCREngine(self.config)
            self.pdf_processor = PDFProcessor(self.config)
            logger.info("🔍 کامپوننت‌های اصلی آماده")
        except Exception as e:
            logger.error(f"❌ خطا در راه‌اندازی: {e}")
            messagebox.showerror("خطا", f"خطا در راه‌اندازی:\n{e}")

    def create_widgets(self):
        """ایجاد عناصر رابط - ساده شده"""
        self.create_header()
        self.create_notebook()
        self.create_status_bar()

    def create_header(self):
        """هدر ساده"""
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        header_frame.pack(fill='x', padx=10, pady=5)
        header_frame.pack_propagate(False)

        title_label = tk.Label(header_frame,
                               text="🚀 سیستم استخراج گمرکی - نسخه ساده",
                               font=('Tahoma', 18, 'bold'),
                               bg='#2c3e50', fg='#ecf0f1')
        title_label.pack(side='left', pady=15)

    def create_notebook(self):
        """تب‌های ساده"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # فقط تب‌های ضروری
        self.create_file_selection_tab()
        self.create_processing_tab()
        self.create_results_tab()

    def create_file_selection_tab(self):
        """تب انتخاب فایل - ساده"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📁 انتخاب فایل")

        # انتخاب نوع سند (فقط ظاهری)
        doc_frame = tk.LabelFrame(tab, text="نوع سند گمرکی",
                                  font=('Tahoma', 12, 'bold'))
        doc_frame.pack(fill='x', padx=20, pady=10)

        tk.Radiobutton(doc_frame, text="📥 وارداتی",
                       variable=self.document_type, value="وارداتی",
                       font=('Tahoma', 11)).pack(side='left', padx=20)

        tk.Radiobutton(doc_frame, text="📤 صادراتی",
                       variable=self.document_type, value="صادراتی",
                       font=('Tahoma', 11)).pack(side='left', padx=20)

        # انتخاب فایل
        file_frame = tk.LabelFrame(tab, text="فایل‌های PDF",
                                   font=('Tahoma', 12, 'bold'))
        file_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # دکمه‌ها
        button_frame = tk.Frame(file_frame)
        button_frame.pack(fill='x', pady=10)

        tk.Button(button_frame, text="📁 انتخاب فایل‌ها",
                  command=self.select_files,
                  font=('Tahoma', 11, 'bold'),
                  bg='#3498db', fg='white', padx=20, pady=8).pack(side='left', padx=10)

        tk.Button(button_frame, text="🗑️ پاک کردن",
                  command=self.clear_files,
                  font=('Tahoma', 11, 'bold'),
                  bg='#e74c3c', fg='white', padx=20, pady=8).pack(side='left', padx=10)

        # لیست فایل‌ها
        self.files_listbox = tk.Listbox(file_frame, font=('Tahoma', 10))
        self.files_listbox.pack(fill='both', expand=True, pady=10)

        # آمار و دکمه پردازش
        stats_frame = tk.Frame(file_frame)
        stats_frame.pack(fill='x', pady=5)

        self.files_count_label = tk.Label(stats_frame,
                                          text="📊 فایل انتخاب شده: 0",
                                          font=('Tahoma', 11))
        self.files_count_label.pack(side='left')

        self.start_processing_btn = tk.Button(stats_frame,
                                              text="🚀 شروع پردازش",
                                              command=self.start_processing,
                                              font=('Tahoma', 12, 'bold'),
                                              bg='#27ae60', fg='white',
                                              padx=25, pady=10, state='disabled')
        self.start_processing_btn.pack(side='right', padx=10)

    def create_processing_tab(self):
        """تب پردازش - ساده"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚙️ پردازش")

        # کنترل پردازش
        control_frame = tk.LabelFrame(tab, text="وضعیت پردازش")
        control_frame.pack(fill='x', padx=20, pady=10)

        # نوار پیشرفت
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(control_frame,
                                            variable=self.progress_var,
                                            maximum=100)
        self.progress_bar.pack(fill='x', padx=20, pady=10)

        self.progress_label = tk.Label(control_frame, text="آماده پردازش...")
        self.progress_label.pack()

        # لاگ پردازش
        log_frame = tk.LabelFrame(tab, text="لاگ پردازش")
        log_frame.pack(fill='both', expand=True, padx=20, pady=10)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=20,
                                                  font=('Consolas', 9),
                                                  bg='#2c3e50', fg='#ecf0f1',
                                                  state='disabled')
        self.log_text.pack(fill='both', expand=True, pady=5)

        # تنظیم رنگ‌ها
        self.log_text.tag_configure("INFO", foreground="#3498db")
        self.log_text.tag_configure("ERROR", foreground="#e74c3c")

    def create_results_tab(self):
        """تب نتایج - ساده"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 نتایج")

        # آمار
        stats_frame = tk.Frame(tab)
        stats_frame.pack(fill='x', padx=20, pady=10)

        self.stats_label = tk.Label(stats_frame,
                                    text="📊 آمار: 0 فایل پردازش شده",
                                    font=('Tahoma', 12, 'bold'))
        self.stats_label.pack()

        # جدول نتایج (ساده)
        table_frame = tk.Frame(tab)
        table_frame.pack(fill='both', expand=True, padx=20, pady=10)

        self.results_text = scrolledtext.ScrolledText(table_frame,
                                                      font=('Tahoma', 10),
                                                      wrap='word')
        self.results_text.pack(fill='both', expand=True)

        # دکمه‌های خروجی
        export_frame = tk.Frame(tab)
        export_frame.pack(fill='x', padx=20, pady=10)

        tk.Button(export_frame, text="💾 ذخیره Excel",
                  command=self.export_excel,
                  font=('Tahoma', 11, 'bold'),
                  bg='#27ae60', fg='white', padx=20, pady=8).pack(side='left', padx=10)

        tk.Button(export_frame, text="📄 ذخیره CSV",
                  command=self.export_csv,
                  font=('Tahoma', 11, 'bold'),
                  bg='#9b59b6', fg='white', padx=20, pady=8).pack(side='left', padx=10)

    def create_status_bar(self):
        """نوار وضعیت ساده"""
        self.status_frame = tk.Frame(self.root, bg='#34495e', height=25)
        self.status_frame.pack(fill='x', side='bottom')

        self.status_label = tk.Label(self.status_frame,
                                     text="🔮 آماده پردازش...",
                                     bg='#34495e', fg='#ecf0f1')
        self.status_label.pack(side='left', padx=10, pady=2)

    def setup_logging(self):
        """راه‌اندازی لاگ"""
        if hasattr(self, 'log_text'):
            gui_handler = LogHandler(self.log_text)
            gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s',
                                                       datefmt='%H:%M:%S'))
            logging.getLogger().addHandler(gui_handler)

    # متدهای اصلی پردازش

    def start_processing(self):
        """شروع پردازش ساده"""
        if not self.selected_files:
            messagebox.showwarning("هشدار", "فایلی انتخاب نشده!")
            return

        if self.processing_active:
            messagebox.showinfo("اطلاع", "پردازش در حال انجام است!")
            return

        self.processing_active = True
        self.start_processing_btn.config(state='disabled')
        self.current_results.clear()

        # شروع thread
        self.processing_thread = threading.Thread(target=self._process_files_worker, daemon=True)
        self.processing_thread.start()

        logger.info(f"🚀 شروع پردازش {len(self.selected_files)} فایل")

    def _process_files_worker(self):
        """پردازش فایل‌ها - ساده"""
        try:
            total_files = len(self.selected_files)

            for i, file_path in enumerate(self.selected_files):
                if not self.processing_active:
                    break

                try:
                    # بروزرسانی پیشرفت
                    progress = ((i + 1) / total_files) * 100
                    self.root.after(0, lambda p=progress: self.progress_var.set(p))
                    self.root.after(0, lambda: self.progress_label.config(
                        text=f"پردازش {i + 1}/{total_files}: {Path(file_path).name}"))

                    logger.info(f"📄 پردازش: {Path(file_path).name}")

                    # پردازش اصلی
                    results = self.pdf_processor.process_pdf_pages_individually(file_path)

                    if results:
                        self.current_results.extend(results)
                        logger.info(f"✅ موفق: {len(results)} صفحه")
                    else:
                        logger.warning(f"❌ ناموفق: {Path(file_path).name}")

                except Exception as e:
                    logger.error(f"❌ خطا در {Path(file_path).name}: {e}")

            # اتمام پردازش
            self.root.after(0, self._finish_processing)

        except Exception as e:
            logger.error(f"❌ خطای کلی: {e}")
            self.root.after(0, self._finish_processing)

    def _finish_processing(self):
        """اتمام پردازش"""
        self.processing_active = False
        self.start_processing_btn.config(state='normal')
        self.progress_var.set(100)
        self.progress_label.config(text="✅ پردازش کامل شد!")

        # بروزرسانی نتایج
        self.update_results_display()

        # تغییر به تب نتایج
        self.notebook.select(2)

        logger.info(f"🎉 پردازش کامل: {len(self.current_results)} نتیجه")
        messagebox.showinfo("موفقیت", f"پردازش کامل شد!\n{len(self.current_results)} صفحه پردازش شد")

    def update_results_display(self):
        """بروزرسانی نمایش نتایج"""
        # آمار
        self.stats_label.config(text=f"📊 آمار: {len(self.current_results)} صفحه پردازش شده")

        # نمایش نتایج در text widget
        self.results_text.delete(1.0, tk.END)

        if self.current_results:
            self.results_text.insert(tk.END, "نتایج پردازش:\n" + "=" * 50 + "\n\n")

            for i, result in enumerate(self.current_results, 1):
                self.results_text.insert(tk.END, f"📄 صفحه {i}:\n")
                self.results_text.insert(tk.END, f"   فایل JSON: {result.get('json_file', 'نامشخص')}\n")
                self.results_text.insert(tk.END, f"   طول متن: {result.get('text_length', 0)} کاراکتر\n")
                self.results_text.insert(tk.END, f"   اعتماد: {result.get('confidence', 0):.2f}\n\n")

    # متدهای فایل

    def select_files(self):
        """انتخاب فایل‌ها"""
        files = filedialog.askopenfilenames(
            title="انتخاب فایل‌های PDF",
            filetypes=[("PDF files", "*.pdf")],
            initialdir=Path.home() / "Desktop"
        )

        if files:
            self.selected_files.extend(files)
            self.update_files_display()

    def clear_files(self):
        """پاک کردن فایل‌ها"""
        self.selected_files.clear()
        self.update_files_display()

    def update_files_display(self):
        """بروزرسانی نمایش فایل‌ها"""
        self.files_listbox.delete(0, tk.END)

        for file_path in self.selected_files:
            self.files_listbox.insert(tk.END, Path(file_path).name)

        count = len(self.selected_files)
        self.files_count_label.config(text=f"📊 فایل انتخاب شده: {count}")

        # فعال/غیرفعال کردن دکمه
        state = 'normal' if count > 0 else 'disabled'
        self.start_processing_btn.config(state=state)

    # متدهای خروجی (ساده)

    def export_excel(self):
        """خروجی Excel ساده"""
        if not self.current_results:
            messagebox.showwarning("هشدار", "نتیجه‌ای وجود ندارد!")
            return

        file_path = filedialog.asksaveasfilename(
            title="ذخیره Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )

        if file_path:
            try:
                # ساده: فقط لیست فایل‌های JSON
                import pandas as pd

                data = []
                for result in self.current_results:
                    data.append({
                        'صفحه': result.get('page_number', ''),
                        'فایل JSON': result.get('json_file', ''),
                        'طول متن': result.get('text_length', 0),
                        'اعتماد': result.get('confidence', 0)
                    })

                df = pd.DataFrame(data)
                df.to_excel(file_path, index=False)

                logger.info(f"💾 Excel ذخیره شد: {file_path}")
                messagebox.showinfo("موفقیت", "فایل Excel ذخیره شد!")

            except Exception as e:
                logger.error(f"❌ خطا در Excel: {e}")
                messagebox.showerror("خطا", f"خطا در ذخیره: {e}")

    def export_csv(self):
        """خروجی CSV ساده"""
        if not self.current_results:
            messagebox.showwarning("هشدار", "نتیجه‌ای وجود ندارد!")
            return

        file_path = filedialog.asksaveasfilename(
            title="ذخیره CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )

        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    fieldnames = ['صفحه', 'فایل JSON', 'طول متن', 'اعتماد']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                    writer.writeheader()
                    for result in self.current_results:
                        writer.writerow({
                            'صفحه': result.get('page_number', ''),
                            'فایل JSON': result.get('json_file', ''),
                            'طول متن': result.get('text_length', 0),
                            'اعتماد': result.get('confidence', 0)
                        })

                logger.info(f"📄 CSV ذخیره شد: {file_path}")
                messagebox.showinfo("موفقیت", "فایل CSV ذخیره شد!")

            except Exception as e:
                logger.error(f"❌ خطا در CSV: {e}")
                messagebox.showerror("خطا", f"خطا در ذخیره: {e}")

    def run(self):
        """اجرای برنامه"""
        logger.info("🎯 شروع برنامه ساده")
        self.root.mainloop()
        logger.info("👋 برنامه بسته شد")


if __name__ == "__main__":
    config = ConfigManager()
    app = CustomsOCRApp(config)
    app.run()