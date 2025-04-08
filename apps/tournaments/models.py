from django.db import models
from apps.accounts.models import User
from django.utils import timezone

class Tournament(models.Model):
    STATUS_CHOICES = [
        ('UPCOMING', 'Upcoming'),
        ('REGISTRATION', 'Registration Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELED', 'Canceled')
    ]
    
    name = models.CharField(max_length=100, blank=False, null=False)
    start_date = models.DateField(blank=False, null=False)
    end_date = models.DateField(blank=False, null=False)
    location = models.CharField(max_length=100, blank=False, null=False)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tournaments', null=False)
    participants = models.ManyToManyField(User, related_name='tournaments_participated', blank=True)
    
    registration_deadline = models.DateField(null=True, blank=True)
    max_participants = models.PositiveIntegerField(default=32)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UPCOMING')
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} - {self.start_date} to {self.end_date}'
    
    def is_registration_open(self):
        if self.status != 'REGISTRATION':
            return False
        if self.registration_deadline:
            return timezone.now().date() <= self.registration_deadline
        return True
        
    def can_generate_matches(self):
        """Check if conditions are met to generate tournament matches"""
        return (self.status == 'REGISTRATION' and 
                self.participants.count() >= 2 and 
                (not self.registration_deadline or timezone.now().date() > self.registration_deadline))