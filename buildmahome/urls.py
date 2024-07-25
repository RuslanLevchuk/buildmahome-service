from django.urls import path

from .views import (
    IndexView,
    UserCreateView,
    UserProfileView,
    UserUpdateView,
    WorkerListView,
    WorkTeamListView,
    WorkTeamDetailView,
    MakeWorkerView,
    WorkTeamCreateView,
    SuccessfulActionView,
    WorkTeamUpdateView,
    SkillsListView,
    SkillCreateView
)




urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("accounts/sign_up/", UserCreateView.as_view(), name="sign_up"),
    path("accounts/<int:pk>/profile/", UserProfileView.as_view(), name="profile"),
    path("accounts/<int:pk>/update/", UserUpdateView.as_view(), name="update"),
    path("workers/", WorkerListView.as_view(), name="worker_list"),
    path("workteams/", WorkTeamListView.as_view(), name="work_team_list"),
    path("workteams/<int:pk>/", WorkTeamDetailView.as_view(), name="work_team_detail"),
    path("accounts/upgrade/", MakeWorkerView.as_view(), name="make_worker"),
    path("workteams/create", WorkTeamCreateView.as_view(), name="work_team_create"),
    path("succesful/", SuccessfulActionView.as_view(), name="successful_action"),
    path("workteams/<int:pk>/update/", WorkTeamUpdateView.as_view(), name="team_update"),
    path("skills/", SkillsListView.as_view(), name="skills_list"),
    path("skills/create", SkillCreateView.as_view(), name="skill_create"),
]

app_name = "buildmahome"
