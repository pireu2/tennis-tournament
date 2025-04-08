from django.db import models
from apps.accounts.models import User

class Tournament(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)
    start_Date = models.DateField(blank=False, null=False)
    end_Date = models.DateField(blank=False, null=False)
    location = models.CharField(max_length=100, blank=False, null=False)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tournaments', null=False)
    participants = models.ManyToManyField(User, related_name='tournaments_participated', blank=True)

    def __str__(self):
        return f'{self.name} - {self.start_Date} to {self.end_Date}'