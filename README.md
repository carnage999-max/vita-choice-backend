# VitaChoice Backend API

A comprehensive RESTful API for supplement e-commerce and formula development. Features product catalog, user authentication, supplement formulas builder with regulatory compliance checking, and extensive ingredient database.

---

## 🎯 Key Features

### E-Commerce Platform
- **Product Catalog** - Browse and search 17+ premium supplements and stacks
- **User Management** - JWT authentication with profile management and token blacklisting
- **Contact System** - Customer inquiry and support messaging
- **Redis Caching** - High-performance product data caching (24-hour TTL)
- **Comprehensive Testing** - 118 test cases with 95%+ success rate ensuring code quality

### Formula Development (Fully Integrated)
- **5,000+ Ingredient Database** - Searchable library with safety classifications
- **Formula Builder** - Create custom supplement formulas with precise dosing
- **Compliance Checker** - Automated safety validation with APPROVED/WARNING/STOP status
- **CSV Exports** - Export formulas for manufacturing or documentation
- **User Isolation** - Each user can only access their own formulas
- **Real-time Validation** - Ingredient safety checking and dose validation

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+ (or SQLite for development)
- Redis (for caching)
- pip

### Installation

```bash
# Clone repository
git clone <repository-url>
cd vitachoice_backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Populate sample products
python manage.py populate_products

# Run comprehensive test suite (optional but recommended)
python manage.py test

# Run development server
python manage.py runserver
```

### Environment Variables

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/vitachoice
REDIS_URL=redis://127.0.0.1:6379/1
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:19006

# Email Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_SSL=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
CONTACT_EMAIL_RECIPIENT=support@vitachoice.com

# AWS S3 Settings (for product images)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=your-bucket-name
```

---

## ⚡ Recent Improvements (v1.3.0)

### 🔧 Infrastructure Fixes
- **Complete Database Migration** - All models properly migrated including Formula and FormulaItem tables
- **URL Routing Fixed** - Ingredients app fully integrated with proper API endpoints
- **JWT Token Blacklisting** - Enhanced security with proper token invalidation
- **Pagination System** - Consistent paginated responses across all list endpoints
- **Cache Invalidation** - Automatic cache clearing on model updates via Django signals

### 🧪 Test Suite Overhaul
- **118 Comprehensive Tests** - Covering all apps with 95%+ success rate
- **Model Testing** - Database operations, constraints, business logic validation
- **API Testing** - Complete endpoint coverage with authentication scenarios
- **Integration Testing** - End-to-end user workflows and complex operations
- **Error Handling** - Validation, permissions, and edge case scenarios

### 🔐 Security Enhancements
- **Enhanced Authentication** - Proper JWT token lifecycle management
- **Permission Systems** - User isolation and admin-only operations
- **Data Validation** - Comprehensive input validation and sanitization
- **CORS Configuration** - Secure cross-origin resource sharing setup

### 📊 API Improvements
- **Consistent Responses** - Standardized pagination and error formats
- **Advanced Filtering** - Search, category, and safety-level filtering for ingredients
- **Compliance Checking** - Real-time formula safety validation
- **Export Functions** - CSV exports for formulas and ingredient data

---

## 📚 API Documentation

### Base URL
- **Production**: `https://vita-choice-backend.onrender.com`
- **Development**: `http://localhost:8000`

### Swagger Documentation
- **Schema**: `/api/schema/`
- **Interactive Docs**: Available when DEBUG=True
- **OpenAPI 3.0**: Comprehensive API specification with examples

---

## 🔑 Authentication

All authentication uses JWT tokens with automatic refresh capability.

### Register
```bash
POST /api/auth/register/
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "password2": "SecurePass123",
  "first_name": "John",
  "last_name": "Doe"
}

# Response
{
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

### Login
```bash
POST /api/auth/login/
Content-Type: application/json

{
  "username": "john_doe",
  "password": "SecurePass123"
}

# Response
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Refresh Token
```bash
POST /api/auth/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

# Response
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Logout
```bash
POST /api/auth/logout/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

# Response
{
  "message": "Logout successful"
}
```

### User Profile
```bash
# Get current user profile
GET /api/auth/me/
Authorization: Bearer {access_token}

# Update user profile
PUT /api/auth/me/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Smith",
  "email": "john.smith@example.com"
}
```

### Change Password
```bash
POST /api/auth/change-password/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "old_password": "OldPass123",
  "new_password": "NewPass456"
}
```

---

## 🛍️ E-Commerce Endpoints

### Products

#### List All Products (Cached)
```bash
GET /api/product/

# Response includes 17 products across categories:
# - Stax (13 products): Immune, Brain, Energy, Heart, Cholesterol, Diabetes, Sleep, Anti-Aging, Longevity, Gut Health, Joint & Bone, Men's & Women's Health, Vision/Eye Health
# - Premium (4 products): Core Liquid Multivitamin, Diabetes Support Stack, Microplastics Cleanse Stack, Daily Dosing Device
```

#### Get Single Product
```bash
GET /api/product/{id}/

# Response
{
  "id": "uuid-here",
  "name": "Immune Stax",
  "subtitle": "Daily immune defense for all seasons",
  "price": "59.00",
  "original_price": null,
  "category": "stax",
  "image": "https://vitachoice-media.s3.amazonaws.com/media/products/immune_stax.png",
  "rating": "4.6",
  "review_count": 124,
  "description": "Immune Stax is formulated with essential vitamins...",
  "short_description": "Boosts immunity and resilience...",
  "key_actives": ["Vitamin C", "Zinc", "Elderberry", "Echinacea"],
  "free_from": ["Gluten", "Artificial preservatives", "GMOs"],
  "benefits": ["Supports strong immune response", "Helps fight seasonal colds", "Promotes overall vitality"],
  "serving_size": "2 capsules",
  "servings_per_bottle": 30,
  "faqs": [
    {
      "question": "When should I take Immune Stax?",
      "answer": "Take two capsules daily with meals, preferably in the morning."
    }
  ],
  "usage": "Take two capsules daily with meals.",
  "created_at": "2025-09-30T11:11:12.358101Z",
  "updated_at": "2025-09-30T11:11:12.358172Z"
}
```

#### Create Product (Admin Only)
```bash
POST /api/product/
Authorization: Bearer {admin_access_token}
Content-Type: application/json

{
  "name": "New Product",
  "subtitle": "Product subtitle",
  "price": "99.00",
  "category": "stax",
  "description": "Product description...",
  "key_actives": ["Ingredient 1", "Ingredient 2"],
  "benefits": ["Benefit 1", "Benefit 2"]
}
```

#### Update Product (Admin Only)
```bash
PUT /api/product/{id}/
Authorization: Bearer {admin_access_token}

PATCH /api/product/{id}/
Authorization: Bearer {admin_access_token}
```

#### Delete Product (Admin Only)
```bash
DELETE /api/product/{id}/
Authorization: Bearer {admin_access_token}
```

### Contact

#### Submit Contact Form
```bash
POST /api/contact/
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "phone_number": "+1234567890",
  "inquiry_type": "product_question",
  "subject": "Question about Immune Stax",
  "message": "I would like to know more about the ingredients..."
}

# Response
{
  "status": "Message received"
}
```

---

## 🧪 Formula Development Endpoints

*Note: These endpoints are fully integrated and functional in the current version*

### Ingredients

#### List Ingredients (Paginated & Searchable)
```bash
GET /api/ingredients/
GET /api/ingredients/?search=vitamin
GET /api/ingredients/?category=Vitamins&safety_level=SAFE
GET /api/ingredients/?exclude_risk=true

# Query Parameters:
# - search: Search by name, category, source
# - category: Filter by ingredient category
# - source: Filter by ingredient source
# - safety: Filter by safety text
# - exclude_risk: Exclude high-risk ingredients (true/false)
```

#### Get Ingredient Details
```bash
GET /api/ingredients/{id}/

# Response
{
  "id": 1,
  "name": "Vitamin C (Ascorbic Acid)",
  "category": "Vitamins",
  "source": "Synthetic",
  "safety": "General Dietary Use",
  "safety_level": "SAFE",
  "safety_color": "#4caf50",
  "evidence": "Well-established antioxidant properties...",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

#### Get Ingredient Categories
```bash
GET /api/ingredients/categories/

# Response
["Vitamins", "Minerals", "Herbs", "Amino Acids", "Enzymes", ...]
```

#### Get Ingredient Sources
```bash
GET /api/ingredients/sources/

# Response
["Plant", "Synthetic", "Animal", "Marine", "Fungal", ...]
```

#### Get Ingredient Statistics
```bash
GET /api/ingredients/stats/

# Response
{
  "total": 5066,
  "by_safety_level": {
    "safe": 3200,
    "caution": 1500,
    "risk": 366
  },
  "categories": 25
}
```

### Formulas

#### List User's Formulas
```bash
GET /api/formulas/
Authorization: Bearer {access_token}

# Response
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "name": "My Daily Multivitamin",
      "description": "Custom daily supplement",
      "region": "US",
      "ingredient_count": 12,
      "total_weight_mg": 850.5,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-16T14:30:00Z"
    }
  ]
}
```

#### Create New Formula
```bash
POST /api/formulas/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "My Multivitamin",
  "description": "Daily essential vitamins",
  "region": "US"
}

# Response
{
  "id": 1,
  "name": "My Multivitamin",
  "description": "Daily essential vitamins",
  "region": "US",
  "items": [],
  "owner": 1,
  "created_at": "2024-01-15T10:00:00Z"
}
```

#### Get Formula Details
```bash
GET /api/formulas/{id}/
Authorization: Bearer {access_token}

# Response
{
  "id": 1,
  "name": "My Multivitamin",
  "description": "Daily essential vitamins",
  "region": "US",
  "owner": 1,
  "items": [
    {
      "id": 1,
      "ingredient": {
        "id": 123,
        "name": "Vitamin C (Ascorbic Acid)",
        "category": "Vitamins",
        "safety_level": "SAFE"
      },
      "dose_value": "500.00",
      "dose_unit": "mg",
      "notes": "For immune support",
      "order": 0
    }
  ],
  "total_weight_mg": 500.0,
  "ingredient_count": 1,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-16T14:30:00Z"
}
```

#### Update Formula
```bash
PUT /api/formulas/{id}/
PATCH /api/formulas/{id}/
Authorization: Bearer {access_token}
```

#### Delete Formula
```bash
DELETE /api/formulas/{id}/
Authorization: Bearer {access_token}
```

#### Add Ingredient to Formula
```bash
POST /api/formulas/{id}/add_ingredient/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "ingredient_id": 123,
  "dose_value": 500,
  "dose_unit": "mg",
  "notes": "For immune support"
}
```

#### Remove Ingredient from Formula
```bash
DELETE /api/formulas/{id}/remove_ingredient/{item_id}/
Authorization: Bearer {access_token}
```

#### Update Ingredient in Formula
```bash
PATCH /api/formulas/{id}/update_ingredient/{item_id}/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "dose_value": 750,
  "dose_unit": "mg",
  "notes": "Increased dose for winter season"
}
```

#### Duplicate Formula
```bash
POST /api/formulas/{id}/duplicate/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "My Multivitamin v2"  # Optional
}
```

### Compliance Checking

#### Full Compliance Check
```bash
POST /api/formulas/{id}/check_compliance/
Authorization: Bearer {access_token}

# Response
{
  "formula_id": 1,
  "formula_name": "My Multivitamin",
  "region": "US",
  "status": "WARNING",
  "status_message": "Formula contains 1 ingredient(s) that require attention...",
  "can_proceed": true,
  "total_ingredients": 3,
  "total_weight_mg": 1250.5,
  "summary": {
    "safe": 2,
    "caution": 1,
    "risk": 0
  },
  "issues": [
    {
      "ingredient_id": 456,
      "ingredient": "Kava Extract",
      "dose": "300mg",
      "category": "Herbs",
      "severity": "CAUTION",
      "level": "CAUTION",
      "safety_info": "Caution (processing required)",
      "message": "Special processing or preparation is required.",
      "action": "Verify proper processing methods are applied"
    }
  ],
  "checked_at": "2024-01-16T14:30:00Z"
}
```

#### Quick Compliance Summary
```bash
GET /api/formulas/{id}/compliance_summary/
Authorization: Bearer {access_token}

# Response
{
  "status": "APPROVED",
  "summary": {
    "safe": 5,
    "caution": 0,
    "risk": 0
  },
  "total_ingredients": 5
}
```

### Export Functions

#### Export Supplement Facts Label (PDF)
```bash
GET /api/formulas/{id}/export_label/
Authorization: Bearer {access_token}

# Note: PDF generation is currently under development
# Returns: 501 Not Implemented (placeholder response)
```

#### Export Formula Summary (PDF)
```bash
GET /api/formulas/{id}/export_summary/
Authorization: Bearer {access_token}

# Note: PDF generation is currently under development  
# Returns: 501 Not Implemented (placeholder response)
```

#### Export Formula as CSV
```bash
GET /api/formulas/{id}/export_csv/
Authorization: Bearer {access_token}

# Returns: CSV file with columns:
# Ingredient, Category, Source, Dose Value, Dose Unit, Safety, Safety Level, Notes
```

#### Export All User Formulas as CSV
```bash
GET /api/formulas/export_all_csv/
Authorization: Bearer {access_token}

# Returns: CSV file with all user's formulas
# Content-Disposition: attachment; filename="my_formulas.csv"
```

---

## 🛡️ Quality Assurance

### Test Coverage
The project includes comprehensive test coverage across all apps:

| App | Test Categories | Coverage |
|-----|----------------|----------|
| **Main** | Product CRUD, Contact forms, Caching, Integration workflows | ✅ Full |
| **Users** | Authentication, Registration, Profile management, Password changes | ✅ Full |
| **Ingredients** | Formula building, Compliance checking, Ingredient management, CSV exports | ✅ Full |

### Test Categories
- **Model Tests**: Database operations, business logic, properties
- **API Tests**: Endpoint functionality, authentication, permissions
- **Serializer Tests**: Data validation, transformation, error handling
- **Integration Tests**: Complete user workflows, end-to-end scenarios
- **URL Tests**: Route verification and parameter handling

### Running Quality Checks
```bash
# Run all tests
python manage.py test

# Check for Django issues
python manage.py check

# Validate migrations
python manage.py makemigrations --check --dry-run

# Security check (if using django-security)
python manage.py check --deploy
```

## 🛡️ Safety Classification System

The system automatically categorizes ingredients into safety levels:

| Level | Description | Color | Example Ingredients |
|-------|-------------|-------|-------------------|
| **SAFE** | General dietary use approved | 🟢 Green | Vitamin C, Magnesium, B-Complex |
| **CAUTION** | Special handling/processing required | 🟡 Orange | Topical herbs, PA alkaloid plants |
| **RISK** | Restricted/controlled substances | 🔴 Red | Banned substances, high-risk compounds |
| **UNKNOWN** | Unclassified safety status | ⚫ Gray | Newly added or incomplete data |

### Compliance Status Levels

| Status | Description | Action Required |
|--------|-------------|-----------------|
| **APPROVED** | All ingredients are safe | ✅ Ready to proceed |
| **WARNING** | Contains caution-level ingredients | ⚠️ Review warnings before proceeding |
| **STOP** | Contains restricted/high-risk ingredients | 🛑 Cannot proceed without regulatory approval |

---

## 🗃️ Data Models

### Product Model
```python
{
  "id": "UUID",
  "name": "string",
  "subtitle": "string",
  "price": "decimal",
  "original_price": "decimal (optional)",
  "category": "string",
  "image": "ImageField (S3)",
  "rating": "decimal",
  "review_count": "integer",
  "description": "text",
  "short_description": "text",
  "key_actives": "JSONField (array)",
  "free_from": "JSONField (array)",
  "benefits": "JSONField (array)",
  "serving_size": "string",
  "servings_per_bottle": "integer",
  "faqs": "JSONField (array of objects)",
  "usage": "text",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Ingredient Model
```python
{
  "id": "integer",
  "name": "string (unique)",
  "category": "string",
  "source": "string",
  "safety": "string",
  "evidence": "text",
  "safety_level": "property (SAFE/CAUTION/RISK/UNKNOWN)",
  "safety_color": "property (hex color)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Formula Model
```python
{
  "id": "integer",
  "owner": "User FK",
  "name": "string",
  "description": "text",
  "region": "string (US/EU/CA/AU)",
  "items": "FormulaItem[]",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### FormulaItem Model
```python
{
  "id": "integer",
  "formula": "Formula FK",
  "ingredient": "Ingredient FK",
  "dose_value": "decimal",
  "dose_unit": "string (mg/mcg/g/IU)",
  "notes": "text",
  "order": "integer"
}
```

---

## 🚢 Deployment

### Environment Setup
- **Framework**: Django 4.2+ with Django REST Framework
- **Database**: PostgreSQL (production) / SQLite (development)
- **Cache**: Redis with django-redis
- **File Storage**: AWS S3 (production) / Local (development)
- **Server**: Gunicorn + WhiteNoise for static files

### Render.com Deployment
```yaml
# render.yaml
services:
  - type: web
    name: vita-choice-backend
    env: python
    buildCommand: |
      pip install -r requirements.txt
      python manage.py collectstatic --no-input
      python manage.py migrate
    startCommand: gunicorn vitachoice_backend.wsgi:application

databases:
  - name: vita-choice-db
    databaseName: vitachoice
```

### Required Environment Variables
```env
# Production Settings
DEBUG=False
SECRET_KEY=generated-secret-key
ALLOWED_HOSTS=vita-choice-backend.onrender.com
DATABASE_URL=postgresql://... (auto-set by Render)
REDIS_URL=redis://... (external Redis service)

# CORS Settings
CORS_ALLOWED_ORIGINS=https://vita-choice.vercel.app

# AWS S3 Settings
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=vitachoice-media

# Email Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_SSL=True
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@vitachoice.com
CONTACT_EMAIL_RECIPIENT=support@vitachoice.com
```

---

## 🔧 Development

### Running Tests
```bash
# Run all tests (118 test cases)
python manage.py test

# Run specific app tests
python manage.py test main
python manage.py test users  
python manage.py test ingredients

# Run tests with verbose output
python manage.py test --verbosity=2

# Run specific test classes
python manage.py test main.tests.ProductModelTests
python manage.py test users.tests.AuthenticationIntegrationTests
python manage.py test ingredients.tests.ComplianceTests

# With coverage
coverage run --source='.' manage.py test
coverage report

# Keep test database for faster subsequent runs
python manage.py test --keepdb
```

### Management Commands
```bash
# Populate sample products
python manage.py populate_products

# Import ingredients (if CSV provided)
python manage.py import_ingredients path/to/ingredients.csv

# Clear cache
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

### API Testing Examples

#### Using cURL
```bash
# Login and get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['access'])")

# Use token to access protected endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/formulas/
```

#### Using Python requests
```python
import requests

# Login
response = requests.post('http://localhost:8000/api/auth/login/', {
    'username': 'testuser',
    'password': 'testpass'
})
token = response.json()['access']

# Access protected endpoint
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('http://localhost:8000/api/formulas/', headers=headers)
```

---

## 📊 Performance & Caching

### Redis Caching Strategy
- **Product List**: 24-hour TTL with cache invalidation on CRUD operations
- **Cache Key**: `vitachoice:product_list_cache`
- **Auto-Invalidation**: Triggered by Django signals on model save/delete

### Cache Management
```python
# Manual cache operations
from django.core.cache import cache

# Clear product cache
cache.delete('product_list_cache')

# Clear all cache
cache.clear()

# Check cache status
cache.get('product_list_cache')  # Returns data or None
```

---

## 🤝 Support & Documentation

- **API Health Check**: `/health/`
- **Admin Interface**: `/admin/` (requires superuser)
- **API Schema**: `/api/schema/`
- **Production URL**: https://vita-choice-backend.onrender.com
- **Frontend**: https://vita-choice.vercel.app

---

## 📄 License

[Your License Here]

---

## 🔄 Version History

### v1.3.0 (Current)
- **Full ingredients app integration** - Complete formula builder functionality
- **Comprehensive test suite** - 118 test cases with 95%+ success rate
- **Enhanced authentication** - JWT token blacklisting and improved validation
- **Fixed API endpoints** - All URL routing and pagination properly configured
- **Database optimizations** - Proper migrations and constraint handling
- **Production-ready** - All major bugs fixed and performance optimized

### v1.2.0
- E-commerce product catalog (17 products)
- JWT authentication with refresh tokens
- Redis caching for performance
- Contact form with email notifications
- AWS S3 integration for media storage
- Comprehensive API documentation

### v1.1.0
- Formula builder foundation
- Ingredient database structure
- Compliance checking framework
- CSV export capabilities

### v1.0.0
- Initial Django REST API setup
- Basic authentication
- Core models and serializers

---

## 🚀 Roadmap

### Completed ✅
- [x] Complete ingredients app integration
- [x] Comprehensive test coverage (118 tests)
- [x] JWT authentication with token blacklisting
- [x] Formula builder with compliance checking
- [x] CSV export functionality
- [x] User access control and permissions
- [x] API pagination and filtering
- [x] Cache invalidation system

### Upcoming Features
- [ ] PDF generation for supplement facts labels
- [ ] Payment processing with Stripe
- [ ] Order management system
- [ ] Advanced formula analytics
- [ ] API rate limiting
- [ ] Advanced search with Elasticsearch
- [ ] Real-time notifications
- [ ] Mobile app support
- [ ] Batch operations for formulas
- [ ] Formula sharing between users
