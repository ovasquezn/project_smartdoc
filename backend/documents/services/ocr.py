def run_ocr(file_field):
    import easyocr
    import os
    import tempfile

    from PIL import Image

    import logging
    logger = logging.getLogger('ocr')

    reader = easyocr.Reader(['en', 'es'], gpu=False)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp:
        for chunk in file_field.chunks():
            temp.write(chunk)
        temp_path = temp.name

    print(f"🧪 Archivo temporal guardado en: {temp_path}")
    logger.info("Iniciando OCR para archivo temporal: %s", temp_path)

    # Validar si el archivo es legible por PIL
    try:
        img = Image.open(temp_path)
        img.verify()  # No lanza excepción = archivo válido
        print("✅ Imagen verificada con PIL.")
    except Exception as e:
        print("❌ Error verificando la imagen:", e)
        os.remove(temp_path)
        return {"error": "Imagen no válida"}

    try:
        result = reader.readtext(temp_path, detail=1, paragraph=True)
        print(f"🔍 Resultado OCR: {result}")
        parsed = []
        for item in result:
            try:
                bbox, text, conf = item
                parsed.append({
                    "text": text,
                    "confidence": conf,
                    "bbox": bbox
                })
            except ValueError:
                # Fallback si no hay confidence (por ejemplo con paragraph=True)
                bbox, text = item
                parsed.append({
                    "text": text,
                    "confidence": None,
                    "bbox": bbox
                })
        return parsed
    except Exception as e:
        print("❌ Error en EasyOCR:", e)
        return {"error": str(e)}
    finally:
        os.remove(temp_path)
