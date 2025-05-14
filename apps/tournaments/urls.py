from django.urls import path
from . import views

app_name = 'tournaments'

urlpatterns = [
    path('', views.TournamentListView.as_view(), name='tournament_list'),
    path('create/', views.TournamentCreateView.as_view(), name='tournament_create'),
    path('<int:pk>/', views.TournamentDetailView.as_view(), name='tournament_detail'),
    path('<int:pk>/edit/', views.TournamentUpdateView.as_view(), name='tournament_edit'),
    path('<int:pk>/register/', views.PlayerRegistrationView.as_view(), name='tournament_register'),
    path('<int:pk>/generate-matches/', views.GenerateMatchesView.as_view(), name='generate_matches'),
    path('<int:tournament_id>/matches/', views.TournamentMatchesView.as_view(), name='tournament_matches'),
    path('<int:pk>/approve-registration/', views.ApproveRegistrationView.as_view(), name='approve_registration'),
]