#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
رابط گرافیکی اصلی برنامه
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
from pathlib import Path
from typing import List, Dict, Any

from core.ocr_engine import OCREngine
from core.pdf_processor import PDFProcessor
from core.data_extractor import DataExtractor
from utils.logger import get_logger
from utils.config import ConfigManager
from patterns.regex_patterns import PatternManager

logger = get_logger(__name__)

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
        
        # متغیرهای تنظیمات
        self.use_gpu = tk.BooleanVar(value=self.config.get('ocr.easyocr.gpu', True))
        self.dpi_var = tk.IntVar(value=self.config.get('processing.default_dpi', 350))
        self.save_debug = tk.BooleanVar(value=False)
    
    def setup_components(self):
        """راهاندازی کامپوننتهای اصلی"""
        self.pattern_manager = PatternManager()
        self.ocr_engine = OCREngine(self.config)
        self.pdf_processor = PDFProcessor(self.config)
        self.data_extractor = DataExtractor(self.pattern_manager, self.config)
    
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
        user_info = f"کاربر: {self.config.get('app.author', 'Mohsen-data-wizard')} | تاریخ: 2025-06-10"
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
        
        # فریم نوع سند
        doc_frame = tk.LabelFrame(tab, text="نوع اسناد گمرکی", 
                                 font=('Tahoma', 12, 'bold'),
                                 bg='#ecf0f1', fg='#2c3e50', 
                                 padx=15, pady=15)
        doc_frame.pack(fill='x', padx=20, pady=10)
        
        # رادیو باتنها
        radio_frame = tk.Frame(doc_frame, bg='#ecf0f1')
        radio_frame.pack(fill='x')
        
        import_radio = tk.Radiobutton(radio_frame, 
                                     text="📥 اسناد وارداتی (Import Documents)", 
                                     variable=self.document_type, value="وارداتی",
                                     font=('Tahoma', 11, 'bold'), 
                                     bg='#ecf0f1', fg='#27ae60',
                                     selectcolor='#27ae60',
                                     command=self.on_document_type_change)
        import_radio.pack(side='left', padx=30, pady=10)
        
        export_radio = tk.Radiobutton(radio_frame, 
                                     text="📤 اسناد صادراتی (Export Documents)", 
                                     variable=self.document_type, value="صادراتی",
                                     font=('Tahoma', 11, 'bold'), 
                                     bg='#ecf0f1', fg='#e74c3c',
                                     selectcolor='#e74c3c',
                                     command=self.on_document_type_change)
        export_radio.pack(side='left', padx=30, pady=10)
        
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
        columns = ('نام فایل', 'اندازه', 'مسیر')
        self.files_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=12)
        
        # تنظیم ستونها
        self.files_tree.heading('#0', text='#', anchor='w')
        self.files_tree.heading('نام فایل', text='نام فایل', anchor='w')
        self.files_tree.heading('اندازه', text='اندازه', anchor='center')
        self.files_tree.heading('مسیر', text='مسیر', anchor='w')
        
        self.files_tree.column('#0', width=50)
        self.files_tree.column('نام فایل', width=300)
        self.files_tree.column('اندازه', width=100)
        self.files_tree.column('مسیر', width=400)
        
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
        log_frame = tk.LabelFrame(tab, text="لاگ پردازش", 
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
            'شماره_کوتا', 'شرح_کالا', 'کد_کالا', 'تعداد_بسته', 'نوع_بسته', 
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
            elif col in ['شماره_کوتا', 'کد_کالا']:
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
    
    def run(self):
        """اجرای برنامه"""
        logger.info("🎯 شروع حلقه اصلی برنامه")
        self.root.mainloop()
        logger.info("👋 برنامه بسته شد")

# متدهای کمکی...
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
                
                self.files_tree.insert('', 'end', 
                                      text=str(i),
                                      values=(
                                          file_obj.name,
                                          f"{size_mb:.1f} MB",
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

if __name__ == "__main__":
    config = ConfigManager()
    app = CustomsOCRApp(config)
    app.run()
