from django.db import migrations, models
import django.db.models.deletion

import users.models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Person",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("address", models.TextField()),
                (
                    "unique_code",
                    models.CharField(
                        default=users.models.generate_unique_code,
                        editable=False,
                        max_length=32,
                        unique=True,
                    ),
                ),
                ("face_image", models.ImageField(upload_to=users.models.face_upload_to)),
                ("qr_code_image", models.ImageField(blank=True, null=True, upload_to=users.models.qr_upload_to)),
                ("face_signature", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PersonHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("registered", "Registered"),
                            ("updated", "Updated"),
                            ("qr_scanned", "QR Scanned"),
                        ],
                        max_length=32,
                    ),
                ),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "person",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="history", to="users.person"),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
