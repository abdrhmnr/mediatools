# 🎬 MediaTools PRO

تطبيق ويب شامل لتحويل ومعالجة الوسائط — PDF، صور، فيديو، صوت، تنزيل، OCR

A full-featured web app for media processing — PDF, Images, Video, Audio, Download, OCR

---

## ✨ المميزات / Features

| الأداة | الوظيفة |
|--------|---------|
| PDF | دمج، تحويل صور→PDF، ضغط |
| صور | تحويل الصيغة، ضغط، تغيير الأبعاد |
| فيديو | تحويل، ضغط، قص، استخراج صوت |
| صوت | تحويل بين MP3/AAC/FLAC/WAV/OGG |
| تنزيل | URL مباشر، YouTube، سوشيال ميديا |
| OCR | استخراج نصوص عربية/إنجليزية |

---

## 🚀 التشغيل المحلي / Local Setup

### الطريقة 1: Python مباشرة

```bash
# 1. تثبيت متطلبات النظام (Ubuntu/Debian)
sudo apt-get install ffmpeg tesseract-ocr tesseract-ocr-ara tesseract-ocr-eng

# 2. تثبيت مكتبات Python
pip install -r requirements.txt

# 3. تشغيل التطبيق
python app.py
```

افتح المتصفح على: http://localhost:5000

### الطريقة 2: macOS

```bash
brew install ffmpeg tesseract tesseract-lang
pip install -r requirements.txt
python app.py
```

### الطريقة 3: Windows

1. حمّل FFmpeg من https://ffmpeg.org/download.html وأضفه لـ PATH
2. حمّل Tesseract من https://github.com/UB-Mannheim/tesseract/wiki
3. ```pip install -r requirements.txt && python app.py```

---

## 🐳 Docker (للنشر على السيرفر)

```bash
# بناء وتشغيل
docker-compose up -d

# مشاهدة السجلات
docker-compose logs -f

# إيقاف
docker-compose down
```

---

## 🔧 متطلبات النظام / System Requirements

- **Python**: 3.10+
- **FFmpeg**: لتحويل الفيديو والصوت
- **Tesseract**: لـ OCR (اختياري — يمكن الاستخدام مع EasyOCR فقط)
- **RAM**: 2GB minimum (4GB مستحسن للفيديو)
- **Disk**: مساحة كافية للملفات المؤقتة

---

## 📁 هيكل المشروع / Project Structure

```
mediatools/
├── app.py                 # Flask main app
├── modules/
│   ├── pdf_tools.py       # PDF operations
│   ├── image_tools.py     # Image operations
│   ├── video_tools.py     # Video/Audio (FFmpeg)
│   ├── downloader.py      # yt-dlp downloader
│   └── ocr_tools.py       # EasyOCR + Tesseract
├── templates/
│   └── index.html         # Main UI
├── static/
│   ├── css/style.css
│   ├── js/app.js
│   ├── uploads/           # Temp uploads
│   └── outputs/           # Generated files
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## 🔒 الأمان / Security Notes

- الملفات تُحذف تلقائياً بعد ساعة / Files auto-deleted after 1 hour
- الحد الأقصى لحجم الملف: 500MB / Max file size: 500MB
- للإنتاج: أضف HTTPS + Authentication حسب احتياجك

---

## 🛠️ التطوير / Development

```bash
# تشغيل في وضع التطوير مع إعادة التحميل التلقائي
FLASK_DEBUG=1 python app.py
```

---

## 📦 إضافة أدوات جديدة / Adding New Tools

1. أضف دالة في الـ module المناسب في `/modules/`
2. أضف route جديد في `app.py`
3. أضف بطاقة HTML في `templates/index.html`
4. أضف دالة JavaScript في `static/js/app.js`

---

Made with ❤️ | MIT License
