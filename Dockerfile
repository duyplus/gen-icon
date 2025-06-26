FROM python:3.9-slim

# Thiết lập thông tin
LABEL maintainer="Python Favicon Generator"
LABEL description="Favicon và App Icons Generator bằng Python Flask"

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt system dependencies cho Pillow
RUN apt-get update && apt-get install -y \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    libffi-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements và cài đặt Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Tạo thư mục temp
RUN mkdir -p temp

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Chạy ứng dụng
CMD ["python", "app.py"] 