from datetime import date, timedelta

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Prefetch, Q
from django.http import request, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import generic

from bootstrap_datepicker_plus.widgets import DateTimePickerInput

from buildmahome.forms import SignUpForm, UserUpdateForm, WorkTeamCreateFrom, \
    WorkTeamUpdateFrom, SkillCreateForm, ListSearchForm, TaskCreateForm
from buildmahome.models import User, Worker, WorkTeam, Skill, Task


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
    paginate_by = 3

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_query = None
        self.worker = Worker.objects.select_related('user').all()

    def get_queryset(self):
        self.worker = self.worker.select_related("team")
        self.worker = self.worker.prefetch_related("skills")
        self.worker = self.worker.order_by('user__username')
        self.search_query = self.request.GET.get("search_data", None)
        if self.search_query:
            self.worker = self.worker.filter(
                user__username__icontains=self.search_query)

        return self.worker

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context["search_form"] = ListSearchForm(
            placeholder="Search by username...",
            initial={"search_data": self.search_query}
        )

        return context


class WorkTeamListView(generic.ListView):
    model = WorkTeam
    template_name = "buildmahome/workteam-list.html"
    context_object_name = "work_teams"
    paginate_by = 3

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_query = None
        self.work_team = WorkTeam.objects.all()

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        self.search_query = self.request.GET.get("search_data", None)
        context["search_form"] = ListSearchForm(
            placeholder="Search team by name...",
            initial={"search_data": self.search_query}
        )

        return context

    def get_queryset(self):
        self.work_team = self.work_team.prefetch_related("workers")
        self.search_query = self.request.GET.get("search_data", None)
        if self.search_query:
            self.work_team = self.work_team.filter(
                name__icontains=self.search_query)

        return self.work_team


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
        try:
            context["current_worker"] = Worker.objects.get(user=self.request.user)
        except Worker.DoesNotExist:
            context["current_worker"] = None
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


class WorkTeamUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = WorkTeam
    template_name = "buildmahome/work-team-update.html"
    form_class = WorkTeamUpdateFrom

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        team_name = self.object.name
        message = f"Team {team_name} updated successfully!"
        return HttpResponseRedirect(
            f"{reverse('buildmahome:successful_action')}?message={message}")

    def get_success_url(self):
        return reverse('buildmahome:successful_action')


class SkillsListView(generic.ListView):
    model = Skill
    template_name = "buildmahome/skills-list.html"
    paginate_by = 5

    def get_context_data(self, **kwargs):
        # get all work teams with workers that has current skill
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get("search_data", None)
        context["search_form"] = ListSearchForm(
            placeholder="Search skill...",
            initial={"search_data": search_query}
        )

        skill_teams = Skill.objects.prefetch_related(
            Prefetch(
                'workers',
                queryset=Worker.objects.select_related('team').filter(
                    team__isnull=False)
            )
        )

        if search_query:
            skill_teams = skill_teams.filter(name__icontains=search_query)

        skill_teams_dict = {}
        for skill in skill_teams:
            teams = set()
            for worker in skill.workers.all():
                if worker.team:
                    teams.add(worker.team)
            skill_teams_dict[skill] = teams

        current_page = self.request.GET.get("page", 1)
        paginator = Paginator(list(skill_teams_dict.items()), self.paginate_by)

        try:
            skills_page = paginator.page(current_page)
        except PageNotAnInteger:
            skills_page = paginator.page(1)
        except EmptyPage:
            skills_page = paginator.page(paginator.num_pages)

        context['skills_page'] = skills_page
        context['paginator'] = paginator

        return context


class SkillCreateView(generic.CreateView):
    form_class = SkillCreateForm
    template_name = "buildmahome/skill-create.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        skill_name = self.object.name
        message = f"Skill \"{skill_name}\" created successfully!"
        return HttpResponseRedirect(
            f"{reverse('buildmahome:successful_action')}?message={message}")

    def get_success_url(self):
        return reverse('buildmahome:successful_action')


class TaskCreateView(generic.CreateView):
    form_class = TaskCreateForm
    template_name = "buildmahome/task-create.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.work_team_pk = None
        self.work_team = None
        self.object = None

    def get_initial(self):
        initial = super().get_initial()
        self.work_team = self.kwargs.get('pk')
        if self.work_team:
            try:
                self.work_team = WorkTeam.objects.get(pk=self.work_team)
                initial['work_team'] = self.work_team
            except WorkTeam.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        form.instance.customer = self.request.user
        form.instance.work_team = self.work_team
        start_date = form.cleaned_data.get("start_date")
        if start_date:
            form.instance.end_date = start_date
        self.object = form.save()
        task_name = self.object.name
        message = f"Order \"{task_name}\" created successfully!"
        return HttpResponseRedirect(
            f"{reverse('buildmahome:successful_action')}?message={message}")

    def get_success_url(self):
        return reverse('buildmahome:successful_action')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.work_team_pk = self.kwargs.get('pk')
        if self.work_team:
            try:
                context['work_team'] = WorkTeam.objects.get(pk=self.work_team_pk)
            except WorkTeam.DoesNotExist:
                context['work_team'] = None
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        work_team_pk = self.kwargs.get('pk')
        if work_team_pk:
            try:
                work_team = WorkTeam.objects.get(pk=work_team_pk)
                kwargs['initial'] = {'work_team': work_team}
                tasks = Task.objects.filter(work_team=work_team)
                disable_dates = []
                for task in tasks:
                    date_range = [task.start_date + timedelta(days=i) for i in range((task.end_date - task.start_date).days + 1)]
                    disable_dates.extend(date_range)
                kwargs['disable_dates'] = [str(disable_date.isoformat()) for disable_date in disable_dates]

            except WorkTeam.DoesNotExist:
                kwargs['disable_dates'] = []
        return kwargs


class OrderListView(generic.ListView):
    model = Task
    template_name = "buildmahome/order-list.html"
    context_object_name = "orders"
    paginate_by = 5

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orders = None
        self.search_query = None

    def get_queryset(self):
        self.orders = Task.objects.filter(customer=self.request.user)
        now = timezone.now().date()
        filter_type = self.request.GET.get("type", None)
        self.search_query = self.request.GET.get("search_data", None)

        if self.search_query:
            self.name_search = self.orders.filter(name__icontains=self.search_query)
            self.description_search = self.orders.filter(description__icontains=self.search_query)
            self.orders = self.name_search.union(self.description_search)

        if filter_type:
            if filter_type == "actual":
                self.orders = self.orders.filter(Q(start_date__gte=now) and Q(approved=True))
            if filter_type == "ended":
                self.orders = self.orders.filter(end_date__lt=now)
            if filter_type == "unapproved":
                self.orders = self.orders.filter(approved=False)

        return self.orders

    def get_context_data(self, **kwargs):
        filter_type_params = ["actual", "ended", "unapproved", "all"]
        context = super().get_context_data(**kwargs)
        filter_type = self.request.GET.get("type", None)
        if filter_type not in filter_type_params:
            filter_type = "all"
        context['filter_type'] = filter_type
        context["search_form"] = ListSearchForm(
            placeholder="Search...",
            initial={"search_data": self.search_query}
        )
        return context
