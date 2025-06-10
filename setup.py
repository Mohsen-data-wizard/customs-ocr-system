from setuptools import setup, find_packages

setup(
    name="customs-ocr-system",
    version="2.0.0",
    author="Mohsen Data Wizard",
    author_email="mohsen@datawizard.ir",
    description="🚀 سیستم هوشمند استخراج دادههای گمرکی",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/mohsen-data-wizard/customs-ocr-system",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "easyocr>=1.7.0",
        "pytesseract>=0.3.10",
        "opencv-python>=4.8.0",
        "Pillow>=10.0.0",
        "PyMuPDF>=1.23.0",
        "pandas>=2.1.0",
        "numpy>=1.24.0",
        "openpyxl>=3.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "customs-ocr=src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "src": ["assets/*", "config/*"],
    },
)
