from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('register/player/', views.PlayerRegistrationView.as_view(), name='register_player'),
    path('register/referee/', views.RefereeRegistrationView.as_view(), name='register_referee'),
    path('register/admin/', views.AdminRegistrationView.as_view(), name='register_admin'),
    path('login/', views.UserLogInView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.UserUpdateView.as_view(), name='edit_profile'),
    path('profile/change-password/', views.CustomPasswordChangeView.as_view(), name='change_password'),
    path('admin/users/', views.UserListView.as_view(), name='admin_user_list'),
    path('admin/users/<int:pk>/', views.UserDetailView.as_view(), name='admin_user_detail'),
    path('admin/users/<int:pk>/edit/', views.AdminEditUserView.as_view(), name='admin_edit_user'),
]