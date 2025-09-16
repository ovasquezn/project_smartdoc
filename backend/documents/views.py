import re
from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Document
from .serializers import DocumentSerializer
from .services.ocr import run_ocr
from django.http import JsonResponse
from rest_framework.decorators import action
from django.http import JsonResponse
from rest_framework.decorators import action

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        print("📥 Documento recibido. Ejecutando OCR...")
        document = serializer.save(owner=self.request.user)
        extracted = run_ocr(document.file)
        print("🧠 Resultado OCR:", extracted)
        document.extracted_data = extracted
        try:
            confidences = []
            for item in extracted:
                conf = item.get("confidence")
                if isinstance(conf, (int, float)):  # Solo si es un número real
                    confidences.append(conf)
            
            if confidences:
                document.confidence_score = sum(confidences) / len(confidences)
            else:
                document.confidence_score = None
        except Exception as e:
            print("❌ Error al calcular confianza:", e)
        document.save()

    def parse_invoice(self, extracted):
        all_text = " ".join([item['text'] for item in extracted if item.get('text')])

        def get_match(pattern):
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                if match.groups():
                    return match.group(1).strip()
                else:
                    return match.group(0).strip()
            return None

        return {
            "n_factura": get_match(r'(?:Factura|FACTURA)[\s#:]*([A-Za-z0-9\-\/]+)'),
            "fecha_emision": get_match(r'Fecha[:\s]*([0-9]{2}/[0-9]{2}/[0-9]{4})'),
            "vencimiento": get_match(r'Vencimiento[:\s]*([0-9]{2}/[0-9]{2}/[0-9]{4})'),
            "total": get_match(r'Total\s+([0-9]+[\.,]?[0-9]*)\s*€'),
            "base_imponible": get_match(r'BASE\s+IMPONIBLE\s*([0-9]+[\.,]?[0-9]*)'),
            "iva": get_match(r'IVA\s*([0-9]{1,2}%)'),
            "impuesto_total": get_match(r'TOTAL\s+IMPUESTO\s*([0-9]+[\.,]?[0-9]*)'),
            "iban": get_match(r'(ES\d{2}\d{20})'),
            "correo": get_match(r'([\w\.-]+@[\w\.-]+)'),
            "telefono": get_match(r'\b[67]\d{8}\b'),
        }

    @action(detail=True, methods=["get"])
    def run_ocr_again(self, request, pk=None):
        document = self.get_object()
        print("🔁 Reprocesando OCR para documento:", document.id)

        extracted = run_ocr(document.file)
        print("🧠 Resultado OCR:", extracted)

        parsed_data = self.parse_invoice(extracted)

        items = extract_items_from_ocr(extracted)
        parsed_data["items"] = items
        print("📄 Datos estructurados:", parsed_data)

        document.extracted_data = parsed_data

        try:
            confidences = [item['confidence'] for item in extracted if item.get('confidence') is not None]
            document.confidence_score = sum(confidences) / len(confidences) if confidences else None
        except Exception as e:
            print("❌ Error al calcular confianza:", e)

        document.save()
        return JsonResponse({
            "ok": True,
            "fields": parsed_data
        })

def extract_items_from_ocr(extracted):
    import numpy as np

    rows = []
    # Agrupar textos por línea usando coordenada Y aproximada
    line_map = {}

    for item in extracted:
        text = item.get("text", "").strip()
        if not text:
            continue

        # Usamos el Y promedio para estimar la línea
        bbox = item.get("bbox", [])
        if len(bbox) < 4:
            continue

        y_coords = [point[1] for point in bbox]
        y_avg = int(np.mean(y_coords) // 5 * 5)  # agrupamos por bloques de 5 pixeles
        line_map.setdefault(y_avg, []).append(item)

    # Ordenar líneas de arriba a abajo
    for y in sorted(line_map.keys()):
        line = sorted(line_map[y], key=lambda x: x["bbox"][0][0])  # orden izquierda a derecha
        line_texts = [x["text"] for x in line]
        rows.append(line_texts)

    # Detectar si hay encabezado
    header_keywords = {"concepto", "precio", "unidades", "subtotal", "iva", "total"}
    header_row_index = None
    for i, row in enumerate(rows):
        if any(cell.lower() in header_keywords for cell in row):
            header_row_index = i
            break

    # Extraer ítems desde la fila siguiente al encabezado
    items = []
    if header_row_index is not None:
        for row in rows[header_row_index + 1:]:
            if len(row) >= 5:
                items.append({
                    "descripcion": row[0],
                    "precio": row[1],
                    "unidades": row[2] if len(row) >= 6 else "",
                    "subtotal": row[-3],
                    "iva": row[-2],
                    "total": row[-1]
                })

    return items




    # def run_ocr_again(self, request, pk=None):
    #     document = self.get_object()
    #     print("🔁 Reprocesando OCR para documento:", document.id)

    #     extracted = run_ocr(document.file)
    #     print("🧠 Resultado nuevo:", extracted)

    #     document.extracted_data = extracted

    #     try:
    #         # Solo considera valores numéricos válidos de confianza
    #         confidences = [
    #             item['confidence'] for item in extracted
    #             if isinstance(item, dict) and 'confidence' in item and item['confidence'] is not None
    #         ]
    #         document.confidence_score = (
    #             sum(confidences) / len(confidences)
    #             if confidences else None
    #         )
    #     except Exception as e:
    #         print("❌ Error al calcular confianza:", e)

    #     document.save()
    #     return JsonResponse({"ok": True, "fields": extracted})