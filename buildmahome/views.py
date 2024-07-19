from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic

from buildmahome.forms import SignUpForm


class IndexView(generic.TemplateView):
    template_name = "buildmahome/index.html"


class UserCreateView(generic.CreateView):
    template_name = "buildmahome/sign-up.html"
    form_class = SignUpForm
    success_url = reverse_lazy("buildmahome:index")

