FROM python:3.11-slim

WORKDIR /app

RUN pip install pandas openpyxl langsmith python-dotenv

# Copy scripts and graph into the container to prevent malicious host script modification
COPY scripts /app/scripts
COPY graph /app/graph

# Default execution command
CMD ["python", "/app/scripts/extract_menu.py"]
