from django.urls import path, include

urlpatterns = [
    path("", include("guestbook_app.urls")),
]
