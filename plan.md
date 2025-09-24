# Marivor - Fish & Vegetable Marketplace

## Development Plan

### 🚀 Step 1: Project Setup

- [ ] Create Flask project structure:
  - `app.py` - Main application file
  - `templates/` - HTML templates folder
  - `static/` - CSS, JS, and images folder
- [x] Install required packages:
  - Flask ✅
  - Supabase Python SDK ✅
  - Face-API.js for face detection ✅
- [ ] Set up base HTML template with Bootstrap/Tailwind for styling

### 🗄️ Step 2: Database Models (Supabase)

Database tables implemented in Supabase:

- **Users table**: `id`, `username`, `phone_number`, `face_login_code`, `face_photo_*`, `is_verified`, `created_at` ✅
- **Products table**: `id`, `name`, `category` (Fish/Vegetable), `price`, `stock`, `unit`, `image_url` ✅
- **Orders table**: `id`, `user_id`, `items`, `total_price`, `status`, `created_at` ✅
- **Storage buckets**: `faces` (user photos), `products` (product images) ✅

### 📱 Step 3: User Authentication (Face Recognition) ✅

#### Face Registration Flow
- **Face Detection**: Real-time camera capture with face-api.js ✅
- **Multi-angle Capture**: Front, left, right face photos ✅
- **Supabase Storage**: Secure cloud storage for face photos ✅
- **Auto-generated Codes**: 6-digit login codes for each user ✅

#### Face Login Flow
- **Code Entry**: Users enter their 6-digit face login code ✅
- **Session Management**: Secure user sessions ✅
- **Profile Access**: View account details and login code ✅

### 🔐 Step 4: Session & Authentication

- [ ] Use Flask session/cookies to maintain user login state
- [ ] Protect routes (`/cart`, `/checkout`) - require authentication
- [ ] Add logout functionality (clear session)

### 🧭 Step 5: Navbar & Pages

#### Navigation Structure
Create `base.html` template with navbar containing:
- **Home** - General overview, featured products
- **Fish** - Query products where `category = 'Fish'`
- **Vegetable** - Query products where `category = 'Vegetable'`
- **Cart** - Shopping cart page
- **Profile** - User account page

#### Dynamic Content
- Use Flask templates: `{% for product in products %}`
- Display products dynamically by category

### 🛒 Step 6: Product & Cart System

#### Product Features
- Product list page with "Add to Cart" button (JS or form)
- Cart storage options:
  - **Session storage** (simpler for MVP)
  - **Database storage** (for persistent carts)

#### Cart & Checkout
- **Cart page**: Show products, quantities, subtotal
- **Checkout page**: Delivery details + payment (future implementation)

### 👑 Step 7: Admin Panel (Basic)

- [ ] Create `/admin` route for product management
- [ ] Admin authentication (special flag in Users table)
- [ ] Admin features:
  - Add new products (Fish/Vegetable)
  - Form fields: name, price, stock, category, image
  - Inventory management

### 🧪 Step 8: Testing

#### Test Coverage
- [ ] **OTP Flow**: Correct codes, incorrect codes, expired codes
- [ ] **Navigation**: Home, Fish, Vegetable pages
- [ ] **Cart System**: Add items, remove items, checkout process
- [ ] **Session Persistence**: User stays logged in after page refresh

### 🚀 Step 9: Deployment

#### Production Setup
- [ ] Use **Gunicorn** or **uWSGI** with **Nginx**
- [ ] Configure `.env` for:
  - SMS API keys
  - Database credentials
- [ ] **HTTPS** implementation (critical for login & payments)
- [ ] Set up monitoring for logs & errors

---

## 📋 Project Status
- ✅ Environment setup (`.env` file)
- ✅ Supabase database setup with tables and storage
- ✅ Face recognition authentication system
- ✅ Flask application with full routing
- ✅ Product catalog system
- ✅ Admin panel with product management
- ✅ Modern responsive UI with Bootstrap 5
- ⏳ Shopping cart implementation (session-based placeholder)
- ⏳ Order management system completion
- ⏳ Payment integration
- ⏳ Multi-vendor seller dashboard