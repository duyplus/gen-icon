#!/usr/bin/env python3
"""
Python Favicon Generator
Chạy ứng dụng Flask để tạo favicon và app icons
"""

import os
from app import app

if __name__ == '__main__':
    # Tạo thư mục temp nếu chưa tồn tại
    if not os.path.exists('temp'):
        os.makedirs('temp')
    
    print("-" * 50)
    
    # Chạy ứng dụng Flask
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        threaded=True
    ) 