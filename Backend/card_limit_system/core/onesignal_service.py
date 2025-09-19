"""
OneSignal API integration for push notifications.

Provides comprehensive push notification delivery with
segmentation, scheduling, and analytics tracking.
"""

import requests
import json
import logging
from typing import Optional, Dict, Any, List
from django.conf import settings
from django.core.cache import cache
import time

logger = logging.getLogger(__name__)


class OneSignalService:
    """
    Service for OneSignal push notification operations.
    
    Handles push notification delivery, user management,
    and analytics with proper error handling and retry logic.
    """
    
    _app_id = None
    _rest_api_key = None
    _user_auth_key = None
    _base_url = "https://onesignal.com/api/v1"
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Initialize OneSignal configuration."""
        if cls._initialized:
            return
        
        try:
            # Get OneSignal credentials from settings
            cls._app_id = getattr(settings, 'ONESIGNAL_APP_ID', None)
            cls._rest_api_key = getattr(settings, 'ONESIGNAL_REST_API_KEY', None)
            cls._user_auth_key = getattr(settings, 'ONESIGNAL_USER_AUTH_KEY', None)
            
            if cls._app_id and cls._rest_api_key:
                cls._initialized = True
                logger.info("OneSignal service initialized successfully")
            else:
                logger.warning("OneSignal credentials not configured")
                
        except Exception as e:
            logger.error(f"OneSignal initialization failed: {str(e)}")
            raise
    
    @classmethod
    def _make_request(cls, method: str, endpoint: str, data: Dict[str, Any] = None,
                     use_user_auth: bool = False) -> Dict[str, Any]:
        """
        Make HTTP request to OneSignal API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request payload
            use_user_auth: Whether to use user auth key instead of REST API key
            
        Returns:
            Dictionary with response data
        """
        if not cls._initialized:
            cls.initialize()
        
        if not cls._app_id or not cls._rest_api_key:
            return {
                'success': False,
                'error': 'OneSignal not configured'
            }
        
        try:
            url = f"{cls._base_url}/{endpoint}"
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Basic {cls._user_auth_key if use_user_auth else cls._rest_api_key}'
            }
            
            # Make request
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            # Parse response
            if response.status_code in [200, 201, 202]:
                return {
                    'success': True,
                    'data': response.json() if response.content else {},
                    'status_code': response.status_code
                }
            else:
                error_data = response.json() if response.content else {}
                logger.error(f"OneSignal API error: {response.status_code} - {error_data}")
                return {
                    'success': False,
                    'error': error_data.get('errors', [response.text]),
                    'status_code': response.status_code
                }
                
        except requests.exceptions.Timeout:
            logger.error("OneSignal API request timeout")
            return {
                'success': False,
                'error': 'Request timeout',
                'error_code': 'TIMEOUT'
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"OneSignal API request failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'REQUEST_ERROR'
            }
        except Exception as e:
            logger.error(f"OneSignal request error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'UNKNOWN_ERROR'
            }
    
    @classmethod
    def send_notification(cls, player_ids: List[str] = None, segments: List[str] = None,
                         title: str = None, message: str = None, data: Dict[str, Any] = None,
                         url: str = None, icon: str = None, large_icon: str = None,
                         image: str = None, scheduled_at: str = None,
                         filters: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send push notification via OneSignal.
        
        Args:
            player_ids: List of specific player IDs to target
            segments: List of segments to target
            title: Notification title
            message: Notification message
            data: Custom data payload
            url: URL to open when notification is clicked
            icon: Small notification icon URL
            large_icon: Large notification icon URL
            image: Big picture URL for rich notifications
            scheduled_at: UTC datetime string for scheduled delivery
            filters: Advanced targeting filters
            
        Returns:
            Dictionary with notification send result
        """
        if not cls._initialized:
            cls.initialize()
        
        try:
            # Build notification payload
            notification_data = {
                'app_id': cls._app_id,
            }
            
            # Targeting
            if player_ids:
                notification_data['include_player_ids'] = player_ids
            elif segments:
                notification_data['included_segments'] = segments
            elif filters:
                notification_data['filters'] = filters
            else:
                # Default to all users
                notification_data['included_segments'] = ['All']
            
            # Content
            if title:
                notification_data['headings'] = {'en': title}
            if message:
                notification_data['contents'] = {'en': message}
            
            # Additional data
            if data:
                notification_data['data'] = data
            
            # Media and styling
            if url:
                notification_data['url'] = url
            if icon:
                notification_data['small_icon'] = icon
            if large_icon:
                notification_data['large_icon'] = large_icon
            if image:
                notification_data['big_picture'] = image
            
            # Scheduling
            if scheduled_at:
                notification_data['send_after'] = scheduled_at
            
            # Send notification
            response = cls._make_request('POST', 'notifications', notification_data)
            
            if response['success']:
                notification_id = response['data'].get('id')
                logger.info(f"OneSignal notification sent - ID: {notification_id}")
                
                return {
                    'success': True,
                    'notification_id': notification_id,
                    'recipients': response['data'].get('recipients', 0),
                    'external_id': response['data'].get('external_id'),
                    'data': response['data']
                }
            else:
                return response
                
        except Exception as e:
            logger.error(f"OneSignal send notification failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'SEND_ERROR'
            }
    
    @classmethod
    def send_to_user(cls, user_id: str, title: str, message: str,
                    data: Dict[str, Any] = None, url: str = None) -> Dict[str, Any]:
        """
        Send notification to specific user by external user ID.
        
        Args:
            user_id: External user ID (typically customer ID)
            title: Notification title
            message: Notification message
            data: Custom data payload
            url: URL to open when notification is clicked
            
        Returns:
            Dictionary with notification send result
        """
        try:
            # Use filters to target specific external user ID
            filters = [
                {
                    'field': 'tag',
                    'key': 'user_id',
                    'relation': '=',
                    'value': user_id
                }
            ]
            
            return cls.send_notification(
                filters=filters,
                title=title,
                message=message,
                data=data,
                url=url
            )
            
        except Exception as e:
            logger.error(f"OneSignal send to user failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'SEND_TO_USER_ERROR'
            }
    
    @classmethod
    def send_to_segment(cls, segment_name: str, title: str, message: str,
                       data: Dict[str, Any] = None, url: str = None) -> Dict[str, Any]:
        """
        Send notification to user segment.
        
        Args:
            segment_name: OneSignal segment name
            title: Notification title
            message: Notification message
            data: Custom data payload
            url: URL to open when notification is clicked
            
        Returns:
            Dictionary with notification send result
        """
        try:
            return cls.send_notification(
                segments=[segment_name],
                title=title,
                message=message,
                data=data,
                url=url
            )
            
        except Exception as e:
            logger.error(f"OneSignal send to segment failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'SEND_TO_SEGMENT_ERROR'
            }
    
    @classmethod
    def get_notification_status(cls, notification_id: str) -> Dict[str, Any]:
        """
        Get notification delivery status and statistics.
        
        Args:
            notification_id: OneSignal notification ID
            
        Returns:
            Dictionary with notification status and stats
        """
        try:
            response = cls._make_request(
                'GET',
                f'notifications/{notification_id}?app_id={cls._app_id}'
            )
            
            if response['success']:
                notification_data = response['data']
                
                return {
                    'success': True,
                    'notification_id': notification_id,
                    'successful': notification_data.get('successful', 0),
                    'failed': notification_data.get('failed', 0),
                    'errored': notification_data.get('errored', 0),
                    'converted': notification_data.get('converted', 0),
                    'remaining': notification_data.get('remaining', 0),
                    'queued_at': notification_data.get('queued_at'),
                    'send_after': notification_data.get('send_after'),
                    'completed_at': notification_data.get('completed_at'),
                    'data': notification_data
                }
            else:
                return response
                
        except Exception as e:
            logger.error(f"OneSignal get notification status failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'STATUS_ERROR'
            }
    
    @classmethod
    def cancel_notification(cls, notification_id: str) -> Dict[str, Any]:
        """
        Cancel scheduled notification.
        
        Args:
            notification_id: OneSignal notification ID
            
        Returns:
            Dictionary with cancellation result
        """
        try:
            response = cls._make_request(
                'DELETE',
                f'notifications/{notification_id}?app_id={cls._app_id}'
            )
            
            if response['success']:
                logger.info(f"OneSignal notification cancelled - ID: {notification_id}")
                return {
                    'success': True,
                    'notification_id': notification_id,
                    'cancelled': True
                }
            else:
                return response
                
        except Exception as e:
            logger.error(f"OneSignal cancel notification failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'CANCEL_ERROR'
            }
    
    @classmethod
    def create_player(cls, device_token: str, device_type: int, user_id: str = None,
                     tags: Dict[str, Any] = None, language: str = 'en') -> Dict[str, Any]:
        """
        Create/register a new player (device) in OneSignal.
        
        Args:
            device_token: Device token for push notifications
            device_type: Device type (1=iOS, 2=Android, 3=Amazon, 4=Chrome, etc.)
            user_id: External user ID (customer ID)
            tags: Custom tags for targeting
            language: Device language
            
        Returns:
            Dictionary with player creation result
        """
        try:
            player_data = {
                'app_id': cls._app_id,
                'device_token': device_token,
                'device_type': device_type,
                'language': language
            }
            
            if user_id:
                player_data['external_user_id'] = user_id
                # Also add as tag for easier filtering
                if not tags:
                    tags = {}
                tags['user_id'] = user_id
            
            if tags:
                player_data['tags'] = tags
            
            response = cls._make_request('POST', 'players', player_data)
            
            if response['success']:
                player_id = response['data'].get('id')
                logger.info(f"OneSignal player created - ID: {player_id}")
                
                return {
                    'success': True,
                    'player_id': player_id,
                    'device_token': device_token,
                    'user_id': user_id,
                    'data': response['data']
                }
            else:
                return response
                
        except Exception as e:
            logger.error(f"OneSignal create player failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'CREATE_PLAYER_ERROR'
            }
    
    @classmethod
    def update_player(cls, player_id: str, device_token: str = None,
                     user_id: str = None, tags: Dict[str, Any] = None,
                     language: str = None) -> Dict[str, Any]:
        """
        Update existing player in OneSignal.
        
        Args:
            player_id: OneSignal player ID
            device_token: Updated device token
            user_id: External user ID
            tags: Updated tags
            language: Updated language
            
        Returns:
            Dictionary with player update result
        """
        try:
            update_data = {}
            
            if device_token:
                update_data['device_token'] = device_token
            if user_id:
                update_data['external_user_id'] = user_id
            if tags:
                update_data['tags'] = tags
            if language:
                update_data['language'] = language
            
            if not update_data:
                return {
                    'success': False,
                    'error': 'No update data provided',
                    'error_code': 'NO_DATA'
                }
            
            response = cls._make_request('PUT', f'players/{player_id}', update_data)
            
            if response['success']:
                logger.info(f"OneSignal player updated - ID: {player_id}")
                return {
                    'success': True,
                    'player_id': player_id,
                    'updated': True,
                    'data': response['data']
                }
            else:
                return response
                
        except Exception as e:
            logger.error(f"OneSignal update player failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'UPDATE_PLAYER_ERROR'
            }
    
    @classmethod
    def get_player(cls, player_id: str) -> Dict[str, Any]:
        """
        Get player information from OneSignal.
        
        Args:
            player_id: OneSignal player ID
            
        Returns:
            Dictionary with player information
        """
        try:
            response = cls._make_request('GET', f'players/{player_id}?app_id={cls._app_id}')
            
            if response['success']:
                player_data = response['data']
                
                return {
                    'success': True,
                    'player_id': player_id,
                    'device_token': player_data.get('identifier'),
                    'device_type': player_data.get('device_type'),
                    'external_user_id': player_data.get('external_user_id'),
                    'tags': player_data.get('tags', {}),
                    'language': player_data.get('language'),
                    'timezone': player_data.get('timezone'),
                    'country': player_data.get('country'),
                    'last_active': player_data.get('last_active'),
                    'created_at': player_data.get('created_at'),
                    'data': player_data
                }
            else:
                return response
                
        except Exception as e:
            logger.error(f"OneSignal get player failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'GET_PLAYER_ERROR'
            }
    
    @classmethod
    def delete_player(cls, player_id: str) -> Dict[str, Any]:
        """
        Delete player from OneSignal.
        
        Args:
            player_id: OneSignal player ID
            
        Returns:
            Dictionary with deletion result
        """
        try:
            response = cls._make_request(
                'DELETE',
                f'players/{player_id}?app_id={cls._app_id}'
            )
            
            if response['success']:
                logger.info(f"OneSignal player deleted - ID: {player_id}")
                return {
                    'success': True,
                    'player_id': player_id,
                    'deleted': True
                }
            else:
                return response
                
        except Exception as e:
            logger.error(f"OneSignal delete player failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'DELETE_PLAYER_ERROR'
            }
    
    @classmethod
    def get_app_stats(cls) -> Dict[str, Any]:
        """
        Get application statistics from OneSignal.
        
        Returns:
            Dictionary with application statistics
        """
        try:
            response = cls._make_request('GET', f'apps/{cls._app_id}', use_user_auth=True)
            
            if response['success']:
                app_data = response['data']
                
                return {
                    'success': True,
                    'app_id': cls._app_id,
                    'players': app_data.get('players', 0),
                    'messageable_players': app_data.get('messageable_players', 0),
                    'updated_at': app_data.get('updated_at'),
                    'created_at': app_data.get('created_at'),
                    'data': app_data
                }
            else:
                return response
                
        except Exception as e:
            logger.error(f"OneSignal get app stats failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'STATS_ERROR'
            }


# Initialize OneSignal on module load
try:
    OneSignalService.initialize()
except Exception as e:
    logger.error(f"OneSignal initialization failed on import: {str(e)}")
    # Don't raise exception on import to allow application to start