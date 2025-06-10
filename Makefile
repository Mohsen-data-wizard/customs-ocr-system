# Makefile برای مدیریت پروژه

.PHONY: install run test clean build

install:
pip install -r requirements.txt
pip install -e .

run:
python src/main.py

test:
pytest tests/ -v

clean:
find . -type d -name "__pycache__" -delete
find . -name "*.pyc" -delete
rm -rf build/ dist/ *.egg-info/

build:
python setup.py sdist bdist_wheel

dev-install:
pip install -r requirements.txt
pip install -e ".[dev]"

format:
black src/ tests/
flake8 src/ tests/

type-check:
mypy src/
