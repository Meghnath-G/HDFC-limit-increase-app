"""
URL configuration for Authentication app
"""
from django.urls import path
from . import views
from . import otp_auth_views

app_name = 'authentication'

urlpatterns = [
    # Traditional authentication endpoints
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('refresh/', views.refresh_token_view, name='refresh_token'),
    
    # OTP-based authentication endpoints
    path('phone-login/request/', otp_auth_views.phone_login_request, name='phone_login_request'),
    path('phone-login/verify/', otp_auth_views.phone_login_verify, name='phone_login_verify'),
    path('phone-register/request/', otp_auth_views.phone_register_request, name='phone_register_request'),
    path('phone-register/verify/', otp_auth_views.phone_register_verify, name='phone_register_verify'),
    
    # Common endpoints
    path('status/', otp_auth_views.auth_status, name='auth_status'),
    path('logout/', otp_auth_views.logout, name='otp_logout'),
]