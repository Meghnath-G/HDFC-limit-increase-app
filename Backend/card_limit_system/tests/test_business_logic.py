"""
Tests for business logic and workflows.

Tests the limit increase request workflow, risk assessment,
approval processes, and business rule validation.
"""

import unittest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.exceptions import ValidationError

from requests.models import LimitIncreaseRequest, ApprovalWorkflow, RiskAssessment
from accounts.models import Customer, CustomerProfile
from cards.models import Card, NetbankingAccount
from tests.factories import (
    CustomerFactory, CustomerProfileFactory, CardFactory,
    NetbankingAccountFactory, LimitIncreaseRequestFactory,
    ApprovalWorkflowFactory, RiskAssessmentFactory, TestDataBuilder
)


class LimitIncreaseRequestWorkflowTest(TestCase):
    """Test cases for limit increase request workflow."""
    
    def setUp(self):
        """Set up test data."""
        self.customer_data = TestDataBuilder.create_complete_customer()
        self.customer = self.customer_data['customer']
        self.profile = self.customer_data['profile']
        self.credit_card = self.customer_data['credit_card']
        self.netbanking = self.customer_data['netbanking']
    
    def test_credit_card_limit_increase_request_creation(self):
        """Test creating a credit card limit increase request."""
        request_data = {
            'customer': self.customer,
            'request_type': 'CREDIT_CARD',
            'current_limit': self.credit_card.current_limit,
            'requested_limit': self.credit_card.current_limit * Decimal('2.0'),
            'reason': 'SALARY_INCREASE',
            'income_proof_amount': Decimal('800000')
        }
        
        request = LimitIncreaseRequest.objects.create(**request_data)
        
        self.assertEqual(request.status, 'PENDING')
        self.assertEqual(request.priority, 'MEDIUM')
        self.assertIsNotNone(request.request_id)
        self.assertIsNotNone(request.submitted_at)
        self.assertFalse(request.auto_approved)
    
    def test_netbanking_limit_increase_request_creation(self):
        """Test creating a netbanking limit increase request."""
        request_data = {
            'customer': self.customer,
            'request_type': 'NETBANKING_DAILY',
            'current_limit': self.netbanking.daily_limit,
            'requested_limit': self.netbanking.daily_limit * Decimal('1.5'),
            'reason': 'BUSINESS_EXPANSION',
            'income_proof_amount': Decimal('1000000')
        }
        
        request = LimitIncreaseRequest.objects.create(**request_data)
        
        self.assertEqual(request.status, 'PENDING')
        self.assertEqual(request.request_type, 'NETBANKING_DAILY')
    
    def test_request_validation_minimum_amount(self):
        """Test validation for minimum increase amount."""
        request_data = {
            'customer': self.customer,
            'request_type': 'CREDIT_CARD',
            'current_limit': Decimal('50000'),
            'requested_limit': Decimal('51000'),  # Only 1000 increase (below minimum)
            'reason': 'SALARY_INCREASE',
            'income_proof_amount': Decimal('500000')
        }
        
        request = LimitIncreaseRequest(**request_data)
        
        with self.assertRaises(ValidationError):
            request.full_clean()
    
    def test_request_validation_maximum_increase_percentage(self):
        """Test validation for maximum increase percentage."""
        request_data = {
            'customer': self.customer,
            'request_type': 'CREDIT_CARD',
            'current_limit': Decimal('50000'),
            'requested_limit': Decimal('500000'),  # 1000% increase (above maximum)
            'reason': 'SALARY_INCREASE',
            'income_proof_amount': Decimal('1000000')
        }
        
        request = LimitIncreaseRequest(**request_data)
        
        with self.assertRaises(ValidationError):
            request.full_clean()
    
    def test_auto_approval_criteria(self):
        """Test auto-approval criteria for small increases."""
        # Create a request below auto-approval threshold
        request_data = {
            'customer': self.customer,
            'request_type': 'CREDIT_CARD',
            'current_limit': Decimal('50000'),
            'requested_limit': Decimal('75000'),  # 25000 increase (below 50000 threshold)
            'reason': 'SALARY_INCREASE',
            'income_proof_amount': Decimal('800000')
        }
        
        # Ensure customer has good credit score
        self.profile.credit_score = 750
        self.profile.save()
        
        request = LimitIncreaseRequest.objects.create(**request_data)
        result = request.evaluate_auto_approval()
        
        self.assertTrue(result['eligible'])
        self.assertEqual(result['reason'], 'AMOUNT_BELOW_THRESHOLD')
    
    def test_auto_approval_denied_low_credit_score(self):
        """Test auto-approval denied for low credit score."""
        request_data = {
            'customer': self.customer,
            'request_type': 'CREDIT_CARD',
            'current_limit': Decimal('50000'),
            'requested_limit': Decimal('75000'),
            'reason': 'SALARY_INCREASE',
            'income_proof_amount': Decimal('800000')
        }
        
        # Set low credit score
        self.profile.credit_score = 600
        self.profile.save()
        
        request = LimitIncreaseRequest.objects.create(**request_data)
        result = request.evaluate_auto_approval()
        
        self.assertFalse(result['eligible'])
        self.assertEqual(result['reason'], 'LOW_CREDIT_SCORE')
    
    def test_workflow_creation_on_request_submission(self):
        """Test that workflow is created when request is submitted."""
        request = LimitIncreaseRequestFactory(customer=self.customer)
        
        # Trigger workflow creation
        workflow = request.create_approval_workflow()
        
        self.assertIsNotNone(workflow)
        self.assertEqual(workflow.request, request)
        self.assertEqual(workflow.current_stage, 'INITIAL_REVIEW')
        self.assertIsNotNone(workflow.workflow_id)
    
    def test_risk_assessment_creation(self):
        """Test risk assessment creation for request."""
        request = LimitIncreaseRequestFactory(customer=self.customer)
        
        # Create risk assessment
        assessment = request.perform_risk_assessment()
        
        self.assertIsNotNone(assessment)
        self.assertEqual(assessment.request, request)
        self.assertIsNotNone(assessment.assessment_id)
        self.assertIsNotNone(assessment.risk_score)
        self.assertIn(assessment.risk_category, ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])


class RiskAssessmentTest(TestCase):
    """Test cases for risk assessment functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.customer_data = TestDataBuilder.create_complete_customer()
        self.customer = self.customer_data['customer']
        self.profile = self.customer_data['profile']
        self.request = LimitIncreaseRequestFactory(customer=self.customer)
    
    def test_risk_assessment_low_risk(self):
        """Test risk assessment for low-risk customer."""
        # Set up low-risk profile
        self.profile.credit_score = 800
        self.profile.annual_income = Decimal('1000000')
        self.profile.employment_type = 'SALARIED'
        self.profile.save()
        
        # Set reasonable request amount
        self.request.requested_limit = self.request.current_limit * Decimal('1.5')
        self.request.save()
        
        assessment = RiskAssessment.create_assessment(self.request)
        
        self.assertEqual(assessment.risk_category, 'LOW')
        self.assertLess(assessment.risk_score, 30)
        self.assertTrue(assessment.is_approved)
    
    def test_risk_assessment_high_risk(self):
        """Test risk assessment for high-risk customer."""
        # Set up high-risk profile
        self.profile.credit_score = 620
        self.profile.annual_income = Decimal('300000')
        self.profile.employment_type = 'SELF_EMPLOYED'
        self.profile.save()
        
        # Set high request amount
        self.request.requested_limit = self.request.current_limit * Decimal('4.0')
        self.request.save()
        
        assessment = RiskAssessment.create_assessment(self.request)
        
        self.assertEqual(assessment.risk_category, 'HIGH')
        self.assertGreater(assessment.risk_score, 70)
        self.assertFalse(assessment.is_approved)
    
    def test_risk_factors_calculation(self):
        """Test individual risk factors calculation."""
        assessment = RiskAssessmentFactory(request=self.request)
        
        # Test credit score factor
        credit_factor = assessment.calculate_credit_score_risk(750)
        self.assertLess(credit_factor, 20)  # Good credit score = low risk
        
        # Test income factor
        income_factor = assessment.calculate_income_risk(
            Decimal('800000'), Decimal('100000')
        )
        self.assertLess(income_factor, 15)  # High income vs request = low risk
        
        # Test employment factor
        employment_factor = assessment.calculate_employment_risk('SALARIED')
        self.assertLess(employment_factor, 10)  # Salaried = low risk
    
    def test_risk_assessment_recommendations(self):
        """Test risk assessment recommendations generation."""
        assessment = RiskAssessmentFactory(
            request=self.request,
            risk_category='MEDIUM',
            risk_score=55
        )
        
        recommendations = assessment.generate_recommendations()
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Check for typical recommendations
        recommendation_text = ' '.join(recommendations)
        self.assertIn('verification', recommendation_text.lower())


class ApprovalWorkflowTest(TestCase):
    """Test cases for approval workflow functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.workflow_data = TestDataBuilder.create_limit_request_workflow()
        self.request = self.workflow_data['request']
        self.workflow = self.workflow_data['workflow']
        self.assessment = self.workflow_data['assessment']
    
    def test_workflow_stage_progression(self):
        """Test workflow stage progression."""
        # Start at INITIAL_REVIEW
        self.assertEqual(self.workflow.current_stage, 'INITIAL_REVIEW')
        
        # Progress to RISK_ASSESSMENT
        self.workflow.advance_stage('RISK_ASSESSMENT')
        self.assertEqual(self.workflow.current_stage, 'RISK_ASSESSMENT')
        
        # Progress to MANAGER_APPROVAL
        self.workflow.advance_stage('MANAGER_APPROVAL')
        self.assertEqual(self.workflow.current_stage, 'MANAGER_APPROVAL')
    
    def test_workflow_approval_thresholds(self):
        """Test approval thresholds for different request amounts."""
        # Small amount - should go to FINAL_VERIFICATION
        self.request.requested_limit = Decimal('75000')
        self.request.save()
        
        next_stage = self.workflow.determine_next_stage()
        self.assertEqual(next_stage, 'FINAL_VERIFICATION')
        
        # Large amount - should go to SENIOR_APPROVAL
        self.request.requested_limit = Decimal('2500000')
        self.request.save()
        
        next_stage = self.workflow.determine_next_stage()
        self.assertEqual(next_stage, 'SENIOR_APPROVAL')
    
    def test_workflow_completion(self):
        """Test workflow completion."""
        # Complete workflow with approval
        result = self.workflow.complete_workflow('APPROVED', 'manager@hdfc.com')
        
        self.assertTrue(result['success'])
        self.assertEqual(self.workflow.status, 'COMPLETED')
        self.assertIsNotNone(self.workflow.completed_at)
        
        # Check request status is updated
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, 'APPROVED')
    
    def test_workflow_rejection(self):
        """Test workflow rejection."""
        # Reject workflow
        result = self.workflow.complete_workflow(
            'REJECTED', 
            'manager@hdfc.com',
            rejection_reason='Insufficient income proof'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(self.workflow.status, 'REJECTED')
        
        # Check request status is updated
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, 'REJECTED')
        self.assertIsNotNone(self.request.rejected_at)
    
    def test_workflow_timeout_handling(self):
        """Test workflow timeout handling."""
        # Set expired deadline
        self.workflow.stage_deadline = datetime.now() - timedelta(days=1)
        self.workflow.save()
        
        # Check if workflow is overdue
        self.assertTrue(self.workflow.is_overdue())
        
        # Trigger escalation
        escalation_result = self.workflow.escalate_overdue()
        
        self.assertTrue(escalation_result['escalated'])
        self.assertIsNotNone(escalation_result['escalated_to'])


class BusinessRulesValidationTest(TestCase):
    """Test cases for business rules validation."""
    
    def setUp(self):
        """Set up test data."""
        self.customer_data = TestDataBuilder.create_complete_customer()
        self.customer = self.customer_data['customer']
        self.profile = self.customer_data['profile']
        self.credit_card = self.customer_data['credit_card']
    
    def test_minimum_account_age_requirement(self):
        """Test minimum account age requirement."""
        # Set recent account opening
        self.credit_card.issued_date = datetime.now().date() - timedelta(days=30)
        self.credit_card.save()
        
        request = LimitIncreaseRequestFactory(
            customer=self.customer,
            request_type='CREDIT_CARD'
        )
        
        validation_result = request.validate_business_rules()
        
        self.assertFalse(validation_result['valid'])
        self.assertIn('ACCOUNT_AGE_MINIMUM', validation_result['violations'])
    
    def test_minimum_income_requirement(self):
        """Test minimum income requirement."""
        # Set low income
        self.profile.annual_income = Decimal('200000')
        self.profile.save()
        
        request = LimitIncreaseRequestFactory(
            customer=self.customer,
            requested_limit=Decimal('500000')
        )
        
        validation_result = request.validate_business_rules()
        
        self.assertFalse(validation_result['valid'])
        self.assertIn('INCOME_MINIMUM', validation_result['violations'])
    
    def test_maximum_utilization_ratio(self):
        """Test maximum utilization ratio check."""
        # Set high utilization
        self.credit_card.available_limit = Decimal('5000')  # High utilization
        self.credit_card.save()
        
        request = LimitIncreaseRequestFactory(
            customer=self.customer,
            request_type='CREDIT_CARD'
        )
        
        validation_result = request.validate_business_rules()
        
        self.assertFalse(validation_result['valid'])
        self.assertIn('UTILIZATION_RATIO_HIGH', validation_result['violations'])
    
    def test_previous_request_cooling_period(self):
        """Test cooling period between requests."""
        # Create a recent previous request
        previous_request = LimitIncreaseRequestFactory(
            customer=self.customer,
            status='APPROVED',
            submitted_at=datetime.now() - timedelta(days=30)
        )
        
        # Try to create new request
        new_request = LimitIncreaseRequestFactory(customer=self.customer)
        
        validation_result = new_request.validate_business_rules()
        
        self.assertFalse(validation_result['valid'])
        self.assertIn('COOLING_PERIOD_VIOLATION', validation_result['violations'])
    
    def test_all_business_rules_passed(self):
        """Test when all business rules are satisfied."""
        # Set up compliant profile
        self.profile.annual_income = Decimal('800000')
        self.profile.credit_score = 750
        self.profile.save()
        
        # Set up compliant card
        self.credit_card.issued_date = datetime.now().date() - timedelta(days=365)
        self.credit_card.available_limit = self.credit_card.current_limit * Decimal('0.5')
        self.credit_card.save()
        
        request = LimitIncreaseRequestFactory(
            customer=self.customer,
            requested_limit=self.credit_card.current_limit * Decimal('1.5')
        )
        
        validation_result = request.validate_business_rules()
        
        self.assertTrue(validation_result['valid'])
        self.assertEqual(len(validation_result['violations']), 0)


class LimitUpdateProcessTest(TestCase):
    """Test cases for limit update process after approval."""
    
    def setUp(self):
        """Set up test data."""
        self.customer_data = TestDataBuilder.create_complete_customer()
        self.customer = self.customer_data['customer']
        self.credit_card = self.customer_data['credit_card']
        self.netbanking = self.customer_data['netbanking']
    
    @patch('core.twilio_service.TwilioService.send_sms')
    @patch('core.sendgrid_service.SendGridService.send_email')
    @patch('core.onesignal_service.OneSignalService.send_notification')
    def test_credit_card_limit_update_process(self, mock_push, mock_email, mock_sms):
        """Test complete credit card limit update process."""
        # Mock external services
        mock_sms.return_value = {'success': True, 'message_sid': 'sms_123'}
        mock_email.return_value = {'success': True, 'message_id': 'email_123'}
        mock_push.return_value = {'success': True, 'notification_id': 'push_123'}
        
        # Create approved request
        request = LimitIncreaseRequestFactory(
            customer=self.customer,
            request_type='CREDIT_CARD',
            current_limit=self.credit_card.current_limit,
            requested_limit=Decimal('100000'),
            status='APPROVED'
        )
        
        # Process limit update
        update_result = request.process_limit_update()
        
        self.assertTrue(update_result['success'])
        
        # Verify card limit was updated
        self.credit_card.refresh_from_db()
        self.assertEqual(self.credit_card.current_limit, Decimal('100000'))
        self.assertIsNotNone(self.credit_card.last_limit_increase)
        
        # Verify notifications were sent
        mock_sms.assert_called_once()
        mock_email.assert_called_once()
        mock_push.assert_called_once()
    
    @patch('core.twilio_service.TwilioService.send_sms')
    def test_netbanking_limit_update_process(self, mock_sms):
        """Test netbanking limit update process."""
        mock_sms.return_value = {'success': True, 'message_sid': 'sms_123'}
        
        # Create approved netbanking request
        request = LimitIncreaseRequestFactory(
            customer=self.customer,
            request_type='NETBANKING_DAILY',
            current_limit=self.netbanking.daily_limit,
            requested_limit=Decimal('200000'),
            status='APPROVED'
        )
        
        # Process limit update
        update_result = request.process_limit_update()
        
        self.assertTrue(update_result['success'])
        
        # Verify netbanking limit was updated
        self.netbanking.refresh_from_db()
        self.assertEqual(self.netbanking.daily_limit, Decimal('200000'))
        self.assertIsNotNone(self.netbanking.last_limit_increase)


if __name__ == '__main__':
    unittest.main()