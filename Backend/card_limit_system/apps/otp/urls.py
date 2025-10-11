from django.urls import path
from . import api_views

app_name = 'otp'

urlpatterns = [
    # OTP Management APIs
    path('send-otp/', api_views.OTPView.as_view(), name='send_otp'),
    path('verify-otp/', api_views.verify_otp, name='verify_otp'),
    path('resend-otp/', api_views.resend_otp, name='resend_otp'),
]
