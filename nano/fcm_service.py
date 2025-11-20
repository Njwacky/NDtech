import json
import logging
from typing import Dict, List, Optional
from django.conf import settings
from django.contrib.auth.models import User
import requests
from .models import Notification

logger = logging.getLogger(__name__)

class FCMService:
    """Firebase Cloud Messaging Service for sending push notifications"""
    
    def __init__(self):
        self.api_key = settings.FCM_API_KEY
        self.fcm_url = "https://fcm.googleapis.com/fcm/send"
        self.headers = {
            'Authorization': f'key={self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def send_notification(self, 
                         title: str, 
                         message: str, 
                         token: str, 
                         data: Optional[Dict] = None,
                         notification_type: str = 'general') -> bool:
        """
        Send a push notification to a specific device token
        
        Args:
            title: Notification title
            message: Notification message
            token: FCM device token
            data: Additional data payload
            notification_type: Type of notification for categorization
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            payload = {
                'to': token,
                'notification': {
                    'title': title,
                    'body': message,
                    'sound': 'default',
                    'badge': '1'
                },
                'data': {
                    'type': notification_type,
                    'click_action': 'FLUTTER_NOTIFICATION_CLICK',
                    **(data or {})
                },
                'priority': 'high'
            }
            
            response = requests.post(
                self.fcm_url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success', 0) > 0:
                    logger.info(f"FCM notification sent successfully to token: {token[:10]}...")
                    return True
                else:
                    error = result.get('results', [{}])[0].get('error', 'Unknown error')
                    logger.error(f"FCM notification failed: {error}")
                    return False
            else:
                logger.error(f"FCM HTTP error: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"FCM request exception: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"FCM unexpected error: {str(e)}")
            return False
    
    def send_multicast_notification(self, 
                                   title: str, 
                                   message: str, 
                                   tokens: List[str], 
                                   data: Optional[Dict] = None,
                                   notification_type: str = 'general') -> Dict:
        """
        Send a push notification to multiple device tokens
        
        Args:
            title: Notification title
            message: Notification message
            tokens: List of FCM device tokens
            data: Additional data payload
            notification_type: Type of notification for categorization
            
        Returns:
            Dict: Results with success count, failure count, and details
        """
        if not tokens:
            return {'success': 0, 'failure': 0, 'results': []}
        
        try:
            payload = {
                'registration_ids': tokens,
                'notification': {
                    'title': title,
                    'body': message,
                    'sound': 'default',
                    'badge': '1'
                },
                'data': {
                    'type': notification_type,
                    'click_action': 'FLUTTER_NOTIFICATION_CLICK',
                    **(data or {})
                },
                'priority': 'high'
            }
            
            response = requests.post(
                self.fcm_url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                success_count = result.get('success', 0)
                failure_count = result.get('failure', 0)
                results = result.get('results', [])
                
                logger.info(f"FCM multicast: {success_count} success, {failure_count} failure out of {len(tokens)} tokens")
                
                return {
                    'success': success_count,
                    'failure': failure_count,
                    'results': results
                }
            else:
                logger.error(f"FCM multicast HTTP error: {response.status_code} - {response.text}")
                return {'success': 0, 'failure': len(tokens), 'results': []}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"FCM multicast request exception: {str(e)}")
            return {'success': 0, 'failure': len(tokens), 'results': []}
        except Exception as e:
            logger.error(f"FCM multicast unexpected error: {str(e)}")
            return {'success': 0, 'failure': len(tokens), 'results': []}
    
    def send_price_change_notification(self, 
                                     customer_name: str, 
                                     item_name: str, 
                                     new_price: float, 
                                     price_change: float, 
                                     token: str) -> bool:
        """
        Send price change notification to customer
        
        Args:
            customer_name: Name of the customer
            item_name: Name of the product
            new_price: New price of the product
            price_change: Amount of price change
            token: FCM device token
            
        Returns:
            bool: True if successful, False otherwise
        """
        title = "Price Update Alert"
        change_indicator = "↑" if price_change > 0 else "↓"
        message = f"Hello {customer_name}, {item_name} now costs R{new_price:.2f}. Change: {change_indicator}R{abs(price_change):.2f}"
        
        data = {
            'item_name': item_name,
            'new_price': str(new_price),
            'price_change': str(price_change),
            'customer_name': customer_name,
            'notification_type': 'price_change'
        }
        
        return self.send_notification(title, message, token, data, 'price_change')
    
    def send_low_stock_notification(self, 
                                  product_name: str, 
                                  stock_level: int, 
                                  tokens: List[str]) -> Dict:
        """
        Send low stock notification to admins/managers
        
        Args:
            product_name: Name of the product with low stock
            stock_level: Current stock level
            tokens: List of FCM device tokens for admins/managers
            
        Returns:
            Dict: Results with success and failure counts
        """
        title = "Low Stock Alert"
        message = f"Low stock alert: {product_name} has only {stock_level} units remaining"
        
        data = {
            'product_name': product_name,
            'stock_level': str(stock_level),
            'notification_type': 'low_stock'
        }
        
        return self.send_multicast_notification(title, message, tokens, data, 'low_stock')
    
    def send_cashier_request_notification(self, 
                                         requester_name: str, 
                                         request_type: str, 
                                         message: str, 
                                         tokens: List[str]) -> Dict:
        """
        Send cashier request notification to admins/managers
        
        Args:
            requester_name: Name of the cashier making the request
            request_type: Type of request
            message: Request message
            tokens: List of FCM device tokens for admins/managers
            
        Returns:
            Dict: Results with success and failure counts
        """
        title = f"Cashier Request: {request_type}"
        full_message = f"Request from {requester_name}: {message}"
        
        data = {
            'requester_name': requester_name,
            'request_type': request_type,
            'message': message,
            'notification_type': 'cashier_request'
        }
        
        return self.send_multicast_notification(title, full_message, tokens, data, 'cashier_request')
    
    def test_fcm_connection(self) -> bool:
        """
        Test FCM connection by sending a test notification to a dummy token
        
        Returns:
            bool: True if FCM service is accessible, False otherwise
        """
        try:
            # Send to an invalid token to test connectivity
            payload = {
                'to': 'invalid_test_token',
                'notification': {
                    'title': 'Test',
                    'body': 'Test message'
                },
                'priority': 'high'
            }
            
            response = requests.post(
                self.fcm_url,
                headers=self.headers,
                json=payload,
                timeout=5
            )
            
            # If we get a response (even error), FCM is accessible
            return response.status_code in [200, 400, 401, 403]
            
        except Exception as e:
            logger.error(f"FCM connection test failed: {str(e)}")
            return False

# Global FCM service instance
fcm_service = FCMService()

def send_fcm_notification_to_user(user: User, title: str, message: str, data: Optional[Dict] = None) -> bool:
    """
    Helper function to send FCM notification to a user
    
    Args:
        user: Django User object
        title: Notification title
        message: Notification message
        data: Additional data payload
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get user's FCM tokens
        tokens = get_user_fcm_tokens(user)
        
        if not tokens:
            logger.warning(f"No FCM tokens found for user: {user.username}")
            return False
        
        # Send to all tokens
        result = fcm_service.send_multicast_notification(title, message, tokens, data)
        
        # Remove invalid tokens
        if result['failure'] > 0:
            cleanup_invalid_tokens(user, tokens, result['results'])
        
        return result['success'] > 0
        
    except Exception as e:
        logger.error(f"Error sending FCM notification to user {user.username}: {str(e)}")
        return False

def get_user_fcm_tokens(user: User) -> List[str]:
    """
    Get all active FCM tokens for a user
    
    Args:
        user: Django User object
        
    Returns:
        List[str]: List of active FCM tokens
    """
    try:
        # This will be implemented after we add FCM token model
        from .models import FCMToken
        tokens = FCMToken.objects.filter(user=user, is_active=True).values_list('token', flat=True)
        return list(tokens)
    except ImportError:
        # FCMToken model doesn't exist yet
        logger.warning("FCMToken model not found - please run migrations")
        return []
    except Exception as e:
        logger.error(f"Error getting FCM tokens for user {user.username}: {str(e)}")
        return []

def cleanup_invalid_tokens(user: User, sent_tokens: List[str], results: List[Dict]):
    """
    Remove invalid FCM tokens based on FCM response
    
    Args:
        user: Django User object
        sent_tokens: List of tokens that were sent
        results: FCM response results
    """
    try:
        from .models import FCMToken
        
        for i, result in enumerate(results):
            if i < len(sent_tokens):
                token = sent_tokens[i]
                error = result.get('error')
                
                # Remove tokens for permanent errors
                if error in ['NotRegistered', 'InvalidRegistration']:
                    FCMToken.objects.filter(user=user, token=token).delete()
                    logger.info(f"Removed invalid FCM token for user {user.username}: {token[:10]}...")
                    
    except ImportError:
        logger.warning("FCMToken model not found - cannot cleanup invalid tokens")
    except Exception as e:
        logger.error(f"Error cleaning up invalid tokens: {str(e)}")
