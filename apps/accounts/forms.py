from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import User, TennisPlayer, Referee
from django.core.exceptions import ValidationError



class UserRegistrationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return cleaned_data
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'user_type', 'password1', 'password2']


class TennisPlayerForm(forms.ModelForm):
    class Meta:
        model = TennisPlayer
        fields = ['date_of_birth', 'gender', 'ranking']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean_ranking(self):
        ranking = self.cleaned_data.get('ranking')
        if ranking is not None and ranking <= 0:
            raise forms.ValidationError("Ranking must be greater than 0.")
        return ranking



class RefereeForm(forms.ModelForm):
    class Meta:
        model = Referee
        fields = ['certification_level']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class PlayerProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = TennisPlayer
        fields = ['date_of_birth', 'gender', 'ranking']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean_ranking(self):
        ranking = self.cleaned_data.get('ranking')
        if ranking is not None and ranking <= 0:
            raise forms.ValidationError("Ranking must be greater than 0.")
        return ranking

class RefereeProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Referee
        fields = ['certification_level']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


