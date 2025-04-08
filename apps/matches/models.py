from django.db import models
from apps.accounts.models import User, Referee
from apps.tournaments.models import Tournament

class Match(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELED', 'Canceled')
    ]
    
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    player1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_as_player1')
    player2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_as_player2')
    referee = models.ForeignKey(Referee, on_delete=models.SET_NULL, null=True, blank=True, related_name='officiated_matches')
    
    round_number = models.PositiveIntegerField()
    court_number = models.PositiveIntegerField(null=True, blank=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.player1.username} vs {self.player2.username} - Round {self.round_number}"
    
    class Meta:
        verbose_name_plural = "Matches"
    
    # Helper methods for score access
    def get_player1_set1(self):
        if hasattr(self, 'score') and self.score:
            return self.score.player1_set1
        return None
    
    def get_player1_set2(self):
        if hasattr(self, 'score') and self.score:
            return self.score.player1_set2
        return None
    
    def get_player1_set3(self):
        if hasattr(self, 'score') and self.score:
            return self.score.player1_set3
        return None
    
    def get_player1_set4(self):
        if hasattr(self, 'score') and self.score:
            return self.score.player1_set4
        return None
    
    def get_player1_set5(self):
        if hasattr(self, 'score') and self.score:
            return self.score.player1_set5
        return None
    
    def get_player2_set1(self):
        if hasattr(self, 'score') and self.score:
            return self.score.player2_set1
        return None
    
    def get_player2_set2(self):
        if hasattr(self, 'score') and self.score:
            return self.score.player2_set2
        return None
    
    def get_player2_set3(self):
        if hasattr(self, 'score') and self.score:
            return self.score.player2_set3
        return None
    
    def get_player2_set4(self):
        if hasattr(self, 'score') and self.score:
            return self.score.player2_set4
        return None
    
    def get_player2_set5(self):
        if hasattr(self, 'score') and self.score:
            return self.score.player2_set5
        return None
    
    def get_winner(self):
        if hasattr(self, 'score') and self.score:
            return self.score.winner
        return None
    
    def is_completed(self):
        return self.status == 'COMPLETED'
    
    def is_in_progress(self):
        return self.status == 'IN_PROGRESS'
    
    def is_scheduled(self):
        return self.status == 'SCHEDULED'
    
    def is_canceled(self):
        return self.status == 'CANCELED'

class MatchScore(models.Model):
    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name='score')
    
    # Tennis matches typically have up to 5 sets
    player1_set1 = models.PositiveIntegerField(null=True, blank=True)
    player2_set1 = models.PositiveIntegerField(null=True, blank=True)
    
    player1_set2 = models.PositiveIntegerField(null=True, blank=True)
    player2_set2 = models.PositiveIntegerField(null=True, blank=True)
    
    player1_set3 = models.PositiveIntegerField(null=True, blank=True)
    player2_set3 = models.PositiveIntegerField(null=True, blank=True)
    
    player1_set4 = models.PositiveIntegerField(null=True, blank=True)
    player2_set4 = models.PositiveIntegerField(null=True, blank=True)
    
    player1_set5 = models.PositiveIntegerField(null=True, blank=True)
    player2_set5 = models.PositiveIntegerField(null=True, blank=True)
    
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='matches_won')
    
    def __str__(self):
        result = []
        for i in range(1, 6):
            p1_score = getattr(self, f'player1_set{i}')
            p2_score = getattr(self, f'player2_set{i}')
            if p1_score is not None and p2_score is not None:
                result.append(f"{p1_score}-{p2_score}")
        return " ".join(result)
    
    def get_player1_sets_won(self):
        """Count sets won by player 1"""
        sets_won = 0
        for i in range(1, 6):
            p1_score = getattr(self, f'player1_set{i}')
            p2_score = getattr(self, f'player2_set{i}')
            if p1_score is not None and p2_score is not None and p1_score > p2_score:
                sets_won += 1
        return sets_won
    
    def get_player2_sets_won(self):
        """Count sets won by player 2"""
        sets_won = 0
        for i in range(1, 6):
            p1_score = getattr(self, f'player1_set{i}')
            p2_score = getattr(self, f'player2_set{i}')
            if p1_score is not None and p2_score is not None and p2_score > p1_score:
                sets_won += 1
        return sets_won
    
    def determine_winner(self):
        """Determine the winner based on sets won"""
        player1_sets = self.get_player1_sets_won()
        player2_sets = self.get_player2_sets_won()
        
        if player1_sets > player2_sets:
            return self.match.player1
        elif player2_sets > player1_sets:
            return self.match.player2
        return None