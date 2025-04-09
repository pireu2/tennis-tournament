from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
import csv
from django.http import HttpResponse
import datetime

from .models import Match, MatchScore
from .forms import MatchScoreForm

from core.observers import TournamentNotificationSubject, EmailNotifier, DatabaseNotifier

tournament_notifier = TournamentNotificationSubject()
email_observer = EmailNotifier()
db_observer = DatabaseNotifier()

tournament_notifier.attach(email_observer)
tournament_notifier.attach(db_observer)

class MatchListView(ListView):
    model = Match
    template_name = 'matches/match_list.html'
    context_object_name = 'matches'
    
    def get_queryset(self):
        queryset = Match.objects.all().order_by('-tournament__start_date', 'round_number')
        status_filter = self.request.GET.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Match.STATUS_CHOICES
        context['status_filter'] = self.request.GET.get('status', None)
        
        # Add a flag to indicate if the user is an admin
        context['is_admin'] = self.request.user.is_authenticated and self.request.user.is_admin()
        
        return context

# Add these functions after the class definitions

def export_matches_csv(request):
    if not request.user.is_authenticated or not request.user.is_admin():
        messages.error(request, "You don't have permission to export matches.")
        return redirect('matches:match_list')  # Change this if needed to match your actual URL name
    
    # Get selected match IDs from POST data
    match_ids = request.POST.getlist('match_ids')
    if not match_ids:
        messages.error(request, "No matches selected for export.")
        return redirect('matches:match_list')  # Change this if needed
    
    
    queryset = Match.objects.filter(id__in=match_ids)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename=matches-{datetime.date.today().isoformat()}.csv'
    
    writer = csv.writer(response)
    # Write header row
    writer.writerow([
        'Match ID', 'Tournament', 'Round', 'Player 1', 'Player 2',
        'Status', 'Scheduled Time', 'Court', 'Referee',
        'Set 1', 'Set 2', 'Set 3', 'Winner'
    ])
    
    # Write data rows
    for match in queryset:
        # Get score info if available
        set1_score = set2_score = set3_score = winner_name = "N/A"
        try:
            if hasattr(match, 'score'):
                score = match.score
                if score.player1_set1 is not None and score.player2_set1 is not None:
                    set1_score = f"{score.player1_set1}-{score.player2_set1}"
                if score.player1_set2 is not None and score.player2_set2 is not None:
                    set2_score = f"{score.player1_set2}-{score.player2_set2}"
                if score.player1_set3 is not None and score.player2_set3 is not None:
                    set3_score = f"{score.player1_set3}-{score.player2_set3}"
                if score.winner:
                    winner_name = score.winner.get_full_name()
        except Match.score.RelatedObjectDoesNotExist:
            pass
        
        writer.writerow([
            match.id,
            match.tournament.name if match.tournament else "N/A",
            f"Round {match.round_number}" if match.round_number else "Unknown Round",
            match.player1.get_full_name() if match.player1 else "TBD",
            match.player2.get_full_name() if match.player2 else "TBD",
            match.get_status_display(),
            match.scheduled_time.strftime('%Y-%m-%d %H:%M') if match.scheduled_time else "Not scheduled",
            match.court_number or "Not assigned",
            match.referee.user.get_full_name() if match.referee and match.referee.user else "Not assigned",
            set1_score,
            set2_score,
            set3_score,
            winner_name
        ])
    
    return response

def export_matches_txt(request):
    if not request.user.is_authenticated or not request.user.is_admin():
        messages.error(request, "You don't have permission to export matches.")
        return redirect('matches:match_list')  # Change this if needed
    
    # Get selected match IDs from POST data
    match_ids = request.POST.getlist('match_ids')
    if not match_ids:
        messages.error(request, "No matches selected for export.")
        return redirect('matches:match_list')  # Change this if needed
    
    
    queryset = Match.objects.filter(id__in=match_ids)
    
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename=matches-{datetime.date.today().isoformat()}.txt'
    
    # Write header
    response.write("TENNIS TOURNAMENT - MATCH EXPORT\n")
    response.write(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    response.write(f"Number of matches: {queryset.count()}\n")
    response.write("=" * 80 + "\n\n")
    
    # Write data for each match
    for match in queryset:
        response.write(f"MATCH ID: {match.id}\n")
        response.write(f"Tournament: {match.tournament.name if match.tournament else 'N/A'}\n")
        response.write(f"Round: {f'Round {match.round_number}' if match.round_number else 'Unknown Round'}\n")
        response.write(f"Status: {match.get_status_display()}\n")
        
        response.write(f"Player 1: {match.player1.get_full_name() if match.player1 else 'TBD'}\n")
        response.write(f"Player 2: {match.player2.get_full_name() if match.player2 else 'TBD'}\n")
        
        if match.scheduled_time:
            response.write(f"Scheduled Time: {match.scheduled_time.strftime('%Y-%m-%d %H:%M')}\n")
        
        if match.court_number:
            response.write(f"Court: {match.court_number}\n")
            
        if match.referee and match.referee.user:
            response.write(f"Referee: {match.referee.user.get_full_name()}\n")
        
        # Add score information
        response.write("Score:\n")
        try:
            if hasattr(match, 'score'):
                score = match.score
                if score.player1_set1 is not None and score.player2_set1 is not None:
                    response.write(f"  Set 1: {score.player1_set1}-{score.player2_set1}\n")
                if score.player1_set2 is not None and score.player2_set2 is not None:
                    response.write(f"  Set 2: {score.player1_set2}-{score.player2_set2}\n")
                if score.player1_set3 is not None and score.player2_set3 is not None:
                    response.write(f"  Set 3: {score.player1_set3}-{score.player2_set3}\n")
                
                if score.winner:
                    response.write(f"Winner: {score.winner.get_full_name()}\n")
            else:
                response.write("  No score recorded\n")
        except Match.score.RelatedObjectDoesNotExist:
            response.write("  No score recorded\n")
        
        response.write("\n" + "-" * 40 + "\n\n")
    
    return response

class MatchDetailView(DetailView):
    model = Match
    template_name = 'matches/match_detail.html'
    context_object_name = 'match'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        match = self.get_object()
        
        user = self.request.user
        if user.is_authenticated and user.is_referee():
            if hasattr(match, 'referee') and match.referee and match.referee.user == user:
                # Check if the match has a score
                try:
                    # Try to get the score instance
                    score_instance = match.score
                    context['score_form'] = MatchScoreForm(instance=score_instance)
                except match._meta.model.score.RelatedObjectDoesNotExist:
                    # If no score record exists yet, provide an empty form
                    context['score_form'] = MatchScoreForm()
        
        # Check if user is the referee
        if user.is_authenticated and user.is_referee():
            context['is_referee'] = True
            if hasattr(match, 'referee') and match.referee:
                context['is_match_referee'] = match.referee.user == user
            else:
                context['is_match_referee'] = False
        
        return context

class RefereeSignupView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        match = get_object_or_404(Match, pk=kwargs['pk'])
        
        # Check if user is a referee
        if not request.user.is_referee():
            messages.error(request, "Only referees can sign up to officiate matches.")
            return HttpResponseRedirect(reverse('matches:match_detail', kwargs={'pk': match.pk}))
        
        # Check if match already has a referee
        if match.referee and match.referee.user != request.user:
            messages.error(request, "This match already has a referee assigned.")
            return HttpResponseRedirect(reverse('matches:match_detail', kwargs={'pk': match.pk}))
        
        # Check if match is scheduled (not completed or cancelled)
        if match.status not in ['SCHEDULED', 'IN_PROGRESS']:
            messages.error(request, "Cannot sign up for matches that are completed or cancelled.")
            return HttpResponseRedirect(reverse('matches:match_detail', kwargs={'pk': match.pk}))
        
        # Assign referee to match
        if match.referee and match.referee.user == request.user:
            # Unassign if already assigned
            match.referee = None
            match.save()
            messages.success(request, "You have been unassigned from this match.")
        else:
            match.referee = request.user.referee
            match.save()
            messages.success(request, "You have been assigned as the referee for this match.")
        
        return HttpResponseRedirect(reverse('matches:match_detail', kwargs={'pk': match.pk}))

class UpdateScoreView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        match = get_object_or_404(Match, pk=kwargs['pk'])
        
        # Check if user is the assigned referee
        if not request.user.is_referee() or not match.referee or match.referee.user != request.user:
            messages.error(request, "Only the assigned referee can update match scores.")
            return HttpResponseRedirect(reverse('matches:match_detail', kwargs={'pk': match.pk}))
        
        # Check if match is in progress
        if match.is_completed() or match.is_canceled():
            messages.error(request, "Cannot update scores for completed or cancelled matches.")
            return HttpResponseRedirect(reverse('matches:match_detail', kwargs={'pk': match.pk}))
        
        # Get or create the score object
        try:
            score_instance = match.score
        except Match.score.RelatedObjectDoesNotExist:
            # Create a new score instance if it doesn't exist
            score_instance = MatchScore(match=match)
            score_instance.save()
        
        # Now use the score instance with the form
        form = MatchScoreForm(request.POST, instance=score_instance)
        
        if form.is_valid():
            score = form.save(commit=False)
            
            # Determine winner
            winner = score.determine_winner()
            score.winner = winner
            score.save()
            
            # Update match status if a winner is determined
            if winner:
                match.status = 'COMPLETED'
                match.save()
                tournament_notifier.match_result_recorded(match)
                
                # Generate next round match if applicable
                self.advance_winner_to_next_round(match, winner)
                
                messages.success(request, "Match score updated and match completed.")
            else:
                match.status = 'IN_PROGRESS'
                match.save()
                messages.success(request, "Match score updated. No winner determined yet.")
            
            return HttpResponseRedirect(reverse('matches:match_detail', kwargs={'pk': match.pk}))
        else:
            messages.error(request, "Error updating match score. Please check the form.")
            return render(request, 'matches/match_detail.html', {
                'match': match,
                'score_form': form,
                'is_referee': request.user.is_referee(),
                'is_match_referee': match.referee and match.referee.user == request.user
            })
    
    def advance_winner_to_next_round(self, match, winner):
        """Create or update next round match with the winner"""
        tournament = match.tournament
        next_round = match.round_number + 1
        
        # Find potential matches in the next round
        # Logic: In a bracket, match X in round N feeds into match X//2 in round N+1
        next_matches = Match.objects.filter(
            tournament=tournament,
            round_number=next_round
        ).order_by('id')
        
        # Get the match index in current round (0-based)
        current_round_matches = list(Match.objects.filter(
            tournament=tournament,
            round_number=match.round_number
        ).order_by('id'))
        
        match_index = current_round_matches.index(match)
        next_match_index = match_index // 2
        
        # If the next round match already exists, update it
        if next_match_index < len(next_matches):
            next_match = next_matches[next_match_index]
            
            # Determine if this winner should be player1 or player2
            if match_index % 2 == 0:  # Even index goes to player1
                next_match.player1 = winner
            else:  # Odd index goes to player2
                next_match.player2 = winner
                
            next_match.save()
            
        # If the next round match doesn't exist yet but we have both winners, create it
        elif next_match_index >= len(next_matches):
            # Find the paired match
            paired_index = match_index + 1 if match_index % 2 == 0 else match_index - 1
            
            # Check if the paired match exists and is completed
            paired_matches = [m for m in current_round_matches if current_round_matches.index(m) == paired_index]
            
            if paired_matches and hasattr(paired_matches[0], 'score') and paired_matches[0].score.winner:
                paired_match = paired_matches[0]
                paired_winner = paired_match.score.winner
                
                # Create the next round match
                if match_index % 2 == 0:
                    player1, player2 = winner, paired_winner
                else:
                    player1, player2 = paired_winner, winner
                
                new_match = Match.objects.create(
                    tournament=tournament,
                    player1=player1,
                    player2=player2,
                    round_number=next_round,
                    status='SCHEDULED'
                )
                
                # Create empty score object
                MatchScore.objects.create(match=new_match)