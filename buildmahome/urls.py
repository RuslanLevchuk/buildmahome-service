from django.urls import path

from .views import (
    IndexView,
    UserCreateView,
    UserProfileView,
    UserUpdateView,
)

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("accounts/sign_up/", UserCreateView.as_view(), name="sign_up"),
    path("accounts/<int:pk>/profile/", UserProfileView.as_view(), name="profile"),
    path("accounts/<int:pk>/update/", UserUpdateView.as_view(), name="update"),
]

app_name = "buildmahome"
