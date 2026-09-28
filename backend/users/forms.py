from django import forms

from .models import Person

class PersonRegistrationForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ["name", "address", "unique_number", "face_image"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Full name"}),
            "address": forms.Textarea(attrs={"rows": 4, "placeholder": "Address"}),
            "unique_number": forms.TextInput(attrs={"placeholder": "Unique number"}),
            "face_image": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }
