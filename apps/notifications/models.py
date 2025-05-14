from django.db import models
from apps.accounts.models import User

class Notification(models.Model):
    """Model for storing user notifications"""
    NOTIFICATION_TYPES = [
        ('TOURNAMENT', 'Tournament'),
        ('MATCH', 'Match'),
        ('REGISTRATION_APPROVAL', 'Registration Approval'),
        ('SYSTEM', 'System'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    related_id = models.IntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    requires_action = models.BooleanField(default=False)
    
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} notification for {self.user.username}"