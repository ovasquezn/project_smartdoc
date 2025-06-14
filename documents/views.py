from django.shortcuts import render

from rest_framework import viewsets, permissions
from .models import Document
from .serializers import DocumentSerializer
from .services.ocr import run_ocr

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        document = serializer.save(owner=self.request.user)
        extracted = run_ocr(document.file)
        document.extracted_data = extracted
        # Calcular confianza si es posible
        try:
            confidences = [item['confidence'] for item in extracted if 'confidence' in item]
            document.confidence_score = sum(confidences) / len(confidences) if confidences else None
        except:
            pass
        document.save()


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        document = serializer.save(owner=self.request.user)
        extracted = run_ocr(document.file)
        document.extracted_data = extracted
        
        try:
            confidences = [item['confidence'] for item in extracted if 'confidence' in item]
            document.confidence_score = sum(confidences) / len(confidences) if confidences else None
        except:
            pass
        document.save()
