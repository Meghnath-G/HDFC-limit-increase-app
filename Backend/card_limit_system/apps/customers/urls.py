"""
URL configuration for Customer app with Firebase support.

Provides routing for both traditional Django ORM views and 
Firebase-compatible views based on settings.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings

# Import both view sets
from .views import CustomerViewSet
from .firebase_views import FirebaseCustomerViewSet

# Choose view set based on database backend
if getattr(settings, 'USE_FIREBASE_DB', False):
    # Use Firebase views
    CustomerViewSetClass = FirebaseCustomerViewSet
    app_name = 'customers_firebase'
else:
    # Use traditional Django ORM views
    CustomerViewSetClass = CustomerViewSet
    app_name = 'customers'

# Create router and register viewset
router = DefaultRouter()
router.register(r'', CustomerViewSetClass, basename='customer')

urlpatterns = [
    # Customer management endpoints
    path('', include(router.urls)),
    
    # Additional customer-specific endpoints can be added here
    # For example:
    # path('bulk-import/', CustomerBulkImportView.as_view(), name='bulk-import'),
    # path('export/', CustomerExportView.as_view(), name='export'),
]

# URL patterns for API documentation
app_name = app_name