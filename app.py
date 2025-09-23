import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from supabase_utils import get_supabase_client

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
    """User profile page using Supabase"""
    if not is_logged_in():
        session['next_page'] = url_for('profile')
        flash('Please log in to view your profile.', 'warning')
        return redirect(url_for('login'))
    
    # Fetch user information from Supabase database
    try:
        supabase_client = get_supabase_client()
        user_info = supabase_client.get_user_by_id(session['user_id'])
        
        if not user_info:
            flash('User not found. Please log in again.', 'error')
            return redirect(url_for('logout'))
        
        # Convert string date to datetime object for template compatibility
        if user_info.get('created_at') and isinstance(user_info['created_at'], str):
            from datetime import datetime
            try:
                # Parse ISO format date string (e.g., "2023-09-23T12:34:56.789Z")
                user_info['created_at'] = datetime.fromisoformat(user_info['created_at'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                # If parsing fails, keep as string and handle in template
                pass
        
        return render_template('profile.html', 
                             user_info=user_info,
                             page_title="My Profile - Marivor")
    
    except Exception as e:
        print(f"Profile fetch error: {e}")
        flash('Error loading profile. Please try again.', 'error')
        return redirect(url_for('home'))

@app.route('/login')
def login():
    """Login page"""
    if is_logged_in():
        return redirect(url_for('home'))
    
    return render_template('login.html', 
                         page_title="Login - Marivor")

@app.route('/face_login', methods=['POST'])
def face_login():
    """Handle face code login using Supabase"""
    try:
        face_code = request.form.get('face_code', '').strip()
        
        if not face_code:
            flash('Face code is required.', 'error')
            return redirect(url_for('login'))
        
        # Validate code format (6 digits)
        if not face_code.isdigit() or len(face_code) != 6:
            flash('Please enter a valid 6-digit face code.', 'error')
            return redirect(url_for('login'))
        
        # Get Supabase client and check if user exists with this face code
        supabase_client = get_supabase_client()
        user = supabase_client.get_user_by_face_code(face_code)
        
        if not user:
            flash('Invalid face code. Please check your code and try again.', 'error')
            return redirect(url_for('login'))
        
        # Log user in
        session['user_id'] = user['id']
        session['phone_number'] = user['phone_number']
        session['face_login_code'] = user['face_login_code']
        session['is_verified'] = True
        session['login_method'] = 'face_code'
        
        flash(f'Welcome back, {user.get("username") or user["phone_number"]}!', 'success')
        
        # Redirect to next page or home
        next_page = session.pop('next_page', None)
        return redirect(next_page if next_page else url_for('profile'))
        
    except Exception as e:
        print(f"Face login error: {e}")
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
    """Handle face registration with photos using Supabase"""
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
        
        # Get Supabase client
        supabase_client = get_supabase_client()
        
        # Debug: Print received photos data
        print(f"Received {len(photos)} photos")
        for i, photo in enumerate(photos):
            print(f"Photo {i+1}: direction={photo.get('direction', 'unknown')}, data_type={type(photo.get('data'))}")
            if isinstance(photo.get('data'), str):
                print(f"Photo {i+1}: data_length={len(photo.get('data', ''))}")
            else:
                print(f"Photo {i+1}: data_value={photo.get('data')}")
        
        # Upload photos to Supabase Storage
        photo_urls = {}
        for photo in photos:
            direction = photo['direction']  # 'front', 'left', 'right'
            photo_data = photo['data']
            
            # Upload to Supabase Storage
            photo_url = supabase_client.upload_face_photo(user_id, photo_data, direction)
            if not photo_url:
                return jsonify({'success': False, 'error': f'Failed to upload {direction} photo'})
            
            photo_urls[direction] = photo_url
        
        # Create user account in Supabase database
        user_result = supabase_client.create_user(
            username=username,
            phone_number=username,  # Using username as phone for face users
            face_login_code=face_code,
            auth_type='face'
        )
        
        if not user_result['success']:
            return jsonify({'success': False, 'error': 'Failed to create user account'})
        
        user_data = user_result['data']
        user_id_db = user_data['id']
        
        # Update user with photo URLs
        update_success = supabase_client.update_user_photos(
            user_id_db,
            photo_urls.get('front', ''),
            photo_urls.get('left', ''),
            photo_urls.get('right', '')
        )
        
        if not update_success:
            return jsonify({'success': False, 'error': 'Failed to save photo references'})
        
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
        print(f"Face registration error: {e}")
        return jsonify({'success': False, 'error': f'Registration failed: {str(e)}'})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return "<h1>404 - Page Not Found</h1><p>The page you're looking for doesn't exist.</p>", 404

@app.errorhandler(500)
def internal_error(error):
    return "<h1>500 - Internal Server Error</h1><p>Something went wrong on our end.</p>", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)