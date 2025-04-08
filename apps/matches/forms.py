from django import forms
from .models import MatchScore

class MatchScoreForm(forms.ModelForm):
    class Meta:
        model = MatchScore
        fields = [
            'player1_set1', 'player2_set1',
            'player1_set2', 'player2_set2',
            'player1_set3', 'player2_set3',
            'player1_set4', 'player2_set4',
            'player1_set5', 'player2_set5'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})