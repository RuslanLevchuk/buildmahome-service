from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.http import request, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views import generic

from buildmahome.forms import SignUpForm, UserUpdateForm, WorkTeamCreateFrom
from buildmahome.models import User, Worker, WorkTeam, Skill


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


class WorkerListView(generic.ListView):
    model = Worker
    template_name = "buildmahome/worker-list.html"
    context_object_name = "workers"

    def get_queryset(self):
        worker = Worker.objects.select_related('user').all()
        worker = worker.select_related("team")
        worker = worker.prefetch_related("skills")
        worker = worker.order_by('user__username')
        return worker


class WorkTeamListView(generic.ListView):
    model = WorkTeam
    template_name = "buildmahome/workteam-list.html"
    context_object_name = "work_teams"

    def get_queryset(self):
        work_team = WorkTeam.objects.all()
        work_team = work_team.prefetch_related("workers")
        return work_team


class WorkTeamDetailView(generic.DetailView):
    model = WorkTeam
    queryset = WorkTeam.objects.prefetch_related(
        Prefetch('workers', queryset=Worker.objects.prefetch_related('skills')
                 ))
    template_name = "buildmahome/work-team-detail.html"
    context_object_name = "work_team"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        work_team = self.get_object()
        workers = work_team.workers.all().prefetch_related('user')

        workers_count = workers.count()
        distinct_skills = Skill.objects.filter(workers__in=workers).distinct()
        context["workers"] = workers
        context["skills"] = distinct_skills
        context["workers_count"] = workers_count
        return context


class MakeWorkerView(LoginRequiredMixin, generic.TemplateView):
    template_name = "buildmahome/action-message.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["message"] = "You are worker now!"
        return context

    def get(self, *args, **kwargs):
        user = self.request.user
        user.is_worker = True
        user.save()
        Worker.objects.create(user=user)
        return super().get(request, *args, **kwargs)


class WorkTeamCreateView(LoginRequiredMixin, generic.CreateView):
    form_class = WorkTeamCreateFrom
    template_name = "buildmahome/work-team-create.html"

    def dispatch(self, *args, **kwargs):
        try:
            worker = Worker.objects.get(user=self.request.user)
            if worker.team:
                message = "You are already a member of a team. <br>Leave existing team to create new one.</br>"
                return HttpResponseRedirect(
                    f"{reverse('buildmahome:successful_action')}?message={message}")
        except Worker.DoesNotExist:
            pass
        return super().dispatch(*args, **kwargs)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        team_name = self.object.name
        message = f"Team {team_name} created successfully!"
        return HttpResponseRedirect(
            f"{reverse('buildmahome:successful_action')}?message={message}")

    def get_success_url(self):
        return reverse('buildmahome:successful_action')


class SuccessfulActionView(generic.TemplateView):
    template_name = "buildmahome/action-message.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["message"] = self.request.GET.get('message', '')
        return context
