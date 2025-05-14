from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import TennisPlayer
from apps.tournaments.models import Tournament, Registration

User = get_user_model()

class TournamentModelTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username='organizer',
            email='organizer@example.com',
            password='testpass'
        )
        self.tournament = Tournament.objects.create(
            name='Test Tournament',
            organizer=self.organizer,
            location='Test Location',
            start_date=timezone.now().date() + timedelta(days=10),
            end_date=timezone.now().date() + timedelta(days=15),
            registration_deadline=timezone.now().date() + timedelta(days=5),
            max_participants=32,
            tournament_type='SE',  # Single Elimination
            status='REGISTRATION'
        )
        
    def test_tournament_creation(self):
        self.assertEqual(self.tournament.name, 'Test Tournament')
        self.assertEqual(self.tournament.organizer, self.organizer)
        self.assertEqual(self.tournament.max_participants, 32)
        self.assertEqual(self.tournament.tournament_type, 'SE')
        self.assertEqual(self.tournament.status, 'REGISTRATION')
        
    def test_tournament_str_method(self):
        expected_str = 'Test Tournament'
        self.assertEqual(str(self.tournament), expected_str)
        
    def test_is_registration_open_method(self):
        self.assertTrue(self.tournament.is_registration_open())
        
        # Test with past deadline
        self.tournament.registration_deadline = timezone.now().date() - timedelta(days=1)
        self.tournament.save()
        self.assertFalse(self.tournament.is_registration_open())
        
        # Test with different status
        self.tournament.registration_deadline = timezone.now().date() + timedelta(days=5)
        self.tournament.status = 'IN_PROGRESS'
        self.tournament.save()
        self.assertFalse(self.tournament.is_registration_open())

class RegistrationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testplayer',
            email='testplayer@example.com',
            password='testpass'
        )
        self.player = TennisPlayer.objects.create(
            user=self.user,
            ranking=100,
            gender='M',
            skill_level='INT'
        )
        
        self.organizer = User.objects.create_user(
            username='organizer',
            email='organizer@example.com',
            password='testpass'
        )
        
        self.tournament = Tournament.objects.create(
            name='Test Tournament',
            organizer=self.organizer,
            location='Test Location',
            start_date=timezone.now().date() + timedelta(days=10),
            end_date=timezone.now().date() + timedelta(days=15),
            registration_deadline=timezone.now().date() + timedelta(days=5),
            max_participants=32,
            tournament_type='SE',
            status='REGISTRATION'
        )
        
        self.registration = Registration.objects.create(
            tournament=self.tournament,
            player=self.user,
            status='PENDING'
        )
        
    def test_registration_creation(self):
        self.assertEqual(self.registration.tournament, self.tournament)
        self.assertEqual(self.registration.player, self.user)
        self.assertEqual(self.registration.status, 'PENDING')
        
    def test_registration_str_method(self):
        expected_str = f"{self.user.get_full_name()} - {self.tournament.name}"
        self.assertEqual(str(self.registration), expected_str)

class TournamentViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass'
        )
        
        self.organizer = User.objects.create_user(
            username='organizer',
            email='organizer@example.com',
            password='testpass'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass',
            is_staff=True
        )
        
        self.tournament = Tournament.objects.create(
            name='Test Tournament',
            organizer=self.organizer,
            location='Test Location',
            start_date=timezone.now().date() + timedelta(days=10),
            end_date=timezone.now().date() + timedelta(days=15),
            registration_deadline=timezone.now().date() + timedelta(days=5),
            max_participants=32,
            tournament_type='SE',
            status='REGISTRATION'
        )
        
    def test_tournament_list_view(self):
        response = self.client.get(reverse('tournaments:tournament_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tournaments/tournament_list.html')
        self.assertContains(response, 'Test Tournament')
        
    def test_tournament_detail_view(self):
        response = self.client.get(reverse('tournaments:tournament_detail', args=[self.tournament.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tournaments/tournament_detail.html')
        self.assertContains(response, 'Test Tournament')
        
    def test_create_tournament_view_authenticated(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('tournaments:create_tournament'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tournaments/tournament_form.html')
        
    def test_create_tournament_view_unauthenticated(self):
        response = self.client.get(reverse('tournaments:create_tournament'))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('tournaments:create_tournament')}")
        
    def test_tournament_registration_authenticated(self):
        self.client.login(username='testuser', password='testpass')
        TennisPlayer.objects.create(user=self.user)
        
        response = self.client.post(reverse('tournaments:register_tournament', args=[self.tournament.id]))
        self.assertEqual(response.status_code, 302)  # Redirect after successful registration
        self.assertTrue(Registration.objects.filter(tournament=self.tournament, player=self.user).exists())
