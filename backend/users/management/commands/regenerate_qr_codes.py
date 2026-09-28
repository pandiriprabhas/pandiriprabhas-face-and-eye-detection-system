from __future__ import annotations

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse

from users.models import Person
from users.utils.qr_utils import build_qr_png


class Command(BaseCommand):
    help = "Regenerate all person QR images using the active base URL."

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-url",
            dest="base_url",
            default="",
            help="Base URL for QR links, e.g. http://192.168.68.145:8000",
        )

    def handle(self, *args, **options):
        base_url = (options.get("base_url") or "").strip()
        if not base_url:
            base_url = (getattr(settings, "PUBLIC_BASE_URL", "") or "").strip()
        if not base_url:
            base_url = (getattr(settings, "SITE_BASE_URL", "") or "").strip()

        if not base_url:
            raise CommandError(
                "No base URL found. Pass --base-url or set PUBLIC_BASE_URL."
            )

        base_url = base_url.rstrip("/")

        updated = 0
        for person in Person.objects.all().only("id", "unique_code", "qr_code_image", "updated_at"):
            detail_path = reverse("users:person_detail", args=[person.unique_code])
            payload = f"{base_url}{detail_path}"
            qr_bytes = build_qr_png(payload)
            person.qr_code_image.save(
                f"{person.unique_code}.png",
                ContentFile(qr_bytes),
                save=False,
            )
            person.save(update_fields=["qr_code_image", "updated_at"])
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Regenerated {updated} QR code(s) using base URL: {base_url}"
            )
        )
