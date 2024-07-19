from django.contrib.auth.forms import UserCreationForm
from django.http import request
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic

from buildmahome.forms import SignUpForm
from buildmahome.models import User, Worker


class IndexView(generic.TemplateView):
    template_name = "buildmahome/index.html"


class UserCreateView(generic.CreateView):
    template_name = "registration/sign-up.html"
    form_class = SignUpForm
    success_url = reverse_lazy("buildmahome:index")
    
    
class UserProfileView(generic.DetailView):
    model = User
    queryset = User.objects.all()
    template_name = "buildmahome/user-profile.html"
    context_object_name = "user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        try:
            worker = user.worker
        except Worker.DoesNotExist:
            worker = None

        context['worker'] = worker

        if worker:
            context['skills'] = worker.skills.all()
        return context
