from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import TennisPlayer, Referee
from apps.tournaments.models import Tournament, Registration
from apps.matches.models import Match, MatchScore

User = get_user_model()

class TournamentRegistrationFlowTest(TestCase):
    def setUp(self):
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass',
            is_staff=True
        )
        
        # Create player
        self.player_user = User.objects.create_user(
            username='player',
            email='player@example.com',
            password='playerpass',
            first_name='Test',
            last_name='Player'
        )
        self.player = TennisPlayer.objects.create(
            user=self.player_user,
            ranking=100,
            gender='M',
            skill_level='INT'
        )
        
        # Create tournament organizer
        self.organizer = User.objects.create_user(
            username='organizer',
            email='organizer@example.com',
            password='organizerpass'
        )
        
        # Create tournament
        self.tournament = Tournament.objects.create(
            name='Integration Test Tournament',
            organizer=self.organizer,
            location='Test Venue',
            start_date=timezone.now().date() + timedelta(days=10),
            end_date=timezone.now().date() + timedelta(days=15),
            registration_deadline=timezone.now().date() + timedelta(days=5),
            max_participants=32,
            tournament_type='SE',
            status='REGISTRATION'
        )
        
        self.client = Client()
        
    def test_tournament_registration_flow(self):
        # 1. Player logs in and registers for tournament
        self.client.login(username='player', password='playerpass')
        
        response = self.client.post(
            reverse('tournaments:register_tournament', args=[self.tournament.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirect after successful registration
        
        # Verify registration was created
        registration = Registration.objects.get(
            tournament=self.tournament, 
            player=self.player_user
        )
        self.assertEqual(registration.status, 'PENDING')
        
        # 2. Organizer logs in and approves the registration
        self.client.logout()
        self.client.login(username='organizer', password='organizerpass')
        
        response = self.client.post(
            reverse('tournaments:approve_registration', args=[self.tournament.id]),
            {
                'player_id': self.player_user.id,
                'action': 'approve'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after successful approval
        
        # Verify registration status was updated
        registration.refresh_from_db()
        self.assertEqual(registration.status, 'APPROVED')
        
        # 3. Organizer starts the tournament
        response = self.client.post(
            reverse('tournaments:update_status', args=[self.tournament.id]),
            {'new_status': 'IN_PROGRESS'}
        )
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        
        # Verify tournament status was updated
        self.tournament.refresh_from_db()
        self.assertEqual(self.tournament.status, 'IN_PROGRESS')
        
        # 4. Verify matches were created automatically
        matches = Match.objects.filter(tournament=self.tournament)
        self.assertTrue(matches.exists())

class MatchScoringFlowTest(TestCase):
    def setUp(self):
        # Create players
        self.player1 = User.objects.create_user(
            username='player1',
            email='player1@example.com',
            password='playerpass',
            first_name='Player',
            last_name='One'
        )
        self.tennis_player1 = TennisPlayer.objects.create(
            user=self.player1,
            ranking=100
        )
        
        self.player2 = User.objects.create_user(
            username='player2',
            email='player2@example.com',
            password='playerpass',
            first_name='Player',
            last_name='Two'
        )
        self.tennis_player2 = TennisPlayer.objects.create(
            user=self.player2,
            ranking=200
        )
        
        # Create referee
        self.referee_user = User.objects.create_user(
            username='referee',
            email='referee@example.com',
            password='refereepass',
            first_name='Test',
            last_name='Referee'
        )
        self.referee = Referee.objects.create(
            user=self.referee_user,
            certification_level='NAT'
        )
        
        # Create tournament
        self.organizer = User.objects.create_user(
            username='organizer',
            email='organizer@example.com',
            password='organizerpass'
        )
        
        self.tournament = Tournament.objects.create(
            name='Match Scoring Test Tournament',
            organizer=self.organizer,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=5),
            status='IN_PROGRESS'
        )
        
        # Create match
        self.match = Match.objects.create(
            tournament=self.tournament,
            player1=self.player1,
            player2=self.player2,
            referee=self.referee,
            round_number=1,
            status='IN_PROGRESS',
            court_number=1
        )
        
        self.client = Client()
        
    def test_match_scoring_flow(self):
        # 1. Referee logs in
        self.client.login(username='referee', password='refereepass')
        
        # 2. Referee submits score
        score_data = {
            'player1_set1': 6, 'player2_set1': 3,
            'player1_set2': 6, 'player2_set2': 4
        }
        
        response = self.client.post(
            reverse('matches:submit_score', args=[self.match.id]),
            score_data
        )
        self.assertEqual(response.status_code, 302)  # Redirect after successful submission
        
        # 3. Verify match score was recorded
        match_score = MatchScore.objects.get(match=self.match)
        self.assertEqual(match_score.player1_set1, 6)
        self.assertEqual(match_score.player2_set1, 3)
        self.assertEqual(match_score.player1_set2, 6)
        self.assertEqual(match_score.player2_set2, 4)
        
        # 4. Verify match status was updated to completed
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, 'COMPLETED')
        
        # 5. Verify winner was correctly determined
        winner = self.match.get_winner()
        self.assertEqual(winner, self.player1)
