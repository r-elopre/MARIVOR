import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from auth_utils import auth_service

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Database configuration
DATABASE = os.getenv('DATABASE_URL', 'sqlite:///marivor.db').replace('sqlite:///', '')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    return conn

def get_products_by_category(category=None, limit=None):
    """Get products filtered by category"""
    conn = get_db_connection()
    if category:
        if limit:
            query = "SELECT * FROM products WHERE category = ? AND is_active = 1 ORDER BY created_at DESC LIMIT ?"
            products = conn.execute(query, (category, limit)).fetchall()
        else:
            query = "SELECT * FROM products WHERE category = ? AND is_active = 1 ORDER BY created_at DESC"
            products = conn.execute(query, (category,)).fetchall()
    else:
        if limit:
            query = "SELECT * FROM products WHERE is_active = 1 ORDER BY created_at DESC LIMIT ?"
            products = conn.execute(query, (limit,)).fetchall()
        else:
            query = "SELECT * FROM products WHERE is_active = 1 ORDER BY created_at DESC"
            products = conn.execute(query).fetchall()
    
    conn.close()
    return products

def get_featured_products():
    """Get featured products for home page (mix of fish and vegetables)"""
    conn = get_db_connection()
    
    # Get 2 fish and 2 vegetable products
    fish_products = conn.execute(
        "SELECT * FROM products WHERE category = 'Fish' AND is_active = 1 ORDER BY created_at DESC LIMIT 2"
    ).fetchall()
    
    vegetable_products = conn.execute(
        "SELECT * FROM products WHERE category = 'Vegetable' AND is_active = 1 ORDER BY created_at DESC LIMIT 2"
    ).fetchall()
    
    conn.close()
    
    # Combine and return
    featured = list(fish_products) + list(vegetable_products)
    return featured

def is_logged_in():
    """Check if user is logged in"""
    return 'user_id' in session and 'phone_number' in session

@app.context_processor
def inject_user():
    """Make user info available in all templates"""
    return {
        'is_logged_in': is_logged_in(),
        'user_phone': session.get('phone_number'),
        'cart_count': len(session.get('cart', {}))
    }

# Routes

# Authentication Routes
@app.route('/send_otp', methods=['POST'])
def send_otp():
    """Send OTP to user's phone number"""
    try:
        phone_number = request.form.get('phone_number', '').strip()
        is_resend = request.form.get('resend') == 'true'
        
        if not phone_number:
            flash('Phone number is required.', 'error')
            return redirect(url_for('login'))
        
        # Validate phone number format (10 digits)
        if not phone_number.isdigit() or len(phone_number) != 10:
            flash('Please enter a valid 10-digit Philippine phone number.', 'error')
            return redirect(url_for('login'))
        
        # Generate OTP
        otp_code = auth_service.generate_otp()
        
        # Store OTP in database
        store_result = auth_service.store_otp(phone_number, otp_code)
        if not store_result['success']:
            flash(f'Error storing OTP: {store_result["error"]}', 'error')
            return redirect(url_for('login'))
        
        # Send SMS
        sms_result = auth_service.send_sms_otp(phone_number, otp_code)
        if not sms_result['success']:
            flash(f'Error sending SMS: {sms_result["error"]}', 'error')
            return redirect(url_for('login'))
        
        # Store phone number in session for verification
        session['verification_phone'] = store_result['formatted_phone']
        session['verification_step'] = 'otp_sent'
        
        if is_resend:
            # Return JSON response for AJAX request
            return jsonify({'success': True, 'message': 'OTP sent successfully'})
        else:
            flash('Verification code sent to your phone!', 'success')
            return redirect(url_for('verify_otp_page'))
            
    except Exception as e:
        error_msg = f'Error sending OTP: {str(e)}'
        if is_resend:
            return jsonify({'success': False, 'error': error_msg})
        else:
            flash(error_msg, 'error')
            return redirect(url_for('login'))

@app.route('/verify_otp_page')
def verify_otp_page():
    """Show OTP verification page"""
    if 'verification_phone' not in session:
        flash('Please enter your phone number first.', 'warning')
        return redirect(url_for('login'))
    
    # Extract last 4 digits for display
    phone = session['verification_phone']
    display_phone = phone[-4:] if len(phone) > 4 else phone
    
    return render_template('verify_otp.html', 
                         phone_number=session['verification_phone'],
                         display_phone=display_phone)

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    """Verify OTP code and log user in"""
    try:
        phone_number = request.form.get('phone_number', '').strip()
        otp_code = request.form.get('otp_code', '').strip()
        
        # Validate inputs
        if not phone_number or not otp_code:
            flash('Phone number and OTP code are required.', 'error')
            return redirect(url_for('verify_otp_page'))
        
        # Validate OTP format
        if not otp_code.isdigit() or len(otp_code) != 6:
            flash('Please enter a valid 6-digit verification code.', 'error')
            return redirect(url_for('verify_otp_page'))
        
        # Verify OTP
        verify_result = auth_service.verify_otp(phone_number, otp_code)
        
        if not verify_result['success']:
            error_msg = verify_result['error']
            
            # Handle specific error cases
            if 'attempts' in verify_result:
                attempts_left = verify_result['attempts_left']
                if attempts_left > 0:
                    flash(f'Invalid code. {attempts_left} attempts remaining.', 'error')
                    return render_template('verify_otp.html', 
                                         phone_number=phone_number,
                                         attempts_left=attempts_left)
                else:
                    flash('Maximum attempts exceeded. Please request a new code.', 'error')
                    session.pop('verification_phone', None)
                    session.pop('verification_step', None)
                    return redirect(url_for('login'))
            else:
                flash(error_msg, 'error')
                return redirect(url_for('verify_otp_page'))
        
        # OTP verified successfully - get or create user
        user_result = auth_service.get_or_create_user(phone_number)
        
        if not user_result['success']:
            flash(f'Error creating user account: {user_result["error"]}', 'error')
            return redirect(url_for('login'))
        
        # Log user in
        user = user_result['user']
        session['user_id'] = user['id']
        session['phone_number'] = user['phone_number']
        session['is_verified'] = True
        session['is_admin'] = user.get('is_admin', False)
        
        # Clean up verification session data
        session.pop('verification_phone', None)
        session.pop('verification_step', None)
        
        # Show success message
        if user_result['is_new']:
            flash(f'Welcome to Marivor! Your account has been created.', 'success')
        else:
            flash(f'Welcome back! You\'re now logged in.', 'success')
        
        # Redirect to intended page or home
        next_page = session.pop('next_page', None)
        return redirect(next_page or url_for('home'))
        
    except Exception as e:
        flash(f'Error verifying OTP: {str(e)}', 'error')
        return redirect(url_for('verify_otp_page'))

@app.route('/')
def home():
    """Home page with featured products"""
    featured_products = get_featured_products()
    return render_template('home.html', 
                         products=featured_products,
                         page_title="Fresh Fish & Vegetables - Marivor")

@app.route('/fish')
def fish_products():
    """Fish category page"""
    fish_products = get_products_by_category('Fish')
    return render_template('category.html', 
                         products=fish_products,
                         category='Fish',
                         page_title="Fresh Fish - Marivor",
                         category_icon="🐟")

@app.route('/vegetable')
def vegetable_products():
    """Vegetable category page"""
    vegetable_products = get_products_by_category('Vegetable')
    return render_template('category.html', 
                         products=vegetable_products,
                         category='Vegetable',
                         page_title="Fresh Vegetables - Marivor",
                         category_icon="🥬")

@app.route('/cart')
def cart():
    """Shopping cart page"""
    if not is_logged_in():
        session['next_page'] = url_for('cart')
        flash('Please log in to view your cart.', 'warning')
        return redirect(url_for('login'))
    
    # For now, return a simple cart page
    # We'll implement cart functionality later
    cart_items = session.get('cart', {})
    return render_template('cart.html', 
                         cart_items=cart_items,
                         page_title="Shopping Cart - Marivor")

@app.route('/profile')
def profile():
    """User profile page"""
    if not is_logged_in():
        session['next_page'] = url_for('profile')
        flash('Please log in to view your profile.', 'warning')
        return redirect(url_for('login'))
    
    # Fetch user information from database
    conn = get_db_connection()
    user_info = conn.execute(
        'SELECT * FROM users WHERE id = ?', 
        (session['user_id'],)
    ).fetchone()
    conn.close()
    
    if not user_info:
        flash('User not found. Please log in again.', 'error')
        return redirect(url_for('logout'))
    
    return render_template('profile.html', 
                         user_info=user_info,
                         page_title="My Profile - Marivor")

@app.route('/login')
def login():
    """Login page"""
    if is_logged_in():
        return redirect(url_for('home'))
    
    return render_template('login.html', 
                         page_title="Login - Marivor")

@app.route('/face_login', methods=['POST'])
def face_login():
    """Handle face code login"""
    try:
        face_code = request.form.get('face_code', '').strip()
        
        if not face_code:
            flash('Face code is required.', 'error')
            return redirect(url_for('login'))
        
        # Validate code format (6 digits)
        if not face_code.isdigit() or len(face_code) != 6:
            flash('Please enter a valid 6-digit face code.', 'error')
            return redirect(url_for('login'))
        
        # Check if user exists with this face code
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE face_login_code = ? AND is_verified = 1',
            (face_code,)
        ).fetchone()
        conn.close()
        
        if not user:
            flash('Invalid face code. Please check your code and try again.', 'error')
            return redirect(url_for('login'))
        
        # Log user in
        session['user_id'] = user['id']
        session['phone_number'] = user['phone_number']
        session['face_login_code'] = user['face_login_code']
        session['is_verified'] = True
        session['login_method'] = 'face_code'
        
        flash(f'Welcome back, {user["username"] or user["phone_number"]}!', 'success')
        
        # Redirect to next page or home
        next_page = session.pop('next_page', None)
        return redirect(next_page if next_page else url_for('profile'))
        
    except Exception as e:
        flash('Login failed. Please try again.', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('home'))

@app.route('/face_register')
def face_register():
    """Face detection registration page"""
    if is_logged_in():
        return redirect(url_for('home'))
    
    return render_template('face_register.html', 
                         page_title="Face Registration - Marivor")

@app.route('/register_face', methods=['POST'])
def register_face():
    """Handle face registration with photos"""
    try:
        data = request.json
        photos = data.get('photos', [])
        
        if len(photos) != 3:
            return jsonify({'success': False, 'error': 'Invalid number of photos'})
        
        # Generate a unique user ID and 6-digit login code
        import uuid
        import random
        user_id = str(uuid.uuid4())[:8]
        face_code = f"{random.randint(100000, 999999)}"  # 6-digit code
        username = f"face_{user_id}"
        
        # Store photos (in production, save to file system or cloud storage)
        import base64
        
        # Create user photos directory
        user_dir = f"static/face_photos/{user_id}"
        os.makedirs(user_dir, exist_ok=True)
        
        photo_paths = []
        for i, photo in enumerate(photos):
            # Remove data URL prefix
            photo_data = photo['data'].split(',')[1]
            photo_bytes = base64.b64decode(photo_data)
            
            # Save photo
            photo_path = f"{user_dir}/{photo['direction']}.jpg"
            with open(photo_path, 'wb') as f:
                f.write(photo_bytes)
            photo_paths.append(photo_path)
        
        # Create user account in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if users table has the required columns
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'face_photos_path' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN face_photos_path TEXT')
        if 'face_login_code' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN face_login_code VARCHAR(6)')
        if 'username' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN username VARCHAR(50)')
        
        conn.commit()
        
        # Insert new user
        cursor.execute('''
            INSERT INTO users (phone_number, username, face_login_code, face_photos_path, created_at, is_verified) 
            VALUES (?, ?, ?, ?, datetime('now'), 1)
        ''', (username, username, face_code, ','.join(photo_paths)))
        
        user_id_db = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Set session (log user in)
        session['user_id'] = user_id_db
        session['phone_number'] = username
        session['face_login_code'] = face_code
        session['is_verified'] = True
        session['registration_method'] = 'face'
        
        return jsonify({
            'success': True, 
            'message': 'Face registration completed successfully!',
            'user_id': user_id,
            'username': username,
            'face_code': face_code
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return "<h1>404 - Page Not Found</h1><p>The page you're looking for doesn't exist.</p>", 404

@app.errorhandler(500)
def internal_error(error):
    return "<h1>500 - Internal Server Error</h1><p>Something went wrong on our end.</p>", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)