from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.views import View
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, TennisPlayerForm, RefereeForm
from .models import User, TennisPlayer, Referee
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView, DetailView
from .forms import UserUpdateForm, PlayerProfileUpdateForm, RefereeProfileUpdateForm, CustomPasswordChangeForm
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from core.mixins import PlayerRequiredMixin, RefereeRequiredMixin, OwnershipRequiredMixin


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
        next_url = request.POST.get('next') or request.GET.get('next') or 'home'

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, self.template_name, {'next': next_url})

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

        from apps.notifications.models import Notification
        context['unread_notifications_count'] = Notification.objects.filter(
            user=user,
            is_read=False
        ).count()
        
        context['action_required_count'] = Notification.objects.filter(
            user=user,
            is_read=False,
            requires_action=True
        ).count()

        if user.is_player():
            context['is_player'] = True
            context['player_profile'] = user.tennis_player
            
            # Get player's matches (both as player1 and player2)
            from apps.matches.models import Match
            player_matches = Match.objects.filter(
                Q(player1=user) | Q(player2=user)
            ).order_by('-tournament__start_date', 'round_number')
            
            context['player_matches'] = player_matches
            
            # Get recent upcoming matches
            context['upcoming_matches'] = player_matches.filter(
                status__in=['SCHEDULED', 'IN_PROGRESS']
            )[:5]
            
            # Get recent completed matches
            context['completed_matches'] = player_matches.filter(
                status='COMPLETED'
            )[:5]
            
        elif user.is_referee():
            context['is_referee'] = True
            context['referee_profile'] = user.referee
            
            # Get matches officiated by this referee
            from apps.matches.models import Match
            context['officiated_matches'] = Match.objects.filter(
                referee=user.referee
            ).order_by('-tournament__start_date', 'round_number')
            
            # Get upcoming matches to officiate
            context['upcoming_officiated_matches'] = context['officiated_matches'].filter(
                status__in=['SCHEDULED', 'IN_PROGRESS']
            )[:5]
            
            # Get completed matches officiated
            context['completed_officiated_matches'] = context['officiated_matches'].filter(
                status='COMPLETED'
            )[:5]
            
        elif user.is_admin():
            context['is_admin'] = True
            
            # Get recent tournaments for admin
            from apps.tournaments.models import Tournament
            context['recent_tournaments'] = Tournament.objects.all().order_by(
                '-start_date'
            )[:5]
            
            # Get matches that need referee assignment
            from apps.matches.models import Match
            context['unassigned_matches'] = Match.objects.filter(
                referee__isnull=True,
                status__in=['SCHEDULED', 'IN_PROGRESS']
            ).order_by('tournament__start_date', 'round_number')[:10]

        return context

# Create a class for viewing other players' profiles with ownership checks
class PlayerProfileView(LoginRequiredMixin, OwnershipRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/player_profile.html'
    context_object_name = 'viewed_player'
    
    def get_owner(self):
        return self.get_object()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        if hasattr(user, 'tennis_player'):
            context['player_profile'] = user.tennis_player
            
            from apps.matches.models import Match
            from django.db.models import Q
            
            # Only show completed matches for privacy
            player_matches = Match.objects.filter(
                Q(player1=user) | Q(player2=user),
                status='COMPLETED'
            ).order_by('-tournament__start_date', 'round_number')
            
            context['player_matches'] = player_matches
            
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


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to restrict views to admin users only"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin()
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('accounts:profile')

class UserListView(AdminRequiredMixin, ListView):
    """View for admins to see all users"""
    model = User
    template_name = 'accounts/admin/user_list.html'
    context_object_name = 'users'
    
    def get_queryset(self):
        # Get the filter parameter from the URL query string
        user_type = self.request.GET.get('type', None)
        queryset = User.objects.all().order_by('username')
        
        # Filter by user type if specified
        if user_type:
            queryset = queryset.filter(user_type=user_type.upper())
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_type'] = self.request.GET.get('type', None)
        return context

class AdminEditUserView(AdminRequiredMixin, UpdateView):
    """View for admins to edit any user profile"""
    model = User
    form_class = UserUpdateForm
    template_name = 'accounts/admin/edit_user.html'
    
    def get_success_url(self):
        messages.success(self.request, f"User {self.object.username}'s profile updated successfully!")
        return reverse('accounts:admin_user_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Add player form if user is a player
        if hasattr(user, 'tennis_player'):
            if self.request.POST:
                context['player_form'] = PlayerProfileUpdateForm(
                    self.request.POST, 
                    instance=user.tennis_player
                )
            else:
                context['player_form'] = PlayerProfileUpdateForm(instance=user.tennis_player)
                
        # Add referee form if user is a referee
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
        user = self.object
        
        # Handle player form
        if hasattr(user, 'tennis_player'):
            player_form = PlayerProfileUpdateForm(
                request.POST, 
                instance=user.tennis_player
            )
            if form.is_valid() and player_form.is_valid():
                form.save()
                player_form.save()
                return redirect(self.get_success_url())
            else:
                return self.render_to_response(
                    self.get_context_data(form=form, player_form=player_form)
                )
                
        # Handle referee form
        elif hasattr(user, 'referee'):
            referee_form = RefereeProfileUpdateForm(
                request.POST, 
                instance=user.referee
            )
            if form.is_valid() and referee_form.is_valid():
                form.save()
                referee_form.save()
                return redirect(self.get_success_url())
            else:
                return self.render_to_response(
                    self.get_context_data(form=form, referee_form=referee_form)
                )
                
        # Handle admin form (no profile)
        else:
            if form.is_valid():
                form.save()
                return redirect(self.get_success_url())
            else:
                return self.render_to_response(
                    self.get_context_data(form=form)
                )

class UserDetailView(AdminRequiredMixin, DetailView):
    """View for admins to see detailed user info"""
    model = User
    template_name = 'accounts/admin/user_detail.html'
    context_object_name = 'user_detail'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        if hasattr(user, 'tennis_player'):
            context['is_player'] = True
            context['player_profile'] = user.tennis_player
        elif hasattr(user, 'referee'):
            context['is_referee'] = True
            context['referee_profile'] = user.referee
        elif user.is_admin():
            context['is_admin'] = True
            
        return context