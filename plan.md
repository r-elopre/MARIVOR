# Marivor - Fish & Vegetable Marketplace

## Development Plan

### 🚀 Step 1: Project Setup

- [ ] Create Flask project structure:
  - `app.py` - Main application file
  - `templates/` - HTML templates folder
  - `static/` - CSS, JS, and images folder
- [ ] Install required packages:
  - Flask
  - SQLAlchemy/SQLite
  - Twilio SMS API SDK
- [ ] Set up base HTML template with Bootstrap/Tailwind for styling

### 🗄️ Step 2: Database Models

Create database tables with the following structure:

- **Users table**: `id`, `phone_number`, `is_verified`, `created_at`
- **OTP table**: `id`, `phone_number`, `otp_code` (hashed), `expires_at`, `attempts`
- **Products table**: `id`, `name`, `category` (Fish/Vegetable), `price`, `stock`, `image_url`
- **Orders table**: `id`, `user_id`, `items`, `total_price`, `status`

### 📱 Step 3: User Signup & Login (OTP Flow)

#### Phone Number Entry
- User enters phone number in HTML form

#### `/send_otp` Route
- Validate phone number format
- Generate 6-digit OTP code
- Store OTP (hashed) with expiration time
- Send OTP via SMS API

#### `/verify_otp` Route
- Check OTP against stored value and expiry
- If valid:
  - Log user in (store `user_id` in session)
  - Create new account if first-time user

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
- ✅ Database created (`marivor.db`)
- ✅ Sample data populated
- ⏳ Flask application development
- ⏳ Authentication system
- ⏳ Product catalog
- ⏳ Shopping cart
- ⏳ Admin panel