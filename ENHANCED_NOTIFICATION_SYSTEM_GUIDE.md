# Enhanced Notification System Guide

## Overview

The notification system has been enhanced with smart redirect functionality and improved notification count display. This guide explains the new features and how they work.

## New Features Implemented

### 1. Smart Notification Type Detection

The system now automatically detects different types of notifications and handles them appropriately:

#### Password-Related Notifications
- **Detection**: Identifies notifications with keywords like 'password', 'pwd', 'reset', 'change password'
- **Redirect**: Takes user directly to the edit user page for the specific user
- **Button**: Shows "Edit User" button with orange styling

#### Low Stock Notifications
- **Detection**: Identifies notifications with keywords like 'low stock', 'stock alert', 'running low', 'inventory'
- **Redirect**: Takes user to the Add Stock page (`/add_stock/`)
- **Button**: Shows "Add Stock" button with green styling

#### Suggestion Notifications
- **Detection**: Identifies notifications with keywords like 'suggestion', 'info', 'fyi', 'for your information', 'sent successfully'
- **Redirect**: No redirect - just marks as read
- **Button**: No action button shown (only dismiss button)

### 2. Enhanced Notification Badge

The notification bell icon now displays:
- **Count**: Shows exact number of unread notifications
- **Large Numbers**: Shows "99+" for counts over 99
- **Tooltip**: Hover shows full count with proper grammar ("1 notification" vs "2 notifications")
- **Dynamic**: Updates in real-time as notifications are read/dismissed

### 3. Contextual Action Buttons

Different notification types show different action buttons:

| Notification Type | Action Button | Redirect Destination | Color |
|------------------|----------------|---------------------|-------|
| Password Reset | "Edit User" | `/edit_user/{user_id}/` | Orange (#ff6b35) |
| Low Stock | "Add Stock" | `/add_stock/` | Green (#28a745) |
| Suggestions | None (just mark as read) | None | N/A |
| Other | "Mark as read" | None | Blue (#28a745) |

## Technical Implementation

### Files Modified

#### 1. `nano/static/nano/notifications.js`
Enhanced with:
- `isLowStockNotification()` - Detects low stock notifications
- `isSuggestionNotification()` - Detects suggestion notifications  
- `handleNotificationAction()` - Handles redirects based on notification type
- Enhanced `updateBadge()` - Shows count with tooltip

#### 2. `nano/templates/nano/notifications_page.html`
Enhanced with:
- New action buttons for different notification types
- CSS styling for "Add Stock" button
- Smart button display logic
- Enhanced notification type detection methods

### Key Methods

#### Notification Detection Methods

```javascript
// Password notification detection
isPasswordRelatedNotification(notification) {
    // Checks notification_type, request_type, and content keywords
    // Returns true for password-related notifications
}

// Low stock notification detection  
isLowStockNotification(notification) {
    // Checks notification_type and content keywords
    // Returns true for low stock notifications
}

// Suggestion notification detection
isSuggestionNotification(notification) {
    // Checks for confirmation/info notifications
    // Returns true for suggestions (no action needed)
}
```

#### Action Handling

```javascript
// Main action handler
handleNotificationAction(notificationId) {
    // 1. Marks notification as read
    // 2. Determines notification type
    // 3. Redirects to appropriate page:
    //    - Password: /edit_user/{user_id}/
    //    - Low Stock: /add_stock/
    //    - Suggestions: No redirect
    //    - Other: /notifications_page/
}
```

#### Badge Enhancement

```javascript
// Enhanced badge with count and tooltip
updateBadge() {
    // Shows exact count or "99+"
    // Adds hover tooltip with full count
    // Handles both desktop and mobile badges
    // Updates display: flex/none based on count
}
```

## User Experience

### Notification Bell Behavior

1. **No unread notifications**: Badge hidden
2. **1-99 unread notifications**: Badge shows exact number
3. **100+ unread notifications**: Badge shows "99+"
4. **Hover**: Shows tooltip with full count and proper grammar

### Notification Page Behavior

1. **Password notifications**: Show orange "Edit User" button
2. **Low stock notifications**: Show green "Add Stock" button  
3. **Suggestion notifications**: Only show dismiss button
4. **Click notification**: Opens detail modal with appropriate action

### Redirect Flow

1. **User clicks action button**
2. **Notification marked as read**
3. **Brief delay (500ms) for visual feedback**
4. **Redirect to appropriate page**

## Testing

### Test Script

Run the enhanced notification test:

```bash
python test_enhanced_notifications.py
```

This tests:
- API endpoints for notifications
- Notification type detection logic
- Redirect logic for different types
- Badge count functionality
- User lookup functionality

### Manual Testing Steps

1. **Start Django server**: `python manage.py runserver`
2. **Login as admin**: Access the system as an admin user
3. **Create notifications**: Use the floating message button or forgot password
4. **Test badge**: Verify count displays correctly
5. **Test redirects**: Click action buttons to verify redirects
6. **Test suggestions**: Verify suggestions don't redirect

## Notification Types and Examples

### Password Reset Example
```
Title: "Password Reset Request: johndoe"
Message: "Password reset requested for user: johndoe (john@example.com). Click to edit user and set new password."
Type: cashier_request
Request Type: password_reset
Action: Edit User → /edit_user/123/
```

### Low Stock Example
```
Title: "Low Stock Alert: Product Name"
Message: "Low stock alert: Product Name has only 5 units remaining"
Type: low_stock
Action: Add Stock → /add_stock/
```

### Suggestion Example
```
Title: "Message Sent: system_problem"
Message: "Your system_problem request has been sent to 1 admin(s)"
Type: system_alert
Request Type: message_confirmation
Action: Mark as read (no redirect)
```

## CSS Classes

### Button Styling
```css
.btn-edit-user { background: #ff6b35; color: white; }
.btn-add-stock { background: #28a745; color: white; }
.btn-mark-read { background: #28a745; color: white; }
.btn-dismiss { background: #dc3545; color: white; }
```

### Badge Styling
```css
.notification-badge {
    position: absolute;
    top: -8px;
    right: -8px;
    background: #dc3545;
    color: white;
    border-radius: 50%;
    min-width: 18px;
    height: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    font-weight: bold;
}
```

## API Endpoints

### Enhanced Endpoints

#### `/api/notifications/`
- **Method**: GET
- **Returns**: List of notifications with full details
- **Includes**: notification_type, request_type, created_by_id, request_data

#### `/api/notifications/{id}/read/`
- **Method**: POST  
- **Action**: Marks specific notification as read
- **Returns**: Success status

#### `/api/get_user_by_username/?username={username}`
- **Method**: GET
- **Action**: Finds user by username for password redirects
- **Returns**: User data including ID

## Troubleshooting

### Common Issues

1. **Badge not showing**
   - Check user is authenticated
   - Verify notifications exist
   - Check CSS is loading

2. **Redirect not working**
   - Verify notification type detection
   - Check user ID extraction
   - Test API endpoints

3. **Wrong button showing**
   - Check notification type matching
   - Verify keyword detection
   - Test different notification content

### Debugging

Add console logging to track notification handling:

```javascript
console.log('Notification type:', notification.notification_type);
console.log('Is password:', this.isPasswordRelatedNotification(notification));
console.log('Is low stock:', this.isLowStockNotification(notification));
console.log('Is suggestion:', this.isSuggestionNotification(notification));
```

## Future Enhancements

### Potential Improvements

1. **Batch Actions**: Select multiple notifications for bulk actions
2. **Notification Templates**: Predefined notification types with standard actions
3. **Custom Redirects**: User-configurable redirect destinations
4. **Notification Scheduling**: Delayed notification delivery
5. **Rich Content**: Support for HTML, images, and links in notifications

### Performance Considerations

1. **Caching**: Cache notification counts for better performance
2. **Lazy Loading**: Load notifications on demand
3. **Debouncing**: Prevent rapid API calls
4. **Optimistic Updates**: Update UI before server response

## Security

### Considerations

1. **CSRF Protection**: All API calls include CSRF tokens
2. **User Authorization**: Users can only access their own notifications
3. **Input Validation**: Sanitize notification content
4. **Rate Limiting**: Prevent notification spam

## Conclusion

The enhanced notification system provides:
- **Smart redirects** based on notification type
- **Improved UX** with contextual action buttons  
- **Better visibility** with notification counts
- **Intuitive handling** of different notification types

This creates a more efficient workflow where users can quickly take action on notifications without extra clicks or navigation steps.
