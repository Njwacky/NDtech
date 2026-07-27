# NDtech POS System

A modern, full-featured Point of Sale (POS) system with inventory management, built with Django and Next.js.

## 🌟 Features

### **Backend (Django)**
- ✅ User authentication & role management (Admin, Manager, Cashier)
- ✅ Product & inventory management
- ✅ POS system with cart functionality
- ✅ Sales tracking & order management
- ✅ Notifications system with FCM push notifications
- ✅ Airtime & data bundle sales
- ✅ Warehouse price comparisons
- ✅ Comprehensive audit logging
- ✅ RESTful API with Django REST Framework
- ✅ Data protection & GDPR compliance

### **Frontend (Next.js + React)**
- ✅ Modern React 19 + Next.js 16 frontend
- ✅ TypeScript for type safety
- ✅ Tailwind CSS with shadcn/ui components
- ✅ Interactive checkout component
- ✅ Responsive design
- ✅ Real-time cart management

## 📊 Project Structure

```
NDtech/
├── nano/                          # Django backend
│   ├── views.py                 # Main views (imports from modules)
│   ├── views_core.py            # Authentication, Users, Dashboard
│   ├── views_pos.py             # POS, Sales, Orders, Inventory
│   ├── views_communications.py  # Notifications, FCM, Airtime, Tracking
│   ├── views_api_v1.py         # API endpoints
│   ├── models.py                # Database models
│   ├── serializers.py           # API serializers
│   └── ...
├── frontend/                     # Next.js frontend
│   ├── src/
│   │   ├── app/                # Next.js app router
│   │   ├── components/ui/      # Reusable UI components
│   │   └── lib/               # Utilities
│   ├── package.json
│   └── ...
├── confige/                      # Django configuration
├── manage.py
└── README.md
```

## 💻 Installation & Setup

### **Prerequisites**
- Python 3.11+
- Node.js 18+
- PostgreSQL (for production)
- Firebase project (for FCM notifications)

### **Backend Setup**

1. **Clone the repository**
   ```bash
   git clone https://github.com/Njwacky/NDtech.git
   cd NDtech
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start Django server**
   ```bash
   python manage.py runserver
   ```
   Backend runs at: http://localhost:8000

### **Frontend Setup**

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```
   Frontend runs at: http://localhost:3000

## 🧪 Testing

### **Backend Tests**
```bash
# Run all tests
python manage.py test

# Run specific test module
python manage.py test nano.tests_api
python manage.py test nano.test_data_protection
```

### **Frontend Tests**
```bash
cd frontend
npm test
npm run test:watch
npm run test:coverage
```

### **View Structure Tests**
```bash
python3 test_view_imports.py
```

## 📚 API Documentation

Once the server is running, access:
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## 🔐 User Roles & Permissions

| Role | Permissions |
|------|-------------|
| **Superuser** | Full access to everything |
| **Admin** | Manage users, products, sales, view reports |
| **Manager** | Manage products, sales, view reports |
| **Cashier** | Process sales, view own sales |

## 🚀 Production Deployment

### **Backend (Django)**
1. Set `DJANGO_DEBUG=False`
2. Configure PostgreSQL database
3. Set up static files with WhiteNoise
4. Use Gunicorn: `gunicorn confige.wsgi:application`
5. Configure HTTPS with SSL certificates

### **Frontend (Next.js)**
1. Build for production: `npm run build`
2. Start production server: `npm start`
3. Or deploy to Vercel/Netlify

### **Docker Deployment**
```bash
# Build and run with Docker
docker-compose up --build
```

## 📁 Key Configuration Files

- **`.env`** - Environment variables
- **`confige/settings.py`** - Django settings
- **`frontend/next.config.js`** - Next.js configuration
- **`frontend/tailwind.config.js`** - Tailwind CSS config
- **`requirements.txt`** - Python dependencies
- **`frontend/package.json`** - Node.js dependencies

## 🛠️ Management Commands

```bash
# Clean up old data
python manage.py data_protection --action=cleanup

# Export user data (GDPR)
python manage.py data_protection --action=export-user --user-id=1

# Run price comparison
python manage.py run_price_comparison

# Import warehouse prices
python manage.py import_warehouse_prices path/to/file.csv
```

## 📊 Database Models

Key models in `nano/models.py`:
- `Product` - Product inventory
- `UserProfile` - Extended user info
- `PendingOrder` / `CompletedOrder` - Order management
- `Notification` - User notifications
- `FCMToken` - Firebase push notification tokens
- `AirtimeProduct` / `AirtimeSale` - Airtime sales
- `WarehousePrice` - Price comparison data
- `ErrorLog` - Error tracking
- `SecurityAuditLog` - Security auditing

## 🔒 Security Features

- ✅ GDPR compliance with data protection tools
- ✅ Sensitive data masking in logs
- ✅ Role-based access control
- ✅ CSRF protection
- ✅ SQL injection prevention
- ✅ XSS protection
- ✅ Security headers (HSTS, X-Frame-Options, etc.)
- ✅ Audit logging for sensitive actions
- ✅ Data retention policies
- ✅ Environment variables for secrets

## 📖 Documentation

Additional documentation in the repository:
- `API_IMPLEMENTATION_SUMMARY.md` - API documentation
- `DATA_PROTECTION_IMPLEMENTATION.md` - Data protection guide
- `DOCKER_SETUP_GUIDE.md` - Docker deployment
- `SECURITY_AUDIT_LOG_DATABASE_FIX_SUMMARY.md` - Security setup

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 License

[Specify your license here]

## 👤 Contact

- **GitHub**: [@Njwacky](https://github.com/Njwacky)
- **Issues**: [Report bugs here](https://github.com/Njwacky/NDtech/issues)

---

## 🎯 TODO (Completed ✅)

- [x] Repository cleanup (remove backup files)
- [x] Frontend implementation (Next.js + React + TypeScript)
- [x] View consolidation (modular structure)
- [x] API documentation
- [x] Data protection implementation
- [x] Security audit logging
- [ ] Add comprehensive tests
- [ ] Set up CI/CD pipeline
- [ ] Deploy to production

---

**Built with ❤️ using Django, Next.js, React, and Tailwind CSS**
