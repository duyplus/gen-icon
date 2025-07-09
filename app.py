from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import os
import uuid
import json
import zipfile
import shutil
import logging
import sys
from datetime import datetime
from PIL import Image, ImageOps
import io
import xml.etree.ElementTree as ET
from PIL.PngImagePlugin import PngInfo

# Production configuration
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
app.config['UPLOAD_FOLDER'] = 'temp'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key-for-development')

# Production logging
if not app.debug:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    app.logger.setLevel(logging.INFO)
    app.logger.info('🚀 Favicon Generator Production Mode Started')

# Tạo thư mục temp nếu chưa tồn tại
if not os.path.exists('temp'):
    os.makedirs('temp')

# Các định dạng file được phép
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_icon_sizes(only_favicon=False, extension='png'):
    """Lấy danh sách kích thước icon cần tạo"""
    if only_favicon:
        return {'favicon.ico': 16}
    
    sizes = {
        # Web favicons
        f"favicon-16x16.{extension}": 16,
        f"favicon-32x32.{extension}": 32,
        f"favicon-96x96.{extension}": 96,
        
        # Android icons
        f"android-icon-36x36.{extension}": 36,
        f"android-icon-48x48.{extension}": 48,
        f"android-icon-72x72.{extension}": 72,
        f"android-icon-96x96.{extension}": 96,
        f"android-icon-144x144.{extension}": 144,
        f"android-icon-192x192.{extension}": 192,
        
        # Apple Touch icons
        f"apple-icon-40x40.{extension}": 40,
        f"apple-icon-58x58.{extension}": 58,
        f"apple-icon-60x60.{extension}": 60,
        f"apple-icon-76x76.{extension}": 76,
        f"apple-icon-80x80.{extension}": 80,
        f"apple-icon-87x87.{extension}": 87,
        f"apple-icon-114x114.{extension}": 114,
        f"apple-icon-120x120.{extension}": 120,
        f"apple-icon-128x128.{extension}": 128,
        f"apple-icon-136x136.{extension}": 136,
        f"apple-icon-144x144.{extension}": 144,
        f"apple-icon-152x152.{extension}": 152,
        f"apple-icon-167x167.{extension}": 167,
        f"apple-icon-180x180.{extension}": 180,
        f"apple-icon-192x192.{extension}": 192,
        f"apple-icon-1024x1024.{extension}": 1024,
        
        # Microsoft icons
        f"ms-icon-70x70.{extension}": 70,
        f"ms-icon-144x144.{extension}": 144,
        f"ms-icon-150x150.{extension}": 150,
        f"ms-icon-310x310.{extension}": 310
    }
    
    # Thêm favicon.ico
    sizes['favicon.ico'] = 16
    
    return sizes

def create_icons_from_image(image_path, sizes, temp_path, maintain_dimensions=True, original_extension='png'):
    """Tạo icons từ hình ảnh gốc"""
    original_image = Image.open(image_path)
    
    # Chuyển đổi sang RGBA nếu cần
    if original_image.mode != 'RGBA':
        original_image = original_image.convert('RGBA')
    
    for filename, size in sizes.items():
        try:
            # Tạo bản sao của hình ảnh gốc
            img = original_image.copy()
            
            if maintain_dimensions:
                # Resize giữ tỷ lệ và thêm padding trắng
                img.thumbnail((size, size), Image.Resampling.LANCZOS)
                
                # Tạo canvas trắng
                new_img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
                
                # Tính toán vị trí để căn giữa
                x = (size - img.width) // 2
                y = (size - img.height) // 2
                
                # Dán hình ảnh vào giữa canvas
                new_img.paste(img, (x, y), img)
                img = new_img
            else:
                # Resize cưỡng bức về kích thước chính xác
                img = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Lưu file
            file_path = os.path.join(temp_path, filename)
            
            if filename.endswith('.ico'):
                # Tạo file ICO
                img = img.convert('RGBA')
                img.save(file_path, format='ICO', sizes=[(size, size)])
            else:
                img.save(file_path, format='PNG')
                    
        except Exception as e:
            print(f"Lỗi khi tạo {filename}: {str(e)}")
            continue

def create_apple_icons_folder(image_path, temp_path, maintain_dimensions=True, original_extension='png'):
    """Tạo thư mục icons với tên đơn giản cho Apple"""
    icons_path = os.path.join(temp_path, 'icons')
    os.makedirs(icons_path, exist_ok=True)
    
    apple_sizes = [40, 58, 60, 76, 80, 87, 114, 120, 128, 136, 144, 152, 167, 180, 192, 1024]
    original_image = Image.open(image_path)
    
    if original_image.mode != 'RGBA':
        original_image = original_image.convert('RGBA')
    
    for size in apple_sizes:
        try:
            img = original_image.copy()
            
            if maintain_dimensions:
                img.thumbnail((size, size), Image.Resampling.LANCZOS)
                new_img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
                x = (size - img.width) // 2
                y = (size - img.height) // 2
                new_img.paste(img, (x, y), img)
                img = new_img
            else:
                img = img.resize((size, size), Image.Resampling.LANCZOS)
            
            filename = f"{size}x{size}.{original_extension}"
            file_path = os.path.join(icons_path, filename)
            
            img.save(file_path, format='PNG')
                
        except Exception as e:
            print(f"Lỗi khi tạo Apple icon {size}x{size}: {str(e)}")
            continue

def create_manifest(temp_path, extension='png'):
    """Tạo file manifest.json"""
    content_type = 'image/jpeg' if extension.lower() in ['jpg', 'jpeg'] else f'image/{extension}'
    
    manifest = {
        "name": "Generated App",
        "icons": [
            {"src": f"/android-icon-36x36.{extension}", "sizes": "36x36", "type": content_type, "density": "0.75"},
            {"src": f"/android-icon-48x48.{extension}", "sizes": "48x48", "type": content_type, "density": "1.0"},
            {"src": f"/android-icon-72x72.{extension}", "sizes": "72x72", "type": content_type, "density": "1.5"},
            {"src": f"/android-icon-96x96.{extension}", "sizes": "96x96", "type": content_type, "density": "2.0"},
            {"src": f"/android-icon-144x144.{extension}", "sizes": "144x144", "type": content_type, "density": "3.0"},
            {"src": f"/android-icon-192x192.{extension}", "sizes": "192x192", "type": content_type, "density": "4.0"}
        ]
    }
    
    with open(os.path.join(temp_path, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

def create_browserconfig(temp_path, extension='png'):
    """Tạo file browserconfig.xml"""
    browserconfig = f'''<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
    <msapplication>
        <tile>
            <square70x70logo src="/ms-icon-70x70.{extension}"/>
            <square150x150logo src="/ms-icon-150x150.{extension}"/>
            <square310x310logo src="/ms-icon-310x310.{extension}"/>
            <TileColor>#ffffff</TileColor>
        </tile>
    </msapplication>
</browserconfig>'''
    
    with open(os.path.join(temp_path, 'browserconfig.xml'), 'w', encoding='utf-8') as f:
        f.write(browserconfig)

def create_zip_file(temp_path, unique_id):
    """Tạo file ZIP chứa tất cả icons"""
    zip_path = os.path.join('temp', f'favicon-{unique_id}.zip')
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_path):
            for file in files:
                if file.startswith('original.'):
                    continue  # Bỏ qua file gốc
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_path)
                zipf.write(file_path, arcname)
    
    # Xóa thư mục temp sau khi tạo ZIP xong
    cleanup_directory(temp_path)
    
    return zip_path

def cleanup_directory(directory):
    """Xóa thư mục và nội dung"""
    if os.path.exists(directory):
        shutil.rmtree(directory)

@app.route('/health')
def health_check():
    """Health check endpoint cho Railway"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'favicon-generator'
    }), 200

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        app.logger.info(f'New favicon generation request from {request.remote_addr}')
        
        # Kiểm tra file upload
        if 'image' not in request.files:
            app.logger.warning('No file uploaded')
            return jsonify({'success': False, 'message': 'Không có file được tải lên'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Không có file được chọn'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Định dạng file không được hỗ trợ'}), 400
        
        # Lấy các tùy chọn
        maintain_dimensions = request.form.get('maintain_dimensions') == 'on'
        generation_type = request.form.get('generation_type', 'full_set')
        only_favicon = generation_type == 'favicon_only'
        
        # Tạo thư mục tạm thời
        unique_id = str(uuid.uuid4())[:16]
        temp_path = os.path.join('temp', unique_id)
        os.makedirs(temp_path, exist_ok=True)
        
        # Lưu file gốc
        filename = secure_filename(file.filename)
        original_extension = filename.rsplit('.', 1)[1].lower()
        original_path = os.path.join(temp_path, f'original.{original_extension}')
        file.save(original_path)

        # Resize về 1024x1024 nếu chưa đúng kích thước
        with Image.open(original_path) as img:
            if img.width != 1024 or img.height != 1024:
                img = img.convert('RGB')
                img = img.resize((1024, 1024), Image.Resampling.LANCZOS)
                img.save(original_path, format='PNG')
        
        # Lấy danh sách kích thước cần tạo
        sizes = get_icon_sizes(only_favicon, original_extension)
        
        # Tạo icons
        create_icons_from_image(original_path, sizes, temp_path, maintain_dimensions, original_extension)
        
        # Nếu chỉ tạo favicon
        if only_favicon:
            favicon_path = os.path.join(temp_path, 'favicon.ico')
            if os.path.exists(favicon_path):
                return jsonify({
                    'success': True,
                    'download_url': f'/direct/{unique_id}/favicon',
                    'is_single_file': True,
                    'filename': 'favicon.ico'
                })
        
        # Tạo thêm các file bổ sung cho full set
        if not only_favicon:
            create_apple_icons_folder(original_path, temp_path, maintain_dimensions, original_extension)
            create_manifest(temp_path, original_extension)
            create_browserconfig(temp_path, original_extension)
        
        # Tạo file ZIP
        zip_path = create_zip_file(temp_path, unique_id)
        
        return jsonify({
            'success': True,
            'download_url': f'/download/{os.path.basename(zip_path)}',
            'is_single_file': False
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi xử lý: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join('temp', filename)
        if not os.path.exists(file_path):
            return "File không tồn tại", 404
        
        def remove_file(response):
            try:
                os.remove(file_path)
            except:
                pass
            return response
        
        return send_file(file_path, as_attachment=True, download_name=filename)
    except Exception as e:
        return f"Lỗi tải file: {str(e)}", 500

@app.route('/direct/<file_id>/<file_type>')
def download_direct(file_id, file_type):
    try:
        if file_type == 'favicon':
            temp_path = os.path.join('temp', file_id)
            favicon_path = os.path.join(temp_path, 'favicon.ico')
            
            if not os.path.exists(favicon_path):
                return "File không tồn tại", 404
            
            return send_file(favicon_path, as_attachment=True, download_name='favicon.ico')
        
        return "Loại file không hỗ trợ", 404
    except Exception as e:
        return f"Lỗi tải file: {str(e)}", 500

@app.route('/cleanup/<file_id>', methods=['DELETE'])
def cleanup(file_id):
    try:
        # Kiểm tra nếu là file ZIP
        if file_id.endswith('.zip'):
            # Chỉ cần xóa file ZIP (thư mục temp đã bị xóa khi tạo ZIP)
            zip_path = os.path.join('temp', file_id)
            if os.path.exists(zip_path):
                os.remove(zip_path)
        else:
            # Xóa thư mục (cho trường hợp favicon only)
            temp_path = os.path.join('temp', file_id)
            if os.path.exists(temp_path):
                cleanup_directory(temp_path)
        
        return jsonify({'success': True, 'message': 'Đã dọn dẹp thành công!'})
    except Exception as e:
        return jsonify({'success': True, 'message': 'Đã dọn dẹp thành công!'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)