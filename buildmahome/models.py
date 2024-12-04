from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models


class User(AbstractUser):
    is_worker = models.BooleanField(default=False, null=False, blank=False)
    groups = models.ManyToManyField(
        Group,
        related_name='bmh_user_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='bmh_user_set',
        blank=True
    )

    def __str__(self):
        return self.username


class Position(models.Model):
    name = models.CharField(max_length=50, unique=True, blank=False, null=False)

    def __str__(self) -> str:
        return self.name


class Skill(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class WorkTeam(models.Model):
    name = models.CharField(max_length=50, unique=True, blank=False, null=False)
    description = models.TextField(blank=True)
    phone_number = models.CharField(max_length=12, unique=True)

    def __str__(self) -> str:
        return self.name


class Worker(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    about = models.TextField(blank=True)
    position = models.ManyToManyField(
        Position,
        related_name='workers',
        blank=True
    )
    skills = models.ManyToManyField(Skill, related_name='workers', blank=True)
    is_active = models.BooleanField(default=True, blank=False, null=False)
    phone_number = models.CharField(max_length=12, unique=True)
    team = models.ForeignKey(
        WorkTeam,
        related_name='workers',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    groups = models.ManyToManyField(
        Group,
        related_name='bmh_worker_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='bmh_worker_set',
        blank=True
    )

    def __str__(self) -> str:
        return self.user.username


class Task(models.Model):
    name = models.CharField(max_length=255, blank=False, null=False)
    description = models.TextField(blank=True)
    customer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tasks'
    )
    work_team = models.ForeignKey(
        WorkTeam,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tasks'
    )
    approved = models.BooleanField(default=False)
    creation_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self) -> str:
        return self.name
