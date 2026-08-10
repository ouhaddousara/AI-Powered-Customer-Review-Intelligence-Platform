FROM python:3.12-slim

WORKDIR /app

# System dependency for Tesseract OCR (Layer 3)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["python", "app/gradio_app.py"]