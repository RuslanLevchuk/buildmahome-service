from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.forms import CheckboxSelectMultiple

from buildmahome.models import User, WorkTeam, Worker, Skill


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

