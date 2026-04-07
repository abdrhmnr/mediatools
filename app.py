from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import os, uuid, threading, time, json
from pathlib import Path
from modules import pdf_tools, image_tools, video_tools, downloader, ocr_tools

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['OUTPUT_FOLDER'] = 'static/outputs'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Task tracking
tasks = {}

def allowed_file(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

def save_upload(file):
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    uid = str(uuid.uuid4())
    fname = f"{uid}.{ext}" if ext else uid
    path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
    file.save(path)
    return path, fname

def run_task(task_id, fn, *args, **kwargs):
    try:
        tasks[task_id]['status'] = 'running'
        result = fn(*args, **kwargs)
        tasks[task_id]['status'] = 'done'
        tasks[task_id]['result'] = result
    except Exception as e:
        tasks[task_id]['status'] = 'error'
        tasks[task_id]['error'] = str(e)

def start_task(fn, *args, **kwargs):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'pending', 'result': None, 'error': None}
    t = threading.Thread(target=run_task, args=(task_id, fn, *args), kwargs=kwargs)
    t.daemon = True
    t.start()
    return task_id

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/task/<task_id>')
def get_task(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(task)

@app.route('/api/download-result/<filename>')
def download_result(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

# ─── PDF Routes ───────────────────────────────────────────────
@app.route('/api/pdf/merge', methods=['POST'])
def pdf_merge():
    files = request.files.getlist('files')
    if len(files) < 2:
        return jsonify({'error': 'Need at least 2 PDF files'}), 400
    paths = []
    for f in files:
        p, _ = save_upload(f)
        paths.append(p)
    out = os.path.join(app.config['OUTPUT_FOLDER'], f"{uuid.uuid4()}_merged.pdf")
    task_id = start_task(pdf_tools.merge_pdfs, paths, out)
    return jsonify({'task_id': task_id})

@app.route('/api/pdf/images-to-pdf', methods=['POST'])
def images_to_pdf():
    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'No files provided'}), 400
    paths = []
    for f in files:
        p, _ = save_upload(f)
        paths.append(p)
    out = os.path.join(app.config['OUTPUT_FOLDER'], f"{uuid.uuid4()}_converted.pdf")
    task_id = start_task(pdf_tools.images_to_pdf, paths, out)
    return jsonify({'task_id': task_id})

@app.route('/api/pdf/compress', methods=['POST'])
def pdf_compress():
    f = request.files.get('file')
    if not f:
        return jsonify({'error': 'No file provided'}), 400
    p, _ = save_upload(f)
    out = os.path.join(app.config['OUTPUT_FOLDER'], f"{uuid.uuid4()}_compressed.pdf")
    task_id = start_task(pdf_tools.compress_pdf, p, out)
    return jsonify({'task_id': task_id})

# ─── Image Routes ─────────────────────────────────────────────
@app.route('/api/image/convert', methods=['POST'])
def image_convert():
    f = request.files.get('file')
    fmt = request.form.get('format', 'png').lower()
    if not f:
        return jsonify({'error': 'No file provided'}), 400
    p, _ = save_upload(f)
    out = os.path.join(app.config['OUTPUT_FOLDER'], f"{uuid.uuid4()}_converted.{fmt}")
    task_id = start_task(image_tools.convert_image, p, out, fmt)
    return jsonify({'task_id': task_id})

@app.route('/api/image/compress', methods=['POST'])
def image_compress():
    f = request.files.get('file')
    quality = int(request.form.get('quality', 75))
    if not f:
        return jsonify({'error': 'No file provided'}), 400
    p, _ = save_upload(f)
    ext = f.filename.rsplit('.', 1)[1].lower()
    out = os.path.join(app.config['OUTPUT_FOLDER'], f"{uuid.uuid4()}_compressed.{ext}")
    task_id = start_task(image_tools.compress_image, p, out, quality)
    return jsonify({'task_id': task_id})

@app.route('/api/image/resize', methods=['POST'])
def image_resize():
    f = request.files.get('file')
    width = request.form.get('width')
    height = request.form.get('height')
    if not f:
        return jsonify({'error': 'No file provided'}), 400
    p, _ = save_upload(f)
    ext = f.filename.rsplit('.', 1)[1].lower()
    out = os.path.join(app.config['OUTPUT_FOLDER'], f"{uuid.uuid4()}_resized.{ext}")
    task_id = start_task(image_tools.resize_image, p, out,
                         int(width) if width else None,
                         int(height) if height else None)
    return jsonify({'task_id': task_id})

# ─── Video/Audio Routes ───────────────────────────────────────
@app.route('/api/video/convert', methods=['POST'])
def video_convert():
    f = request.files.get('file')
    fmt = request.form.get('format', 'mp4')
    quality = request.form.get('quality', 'medium')
    if not f:
        return jsonify({'error': 'No file provided'}), 400
    p, _ = save_upload(f)
    out = os.path.join(app.config['OUTPUT_FOLDER'], f"{uuid.uuid4()}_converted.{fmt}")
    task_id = start_task(video_tools.convert_video, p, out, fmt, quality)
    return jsonify({'task_id': task_id})

@app.route('/api/video/extract-audio', methods=['POST'])
def video_extract_audio():
    f = request.files.get('file')
    fmt = request.form.get('format', 'mp3')
    if not f:
        return jsonify({'error': 'No file provided'}), 400
    p, _ = save_upload(f)
    out = os.path.join(app.config['OUTPUT_FOLDER'], f"{uuid.uuid4()}_audio.{fmt}")
    task_id = start_task(video_tools.extract_audio, p, out, fmt)
    return jsonify({'task_id': task_id})

@app.route('/api/video/trim', methods=['POST'])
def video_trim():
    f = request.files.get('file')
    start = request.form.get('start', '0')
    end = request.form.get('end')
    if not f or not end:
        return jsonify({'error': 'File and end time required'}), 400
    p, _ = save_upload(f)
    ext = f.filename.rsplit('.', 1)[1].lower()
    out = os.path.join(app.config['OUTPUT_FOLDER'], f"{uuid.uuid4()}_trimmed.{ext}")
    task_id = start_task(video_tools.trim_video, p, out, start, end)
    return jsonify({'task_id': task_id})

@app.route('/api/video/compress', methods=['POST'])
def video_compress():
    f = request.files.get('file')
    quality = request.form.get('quality', 'medium')
    if not f:
        return jsonify({'error': 'No file provided'}), 400
    p, _ = save_upload(f)
    ext = f.filename.rsplit('.', 1)[1].lower() or 'mp4'
    out = os.path.join(app.config['OUTPUT_FOLDER'], f"{uuid.uuid4()}_compressed.{ext}")
    task_id = start_task(video_tools.compress_video, p, out, quality)
    return jsonify({'task_id': task_id})

@app.route('/api/audio/convert', methods=['POST'])
def audio_convert():
    f = request.files.get('file')
    fmt = request.form.get('format', 'mp3')
    if not f:
        return jsonify({'error': 'No file provided'}), 400
    p, _ = save_upload(f)
    out = os.path.join(app.config['OUTPUT_FOLDER'], f"{uuid.uuid4()}_converted.{fmt}")
    task_id = start_task(video_tools.convert_audio, p, out, fmt)
    return jsonify({'task_id': task_id})

# ─── Downloader Routes ────────────────────────────────────────
@app.route('/api/download/url', methods=['POST'])
def download_url():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL required'}), 400
    task_id = start_task(downloader.download_file, url, app.config['OUTPUT_FOLDER'])
    return jsonify({'task_id': task_id})

@app.route('/api/download/youtube', methods=['POST'])
def download_youtube():
    data = request.get_json()
    url = data.get('url')
    fmt = data.get('format', 'video')  # video or audio
    quality = data.get('quality', 'best')
    if not url:
        return jsonify({'error': 'URL required'}), 400
    task_id = start_task(downloader.download_youtube, url, app.config['OUTPUT_FOLDER'], fmt, quality)
    return jsonify({'task_id': task_id})

@app.route('/api/download/social', methods=['POST'])
def download_social():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL required'}), 400
    task_id = start_task(downloader.download_social, url, app.config['OUTPUT_FOLDER'])
    return jsonify({'task_id': task_id})

# ─── OCR Routes ───────────────────────────────────────────────
@app.route('/api/ocr/extract', methods=['POST'])
def ocr_extract():
    f = request.files.get('file')
    lang = request.form.get('lang', 'auto')  # auto, eng, ara, both
    engine = request.form.get('engine', 'easyocr')  # easyocr or tesseract
    if not f:
        return jsonify({'error': 'No file provided'}), 400
    p, _ = save_upload(f)
    task_id = start_task(ocr_tools.extract_text, p, lang, engine)
    return jsonify({'task_id': task_id})

# ─── Cleanup ─────────────────────────────────────────────────
def cleanup_old_files():
    """Delete files older than 1 hour"""
    while True:
        time.sleep(3600)
        for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
            for f in Path(folder).iterdir():
                if time.time() - f.stat().st_mtime > 3600:
                    try:
                        f.unlink()
                    except:
                        pass

cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
