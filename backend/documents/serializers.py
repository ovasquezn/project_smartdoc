from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'owner', 'file', 'uploaded_at', 'extracted_data', 'confidence_score']
        read_only_fields = ['id', 'owner', 'uploaded_at', 'extracted_data', 'confidence_score']
