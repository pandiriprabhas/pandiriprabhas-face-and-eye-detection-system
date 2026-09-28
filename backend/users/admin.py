from django.contrib import admin

from .models import Person, PersonHistory

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("name", "unique_number", "unique_code", "address", "created_at")
    search_fields = ("name", "unique_number", "unique_code", "address")
    readonly_fields = ("unique_code", "created_at", "updated_at")

@admin.register(PersonHistory)
class PersonHistoryAdmin(admin.ModelAdmin):
    list_display = ("person", "action", "created_at")
    search_fields = ("person__name", "person__unique_code", "action")
    list_filter = ("action", "created_at")
