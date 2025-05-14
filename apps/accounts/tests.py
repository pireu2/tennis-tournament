from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.accounts.models import TennisPlayer, Referee

User = get_user_model()

class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testplayer',
            email='testplayer@example.com',
            password='testpassword',
            first_name='Test',
            last_name='Player'
        )
        
    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testplayer')
        self.assertEqual(self.user.email, 'testplayer@example.com')
        self.assertEqual(self.user.get_full_name(), 'Test Player')
        
    def test_is_admin_method(self):
        self.assertFalse(self.user.is_admin())
        self.user.is_staff = True
        self.user.save()
        self.assertTrue(self.user.is_admin())

class TennisPlayerModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='playeruser',
            email='player@example.com',
            password='playerpass'
        )
        self.player = TennisPlayer.objects.create(
            user=self.user,
            ranking=100,
            gender='M',
            skill_level='INT'
        )
        
    def test_player_creation(self):
        self.assertEqual(self.player.user.username, 'playeruser')
        self.assertEqual(self.player.ranking, 100)
        self.assertEqual(self.player.gender, 'M')
        self.assertEqual(self.player.skill_level, 'INT')
        
    def test_player_str_method(self):
        expected_str = f"Player: {self.user.username}"
        self.assertEqual(str(self.player), expected_str)

class RefereeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='refuser',
            email='ref@example.com',
            password='refpass'
        )
        self.referee = Referee.objects.create(
            user=self.user,
            certification_level='NAT'
        )
        
    def test_referee_creation(self):
        self.assertEqual(self.referee.user.username, 'refuser')
        self.assertEqual(self.referee.certification_level, 'NAT')
        
    def test_referee_str_method(self):
        expected_str = f"Referee: {self.user.username}"
        self.assertEqual(str(self.referee), expected_str)

class ProfileViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='profileuser',
            email='profile@example.com',
            password='profilepass'
        )
        self.player = TennisPlayer.objects.create(
            user=self.user,
            ranking=200,
            gender='F',
            skill_level='BEG'
        )
        
    def test_profile_view_authenticated(self):
        self.client.login(username='profileuser', password='profilepass')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')
        
    def test_profile_view_unauthenticated(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('accounts:profile')}")

class RegisterViewTest(TestCase):
    def test_register_view_get(self):
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')
        
    def test_register_view_post_player(self):
        data = {
            'username': 'newplayer',
            'email': 'newplayer@example.com',
            'password1': 'complex-password123',
            'password2': 'complex-password123',
            'first_name': 'New',
            'last_name': 'Player',
            'user_type': 'PLAYER',
            'ranking': 300,
            'gender': 'M',
            'skill_level': 'ADV'
        }
        response = self.client.post(reverse('accounts:register'), data)
        self.assertRedirects(response, reverse('accounts:login'))
        self.assertTrue(User.objects.filter(username='newplayer').exists())
        self.assertTrue(TennisPlayer.objects.filter(user__username='newplayer').exists())
