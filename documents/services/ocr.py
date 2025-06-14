import easyocr
from PIL import Image
import os
import tempfile

reader = easyocr.Reader(['en', 'es'], gpu=False)

def run_ocr(file_field):
    print("Ejecutando OCR...") 
    # Crear archivo temporal si es PDF o imagen
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        for chunk in file_field.chunks():
            temp.write(chunk)
        temp_path = temp.name

    # OCR usando EasyOCR
    try:
        result = reader.readtext(temp_path, detail=1, paragraph=True)
        parsed = []
        for bbox, text, conf in result:
            parsed.append({
                "text": text,
                "confidence": conf,
                "bbox": bbox
            })
        return parsed
    except Exception as e:
        return {"error": str(e)}
    finally:
        os.remove(temp_path)
