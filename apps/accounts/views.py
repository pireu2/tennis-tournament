from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.views import View
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, TennisPlayerForm, RefereeForm
from .models import User, TennisPlayer, Referee
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView, DetailView
from .forms import UserUpdateForm, PlayerProfileUpdateForm, RefereeProfileUpdateForm, CustomPasswordChangeForm


def register_view(request):
    return render(request, 'accounts/register.html')

# Update the existing PlayerRegistrationView

class PlayerRegistrationView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/player_register.html'
    success_url = reverse_lazy('home')

    def get_initial(self):
        return {'user_type': 'PLAYER'}

    def form_valid(self, form):
        user = form.save(commit=False)
        player_form = TennisPlayerForm(self.request.POST)

        if player_form.is_valid():
            user.save()
            player = player_form.save(commit=False)
            player.user = user
            player.save()
            login(self.request, user)
            messages.success(self.request, "Registration successful!")
            return redirect(self.success_url)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['player_form'] = TennisPlayerForm(self.request.POST)
        else:
            context['player_form'] = TennisPlayerForm()
        return context


class RefereeRegistrationView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/referee_register.html'
    success_url = reverse_lazy('home')

    def get_initial(self):
        return {'user_type': 'REFEREE'}

    def form_valid(self, form):
        user = form.save(commit=False)
        referee_form = RefereeForm(self.request.POST)

        if referee_form.is_valid():
            user.save()
            referee = referee_form.save(commit=False)
            referee.user = user
            referee.save()
            login(self.request, user)
            messages.success(self.request, "Registration successful!")
            return redirect(self.success_url)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['referee_form'] = RefereeForm(self.request.POST)
        else:
            context['referee_form'] = RefereeForm()
        return context

class AdminRegistrationView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/admin_register.html'
    success_url = reverse_lazy('home')

    def get_initial(self):
        return {'user_type': 'ADMIN'}

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Admin registration successful!")
        return redirect(self.success_url)

class UserLogInView(CreateView):
    template_name = 'accounts/login.html'
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, self.template_name)

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')


class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'user_profile'

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_player():
            context['is_player'] = True
            context['player_profile'] = user.tennis_player
        elif user.is_referee():
            context['is_referee'] = True
            context['referee_profile'] = user.referee
        elif user.is_admin():
            context['is_admin'] = True

        return context

class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'accounts/edit_profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Your profile has been updated successfully!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if hasattr(user, 'tennis_player'):
            if self.request.POST:
                context['player_form'] = PlayerProfileUpdateForm(
                    self.request.POST, 
                    instance=user.tennis_player
                )
            else:
                context['player_form'] = PlayerProfileUpdateForm(instance=user.tennis_player)

        elif hasattr(user, 'referee'):
            if self.request.POST:
                context['referee_form'] = RefereeProfileUpdateForm(
                    self.request.POST, 
                    instance=user.referee
                )
            else:
                context['referee_form'] = RefereeProfileUpdateForm(instance=user.referee)

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        if hasattr(request.user, 'tennis_player'):
            player_form = PlayerProfileUpdateForm(
                request.POST, 
                instance=request.user.tennis_player
            )
            if form.is_valid() and player_form.is_valid():
                return self.form_valid(form, player_form)
            else:
                return self.form_invalid(form, player_form)

        elif hasattr(request.user, 'referee'):
            referee_form = RefereeProfileUpdateForm(
                request.POST, 
                instance=request.user.referee
            )
            if form.is_valid() and referee_form.is_valid():
                return self.form_valid(form, referee_form)
            else:
                return self.form_invalid(form, referee_form)

        else:
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)

    def form_valid(self, form, profile_form=None):
        form.save()
        if profile_form:
            profile_form.save()
        messages.success(self.request, "Your profile has been updated successfully!")
        return redirect(self.success_url)

    def form_invalid(self, form, profile_form=None):
        context = self.get_context_data(form=form)
        if profile_form:
            if hasattr(self.request.user, 'tennis_player'):
                context['player_form'] = profile_form
            elif hasattr(self.request.user, 'referee'):
                context['referee_form'] = profile_form
        return self.render_to_response(context)

class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = 'accounts/change_password.html'
    success_url = reverse_lazy('accounts:profile')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Your password has been changed successfully!")
        return response
