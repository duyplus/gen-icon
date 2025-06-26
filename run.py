#!/usr/bin/env python3
"""
Production runner for Railway deployment
Sử dụng Gunicorn để chạy Flask app với cấu hình tối ưu
"""

import os
import subprocess
import sys

def main():
    """Khởi động production server với Gunicorn"""
    
    # Lấy PORT từ environment hoặc mặc định 5000
    port = os.environ.get('PORT', '5000')
    
    print(f"🚀 Starting production server on port {port}")
    
    # Cấu hình Gunicorn
    gunicorn_cmd = [
        'gunicorn',
        '--bind', f'0.0.0.0:{port}',
        '--workers', '2',
        '--worker-class', 'sync',
        '--worker-connections', '1000',
        '--max-requests', '1000',
        '--max-requests-jitter', '100',
        '--timeout', '30',
        '--keep-alive', '2',
        '--preload',
        '--access-logfile', '-',
        '--error-logfile', '-',
        '--log-level', 'info',
        'app:app'
    ]
    
    try:
        # Chạy Gunicorn
        subprocess.run(gunicorn_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khởi động server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Server đã dừng")
        sys.exit(0)

if __name__ == '__main__':
    main() 