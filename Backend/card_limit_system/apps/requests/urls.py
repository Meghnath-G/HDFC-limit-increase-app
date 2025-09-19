"""
URL configuration for Requests app with Firebase support.

Provides routing for both traditional Django ORM views and 
Firebase-compatible views based on settings.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings

# Import both view sets
from .views import LimitRequestViewSet
from .firebase_views import FirebaseLimitRequestViewSet

# Choose view set based on database backend
if getattr(settings, 'USE_FIREBASE_DB', False):
    # Use Firebase views
    LimitRequestViewSetClass = FirebaseLimitRequestViewSet
    app_name = 'requests_firebase'
else:
    # Use traditional Django ORM views
    LimitRequestViewSetClass = LimitRequestViewSet
    app_name = 'requests'

# Create router and register viewset
router = DefaultRouter()
router.register(r'', LimitRequestViewSetClass, basename='limitrequest')

urlpatterns = [
    # Limit request management endpoints
    path('', include(router.urls)),
    
    # Additional request-specific endpoints can be added here
    # For example:
    # path('reports/', RequestReportView.as_view(), name='reports'),
    # path('bulk-approve/', BulkApprovalView.as_view(), name='bulk-approve'),
]

# URL patterns for API documentation
app_name = app_name