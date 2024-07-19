from django.urls import path

from .views import (
    IndexView, UserCreateView
)

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("accounts/sign_up/", UserCreateView.as_view(), name="sign_up"),
]

app_name = "buildmahome"
