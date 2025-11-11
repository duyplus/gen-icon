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
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024  # 15MB max file size
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

def get_icon_sizes(only_favicon=False):
    """Lấy danh sách kích thước icon cần tạo - luôn sử dụng đuôi PNG"""
    if only_favicon:
        return {'favicon.ico': 16}
    
    sizes = {
        # Web favicons
        "favicon-16x16.png": 16,
        "favicon-32x32.png": 32,
        "favicon-96x96.png": 96,
        
        # Android icons
        "android-icon-36x36.png": 36,
        "android-icon-48x48.png": 48,
        "android-icon-72x72.png": 72,
        "android-icon-96x96.png": 96,
        "android-icon-144x144.png": 144,
        "android-icon-192x192.png": 192,
        
        # Apple Touch icons
        "apple-icon-40x40.png": 40,
        "apple-icon-58x58.png": 58,
        "apple-icon-60x60.png": 60,
        "apple-icon-76x76.png": 76,
        "apple-icon-80x80.png": 80,
        "apple-icon-87x87.png": 87,
        "apple-icon-114x114.png": 114,
        "apple-icon-120x120.png": 120,
        "apple-icon-128x128.png": 128,
        "apple-icon-136x136.png": 136,
        "apple-icon-144x144.png": 144,
        "apple-icon-152x152.png": 152,
        "apple-icon-167x167.png": 167,
        "apple-icon-180x180.png": 180,
        "apple-icon-192x192.png": 192,
        "apple-icon-1024x1024.png": 1024,
        
        # Microsoft icons
        "ms-icon-70x70.png": 70,
        "ms-icon-144x144.png": 144,
        "ms-icon-150x150.png": 150,
        "ms-icon-310x310.png": 310
    }
    
    # Thêm favicon.ico
    sizes['favicon.ico'] = 16
    
    return sizes

def has_transparency(img):
    """Kiểm tra xem ảnh có nền trong suốt không"""
    if img.mode == 'RGBA':
        # Lấy alpha channel
        alpha = img.split()[-1]
        # Kiểm tra xem có pixel nào có alpha < 255 không
        return alpha.getbbox() is not None and min(alpha.getextrema()) < 255
    elif img.mode == 'P' and 'transparency' in img.info:
        return True
    return False

def add_white_background(img):
    """Thêm nền trắng cho ảnh có nền trong suốt"""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Tạo background trắng
    background = Image.new('RGB', img.size, (255, 255, 255))
    # Paste ảnh lên background, sử dụng alpha channel làm mask
    background.paste(img, mask=img.split()[-1])
    
    return background

def compress_image(img, target_size=None):
    """
    Compress ảnh để giảm kích thước file bằng cách giảm chất lượng nhẹ
    """
    # Đảm bảo là RGB mode
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Không cần quantization vì nó làm tăng kích thước file
    # Chỉ cần lưu với quality thấp hơn
    return img

def save_optimized_png(img, path, max_quality=80):
    """
    Lưu PNG với compression mạnh sử dụng palette mode để giảm kích thước đáng kể
    """
    # Log kích thước trước khi compress
    original_size = img.size
    app.logger.info(f'Compressing image {original_size} to: {path}')
    
    # Đảm bảo mode RGB
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Convert sang P mode (palette) với 256 màu - giống pngquant
    # Sử dụng dithering để giữ chất lượng
    img_palette = img.convert('P', palette=Image.Palette.ADAPTIVE, colors=256)
    
    # Lưu với compression tối đa
    img_palette.save(
        path,
        format='PNG',
        optimize=True,
        compress_level=9
    )
    
    # Log kích thước file sau khi compress
    if os.path.exists(path):
        file_size = os.path.getsize(path) / 1024  # KB
        app.logger.info(f'Compressed PNG saved: {path} ({file_size:.1f} KB)')
    
    return path

def create_icons_from_image(image_path, sizes, temp_path, maintain_dimensions=True):
    """Tạo icons từ hình ảnh gốc - luôn xuất ra PNG"""
    original_image = Image.open(image_path)
    
    # Kiểm tra và xử lý nền trong suốt
    if has_transparency(original_image):
        app.logger.info('Detected transparent background, adding white background')
        original_image = add_white_background(original_image)
    else:
        # Chuyển đổi sang RGB nếu không có alpha
        if original_image.mode != 'RGB':
            original_image = original_image.convert('RGB')
    
    for filename, size in sizes.items():
        try:
            # Tạo bản sao của hình ảnh gốc
            img = original_image.copy()
            
            if maintain_dimensions:
                # Resize giữ tỷ lệ và thêm padding trắng
                img.thumbnail((size, size), Image.Resampling.LANCZOS)
                
                # Tạo canvas trắng
                new_img = Image.new('RGB', (size, size), (255, 255, 255))
                
                # Tính toán vị trí để căn giữa
                x = (size - img.width) // 2
                y = (size - img.height) // 2
                
                # Dán hình ảnh vào giữa canvas
                new_img.paste(img, (x, y))
                img = new_img
            else:
                # Resize cưỡng bức về kích thước chính xác
                img = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Lưu file
            file_path = os.path.join(temp_path, filename)
            
            if filename.endswith('.ico'):
                # Tạo file ICO - chuyển về RGBA cho ICO
                img_ico = img.convert('RGBA')
                img_ico.save(file_path, format='ICO', sizes=[(size, size)])
            else:
                # Compress cho size 1024x1024, các size khác giữ nguyên
                if size == 1024:
                    save_optimized_png(img, file_path, max_quality=80)
                else:
                    img.save(file_path, format='PNG', optimize=True)
                    
        except Exception as e:
            app.logger.error(f"Lỗi khi tạo {filename}: {str(e)}")
            continue

def create_apple_icons_folder(image_path, temp_path, maintain_dimensions=True):
    """Tạo thư mục icons với tên đơn giản cho Apple - luôn xuất ra PNG"""
    icons_path = os.path.join(temp_path, 'icons')
    os.makedirs(icons_path, exist_ok=True)
    
    apple_sizes = [48, 72, 96, 120, 144, 152, 167, 180, 192, 1024]
    original_image = Image.open(image_path)
    
    # Kiểm tra và xử lý nền trong suốt
    if has_transparency(original_image):
        original_image = add_white_background(original_image)
    else:
        if original_image.mode != 'RGB':
            original_image = original_image.convert('RGB')
    
    for size in apple_sizes:
        try:
            img = original_image.copy()
            
            if maintain_dimensions:
                img.thumbnail((size, size), Image.Resampling.LANCZOS)
                new_img = Image.new('RGB', (size, size), (255, 255, 255))
                x = (size - img.width) // 2
                y = (size - img.height) // 2
                new_img.paste(img, (x, y))
                img = new_img
            else:
                img = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Luôn sử dụng đuôi .png
            filename = f"{size}x{size}.png"
            file_path = os.path.join(icons_path, filename)
            
            # Chỉ compress cho size 1024x1024, các size khác giữ nguyên
            if size == 1024:
                save_optimized_png(img, file_path, max_quality=80)
            else:
                img.save(file_path, format='PNG', optimize=True)
                
        except Exception as e:
            app.logger.error(f"Lỗi khi tạo Apple icon {size}x{size}: {str(e)}")
            continue

def create_manifest(temp_path):
    """Tạo file manifest.json - luôn sử dụng PNG"""
    manifest = {
        "name": "Generated App",
        "icons": [
            {"src": "/android-icon-36x36.png", "sizes": "36x36", "type": "image/png", "density": "0.75"},
            {"src": "/android-icon-48x48.png", "sizes": "48x48", "type": "image/png", "density": "1.0"},
            {"src": "/android-icon-72x72.png", "sizes": "72x72", "type": "image/png", "density": "1.5"},
            {"src": "/android-icon-96x96.png", "sizes": "96x96", "type": "image/png", "density": "2.0"},
            {"src": "/android-icon-144x144.png", "sizes": "144x144", "type": "image/png", "density": "3.0"},
            {"src": "/android-icon-192x192.png", "sizes": "192x192", "type": "image/png", "density": "4.0"}
        ]
    }
    
    with open(os.path.join(temp_path, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

def create_browserconfig(temp_path):
    """Tạo file browserconfig.xml - luôn sử dụng PNG"""
    browserconfig = '''<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
    <msapplication>
        <tile>
            <square70x70logo src="/ms-icon-70x70.png"/>
            <square150x150logo src="/ms-icon-150x150.png"/>
            <square310x310logo src="/ms-icon-310x310.png"/>
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

        # Mở và tối ưu hóa ảnh
        with Image.open(original_path) as img:
            app.logger.info(f'Original image: {img.size}, mode: {img.mode}, format: {original_extension}')
            
            # Kiểm tra và xử lý nền trong suốt
            if has_transparency(img):
                app.logger.info('Adding white background to transparent image')
                img = add_white_background(img)
            else:
                # Chuyển sang RGB nếu chưa phải
                if img.mode != 'RGB':
                    img = img.convert('RGB')
            
            # Tối ưu hóa kích thước về 1024x1024
            if img.width != 1024 or img.height != 1024:
                app.logger.info(f'Resizing from {img.size} to 1024x1024')
                
                if maintain_dimensions:
                    # Giữ tỷ lệ: resize vào 1024x1024 với padding trắng
                    img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                    
                    # Tạo canvas trắng 1024x1024
                    new_img = Image.new('RGB', (1024, 1024), (255, 255, 255))
                    
                    # Tính toán vị trí để căn giữa
                    x = (1024 - img.width) // 2
                    y = (1024 - img.height) // 2
                    
                    # Dán hình ảnh vào giữa canvas
                    new_img.paste(img, (x, y))
                    img = new_img
                    app.logger.info(f'Resized with aspect ratio maintained, centered on 1024x1024 canvas')
                else:
                    # Không giữ tỷ lệ: resize cưỡng bức thành 1024x1024
                    img = img.resize((1024, 1024), Image.Resampling.LANCZOS)
                    app.logger.info(f'Resized to exact 1024x1024 (aspect ratio not maintained)')
            
            # Lưu lại ảnh đã tối ưu hóa - luôn chuyển sang PNG với compression
            png_path = os.path.join(temp_path, 'original.png')
            save_optimized_png(img, png_path, max_quality=80)
            app.logger.info(f'Optimized image saved as PNG: {png_path}')
            
            # Xóa file gốc nếu không phải PNG
            if original_extension.lower() != 'png':
                os.remove(original_path)
                app.logger.info(f'Removed original {original_extension} file, converted to PNG')
                original_path = png_path
        
        # Lấy danh sách kích thước cần tạo
        sizes = get_icon_sizes(only_favicon)
        
        # Tạo icons
        create_icons_from_image(original_path, sizes, temp_path, maintain_dimensions)
        
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
            create_apple_icons_folder(original_path, temp_path, maintain_dimensions)
            create_manifest(temp_path)
            create_browserconfig(temp_path)
        
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