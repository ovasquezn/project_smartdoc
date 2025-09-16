from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Document(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Salida estructurada (OCR/ML) en JSON
    extracted_data = models.JSONField(blank=True, null=True)
    
    # Puntuación de confianza (opcional por ahora)
    confidence_score = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f'Document #{self.pk} - {self.file.name}'
