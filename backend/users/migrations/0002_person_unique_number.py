from django.db import migrations, models

import users.models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="person",
            name="unique_number",
            field=models.CharField(default=users.models.generate_unique_number, max_length=32, unique=True),
        ),
    ]
