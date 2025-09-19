"""
Limit Request API Schema Documentation
=====================================

OpenAPI schema definitions and examples for limit increase request endpoints.
"""

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status


# Limit Request Creation Examples
LIMIT_REQUEST_CREATE_REQUEST_EXAMPLE = OpenApiExample(
    'Limit Request Creation',
    value={
        'request_type': 'credit_card',
        'card_number': '1234567890123456',
        'current_limit': 100000.00,
        'requested_limit': 150000.00,
        'reason': 'Higher monthly expenses due to business growth',
        'income_details': {
            'monthly_income': 75000.00,
            'income_source': 'salary',
            'employer_name': 'Tech Corp Pvt Ltd',
            'employment_type': 'permanent'
        },
        'supporting_documents': [
            {
                'document_type': 'salary_slip',
                'file_url': 'https://storage.hdfc.com/docs/salary_slip_202412.pdf',
                'file_hash': 'sha256:abc123...'
            },
            {
                'document_type': 'bank_statement',
                'file_url': 'https://storage.hdfc.com/docs/bank_statement_6m.pdf',
                'file_hash': 'sha256:def456...'
            }
        ],
        'declaration': {
            'income_accuracy': True,
            'no_default_history': True,
            'terms_accepted': True,
            'declaration_date': '2024-12-19T10:30:00Z'
        }
    },
    request_only=True
)

LIMIT_REQUEST_CREATE_RESPONSE_EXAMPLE = OpenApiExample(
    'Limit Request Creation Response',
    value={
        'success': True,
        'data': {
            'request_id': 'REQ123456789',
            'reference_number': 'HDFC/LMT/2024/123456',
            'request_type': 'credit_card',
            'customer_id': 'CUST123456789',
            'card_number': '****-****-****-3456',
            'current_limit': 100000.00,
            'requested_limit': 150000.00,
            'status': 'submitted',
            'priority': 'normal',
            'estimated_processing_time': '3-5 business days',
            'next_steps': [
                'Document verification',
                'Credit assessment',
                'Management approval'
            ],
            'tracking_url': 'https://card-limit.hdfc.com/track/REQ123456789',
            'submitted_at': '2024-12-19T10:30:00Z',
            'expected_completion': '2024-12-24T18:00:00Z'
        },
        'message': 'Limit increase request submitted successfully',
        'request_id': 'req_1234567890',
        'timestamp': '2024-12-19T10:30:00Z'
    },
    response_only=True
)

# Netbanking Limit Request Example
NETBANKING_LIMIT_REQUEST_EXAMPLE = OpenApiExample(
    'Netbanking Limit Request',
    value={
        'request_type': 'netbanking',
        'account_number': '1234567890',
        'limit_type': 'daily_transaction',
        'current_limit': 50000.00,
        'requested_limit': 100000.00,
        'reason': 'Business payments require higher daily limits',
        'business_details': {
            'business_type': 'trading',
            'monthly_turnover': 500000.00,
            'gst_number': '27ABCDE1234F1Z5',
            'business_vintage': 36
        },
        'usage_pattern': {
            'typical_transaction_amount': 25000.00,
            'monthly_transaction_count': 20,
            'peak_usage_time': 'business_hours',
            'transaction_types': ['vendor_payment', 'utility_bills', 'tax_payment']
        }
    },
    request_only=True
)

# Limit Request Status Examples
LIMIT_REQUEST_STATUS_RESPONSE_EXAMPLE = OpenApiExample(
    'Limit Request Status Response',
    value={
        'success': True,
        'data': {
            'request_id': 'REQ123456789',
            'reference_number': 'HDFC/LMT/2024/123456',
            'status': 'under_review',
            'current_stage': 'credit_assessment',
            'progress_percentage': 60,
            'status_history': [
                {
                    'status': 'submitted',
                    'timestamp': '2024-12-19T10:30:00Z',
                    'comment': 'Request submitted by customer'
                },
                {
                    'status': 'document_verified',
                    'timestamp': '2024-12-20T14:15:00Z',
                    'comment': 'All documents verified successfully'
                },
                {
                    'status': 'under_review',
                    'timestamp': '2024-12-21T09:00:00Z',
                    'comment': 'Credit assessment in progress'
                }
            ],
            'estimated_completion': '2024-12-24T18:00:00Z',
            'can_cancel': True,
            'can_modify': False,
            'next_update_expected': '2024-12-22T12:00:00Z'
        },
        'message': 'Request status retrieved successfully',
        'request_id': 'req_1234567890',
        'timestamp': '2024-12-19T10:30:00Z'
    },
    response_only=True
)

# Limit Request List Examples
LIMIT_REQUEST_LIST_RESPONSE_EXAMPLE = OpenApiExample(
    'Limit Request List Response',
    value={
        'success': True,
        'data': {
            'results': [
                {
                    'request_id': 'REQ123456789',
                    'reference_number': 'HDFC/LMT/2024/123456',
                    'request_type': 'credit_card',
                    'card_number': '****-****-****-3456',
                    'requested_limit': 150000.00,
                    'status': 'under_review',
                    'priority': 'normal',
                    'submitted_at': '2024-12-19T10:30:00Z',
                    'estimated_completion': '2024-12-24T18:00:00Z'
                },
                {
                    'request_id': 'REQ123456788',
                    'reference_number': 'HDFC/LMT/2024/123455',
                    'request_type': 'netbanking',
                    'account_number': '****1234',
                    'requested_limit': 100000.00,
                    'status': 'approved',
                    'priority': 'normal',
                    'submitted_at': '2024-12-15T08:00:00Z',
                    'completed_at': '2024-12-18T16:30:00Z'
                }
            ],
            'pagination': {
                'count': 15,
                'next': 'cursor_token_next_page',
                'previous': None,
                'page_size': 10,
                'total_pages': 2
            },
            'filters_applied': {
                'status': 'all',
                'request_type': 'all',
                'date_range': 'last_30_days'
            }
        },
        'message': 'Limit requests retrieved successfully',
        'request_id': 'req_1234567890',
        'timestamp': '2024-12-19T10:30:00Z'
    },
    response_only=True
)

# Request Cancellation Example
LIMIT_REQUEST_CANCEL_REQUEST_EXAMPLE = OpenApiExample(
    'Limit Request Cancellation',
    value={
        'cancellation_reason': 'changed_mind',
        'comments': 'No longer need the increased limit due to change in financial plans'
    },
    request_only=True
)

LIMIT_REQUEST_CANCEL_RESPONSE_EXAMPLE = OpenApiExample(
    'Limit Request Cancellation Response',
    value={
        'success': True,
        'data': {
            'request_id': 'REQ123456789',
            'status': 'cancelled',
            'cancelled_at': '2024-12-19T15:30:00Z',
            'cancellation_reason': 'changed_mind',
            'refund_applicable': False,
            'can_reapply': True,
            'reapply_after': '2024-12-26T00:00:00Z'
        },
        'message': 'Request cancelled successfully',
        'request_id': 'req_1234567890',
        'timestamp': '2024-12-19T15:30:00Z'
    },
    response_only=True
)

# Schema Decorators
limit_request_create_schema = extend_schema(
    operation_id='limit_request_create',
    summary='Create Limit Increase Request',
    description='''
    Submit a new card or netbanking limit increase request with supporting documentation.
    
    This endpoint handles various types of limit increase requests:
    - Credit card limit increases
    - Debit card limit increases  
    - Netbanking transaction limit increases
    - International transaction limit increases
    
    **Request Types:**
    - credit_card: Credit card limit increase
    - debit_card: Debit card limit increase
    - netbanking: Netbanking daily/monthly limit increase
    - international: International transaction limit increase
    
    **Business Rules:**
    - Customer must have active account/card for minimum 6 months
    - No pending limit requests for same product
    - Requested limit must be within policy guidelines
    - Income verification documents required for significant increases
    - Rate limited to 5 requests per 24 hours per customer
    
    **Processing Workflow:**
    1. Initial validation and document upload
    2. Automated eligibility assessment
    3. Document verification by operations team
    4. Credit assessment and risk evaluation
    5. Management approval for high-value requests
    6. Final approval and limit activation
    
    **Required Documents:**
    - Income proof (salary slips, ITR, bank statements)
    - Identity proof (PAN, Aadhaar)
    - Address proof (if address changed)
    - Business proof (for business accounts)
    ''',
    examples=[
        LIMIT_REQUEST_CREATE_REQUEST_EXAMPLE,
        NETBANKING_LIMIT_REQUEST_EXAMPLE,
        LIMIT_REQUEST_CREATE_RESPONSE_EXAMPLE
    ],
    tags=['Requests']
)

limit_request_status_schema = extend_schema(
    operation_id='limit_request_status',
    summary='Get Request Status',
    description='''
    Retrieve detailed status and progress information for a limit increase request.
    
    This endpoint provides comprehensive tracking information including:
    - Current processing stage and status
    - Progress percentage and timeline
    - Status history with timestamps
    - Expected completion date
    - Available actions (cancel, modify)
    
    **Status Values:**
    - submitted: Request received and queued for processing
    - document_verification: Documents being verified
    - under_review: Credit assessment in progress
    - pending_approval: Awaiting management approval
    - approved: Request approved, limit being updated
    - completed: Limit increase activated
    - rejected: Request declined with reason
    - cancelled: Request cancelled by customer
    
    **Real-time Updates:**
    Status updates are available in real-time and customers are notified via:
    - Email notifications
    - SMS updates
    - Push notifications
    - In-app notifications
    ''',
    examples=[LIMIT_REQUEST_STATUS_RESPONSE_EXAMPLE],
    tags=['Requests']
)

limit_request_list_schema = extend_schema(
    operation_id='limit_request_list',
    summary='List Customer Requests',
    description='''
    Retrieve a paginated list of all limit increase requests for the authenticated customer.
    
    This endpoint supports filtering and sorting:
    - Filter by status, request type, date range
    - Sort by submission date, completion date, priority
    - Pagination with cursor-based navigation
    - Search by reference number or request ID
    
    **Filtering Options:**
    - status: Filter by request status
    - request_type: Filter by type of limit request
    - date_range: Filter by submission date range
    - priority: Filter by request priority
    
    **Response Information:**
    - Summary view of each request
    - Key details for quick identification
    - Status and progress indicators
    - Timeline and completion estimates
    
    **Performance:**
    - Results are cached for improved performance
    - Paginated responses for large datasets
    - Optimized queries for fast response times
    ''',
    examples=[LIMIT_REQUEST_LIST_RESPONSE_EXAMPLE],
    tags=['Requests']
)

limit_request_cancel_schema = extend_schema(
    operation_id='limit_request_cancel',
    summary='Cancel Limit Request',
    description='''
    Cancel a pending limit increase request with optional reason and comments.
    
    This endpoint allows customers to cancel requests that are:
    - In submitted status
    - Under document verification
    - Under review (before final approval)
    
    **Cancellation Rules:**
    - Requests can only be cancelled before final approval
    - Approved or completed requests cannot be cancelled
    - Cancellation reasons are mandatory for audit purposes
    - Processing fees (if any) may not be refundable
    
    **Cancellation Reasons:**
    - changed_mind: Customer changed mind
    - found_alternative: Found alternative solution
    - financial_change: Change in financial situation
    - error_in_request: Error in original request
    - other: Other reason with mandatory comments
    
    **After Cancellation:**
    - Request status changes to 'cancelled'
    - Customer can submit new request after cooling period
    - Audit trail maintains cancellation record
    - Notifications sent to customer confirming cancellation
    ''',
    examples=[
        LIMIT_REQUEST_CANCEL_REQUEST_EXAMPLE,
        LIMIT_REQUEST_CANCEL_RESPONSE_EXAMPLE
    ],
    tags=['Requests']
)

# Export all request schema decorators
__all__ = [
    'limit_request_create_schema',
    'limit_request_status_schema',
    'limit_request_list_schema',
    'limit_request_cancel_schema',
    'LIMIT_REQUEST_CREATE_REQUEST_EXAMPLE',
    'LIMIT_REQUEST_CREATE_RESPONSE_EXAMPLE',
    'NETBANKING_LIMIT_REQUEST_EXAMPLE',
    'LIMIT_REQUEST_STATUS_RESPONSE_EXAMPLE',
    'LIMIT_REQUEST_LIST_RESPONSE_EXAMPLE',
    'LIMIT_REQUEST_CANCEL_REQUEST_EXAMPLE',
    'LIMIT_REQUEST_CANCEL_RESPONSE_EXAMPLE'
]