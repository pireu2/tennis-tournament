from django import forms
from .models import Tournament
from django.core.exceptions import ValidationError

class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = [
            'name', 'location', 'start_date', 'end_date', 
            'registration_deadline', 'max_participants', 
            'status', 'tournament_type', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'registration_deadline': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control', 'min': '2'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'tournament_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.DateInput):
                field.widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        registration_deadline = cleaned_data.get('registration_deadline')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError("End date cannot be before start date.")
        
        if registration_deadline and start_date and registration_deadline > start_date:
            raise ValidationError("Registration deadline must be before tournament start date.")
        
        return cleaned_data