"""Image Tools: convert, compress, resize — with HEIC/HEIF support"""
import os
import subprocess
import shutil
from PIL import Image


def open_image(input_path):
    """
    Open any image file. Handles HEIC/HEIF via multiple fallback methods:
    1. pillow-heif plugin (best, pure Python)
    2. pyheif library
    3. ImageMagick convert (system tool)
    4. FFmpeg (last resort)
    Raises RuntimeError if all methods fail.
    """
    ext = input_path.rsplit('.', 1)[-1].lower() if '.' in input_path else ''

    if ext in ('heic', 'heif'):
        # ── Method 1: pillow-heif (registers itself as a Pillow plugin) ──
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
            return Image.open(input_path).copy()
        except ImportError:
            pass
        except Exception:
            pass

        # ── Method 2: pyheif ──────────────────────────────────────────
        try:
            import pyheif
            heif_file = pyheif.read(input_path)
            return Image.frombytes(
                heif_file.mode,
                heif_file.size,
                heif_file.data,
                "raw",
                heif_file.mode,
                heif_file.stride,
            )
        except ImportError:
            pass
        except Exception:
            pass

        # ── Method 3: ImageMagick convert ─────────────────────────────
        if shutil.which('convert'):
            tmp = input_path + '_magick.png'
            try:
                result = subprocess.run(
                    ['convert', input_path, tmp],
                    capture_output=True, timeout=60
                )
                if result.returncode == 0 and os.path.exists(tmp):
                    img = Image.open(tmp).copy()
                    os.remove(tmp)
                    return img
            except Exception:
                if os.path.exists(tmp):
                    os.remove(tmp)

        # ── Method 4: FFmpeg ──────────────────────────────────────────
        if shutil.which('ffmpeg'):
            tmp = input_path + '_ffmpeg.png'
            try:
                result = subprocess.run(
                    ['ffmpeg', '-y', '-i', input_path, tmp],
                    capture_output=True, timeout=60
                )
                if result.returncode == 0 and os.path.exists(tmp):
                    img = Image.open(tmp).copy()
                    os.remove(tmp)
                    return img
            except Exception:
                if os.path.exists(tmp):
                    os.remove(tmp)

        raise RuntimeError(
            "لا يمكن فتح ملف HEIC. يرجى تثبيت: pip install pillow-heif\n"
            "Cannot open HEIC file. Please install: pip install pillow-heif"
        )

    # ── Standard formats via Pillow ────────────────────────────────────
    try:
        return Image.open(input_path)
    except Exception:
        # Try registering pillow-heif anyway (handles edge cases)
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
            return Image.open(input_path)
        except Exception:
            pass
        raise


def _ensure_rgb_for_format(img, pil_fmt):
    """Convert mode if required by the target format."""
    if pil_fmt in ('JPEG',) and img.mode in ('RGBA', 'P', 'LA', 'CMYK'):
        return img.convert('RGB')
    if pil_fmt in ('BMP', 'ICO') and img.mode in ('RGBA', 'P'):
        return img.convert('RGBA')
    return img


def convert_image(input_path, output_path, fmt):
    fmt_map = {
        'jpg': 'JPEG', 'jpeg': 'JPEG', 'png': 'PNG',
        'webp': 'WEBP', 'gif': 'GIF', 'bmp': 'BMP',
        'tiff': 'TIFF', 'ico': 'ICO', 'avif': 'AVIF',
        'heic': 'HEIF', 'heif': 'HEIF',
    }
    pil_fmt = fmt_map.get(fmt.lower(), fmt.upper())
    img = open_image(input_path)
    img = _ensure_rgb_for_format(img, pil_fmt)
    if pil_fmt == 'ICO':
        img.save(output_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
    elif pil_fmt == 'HEIF':
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
            img.save(output_path, format='HEIF')
        except ImportError:
            raise RuntimeError("Install pillow-heif to save as HEIC: pip install pillow-heif")
    else:
        img.save(output_path, format=pil_fmt)
    return {'file': os.path.basename(output_path), 'path': output_path}


def compress_image(input_path, output_path, quality=75):
    img = open_image(input_path)
    ext = output_path.rsplit('.', 1)[-1].lower()
    if ext in ('jpg', 'jpeg'):
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        img.save(output_path, 'JPEG', quality=quality, optimize=True)
    elif ext == 'png':
        img.save(output_path, 'PNG', optimize=True, compress_level=min(9, int((100 - quality) / 11)))
    elif ext == 'webp':
        img.save(output_path, 'WEBP', quality=quality, method=6)
    else:
        img.save(output_path, optimize=True)
    original = os.path.getsize(input_path)
    compressed = os.path.getsize(output_path)
    ratio = round((1 - compressed / original) * 100, 1) if original > 0 else 0
    return {
        'file': os.path.basename(output_path),
        'path': output_path,
        'original_size': original,
        'compressed_size': compressed,
        'reduction': f"{ratio}%"
    }


def resize_image(input_path, output_path, width=None, height=None):
    img = open_image(input_path)
    orig_w, orig_h = img.size
    if width and height:
        new_size = (width, height)
    elif width:
        ratio = width / orig_w
        new_size = (width, int(orig_h * ratio))
    elif height:
        ratio = height / orig_h
        new_size = (int(orig_w * ratio), height)
    else:
        new_size = img.size
    img = img.resize(new_size, Image.LANCZOS)
    img.save(output_path)
    return {
        'file': os.path.basename(output_path),
        'path': output_path,
        'original_dimensions': f"{orig_w}x{orig_h}",
        'new_dimensions': f"{new_size[0]}x{new_size[1]}"
    }
