from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    USER_TYPES = (
        ('PLAYER', 'Tennis Player'),
        ('REFEREE', 'Referee'),
        ('ADMIN', 'Admin'),
    )

    user_type = models.CharField(max_length=10, choices=USER_TYPES, null=False, blank=False)

    def is_player(self):
        return self.user_type == 'PLAYER'
    def is_referee(self):
        return self.user_type == 'REFEREE'
    def is_admin(self):
        return self.user_type == 'ADMIN'

class TennisPlayer(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tennis_player', primary_key=True)
    ranking = models.IntegerField(default=0)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='O')
    date_of_birth = models.DateField(null=True, blank=True)
    tournaments = models.ManyToManyField('tournaments.Tournament') 

    def __str__(self):
        return f'{self.user.username} - Ranking: {self.ranking}'

class Referee(models.Model):
    CERTIFICATION_CHOICES = [
        ('BRONZE', 'Bronze Level'),
        ('SILVER', 'Silver Level'),
        ('GOLD', 'Gold Level'),
        ('PLATINUM', 'Platinum Level'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='referee', primary_key=True)
    tournaments = models.ManyToManyField('tournaments.Tournament', related_name='referees', blank=True)  # Updated
    certification_level = models.CharField(
        max_length=10, 
        choices=CERTIFICATION_CHOICES,
        default='BRONZE'
    )
    

    def __str__(self):
        return f'{self.user.username} - Referee'