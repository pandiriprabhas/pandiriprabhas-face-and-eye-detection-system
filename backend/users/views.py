from __future__ import annotations

import socket
from datetime import timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
import os

from django.conf import settings
from django.contrib import messages
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework import status

from .forms import PersonRegistrationForm
from .models import Person, PersonHistory
from .serializers import PersonCreateSerializer, PersonSerializer
from .utils.face_utils import detect_face_and_eyes, extract_face_encoding
from .utils.qr_utils import build_qr_png


SCAN_LOG_COOLDOWN_SECONDS = 6 * 60 * 60


def _detail_url(request, unique_code: str) -> str:
    relative_url = reverse("users:person_detail", args=[unique_code])
    public_base_url = getattr(settings, "PUBLIC_BASE_URL", "").strip()
    if public_base_url:
        return f"{public_base_url.rstrip('/')}{relative_url}"

    port = "8000"
    if request is not None:
        try:
            port = str(request.get_port())
        except Exception:
            port = "8000"
    else:
        port = str(os.environ.get("APP_PORT", "8000"))

    if request is not None:
        host = request.get_host().split(":")[0].lower()
        if host not in {"127.0.0.1", "localhost"}:
            return request.build_absolute_uri(relative_url)

    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(("8.8.8.8", 80))
        local_ip = probe.getsockname()[0]
    except OSError:
        local_ip = "127.0.0.1"
    finally:
        try:
            probe.close()
        except Exception:
            pass

    return f"http://{local_ip}:{port}{relative_url}"


def _store_qr_code(person: Person, request) -> None:
    payload = _detail_url(request, person.unique_code)
    qr_bytes = build_qr_png(payload)
    person.qr_code_image.save(f"{person.unique_code}.png", ContentFile(qr_bytes), save=False)


def _log_qr_scan_once(person: Person, source: str, dedupe_seconds: int = 30) -> None:
    """Avoid duplicate scan rows when users refresh the same page repeatedly."""
    cutoff = timezone.now() - timedelta(seconds=dedupe_seconds)
    recent_scan_exists = PersonHistory.objects.filter(
        person=person,
        action=PersonHistory.ACTION_QR_SCANNED,
        created_at__gte=cutoff,
    ).exists()
    if recent_scan_exists:
        return

    PersonHistory.objects.create(
        person=person,
        action=PersonHistory.ACTION_QR_SCANNED,
        payload={"source": source},
    )


def _should_log_scan_in_session(request, person: Person, cooldown_seconds: int = SCAN_LOG_COOLDOWN_SECONDS) -> bool:
    """Prevent repeated QR scan logs from browser refresh in the same session."""
    if request is None or not hasattr(request, "session"):
        return True

    key = f"qr_scan_seen:{person.unique_code}"
    now_ts = int(timezone.now().timestamp())
    last_seen_ts = request.session.get(key)

    if isinstance(last_seen_ts, int) and now_ts - last_seen_ts < cooldown_seconds:
        return False

    request.session[key] = now_ts
    return True


def _create_person(validated_data, request):
    with transaction.atomic():
        person = Person.objects.create(**validated_data)
        detection = detect_face_and_eyes(person.face_image.path)
        if detection is None:
            person.delete()
            raise ValueError("No face detected in the uploaded image.")
        if detection["eye_count"] < 2:
            person.delete()
            raise ValueError("Face detected, but both eyes were not detected clearly. Please use a clear front-facing photo with both eyes visible.")

        face_encoding = extract_face_encoding(person.face_image.path)
        person.face_signature = {
            "face_box": detection["face_box"],
            "eyes": detection["eyes"],
            "eye_count": detection["eye_count"],
            "encoding": face_encoding,
        }
        _store_qr_code(person, request)
        person.save(update_fields=["face_signature", "qr_code_image", "updated_at"])
        PersonHistory.objects.create(
            person=person,
            action=PersonHistory.ACTION_REGISTERED,
            payload={"name": person.name, "address": person.address, "unique_code": person.unique_code},
        )
        return person


def dashboard(request):
    form = PersonRegistrationForm()
    people = Person.objects.all()[:12]
    history = PersonHistory.objects.select_related("person")[:12]
    qr_base_url = getattr(settings, "PUBLIC_BASE_URL", "") or settings.SITE_BASE_URL
    public_url_warning = "127.0.0.1" in qr_base_url or "localhost" in qr_base_url
    return render(
        request,
        "users/dashboard.html",
        {
            "form": form,
            "people": people,
            "history": history,
            "public_url_warning": public_url_warning,
            "qr_base_url": qr_base_url,
        },
    )


def register_person(request):
    if request.method != "POST":
        return redirect("users:dashboard")

    form = PersonRegistrationForm(request.POST, request.FILES)
    if not form.is_valid():
        people = Person.objects.all()[:12]
        history = PersonHistory.objects.select_related("person")[:12]
        return render(
            request,
            "users/dashboard.html",
            {
                "form": form,
                "people": people,
                "history": history,
            },
            status=400,
        )

    try:
        person = _create_person(form.cleaned_data, request)
    except ValueError as exc:
        form.add_error("face_image", str(exc))
        people = Person.objects.all()[:12]
        history = PersonHistory.objects.select_related("person")[:12]
        return render(
            request,
            "users/dashboard.html",
            {
                "form": form,
                "people": people,
                "history": history,
            },
            status=400,
        )

    messages.success(request, f"{person.name} registered successfully.")
    return redirect("users:person_detail_full", unique_code=person.unique_code)


def person_detail(request, unique_code: str):
    person = get_object_or_404(Person, unique_code=unique_code)
    scan_url = _detail_url(request, person.unique_code)
    full_profile_url = reverse("users:person_detail_full", args=[unique_code])
    if _should_log_scan_in_session(request, person, cooldown_seconds=SCAN_LOG_COOLDOWN_SECONDS):
        _log_qr_scan_once(person, source="qr_direct_detail", dedupe_seconds=SCAN_LOG_COOLDOWN_SECONDS)
    return render(
        request,
        "users/person_scan.html",
        {
            "person": person,
            "scan_url": scan_url,
            "full_profile_url": full_profile_url,
            "hide_topbar": True,
        },
    )


def person_detail_full(request, unique_code: str):
    person = get_object_or_404(Person, unique_code=unique_code)
    history_events = person.history.all()[:20]
    scan_url = _detail_url(request, person.unique_code)
    return render(
        request,
        "users/person_detail.html",
        {
            "person": person,
            "history_events": history_events,
            "scan_url": scan_url,
            "hide_topbar": True,
        },
    )


def person_activate(request, unique_code: str):
    person = get_object_or_404(Person.objects.prefetch_related("history"), unique_code=unique_code)
    scan_url = _detail_url(request, unique_code)
    return render(
        request,
        "users/person_activate.html",
        {
            "person": person,
            "scan_url": scan_url,
            "hide_topbar": True,
        },
    )


def history_list(request):
    events = PersonHistory.objects.select_related("person")[:100]
    return render(request, "users/history_list.html", {"events": events})


def delete_person(request, unique_code: str):
    if request.method != "POST":
        return redirect("users:history_list")

    person = get_object_or_404(Person, unique_code=unique_code)
    person_name = person.name

    if person.face_image:
        person.face_image.delete(save=False)
    if person.qr_code_image:
        person.qr_code_image.delete(save=False)

    person.delete()
    messages.success(request, f"Deleted person record: {person_name}")
    return redirect("users:history_list")


@api_view(["GET", "POST"])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def people_api(request):
    if request.method == "GET":
        queryset = Person.objects.prefetch_related("history").all()
        return Response(PersonSerializer(queryset, many=True).data)

    serializer = PersonCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        person = _create_person(serializer.validated_data, request)
    except ValueError as exc:
        return Response({"face_image": [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)

    return Response(PersonSerializer(person).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def person_api_detail(request, unique_code: str):
    person = get_object_or_404(Person.objects.prefetch_related("history"), unique_code=unique_code)
    return Response(PersonSerializer(person).data)


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def validate_face_api(request):
    uploaded = request.FILES.get("face_image")
    if not uploaded:
        return Response({"valid": False, "message": "No image file provided."}, status=status.HTTP_400_BAD_REQUEST)

    suffix = Path(uploaded.name).suffix or ".jpg"
    with NamedTemporaryFile(suffix=suffix) as tmp:
        for chunk in uploaded.chunks():
            tmp.write(chunk)
        tmp.flush()
        detection = detect_face_and_eyes(tmp.name)

    if detection is None:
        return Response({"valid": False, "message": "No face detected. Use a clear front-facing photo."})
    if detection["eye_count"] < 2:
        return Response({"valid": False, "message": "Face detected, but both eyes were not clear. Keep both eyes visible and try again."})

    return Response(
        {
            "valid": True,
            "message": f"Face and both eyes detected successfully. Eye count: {detection['eye_count']}",
            "eye_count": detection["eye_count"],
            "face_box": detection["face_box"],
        }
    )
