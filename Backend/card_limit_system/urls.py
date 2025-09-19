"""
URL configuration for Card Limit Increase System project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API endpoints v1
    path('api/v1/auth/', include('card_limit_system.apps.authentication.urls')),
    path('api/v1/customers/', include('card_limit_system.apps.customers.urls')),
    path('api/v1/requests/', include('card_limit_system.apps.requests.urls')),
    path('api/v1/otp/', include('card_limit_system.apps.otp.urls')),
    path('api/v1/notifications/', include('card_limit_system.apps.notifications.urls')),
]

# Add API versioning for future releases
api_v1_patterns = [
    path('auth/', include('card_limit_system.apps.authentication.urls')),
    path('customers/', include('card_limit_system.apps.customers.urls')),
    path('requests/', include('card_limit_system.apps.requests.urls')),
    path('otp/', include('card_limit_system.apps.otp.urls')),
    path('notifications/', include('card_limit_system.apps.notifications.urls')),
]

urlpatterns += [
    path('api/v1/', include((api_v1_patterns, 'api_v1'), namespace='v1')),
]