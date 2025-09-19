"""
SendGrid API integration for email services.

Provides secure email delivery with template support,
tracking, analytics, and proper error handling.
"""

import sendgrid
from sendgrid.helpers.mail import (
    Mail, From, To, Subject, PlainTextContent, HtmlContent,
    Attachment, FileContent, FileName, FileType, Disposition,
    ContentId, TemplateId, DynamicTemplateData
)
import logging
from typing import Optional, Dict, Any, List
from django.conf import settings
from django.core.cache import cache
import base64
import mimetypes
import os

logger = logging.getLogger(__name__)


class SendGridService:
    """
    Service for SendGrid email operations.
    
    Handles email sending, template management, and delivery
    tracking with proper error handling and analytics.
    """
    
    _client = None
    _default_from_email = None
    _default_from_name = None
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Initialize SendGrid client."""
        if cls._initialized:
            return
        
        try:
            # Get SendGrid API key from settings
            api_key = getattr(settings, 'SENDGRID_API_KEY', None)
            
            if api_key:
                cls._client = sendgrid.SendGridAPIClient(api_key=api_key)
                cls._default_from_email = getattr(settings, 'SENDGRID_FROM_EMAIL', None)
                cls._default_from_name = getattr(settings, 'SENDGRID_FROM_NAME', 'HDFC Bank')
                cls._initialized = True
                logger.info("SendGrid client initialized successfully")
            else:
                logger.warning("SendGrid API key not configured")
                
        except Exception as e:
            logger.error(f"SendGrid initialization failed: {str(e)}")
            raise
    
    @classmethod
    def send_email(cls, to_email: str, subject: str, plain_content: str = None,
                   html_content: str = None, from_email: str = None, from_name: str = None,
                   attachments: List[Dict[str, Any]] = None, 
                   custom_args: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Send email using SendGrid.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            plain_content: Plain text content
            html_content: HTML content
            from_email: Sender email (uses default if not provided)
            from_name: Sender name (uses default if not provided)
            attachments: List of attachments
            custom_args: Custom tracking arguments
            
        Returns:
            Dictionary with delivery status and details
        """
        if not cls._initialized:
            cls.initialize()
        
        if not cls._client:
            return {
                'success': False,
                'error': 'SendGrid not configured',
                'error_code': 'CONFIG_ERROR'
            }
        
        try:
            # Use default sender if not provided
            if not from_email:
                from_email = cls._default_from_email
                if not from_email:
                    return {
                        'success': False,
                        'error': 'No sender email configured',
                        'error_code': 'CONFIG_ERROR'
                    }
            
            if not from_name:
                from_name = cls._default_from_name
            
            # Create mail object
            from_addr = From(from_email, from_name)
            to_addr = To(to_email)
            subject_obj = Subject(subject)
            
            mail = Mail(
                from_email=from_addr,
                to_emails=to_addr,
                subject=subject_obj
            )
            
            # Add content
            if plain_content:
                mail.content = PlainTextContent(plain_content)
            
            if html_content:
                if plain_content:
                    mail.add_content(HtmlContent(html_content))
                else:
                    mail.content = HtmlContent(html_content)
            
            # Add attachments
            if attachments:
                for attachment_data in attachments:
                    attachment = cls._create_attachment(attachment_data)
                    if attachment:
                        mail.add_attachment(attachment)
            
            # Add custom arguments for tracking
            if custom_args:
                for key, value in custom_args.items():
                    mail.custom_arg = {key: value}
            
            # Add tracking settings
            mail.tracking_settings = {
                'click_tracking': {'enable': True},
                'open_tracking': {'enable': True},
                'subscription_tracking': {'enable': False}
            }
            
            # Send email
            response = cls._client.send(mail)
            
            logger.info(f"Email sent successfully - Status: {response.status_code}")
            
            return {
                'success': True,
                'status_code': response.status_code,
                'message_id': response.headers.get('X-Message-Id'),
                'to_email': to_email,
                'subject': subject,
                'response_body': response.body,
                'response_headers': dict(response.headers)
            }
            
        except Exception as e:
            logger.error(f"SendGrid email send failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'SEND_ERROR'
            }
    
    @classmethod
    def send_template_email(cls, to_email: str, template_id: str, 
                           dynamic_data: Dict[str, Any], from_email: str = None,
                           from_name: str = None, custom_args: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Send email using SendGrid template.
        
        Args:
            to_email: Recipient email address
            template_id: SendGrid template ID
            dynamic_data: Template variables
            from_email: Sender email (uses default if not provided)
            from_name: Sender name (uses default if not provided)
            custom_args: Custom tracking arguments
            
        Returns:
            Dictionary with delivery status and details
        """
        if not cls._initialized:
            cls.initialize()
        
        if not cls._client:
            return {
                'success': False,
                'error': 'SendGrid not configured',
                'error_code': 'CONFIG_ERROR'
            }
        
        try:
            # Use default sender if not provided
            if not from_email:
                from_email = cls._default_from_email
                if not from_email:
                    return {
                        'success': False,
                        'error': 'No sender email configured',
                        'error_code': 'CONFIG_ERROR'
                    }
            
            if not from_name:
                from_name = cls._default_from_name
            
            # Create mail object with template
            mail = Mail(
                from_email=From(from_email, from_name),
                to_emails=To(to_email)
            )
            
            # Set template ID and dynamic data
            mail.template_id = TemplateId(template_id)
            mail.dynamic_template_data = DynamicTemplateData(dynamic_data)
            
            # Add custom arguments for tracking
            if custom_args:
                for key, value in custom_args.items():
                    mail.custom_arg = {key: value}
            
            # Add tracking settings
            mail.tracking_settings = {
                'click_tracking': {'enable': True},
                'open_tracking': {'enable': True},
                'subscription_tracking': {'enable': False}
            }
            
            # Send email
            response = cls._client.send(mail)
            
            logger.info(f"Template email sent successfully - Status: {response.status_code}")
            
            return {
                'success': True,
                'status_code': response.status_code,
                'message_id': response.headers.get('X-Message-Id'),
                'to_email': to_email,
                'template_id': template_id,
                'response_body': response.body,
                'response_headers': dict(response.headers)
            }
            
        except Exception as e:
            logger.error(f"SendGrid template email send failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'TEMPLATE_SEND_ERROR'
            }
    
    @classmethod
    def send_bulk_email(cls, recipients: List[Dict[str, Any]], template_id: str,
                       from_email: str = None, from_name: str = None) -> Dict[str, Any]:
        """
        Send bulk email using SendGrid template.
        
        Args:
            recipients: List of recipient dictionaries with email and dynamic_data
            template_id: SendGrid template ID
            from_email: Sender email (uses default if not provided)
            from_name: Sender name (uses default if not provided)
            
        Returns:
            Dictionary with bulk send status and details
        """
        if not cls._initialized:
            cls.initialize()
        
        if not cls._client:
            return {
                'success': False,
                'error': 'SendGrid not configured',
                'error_code': 'CONFIG_ERROR'
            }
        
        try:
            # Use default sender if not provided
            if not from_email:
                from_email = cls._default_from_email
                if not from_email:
                    return {
                        'success': False,
                        'error': 'No sender email configured',
                        'error_code': 'CONFIG_ERROR'
                    }
            
            if not from_name:
                from_name = cls._default_from_name
            
            # Prepare recipient list
            to_emails = []
            for recipient in recipients:
                to_email = To(
                    email=recipient['email'],
                    dynamic_template_data=recipient.get('dynamic_data', {})
                )
                to_emails.append(to_email)
            
            # Create mail object for bulk send
            mail = Mail(
                from_email=From(from_email, from_name),
                to_emails=to_emails
            )
            
            # Set template ID
            mail.template_id = TemplateId(template_id)
            
            # Add tracking settings
            mail.tracking_settings = {
                'click_tracking': {'enable': True},
                'open_tracking': {'enable': True},
                'subscription_tracking': {'enable': False}
            }
            
            # Send bulk email
            response = cls._client.send(mail)
            
            logger.info(f"Bulk email sent successfully - Status: {response.status_code}, Recipients: {len(recipients)}")
            
            return {
                'success': True,
                'status_code': response.status_code,
                'message_id': response.headers.get('X-Message-Id'),
                'recipient_count': len(recipients),
                'template_id': template_id,
                'response_body': response.body,
                'response_headers': dict(response.headers)
            }
            
        except Exception as e:
            logger.error(f"SendGrid bulk email send failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'BULK_SEND_ERROR'
            }
    
    @classmethod
    def _create_attachment(cls, attachment_data: Dict[str, Any]) -> Optional[Attachment]:
        """
        Create SendGrid attachment object.
        
        Args:
            attachment_data: Dictionary with attachment details
            
        Returns:
            SendGrid Attachment object or None if invalid
        """
        try:
            file_content = attachment_data.get('content')
            file_name = attachment_data.get('filename')
            file_type = attachment_data.get('type')
            
            if not all([file_content, file_name]):
                return None
            
            # Encode file content if not already base64
            if isinstance(file_content, bytes):
                encoded_content = base64.b64encode(file_content).decode()
            elif isinstance(file_content, str):
                encoded_content = file_content
            else:
                return None
            
            # Determine file type if not provided
            if not file_type:
                file_type, _ = mimetypes.guess_type(file_name)
                if not file_type:
                    file_type = 'application/octet-stream'
            
            attachment = Attachment(
                FileContent(encoded_content),
                FileName(file_name),
                FileType(file_type),
                Disposition('attachment')
            )
            
            return attachment
            
        except Exception as e:
            logger.error(f"Create attachment failed: {str(e)}")
            return None
    
    @classmethod
    def get_delivery_stats(cls, start_date: str, end_date: str = None) -> Dict[str, Any]:
        """
        Get email delivery statistics from SendGrid.
        
        Args:
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            
        Returns:
            Dictionary with delivery statistics
        """
        if not cls._initialized:
            cls.initialize()
        
        if not cls._client:
            return {
                'success': False,
                'error': 'SendGrid not configured'
            }
        
        try:
            # Prepare query parameters
            params = {
                'start_date': start_date,
                'aggregated_by': 'day'
            }
            
            if end_date:
                params['end_date'] = end_date
            
            # Get stats from SendGrid
            response = cls._client.stats.get(query_params=params)
            
            if response.status_code == 200:
                stats_data = response.body
                
                return {
                    'success': True,
                    'stats': stats_data,
                    'period': {
                        'start_date': start_date,
                        'end_date': end_date
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f'API returned status {response.status_code}',
                    'error_code': 'API_ERROR'
                }
                
        except Exception as e:
            logger.error(f"Get delivery stats failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'STATS_ERROR'
            }
    
    @classmethod
    def validate_email(cls, email: str) -> Dict[str, Any]:
        """
        Validate email address using SendGrid validation API.
        
        Args:
            email: Email address to validate
            
        Returns:
            Dictionary with validation result
        """
        if not cls._initialized:
            cls.initialize()
        
        if not cls._client:
            return {
                'success': False,
                'error': 'SendGrid not configured'
            }
        
        try:
            # Use SendGrid email validation API
            response = cls._client.validations.email.post(
                request_body={'email': email}
            )
            
            if response.status_code == 200:
                validation_data = response.body
                
                return {
                    'success': True,
                    'email': email,
                    'validation_result': validation_data
                }
            else:
                return {
                    'success': False,
                    'error': f'Validation API returned status {response.status_code}',
                    'error_code': 'VALIDATION_ERROR'
                }
                
        except Exception as e:
            logger.error(f"Email validation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'VALIDATION_ERROR'
            }
    
    @classmethod
    def create_contact(cls, email: str, first_name: str = None, 
                      last_name: str = None, custom_fields: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create contact in SendGrid for marketing campaigns.
        
        Args:
            email: Contact email address
            first_name: Contact first name
            last_name: Contact last name
            custom_fields: Custom field values
            
        Returns:
            Dictionary with contact creation result
        """
        if not cls._initialized:
            cls.initialize()
        
        if not cls._client:
            return {
                'success': False,
                'error': 'SendGrid not configured'
            }
        
        try:
            # Prepare contact data
            contact_data = {
                'email': email
            }
            
            if first_name:
                contact_data['first_name'] = first_name
            if last_name:
                contact_data['last_name'] = last_name
            if custom_fields:
                contact_data.update(custom_fields)
            
            # Create contact
            response = cls._client.marketing.contacts.put(
                request_body={'contacts': [contact_data]}
            )
            
            if response.status_code in [200, 202]:
                return {
                    'success': True,
                    'contact_data': contact_data,
                    'job_id': response.body.get('job_id')
                }
            else:
                return {
                    'success': False,
                    'error': f'Contact creation API returned status {response.status_code}',
                    'error_code': 'CONTACT_ERROR'
                }
                
        except Exception as e:
            logger.error(f"Contact creation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'CONTACT_ERROR'
            }
    
    @classmethod
    def unsubscribe_contact(cls, email: str) -> Dict[str, Any]:
        """
        Add email to global unsubscribe list.
        
        Args:
            email: Email address to unsubscribe
            
        Returns:
            Dictionary with unsubscribe result
        """
        if not cls._initialized:
            cls.initialize()
        
        if not cls._client:
            return {
                'success': False,
                'error': 'SendGrid not configured'
            }
        
        try:
            # Add to global unsubscribe list
            response = cls._client.asm.global_unsubscribes.post(
                request_body={'recipient_emails': [email]}
            )
            
            if response.status_code in [201, 200]:
                return {
                    'success': True,
                    'email': email,
                    'unsubscribed': True
                }
            else:
                return {
                    'success': False,
                    'error': f'Unsubscribe API returned status {response.status_code}',
                    'error_code': 'UNSUBSCRIBE_ERROR'
                }
                
        except Exception as e:
            logger.error(f"Email unsubscribe failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'UNSUBSCRIBE_ERROR'
            }


# Initialize SendGrid on module load
try:
    SendGridService.initialize()
except Exception as e:
    logger.error(f"SendGrid initialization failed on import: {str(e)}")
    # Don't raise exception on import to allow application to start