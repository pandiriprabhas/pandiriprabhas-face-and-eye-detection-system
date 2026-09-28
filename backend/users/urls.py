from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("people/register/", views.register_person, name="register_person"),
    path("people/<str:unique_code>/delete/", views.delete_person, name="delete_person"),
    path("activate/<str:unique_code>/", views.person_activate, name="person_activate"),
    path("people/<str:unique_code>/", views.person_detail, name="person_detail"),
    path("people/<str:unique_code>/full/", views.person_detail_full, name="person_detail_full"),
    path("history/", views.history_list, name="history_list"),
    path("api/validate-face/", views.validate_face_api, name="validate_face_api"),
    path("api/people/", views.people_api, name="people_api"),
    path("api/people/<str:unique_code>/", views.person_api_detail, name="person_api_detail"),
]
