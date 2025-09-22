# 🐟 Marivor - Fish & Vegetable Marketplace

A modern web application for ordering fresh fish and vegetables with innovative face detection authentication.

## ✨ Features Implemented

### 🔐 Authentication System
- **SMS OTP Verification** - Traditional phone number authentication via Twilio
- **Face Detection Registration** - AI-powered face recognition using face-api.js
- **6-Digit Face Login Codes** - Quick login alternative to SMS
- **User Profile Management** - View account details and face login codes

### 🛒 E-commerce Core
- **Product Categories** - Fish and Vegetable sections
- **Shopping Cart** - Session-based cart management
- **Product Display** - Grid layout with images and pricing
- **Responsive Design** - Mobile-friendly interface

### 🤖 AI Face Detection
- **Real-time Face Detection** - Uses TinyFaceDetector ML model
- **Direction Analysis** - Captures front, left, and right face angles
- **Auto-capture** - Smart photo capture when face is properly positioned
- **Visual Feedback** - Color-coded overlay for detection status

### 💾 Database Structure
- **SQLite Database** - User management and product storage
- **Face Photo Storage** - File-based image storage with database paths
- **User Sessions** - Secure session management
- **Order Tracking** - Order and cart item persistence

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, Bootstrap 5, JavaScript
- **AI/ML**: face-api.js with TinyFaceDetector
- **Database**: SQLite
- **Authentication**: Twilio SMS + Custom Face Recognition
- **Storage**: Local file system (photos)

## 📁 Project Structure

```
Marivor/
├── app.py                 # Main Flask application
├── auth_utils.py          # Authentication utilities
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── face_register.html # Face detection registration
│   ├── login.html        # Login page with SMS and face options
│   ├── profile.html      # User profile with face code display
│   └── ...
├── static/              # Static assets
│   ├── css/             # Stylesheets
│   ├── js/              # JavaScript files
│   └── face_photos/     # User face photos (excluded from git)
├── scripts/             # Database and utility scripts
└── requirements.txt     # Python dependencies
```

## 🚀 Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/r-elopre/MARIVOR.git
   cd MARIVOR
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file with:
   SECRET_KEY=your_secret_key
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   TWILIO_PHONE_NUMBER=your_twilio_number
   ```

5. **Initialize database**
   ```bash
   python scripts/create_database.py
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

## 🎯 Usage

### Face Registration
1. Visit `/face_register`
2. Allow camera access
3. Follow the 3-step process (front, left, right)
4. Get your 6-digit login code
5. Access your profile to view the code anytime

### Face Login
1. Visit `/login`
2. Click "Login with Face Code"
3. Enter your 6-digit code
4. Instant access to your account

## 🔮 Future Plans

### 📊 Database Migration
- **Moving to Supabase** - PostgreSQL database with built-in image storage
- **Cloud Image Storage** - Secure and scalable photo management
- **Better Performance** - Faster queries and image serving

### 🛡️ Security Enhancements
- **Photo Encryption** - Encrypt stored face photos
- **Privacy Controls** - User data deletion options
- **GDPR Compliance** - Enhanced privacy protection

### 🚀 Feature Roadmap
- **Real-time Order Tracking**
- **Payment Integration**
- **Delivery Management**
- **Admin Dashboard**
- **Mobile App** (React Native)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **face-api.js** - For the excellent face detection library
- **Twilio** - For SMS authentication services
- **Bootstrap** - For the responsive UI framework