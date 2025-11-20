from flask import Flask, render_template, request, send_file, jsonify
import os
import numpy as np
from PIL import Image
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime, timedelta
from rembg import remove

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# 폴더 생성
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def resize_images(img1, img2, resize_mode='fit'):
    """
    두 이미지의 크기를 조정합니다.

    :param img1: 첫 번째 이미지
    :param img2: 두 번째 이미지
    :param resize_mode: 크기 조정 모드
        - 'fit': 첫 번째 이미지 크기에 맞춤 (기존 방식)
        - 'center': 두 이미지를 더 큰 캔버스에 중앙 정렬
        - 'contain': 비율을 유지하며 큰 캔버스에 맞춤
        - 'smart': AI 기반 객체 감지 및 정렬
        - 'nobg': 배경 제거 후 객체 크기 동일하게 정규화
    :return: 크기가 조정된 두 이미지
    """
    if resize_mode == 'fit':
        # 기존 방식: 두 번째 이미지를 첫 번째 크기에 맞춤
        img2_resized = img2.resize(img1.size, Image.Resampling.LANCZOS)
        return img1, img2_resized

    elif resize_mode == 'center':
        # 두 이미지를 더 큰 캔버스 중앙에 배치
        max_width = max(img1.width, img2.width)
        max_height = max(img1.height, img2.height)

        # 새 캔버스 생성
        new_img1 = Image.new('RGBA', (max_width, max_height), (0, 0, 0, 0))
        new_img2 = Image.new('RGBA', (max_width, max_height), (0, 0, 0, 0))

        # 중앙에 붙여넣기
        offset1 = ((max_width - img1.width) // 2, (max_height - img1.height) // 2)
        offset2 = ((max_width - img2.width) // 2, (max_height - img2.height) // 2)

        new_img1.paste(img1, offset1)
        new_img2.paste(img2, offset2)

        return new_img1, new_img2

    elif resize_mode == 'contain':
        # 비율을 유지하며 큰 캔버스에 맞춤
        max_width = max(img1.width, img2.width)
        max_height = max(img1.height, img2.height)

        # 각 이미지를 비율 유지하며 리사이즈
        img1_ratio = min(max_width / img1.width, max_height / img1.height)
        img2_ratio = min(max_width / img2.width, max_height / img2.height)

        new_size1 = (int(img1.width * img1_ratio), int(img1.height * img1_ratio))
        new_size2 = (int(img2.width * img2_ratio), int(img2.height * img2_ratio))

        img1_resized = img1.resize(new_size1, Image.Resampling.LANCZOS)
        img2_resized = img2.resize(new_size2, Image.Resampling.LANCZOS)

        # 새 캔버스에 중앙 배치
        new_img1 = Image.new('RGBA', (max_width, max_height), (0, 0, 0, 0))
        new_img2 = Image.new('RGBA', (max_width, max_height), (0, 0, 0, 0))

        offset1 = ((max_width - new_size1[0]) // 2, (max_height - new_size1[1]) // 2)
        offset2 = ((max_width - new_size2[0]) // 2, (max_height - new_size2[1]) // 2)

        new_img1.paste(img1_resized, offset1)
        new_img2.paste(img2_resized, offset2)

        return new_img1, new_img2

    elif resize_mode == 'smart':
        # AI 기반 객체 감지 및 정렬
        return smart_align_images(img1, img2)

    elif resize_mode == 'nobg':
        # 배경 제거 후 객체 크기 동일하게 정규화
        return normalize_objects_with_bg_removal(img1, img2)

    else:
        # 기본값
        return img1, img2.resize(img1.size, Image.Resampling.LANCZOS)


def get_object_bounds(img):
    """
    AI를 사용해 이미지에서 주요 객체의 경계를 찾습니다.

    :param img: PIL 이미지
    :return: (x, y, width, height) 객체의 바운딩 박스
    """
    # PIL 이미지를 바이트로 변환
    import io
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    # 배경 제거로 주요 객체 감지
    output = remove(img_byte_arr)
    no_bg_img = Image.open(io.BytesIO(output)).convert('RGBA')

    # numpy 배열로 변환
    img_array = np.array(no_bg_img)

    # 알파 채널에서 객체가 있는 영역 찾기
    alpha = img_array[:, :, 3]
    coords = np.argwhere(alpha > 0)

    if len(coords) == 0:
        # 객체를 찾지 못한 경우 전체 이미지 반환
        return 0, 0, img.width, img.height

    # 바운딩 박스 계산
    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)

    return x_min, y_min, x_max - x_min, y_max - y_min


def smart_align_images(img1, img2):
    """
    AI를 사용해 두 이미지의 주요 객체를 감지하고 크기와 위치를 정렬합니다.

    :param img1: 첫 번째 이미지
    :param img2: 두 번째 이미지
    :return: 정렬된 두 이미지
    """
    # 각 이미지에서 객체 바운딩 박스 찾기
    x1, y1, w1, h1 = get_object_bounds(img1)
    x2, y2, w2, h2 = get_object_bounds(img2)

    # 두 객체의 크기 비율 계산
    scale1 = max(w1, h1)
    scale2 = max(w2, h2)

    # 더 큰 객체를 기준으로 크기 조정 비율 계산
    if scale1 > scale2:
        scale_ratio = scale2 / scale1
        # img1의 객체를 img2 크기에 맞춤
        new_size1 = (int(img1.width * scale_ratio), int(img1.height * scale_ratio))
        img1_resized = img1.resize(new_size1, Image.Resampling.LANCZOS)
        img2_resized = img2
        # 새로운 바운딩 박스 계산
        x1, y1, w1, h1 = int(x1 * scale_ratio), int(y1 * scale_ratio), int(w1 * scale_ratio), int(h1 * scale_ratio)
    else:
        scale_ratio = scale1 / scale2
        # img2의 객체를 img1 크기에 맞춤
        new_size2 = (int(img2.width * scale_ratio), int(img2.height * scale_ratio))
        img1_resized = img1
        img2_resized = img2.resize(new_size2, Image.Resampling.LANCZOS)
        # 새로운 바운딩 박스 계산
        x2, y2, w2, h2 = int(x2 * scale_ratio), int(y2 * scale_ratio), int(w2 * scale_ratio), int(h2 * scale_ratio)

    # 캔버스 크기 계산 (여유 공간 포함)
    max_width = max(img1_resized.width, img2_resized.width) + 100
    max_height = max(img1_resized.height, img2_resized.height) + 100

    # 새 캔버스 생성
    new_img1 = Image.new('RGBA', (max_width, max_height), (0, 0, 0, 0))
    new_img2 = Image.new('RGBA', (max_width, max_height), (0, 0, 0, 0))

    # 객체 중심을 캔버스 중심에 맞춤
    center_x1 = x1 + w1 // 2
    center_y1 = y1 + h1 // 2
    center_x2 = x2 + w2 // 2
    center_y2 = y2 + h2 // 2

    canvas_center_x = max_width // 2
    canvas_center_y = max_height // 2

    offset1 = (canvas_center_x - center_x1, canvas_center_y - center_y1)
    offset2 = (canvas_center_x - center_x2, canvas_center_y - center_y2)

    new_img1.paste(img1_resized, offset1, img1_resized)
    new_img2.paste(img2_resized, offset2, img2_resized)

    return new_img1, new_img2


def normalize_objects_with_bg_removal(img1, img2):
    """
    두 이미지의 배경을 제거하고 객체 크기를 동일하게 정규화합니다.

    :param img1: 첫 번째 이미지
    :param img2: 두 번째 이미지
    :return: 배경이 제거되고 크기가 정규화된 두 이미지
    """
    import io

    # 배경 제거
    def remove_bg(img):
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        output = remove(img_byte_arr)
        return Image.open(io.BytesIO(output)).convert('RGBA')

    nobg1 = remove_bg(img1)
    nobg2 = remove_bg(img2)

    # 각 이미지에서 객체의 실제 경계 찾기
    def get_tight_bounds(img):
        img_array = np.array(img)
        alpha = img_array[:, :, 3]
        coords = np.argwhere(alpha > 0)

        if len(coords) == 0:
            return None, None

        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)

        # 객체만 크롭
        cropped = img.crop((x_min, y_min, x_max + 1, y_max + 1))
        return cropped, (x_max - x_min + 1, y_max - y_min + 1)

    obj1, size1 = get_tight_bounds(nobg1)
    obj2, size2 = get_tight_bounds(nobg2)

    if obj1 is None or obj2 is None:
        # 객체를 찾지 못한 경우 원본 반환
        return img1, img2

    # 두 객체의 최대 크기 계산
    max_dim1 = max(size1)
    max_dim2 = max(size2)

    # 더 큰 객체를 기준으로 크기 정규화
    target_size = max(max_dim1, max_dim2)

    # 각 객체를 동일한 크기로 리사이즈 (비율 유지)
    def resize_to_target(obj, current_max):
        scale = target_size / current_max
        new_w = int(obj.width * scale)
        new_h = int(obj.height * scale)
        return obj.resize((new_w, new_h), Image.Resampling.LANCZOS)

    obj1_resized = resize_to_target(obj1, max_dim1)
    obj2_resized = resize_to_target(obj2, max_dim2)

    # 여유 공간을 포함한 캔버스 크기 계산
    canvas_size = target_size + 200

    # 새 캔버스에 중앙 배치
    def center_on_canvas(obj, canvas_size):
        canvas = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
        offset = ((canvas_size - obj.width) // 2, (canvas_size - obj.height) // 2)
        canvas.paste(obj, offset, obj)
        return canvas

    result1 = center_on_canvas(obj1_resized, canvas_size)
    result2 = center_on_canvas(obj2_resized, canvas_size)

    return result1, result2


def generate_gif(img1_path, img2_path, output_path, frames_per_beat=12, duration_ms=100, resize_mode='fit'):
    """
    두 이미지를 부드럽게 연결하는 루프 GIF를 생성합니다.

    :param resize_mode: 이미지 크기 조정 모드 ('fit', 'center', 'contain')
    """
    # 이미지 로드
    img1 = Image.open(img1_path).convert("RGBA")
    img2 = Image.open(img2_path).convert("RGBA")

    # 크기 조정
    img1, img2 = resize_images(img1, img2, resize_mode)

    # 이미지 데이터 변환 (Numpy array)
    arr1 = np.array(img1, dtype=float)
    arr2 = np.array(img2, dtype=float)

    generated_frames = []

    # 1. A -> B (갈 때)
    for i in range(frames_per_beat):
        alpha = i / frames_per_beat
        # 선형 보간 (Linear Interpolation)
        blended = (1 - alpha) * arr1 + alpha * arr2
        frame_img = Image.fromarray(np.uint8(blended), mode='RGBA')
        generated_frames.append(frame_img)

    # 2. B -> A (돌아올 때) - 루프를 위해
    for i in range(frames_per_beat):
        alpha = i / frames_per_beat
        blended = (1 - alpha) * arr2 + alpha * arr1
        frame_img = Image.fromarray(np.uint8(blended), mode='RGBA')
        generated_frames.append(frame_img)

    # GIF 저장
    generated_frames[0].save(
        output_path,
        save_all=True,
        append_images=generated_frames[1:],
        duration=duration_ms,
        loop=0,  # 무한 루프
        disposal=2
    )
    return output_path

def cleanup_old_files():
    """24시간 이상 된 파일들을 삭제"""
    now = datetime.now()
    for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if now - file_time > timedelta(hours=24):
                    os.remove(filepath)

@app.route('/')
def index():
    cleanup_old_files()
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        # 파일 검증
        if 'image1' not in request.files or 'image2' not in request.files:
            return jsonify({'error': '두 개의 이미지를 모두 업로드해주세요.'}), 400

        file1 = request.files['image1']
        file2 = request.files['image2']

        if file1.filename == '' or file2.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400

        if not allowed_file(file1.filename) or not allowed_file(file2.filename):
            return jsonify({'error': '지원되지 않는 파일 형식입니다. (png, jpg, jpeg, gif, webp만 가능)'}), 400

        # 파라미터 가져오기
        frames_per_beat = int(request.form.get('frames', 12))
        duration_ms = int(request.form.get('duration', 100))
        resize_mode = request.form.get('resize_mode', 'center')

        # 유효성 검사
        if not (5 <= frames_per_beat <= 30):
            frames_per_beat = 12
        if not (20 <= duration_ms <= 500):
            duration_ms = 100
        if resize_mode not in ['fit', 'center', 'contain', 'smart', 'nobg']:
            resize_mode = 'smart'

        # 고유 파일명 생성
        unique_id = str(uuid.uuid4())

        # 파일 저장
        ext1 = secure_filename(file1.filename).rsplit('.', 1)[1].lower()
        ext2 = secure_filename(file2.filename).rsplit('.', 1)[1].lower()

        img1_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_1.{ext1}")
        img2_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_2.{ext2}")
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{unique_id}.gif")

        file1.save(img1_path)
        file2.save(img2_path)

        # GIF 생성
        generate_gif(img1_path, img2_path, output_path, frames_per_beat, duration_ms, resize_mode)

        # 업로드된 원본 이미지 삭제 (선택사항)
        os.remove(img1_path)
        os.remove(img2_path)

        return jsonify({
            'success': True,
            'filename': f"{unique_id}.gif"
        })

    except Exception as e:
        return jsonify({'error': f'GIF 생성 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/remove-background', methods=['POST'])
def remove_background():
    try:
        # 파일 검증
        if 'image' not in request.files:
            return jsonify({'error': '이미지를 업로드해주세요.'}), 400

        file = request.files['image']

        if file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': '지원되지 않는 파일 형식입니다.'}), 400

        # 고유 파일명 생성
        unique_id = str(uuid.uuid4())
        ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()

        # 원본 이미지 저장
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_input.{ext}")
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{unique_id}_nobg.png")

        file.save(input_path)

        # 배경 제거
        with open(input_path, 'rb') as i:
            input_image = i.read()
            output_image = remove(input_image)

        # 배경 제거된 이미지 저장
        with open(output_path, 'wb') as o:
            o.write(output_image)

        # 원본 이미지 삭제
        os.remove(input_path)

        return jsonify({
            'success': True,
            'filename': f"{unique_id}_nobg.png"
        })

    except Exception as e:
        return jsonify({'error': f'배경 제거 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/download/<filename>')
def download(filename):
    try:
        # 보안을 위해 파일명 검증
        if not (filename.endswith('.gif') or filename.endswith('.png')):
            return "Invalid file", 400

        filepath = os.path.join(app.config['OUTPUT_FOLDER'], secure_filename(filename))

        if not os.path.exists(filepath):
            return "File not found", 404

        # 파일 타입에 따라 MIME 타입 및 다운로드 이름 설정
        if filename.endswith('.gif'):
            mimetype = 'image/gif'
            download_name = 'animated.gif'
        else:  # .png
            mimetype = 'image/png'
            download_name = 'no_background.png'

        return send_file(filepath, mimetype=mimetype, as_attachment=True, download_name=download_name)
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
