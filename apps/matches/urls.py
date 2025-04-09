from django.urls import path
from . import views

app_name = 'matches'

urlpatterns = [
    path('', views.MatchListView.as_view(), name='list'),
    path('', views.MatchListView.as_view(), name='match_list'),
    path('<int:pk>/', views.MatchDetailView.as_view(), name='match_detail'),
    path('<int:pk>/referee-signup/', views.RefereeSignupView.as_view(), name='referee_signup'),
    path('<int:pk>/update-score/', views.UpdateScoreView.as_view(), name='update_score'),
    path('export/csv/', views.export_matches_csv, name='export_csv'),
    path('export/txt/', views.export_matches_txt, name='export_txt'),
]