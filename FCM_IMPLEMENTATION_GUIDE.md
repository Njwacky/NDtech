# FCM (Firebase Cloud Messaging) Implementation Guide

This guide explains how to use the FCM push notification system that has been integrated into futurePOS.

## 🚀 Overview

The futurePOS system now includes complete FCM (Firebase Cloud Messaging) integration for sending push notifications to users. This allows real-time notifications for:

- Low stock alerts
- Cashier requests
- System notifications
- Price change notifications to customers
- Custom notifications

## 🔑 Configuration

### FCM API Key
The system is configured with your provided FCM API key:
```
API Key: AIzaSyABApzh-74Kr5oOz_kv_M8mlJa33TCadPA
```

### Settings Added
The following settings have been added to `confige/settings.py`:
- `FCM_API_KEY`: Your Firebase API key
- Logging configuration for FCM notifications

## 📱 Database Model

### FCMToken Model
A new `FCMToken` model has been created to store user FCM tokens:
- Links to Django User model
- Stores device token, device type, and device ID
- Tracks token creation and last used timestamps
- Supports web, Android, and iOS devices

### Model Fields
- `user`: Foreign key to User
- `token`: Unique FCM token string
- `device_id`: Optional device identifier
- `device_type`: Device type (web/android/ios)
- `is_active`: Token active status
- `created_at`: Token registration time
- `last_used`: Last time token was used

## 🔌 API Endpoints

### Token Management
- `POST /api/fcm/register/` - Register FCM token
- `POST /api/fcm/unregister/` - Unregister FCM token
- `GET /api/fcm/tokens/` - Get user's tokens

### Notification Sending
- `POST /api/fcm/test/` - Send test notification
- `POST /api/fcm/price-change/` - Send price change notification
- `GET /api/fcm/test-connection/` - Test FCM connection

### Token Viewing
- `GET /api/fcm/tokens/` - List user's registered tokens with status

## 🎯 Features

### Notification Types Supported
1. **Low Stock Alerts**: Sent to admins/managers when products have low stock
2. **Cashier Requests**: Sent to admins/managers when cashiers need assistance
3. **Price Change Notifications**: Sent to customers about price changes
4. **Test Notifications**: For testing and debugging
5. **System Alerts**: General system notifications

### Message Format for Price Changes
The system sends price change notifications in this format:
```
"Hello [customer_name], [item_name] now costs R[new_price]. Change: R[price_change]"
```

Example:
```
"Hello John Doe, Coca Cola 2L now costs R25.99. Change: R2.50"
```

## 🧪 Testing

### Test Page
A comprehensive test page is available at `/test/fcm/` with:
- FCM token registration
- Test notification sending
- Price change notification testing
- FCM connection testing
- Token management viewing

### Test Features
- Register multiple device tokens
- Send custom test notifications
- Test price change notifications with sample data
- View all registered tokens
- Monitor FCM connection status

## 📱 Client Integration

### Web Integration
For web browsers, the system supports:
- Service Worker registration
- Push notification display
- Background sync
- Offline notification handling

### Required JavaScript
```javascript
// Register FCM token
await fetch('/api/fcm/register/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({
        token: 'user_fcm_token_here',
        device_type: 'web',
        device_id: 'optional_device_id'
    })
});

// Listen for push notifications
self.addEventListener('push', function(event) {
    const notification = event.data;
    // Handle notification display
});
```

### Mobile Integration
For mobile apps (React Native, Flutter, etc.):
1. Get FCM token from Firebase SDK
2. Register token with `/api/fcm/register/`
3. Handle incoming push notifications
4. Update token when it changes

## 🔧 Development

### Adding New Notification Types
To add a new notification type:
1. Add the type to `Notification.NOTIFICATION_TYPES` in `nano/models.py`
2. Update the `send_fcm_for_notification` function in `nano/fcm_service.py`
3. Handle the new type in your notification creation logic

### Custom Notification Data
You can include custom data payloads:
```python
# In notification creation
notification = Notification.objects.create(
    title="Custom Alert",
    message="Your custom message",
    notification_type='custom_type',
    request_data={
        'custom_field': 'custom_value',
        'priority': 'high'
    }
)

# This data will be included in FCM payload
```

## 📊 Monitoring

### Logging
FCM notifications are logged to:
- `fcm_notifications.log` file
- Django admin interface
- Console output for debugging

### Log Format
```
[2024-01-01 12:00:00] INFO: FCM notification sent successfully to token: abc123...
[2024-01-01 12:00:00] ERROR: FCM notification failed: InvalidRegistration
```

### Error Handling
The system includes comprehensive error handling:
- Network timeouts
- Invalid tokens
- Rate limiting
- Server errors
- Token cleanup for invalid/expired tokens

## 🔒 Security

### Token Security
- Tokens are stored securely in database
- CSRF protection on all endpoints
- Token validation and sanitization
- Automatic cleanup of invalid tokens

### Authentication
All FCM endpoints require:
- User authentication (login required)
- Valid CSRF token
- Proper user permissions

## 🚀 Production Deployment

### Environment Variables
For production deployment, set these environment variables:
```bash
FCM_API_KEY=your_production_fcm_api_key
FCM_SENDER_ID=your_fcm_sender_id
FCM_PROJECT_ID=your_fcm_project_id
```

### Security Considerations
- Use HTTPS in production
- Validate FCM API key
- Implement rate limiting
- Monitor for abuse
- Regular token cleanup

## 📚 Usage Examples

### Sending Low Stock Notification
```python
from nano.fcm_service import send_fcm_notification_to_user

# Send to specific user
success = send_fcm_notification_to_user(
    user=admin_user,
    title="Low Stock Alert",
    message="Product XYZ has only 5 units remaining",
    data={
        'product_id': product.id,
        'stock_level': product.stock
    }
)
```

### Sending Price Change Notification
```python
from nano.fcm_service import fcm_service

success = fcm_service.send_price_change_notification(
    customer_name="John Doe",
    item
