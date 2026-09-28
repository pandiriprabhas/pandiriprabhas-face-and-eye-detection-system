from rest_framework import serializers
from .models import Person, PersonHistory

class PersonHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonHistory
        fields = ["id", "action", "payload", "created_at"]

class PersonSerializer(serializers.ModelSerializer):
    history = PersonHistorySerializer(many=True, read_only=True)
    class Meta:
        model = Person
        fields = ["id","name","address","unique_number","unique_code","face_image","qr_code_image","face_signature","created_at","updated_at","history"]

class PersonCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ["name", "address", "unique_number", "face_image"]
