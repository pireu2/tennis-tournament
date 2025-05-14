from abc import ABC, abstractmethod
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

class Observer(ABC):
    """Abstract observer interface"""
    
    @abstractmethod
    def update(self, subject, **kwargs):
        """Method called when the subject notifies observers"""
        pass


class Subject(ABC):
    """Abstract subject class that observers can subscribe to"""
    
    def __init__(self):
        self._observers = []
    
    def attach(self, observer):
        """Register an observer"""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def detach(self, observer):
        """Remove an observer"""
        try:
            self._observers.remove(observer)
        except ValueError:
            pass
    
    def notify(self, **kwargs):
        """Notify all observers"""
        for observer in self._observers:
            observer.update(self, **kwargs)


class TournamentNotificationSubject(Subject):
    """Subject for tournament-related notifications"""
    
    def tournament_status_changed(self, tournament):
        """Notify observers when a tournament's status changes"""
        self.notify(
            event_type='tournament_status_change',
            tournament=tournament
        )
    
    def tournament_created(self, tournament):
        """Notify observers when a new tournament is created"""
        self.notify(
            event_type='tournament_created',
            tournament=tournament
        )
    
    def player_registered(self, tournament, player):
        """Notify observers when a player registers for a tournament"""
        self.notify(
            event_type='player_registered',
            tournament=tournament,
            player=player
        )
    
    def match_scheduled(self, match):
        """Notify observers when a match is scheduled"""
        self.notify(
            event_type='match_scheduled',
            match=match
        )
    
    def match_result_recorded(self, match):
        """Notify observers when a match result is recorded"""
        self.notify(
            event_type='match_result',
            match=match
        )

    def player_registration_needs_approval(self, tournament, player):
        """Notify observers when a player registration needs approval"""
        self.notify(
            event_type='registration_needs_approval',
            tournament=tournament,
            player=player
        )


class EmailNotifier(Observer):
    """Email notification observer"""
    
    def update(self, subject, **kwargs):
        """Process notification and send emails"""
        event_type = kwargs.get('event_type')
        
        if event_type == 'tournament_status_change':
            self._notify_tournament_status_change(kwargs.get('tournament'))
        elif event_type == 'tournament_created':
            self._notify_tournament_created(kwargs.get('tournament'))
        elif event_type == 'player_registered':
            self._notify_player_registered(kwargs.get('tournament'), kwargs.get('player'))
        elif event_type == 'match_scheduled':
            self._notify_match_scheduled(kwargs.get('match'))
        elif event_type == 'match_result':
            self._notify_match_result(kwargs.get('match'))
        elif event_type == 'registration_needs_approval':
            self._notify_registration_needs_approval(kwargs.get('tournament'), kwargs.get('player'))
    
    
    def _notify_tournament_status_change(self, tournament):
        """Notify relevant users about tournament status changes"""
        if not tournament:
            return
            
        subject = f"Tournament Update: {tournament.name}"
        context = {
            'tournament': tournament,
            'new_status': tournament.get_status_display()
        }
        
        # Email organizer
        if tournament.organizer and tournament.organizer.email:
            organizer_message = render_to_string('emails/tournament_status_change_organizer.txt', context)
            self._send_email(subject, organizer_message, [tournament.organizer.email])
        
        # Email participants
        participant_emails = list(tournament.participants.values_list('email', flat=True))
        if participant_emails:
            participant_message = render_to_string('emails/tournament_status_change_participant.txt', context)
            self._send_email(subject, participant_message, participant_emails)
    
    def _notify_tournament_created(self, tournament):
        """Notify admin users about new tournament creation"""
        if not tournament:
            return
            
        subject = f"New Tournament Created: {tournament.name}"
        context = {
            'tournament': tournament,
            'organizer': tournament.organizer.get_full_name() if tournament.organizer else "Unknown"
        }
        
        # Email to admin users
        from apps.accounts.models import User
        admin_emails = User.objects.filter(user_type='ADMIN').values_list('email', flat=True)
        if admin_emails:
            message = render_to_string('emails/tournament_created.txt', context)
            self._send_email(subject, message, list(admin_emails))
    
    def _notify_player_registered(self, tournament, player):
        """Notify player and organizer about registration"""
        if not tournament or not player:
            return
            
        # Email player confirmation
        subject = f"Registration Confirmation: {tournament.name}"
        context = {
            'tournament': tournament,
            'player': player
        }
        
        if player.email:
            player_message = render_to_string('emails/player_registration_confirmation.txt', context)
            self._send_email(subject, player_message, [player.email])
        
        # Email organizer about new registration
        if tournament.organizer and tournament.organizer.email:
            organizer_subject = f"New Player Registration: {tournament.name}"
            organizer_message = render_to_string('emails/player_registration_organizer.txt', context)
            self._send_email(organizer_subject, organizer_message, [tournament.organizer.email])
    
    def _notify_match_scheduled(self, match):
        """Notify players and referee about scheduled match"""
        if not match:
            return
            
        subject = f"Match Scheduled: {match.tournament.name}"
        context = {
            'match': match,
            'tournament': match.tournament
        }
        
        # Email players
        player_emails = []
        if match.player1 and match.player1.email:
            player_emails.append(match.player1.email)
        if match.player2 and match.player2.email:
            player_emails.append(match.player2.email)
            
        if player_emails:
            player_message = render_to_string('emails/match_scheduled_players.txt', context)
            self._send_email(subject, player_message, player_emails)
        
        # Email referee if assigned
        if match.referee and match.referee.user and match.referee.user.email:
            referee_message = render_to_string('emails/match_scheduled_referee.txt', context)
            self._send_email(subject, referee_message, [match.referee.user.email])
    
    def _notify_match_result(self, match):
        """Notify about match results"""
        if not match or not hasattr(match, 'score') or not match.score:
            return
            
        if match.score.winner:
            subject = f"Match Result: {match.tournament.name}"
            context = {
                'match': match,
                'tournament': match.tournament,
                'winner': match.score.winner,
                'score': match.score
            }
            
            # Email to players
            if match.player1 and match.player1.email:
                context['is_winner'] = (match.score.winner == match.player1)
                player1_message = render_to_string('emails/match_result_player.txt', context)
                self._send_email(subject, player1_message, [match.player1.email])
                
            if match.player2 and match.player2.email:
                context['is_winner'] = (match.score.winner == match.player2)
                player2_message = render_to_string('emails/match_result_player.txt', context)
                self._send_email(subject, player2_message, [match.player2.email])
            
            # Email tournament organizer
            if match.tournament.organizer and match.tournament.organizer.email:
                organizer_message = render_to_string('emails/match_result_organizer.txt', context)
                self._send_email(subject, organizer_message, [match.tournament.organizer.email])
    
    def _send_email(self, subject, message, recipient_list):
        """Helper method to send email"""
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                fail_silently=True,
            )
        except Exception as e:
            # Log the error but don't crash the application
            import logging
            logging.error(f"Failed to send email notification: {str(e)}")

    def _notify_registration_needs_approval(self, tournament, player):
        """Notify organizer about a registration that needs approval"""
        if not tournament or not player or not tournament.organizer:
            return
            
        subject = f"Action Required: Registration Approval for {tournament.name}"
        context = {
            'tournament': tournament,
            'player': player,
            'approval_url': f"{settings.SITE_URL}/tournaments/{tournament.id}/registrations/"
        }
        
        if tournament.organizer.email:
            message = render_to_string('emails/registration_approval_request.txt', context)
            self._send_email(subject, message, [tournament.organizer.email])


class DatabaseNotifier(Observer):
    """Stores notifications in the database for in-app notifications"""
    
    def update(self, subject, **kwargs):
        """Store notification in database"""
        event_type = kwargs.get('event_type')
        
        # Import here to avoid circular imports
        from apps.notifications.models import Notification
        
        if event_type == 'tournament_status_change':
            tournament = kwargs.get('tournament')
            if tournament:
                # Create notification for organizer
                if tournament.organizer:
                    Notification.objects.create(
                        user=tournament.organizer,
                        message=f"Tournament '{tournament.name}' status changed to {tournament.get_status_display()}",
                        notification_type='TOURNAMENT',
                        related_id=tournament.id
                    )
                
                # Create notifications for participants
                for player in tournament.participants.all():
                    Notification.objects.create(
                        user=player,
                        message=f"Tournament '{tournament.name}' status changed to {tournament.get_status_display()}",
                        notification_type='TOURNAMENT',
                        related_id=tournament.id
                    )
        
        elif event_type == 'player_registered':
            tournament = kwargs.get('tournament')
            player = kwargs.get('player')
            
            if tournament and player:
                # Notify the player who registered
                Notification.objects.create(
                    user=player,
                    message=f"You have successfully registered for tournament '{tournament.name}'",
                    notification_type='TOURNAMENT',
                    related_id=tournament.id
                )
                
                # Notify the organizer
                if tournament.organizer:
                    Notification.objects.create(
                        user=tournament.organizer,
                        message=f"{player.get_full_name()} has registered for tournament '{tournament.name}'",
                        notification_type='TOURNAMENT',
                        related_id=tournament.id
                    )
        
        elif event_type == 'match_scheduled':
            match = kwargs.get('match')
            if match:
                # Notify players
                if match.player1:
                    Notification.objects.create(
                        user=match.player1,
                        message=f"You have a match scheduled in '{match.tournament.name}'",
                        notification_type='MATCH',
                        related_id=match.id
                    )
                
                if match.player2:
                    Notification.objects.create(
                        user=match.player2,
                        message=f"You have a match scheduled in '{match.tournament.name}'",
                        notification_type='MATCH',
                        related_id=match.id
                    )
                
                # Notify referee
                if match.referee and match.referee.user:
                    Notification.objects.create(
                        user=match.referee.user,
                        message=f"You are assigned to referee a match in '{match.tournament.name}'",
                        notification_type='MATCH',
                        related_id=match.id
                    )
        
        elif event_type == 'match_result':
            match = kwargs.get('match')
            if match and hasattr(match, 'score') and match.score and match.score.winner:
                winner = match.score.winner
                loser = match.player2 if winner == match.player1 else match.player1
                
                # Notify winner
                Notification.objects.create(
                    user=winner,
                    message=f"Congratulations! You won your match in '{match.tournament.name}'",
                    notification_type='MATCH',
                    related_id=match.id
                )
                
                # Notify loser
                if loser:
                    Notification.objects.create(
                        user=loser,
                        message=f"Match result: You were defeated in '{match.tournament.name}'",
                        notification_type='MATCH',
                        related_id=match.id
                    )
        
        elif event_type == 'registration_needs_approval':
            tournament = kwargs.get('tournament')
            player = kwargs.get('player')
            
            if tournament and player and tournament.organizer:
                # Create notification for the organizer
                Notification.objects.create(
                    user=tournament.organizer,
                    message=f"ACTION REQUIRED: {player.get_full_name()} has requested to join '{tournament.name}'",
                    notification_type='REGISTRATION_APPROVAL',
                    related_id=tournament.id,
                    is_read=False,
                    requires_action=True
                )
                
                # Create a "pending approval" notification for the player
                Notification.objects.create(
                    user=player,
                    message=f"Your registration for '{tournament.name}' is pending approval",
                    notification_type='TOURNAMENT',
                    related_id=tournament.id
                )