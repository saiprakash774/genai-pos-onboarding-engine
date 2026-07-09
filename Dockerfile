FROM python:3.11-slim

WORKDIR /app

RUN pip install pandas openpyxl

CMD ["python", "/scripts/extract_menu.py"]
