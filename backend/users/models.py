from __future__ import annotations
import uuid
from django.db import models

def generate_unique_code() -> str:
    return f"FQR-{uuid.uuid4().hex[:10].upper()}"

def generate_unique_number() -> str:
    return f"UID-{uuid.uuid4().hex[:8].upper()}"

def face_upload_to(instance: "Person", filename: str) -> str:
    return f"faces/{instance.unique_code}/{filename}"

def qr_upload_to(instance: "Person", filename: str) -> str:
    return f"qr_codes/{instance.unique_code}/{filename}"

class Person(models.Model):
    name = models.CharField(max_length=120)
    address = models.TextField()
    unique_number = models.CharField(max_length=32, unique=True, default=generate_unique_number)
    unique_code = models.CharField(max_length=32, unique=True, default=generate_unique_code, editable=False)
    face_image = models.ImageField(upload_to=face_upload_to)
    qr_code_image = models.ImageField(upload_to=qr_upload_to, blank=True, null=True)
    face_signature = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.unique_number})"

class PersonHistory(models.Model):
    ACTION_REGISTERED = "registered"
    ACTION_UPDATED = "updated"
    ACTION_QR_SCANNED = "qr_scanned"
    ACTION_CHOICES = [
        (ACTION_REGISTERED, "Registered"),
        (ACTION_UPDATED, "Updated"),
        (ACTION_QR_SCANNED, "QR Scanned"),
    ]
    person = models.ForeignKey(Person, related_name="history", on_delete=models.CASCADE)
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.person.unique_code} - {self.action}"
