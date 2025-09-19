"""
API Views for HDFC Card Limit System
Handles data submission from Flutter app to Oracle Database
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def submit_limit_request(request):
    """
    API endpoint to receive limit increase requests from Flutter app
    """
    try:
        data = request.data
        
        # Log the incoming request
        logger.info(f"Received limit request: {data}")
        
        # Validate required fields
        required_fields = ['customer_name', 'email', 'card_type', 'current_limit', 'requested_limit', 'reason']
        for field in required_fields:
            if field not in data:
                return Response(
                    {'error': f'Missing required field: {field}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Create request ID
        request_id = str(uuid.uuid4())
        
        # Prepare data for Oracle insertion
        request_data = {
            'id': request_id,
            'customer_name': data.get('customer_name'),
            'email': data.get('email'),
            'phone_number': data.get('phone_number', ''),
            'card_type': data.get('card_type'),
            'current_limit': float(data.get('current_limit', 0)),
            'requested_limit': float(data.get('requested_limit', 0)),
            'reason': data.get('reason'),
            'annual_income': float(data.get('annual_income', 0)),
            'employment_status': data.get('employment_status', 'NOT_SPECIFIED'),
            'status': 'pending',
            'request_date': datetime.now().isoformat(),
        }
        
        # Here you would normally insert into Oracle database
        # For now, we'll log the data and return success
        logger.info(f"Would insert into Oracle: {request_data}")
        
        # Simulate Oracle insertion success
        response_data = {
            'success': True,
            'request_id': request_id,
            'message': 'Limit request submitted successfully',
            'status': 'pending',
            'estimated_review_time': '2-3 business days'
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error processing limit request: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def get_request_status(request, request_id):
    """
    API endpoint to check status of a limit request
    """
    try:
        # Here you would query Oracle database
        # For demo, return mock data
        mock_data = {
            'request_id': request_id,
            'status': 'under_review',
            'submitted_date': '2025-09-19T10:30:00Z',
            'estimated_completion': '2025-09-21T17:00:00Z',
            'reviewer_comments': 'Request is being reviewed by our team'
        }
        
        return Response(mock_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching request status: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint
    """
    return Response({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'HDFC Card Limit API',
        'version': '1.0.0'
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def submit_customer_data(request):
    """
    API endpoint to receive customer data from Flutter app
    """
    try:
        data = request.data
        
        # Log the incoming data
        logger.info(f"Received customer data: {data}")
        
        # Create customer ID
        customer_id = str(uuid.uuid4())
        
        # Prepare customer data
        customer_data = {
            'id': customer_id,
            'firebase_uid': data.get('firebase_uid', ''),
            'name': data.get('name'),
            'email': data.get('email'),
            'phone_number': data.get('phone_number'),
            'date_of_birth': data.get('date_of_birth'),
            'created_at': datetime.now().isoformat(),
        }
        
        # Log data that would be inserted into Oracle
        logger.info(f"Would insert customer into Oracle: {customer_data}")
        
        response_data = {
            'success': True,
            'customer_id': customer_id,
            'message': 'Customer data submitted successfully'
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error processing customer data: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Mock data endpoint for testing
@api_view(['GET'])
@permission_classes([AllowAny])
def get_recent_requests(request):
    """
    Get recent limit requests for demonstration
    """
    mock_requests = [
        {
            'id': str(uuid.uuid4()),
            'customer_name': 'Rajesh Kumar',
            'email': 'rajesh.kumar@email.com',
            'card_type': 'CREDIT',
            'current_limit': 50000,
            'requested_limit': 75000,
            'status': 'pending',
            'request_date': '2025-09-19T10:30:00Z'
        },
        {
            'id': str(uuid.uuid4()),
            'customer_name': 'Priya Sharma',
            'email': 'priya.sharma@email.com',
            'card_type': 'CREDIT',
            'current_limit': 30000,
            'requested_limit': 50000,
            'status': 'under_review',
            'request_date': '2025-09-19T09:15:00Z'
        }
    ]
    
    return Response({
        'success': True,
        'requests': mock_requests,
        'total_count': len(mock_requests)
    })