from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import request
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views import generic

from buildmahome.forms import SignUpForm, UserUpdateForm
from buildmahome.models import User, Worker


class IndexView(generic.TemplateView):
    template_name = "buildmahome/index.html"


class UserCreateView(generic.CreateView):
    template_name = "registration/sign-up.html"
    form_class = SignUpForm
    success_url = reverse_lazy("buildmahome:index")
    
    
class UserProfileView(LoginRequiredMixin, generic.DetailView):
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


class UserUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "buildmahome/user-profile-update.html"

    def get_success_url(self):
        return reverse(
            "buildmahome:profile",
            kwargs={"pk": self.object.pk}
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        if form.cleaned_data.get('password2'):
            update_session_auth_hash(self.request, self.request.user)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['worker'] = Worker.objects.get(user=self.object)
        except Worker.DoesNotExist:
            context['worker'] = None
        return context
