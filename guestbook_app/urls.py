from django.urls import path
from . import views

app_name = "guestbook_app"

urlpatterns = [
    path("", views.list_entries, name="list"),
    path("add/", views.add_entry, name="add"),
    path("edit/<int:entry_id>/", views.edit_entry, name="edit"),
    path("delete/<int:entry_id>/", views.delete_entry, name="delete"),
]
