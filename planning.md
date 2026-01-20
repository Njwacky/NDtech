# futurePOS - Application Planning & Architecture Documentation

## Project Overview

**futurePOS** is a Django-based Point of Sale (POS) system designed for retail and food ordering operations. It provides comprehensive inventory management, order processing, pricing analytics, and notification systems with multi-user role-based access control.

---

## Tech Stack

### Backend
- **Framework**: Django 4.0+
- **Database**: SQLite (persistent storage at repo root: `db.sqlite3`)
- **Server**: Gunicorn (production), Django development server (dev)
- **Web Server**: Nginx (reverse proxy)

### Frontend
- **Template Engine**: Django Template Language (DTL) with HTML5
- **Styling**: CSS3 with modern responsive design (Flexbox/CSS Grid)
- **JavaScript**: Vanilla JavaScript (ES6+) - **No Vue.js framework**
  - Custom classes for UI components (e.g., `BarcodeScanner`, `HamburgerMenu`)
  - Event-driven architecture for interactive features
  - DOM manipulation for real-time updates
- **Icons**: FontAwesome 6.0.0
- **Client-side Libraries**: Firebase SDK for push notifications

### Database Models
- **UserProfile**: Hierarchical user system with roles (admin, cashier, warehouse manager, etc.)
- **Product**: Inventory management with barcode tracking
- **Sale**: Transaction records with timestamp tracking
- **PendingOrder** / **CompletedOrder**: Order management
- **WarehousePrice** / **PriceComparison**: Competitive pricing analytics
- **Notification**: User notification system
- **FCMToken**: Firebase Cloud Messaging device tokens
- **DeviceConnection**: Device tracking and monitoring
- **ErrorLog**: Error tracking and debugging
- **UserActivity**: Activity logging and audit trails
- **AirtimeProduct** / **AirtimeSale** / **AirtimeRequest**: Mobile airtime sales module

---

## API Endpoints

### Authentication & User Management
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/sign_in/` | POST | User login |
| `/sign_up/` | POST | User registration |
| `/logout/` | GET | User logout |
| `/forgot_password/` | GET/POST | Password reset flow |
| `/create_user/` | GET/POST | Admin: Create new user |
| `/manage_users/` | GET | Admin: View all users |
| `/edit_user/<user_id>/` | GET/POST | Admin: Edit user details & password |
| `/delete_user/<user_id>/` | POST | Admin: Delete user |
| `/bulk_delete_users/` | POST | Admin: Delete multiple users |

### Inventory & Sales
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/add_stock/` | GET/POST | Add/manage inventory |
| `/manage_sales/` | GET | View sales history |
| `/api/get_product_by_barcode/` | POST | Quick product lookup |

### Order Management
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/pending_orders/` | GET | View pending orders |
| `/save_order/` | POST | Create new order |
| `/pending_orders/<order_id>/checkout/` | POST | Checkout order |
| `/pending_orders/<order_id>/complete/` | POST | Mark order complete |
| `/pending_orders/<order_id>/cancel/` | POST | Cancel order |
| `/completed_orders/` | GET | View completed orders |
| `/order_details/<order_id>/` | GET | Order details page |
| `/completed_order_details/<order_id>/` | GET | Completed order details |

### Notifications & Real-time
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/notifications/` | GET | Fetch all notifications |
| `/api/notifications/<id>/read/` | POST | Mark notification as read |
| `/api/notifications/<id>/dismiss/` | POST | Dismiss notification |
| `/api/cashier_request/` | POST | Create cashier assistance request |
| `/api/check_role/` | POST | Verify user permissions |
| `/api/check_low_stock/` | GET | Check inventory alerts |
| `/api/get_user_by_username/` | POST | Search users |

### Firebase Cloud Messaging (FCM)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/fcm/register/` | POST | Register device for push notifications |
| `/api/fcm/unregister/` | POST | Unregister device |
| `/api/fcm/test/` | POST | Send test notification |
| `/api/fcm/test-connection/` | GET | Check FCM connectivity |
| `/api/fcm/tokens/` | GET | List user's registered devices |
| `/api/fcm/price-change/` | POST | Send price update notifications |

### Warehouse & Pricing
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/warehouse/import/` | GET/POST | Import warehouse data |
| `/warehouse/prices/` | GET | View warehouse prices |
| `/warehouse/comparisons/` | GET | Price comparison analytics |
| `/warehouse/comparisons/marketing/` | GET | Marketing-focused pricing report |
| `/warehouse/run-comparison/` | POST | Execute price comparison analysis |
| `/warehouse/price-comparison-details/<id>/` | GET | Detailed comparison metrics |
| `/warehouse/sync/` | POST | Sync warehouse inventory |
| `/warehouse/export/prices/` | GET | Export prices to Excel |
| `/warehouse/export/comparisons/` | GET | Export comparison data |
| `/warehouse/export/marketing-report/` | GET | Export marketing report |
| `/warehouse/marketing-analytics-data/` | GET | Get analytics data for dashboard |
| `/api/warehouse/prices/` | GET/POST | API: Warehouse price management |

### UPC/Barcode Lookup
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/upc/lookup/` | GET | UPC lookup page |
| `/upc/lookup/<barcode>/` | GET | Detailed UPC information |
| `/upc/history/` | GET | Lookup history |
| `/upc/scanner/` | GET | Barcode scanner interface |
| `/api/upc/lookup/` | POST | API: Search UPC database |
| `/api/upc/lookup/<barcode>/` | GET | API: Get UPC details |

### Food Ordering Integration
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/food/scanner/` | GET | Food item scanner |
| `/food/menu/` | GET | Browse food menu |
| `/api/food/scanner/lookup/<barcode>/` | GET | Find food items by barcode |
| `/api/food/add-to-pos/` | POST | Add food item to POS order |

### Tracking & Monitoring
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/tracking/` | GET | Tracking dashboard |
| `/tracking/devices/` | GET | Device status monitoring |
| `/tracking/errors/` | GET | Error logs |
| `/tracking/errors/<id>/` | GET | Error details |
| `/tracking/errors/<id>/resolve/` | POST | Mark error resolved |
| `/tracking/activities/` | GET | User activity audit log |
| `/api/tracking/device/` | POST | Log device connection |
| `/api/tracking/activity/` | POST | Log user activity |
| `/api/tracking/error/` | POST | Report error |

### Airtime Management
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/airtime/` | GET | Airtime dashboard |
| `/airtime/management/` | GET | Manage airtime products |
| `/airtime/sales/` | GET | Airtime sales history |
| `/airtime/process/` | POST | Process airtime sale |
| `/airtime/sales/<id>/approve/` | POST | Approve pending sale |
| `/airtime/sales/<id>/reject/` | POST | Reject pending sale |
| `/airtime/requests/` | GET | Airtime restock requests |
| `/airtime/requests/<id>/approve/` | POST | Approve restock request |
| `/airtime/requests/<id>/reject/` | POST | Reject restock request |
| `/api/airtime/request/` | POST | Create restock request |

### Progressive Web App (PWA)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/sw.js` | GET | Service worker script |
| `/manifest.json` | GET | PWA manifest configuration |
| `/offline/` | GET | Offline fallback page |

### Export & Reports
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/export/products/excel/` | GET | Export inventory to Excel |

---

## Frontend Architecture

### UI/UX Design
- **Responsive Design**: Mobile-first approach using CSS Flexbox
- **Color Scheme**: Modern gradient backgrounds (purple/blue theme)
- **Navigation**: 
  - Sticky top navigation bar with hamburger menu for mobile
  - Breadcrumb navigation for sub-pages
  - Sidebar/dropdown menus for role-based features

### JavaScript Components & Modules

#### Core Classes
1. **BarcodeScanner** (`barcode_scanner.js`)
   - Handles barcode input events
   - Product lookup and validation
   - Real-time scan status updates

2. **HamburgerMenu** (`hamburger.js`)
   - Responsive mobile navigation
   - Toggle functionality
   - Accessibility features

3. **Notification System** (`home.js`)
   - Toast notifications
   - Floating message buttons
   - Notification polling

#### Key Features
- **Product Search**: Fetch by barcode or manual search
- **Order Management**: Add/remove items, quantity adjustment
- **Real-time Updates**: Live stock status, price changes
- **Excel Export**: Generate reports with openpyxl
- **Keyboard Shortcuts**: Support for power users

### Template System
- **Base Template**: `base.html` with common layout/scripts
- **Feature-specific Templates**: 
  - Order management (`pending_orders.html`, `checkout_order.html`)
  - Inventory (`add_stock.html`, `warehouse_import.html`)
  - Reports (`price_comparisons.html`, `price_comparisons_marketing.html`)
  - Admin (`manage_users.html`, `create_user.html`)
  - Notifications & Tracking (`notifications_page.html`, `tracking_dashboard.html`)

---

## Security Measures

### Authentication & Authorization
- **Django Authentication**: Built-in user model with custom UserProfile
- **Login Required**: `@login_required` decorator on protected views
- **Role-Based Access Control (RBAC)**: 
  - Custom permission system in UserProfile
  - Hierarchical user roles (admin, manager, cashier, etc.)
  - Permission checks in views

### Data Protection
- **CSRF Protection**: `CsrfViewMiddleware` enabled
- **CORS Management**:
  - `django-cors-headers` middleware
  - Restricted origins in production
  - Debug mode: allow all origins
  - CSRF trusted origins configuration

### HTTPS & Secure Cookies
- **SSL/TLS**: 
  - `SECURE_SSL_REDIRECT = True` (production)
  - `HSTS` headers enabled with 1-year max-age
  - HSTS preload enabled
- **Secure Cookies**:
  - `SESSION_COOKIE_SECURE = True`
  - `CSRF_COOKIE_SECURE = True`
- **X-Frame Options**: `X_FRAME_OPTIONS = 'DENY'` (clickjacking protection)
- **XSS/Content-Type Protection**:
  - `SECURE_BROWSER_XSS_FILTER = True`
  - `SECURE_CONTENT_TYPE_NOSNIFF = True`

### Input Validation
- **Password Validators**:
  - User attribute similarity check
  - Minimum length enforcement
  - Common password blacklist
  - Numeric-only password prevention
- **Form Validation**: Django forms with built-in sanitization

### Environment & Secrets
- **Configuration Management**: `python-decouple` for environment variables
  - Never hardcode secrets in code
  - Separate dev/production settings
  - Configurable security parameters
- **Database**: SQLite (local file storage)
  - Forced SQLite even if DATABASE_URL is set (prevents accidental cloud DB usage)

### Third-party Integrations
- **Firebase Cloud Messaging (FCM)**: API key from environment
- **Brevo Email Service**: API key and credentials from environment
- **OpenFoodFacts API**: External data source for product lookups

### Logging & Monitoring
- **Error Tracking**: ErrorLog model for persistence
- **Activity Logging**: UserActivity model for audit trails
- **Device Monitoring**: DeviceConnection tracking
- **Log Files**: FCM notifications logged to `fcm_notifications.log`
- **Log Levels**: Configurable via `LOG_LEVEL` environment variable

---

## Dependencies

### Core Dependencies
```
Django>=4.0.0
gunicorn>=21.0.0
firebase-admin>=6.0.0
django-cors-headers>=4.0.0
python-decouple>=3.8
```

### Data Processing
```
openpyxl>=3.1.0
pandas>=2.0.0
Pillow>=10.0.0
```

### Third-party Services
```
firebase>=12.5.0
sib-api-v3-sdk>=7.0.0  # Brevo email service
requests>=2.31.0
openfoodfacts>=0.1.0
```

### Development
```
django-extensions>=3.2.0
```

---

## Deployment

### Platforms
- **Production**: Render.com (Cloud hosting)
- **Database**: SQLite (persistent file storage)
- **Static Files**: Served via Nginx with `STATIC_ROOT = staticfiles/`
- **Media Files**: Uploaded to `media/` directory

### Docker Support
- **Dockerfile**: Multi-stage build for production optimization
- **docker-compose.yml**: Local development environment
- **docker-compose.prod.yml**: Production deployment config
- **Nginx Configuration**:
  - `nginx.conf`: Development reverse proxy
  - `nginx.prod.conf`: Production security hardening

### Environment Configuration
- **Development**: `DEBUG = True`, relaxed CORS, localhost allowed
- **Production**: 
  - `DEBUG = False`
  - Restricted ALLOWED_HOSTS
  - SSL enforcement
  - HSTS enabled
  - CORS restricted to trusted origins

---

## Features Overview

### 1. Point of Sale (POS)
- Real-time inventory tracking
- Quick product lookup by barcode
- Order creation and management
- Multi-item cart with quantity adjustment
- Checkout workflow with payment processing

### 2. Inventory Management
- Add/update stock levels
- Low stock alerts and notifications
- Product categorization
- Barcode scanning for quick access
- Excel export for reporting

### 3. Price Analytics & Warehouse Integration
- Import warehouse pricing data
- Competitive price comparison
- Marketing-focused pricing reports
- Price change notifications to customers
- Historical price tracking

### 4. Order Management
- Pending order queue
- Order completion workflow
- Order history with timestamps
- Order details and item breakdown
- Order cancellation tracking

### 5. User Management & Permissions
- Role-based access control (admin, manager, cashier)
- User creation, editing, and deletion
- Bulk user operations
- Password management and reset
- Activity audit logging

### 6. Notifications
- Real-time notification system
- Firebase Cloud Messaging (FCM) for push notifications
- Multi-device support
- Notification read/dismiss tracking
- Notification history

### 7. UPC/Barcode Lookup
- Integration with OpenFoodFacts API
- Barcode scanner interface
- Product information retrieval
- Lookup history
- Fallback UPC database

### 8. Food Ordering Integration
- Food item barcode scanning
- Food menu browser
- Integration with POS system
- Food item tracking separate from retail products

### 9. Airtime & Mobile Services
- Mobile airtime product management
- Airtime sales processing
- Approval workflow for sales
- Restock request management
- Provider integration

### 10. Tracking & Monitoring
- Device connection tracking
- User activity logging
- Error tracking and resolution
- Dashboard with real-time metrics
- Activity audit trails for compliance

### 11. Email Notifications
- Brevo email service integration
- Password reset emails
- Order confirmation emails
- Notification delivery tracking

### 12. Progressive Web App (PWA)
- Service worker for offline support
- App manifest for installability
- Offline fallback page
- Cache strategy for assets

---

## Project Structure

```
futurePOS/
├── confige/                    # Django project settings
│   ├── settings.py             # Configuration (security, database, logging)
│   ├── urls.py                 # Root URL configuration
│   └── wsgi.py                 # WSGI application
├── nano/                       # Main application
│   ├── models.py               # Database models
│   ├── views.py                # View functions & API endpoints
│   ├── views_export.py         # Export functionality
│   ├── upc_views.py            # UPC lookup views
│   ├── food_ordering_integration.py  # Food ordering features
│   ├── urls.py                 # App URL patterns
│   ├── migrations/             # Database migrations
│   ├── management/commands/    # Custom management commands
│   ├── static/nano/            # CSS, JavaScript, images
│   │   ├── barcode_scanner.js
│   │   ├── hamburger.js
│   │   ├── home.js
│   │   ├── home.css
│   │   ├── price_comparisons.js
│   │   └── sw.js               # Service worker
│   └── templates/nano/         # HTML templates
│       ├── base.html
│       ├── home.html
│       ├── pending_orders.html
│       ├── checkout_order.html
│       └── [40+ other templates]
├── food_ordering/              # Food ordering app (separate)
├── static/                     # Collected static files
├── media/                      # User uploads
├── docker-compose.yml          # Development containers
├── docker-compose.prod.yml     # Production containers
├── Dockerfile                  # Development image
├── Dockerfile.prod             # Production image
├── nginx.conf                  # Development nginx config
├── nginx.prod.conf             # Production nginx config
├── requirements.txt            # Python dependencies
├── package.json                # Node.js dependencies (Firebase)
└── manage.py                   # Django CLI
```

---

## Development Workflow

### Local Setup
```bash
# Activate virtual environment (Windows PowerShell)
.\envi\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create/update database
python manage.py migrate

# Run development server
python manage.py runserver
```

### Running Tests
```bash
# Run Django tests
python manage.py test

# Run pytest (if installed)
pytest
```

### Database Management
- **SQLite**: `db.sqlite3` in repo root
- **Migrations**: Stored in `nano/migrations/`
- **Create migration**: `python manage.py makemigrations`
- **Apply migration**: `python manage.py migrate`

---

## Key Configuration Files

### `confige/settings.py`
- DEBUG mode toggle
- Database configuration
- Installed apps
- Middleware stack
- Security settings (HTTPS, HSTS, CORS)
- Static/media files
- FCM and Brevo credentials
- Logging configuration

### `nano/urls.py`
- 90+ URL patterns organized by feature
- API endpoints
- Template-based views
- Admin routes

### `confige/urls.py`
- Root URL dispatcher
- Admin panel routing

---

## Error Handling & Logging

### Error Tracking
- **ErrorLog Model**: Persistent error storage
- **DeviceConnection Tracking**: Monitor device status
- **Activity Logging**: Audit trail for user actions

### Logging
- **FCM Service Logs**: `fcm_notifications.log`
- **Console Logging**: Real-time debug output
- **Log Levels**: Configurable (INFO, DEBUG, WARNING, ERROR)

### Error Pages
- **Offline Page**: `/offline/` for PWA
- **Custom Error Handling**: JSON responses for APIs

---

## Future Enhancement Areas

1. **Enhanced Analytics**: Real-time dashboard with more metrics
2. **Mobile App**: Native iOS/Android app
3. **Advanced Reporting**: Custom report builder
4. **Multi-location Support**: Handle multiple store branches
5. **Inventory Forecasting**: AI-based stock predictions
6. **Integration Ecosystem**: Accounting software, ERP systems
7. **API Rate Limiting**: Protect against abuse
8. **Webhook Support**: Real-time integrations
9. **Custom Themes**: White-label capabilities
10. **Internationalization**: Multi-language support

---

## Performance Considerations

- **Caching**: Leverage service worker for static assets
- **Database Indexing**: Optimize frequent queries
- **Lazy Loading**: Load images/data on demand
- **Minification**: CSS/JS compression in production
- **CDN**: CloudFlare or similar for static assets
- **Query Optimization**: Use select_related/prefetch_related

---

## Maintenance & Support

- **Log Monitoring**: Check `fcm_notifications.log` regularly
- **Security Updates**: Keep Django and dependencies updated
- **Database Backups**: Regular SQLite file backups
- **Error Reporting**: Monitor ErrorLog and ErrorTracking
- **Performance Metrics**: Review UserActivity logs

---

## Contact & Documentation

- **Main App**: `nano/`
- **Settings**: `confige/settings.py`
- **API Docs**: Inline code comments in views
- **Feature Guides**: Markdown files in repo root
- **Tests**: `test_*.py` and `nano/tests.py`

---

**Last Updated**: January 2026  
**Version**: 1.0  
**Status**: Production Ready
