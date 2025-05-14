from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import TennisPlayer, Referee
from apps.tournaments.models import Tournament
from apps.matches.models import Match, MatchScore

User = get_user_model()

class MatchModelTest(TestCase):
    def setUp(self):
        # Create users
        self.player1 = User.objects.create_user(
            username='player1',
            email='player1@example.com',
            password='testpass',
            first_name='Player',
            last_name='One'
        )
        self.player2 = User.objects.create_user(
            username='player2',
            email='player2@example.com',
            password='testpass',
            first_name='Player',
            last_name='Two'
        )
        
        self.referee_user = User.objects.create_user(
            username='referee',
            email='referee@example.com',
            password='testpass'
        )
        
        self.referee = Referee.objects.create(
            user=self.referee_user,
            certification_level='NAT'
        )
        
        self.organizer = User.objects.create_user(
            username='organizer',
            email='organizer@example.com',
            password='testpass'
        )
        
        # Create tournament
        self.tournament = Tournament.objects.create(
            name='Test Tournament',
            organizer=self.organizer,
            location='Test Location',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=5),
            registration_deadline=timezone.now().date() - timedelta(days=1),
            max_participants=32,
            tournament_type='SE',
            status='IN_PROGRESS'
        )
        
        # Create match
        self.match = Match.objects.create(
            tournament=self.tournament,
            player1=self.player1,
            player2=self.player2,
            referee=self.referee,
            round_number=1,
            status='SCHEDULED',
            scheduled_time=timezone.now() + timedelta(hours=2),
            court_number=1
        )
        
    def test_match_creation(self):
        self.assertEqual(self.match.tournament, self.tournament)
        self.assertEqual(self.match.player1, self.player1)
        self.assertEqual(self.match.player2, self.player2)
        self.assertEqual(self.match.referee, self.referee)
        self.assertEqual(self.match.round_number, 1)
        self.assertEqual(self.match.status, 'SCHEDULED')
        self.assertEqual(self.match.court_number, 1)
        
    def test_match_status_properties(self):
        self.assertTrue(self.match.is_scheduled)
        self.assertFalse(self.match.is_in_progress)
        self.assertFalse(self.match.is_completed)
        
        self.match.status = 'IN_PROGRESS'
        self.match.save()
        self.assertFalse(self.match.is_scheduled)
        self.assertTrue(self.match.is_in_progress)
        self.assertFalse(self.match.is_completed)
        
        self.match.status = 'COMPLETED'
        self.match.save()
        self.assertFalse(self.match.is_scheduled)
        self.assertFalse(self.match.is_in_progress)
        self.assertTrue(self.match.is_completed)
        
    def test_get_winner_no_score(self):
        self.assertIsNone(self.match.get_winner())
        
    def test_get_winner_with_score(self):
        # Create score with player1 winning
        MatchScore.objects.create(
            match=self.match,
            player1_set1=6, player2_set1=3,
            player1_set2=6, player2_set2=4
        )
        
        self.match.status = 'COMPLETED'
        self.match.save()
        
        self.assertEqual(self.match.get_winner(), self.player1)

class MatchScoreModelTest(TestCase):
    def setUp(self):
        # Create users
        self.player1 = User.objects.create_user(username='player1', password='testpass')
        self.player2 = User.objects.create_user(username='player2', password='testpass')
        
        # Create tournament
        self.organizer = User.objects.create_user(username='organizer', password='testpass')
        self.tournament = Tournament.objects.create(
            name='Test Tournament',
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
            round_number=1,
            status='COMPLETED'
        )
        
        # Create score
        self.score = MatchScore.objects.create(
            match=self.match,
            player1_set1=6, player2_set1=4,
            player1_set2=6, player2_set2=2
        )
        
    def test_score_creation(self):
        self.assertEqual(self.score.match, self.match)
        self.assertEqual(self.score.player1_set1, 6)
        self.assertEqual(self.score.player2_set1, 4)
        self.assertEqual(self.score.player1_set2, 6)
        self.assertEqual(self.score.player2_set2, 2)
        
    def test_get_winner(self):
        self.assertEqual(self.score.get_winner(), self.player1)
        
        # Change score so player2 wins
        self.score.player1_set1 = 4
        self.score.player2_set1 = 6
        self.score.player1_set2 = 2
        self.score.player2_set2 = 6
        self.score.save()
        
        self.assertEqual(self.score.get_winner(), self.player2)

class MatchViewsTest(TestCase):
    def setUp(self):
        # Create users
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com',
            password='testpass'
        )
        
        self.player1 = User.objects.create_user(username='player1', password='testpass')
        self.player2 = User.objects.create_user(username='player2', password='testpass')
        
        self.referee_user = User.objects.create_user(username='referee', password='testpass')
        self.referee = Referee.objects.create(user=self.referee_user)
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass',
            is_staff=True
        )
        
        # Create tournament
        self.organizer = User.objects.create_user(username='organizer', password='testpass')
        self.tournament = Tournament.objects.create(
            name='Test Tournament',
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
            status='SCHEDULED',
            scheduled_time=timezone.now() + timedelta(hours=2)
        )
        
    def test_match_list_view(self):
        response = self.client.get(reverse('matches:match_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'matches/match_list.html')
        
    def test_match_detail_view(self):
        response = self.client.get(reverse('matches:match_detail', args=[self.match.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'matches/match_detail.html')
        
    def test_submit_score_referee_authorized(self):
        self.client.login(username='referee', password='testpass')
        
        data = {
            'player1_set1': 6, 'player2_set1': 3,
            'player1_set2': 6, 'player2_set2': 4
        }
        
        self.match.status = 'IN_PROGRESS'
        self.match.save()
        
        response = self.client.post(
            reverse('matches:submit_score', args=[self.match.id]),
            data
        )
        
        # Check redirect after successful score submission
        self.assertEqual(response.status_code, 302)
        
        # Verify score was created
        self.assertTrue(MatchScore.objects.filter(match=self.match).exists())
        
        # Verify match status updated to completed
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, 'COMPLETED')
