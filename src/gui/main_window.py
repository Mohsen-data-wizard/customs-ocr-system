#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
رابط گرافیکی اصلی برنامه - نسخه کامل با پردازش
Author: Mohsen Data Wizard
Date: 2025-06-10
Version: 2.0.0
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import logging
import datetime
import sys
import time
import json
import csv
import webbrowser
from pathlib import Path
from typing import List, Dict, Any
import pyperclip  # نیاز به نصب: pip install pyperclip



from core.ocr_engine import OCREngine
from core.pdf_processor import PDFProcessor
from core.data_extractor import DataExtractor
from utils.logger import get_logger
from utils.config import ConfigManager
from core.pattern_extractor import CustomsPatternExtractor
logger = get_logger(__name__)

class LogHandler(logging.Handler):
    """Handler برای نمایش لاگ در GUI"""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        if self.text_widget:
            msg = self.format(record)

            # تعیین تگ بر اساس سطح لاگ
            if record.levelno >= logging.ERROR:
                tag = "ERROR"
            elif record.levelno >= logging.WARNING:
                tag = "WARNING"
            elif record.levelno >= logging.INFO:
                tag = "INFO"
            else:
                tag = "DEBUG"

            # اضافه کردن به text widget در thread اصلی
            try:
                self.text_widget.config(state='normal')
                self.text_widget.insert(tk.END, f"{msg}\n", tag)
                self.text_widget.see(tk.END)
                self.text_widget.config(state='disabled')
                self.text_widget.update_idletasks()
            except:
                pass

class CustomsOCRApp:
    """کلاس اصلی رابط گرافیکی"""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.root = tk.Tk()

        # تنظیمات اولیه
        self.setup_window()
        self.setup_variables()
        self.setup_components()
        self.create_widgets()
        self.setup_logging()

        logger.info("🎨 رابط گرافیکی راهاندازی شد")

    def setup_window(self):
        """تنظیمات پنجره اصلی"""
        self.root.title(f"🚀 {self.config.get('app.name')} v{self.config.get('app.version')}")
        self.root.geometry("1800x1100")
        self.root.configure(bg='#2c3e50')
        self.root.state('zoomed')  # تمام صفحه در ویندوز

        # آیکون (در صورت وجود)
        try:
            icon_path = Path("assets/icons/app_icon.ico")
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except:
            pass

    def setup_variables(self):
        """راهاندازی متغیرها"""
        self.selected_files = []
        self.document_type = tk.StringVar(value="وارداتی")
        self.current_results = []
        self.result_queue = queue.Queue()
        self.field_edit_vars = {}
        self.processing_active = False
        self.processing_thread = None
        self.auto_scroll_enabled = True

        # متغیرهای تنظیمات
        self.use_gpu = tk.BooleanVar(value=self.config.get('ocr.easyocr.gpu', True))
        self.dpi_var = tk.IntVar(value=self.config.get('processing.default_dpi', 350))
        self.save_debug = tk.BooleanVar(value=False)
        self.auto_backup = tk.BooleanVar(value=True)
        self.confirm_delete = tk.BooleanVar(value=True)

        # متغیرهای OCR
        self.ocr_confidence = tk.DoubleVar(value=0.7)
        self.tesseract_mode = tk.IntVar(value=3)
        self.preprocessing_enabled = tk.BooleanVar(value=True)

        # آمار پردازش
        self.processing_start_time = None
        self.total_extracted_items = 0

    def setup_components(self):
        """راهاندازی کامپوننتهای اصلی"""
        self.pattern_extractor = CustomsPatternExtractor()
        try:
            self.ocr_engine = OCREngine(self.config)
            logger.info("🔍 موتور OCR با موفقیت راه‌اندازی شد")
        except Exception as e:
            logger.error(f"❌ خطا در راه‌اندازی OCR: {e}")
            messagebox.showerror("خطا", f"خطا در راه‌اندازی موتور OCR:\n{e}")
            sys.exit(1)
        self.pdf_processor = PDFProcessor(self.config)
        data_extractor = DataExtractor(self.pattern_extractor, self.config)  # تغییر این خط
        self.data_extractor = data_extractor


    def setup_logging(self):
        """راه‌اندازی سیستم لاگینگ"""
        if hasattr(self, 'log_text'):
            # اضافه کردن handler سفارشی
            gui_handler = LogHandler(self.log_text)
            gui_handler.setFormatter(logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%H:%M:%S'
            ))

            # اضافه کردن به logger اصلی
            root_logger = logging.getLogger()
            root_logger.addHandler(gui_handler)

            logger.info("📋 سیستم لاگینگ GUI راه‌اندازی شد")

    def create_widgets(self):
        """ایجاد عناصر رابط گرافیکی"""
        self.setup_styles()
        self.create_header()
        self.create_notebook()
        self.create_status_bar()

    def setup_styles(self):
        """تنظیم استایلهای ttk"""
        style = ttk.Style()
        style.theme_use('clam')

        # استایلهای سفارشی
        style.configure('Header.TLabel',
                       font=('Tahoma', 16, 'bold'),
                       background='#2c3e50',
                       foreground='#ecf0f1')

        style.configure('Success.TLabel',
                       font=('Tahoma', 10, 'bold'),
                       background='#27ae60',
                       foreground='white')

        style.configure('CustomButton.TButton',
                       font=('Tahoma', 11, 'bold'),
                       padding=(10, 5))

    def create_header(self):
        """ایجاد هدر برنامه"""
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        header_frame.pack(fill='x', padx=10, pady=5)
        header_frame.pack_propagate(False)

        # عنوان اصلی
        title_text = f"🚀 {self.config.get('app.name')} v{self.config.get('app.version')}"
        title_label = tk.Label(header_frame, text=title_text,
                              font=('Tahoma', 22, 'bold'),
                              bg='#2c3e50', fg='#ecf0f1')
        title_label.pack(side='left', pady=15)

        # نمایش کاربر فعلی
        user_info = f"کاربر: Mohsen-data-wizard | تاریخ: 2025-06-10"
        user_label = tk.Label(header_frame, text=user_info,
                             font=('Tahoma', 10),
                             bg='#2c3e50', fg='#bdc3c7')
        user_label.pack(side='right', pady=20, padx=20)

    def create_notebook(self):
        """ایجاد تبهای اصلی"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # تبهای مختلف
        self.create_file_selection_tab()
        self.create_processing_tab()
        self.create_edit_tab()
        self.create_results_tab()
        self.create_patterns_tab()
        self.create_settings_tab()
        self.create_about_tab()

    def create_file_selection_tab(self):
        """تب انتخاب فایلها"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📁 انتخاب فایلها")

        # فریم نوع سند - بهبود یافته
        doc_frame = tk.LabelFrame(tab, text="نوع اسناد گمرکی",
                                 font=('Tahoma', 12, 'bold'),
                                 bg='#ecf0f1', fg='#2c3e50',
                                 padx=20, pady=20)
        doc_frame.pack(fill='x', padx=20, pady=10)

        # فریم رادیو باتن‌ها با بهبود بصری
        radio_frame = tk.Frame(doc_frame, bg='#ecf0f1')
        radio_frame.pack(fill='x', pady=10)

        # رادیو باتن وارداتی با آیکون بهتر
        import_frame = tk.Frame(radio_frame, bg='#d5f4e6', relief='ridge', bd=2)
        import_frame.pack(side='left', padx=20, pady=10, fill='both', expand=True)

        import_radio = tk.Radiobutton(import_frame,
                                     text="📥 اسناد وارداتی (Import Documents)\n💰 واردات کالا از خارج به داخل",
                                     variable=self.document_type, value="وارداتی",
                                     font=('Tahoma', 11, 'bold'),
                                     bg='#d5f4e6', fg='#27ae60',
                                     selectcolor='#27ae60', anchor='w',
                                     justify='left', padx=15, pady=15,
                                     command=self.on_document_type_change)
        import_radio.pack(fill='both', expand=True)

        # رادیو باتن صادراتی با آیکون بهتر
        export_frame = tk.Frame(radio_frame, bg='#ffeaa7', relief='ridge', bd=2)
        export_frame.pack(side='left', padx=20, pady=10, fill='both', expand=True)

        export_radio = tk.Radiobutton(export_frame,
                                     text="📤 اسناد صادراتی (Export Documents)\n🌍 صادرات کالا از داخل به خارج",
                                     variable=self.document_type, value="صادراتی",
                                     font=('Tahoma', 11, 'bold'),
                                     bg='#ffeaa7', fg='#e67e22',
                                     selectcolor='#e67e22', anchor='w',
                                     justify='left', padx=15, pady=15,
                                     command=self.on_document_type_change)
        export_radio.pack(fill='both', expand=True)

        # فریم انتخاب فایل
        file_frame = tk.LabelFrame(tab, text="مدیریت فایلهای PDF",
                                  font=('Tahoma', 12, 'bold'),
                                  bg='#ecf0f1', fg='#2c3e50',
                                  padx=15, pady=15)
        file_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # دکمههای کنترل
        button_frame = tk.Frame(file_frame, bg='#ecf0f1')
        button_frame.pack(fill='x', pady=10)

        # دکمه انتخاب فایلها
        select_btn = tk.Button(button_frame, text="📁 انتخاب فایلهای PDF",
                              command=self.select_files,
                              font=('Tahoma', 11, 'bold'),
                              bg='#3498db', fg='white',
                              relief='flat', padx=25, pady=10,
                              cursor='hand2')
        select_btn.pack(side='left', padx=10)

        # دکمه انتخاب پوشه
        folder_btn = tk.Button(button_frame, text="📂 انتخاب پوشه",
                              command=self.select_folder,
                              font=('Tahoma', 11, 'bold'),
                              bg='#9b59b6', fg='white',
                              relief='flat', padx=25, pady=10,
                              cursor='hand2')
        folder_btn.pack(side='left', padx=10)

        # دکمه پاک کردن
        clear_btn = tk.Button(button_frame, text="🗑️ پاک کردن لیست",
                             command=self.clear_files,
                             font=('Tahoma', 11, 'bold'),
                             bg='#e74c3c', fg='white',
                             relief='flat', padx=25, pady=10,
                             cursor='hand2')
        clear_btn.pack(side='left', padx=10)

        # لیست فایلها
        list_frame = tk.Frame(file_frame, bg='#ecf0f1')
        list_frame.pack(fill='both', expand=True, pady=10)

        # Treeview برای نمایش بهتر فایلها
        columns = ('نام فایل', 'اندازه', 'تاریخ تغییر', 'مسیر')
        self.files_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=12)

        # تنظیم ستونها
        self.files_tree.heading('#0', text='#', anchor='w')
        self.files_tree.heading('نام فایل', text='نام فایل', anchor='w')
        self.files_tree.heading('اندازه', text='اندازه', anchor='center')
        self.files_tree.heading('تاریخ تغییر', text='تاریخ تغییر', anchor='center')
        self.files_tree.heading('مسیر', text='مسیر', anchor='w')

        self.files_tree.column('#0', width=50)
        self.files_tree.column('نام فایل', width=250)
        self.files_tree.column('اندازه', width=100)
        self.files_tree.column('تاریخ تغییر', width=150)
        self.files_tree.column('مسیر', width=350)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.files_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient='horizontal', command=self.files_tree.xview)

        self.files_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # پکیج کردن
        self.files_tree.pack(side='left', fill='both', expand=True)
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')

        # آمار فایلها
        stats_frame = tk.Frame(file_frame, bg='#ecf0f1')
        stats_frame.pack(fill='x', pady=5)

        self.files_count_label = tk.Label(stats_frame,
                                         text="📊 فایل انتخاب شده: 0 | حجم کل: 0 MB",
                                         font=('Tahoma', 11, 'bold'),
                                         bg='#ecf0f1', fg='#2c3e50')
        self.files_count_label.pack(side='left')

        # دکمه شروع پردازش
        self.start_processing_btn = tk.Button(stats_frame,
                                             text="🚀 شروع پردازش",
                                             command=self.start_processing,
                                             font=('Tahoma', 12, 'bold'),
                                             bg='#27ae60', fg='white',
                                             relief='flat', padx=30, pady=10,
                                             cursor='hand2', state='disabled')
        self.start_processing_btn.pack(side='right', padx=10)

    def on_document_type_change(self):
        """تغییر نوع سند گمرکی - بهبود یافته"""
        doc_type = self.document_type.get()
        logger.info(f"📋 نوع سند تغییر کرد به: {doc_type}")

        # بروزرسانی الگوهای regex بر اساس نوع سند
        if hasattr(self, 'pattern_manager'):
            try:
                # بارگذاری مجدد الگوها
                patterns = self.pattern_extractor.CustomsPatternExtractor(doc_type)  # درست
                logger.info(f"✅ الگوها بارگذاری شد: {len(patterns)} فیلد")
            except Exception as e:
                logger.error(f"❌ خطا در بارگذاری الگوها: {e}")

        # پیام به کاربر
        status_msg = f"✅ الگوهای استخراج برای اسناد {doc_type} تنظیم شد"
        if hasattr(self, 'status_label'):
            self.status_label.config(text=status_msg)

        # بروزرسانی UI در صورت نیاز
        self.update_ui_for_document_type(doc_type)

        # ذخیره در کانفیگ
        try:
            self.config.set('app.last_document_type', doc_type)
        except:
            pass

    def update_ui_for_document_type(self, doc_type: str):
        """بروزرسانی رابط بر اساس نوع سند"""
        try:
            # تغییر رنگ تم بر اساس نوع سند
            if doc_type == "وارداتی":
                theme_color = "#27ae60"  # سبز
                accent_color = "#2ecc71"
            else:
                theme_color = "#e74c3c"  # قرمز
                accent_color = "#c0392b"

            # اگر دکمه پردازش موجوده، رنگش رو تغییر بده
            if hasattr(self, 'start_processing_btn'):
                self.start_processing_btn.config(bg=theme_color)

            logger.info(f"🎨 رنگ تم برای {doc_type} تنظیم شد: {theme_color}")

        except Exception as e:
            logger.error(f"❌ خطا در بروزرسانی UI: {e}")

    def create_processing_tab(self):
        """تب پردازش"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚙️ پردازش")

        # فریم کنترل
        control_frame = tk.LabelFrame(tab, text="کنترل پردازش",
                                     font=('Tahoma', 12, 'bold'),
                                     bg='#ecf0f1', fg='#2c3e50',
                                     padx=15, pady=15)
        control_frame.pack(fill='x', padx=20, pady=10)

        # دکمههای کنترل
        buttons_frame = tk.Frame(control_frame, bg='#ecf0f1')
        buttons_frame.pack(fill='x', pady=10)

        self.start_btn = tk.Button(buttons_frame, text="🚀 شروع پردازش دستهای",
                                  command=self.start_batch_processing,
                                  font=('Tahoma', 12, 'bold'),
                                  bg='#27ae60', fg='white',
                                  relief='flat', padx=30, pady=12,
                                  cursor='hand2', state='disabled')
        self.start_btn.pack(side='left', padx=10)

        self.pause_btn = tk.Button(buttons_frame, text="⏸️ مکث",
                                  command=self.pause_processing,
                                  font=('Tahoma', 12, 'bold'),
                                  bg='#f39c12', fg='white',
                                  relief='flat', padx=30, pady=12,
                                  cursor='hand2', state='disabled')
        self.pause_btn.pack(side='left', padx=10)

        self.stop_btn = tk.Button(buttons_frame, text="⏹️ توقف",
                                 command=self.stop_processing,
                                 font=('Tahoma', 12, 'bold'),
                                 bg='#e74c3c', fg='white',
                                 relief='flat', padx=30, pady=12,
                                 cursor='hand2', state='disabled')
        self.stop_btn.pack(side='left', padx=10)

        # نوار پیشرفت
        progress_frame = tk.Frame(control_frame, bg='#ecf0f1')
        progress_frame.pack(fill='x', pady=10)

        tk.Label(progress_frame, text="پیشرفت کلی:",
                font=('Tahoma', 10, 'bold'),
                bg='#ecf0f1', fg='#2c3e50').pack(anchor='w')

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame,
                                           variable=self.progress_var,
                                           maximum=100, length=500)
        self.progress_bar.pack(fill='x', pady=5)

        self.progress_label = tk.Label(progress_frame,
                                      text="آماده پردازش...",
                                      font=('Tahoma', 10),
                                      bg='#ecf0f1', fg='#7f8c8d')
        self.progress_label.pack(anchor='w')

        # نوار پیشرفت فایل فعلی
        current_frame = tk.Frame(progress_frame, bg='#ecf0f1')
        current_frame.pack(fill='x', pady=5)

        tk.Label(current_frame, text="فایل فعلی:",
                font=('Tahoma', 10, 'bold'),
                bg='#ecf0f1', fg='#2c3e50').pack(anchor='w')

        self.current_progress_var = tk.DoubleVar()
        self.current_progress_bar = ttk.Progressbar(current_frame,
                                                   variable=self.current_progress_var,
                                                   maximum=100, length=500)
        self.current_progress_bar.pack(fill='x', pady=5)

        self.current_file_label = tk.Label(current_frame,
                                          text="",
                                          font=('Tahoma', 10),
                                          bg='#ecf0f1', fg='#7f8c8d')
        self.current_file_label.pack(anchor='w')

        # لاگ پردازش
        log_frame = tk.LabelFrame(tab, text="لاگ پردازش زنده",
                                 font=('Tahoma', 12, 'bold'),
                                 bg='#ecf0f1', fg='#2c3e50',
                                 padx=15, pady=15)
        log_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Text widget با رنگبندی
        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                 height=25, width=100,
                                                 font=('Consolas', 9),
                                                 bg='#2c3e50', fg='#ecf0f1',
                                                 wrap='word',
                                                 state='disabled')
        self.log_text.pack(fill='both', expand=True, pady=5)

        # تنظیم رنگها برای انواع لاگ
        self.log_text.tag_configure("INFO", foreground="#3498db")
        self.log_text.tag_configure("SUCCESS", foreground="#27ae60")
        self.log_text.tag_configure("WARNING", foreground="#f39c12")
        self.log_text.tag_configure("ERROR", foreground="#e74c3c")
        self.log_text.tag_configure("DEBUG", foreground="#95a5a6")

        # دکمههای لاگ
        log_buttons_frame = tk.Frame(log_frame, bg='#ecf0f1')
        log_buttons_frame.pack(fill='x', pady=5)

        clear_log_btn = tk.Button(log_buttons_frame, text="🗑️ پاک کردن لاگ",
                                 command=self.clear_log,
                                 font=('Tahoma', 10),
                                 bg='#95a5a6', fg='white',
                                 relief='flat', padx=15, pady=5,
                                 cursor='hand2')
        clear_log_btn.pack(side='left', padx=5)

        save_log_btn = tk.Button(log_buttons_frame, text="💾 ذخیره لاگ",
                                command=self.save_log,
                                font=('Tahoma', 10),
                                bg='#34495e', fg='white',
                                relief='flat', padx=15, pady=5,
                                cursor='hand2')
        save_log_btn.pack(side='left', padx=5)

        auto_scroll_btn = tk.Button(log_buttons_frame, text="📜 Auto Scroll",
                                   command=self.toggle_auto_scroll,
                                   font=('Tahoma', 10),
                                   bg='#3498db', fg='white',
                                   relief='flat', padx=15, pady=5,
                                   cursor='hand2')
        auto_scroll_btn.pack(side='left', padx=5)

    def create_edit_tab(self):
        """تب ویرایش فیلدها"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="✏️ ویرایش نتایج")

        # راهنمای ویرایش
        guide_frame = tk.LabelFrame(tab, text="راهنمای ویرایش",
                                   font=('Tahoma', 12, 'bold'),
                                   bg='#ecf0f1', fg='#2c3e50',
                                   padx=15, pady=10)
        guide_frame.pack(fill='x', padx=20, pady=10)

        guide_text = """
📝 نحوه ویرایش:
• پس از پردازش فیلدهای استخراج شده در اینجا نمایش داده میشود
• میتوانید مقادیر را مستقیما ویرایش کنید
• بر روی "ذخیره تغییرات" کلیک کنید تا تغییرات اعمال شود
• فیلدهای خالی با رنگ قرمز نمایش داده میشود
        """

        guide_label = tk.Label(guide_frame, text=guide_text.strip(),
                              font=('Tahoma', 10), bg='#ecf0f1', fg='#2c3e50',
                              justify='left')
        guide_label.pack(anchor='w', padx=10, pady=5)

        # دکمههای کنترل ویرایش
        edit_control_frame = tk.Frame(tab, bg='#ecf0f1')
        edit_control_frame.pack(fill='x', padx=20, pady=10)

        refresh_edit_btn = tk.Button(edit_control_frame, text="🔄 بارگذاری مجدد",
                                    command=self.refresh_edit_fields,
                                    font=('Tahoma', 11, 'bold'),
                                    bg='#3498db', fg='white',
                                    relief='flat', padx=20, pady=8,
                                    cursor='hand2')
        refresh_edit_btn.pack(side='left', padx=10)

        save_edits_btn = tk.Button(edit_control_frame, text="💾 ذخیره تغییرات",
                                  command=self.save_edits,
                                  font=('Tahoma', 11, 'bold'),
                                  bg='#27ae60', fg='white',
                                  relief='flat', padx=20, pady=8,
                                  cursor='hand2')
        save_edits_btn.pack(side='left', padx=10)

        validate_btn = tk.Button(edit_control_frame, text="✅ اعتبارسنجی",
                                command=self.validate_data,
                                font=('Tahoma', 11, 'bold'),
                                bg='#f39c12', fg='white',
                                relief='flat', padx=20, pady=8,
                                cursor='hand2')
        validate_btn.pack(side='left', padx=10)

        # فریم اصلی ویرایش با Scrollbar
        edit_main_frame = tk.Frame(tab, bg='#ecf0f1')
        edit_main_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Canvas برای scroll
        self.edit_canvas = tk.Canvas(edit_main_frame, bg='#ecf0f1')
        edit_scrollbar = ttk.Scrollbar(edit_main_frame, orient="vertical",
                                      command=self.edit_canvas.yview)

        self.edit_scrollable_frame = tk.Frame(self.edit_canvas, bg='#ecf0f1')

        self.edit_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.edit_canvas.configure(scrollregion=self.edit_canvas.bbox("all"))
        )

        self.edit_canvas.create_window((0, 0), window=self.edit_scrollable_frame, anchor="nw")
        self.edit_canvas.configure(yscrollcommand=edit_scrollbar.set)

        self.edit_canvas.pack(side="left", fill="both", expand=True)
        edit_scrollbar.pack(side="right", fill="y")

        # پیام اولیه
        self.edit_placeholder = tk.Label(self.edit_scrollable_frame,
                                        text="📋 پس از پردازش فایلها فیلدهای ویرایش در اینجا نمایش داده میشود",
                                        font=('Tahoma', 12, 'italic'),
                                        bg='#ecf0f1', fg='#7f8c8d')
        self.edit_placeholder.pack(pady=50)

    def create_results_tab(self):
        """تب نتایج"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 نتایج و خروجی")

        # آمار کلی
        stats_frame = tk.LabelFrame(tab, text="آمار کلی استخراج",
                                   font=('Tahoma', 12, 'bold'),
                                   bg='#ecf0f1', fg='#2c3e50',
                                   padx=15, pady=15)
        stats_frame.pack(fill='x', padx=20, pady=10)

        # فریم آمار با 4 ستون
        stats_grid = tk.Frame(stats_frame, bg='#ecf0f1')
        stats_grid.pack(fill='x', pady=10)

        # آمار فایلها
        self.stats_files = tk.Label(stats_grid, text="📁 فایلها: 0",
                                   font=('Tahoma', 11, 'bold'),
                                   bg='#3498db', fg='white',
                                   padx=15, pady=10, relief='raised')
        self.stats_files.grid(row=0, column=0, padx=10, pady=5, sticky='ew')

        # آمار کالاها
        self.stats_items = tk.Label(stats_grid, text="📦 کالاها: 0",
                                   font=('Tahoma', 11, 'bold'),
                                   bg='#27ae60', fg='white',
                                   padx=15, pady=10, relief='raised')
        self.stats_items.grid(row=0, column=1, padx=10, pady=5, sticky='ew')

        # نرخ موفقیت
        self.stats_success = tk.Label(stats_grid, text="✅ موفقیت: 0%",
                                     font=('Tahoma', 11, 'bold'),
                                     bg='#e67e22', fg='white',
                                     padx=15, pady=10, relief='raised')
        self.stats_success.grid(row=0, column=2, padx=10, pady=5, sticky='ew')

        # زمان پردازش
        self.stats_time = tk.Label(stats_grid, text="⏱️ زمان: 00:00",
                                  font=('Tahoma', 11, 'bold'),
                                  bg='#9b59b6', fg='white',
                                  padx=15, pady=10, relief='raised')
        self.stats_time.grid(row=0, column=3, padx=10, pady=5, sticky='ew')

        # تنظیم وزن ستونها
        for i in range(4):
            stats_grid.grid_columnconfigure(i, weight=1)

        # جدول نتایج
        table_frame = tk.LabelFrame(tab, text="جدول نتایج استخراج شده",
                                   font=('Tahoma', 12, 'bold'),
                                   bg='#ecf0f1', fg='#2c3e50',
                                   padx=15, pady=15)
        table_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # فریم جدول
        tree_frame = tk.Frame(table_frame, bg='#ecf0f1')
        tree_frame.pack(fill='both', expand=True)

        # تعریف ستونها (ترتیب راستچین)
        self.result_columns = [
            'شماره_کوتاژ', 'شرح_کالا', 'کد_کالا', 'تعداد_بسته', 'نوع_بسته',
            'نوع_ارز', 'مبلغ_کل_فاکتور', 'نرخ_ارز', 'وزن_خالص', 'تعداد_واحد_کالا',
            'نوع_معامله', 'ارزش_گمرکی_قلم_کالا', 'کشور_طرف_معامله', 'بیمه', 'کرایه',
            'مبلغ_حقوق_ورودی', 'مبلغ_مالیات_بر_ارزش_افزوده', 'جمع_حقوق_و_عوارض_قلم',
            'شماره_صفحه'
        ]

        # Treeview
        self.results_tree = ttk.Treeview(tree_frame,
                                        columns=self.result_columns,
                                        show='tree headings',
                                        height=18)

        # تنظیم ستونها
        self.results_tree.heading('#0', text='ردیف', anchor='center')
        self.results_tree.column('#0', width=60, anchor='center')

        for col in self.result_columns:
            display_name = col.replace('_', ' ')
            self.results_tree.heading(col, text=display_name, anchor='center')

            # تنظیم عرض بر اساس نوع فیلد
            if col == 'شرح_کالا':
                width = 250
            elif col in ['مبلغ_کل_فاکتور', 'ارزش_گمرکی_قلم_کالا', 'مبلغ_حقوق_ورودی',
                        'مبلغ_مالیات_بر_ارزش_افزوده', 'جمع_حقوق_و_عوارض_قلم']:
                width = 150
            elif col in ['شماره_کوتاژ', 'کد_کالا']:
                width = 120
            else:
                width = 100

            self.results_tree.column(col, width=width, anchor='center', minwidth=80)

        # Scrollbars
        results_v_scroll = ttk.Scrollbar(tree_frame, orient='vertical',
                                        command=self.results_tree.yview)
        results_h_scroll = ttk.Scrollbar(tree_frame, orient='horizontal',
                                        command=self.results_tree.xview)

        self.results_tree.configure(yscrollcommand=results_v_scroll.set,
                                   xscrollcommand=results_h_scroll.set)

        # پکیج کردن
        results_v_scroll.pack(side='right', fill='y')
        results_h_scroll.pack(side='bottom', fill='x')
        self.results_tree.pack(side='left', fill='both', expand=True)

        # رنگآمیزی ردیفها
        self.results_tree.tag_configure('complete', background='#d5f4e6')
        self.results_tree.tag_configure('incomplete', background='#ffeaa7')
        self.results_tree.tag_configure('error', background='#fab1a0')

        # دکمههای خروجی
        export_frame = tk.Frame(tab, bg='#ecf0f1')
        export_frame.pack(fill='x', padx=20, pady=15)

        # ردیف اول دکمهها
        export_row1 = tk.Frame(export_frame, bg='#ecf0f1')
        export_row1.pack(fill='x', pady=5)

        excel_btn = tk.Button(export_row1, text="💾 ذخیره Excel زیبا",
                             command=self.export_excel,
                             font=('Tahoma', 12, 'bold'),
                             bg='#27ae60', fg='white',
                             relief='flat', padx=25, pady=10,
                             cursor='hand2')
        excel_btn.pack(side='left', padx=10)

        csv_btn = tk.Button(export_row1, text="📄 خروجی CSV",
                           command=self.export_csv,
                           font=('Tahoma', 12, 'bold'),
                           bg='#9b59b6', fg='white',
                           relief='flat', padx=25, pady=10,
                           cursor='hand2')
        csv_btn.pack(side='left', padx=10)

        json_btn = tk.Button(export_row1, text="📋 خروجی JSON",
                            command=self.export_json,
                            font=('Tahoma', 12, 'bold'),
                            bg='#34495e', fg='white',
                            relief='flat', padx=25, pady=10,
                            cursor='hand2')
        json_btn.pack(side='left', padx=10)

        # ردیف دوم دکمهها
        export_row2 = tk.Frame(export_frame, bg='#ecf0f1')
        export_row2.pack(fill='x', pady=5)

        template_btn = tk.Button(export_row2, text="📄 تولید گزارش",
                                command=self.generate_report,
                                font=('Tahoma', 12, 'bold'),
                                bg='#e67e22', fg='white',
                                relief='flat', padx=25, pady=10,
                                cursor='hand2')
        template_btn.pack(side='left', padx=10)

        print_btn = tk.Button(export_row2, text="🖨️ چاپ نتایج",
                             command=self.print_results,
                             font=('Tahoma', 12, 'bold'),
                             bg='#95a5a6', fg='white',
                             relief='flat', padx=25, pady=10,
                             cursor='hand2')
        print_btn.pack(side='left', padx=10)

        email_btn = tk.Button(export_row2, text="📧 ارسال ایمیل",
                             command=self.email_results,
                             font=('Tahoma', 12, 'bold'),
                             bg='#16a085', fg='white',
                             relief='flat', padx=25, pady=10,
                             cursor='hand2')
        email_btn.pack(side='left', padx=10)

    def show_raw_text(self):
        """نمایش متن خام استخراج شده"""
        if not self.selected_files:
            messagebox.showwarning("هشدار", "ابتدا یک فایل انتخاب کنید!")
            return

        try:
            file_path = self.selected_files[0]
            image = self.pdf_processor.convert_to_image(file_path, 0)

            if image is not None:
                result = self.ocr_engine.extract_text(image)
                raw_text = result.get('text', '')

                if raw_text:
                    # نمایش در پنجره جدید
                    debug_window = tk.Toplevel(self.root)
                    debug_window.title("متن خام استخراج شده")
                    debug_window.geometry("800x600")

                    text_widget = scrolledtext.ScrolledText(debug_window,
                                                            font=('Consolas', 10),
                                                            wrap='word')
                    text_widget.pack(fill='both', expand=True, padx=10, pady=10)
                    text_widget.insert('1.0', raw_text)

                    logger.info(f"🔍 متن خام: {len(raw_text)} کاراکتر")
                else:
                    messagebox.showwarning("هشدار", "هیچ متنی استخراج نشد!")
            else:
                messagebox.showerror("خطا", "تبدیل PDF ناموفق!")

        except Exception as e:
            logger.error(f"❌ خطا در نمایش متن خام: {e}")
            messagebox.showerror("خطا", f"خطا: {e}")

    def save_raw_text_to_file(self):
        """ذخیره متن خام در فایل"""
        try:
            if hasattr(self, 'raw_text') and self.raw_text:
                from tkinter import filedialog

                file_path = filedialog.asksaveasfilename(
                    title="ذخیره متن خام",
                    defaultextension=".txt",
                    filetypes=[
                        ("فایل متنی", "*.txt"),
                        ("همه فایل‌ها", "*.*")
                    ]
                )

                if file_path:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(self.raw_text)
                    self.show_status_message(f"✅ متن خام ذخیره شد: {file_path}", "success")
            else:
                self.show_status_message("❌ متن خامی برای ذخیره وجود ندارد", "warning")
        except Exception as e:
            logger.error(f"خطا در ذخیره: {e}")
            self.show_status_message(f"❌ خطا در ذخیره: {e}", "error")

    def create_patterns_tab(self):
        """تب الگوهای regex - کامل"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🎯 الگوهای Regex")

        # فریم راهنما
        guide_frame = tk.LabelFrame(tab, text="راهنمای الگوهای Regex",
                                   font=('Tahoma', 12, 'bold'),
                                   bg='#ecf0f1', fg='#2c3e50',
                                   padx=15, pady=10)
        guide_frame.pack(fill='x', padx=20, pady=10)

        guide_text = """
🎯 الگوهای Regex برای استخراج فیلدهای گمرکی:
• شماره کوتاژ: الگوی شناسایی شماره کوتاژ در اسناد
• کد کالا: الگوی شناسایی کد کالا (HS Code)
• مبالغ مالی: الگوی شناسایی مبالغ با واحدهای مختلف
• تاریخ: الگوی شناسایی تاریخ‌های مختلف
• کشورها: الگوی شناسایی نام کشورها
        """

        guide_label = tk.Label(guide_frame, text=guide_text.strip(),
                              font=('Tahoma', 10), bg='#ecf0f1', fg='#2c3e50',
                              justify='left')
        guide_label.pack(anchor='w', padx=10, pady=5)

        # فریم کنترل الگوها
        control_frame = tk.Frame(tab, bg='#ecf0f1')
        control_frame.pack(fill='x', padx=20, pady=10)

        load_patterns_btn = tk.Button(control_frame, text="🔄 بارگذاری الگوها",
                                     command=self.load_patterns,
                                     font=('Tahoma', 11, 'bold'),
                                     bg='#3498db', fg='white',
                                     relief='flat', padx=20, pady=8,
                                     cursor='hand2')
        load_patterns_btn.pack(side='left', padx=10)

        save_patterns_btn = tk.Button(control_frame, text="💾 ذخیره الگوها",
                                     command=self.save_patterns,
                                     font=('Tahoma', 11, 'bold'),
                                     bg='#27ae60', fg='white',
                                     relief='flat', padx=20, pady=8,
                                     cursor='hand2')
        save_patterns_btn.pack(side='left', padx=10)

        test_patterns_btn = tk.Button(control_frame, text="🧪 تست الگوها",
                                     command=self.test_patterns,
                                     font=('Tahoma', 11, 'bold'),
                                     bg='#f39c12', fg='white',
                                     relief='flat', padx=20, pady=8,
                                     cursor='hand2')
        test_patterns_btn.pack(side='left', padx=10)

        # جدول الگوها
        patterns_frame = tk.LabelFrame(tab, text="الگوهای فعلی",
                                      font=('Tahoma', 12, 'bold'),
                                      bg='#ecf0f1', fg='#2c3e50',
                                      padx=15, pady=15)
        patterns_frame.pack(fill='both', expand=True, padx=20, pady=10)
        debug_text_btn = tk.Button(control_frame, text="🔍 نمایش متن خام",
                                   command=self.show_raw_text,
                                   font=('Tahoma', 11, 'bold'),
                                   bg='#e74c3c', fg='white',
                                   relief='flat', padx=20, pady=8,
                                   cursor='hand2')
        debug_text_btn.pack(side='left', padx=10)

        # Treeview برای نمایش الگوها
        patterns_columns = ('فیلد', 'الگو', 'توضیحات', 'وضعیت')
        self.patterns_tree = ttk.Treeview(patterns_frame,
                                         columns=patterns_columns,
                                         show='tree headings',
                                         height=15)

        # تنظیم ستونها
        self.patterns_tree.heading('#0', text='#', anchor='center')
        self.patterns_tree.heading('فیلد', text='فیلد', anchor='center')
        self.patterns_tree.heading('الگو', text='الگوی Regex', anchor='center')
        self.patterns_tree.heading('توضیحات', text='توضیحات', anchor='center')
        self.patterns_tree.heading('وضعیت', text='وضعیت', anchor='center')

        self.patterns_tree.column('#0', width=50)
        self.patterns_tree.column('فیلد', width=150)
        self.patterns_tree.column('الگو', width=400)
        self.patterns_tree.column('توضیحات', width=250)
        self.patterns_tree.column('وضعیت', width=100)

        # Scrollbars
        patterns_v_scroll = ttk.Scrollbar(patterns_frame, orient='vertical',
                                         command=self.patterns_tree.yview)
        patterns_h_scroll = ttk.Scrollbar(patterns_frame, orient='horizontal',
                                         command=self.patterns_tree.xview)

        self.patterns_tree.configure(yscrollcommand=patterns_v_scroll.set,
                                    xscrollcommand=patterns_h_scroll.set)

        # پکیج کردن
        patterns_v_scroll.pack(side='right', fill='y')
        patterns_h_scroll.pack(side='bottom', fill='x')
        self.patterns_tree.pack(side='left', fill='both', expand=True)

        # بارگذاری الگوهای پیش‌فرض
        self.load_default_patterns()

    def create_settings_tab(self):
        """تب تنظیمات - کامل"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚙️ تنظیمات")

        # ایجاد notebook فرعی
        settings_notebook = ttk.Notebook(tab)
        settings_notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # تب تنظیمات عمومی
        general_tab = ttk.Frame(settings_notebook)
        settings_notebook.add(general_tab, text="🔧 عمومی")

        # فریم تنظیمات فایل
        file_settings_frame = tk.LabelFrame(general_tab, text="تنظیمات فایل",
                                           font=('Tahoma', 12, 'bold'),
                                           bg='#ecf0f1', fg='#2c3e50',
                                           padx=15, pady=15)
        file_settings_frame.pack(fill='x', padx=20, pady=10)

        # DPI تنظیمات
        dpi_frame = tk.Frame(file_settings_frame, bg='#ecf0f1')
        dpi_frame.pack(fill='x', pady=5)

        tk.Label(dpi_frame, text="رزولوشن PDF (DPI):",
                font=('Tahoma', 11), bg='#ecf0f1', fg='#2c3e50').pack(side='left')

        dpi_scale = tk.Scale(dpi_frame, from_=150, to=600,
                            variable=self.dpi_var, orient='horizontal',
                            font=('Tahoma', 10), bg='#ecf0f1',
                            length=300)
        dpi_scale.pack(side='left', padx=20)

        tk.Label(dpi_frame, text="(بالاتر = کیفیت بهتر، سرعت کمتر)",
                font=('Tahoma', 9, 'italic'), bg='#ecf0f1', fg='#7f8c8d').pack(side='left')

        # تنظیمات backup
        backup_frame = tk.Frame(file_settings_frame, bg='#ecf0f1')
        backup_frame.pack(fill='x', pady=5)

        backup_check = tk.Checkbutton(backup_frame, text="پشتیبان‌گیری خودکار از نتایج",
                                     variable=self.auto_backup,
                                     font=('Tahoma', 11), bg='#ecf0f1', fg='#2c3e50')
        backup_check.pack(side='left')

        # تایید حذف
        confirm_frame = tk.Frame(file_settings_frame, bg='#ecf0f1')
        confirm_frame.pack(fill='x', pady=5)

        confirm_check = tk.Checkbutton(confirm_frame, text="تایید قبل از حذف",
                                      variable=self.confirm_delete,
                                      font=('Tahoma', 11), bg='#ecf0f1', fg='#2c3e50')
        confirm_check.pack(side='left')

        # تب تنظیمات OCR
        ocr_tab = ttk.Frame(settings_notebook)
        settings_notebook.add(ocr_tab, text="🔍 OCR")

        # تنظیمات EasyOCR
        easyocr_frame = tk.LabelFrame(ocr_tab, text="تنظیمات EasyOCR",
                                     font=('Tahoma', 12, 'bold'),
                                     bg='#ecf0f1', fg='#2c3e50',
                                     padx=15, pady=15)
        easyocr_frame.pack(fill='x', padx=20, pady=10)

        # GPU
        gpu_frame = tk.Frame(easyocr_frame, bg='#ecf0f1')
        gpu_frame.pack(fill='x', pady=5)

        gpu_check = tk.Checkbutton(gpu_frame, text="استفاده از GPU (سرعت بالاتر)",
                                  variable=self.use_gpu,
                                  font=('Tahoma', 11), bg='#ecf0f1', fg='#2c3e50')
        gpu_check.pack(side='left')

        # Confidence threshold
        conf_frame = tk.Frame(easyocr_frame, bg='#ecf0f1')
        conf_frame.pack(fill='x', pady=5)

        tk.Label(conf_frame, text="آستانه اطمینان OCR:",
                font=('Tahoma', 11), bg='#ecf0f1', fg='#2c3e50').pack(side='left')

        conf_scale = tk.Scale(conf_frame, from_=0.1, to=1.0, resolution=0.1,
                             variable=self.ocr_confidence, orient='horizontal',
                             font=('Tahoma', 10), bg='#ecf0f1',
                             length=300)
        conf_scale.pack(side='left', padx=20)

        # تنظیمات Tesseract
        tesseract_frame = tk.LabelFrame(ocr_tab, text="تنظیمات Tesseract",
                                       font=('Tahoma', 12, 'bold'),
                                       bg='#ecf0f1', fg='#2c3e50',
                                       padx=15, pady=15)
        tesseract_frame.pack(fill='x', padx=20, pady=10)

        # PSM Mode
        psm_frame = tk.Frame(tesseract_frame, bg='#ecf0f1')
        psm_frame.pack(fill='x', pady=5)

        tk.Label(psm_frame, text="حالت تشخیص صفحه (PSM):",
                font=('Tahoma', 11), bg='#ecf0f1', fg='#2c3e50').pack(side='left')

        psm_combo = ttk.Combobox(psm_frame, textvariable=self.tesseract_mode,
                                values=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
                                state='readonly', width=5)
        psm_combo.pack(side='left', padx=20)

        # دکمههای ذخیره
        save_frame = tk.Frame(tab, bg='#ecf0f1')
        save_frame.pack(fill='x', padx=20, pady=20)

        save_settings_btn = tk.Button(save_frame, text="💾 ذخیره تنظیمات",
                                     command=self.save_settings,
                                     font=('Tahoma', 12, 'bold'),
                                     bg='#27ae60', fg='white',
                                     relief='flat', padx=30, pady=12,
                                     cursor='hand2')
        save_settings_btn.pack(side='left', padx=10)

        reset_settings_btn = tk.Button(save_frame, text="🔄 بازنشانی",
                                      command=self.reset_settings,
                                      font=('Tahoma', 12, 'bold'),
                                      bg='#e74c3c', fg='white',
                                      relief='flat', padx=30, pady=12,
                                      cursor='hand2')
        reset_settings_btn.pack(side='left', padx=10)

    def create_about_tab(self):
        """تب درباره - کامل"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="ℹ️ درباره")

        # فریم اصلی با scroll
        main_frame = tk.Frame(tab, bg='#ecf0f1')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # لوگو و عنوان
        header_frame = tk.Frame(main_frame, bg='#34495e', relief='raised', bd=2)
        header_frame.pack(fill='x', pady=(0, 20))

        title_label = tk.Label(header_frame,
                              text="🚀 سیستم هوشمند استخراج داده‌های گمرکی",
                              font=('Tahoma', 20, 'bold'),
                              bg='#34495e', fg='#ecf0f1',
                              pady=20)
        title_label.pack()

        version_label = tk.Label(header_frame,
                                text="نسخه 2.0.0",
                                font=('Tahoma', 14),
                                bg='#34495e', fg='#bdc3c7',
                                pady=10)
        version_label.pack()

        # اطلاعات پروژه
        info_frame = tk.LabelFrame(main_frame, text="اطلاعات پروژه",
                                  font=('Tahoma', 14, 'bold'),
                                  bg='#ecf0f1', fg='#2c3e50',
                                  padx=20, pady=20)
        info_frame.pack(fill='x', pady=10)

        info_text = """
👨‍💻 توسعه‌دهنده: Mohsen Data Wizard
📅 تاریخ توسعه: 2025-06-10
🌐 GitHub: github.com/Mohsen-data-wizard
📧 ایمیل: mohsen.datawizard@example.com

🎯 هدف پروژه:
این نرم‌افزار برای خودکارسازی فرآیند استخراج داده‌های گمرکی از اسناد PDF طراحی شده است.

✨ قابلیت‌های کلیدی:
• استخراج خودکار داده‌ها از اسناد گمرکی
• پشتیبانی از اسناد وارداتی و صادراتی
• تشخیص متن با دقت بالا (OCR)
• خروجی در فرمت‌های مختلف (Excel, CSV, JSON)
• رابط کاربری فارسی و کاربرپسند
• سیستم لاگینگ پیشرفته
        """

        info_label = tk.Label(info_frame, text=info_text.strip(),
                             font=('Tahoma', 11), bg='#ecf0f1', fg='#2c3e50',
                             justify='left')
        info_label.pack(anchor='w')

        # فناوری‌های استفاده شده
        tech_frame = tk.LabelFrame(main_frame, text="فناوری‌های استفاده شده",
                                  font=('Tahoma', 14, 'bold'),
                                  bg='#ecf0f1', fg='#2c3e50',
                                  padx=20, pady=20)
        tech_frame.pack(fill='x', pady=10)

        tech_text = """
🐍 Python 3.11+
🖼️ OpenCV - پردازش تصویر
🔍 EasyOCR - تشخیص متن انگلیسی و فارسی
🔍 Tesseract - موتور OCR اضافی
📊 Pandas - پردازش داده‌ها
📈 OpenPyXL - خروجی Excel
🖥️ Tkinter - رابط گرافیکی
📄 PyMuPDF - پردازش PDF
🔧 PyInstaller - ساخت فایل اجرایی
        """

        tech_label = tk.Label(tech_frame, text=tech_text.strip(),
                             font=('Tahoma', 11), bg='#ecf0f1', fg='#2c3e50',
                             justify='left')
        tech_label.pack(anchor='w')

        # دکمه‌های مفید
        buttons_frame = tk.Frame(main_frame, bg='#ecf0f1')
        buttons_frame.pack(fill='x', pady=20)

        github_btn = tk.Button(buttons_frame, text="🌐 GitHub Repository",
                              command=self.open_github,
                              font=('Tahoma', 12, 'bold'),
                              bg='#2c3e50', fg='white',
                              relief='flat', padx=25, pady=10,
                              cursor='hand2')
        github_btn.pack(side='left', padx=10)

        docs_btn = tk.Button(buttons_frame, text="📚 مستندات",
                            command=self.open_docs,
                            font=('Tahoma', 12, 'bold'),
                            bg='#3498db', fg='white',
                            relief='flat', padx=25, pady=10,
                            cursor='hand2')
        docs_btn.pack(side='left', padx=10)

        support_btn = tk.Button(buttons_frame, text="🆘 پشتیبانی",
                               command=self.open_support,
                               font=('Tahoma', 12, 'bold'),
                               bg='#e67e22', fg='white',
                               relief='flat', padx=25, pady=10,
                               cursor='hand2')
        support_btn.pack(side='left', padx=10)

        # کپی‌رایت
        copyright_frame = tk.Frame(main_frame, bg='#95a5a6')
        copyright_frame.pack(fill='x', pady=(20, 0))

        copyright_label = tk.Label(copyright_frame,
                                  text="© 2025 Mohsen Data Wizard. All rights reserved.",
                                  font=('Tahoma', 10),
                                  bg='#95a5a6', fg='white',
                                  pady=10)
        copyright_label.pack()

    def create_status_bar(self):
        """ایجاد نوار وضعیت"""
        self.status_frame = tk.Frame(self.root, bg='#34495e', height=30)
        self.status_frame.pack(fill='x', side='bottom')
        self.status_frame.pack_propagate(False)

        self.status_label = tk.Label(self.status_frame,
                                    text="🔮 آماده پردازش فایلهای گمرکی...",
                                    font=('Tahoma', 10),
                                    bg='#34495e', fg='#ecf0f1')
        self.status_label.pack(side='left', padx=10, pady=5)

        # نمایش ساعت
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        self.time_label = tk.Label(self.status_frame,
                                  text=f"⏰ {time_str}",
                                  font=('Tahoma', 10),
                                  bg='#34495e', fg='#bdc3c7')
        self.time_label.pack(side='right', padx=10, pady=5)

        # بروزرسانی ساعت
        self.update_time()

    def update_time(self):
        """بروزرسانی ساعت"""
        try:
            time_str = datetime.datetime.now().strftime("%H:%M:%S")
            if hasattr(self, 'time_label'):
                self.time_label.config(text=f"⏰ {time_str}")
            self.root.after(1000, self.update_time)
        except:
            pass

    # 🔥 متدهای اصلی پردازش

    def start_processing(self):
        """شروع پردازش فایلهای انتخاب شده"""
        if not self.selected_files:
            messagebox.showwarning("هشدار", "هیچ فایلی انتخاب نشده است!")
            return

        if self.processing_active:
            messagebox.showinfo("اطلاع", "پردازش در حال انجام است!")
            return

        # تغییر حالت UI
        self.processing_active = True
        self.start_processing_btn.config(state='disabled')
        self.start_btn.config(state='disabled')
        self.pause_btn.config(state='normal')
        self.stop_btn.config(state='normal')

        # پاک کردن نتایج قبلی
        self.current_results.clear()
        self.total_extracted_items = 0

        # شروع thread پردازش
        self.processing_thread = threading.Thread(
            target=self._process_files_worker,
            daemon=True
        )
        self.processing_thread.start()

        logger.info(f"🚀 شروع پردازش {len(self.selected_files)} فایل")


    def _process_files_worker(self):
        """Worker thread برای پردازش فایلها - نسخه بهبود یافته"""
        try:
            self.processing_start_time = time.time()
            doc_type = self.document_type.get()

            total_files = len(self.selected_files)
            logger.info(f"🚀 شروع پردازش {total_files} فایل با نوع سند: {doc_type}")

            for i, file_path in enumerate(self.selected_files):
                if not self.processing_active:
                    logger.info("⏹️ پردازش متوقف شد توسط کاربر")
                    break

                try:
                    # بروزرسانی UI
                    self.root.after(0, self._update_current_file_progress, i, total_files, file_path)

                    logger.info(f"📄 پردازش فایل {i + 1}/{total_files}: {Path(file_path).name}")

                    # استفاده از متد پردازش جدید
                    file_result = self.process_single_file_complete(file_path)

                    if file_result.get('success'):
                        # اضافه کردن نتیجه به لیست
                        display_result = file_result['result']
                        self.current_results.append(display_result)
                        self.total_extracted_items += 1

                        # نمایش آمار
                        stats = file_result['full_result'].get('extraction_stats', {})
                        extracted_fields = stats.get('extracted_fields', 0)
                        success_rate = stats.get('success_rate', 0)

                        logger.info(
                            f"✅ فایل {Path(file_path).name}: {extracted_fields} فیلد ({success_rate:.1f}% موفقیت)")

                        # بروزرسانی زنده نتایج
                        if i % 5 == 0:  # هر 5 فایل
                            self.root.after(0, self.refresh_results_display)
                    else:
                        error_msg = file_result.get('error', 'خطای نامشخص')
                        logger.warning(f"❌ فایل {Path(file_path).name}: {error_msg}")

                    # بروزرسانی پیشرفت کلی
                    overall_progress = ((i + 1) / total_files) * 100
                    self.root.after(0, lambda p=overall_progress: self.progress_var.set(p))

                except Exception as e:
                    logger.error(f"❌ خطا در پردازش {Path(file_path).name}: {e}")
                    continue

            # اتمام پردازش
            self.root.after(0, self._finish_processing)

        except Exception as e:
            logger.error(f"❌ خطای کلی در worker thread: {e}")
            self.root.after(0, self._finish_processing)

    def _update_current_file_progress(self, current_index, total_files, file_path):
        """بروزرسانی نوار پیشرفت فایل فعلی"""
        try:
            # پیشرفت کلی
            overall_progress = (current_index / total_files) * 100
            self.progress_var.set(overall_progress)
            self.progress_label.config(text=f"پردازش فایل {current_index + 1} از {total_files}")

            # فایل فعلی
            self.current_progress_var.set(0)
            self.current_file_label.config(text=f"📄 {Path(file_path).name}")

            # بروزرسانی UI
            self.root.update_idletasks()

        except Exception as e:
            logger.error(f"❌ خطا در بروزرسانی UI: {e}")

    def _finish_processing(self):
        """اتمام پردازش"""
        try:
            self.processing_active = False

            # بروزرسانی UI
            self.progress_var.set(100)
            self.current_progress_var.set(100)
            self.progress_label.config(text="پردازش کامل شد!")
            self.current_file_label.config(text="✅ همه فایلها پردازش شدند")

            # فعالسازی دکمهها
            self.start_processing_btn.config(state='normal')
            self.start_btn.config(state='normal')
            self.pause_btn.config(state='disabled')
            self.stop_btn.config(state='disabled')

            # محاسبه زمان
            if self.processing_start_time:
                elapsed_time = time.time() - self.processing_start_time
                self.update_processing_stats(elapsed_time)

            # بروزرسانی نتایج
            self.refresh_results_display()

            # تغییر به تب نتایج
            self.notebook.select(3)  # تب نتایج

            logger.info(f"🎉 پردازش کامل شد! {self.total_extracted_items} قلم استخراج شد")
            messagebox.showinfo("موفقیت", f"پردازش کامل شد!\n{self.total_extracted_items} قلم داده استخراج شد")

        except Exception as e:
            logger.error(f"❌ خطا در اتمام پردازش: {e}")

    def update_processing_stats(self, elapsed_time):
        """بروزرسانی آمار پردازش"""
        try:
            # فرمت زمان
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            time_str = f"{minutes:02d}:{seconds:02d}"

            # بروزرسانی لیبل‌های آمار
            if hasattr(self, 'stats_files'):
                self.stats_files.config(text=f"📁 فایلها: {len(self.selected_files)}")

            if hasattr(self, 'stats_items'):
                self.stats_items.config(text=f"📦 کالاها: {self.total_extracted_items}")

            if hasattr(self, 'stats_time'):
                self.stats_time.config(text=f"⏱️ زمان: {time_str}")

            if hasattr(self, 'stats_success'):
                success_rate = (self.total_extracted_items / len(self.selected_files)) * 100 if self.selected_files else 0
                self.stats_success.config(text=f"✅ موفقیت: {success_rate:.1f}%")

        except Exception as e:
            logger.error(f"❌ خطا در بروزرسانی آمار: {e}")

    def refresh_results_display(self):
        """بروزرسانی نمایش نتایج"""
        try:
            if not hasattr(self, 'results_tree'):
                return

            # پاک کردن نتایج قبلی
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)

            # اضافه کردن نتایج جدید
            for i, result_entry in enumerate(self.current_results, 1):
                extraction_result = result_entry.get('extraction_result', {})
                extracted_data = extraction_result.get('extracted_data', {})

                # تشکیل ردیف
                row_values = []
                for column in self.result_columns:
                    field_result = extracted_data.get(column, {})
                    value = field_result.get('value', '') if isinstance(field_result, dict) else ''
                    row_values.append(value)

                # اضافه کردن صفحه
                row_values.append(result_entry.get('page_number', ''))

                # تعیین تگ بر اساس کیفیت
                tag = 'complete' if len([v for v in row_values if v]) > 5 else 'incomplete'

                self.results_tree.insert('', 'end',
                                       text=str(i),
                                       values=row_values,
                                       tags=(tag,))

            logger.info(f"📊 نمایش {len(self.current_results)} نتیجه بروزرسانی شد")

        except Exception as e:
            logger.error(f"❌ خطا در بروزرسانی نتایج: {e}")

    def process_single_file_complete(self, file_path: str) -> Dict[str, Any]:
        """پردازش کامل یک فایل - استفاده از متد جدید"""
        try:
            logger.info(f"🔄 شروع پردازش کامل: {Path(file_path).name}")

            # استفاده از متد جدید پردازش صفحه‌ای
            results = self.pdf_processor.process_pdf_pages_individually(file_path)

            if not results:
                logger.error("❌ هیچ صفحه‌ای پردازش نشد")
                return {'success': False, 'error': 'هیچ صفحه‌ای پردازش نشد'}

            # استفاده از اولین صفحه برای نمایش
            first_result = results[0]

            # خواندن JSON فایل اولین صفحه
            json_file_path = first_result["json_file"]
            with open(json_file_path, 'r', encoding='utf-8') as f:
                page_data = json.load(f)

            # استخراج داده‌های گمرکی
            customs_extraction = page_data.get("customs_extraction", {})
            customs_fields = customs_extraction.get("customs_fields", {})

            if customs_fields:
                # تشکیل نتیجه برای نمایش
                display_result = {
                    'file_name': Path(file_path).name,
                    'file_path': file_path,
                    'page_number': first_result["page_number"],
                    'extraction_result': {
                        'extracted_data': customs_fields,
                        'stats': customs_extraction.get("extraction_stats", {})
                    },
                    'extracted_text': page_data.get('raw_text', '')[:500] + "..."
                }

                extracted_count = len([k for k, v in customs_fields.items() if v.get("value") is not None])
                logger.info(f"✅ پردازش موفق: {extracted_count} فیلد استخراج شد")

                return {
                    'success': True,
                    'result': display_result,
                    'full_result': {
                        'all_pages': results,
                        'extraction_stats': customs_extraction.get("extraction_stats", {})
                    }
                }
            else:
                logger.warning("⚠️ هیچ فیلدی استخراج نشد")
                return {'success': False, 'error': 'هیچ فیلدی استخراج نشد'}

        except Exception as e:
            logger.error(f"❌ خطا در پردازش فایل: {e}")
            return {'success': False, 'error': str(e)}

    def start_batch_processing(self):
        """شروع پردازش دستهای - مشابه start_processing"""
        self.start_processing()

    def pause_processing(self):
        """مکث پردازش"""
        if self.processing_active:
            self.processing_active = False
            logger.info("⏸️ پردازش متوقف شد")
            self.pause_btn.config(state='disabled')
            self.start_processing_btn.config(state='normal')

    def stop_processing(self):
        """توقف کامل پردازش"""
        if self.processing_active:
            self.processing_active = False
            logger.info("⏹️ پردازش لغو شد")

            # بازنشانی UI
            self.progress_var.set(0)
            self.current_progress_var.set(0)
            self.progress_label.config(text="پردازش لغو شد")
            self.current_file_label.config(text="")

            # فعالسازی دکمهها
            self.start_processing_btn.config(state='normal')
            self.start_btn.config(state='normal')
            self.pause_btn.config(state='disabled')
            self.stop_btn.config(state='disabled')

    # متدهای فایل

    def select_files(self):
        """انتخاب فایلهای PDF"""
        files = filedialog.askopenfilenames(
            title="انتخاب فایلهای PDF",
            filetypes=[
                ("PDF files", "*.pdf"),
                ("All files", "*.*")
            ],
            initialdir=Path.home() / "Desktop"
        )

        if files:
            self.selected_files.extend(files)
            self.update_files_display()
            logger.info(f"📁 {len(files)} فایل انتخاب شد")

    def select_folder(self):
        """انتخاب پوشه حاوی PDF"""
        folder = filedialog.askdirectory(
            title="انتخاب پوشه حاوی فایلهای PDF",
            initialdir=Path.home() / "Desktop"
        )

        if folder:
            pdf_files = list(Path(folder).glob("*.pdf"))
            if pdf_files:
                self.selected_files.extend([str(f) for f in pdf_files])
                self.update_files_display()
                logger.info(f"📂 {len(pdf_files)} فایل از پوشه {folder} اضافه شد")
            else:
                messagebox.showwarning("هشدار", "هیچ فایل PDF در پوشه انتخاب شده یافت نشد")

    def clear_files(self):
        """پاک کردن لیست فایلها"""
        if self.confirm_delete.get():
            if not messagebox.askyesno("تایید", "آیا مطمئن هستید که می‌خواهید لیست فایل‌ها را پاک کنید؟"):
                return

        self.selected_files.clear()
        self.update_files_display()
        logger.info("🗑️ لیست فایلها پاک شد")

    def update_files_display(self):
        """بروزرسانی نمایش فایلها"""
        # پاک کردن لیست
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)

        total_size = 0

        # اضافه کردن فایلها
        for i, file_path in enumerate(self.selected_files, 1):
            file_obj = Path(file_path)

            if file_obj.exists():
                size_mb = file_obj.stat().st_size / (1024 * 1024)
                total_size += size_mb

                # تاریخ تغییر
                mod_time = datetime.datetime.fromtimestamp(file_obj.stat().st_mtime)
                mod_time_str = mod_time.strftime('%Y-%m-%d %H:%M')

                self.files_tree.insert('', 'end',
                                      text=str(i),
                                      values=(
                                          file_obj.name,
                                          f"{size_mb:.1f} MB",
                                          mod_time_str,
                                          str(file_obj.parent)
                                      ))

        # بروزرسانی آمار
        count = len(self.selected_files)
        self.files_count_label.config(
            text=f"📊 فایل انتخاب شده: {count} | حجم کل: {total_size:.1f} MB"
        )

        # فعال/غیرفعال کردن دکمه پردازش
        state = 'normal' if count > 0 else 'disabled'
        self.start_processing_btn.config(state=state)
        self.start_btn.config(state=state)

    # متدهای خروجی

    def export_excel(self):
        """خروجی Excel زیبا"""
        try:
            if not self.current_results:
                messagebox.showwarning("هشدار", "هیچ نتیجهای برای خروجی وجود ندارد!")
                return

            file_path = filedialog.asksaveasfilename(
                title="ذخیره Excel",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )

            if file_path:
                import pandas as pd

                # تشکیل دیتافریم
                data_rows = []
                for result_entry in self.current_results:
                    extraction_result = result_entry.get('extraction_result', {})
                    extracted_data = extraction_result.get('extracted_data', {})

                    row = {}
                    for column in self.result_columns:
                        field_result = extracted_data.get(column, {})
                        value = field_result.get('value', '') if isinstance(field_result, dict) else ''
                        row[column.replace('_', ' ')] = value

                    row['نام فایل'] = result_entry.get('file_name', '')
                    row['شماره صفحه'] = result_entry.get('page_number', '')
                    data_rows.append(row)

                df = pd.DataFrame(data_rows)

                # ذخیره Excel
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='داده های گمرکی', index=False)

                    # فرمت دهی
                    worksheet = writer.sheets['داده های گمرکی']
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width

                logger.info(f"💾 فایل Excel ذخیره شد: {file_path}")
                messagebox.showinfo("موفقیت", f"فایل Excel با موفقیت ذخیره شد!\n{file_path}")

        except Exception as e:
            logger.error(f"❌ خطا در ذخیره Excel: {e}")
            messagebox.showerror("خطا", f"خطا در ذخیره Excel: {e}")

    def export_csv(self):
        """خروجی CSV"""
        try:
            if not self.current_results:
                messagebox.showwarning("هشدار", "هیچ نتیجهای برای خروجی وجود ندارد!")
                return

            file_path = filedialog.asksaveasfilename(
                title="ذخیره CSV",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )

            if file_path:
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    fieldnames = [col.replace('_', ' ') for col in self.result_columns] + ['نام فایل', 'شماره صفحه']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                    writer.writeheader()
                    for result_entry in self.current_results:
                        extraction_result = result_entry.get('extraction_result', {})
                        extracted_data = extraction_result.get('extracted_data', {})

                        row = {}
                        for column in self.result_columns:
                            field_result = extracted_data.get(column, {})
                            value = field_result.get('value', '') if isinstance(field_result, dict) else ''
                            row[column.replace('_', ' ')] = value

                        row['نام فایل'] = result_entry.get('file_name', '')
                        row['شماره صفحه'] = result_entry.get('page_number', '')
                        writer.writerow(row)

                logger.info(f"📄 فایل CSV ذخیره شد: {file_path}")
                messagebox.showinfo("موفقیت", f"فایل CSV با موفقیت ذخیره شد!\n{file_path}")

        except Exception as e:
            logger.error(f"❌ خطا در ذخیره CSV: {e}")
            messagebox.showerror("خطا", f"خطا در ذخیره CSV: {e}")

    def export_json(self):
        """خروجی JSON"""
        try:
            if not self.current_results:
                messagebox.showwarning("هشدار", "هیچ نتیجهای برای خروجی وجود ندارد!")
                return

            file_path = filedialog.asksaveasfilename(
                title="ذخیره JSON",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as jsonfile:
                    json.dump(self.current_results, jsonfile, ensure_ascii=False, indent=2)

                logger.info(f"📋 فایل JSON ذخیره شد: {file_path}")
                messagebox.showinfo("موفقیت", f"فایل JSON با موفقیت ذخیره شد!\n{file_path}")

        except Exception as e:
            logger.error(f"❌ خطا در ذخیره JSON: {e}")
            messagebox.showerror("خطا", f"خطا در ذخیره JSON: {e}")

    # متدهای کمکی

    def toggle_auto_scroll(self):
        """تغییر حالت Auto Scroll"""
        self.auto_scroll_enabled = not self.auto_scroll_enabled
        logger.info(f"📜 Auto Scroll: {'فعال' if self.auto_scroll_enabled else 'غیرفعال'}")

    def clear_log(self):
        """پاک کردن لاگ"""
        if hasattr(self, 'log_text'):
            self.log_text.config(state='normal')
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state='disabled')
        logger.info("🗑️ لاگ پاک شد")

    def save_log(self):
        """ذخیره لاگ"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="ذخیره لاگ",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )

            if file_path and hasattr(self, 'log_text'):
                log_content = self.log_text.get(1.0, tk.END)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                logger.info(f"💾 لاگ ذخیره شد: {file_path}")
                messagebox.showinfo("موفقیت", "لاگ با موفقیت ذخیره شد!")

        except Exception as e:
            logger.error(f"❌ خطا در ذخیره لاگ: {e}")
            messagebox.showerror("خطا", f"خطا در ذخیره لاگ: {e}")

    # متدهای الگوها

    def load_default_patterns(self):
        """بارگذاری الگوهای پیش‌فرض"""
        try:
            if not hasattr(self, 'patterns_tree'):
                return

            # پاک کردن آیتم‌های قبلی
            for item in self.patterns_tree.get_children():
                self.patterns_tree.delete(item)

            # بارگذاری الگوهای فعلی
            doc_type = self.document_type.get()
            patterns = self.pattern_extractor.CustomsPatternExtractor(doc_type)

            for i, (field_name, field_patterns) in enumerate(patterns.items(), 1):
                # نمایش اولین الگو
                first_pattern = field_patterns[0] if field_patterns else ""
                description = f"{len(field_patterns)} الگو"
                status = "فعال" if field_patterns else "غیرفعال"

                self.patterns_tree.insert('', 'end',
                                         text=str(i),
                                         values=(field_name, first_pattern, description, status))

            logger.info(f"🎯 {len(patterns)} الگو بارگذاری شد")

        except Exception as e:
            logger.error(f"❌ خطا در بارگذاری الگوها: {e}")

    def load_patterns(self):
        """بارگذاری مجدد الگوها"""
        self.load_default_patterns()
        logger.info("🔄 الگوها بارگذاری مجدد شدند")

    def save_patterns(self):
        """ذخیره الگوها"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="ذخیره الگوها",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if file_path:
                doc_type = self.document_type.get()
                patterns = self.pattern_extractor.get_patterns(doc_type)

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(patterns, f, ensure_ascii=False, indent=2)

                logger.info(f"💾 الگوها ذخیره شدند: {file_path}")
                messagebox.showinfo("موفقیت", "الگوها با موفقیت ذخیره شدند!")

        except Exception as e:
            logger.error(f"❌ خطا در ذخیره الگوها: {e}")
            messagebox.showerror("خطا", f"خطا در ذخیره الگوها: {e}")

    def test_patterns(self):
        """تست الگوها"""
        test_text = """
        ۱۲۳۴۵۶۷۸ - زمینی
        CN کشور طرف معامله
        برات نوع معامله
        عدد نوع بسته
        """

        try:
            doc_type = self.document_type.get()
            result = self.data_extractor.extract_from_text(test_text, doc_type)

            if result:
                extracted_count = len(result.get('extracted_data', {}))
                messagebox.showinfo("نتیجه تست", f"الگوها تست شدند!\n{extracted_count} فیلد استخراج شد")
                logger.info(f"🧪 تست الگوها: {extracted_count} فیلد استخراج شد")
            else:
                messagebox.showwarning("نتیجه تست", "هیچ فیلدی استخراج نشد!")

        except Exception as e:
            logger.error(f"❌ خطا در تست الگوها: {e}")
            messagebox.showerror("خطا", f"خطا در تست الگوها: {e}")

    # متدهای ویرایش

    def refresh_edit_fields(self):
        """بارگذاری مجدد فیلدهای ویرایش"""
        logger.info("🔄 بارگذاری مجدد فیلدهای ویرایش")
        # Implementation needed

    def save_edits(self):
        """ذخیره تغییرات"""
        logger.info("💾 ذخیره تغییرات")
        # Implementation needed

    def validate_data(self):
        """اعتبارسنجی داده‌ها"""
        logger.info("✅ اعتبارسنجی داده‌ها")
        # Implementation needed

    # متدهای تنظیمات

    def save_settings(self):
        """ذخیره تنظیمات"""
        try:
            # اعمال تنظیمات جدید
            new_settings = {
                'ocr.easyocr.gpu': self.use_gpu.get(),
                'processing.default_dpi': self.dpi_var.get(),
                'app.auto_backup': self.auto_backup.get(),
                'app.confirm_delete': self.confirm_delete.get(),
                'ocr.confidence_threshold': self.ocr_confidence.get(),
                'ocr.tesseract.psm': self.tesseract_mode.get()
            }

            for key, value in new_settings.items():
                self.config.set(key, value)

            logger.info("💾 تنظیمات ذخیره شدند")
            messagebox.showinfo("موفقیت", "تنظیمات با موفقیت ذخیره شدند!")

        except Exception as e:
            logger.error(f"❌ خطا در ذخیره تنظیمات: {e}")
            messagebox.showerror("خطا", f"خطا در ذخیره تنظیمات: {e}")

    def reset_settings(self):
        """بازنشانی تنظیمات"""
        if messagebox.askyesno("تایید", "آیا مطمئن هستید که می‌خواهید تنظیمات را بازنشانی کنید؟"):
            try:
                # بازنشانی متغیرها
                self.use_gpu.set(True)
                self.dpi_var.set(350)
                self.auto_backup.set(True)
                self.confirm_delete.set(True)
                self.ocr_confidence.set(0.7)
                self.tesseract_mode.set(3)

                logger.info("🔄 تنظیمات بازنشانی شدند")
                messagebox.showinfo("موفقیت", "تنظیمات بازنشانی شدند!")

            except Exception as e:
                logger.error(f"❌ خطا در بازنشانی تنظیمات: {e}")

    # متدهای درباره

    def open_github(self):
        """باز کردن GitHub"""
        try:
            webbrowser.open("https://github.com/Mohsen-data-wizard/customs-ocr-system")
            logger.info("🌐 GitHub Repository باز شد")
        except Exception as e:
            logger.error(f"❌ خطا در باز کردن GitHub: {e}")

    def open_docs(self):
        """باز کردن مستندات"""
        try:
            webbrowser.open("https://github.com/Mohsen-data-wizard/customs-ocr-system/wiki")
            logger.info("📚 مستندات باز شد")
        except Exception as e:
            logger.error(f"❌ خطا در باز کردن مستندات: {e}")

    def open_support(self):
        """باز کردن پشتیبانی"""
        try:
            webbrowser.open("https://github.com/Mohsen-data-wizard/customs-ocr-system/issues")
            logger.info("🆘 پشتیبانی باز شد")
        except Exception as e:
            logger.error(f"❌ خطا در باز کردن پشتیبانی: {e}")

    # متدهای placeholder

    def generate_report(self):
        """تولید گزارش"""
        logger.info("📄 تولید گزارش")
        messagebox.showinfo("اطلاع", "این قابلیت در حال توسعه است")

    def print_results(self):
        """چاپ نتایج"""
        logger.info("🖨️ چاپ نتایج")
        messagebox.showinfo("اطلاع", "این قابلیت در حال توسعه است")

    def email_results(self):
        """ارسال ایمیل"""
        logger.info("📧 ارسال ایمیل")
        messagebox.showinfo("اطلاع", "این قابلیت در حال توسعه است")

    def run(self):
        """اجرای برنامه"""
        logger.info("🎯 شروع حلقه اصلی برنامه")
        self.root.mainloop()
        logger.info("👋 برنامه بسته شد")

if __name__ == "__main__":
    config = ConfigManager()
    app = CustomsOCRApp(config)
    app.run()
