# 🐍 Favicon Generator

> Ứng dụng web tạo favicon và app icons từ hình ảnh bằng Python Flask và Pillow. Hỗ trợ đa nền tảng Web, Android, iOS và Microsoft.

## ✨ Tính năng

- 🐍 **Python + Flask:** Framework web nhẹ và mạnh mẽ
- 🖼️ **Pillow Processing:** Xử lý ảnh chuyên nghiệp với thư viện Pillow
- 📦 **Upload đa định dạng:** Hỗ trợ PNG, JPG, JPEG, GIF (tối đa 10MB)
- 🎯 **Đa kích thước:** Tự động tạo hàng chục kích thước icon
- 🔧 **Tùy chỉnh linh hoạt:**
  - Chỉ tạo favicon.ico
  - Tạo full set cho tất cả nền tảng
  - Giữ tỷ lệ hình ảnh hoặc resize chính xác
- 📱 **Đa nền tảng:**
  - **Web:** favicon-16x16, favicon-32x32, favicon-96x96
  - **Android:** Từ 36x36 đến 192x192
  - **iOS/Apple Touch:** Từ 40x40 đến 1024x1024  
  - **Microsoft:** Tile icons từ 70x70 đến 310x310
- 📦 **File đầy đủ:** Bao gồm manifest.json, browserconfig.xml
- ⚡ **Xử lý nhanh:** Tạo hàng chục icon trong vài giây
- 🗂️ **Tải về dễ dàng:** ZIP file hoặc favicon đơn lẻ

## 🛠️ Tech Stack

### Backend
- **Python:** 3.8+
- **Framework:** Flask 2.3.3
- **Image Processing:** Pillow 10.0.1
- **File Upload:** Werkzeug 2.3.7

### Frontend  
- **Template Engine:** Jinja2 (Flask)
- **Styling:** CSS3 với gradient animations
- **JavaScript:** jQuery 3.7.1
- **Icons:** Font Awesome 6.4.0
- **Notifications:** Notyf 3.x

## 📋 Yêu cầu hệ thống

- Python 3.8+
- pip package manager
- 512MB RAM tối thiểu

## 🔧 Cài đặt và chạy

### Cài đặt dependencies

```bash
# Di chuyển vào thư mục dự án
cd gen-icon

# Tạo virtual environment (khuyến nghị)
python -m venv venv

# Kích hoạt virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### Chạy ứng dụng

```bash
# Chạy development server
python app.py
```

Ứng dụng sẽ chạy tại: http://localhost:5000

## 🚀 Deployment

### Local Development
```bash
# Windows
.\venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate

# Chạy ứng dụng
python app.py
```

### Railway (Production - Khuyến nghị)
Railway là platform PaaS tuyệt vời để deploy Flask apps:

1. **Commit code lên Git:**
```bash
git add .
git commit -m "Deploy to Railway"
git push origin main
```

2. **Deploy trên Railway:**
   - Truy cập: https://railway.app
   - Connect GitHub repository
   - Chọn project folder
   - Set environment variables:
     ```
     SECRET_KEY=your-super-secret-key-here
     ```

3. **Railway sẽ tự động:**
   - ✅ Detect Python app
   - ✅ Install dependencies từ `requirements.txt`
   - ✅ Chạy với Gunicorn production server
   - ✅ Assign domain và SSL certificate

### Production với Gunicorn (VPS/Server)
```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Chạy production server
python run.py

# Hoặc trực tiếp với Gunicorn
gunicorn --bind 0.0.0.0:5000 app:app
```

### Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "run.py"]
```

## 🎨 Tính năng nổi bật

### 1. Xử lý ảnh với Pillow
- Hỗ trợ nhiều định dạng ảnh
- Resize với chất lượng cao
- Tạo file ICO thực sự
- Giữ tỷ lệ hoặc resize cưỡng bức

### 2. Giao diện người dùng
- Drag & drop upload
- Preview ảnh real-time
- Progress indicator
- Responsive design

### 3. Quản lý file
- Tự động cleanup file tạm
- Tạo ZIP chứa tất cả icons
- Download trực tiếp favicon.ico

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push branch: `git push origin feature/amazing-feature`
5. Tạo Pull Request

## 📝 License

Dự án này được phân phối dưới MIT License.

## 🙏 Acknowledgments

- [Flask](https://flask.palletsprojects.com/) - Python web framework
- [Pillow](https://pillow.readthedocs.io/) - Python imaging library
- [jQuery](https://jquery.com/) - JavaScript library
- [Font Awesome](https://fontawesome.com/) - Icons

---

⭐ **Nếu dự án này hữu ích, hãy cho một star nhé!** ⭐ 