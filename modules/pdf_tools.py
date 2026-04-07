"""PDF Tools: merge, images→pdf, compress"""
import os

def merge_pdfs(input_paths, output_path):
    try:
        import fitz  # PyMuPDF
        doc = fitz.open()
        for path in input_paths:
            with fitz.open(path) as src:
                doc.insert_pdf(src)
        doc.save(output_path)
        doc.close()
    except ImportError:
        from pypdf import PdfWriter
        writer = PdfWriter()
        from pypdf import PdfReader
        for path in input_paths:
            reader = PdfReader(path)
            for page in reader.pages:
                writer.add_page(page)
        with open(output_path, 'wb') as f:
            writer.write(f)
    return {'file': os.path.basename(output_path), 'path': output_path}


def images_to_pdf(input_paths, output_path):
    from modules.image_tools import open_image
    images = []
    first = None
    for path in input_paths:
        img = open_image(path).convert('RGB')
        if first is None:
            first = img
        else:
            images.append(img)
    if first:
        first.save(output_path, save_all=True, append_images=images)
    return {'file': os.path.basename(output_path), 'path': output_path}


def compress_pdf(input_path, output_path):
    try:
        import fitz
        doc = fitz.open(input_path)
        doc.save(output_path, garbage=4, deflate=True, clean=True)
        doc.close()
    except ImportError:
        import shutil
        shutil.copy(input_path, output_path)
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
