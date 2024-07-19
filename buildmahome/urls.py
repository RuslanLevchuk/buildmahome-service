from django.urls import path

from .views import (
    IndexView, UserCreateView, UserProfileView
)

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("accounts/sign_up/", UserCreateView.as_view(), name="sign_up"),
    path("accounts/<int:pk>/profile/", UserProfileView.as_view(), name="profile"),
]

app_name = "buildmahome"
