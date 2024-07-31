from bootstrap_datepicker_plus.widgets import DatePickerInput
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.forms import CheckboxSelectMultiple

from buildmahome.models import User, WorkTeam, Worker, Skill, Task

from datetime import date

class PasswordsMixin(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation',
                                widget=forms.PasswordInput)

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password2")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class SignUpForm(PasswordsMixin):

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + (
            "email",
        )


class UserUpdateForm(PasswordsMixin):
    old_password = forms.CharField(
        label="Old password",
        widget=forms.PasswordInput,
        required=False,
        strip=False
    )
    password1 = forms.CharField(
        label='New password',
        widget=forms.PasswordInput,
        required=False
    )
    password2 = forms.CharField(
        label='New password confirmation',
        widget=forms.PasswordInput,
        required=False
    )
    about = forms.CharField(
        label='About',
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False
    )
    phone_number = forms.CharField(
        label='Phone Number',
        required=False
    )
    team = forms.ModelChoiceField(
        queryset=WorkTeam.objects.all(),
        required=False
    )
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        required=False,
        widget=CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "old_password",
            "password1",
            "password2",
            "about",
            "phone_number",
            "team",
            "skills",
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        try:
            worker = Worker.objects.get(user=self.user)
            self.fields['about'].initial = worker.about
            self.fields['phone_number'].initial = worker.phone_number
            self.fields['team'].initial = worker.team
            self.fields["skills"].initial = worker.skills.all()
        except Worker.DoesNotExist:
            pass

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        password2 = self.cleaned_data.get('password2')
        if password2 and not old_password:
            raise forms.ValidationError(
                "Old password is required to set a new password.")
        if old_password and not self.user.check_password(old_password):
            raise forms.ValidationError("Old password is incorrect.")
        return old_password

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password2")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        try:
            worker = Worker.objects.get(user=user)
            worker.about = self.cleaned_data.get('about', worker.about)
            worker.phone_number = self.cleaned_data.get('phone_number', worker.phone_number)
            worker.team = self.cleaned_data.get('team', worker.team)
            skills = self.cleaned_data.get('skills', None)
            if skills is not None:
                worker.skills.set(skills)
            worker.save()
        except Worker.DoesNotExist:
            pass
        return user


class WorkTeamCreateFrom(forms.ModelForm):
    workers = forms.ModelMultipleChoiceField(
        queryset=Worker.objects.none(),
        required=False,
        widget=CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label="Available Workers"
    )

    class Meta:
        model = WorkTeam
        fields = ("name", "description", "phone_number", "workers")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user:
            try:
                worker = Worker.objects.get(user=self.user)
                self.fields['workers'].queryset = Worker.objects.filter(
                        team__isnull=True).exclude(user=worker.user)
                self.fields['phone_number'].initial = worker.phone_number
            except Worker.DoesNotExist:
                pass

    def save(self, commit=True):
        work_team = super().save(commit=False)
        if commit:
            work_team.save()
            self.save_m2m()

        if self.user:
            try:
                worker = Worker.objects.get(user=self.user)
                worker.team = work_team
                worker.save()
            except Worker.DoesNotExist:
                pass
        selected_workers = self.cleaned_data['workers']
        selected_workers.update(team=work_team)
        return work_team


class WorkTeamUpdateFrom(forms.ModelForm):
    workers = forms.ModelMultipleChoiceField(
        queryset=Worker.objects.none(),
        required=False,
        widget=CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label="Available Workers"
    )

    class Meta:
        model = WorkTeam
        fields = ("name", "description", "phone_number", "workers")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        instance = kwargs.get('instance')

        if instance and self.user:
            team_members = instance.workers.all().exclude(user=self.user)

            workers_without_team = Worker.objects.filter(team__isnull=True)

            self.fields[
                'workers'].queryset = workers_without_team | team_members
            self.fields['workers'].initial = team_members

    def save(self, commit=True):
        work_team = super().save(commit=False)
        if commit:
            work_team.save()
            self.save_m2m()

        selected_workers = list(self.cleaned_data.get('workers', []))

        if self.user:
            try:
                current_worker = Worker.objects.get(user=self.user)
                selected_workers.append(current_worker)
            except Worker.DoesNotExist:
                pass

        work_team.workers.set(selected_workers)

        return work_team


class SkillCreateForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ("name", "description")


class ListSearchForm(forms.Form):

    search_data = forms.CharField(
        max_length=100,
        required=False,
        label="",
        widget=forms.TextInput()
    )

    def __init__(self, *args, placeholder="Search", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["search_data"].widget.attrs["placeholder"] = placeholder


class TaskCreateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ("name", "description", "work_team", "start_date")
        widgets = {
            'start_date': DatePickerInput(options={
                "format": "YYYY-MM-DD",
                "showClose": True,
                "showClear": False,
                "showTodayButton": True,
                "minDate": date.today(),
            }),
        }

    def __init__(self, *args, **kwargs):
        work_team = kwargs.pop('work_team', None)
        super().__init__(*args, **kwargs)
        if work_team is not None:
            self.fields['work_team'].queryset = WorkTeam.objects.filter(
                pk=work_team.pk)
            self.fields['work_team'].initial = work_team

