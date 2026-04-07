"""OCR Tools: extract text from images using EasyOCR or Tesseract"""
import os


def extract_text(input_path, lang='auto', engine='easyocr'):
    """
    Extract text from image.
    lang: 'auto', 'eng', 'ara', 'both'
    engine: 'easyocr', 'tesseract'
    """
    if engine == 'tesseract':
        return _tesseract_ocr(input_path, lang)
    else:
        return _easyocr(input_path, lang)


def _easyocr(input_path, lang='auto'):
    import easyocr
    lang_map = {
        'auto': ['en', 'ar'],
        'eng':  ['en'],
        'ara':  ['ar'],
        'both': ['en', 'ar'],
    }
    langs = lang_map.get(lang, ['en', 'ar'])
    reader = easyocr.Reader(langs, gpu=False)
    results = reader.readtext(input_path, detail=1)

    blocks = []
    full_text = []
    for bbox, text, confidence in results:
        blocks.append({
            'text': text,
            'confidence': round(confidence * 100, 1),
            'bbox': bbox
        })
        full_text.append(text)

    return {
        'engine': 'EasyOCR',
        'language': lang,
        'full_text': '\n'.join(full_text),
        'blocks': blocks,
        'block_count': len(blocks)
    }


def _tesseract_ocr(input_path, lang='auto'):
    import pytesseract
    from PIL import Image
    lang_map = {
        'auto': 'eng+ara',
        'eng':  'eng',
        'ara':  'ara',
        'both': 'eng+ara',
    }
    tess_lang = lang_map.get(lang, 'eng+ara')
    img = Image.open(input_path)
    text = pytesseract.image_to_string(img, lang=tess_lang)
    data = pytesseract.image_to_data(img, lang=tess_lang, output_type=pytesseract.Output.DICT)

    blocks = []
    for i, word in enumerate(data['text']):
        if word.strip() and int(data['conf'][i]) > 30:
            blocks.append({
                'text': word,
                'confidence': int(data['conf'][i]),
                'bbox': [data['left'][i], data['top'][i],
                         data['left'][i] + data['width'][i],
                         data['top'][i] + data['height'][i]]
            })

    return {
        'engine': 'Tesseract',
        'language': lang,
        'full_text': text.strip(),
        'blocks': blocks,
        'block_count': len(blocks)
    }
