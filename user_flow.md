# Marivor - User Flow Summary

## App Overview
Marivor is a fish and vegetable marketplace web application where users can browse products, add items to cart, and place orders. The app features innovative face detection authentication alongside traditional SMS verification for secure and convenient access.

## User Journey Flow

### 1. 🏠 Landing & Discovery
- **Home Page**: User visits the website and sees featured products
- **Navigation**: User can browse different categories via navbar:
  - Home (featured/overview)
  - Fish (all fish products)
  - Vegetable (all vegetable products)
  - Cart (shopping cart)
  - Profile (user account)

### 2. � Authentication Flow (Dual Options)

#### Option A: 📱 SMS OTP Authentication
- **Phone Entry**: User enters their phone number in signup/login form
- **OTP Generation**: System generates 6-digit OTP and sends via SMS
- **OTP Verification**: User enters received OTP code
- **Account Creation**: If new user, account is automatically created
- **Session Start**: User is logged in and session is maintained

#### Option B: 📷 Face Detection Authentication (Innovative)
- **Camera Access**: System requests camera permission from user's browser
- **3-Step Face Capture Process**:
  - **Step 1**: User faces front camera - auto-captures when proper face detected
  - **Step 2**: User turns head left - auto-captures left profile view
  - **Step 3**: User turns head right - auto-captures right profile view
- **Real-time Detection**: Advanced face recognition with visual feedback
- **Photo Processing**: System saves all 3 photos (front, left, right angles)
- **Account Creation**: User account automatically created with face profile
- **Session Start**: User is logged in and session is maintained

### 3. 🛒 Shopping Experience
- **Product Browsing**: User browses Fish or Vegetable categories
- **Product Selection**: User views product details (name, price, stock, image)
- **Add to Cart**: User clicks "Add to Cart" button for desired items
- **Cart Management**: User can view cart, adjust quantities, see subtotal
- **Session Persistence**: Cart and login status maintained across page refreshes

### 4. 💳 Checkout Process
- **Cart Review**: User reviews items and total price in cart
- **Delivery Details**: User enters delivery address and contact info
- **Order Placement**: User confirms order (payment integration planned for future)
- **Order Confirmation**: User receives confirmation of successful order

### 5. 👤 User Account Management
- **Profile Access**: User can access profile section when logged in
- **Session Management**: User can logout (clears session)
- **Login Persistence**: User stays logged in until they logout or session expires

### 6. 🔒 Security & Protection
- **Route Protection**: Cart and checkout pages require authentication
- **Dual Authentication**: Both SMS OTP and face detection provide secure access
- **OTP Security**: OTP codes are hashed and have expiration time (SMS option)
- **Face Biometrics**: 3-angle face capture ensures secure biometric authentication
- **Attempt Limiting**: Failed attempts are tracked and limited
- **Session Security**: User sessions are properly managed and secured

## Admin Features (Separate Flow)
- **Admin Login**: Special admin users can access admin panel
- **Product Management**: Add new fish/vegetable products with details
- **Inventory Control**: Manage stock levels and product information

## Technical Features
- **Responsive Design**: Works on mobile and desktop devices
- **Real-time Updates**: Dynamic product display using Flask templates
- **Database Integration**: Persistent storage for users, products, and orders
- **SMS Integration**: Reliable OTP delivery via SMS API (Twilio)
- **Face Detection**: Advanced camera-based authentication with real-time feedback
- **Auto-Capture**: Smart photo capture when correct face position detected

## Key User Benefits
1. **Dual Authentication**: Choose between SMS OTP or innovative face detection
2. **Quick Registration**: No lengthy signup forms - phone or face recognition
3. **Easy Navigation**: Simple category-based product browsing
4. **Secure Shopping**: Multi-layered authentication and protected checkout
5. **Persistent Cart**: Items saved even if user refreshes page
6. **Mobile-Friendly**: Optimized for smartphone usage with camera integration

## Future Enhancements (Planned)
- Payment gateway integration
- Order tracking and history
- User ratings and reviews
- Delivery scheduling
- Push notifications for order updates