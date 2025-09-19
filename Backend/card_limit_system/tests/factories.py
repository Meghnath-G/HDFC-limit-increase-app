"""
Factory classes for creating test data.

Uses factory_boy to create realistic test instances
of all models in the Card Limit System.
"""

import factory
import factory.fuzzy
from datetime import datetime, timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from accounts.models import Customer, CustomerProfile
from cards.models import Card, NetbankingAccount
from requests.models import LimitIncreaseRequest, ApprovalWorkflow, RiskAssessment
from notifications.models import OTPVerification, NotificationLog, SystemAlert
from core.models import AuditLog, SystemMetrics


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating Django User instances."""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False
    is_superuser = False
    date_joined = factory.fuzzy.FuzzyDateTime(
        datetime.now() - timedelta(days=365),
        datetime.now()
    )


class CustomerFactory(factory.django.DjangoModelFactory):
    """Factory for creating Customer instances."""
    
    class Meta:
        model = Customer
    
    customer_id = factory.Sequence(lambda n: f'CUST{n:06d}')
    phone_number = factory.Faker('phone_number')
    email = factory.Faker('email')
    is_active = True
    firebase_uid = factory.Faker('uuid4')
    created_at = factory.fuzzy.FuzzyDateTime(
        datetime.now() - timedelta(days=365),
        datetime.now()
    )
    last_login = factory.LazyAttribute(
        lambda obj: obj.created_at + timedelta(days=1)
    )


class CustomerProfileFactory(factory.django.DjangoModelFactory):
    """Factory for creating CustomerProfile instances."""
    
    class Meta:
        model = CustomerProfile
    
    customer = factory.SubFactory(CustomerFactory)
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    date_of_birth = factory.Faker('date_of_birth', minimum_age=18, maximum_age=80)
    pan_number = factory.Sequence(lambda n: f'ABCDE{n:04d}F')
    aadhar_number = factory.Sequence(lambda n: f'{n:012d}')
    address_line1 = factory.Faker('street_address')
    address_line2 = factory.Faker('secondary_address')
    city = factory.Faker('city')
    state = factory.Faker('state')
    pincode = factory.Faker('postcode')
    annual_income = factory.fuzzy.FuzzyDecimal(300000, 2000000, 2)
    employment_type = factory.fuzzy.FuzzyChoice([
        'SALARIED', 'SELF_EMPLOYED', 'BUSINESS', 'RETIRED'
    ])
    company_name = factory.Faker('company')
    kyc_status = 'VERIFIED'
    credit_score = factory.fuzzy.FuzzyInteger(600, 850)


class CardFactory(factory.django.DjangoModelFactory):
    """Factory for creating Card instances."""
    
    class Meta:
        model = Card
    
    customer = factory.SubFactory(CustomerFactory)
    card_number = factory.Sequence(lambda n: f'4111111111{n:06d}')
    card_type = factory.fuzzy.FuzzyChoice(['CREDIT', 'DEBIT'])
    card_variant = factory.fuzzy.FuzzyChoice([
        'CLASSIC', 'GOLD', 'PLATINUM', 'SIGNATURE', 'INFINITE'
    ])
    current_limit = factory.fuzzy.FuzzyDecimal(10000, 500000, 2)
    available_limit = factory.LazyAttribute(
        lambda obj: obj.current_limit * Decimal('0.7')
    )
    expiry_date = factory.LazyAttribute(
        lambda obj: datetime.now().date() + timedelta(days=1095)  # 3 years
    )
    status = 'ACTIVE'
    issued_date = factory.fuzzy.FuzzyDate(
        datetime.now().date() - timedelta(days=1095),
        datetime.now().date() - timedelta(days=30)
    )
    last_limit_increase = None


class NetbankingAccountFactory(factory.django.DjangoModelFactory):
    """Factory for creating NetbankingAccount instances."""
    
    class Meta:
        model = NetbankingAccount
    
    customer = factory.SubFactory(CustomerFactory)
    account_number = factory.Sequence(lambda n: f'{n:014d}')
    account_type = factory.fuzzy.FuzzyChoice([
        'SAVINGS', 'CURRENT', 'SALARY', 'NRI'
    ])
    daily_limit = factory.fuzzy.FuzzyDecimal(50000, 1000000, 2)
    per_transaction_limit = factory.fuzzy.FuzzyDecimal(25000, 500000, 2)
    monthly_limit = factory.LazyAttribute(
        lambda obj: obj.daily_limit * 30
    )
    is_active = True
    opened_date = factory.fuzzy.FuzzyDate(
        datetime.now().date() - timedelta(days=3650),  # 10 years ago
        datetime.now().date() - timedelta(days=90)     # 3 months ago
    )
    last_limit_increase = None


class LimitIncreaseRequestFactory(factory.django.DjangoModelFactory):
    """Factory for creating LimitIncreaseRequest instances."""
    
    class Meta:
        model = LimitIncreaseRequest
    
    customer = factory.SubFactory(CustomerFactory)
    request_id = factory.Sequence(lambda n: f'REQ{n:08d}')
    request_type = factory.fuzzy.FuzzyChoice([
        'CREDIT_CARD', 'DEBIT_CARD', 'NETBANKING_DAILY', 
        'NETBANKING_TRANSACTION', 'NETBANKING_MONTHLY'
    ])
    current_limit = factory.fuzzy.FuzzyDecimal(10000, 500000, 2)
    requested_limit = factory.LazyAttribute(
        lambda obj: obj.current_limit * Decimal('2.0')
    )
    reason = factory.fuzzy.FuzzyChoice([
        'SALARY_INCREASE', 'BUSINESS_EXPANSION', 'EMERGENCY_NEED',
        'TRAVEL_REQUIREMENTS', 'INVESTMENT_OPPORTUNITY'
    ])
    supporting_documents = factory.LazyFunction(list)
    income_proof_amount = factory.fuzzy.FuzzyDecimal(300000, 2000000, 2)
    status = 'PENDING'
    priority = 'MEDIUM'
    submitted_at = factory.fuzzy.FuzzyDateTime(
        datetime.now() - timedelta(days=30),
        datetime.now()
    )
    expected_processing_time = timedelta(days=7)
    auto_approved = False


class ApprovalWorkflowFactory(factory.django.DjangoModelFactory):
    """Factory for creating ApprovalWorkflow instances."""
    
    class Meta:
        model = ApprovalWorkflow
    
    request = factory.SubFactory(LimitIncreaseRequestFactory)
    workflow_id = factory.Sequence(lambda n: f'WF{n:08d}')
    current_stage = factory.fuzzy.FuzzyChoice([
        'INITIAL_REVIEW', 'RISK_ASSESSMENT', 'MANAGER_APPROVAL',
        'SENIOR_APPROVAL', 'FINAL_VERIFICATION'
    ])
    assigned_to = factory.Faker('email')
    stage_deadline = factory.LazyAttribute(
        lambda obj: datetime.now() + timedelta(days=3)
    )
    workflow_data = factory.LazyFunction(dict)
    created_at = factory.fuzzy.FuzzyDateTime(
        datetime.now() - timedelta(days=7),
        datetime.now()
    )


class RiskAssessmentFactory(factory.django.DjangoModelFactory):
    """Factory for creating RiskAssessment instances."""
    
    class Meta:
        model = RiskAssessment
    
    request = factory.SubFactory(LimitIncreaseRequestFactory)
    assessment_id = factory.Sequence(lambda n: f'RISK{n:08d}')
    risk_score = factory.fuzzy.FuzzyInteger(1, 100)
    risk_category = factory.fuzzy.FuzzyChoice([
        'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    ])
    assessment_factors = factory.LazyFunction(dict)
    recommendations = factory.LazyFunction(list)
    assessed_by = 'SYSTEM'
    assessed_at = factory.fuzzy.FuzzyDateTime(
        datetime.now() - timedelta(days=7),
        datetime.now()
    )
    is_approved = factory.fuzzy.FuzzyChoice([True, False])


class OTPVerificationFactory(factory.django.DjangoModelFactory):
    """Factory for creating OTPVerification instances."""
    
    class Meta:
        model = OTPVerification
    
    customer = factory.SubFactory(CustomerFactory)
    otp_id = factory.Sequence(lambda n: f'OTP{n:08d}')
    otp_code = factory.Sequence(lambda n: f'{n:06d}')
    purpose = factory.fuzzy.FuzzyChoice([
        'LOGIN', 'REGISTRATION', 'LIMIT_REQUEST', 'PROFILE_UPDATE',
        'CARD_ACTIVATION', 'TRANSACTION_VERIFICATION'
    ])
    delivery_method = factory.fuzzy.FuzzyChoice(['SMS', 'EMAIL', 'VOICE', 'WHATSAPP'])
    delivery_address = factory.Faker('phone_number')
    attempts_count = 0
    max_attempts = 3
    is_verified = False
    expires_at = factory.LazyAttribute(
        lambda obj: datetime.now() + timedelta(minutes=5)
    )
    created_at = factory.fuzzy.FuzzyDateTime(
        datetime.now() - timedelta(minutes=10),
        datetime.now()
    )


class NotificationLogFactory(factory.django.DjangoModelFactory):
    """Factory for creating NotificationLog instances."""
    
    class Meta:
        model = NotificationLog
    
    customer = factory.SubFactory(CustomerFactory)
    notification_id = factory.Sequence(lambda n: f'NOTIF{n:08d}')
    notification_type = factory.fuzzy.FuzzyChoice([
        'REQUEST_STATUS', 'OTP_DELIVERY', 'LIMIT_APPROVED', 
        'LIMIT_REJECTED', 'SYSTEM_ALERT', 'PROMOTIONAL'
    ])
    channel = factory.fuzzy.FuzzyChoice(['SMS', 'EMAIL', 'PUSH', 'WHATSAPP'])
    recipient = factory.Faker('phone_number')
    subject = factory.Faker('sentence', nb_words=6)
    message = factory.Faker('text', max_nb_chars=160)
    template_id = factory.Faker('uuid4')
    delivery_status = factory.fuzzy.FuzzyChoice([
        'PENDING', 'SENT', 'DELIVERED', 'FAILED', 'BOUNCED'
    ])
    external_id = factory.Faker('uuid4')
    metadata = factory.LazyFunction(dict)
    sent_at = factory.fuzzy.FuzzyDateTime(
        datetime.now() - timedelta(hours=24),
        datetime.now()
    )
    delivered_at = factory.LazyAttribute(
        lambda obj: obj.sent_at + timedelta(seconds=30) if obj.delivery_status == 'DELIVERED' else None
    )


class SystemAlertFactory(factory.django.DjangoModelFactory):
    """Factory for creating SystemAlert instances."""
    
    class Meta:
        model = SystemAlert
    
    alert_id = factory.Sequence(lambda n: f'ALERT{n:06d}')
    alert_type = factory.fuzzy.FuzzyChoice([
        'SYSTEM_ERROR', 'SERVICE_DOWN', 'HIGH_LOAD', 'SECURITY_BREACH',
        'DATABASE_ISSUE', 'API_FAILURE', 'INTEGRATION_ERROR'
    ])
    severity = factory.fuzzy.FuzzyChoice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('text', max_nb_chars=500)
    affected_service = factory.fuzzy.FuzzyChoice([
        'API', 'DATABASE', 'FIREBASE', 'TWILIO', 'SENDGRID', 'ONESIGNAL'
    ])
    metrics = factory.LazyFunction(dict)
    status = factory.fuzzy.FuzzyChoice(['ACTIVE', 'ACKNOWLEDGED', 'RESOLVED'])
    acknowledged_by = None
    acknowledged_at = None
    resolved_at = None
    created_at = factory.fuzzy.FuzzyDateTime(
        datetime.now() - timedelta(hours=24),
        datetime.now()
    )


class AuditLogFactory(factory.django.DjangoModelFactory):
    """Factory for creating AuditLog instances."""
    
    class Meta:
        model = AuditLog
    
    log_id = factory.Sequence(lambda n: f'AUDIT{n:08d}')
    user_id = factory.SubFactory(CustomerFactory)
    action = factory.fuzzy.FuzzyChoice([
        'LOGIN', 'LOGOUT', 'PROFILE_UPDATE', 'LIMIT_REQUEST',
        'OTP_VERIFICATION', 'CARD_ACTIVATION', 'DOCUMENT_UPLOAD'
    ])
    resource_type = factory.fuzzy.FuzzyChoice([
        'CUSTOMER', 'CARD', 'NETBANKING', 'LIMIT_REQUEST', 'OTP'
    ])
    resource_id = factory.Faker('uuid4')
    ip_address = factory.Faker('ipv4')
    user_agent = factory.Faker('user_agent')
    request_data = factory.LazyFunction(dict)
    response_data = factory.LazyFunction(dict)
    status_code = factory.fuzzy.FuzzyChoice([200, 201, 400, 401, 403, 404, 500])
    execution_time = factory.fuzzy.FuzzyFloat(0.1, 5.0)
    created_at = factory.fuzzy.FuzzyDateTime(
        datetime.now() - timedelta(days=30),
        datetime.now()
    )


class SystemMetricsFactory(factory.django.DjangoModelFactory):
    """Factory for creating SystemMetrics instances."""
    
    class Meta:
        model = SystemMetrics
    
    metric_id = factory.Sequence(lambda n: f'METRIC{n:06d}')
    metric_type = factory.fuzzy.FuzzyChoice([
        'API_PERFORMANCE', 'DATABASE_PERFORMANCE', 'EXTERNAL_SERVICE',
        'SYSTEM_RESOURCE', 'BUSINESS_KPI', 'SECURITY_METRIC'
    ])
    metric_name = factory.fuzzy.FuzzyChoice([
        'response_time', 'throughput', 'error_rate', 'cpu_usage',
        'memory_usage', 'disk_usage', 'request_count', 'success_rate'
    ])
    metric_value = factory.fuzzy.FuzzyFloat(0.0, 100.0)
    metric_unit = factory.fuzzy.FuzzyChoice([
        'milliseconds', 'seconds', 'requests/minute', 'percentage',
        'count', 'bytes', 'megabytes', 'gigabytes'
    ])
    dimensions = factory.LazyFunction(dict)
    tags = factory.LazyFunction(dict)
    timestamp = factory.fuzzy.FuzzyDateTime(
        datetime.now() - timedelta(hours=24),
        datetime.now()
    )


# Utility functions for test data creation
class TestDataBuilder:
    """Helper class for building complex test scenarios."""
    
    @staticmethod
    def create_complete_customer():
        """Create a customer with profile, cards, and netbanking accounts."""
        customer = CustomerFactory()
        profile = CustomerProfileFactory(customer=customer)
        credit_card = CardFactory(customer=customer, card_type='CREDIT')
        debit_card = CardFactory(customer=customer, card_type='DEBIT')
        netbanking = NetbankingAccountFactory(customer=customer)
        
        return {
            'customer': customer,
            'profile': profile,
            'credit_card': credit_card,
            'debit_card': debit_card,
            'netbanking': netbanking
        }
    
    @staticmethod
    def create_limit_request_workflow():
        """Create a complete limit request with workflow and assessment."""
        request = LimitIncreaseRequestFactory()
        workflow = ApprovalWorkflowFactory(request=request)
        assessment = RiskAssessmentFactory(request=request)
        
        return {
            'request': request,
            'workflow': workflow,
            'assessment': assessment
        }
    
    @staticmethod
    def create_otp_verification_flow(customer=None):
        """Create OTP verification with notifications."""
        if not customer:
            customer = CustomerFactory()
        
        otp = OTPVerificationFactory(customer=customer)
        sms_notification = NotificationLogFactory(
            customer=customer,
            notification_type='OTP_DELIVERY',
            channel='SMS'
        )
        email_notification = NotificationLogFactory(
            customer=customer,
            notification_type='OTP_DELIVERY',
            channel='EMAIL'
        )
        
        return {
            'otp': otp,
            'sms_notification': sms_notification,
            'email_notification': email_notification
        }
    
    @staticmethod
    def create_system_monitoring_data():
        """Create system alerts and metrics for monitoring tests."""
        alerts = [
            SystemAlertFactory(severity='HIGH', status='ACTIVE'),
            SystemAlertFactory(severity='MEDIUM', status='ACKNOWLEDGED'),
            SystemAlertFactory(severity='LOW', status='RESOLVED')
        ]
        
        metrics = [
            SystemMetricsFactory(metric_type='API_PERFORMANCE', metric_name='response_time'),
            SystemMetricsFactory(metric_type='DATABASE_PERFORMANCE', metric_name='query_time'),
            SystemMetricsFactory(metric_type='SYSTEM_RESOURCE', metric_name='cpu_usage'),
            SystemMetricsFactory(metric_type='BUSINESS_KPI', metric_name='approval_rate')
        ]
        
        return {
            'alerts': alerts,
            'metrics': metrics
        }