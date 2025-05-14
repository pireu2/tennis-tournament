from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils import timezone
import random

from .models import Tournament
from apps.accounts.models import User
from apps.matches.models import Match, MatchScore
from .forms import TournamentForm

from core.strategies.match_generator import (
    MatchGeneratorContext, 
    SingleEliminationStrategy,
    RoundRobinStrategy
)
from core.observers import TournamentNotificationSubject, EmailNotifier, DatabaseNotifier
from core.mixins import PlayerRequiredMixin, RefereeRequiredMixin, OwnershipRequiredMixin

# Set up the notification system
tournament_notifier = TournamentNotificationSubject()
email_observer = EmailNotifier()
db_observer = DatabaseNotifier()

# Register both observers
tournament_notifier.attach(email_observer)
tournament_notifier.attach(db_observer)

class AdminRequiredMixin:
    """Mixin to restrict views to admin users only"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin():
            messages.error(request, "You don't have permission to access this page.")
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)

class TournamentListView(ListView):
    model = Tournament
    template_name = 'tournaments/tournament_list.html'
    context_object_name = 'tournaments'
    
    def get_queryset(self):
        queryset = Tournament.objects.all().order_by('-start_date')
        status_filter = self.request.GET.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', None)
        return context

class TournamentCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Tournament
    form_class = TournamentForm
    template_name = 'tournaments/tournament_form.html'
    success_url = reverse_lazy('tournaments:tournament_list')

    def form_valid(self, form):
        form.instance.organizer = self.request.user
        response = super().form_valid(form)
 
        tournament_notifier.tournament_created(self.object)

        messages.success(self.request, "Tournament created successfully!")
        return response

class TournamentDetailView(LoginRequiredMixin, DetailView):
    model = Tournament
    template_name = 'tournaments/tournament_detail.html'
    context_object_name = 'tournament'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tournament = self.get_object()
        user = self.request.user
        
        # Check if user is registered in this tournament
        context['is_registered'] = tournament.participants.filter(id=user.id).exists()
        context['is_pending'] = tournament.pending_registrations.filter(id=user.id).exists()
        
        # Check user type for showing appropriate data
        context['is_player'] = user.is_player()
        context['is_admin'] = user.is_admin()
        context['is_referee'] = user.is_referee()
        
        # Only allow tournament organizer or admins to see pending registrations
        if user.is_admin() and (user == tournament.organizer or user.is_superuser):
            context['pending_players'] = tournament.pending_registrations.all()
        
        # Get matches that user has access to
        match_filter = {}
        if not (user.is_admin() or user.is_referee() or 
                tournament.participants.filter(id=user.id).exists()):
            # Users not involved can only see published matches
            match_filter['status'] = 'COMPLETED'
            
        context['tournament_matches'] = tournament.matches.filter(**match_filter)
        
        return context

class TournamentUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Tournament
    form_class = TournamentForm
    template_name = 'tournaments/tournament_form.html'
    
    def get_success_url(self):
        return reverse('tournaments:tournament_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, "Tournament updated successfully!")
        return super().form_valid(form)

class PlayerRegistrationView(LoginRequiredMixin, PlayerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        tournament = get_object_or_404(Tournament, pk=kwargs['pk'])
        
        # Check if user is a player
        if not request.user.is_player():
            messages.error(request, "Only tennis players can register for tournaments.")
            return HttpResponseRedirect(reverse('tournaments:tournament_detail', kwargs={'pk': tournament.pk}))
        
        # Check if registration is open
        if not tournament.is_registration_open():
            messages.error(request, "Registration is not open for this tournament.")
            return HttpResponseRedirect(reverse('tournaments:tournament_detail', kwargs={'pk': tournament.pk}))
        
        # Check if tournament is full
        if tournament.participants.count() >= tournament.max_participants:
            messages.error(request, "Tournament has reached maximum number of participants.")
            return HttpResponseRedirect(reverse('tournaments:tournament_detail', kwargs={'pk': tournament.pk}))
        
        # Check if user is already registered or has pending registration
        if tournament.participants.filter(id=request.user.id).exists():
            tournament.participants.remove(request.user)
            messages.success(request, "You have been unregistered from the tournament.")
        elif tournament.pending_registrations.filter(id=request.user.id).exists():
            tournament.pending_registrations.remove(request.user)
            messages.success(request, "Your registration request has been withdrawn.")
        else:
            # Add to pending registrations instead of directly to participants
            tournament.pending_registrations.add(request.user)
            messages.success(request, "Your registration request has been submitted and is pending approval.")
            
            # Notify tournament organizer about the pending approval
            tournament_notifier.player_registration_needs_approval(tournament, request.user)
        
        return HttpResponseRedirect(reverse('tournaments:tournament_detail', kwargs={'pk': tournament.pk}))

class GenerateMatchesView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        tournament = get_object_or_404(Tournament, pk=kwargs['pk'])
        
        # Check if tournament can generate matches
        if not tournament.can_generate_matches():
            messages.error(request, "Cannot generate matches at this time.")
            return HttpResponseRedirect(reverse('tournaments:tournament_detail', kwargs={'pk': tournament.pk}))
        
        # Check if matches already exist
        if Match.objects.filter(tournament=tournament).exists():
            messages.error(request, "Matches have already been generated for this tournament.")
            return HttpResponseRedirect(reverse('tournaments:tournament_detail', kwargs={'pk': tournament.pk}))
        
        # Get all players
        players = list(tournament.participants.all())
        
        # Use strategy pattern to generate matches
        generator = MatchGeneratorContext()
        
        # Choose strategy based on tournament type or request parameter
        if tournament.tournament_type == 'ROUND_ROBIN':
            generator.set_strategy(RoundRobinStrategy())
        else:
            generator.set_strategy(SingleEliminationStrategy())
            
        # Generate matches
        matches = generator.generate_tournament_matches(tournament, players)
        
        # Update tournament status
        tournament.status = 'IN_PROGRESS'
        tournament.save()
        
        # Redirect to tournament detail page
        messages.success(request, f"{len(matches)} matches have been generated successfully.")
        return HttpResponseRedirect(reverse('tournaments:tournament_detail', kwargs={'pk': tournament.pk}))

class TournamentMatchesView(ListView):
    template_name = 'tournaments/tournament_matches.html'
    context_object_name = 'matches'
    
    def get_queryset(self):
        self.tournament = get_object_or_404(Tournament, pk=self.kwargs['tournament_id'])
        return Match.objects.filter(tournament=self.tournament).order_by('round_number', 'id')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = self.tournament
        
        # Group matches by round
        matches_by_round = {}
        for match in context['matches']:
            if match.round_number not in matches_by_round:
                matches_by_round[match.round_number] = []
            matches_by_round[match.round_number].append(match)
        
        context['matches_by_round'] = matches_by_round
        return context
    
class UpdateTournamentStatusView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        tournament = get_object_or_404(Tournament, pk=kwargs['pk'])
        
        # Update tournament status logic
        old_status = tournament.status
        new_status = request.POST.get('status')
        
        if new_status and new_status in dict(Tournament.STATUS_CHOICES):
            tournament.status = new_status
            tournament.save()
            
            # Notify observers about the status change
            if old_status != new_status:
                tournament_notifier.tournament_status_changed(tournament)
                
            messages.success(request, "Tournament status updated successfully.")
        else:
            messages.error(request, "Invalid tournament status.")
            
        return HttpResponseRedirect(reverse('tournaments:tournament_detail', kwargs={'pk': tournament.pk}))
    


from django.http import JsonResponse


class ApproveRegistrationView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        tournament_id = kwargs.get('pk')
        player_id = request.POST.get('player_id')
        action = request.POST.get('action')  # 'approve' or 'reject'
        
        tournament = get_object_or_404(Tournament, pk=tournament_id)
        
        if request.user != tournament.organizer and not request.user.is_superuser:
            messages.error(request, "Only the tournament organizer can approve registrations.")
            return HttpResponseRedirect(reverse('tournaments:tournament_detail', kwargs={'pk': tournament_id}))
        
        try:
            from apps.accounts.models import User
            player = User.objects.get(pk=player_id)
            
            if action == 'approve':
                # Add player to tournament participants
                tournament.participants.add(player)
                # Add this after getting the player object
                tournament.pending_registrations.remove(player)
                
                # Notify the player that their registration was approved
                from apps.notifications.models import Notification
                Notification.objects.create(
                    user=player,
                    message=f"Your registration for '{tournament.name}' has been approved",
                    notification_type='TOURNAMENT',
                    related_id=tournament.id
                )
                
                # Send email notification
                tournament_notifier.player_registered(tournament, player)
                
                messages.success(request, f"Registration for {player.get_full_name()} has been approved.")
                
            elif action == 'reject':
                # Just remove from pending registrations without adding to participants
                tournament.pending_registrations.remove(player)
                messages.info(request, f"Registration for {player.get_full_name()} has been rejected.")
                
                # Notify the player that their registration was rejected
                notify_player_of_rejection(tournament, player)
            
            # Remove the approval notification for the organizer
            from apps.notifications.models import Notification
            Notification.objects.filter(
                user=tournament.organizer,
                notification_type='REGISTRATION_APPROVAL',
                related_id=tournament.id,
                message__contains=player.get_full_name()
            ).delete()
            
            # Fix: Replace is_ajax() with the modern way
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
                
            return HttpResponseRedirect(reverse('tournaments:tournament_detail', kwargs={'pk': tournament_id}))
            
        except User.DoesNotExist:
            messages.error(request, "Player not found.")
            
        except Exception as e:
            messages.error(request, f"Error processing registration: {str(e)}")
        
        # Add this check for AJAX requests at the end too
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False}, status=400)
            
        return HttpResponseRedirect(reverse('tournaments:tournament_detail', kwargs={'pk': tournament_id}))

def notify_player_of_rejection(tournament, player):
    """Notify player that their registration was rejected"""
    try:
        # Create a notification for the player
        Notification.objects.create(
            user=player,
            title="Tournament Registration Rejected",
            message=f"Your registration for {tournament.name} has been rejected.",
            notification_type='REGISTRATION_REJECTED'
        )
        
        # Optionally send an email if player has an email address
        if player.email:
            send_mail(
                f"Registration Rejected: {tournament.name}",
                f"Dear {player.get_full_name() or player.username},\n\nYour registration for the tournament '{tournament.name}' has been rejected.\n\nThank you.",
                settings.DEFAULT_FROM_EMAIL,
                [player.email],
                fail_silently=True,
            )
    except Exception:
        # Log the error but don't stop execution
        logger.exception("Failed to notify player of rejection")