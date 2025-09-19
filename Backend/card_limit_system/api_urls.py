"""
URL Configuration for HDFC Card Limit System API
"""

from django.urls import path, include
from . import api_views

urlpatterns = [
    # Health check
    path('health/', api_views.health_check, name='health_check'),
    
    # Customer endpoints
    path('customers/', api_views.submit_customer_data, name='submit_customer_data'),
    
    # Limit request endpoints
    path('limit-requests/', api_views.submit_limit_request, name='submit_limit_request'),
    path('limit-requests/recent/', api_views.get_recent_requests, name='get_recent_requests'),
    path('limit-requests/<str:request_id>/status/', api_views.get_request_status, name='get_request_status'),
]