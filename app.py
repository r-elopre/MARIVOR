import os
from datetime import datetime
import os
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
from supabase_utils import get_supabase_client

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# All database operations now handled through Supabase

# Removed unused helper functions - products now handled directly in home route


def is_logged_in():
    """Check if user is logged in"""
    # Check for customer login
    customer_logged_in = 'user_id' in session and 'phone_number' in session
    # Check for seller login
    seller_logged_in = 'seller_id' in session and 'user_type' in session and session.get('user_type') == 'seller'
    
    return customer_logged_in or seller_logged_in

@app.context_processor
def inject_user():
    """Make user info available in all templates"""
    return {
        'is_logged_in': is_logged_in(),
        'user_phone': session.get('phone_number'),
        'user_type': session.get('user_type', 'customer'),
        'store_name': session.get('store_name'),
        'is_seller': session.get('user_type') == 'seller',
        'is_admin': session.get('is_admin', False),
        'cart_count': len(session.get('cart', {}))
    }

# Routes

# Authentication Routes
@app.route('/')
def home():
    """Home page with all products and filtering/sorting"""
    # Get query parameters
    category = request.args.get('category', 'all')  # all, Fish, Vegetables
    sort_by = request.args.get('sort', 'newest')     # newest, price_low, price_high
    
    try:
        supabase_client = get_supabase_client()
        
        # Get all products
        if category == 'all':
            products = supabase_client.get_all_products()
        else:
            products = supabase_client.get_products_by_category(category)
        
        # Sort products
        if sort_by == 'price_low':
            products = sorted(products, key=lambda x: x.get('price', 0))
        elif sort_by == 'price_high':
            products = sorted(products, key=lambda x: x.get('price', 0), reverse=True)
        elif sort_by == 'newest':
            # Sort by created_at descending (newest first)
            products = sorted(products, key=lambda x: x.get('created_at', ''), reverse=True)
        
        return render_template('home.html', 
                             products=products,
                             current_category=category,
                             current_sort=sort_by,
                             page_title="Fresh Fish & Vegetables - Marivor")
    
    except Exception as e:
        print(f"Error loading products: {e}")
        return render_template('home.html', 
                             products=[],
                             current_category='all',
                             current_sort='newest',
                             page_title="Fresh Fish & Vegetables - Marivor")

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
    """Handle face code login using Supabase - supports both customer and seller codes"""
    try:
        face_code = request.form.get('face_code', '').strip()
        
        if not face_code:
            flash('Face code is required.', 'error')
            return redirect(url_for('login'))
        
        # Validate code format (6 digits)
        if not face_code.isdigit() or len(face_code) != 6:
            flash('Please enter a valid 6-digit face code.', 'error')
            return redirect(url_for('login'))
        
        supabase_client = get_supabase_client()
        
        # First, check if it's a customer face code
        user = supabase_client.get_user_by_face_code(face_code)
        
        if user:
            # Customer login
            session['user_id'] = user['id']
            session['phone_number'] = user['phone_number']
            session['face_login_code'] = user['face_login_code']
            session['user_type'] = user.get('user_type', 'customer')
            session['seller_id'] = user.get('seller_id')
            session['is_verified'] = True
            session['login_method'] = 'face_code'
            
            flash(f'Welcome back, {user.get("username") or user["phone_number"]}!', 'success')
            
            # Redirect based on user type
            if session['user_type'] == 'seller':
                return redirect(url_for('seller_dashboard'))
            else:
                next_page = session.pop('next_page', None)
                return redirect(next_page if next_page else url_for('home'))
        
        # If not a customer code, check if it's a seller code
        seller = supabase_client.get_seller_by_code(face_code)
        
        if seller:
            # Seller login
            session['seller_id'] = seller['id']
            session['user_type'] = 'seller'
            session['store_name'] = seller['store_name']
            session['seller_code'] = seller['seller_code']
            session['is_verified'] = True
            session['login_method'] = 'seller_code'
            
            flash(f'Welcome back, {seller["store_name"]}!', 'success')
            return redirect(url_for('seller_dashboard'))
        
        # Neither customer nor seller code found
        flash('Invalid code. Please check your code and try again.', 'error')
        return redirect(url_for('login'))
        
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

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Hardcoded admin credentials (you can change these)
        ADMIN_USERNAME = "marivor_admin"
        ADMIN_PASSWORD = "admin123!@#"
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['is_admin'] = True
            session['admin_username'] = username
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials!', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin')
@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard - overview"""
    if not session.get('is_admin'):
        flash('Admin access required!', 'error')
        return redirect(url_for('admin_login'))
    
    try:
        supabase_client = get_supabase_client()
        
        # Get statistics
        all_products = supabase_client.get_all_products()
        processed_orders = supabase_client.get_orders_by_status('processed')
        delivery_orders = supabase_client.get_orders_by_status('on_delivery')
        
        stats = {
            'total_products': len(all_products),
            'fish_products': len([p for p in all_products if p['category'] == 'Fish']),
            'vegetable_products': len([p for p in all_products if p['category'] == 'Vegetables']),
            'processed_orders': len(processed_orders),
            'delivery_orders': len(delivery_orders)
        }
        
        return render_template('admin/dashboard.html', stats=stats)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('admin/dashboard.html', stats={})

@app.route('/admin/orders')
def admin_orders():
    """Admin orders management"""
    if not session.get('is_admin'):
        flash('Admin access required!', 'error')
        return redirect(url_for('admin_login'))
    
    try:
        supabase_client = get_supabase_client()
        status_filter = request.args.get('status', 'all')
        
        if status_filter == 'all':
            orders = supabase_client.get_all_orders()
        else:
            orders = supabase_client.get_orders_by_status(status_filter)
        
        return render_template('admin/orders.html', orders=orders, current_filter=status_filter)
    except Exception as e:
        flash(f'Error loading orders: {str(e)}', 'error')
        return render_template('admin/orders.html', orders=[], current_filter='all')

@app.route('/admin/orders/update_status/<int:order_id>', methods=['POST'])
def admin_update_order_status(order_id):
    """Update order status"""
    if not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Admin access required'})
    
    try:
        new_status = request.form.get('status')
        
        supabase_client = get_supabase_client()
        success = supabase_client.update_order_status(order_id, new_status)
        
        if success:
            flash(f'Order #{order_id} status updated to {new_status}!', 'success')
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to update order status'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/products')
def admin_products():
    """Admin products management"""
    if not session.get('is_admin'):
        flash('Admin access required!', 'error')
        return redirect(url_for('admin_login'))
    
    try:
        supabase_client = get_supabase_client()
        products = supabase_client.get_all_products()
        return render_template('admin/products.html', products=products)
    except Exception as e:
        flash(f'Error loading products: {str(e)}', 'error')
        return render_template('admin/products.html', products=[])

@app.route('/admin/products/add', methods=['GET', 'POST'])
def admin_add_product():
    """Add new product"""
    if not session.get('is_admin'):
        flash('Admin access required!', 'error')
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            category = request.form.get('category')
            price = float(request.form.get('price'))
            stock = int(request.form.get('stock'))
            unit = bool(request.form.get('unit'))  # True if checked, False if unchecked
            
            # Handle file upload (required)
            image_file = request.files.get('image_file')
            
            if not image_file or not image_file.filename:
                flash('Please upload an image file.', 'error')
                return render_template('admin/add_product.html')
            
            # Validate file type
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            file_extension = image_file.filename.rsplit('.', 1)[1].lower() if '.' in image_file.filename else ''
            
            if file_extension not in allowed_extensions:
                flash('Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WebP images only.', 'error')
                return render_template('admin/add_product.html')
            
            # Validate file size (5MB limit)
            image_file_data = image_file.read()
            if len(image_file_data) > 5 * 1024 * 1024:  # 5MB
                flash('File size too large. Please upload an image smaller than 5MB.', 'error')
                return render_template('admin/add_product.html')
            
            supabase_client = get_supabase_client()
            
            # Use the method that handles image upload
            result = supabase_client.add_product_with_image(
                name, category, price, stock, unit,
                image_file_data, image_file.filename, ""
            )
            
            if result['success']:
                flash(f'Product "{name}" added successfully!', 'success')
                return redirect(url_for('admin_products'))
            else:
                flash(f'Error adding product: {result["error"]}', 'error')
        except Exception as e:
            flash(f'Error adding product: {str(e)}', 'error')
    
    return render_template('admin/add_product.html')

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    """Edit existing product"""
    if not session.get('is_admin'):
        flash('Admin access required!', 'error')
        return redirect(url_for('admin_login'))
    
    try:
        supabase_client = get_supabase_client()
        
        if request.method == 'POST':
            name = request.form.get('name')
            category = request.form.get('category')
            price = float(request.form.get('price')) if request.form.get('price') else None
            stock = int(request.form.get('stock')) if request.form.get('stock') else None
            unit = bool(request.form.get('unit'))  # True if checked, False if unchecked
            
            # Handle file upload (optional for edit)
            image_file = request.files.get('image_file')
            image_file_data = None
            image_filename = None
            
            if image_file and image_file.filename:
                # Validate file type
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                file_extension = image_file.filename.rsplit('.', 1)[1].lower() if '.' in image_file.filename else ''
                
                if file_extension not in allowed_extensions:
                    flash('Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WebP images only.', 'error')
                    # Get product data for the form
                    products = supabase_client.get_all_products()
                    product = next((p for p in products if p['id'] == product_id), None)
                    return render_template('admin/edit_product.html', product=product)
                
                # Validate file size (5MB limit)
                image_file_data = image_file.read()
                if len(image_file_data) > 5 * 1024 * 1024:  # 5MB
                    flash('File size too large. Please upload an image smaller than 5MB.', 'error')
                    # Get product data for the form
                    products = supabase_client.get_all_products()
                    product = next((p for p in products if p['id'] == product_id), None)
                    return render_template('admin/edit_product.html', product=product)
                
                image_filename = image_file.filename
            
            # Use the new method that handles image upload
            result = supabase_client.update_product_with_image(
                product_id, name, category, price, stock, unit,
                image_file_data, image_filename, None
            )
            
            if result['success']:
                flash('Product updated successfully!', 'success')
                return redirect(url_for('admin_products'))
            else:
                flash(f'Error updating product: {result["error"]}', 'error')
        
        # Get product data for the form
        products = supabase_client.get_all_products()
        product = next((p for p in products if p['id'] == product_id), None)
        
        if not product:
            flash('Product not found!', 'error')
            return redirect(url_for('admin_products'))
        
        return render_template('admin/edit_product.html', product=product)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin_products'))

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
def admin_delete_product(product_id):
    """Delete product"""
    if not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Admin access required'})
    
    try:
        supabase_client = get_supabase_client()
        success = supabase_client.delete_product(product_id)
        
        if success:
            flash('Product deleted successfully!', 'success')
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to delete product'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/sellers')
def admin_sellers():
    """Admin seller management"""
    if not session.get('is_admin'):
        flash('Admin access required!', 'error')
        return redirect(url_for('admin_login'))
    
    try:
        supabase_client = get_supabase_client()
        sellers = supabase_client.get_all_sellers()
        
        # Get product count for each seller
        for seller in sellers:
            seller_products = supabase_client.get_seller_products(seller['id'])
            seller['product_count'] = len(seller_products)
        
        return render_template('admin/sellers.html', sellers=sellers)
    except Exception as e:
        flash(f'Error loading sellers: {str(e)}', 'error')
        return render_template('admin/sellers.html', sellers=[])

@app.route('/admin/sellers/add', methods=['GET', 'POST'])
def admin_add_seller():
    """Add new seller"""
    if not session.get('is_admin'):
        flash('Admin access required!', 'error')
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        try:
            store_name = request.form.get('store_name')
            
            if not store_name:
                flash('Store name is required!', 'error')
                return render_template('admin/add_seller.html')
            
            supabase_client = get_supabase_client()
            
            # Generate unique seller code
            seller_code = supabase_client.generate_seller_code()
            
            # Handle store image upload (optional)
            store_image_url = ""
            image_file = request.files.get('store_image')
            
            if image_file and image_file.filename:
                # Validate file type
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                file_extension = image_file.filename.rsplit('.', 1)[1].lower() if '.' in image_file.filename else ''
                
                if file_extension not in allowed_extensions:
                    flash('Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WebP images only.', 'error')
                    return render_template('admin/add_seller.html')
                
                # Validate file size (5MB limit)
                image_file_data = image_file.read()
                if len(image_file_data) > 5 * 1024 * 1024:  # 5MB
                    flash('File size too large. Please upload an image smaller than 5MB.', 'error')
                    return render_template('admin/add_seller.html')
                
                # First create seller to get ID, then upload image
                result = supabase_client.create_seller_account(store_name, seller_code)
                
                if result['success']:
                    seller_data = result['data']
                    seller_id = seller_data['id']
                    
                    # Upload store image
                    content_type = 'image/jpeg'
                    if image_file.filename.lower().endswith('.png'):
                        content_type = 'image/png'
                    elif image_file.filename.lower().endswith('.gif'):
                        content_type = 'image/gif'
                    elif image_file.filename.lower().endswith('.webp'):
                        content_type = 'image/webp'
                    
                    upload_result = supabase_client.upload_store_image(seller_id, image_file_data, image_file.filename, content_type)
                    
                    if upload_result['success']:
                        store_image_url = upload_result['url']
                        # Update seller with image URL
                        supabase_client.update_seller(seller_id, store_image_url=store_image_url)
                    
                    flash(f'Seller "{store_name}" created successfully! Seller code: {seller_code}', 'success')
                    return redirect(url_for('admin_sellers'))
                else:
                    flash(f'Error creating seller: {result["error"]}', 'error')
            else:
                # No image, just create seller
                result = supabase_client.create_seller_account(store_name, seller_code)
                
                if result['success']:
                    flash(f'Seller "{store_name}" created successfully! Seller code: {seller_code}', 'success')
                    return redirect(url_for('admin_sellers'))
                else:
                    flash(f'Error creating seller: {result["error"]}', 'error')
        
        except Exception as e:
            flash(f'Error creating seller: {str(e)}', 'error')
    
    return render_template('admin/add_seller.html')

@app.route('/admin/sellers/edit/<int:seller_id>', methods=['GET', 'POST'])
def admin_edit_seller(seller_id):
    """Edit existing seller"""
    if not session.get('is_admin'):
        flash('Admin access required!', 'error')
        return redirect(url_for('admin_login'))
    
    try:
        supabase_client = get_supabase_client()
        
        if request.method == 'POST':
            store_name = request.form.get('store_name')
            is_active = bool(request.form.get('is_active'))
            
            update_data = {
                'store_name': store_name,
                'is_active': is_active
            }
            
            # Handle store image upload (optional)
            image_file = request.files.get('store_image')
            
            if image_file and image_file.filename:
                # Validate file type
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                file_extension = image_file.filename.rsplit('.', 1)[1].lower() if '.' in image_file.filename else ''
                
                if file_extension not in allowed_extensions:
                    flash('Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WebP images only.', 'error')
                    seller = supabase_client.get_seller_by_id(seller_id)
                    return render_template('admin/edit_seller.html', seller=seller)
                
                # Validate file size (5MB limit)
                image_file_data = image_file.read()
                if len(image_file_data) > 5 * 1024 * 1024:  # 5MB
                    flash('File size too large. Please upload an image smaller than 5MB.', 'error')
                    seller = supabase_client.get_seller_by_id(seller_id)
                    return render_template('admin/edit_seller.html', seller=seller)
                
                # Upload new store image
                content_type = 'image/jpeg'
                if image_file.filename.lower().endswith('.png'):
                    content_type = 'image/png'
                elif image_file.filename.lower().endswith('.gif'):
                    content_type = 'image/gif'
                elif image_file.filename.lower().endswith('.webp'):
                    content_type = 'image/webp'
                
                upload_result = supabase_client.upload_store_image(seller_id, image_file_data, image_file.filename, content_type)
                
                if upload_result['success']:
                    update_data['store_image_url'] = upload_result['url']
            
            success = supabase_client.update_seller(seller_id, **update_data)
            
            if success:
                flash('Seller updated successfully!', 'success')
                return redirect(url_for('admin_sellers'))
            else:
                flash('Error updating seller!', 'error')
        
        # Get seller data for the form
        seller = supabase_client.get_seller_by_id(seller_id)
        
        if not seller:
            flash('Seller not found!', 'error')
            return redirect(url_for('admin_sellers'))
        
        return render_template('admin/edit_seller.html', seller=seller)
    
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin_sellers'))

@app.route('/admin/sellers/toggle/<int:seller_id>', methods=['POST'])
def admin_toggle_seller(seller_id):
    """Toggle seller active status"""
    if not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Admin access required'})
    
    try:
        supabase_client = get_supabase_client()
        seller = supabase_client.get_seller_by_id(seller_id)
        
        if not seller:
            return jsonify({'success': False, 'error': 'Seller not found'})
        
        new_status = not seller['is_active']
        success = supabase_client.update_seller(seller_id, is_active=new_status)
        
        if success:
            status_text = "activated" if new_status else "deactivated"
            flash(f'Seller {status_text} successfully!', 'success')
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to update seller status'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Seller routes
@app.route('/seller')
@app.route('/seller/dashboard')
def seller_dashboard():
    """Seller dashboard"""
    if session.get('user_type') != 'seller':
        flash('Seller access required!', 'error')
        return redirect(url_for('login'))
    
    try:
        supabase_client = get_supabase_client()
        seller_id = session.get('seller_id')
        
        # Get seller info - handle as simple dict for now
        try:
            seller = supabase_client.get_seller_by_id(seller_id)
        except:
            seller = None
            
        if not seller:
            # Create a basic seller object from session data
            seller = {
                'store_name': session.get('store_name', 'My Store'),
                'seller_code': session.get('user_id', 'UNKNOWN'),
                'description': 'Welcome to your store!',
                'is_active': True,
                'created_at': 'Recently',
                'store_image_url': None
            }
        
        # Get seller's products - handle gracefully if method doesn't exist
        try:
            products = supabase_client.get_seller_products(seller_id) or []
        except:
            products = []
        
        # Calculate stats
        stats = {
            'total_products': len(products),
            'fish_products': len([p for p in products if p.get('category') == 'Fish']),
            'vegetable_products': len([p for p in products if p.get('category') == 'Vegetables']),
            'out_of_stock': len([p for p in products if p.get('stock', 0) == 0]),
            'total_orders': 0,
            'total_revenue': 0.0,
            'monthly_revenue': 0.0,
            'monthly_orders': 0
        }
        
        return render_template('seller/dashboard.html', seller=seller, stats=stats, products=products[:5])  # Show last 5 products
    
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        # Provide basic fallback data
        seller = {
            'store_name': session.get('store_name', 'My Store'),
            'seller_code': session.get('user_id', 'UNKNOWN'),
            'description': 'Welcome to your store!',
            'is_active': True,
            'created_at': 'Recently',
            'store_image_url': None
        }
        stats = {
            'total_products': 0,
            'fish_products': 0,
            'vegetable_products': 0,
            'out_of_stock': 0,
            'total_orders': 0,
            'total_revenue': 0.0,
            'monthly_revenue': 0.0,
            'monthly_orders': 0
        }
        return render_template('seller/dashboard.html', seller=seller, stats=stats, products=[])

@app.route('/seller/products')
def seller_products():
    """Seller products management"""
    if session.get('user_type') != 'seller':
        flash('Seller access required!', 'error')
        return redirect(url_for('login'))
    
    try:
        supabase_client = get_supabase_client()
        seller_id = session.get('seller_id')
        
        # Try to get products, but handle if method doesn't exist
        try:
            products = supabase_client.get_seller_products(seller_id) or []
        except AttributeError:
            # Method doesn't exist yet, return empty list
            products = []
        except Exception as e:
            print(f"Error getting products: {e}")
            products = []
            
        # Get unique categories for filtering
        categories = list(set([p.get('category', 'Other') for p in products if p.get('category')]))
        
        return render_template('seller/products.html', products=products, categories=categories)
    
    except Exception as e:
        flash(f'Error loading products: {str(e)}', 'error')
        return render_template('seller/products.html', products=[], categories=[])

@app.route('/seller/products/add', methods=['GET', 'POST'])
def seller_add_product():
    """Add new product as seller"""
    if session.get('user_type') != 'seller':
        flash('Seller access required!', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            category = request.form.get('category', '').strip()
            description = request.form.get('description', '').strip()
            price = request.form.get('price')
            stock = request.form.get('stock')
            unit = request.form.get('unit')  # This will be 'on' if checked, None if not
            seller_id = session.get('seller_id')
            
            # Validate required fields
            if not name:
                flash('Product name is required!', 'error')
                return render_template('seller/add_product.html')
            
            if not category:
                flash('Category is required!', 'error')
                return render_template('seller/add_product.html')
            
            # Validate and convert numeric fields
            try:
                price = float(price)
                if price <= 0:
                    flash('Price must be greater than 0!', 'error')
                    return render_template('seller/add_product.html')
            except (ValueError, TypeError):
                flash('Please enter a valid price!', 'error')
                return render_template('seller/add_product.html')
            
            try:
                stock = int(stock)
                if stock < 0:
                    flash('Stock cannot be negative!', 'error')
                    return render_template('seller/add_product.html')
            except (ValueError, TypeError):
                flash('Please enter a valid stock quantity!', 'error')
                return render_template('seller/add_product.html')
            
            # Convert unit checkbox to boolean
            unit_bool = unit == 'on'
            
            # Handle image upload
            image_url = None
            images = request.files.getlist('images')
            
            if images and images[0].filename:
                image_file = images[0]  # Take the first image
                
                # Validate file type
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                file_extension = image_file.filename.rsplit('.', 1)[1].lower() if '.' in image_file.filename else ''
                
                if file_extension not in allowed_extensions:
                    flash('Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WebP images only.', 'error')
                    return render_template('seller/add_product.html')
                
                # Validate file size (2MB limit)
                image_file.seek(0, 2)  # Seek to end
                file_size = image_file.tell()
                image_file.seek(0)  # Reset to beginning
                
                if file_size > 2 * 1024 * 1024:  # 2MB
                    flash('File size too large. Please upload an image smaller than 2MB.', 'error')
                    return render_template('seller/add_product.html')
                
                # Upload image to Supabase Storage
                try:
                    supabase_client = get_supabase_client()
                    
                    # Upload using the new method
                    image_data = image_file.read()
                    image_url = supabase_client.upload_product_image(seller_id, image_data, image_file.filename)
                        
                except Exception as e:
                    print(f"Image upload error: {e}")
                    flash('Failed to upload image. Please try again.', 'error')
                    return render_template('seller/add_product.html')
            
            # Insert product into database
            try:
                supabase_client = get_supabase_client()
                
                result = supabase_client.add_product(
                    name=name,
                    category=category,
                    description=description,
                    price=price,
                    stock=stock,
                    unit=unit_bool,
                    image_url=image_url,
                    seller_id=seller_id,
                    created_by='seller'
                )
                
                if result['success']:
                    flash(f'Product "{name}" added successfully!', 'success')
                    return redirect(url_for('seller_products'))
                else:
                    flash(f'Failed to add product: {result.get("error", "Unknown error")}', 'error')
                    return render_template('seller/add_product.html')
                    
            except Exception as e:
                print(f"Database error: {e}")
                flash('Failed to save product. Please try again.', 'error')
                return render_template('seller/add_product.html')
        
        except Exception as e:
            print(f"General error: {e}")
            flash(f'Error adding product: {str(e)}', 'error')
            return render_template('seller/add_product.html')
    
    # GET request - show the form
    return render_template('seller/add_product.html')

@app.route('/seller/store-settings', methods=['GET', 'POST'])
def seller_store_settings():
    """Seller store settings"""
    if session.get('user_type') != 'seller':
        flash('Seller access required!', 'error')
        return redirect(url_for('login'))
    
    try:
        supabase_client = get_supabase_client()
        seller_id = session.get('seller_id')
        
        if request.method == 'POST':
            store_name = request.form.get('store_name')
            
            update_data = {
                'store_name': store_name
            }
            
            # Handle store image upload (optional)
            image_file = request.files.get('store_image')
            
            if image_file and image_file.filename:
                # Validate file type
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                file_extension = image_file.filename.rsplit('.', 1)[1].lower() if '.' in image_file.filename else ''
                
                if file_extension not in allowed_extensions:
                    flash('Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WebP images only.', 'error')
                    seller = supabase_client.get_seller_by_id(seller_id)
                    return render_template('seller/store_settings.html', seller=seller)
                
                # Validate file size (5MB limit)
                image_file_data = image_file.read()
                if len(image_file_data) > 5 * 1024 * 1024:  # 5MB
                    flash('File size too large. Please upload an image smaller than 5MB.', 'error')
                    seller = supabase_client.get_seller_by_id(seller_id)
                    return render_template('seller/store_settings.html', seller=seller)
                
                # Upload new store image
                content_type = 'image/jpeg'
                if image_file.filename.lower().endswith('.png'):
                    content_type = 'image/png'
                elif image_file.filename.lower().endswith('.gif'):
                    content_type = 'image/gif'
                elif image_file.filename.lower().endswith('.webp'):
                    content_type = 'image/webp'
                
                upload_result = supabase_client.upload_store_image(seller_id, image_file_data, image_file.filename, content_type)
                
                if upload_result['success']:
                    update_data['store_image_url'] = upload_result['url']
            
            success = supabase_client.update_seller(seller_id, **update_data)
            
            if success:
                # Update session store name
                session['store_name'] = store_name
                flash('Store settings updated successfully!', 'success')
                return redirect(url_for('seller_store_settings'))
            else:
                flash('Error updating store settings!', 'error')
        
        # Get seller data for the form
        seller = supabase_client.get_seller_by_id(seller_id)
        
        if not seller:
            flash('Seller not found!', 'error')
            return redirect(url_for('logout'))
        
        return render_template('seller/store_settings.html', seller=seller)
    
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('seller_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('is_admin', None)
    session.pop('admin_username', None)
    flash('Admin logged out successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/seller/logout')
def seller_logout():
    """Seller logout"""
    session.pop('user_type', None)
    session.pop('seller_id', None)
    session.pop('store_name', None)
    session.pop('user_id', None)
    session.pop('phone_number', None)
    flash('Seller logged out successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/seller/products/edit/<int:product_id>', methods=['GET', 'POST'])
def seller_edit_product(product_id):
    """Edit seller product"""
    if session.get('user_type') != 'seller':
        flash('Seller access required!', 'error')
        return redirect(url_for('login'))
    
    return render_template('seller/edit_product.html', product={'id': product_id, 'name': 'Sample Product', 'price': 100, 'stock': 10, 'category': 'Other', 'images': []})

@app.route('/seller/products/delete/<int:product_id>', methods=['POST'])
def seller_delete_product(product_id):
    """Delete seller product"""
    if session.get('user_type') != 'seller':
        return redirect(url_for('login'))
    
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('seller_products'))

@app.route('/seller/orders')
def seller_orders():
    """Seller orders page"""
    if session.get('user_type') != 'seller':
        flash('Seller access required!', 'error')
        return redirect(url_for('login'))
    
    return render_template('seller/orders.html', orders=[])

@app.route('/seller/settings', methods=['GET', 'POST'])
def seller_settings():
    """Seller settings page"""
    if session.get('user_type') != 'seller':
        flash('Seller access required!', 'error')
        return redirect(url_for('login'))
    
    # Sample seller info
    seller_info = {
        'seller_code': session.get('user_id', 'UNKNOWN'),
        'store_name': session.get('store_name', 'My Store'),
        'description': '',
        'is_active': True,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    
    stats = {
        'total_products': 0,
        'total_orders': 0,
        'total_revenue': 0.0
    }
    
    return render_template('seller/settings.html', seller_info=seller_info, stats=stats)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return "<h1>404 - Page Not Found</h1><p>The page you're looking for doesn't exist.</p>", 404

@app.errorhandler(500)
def internal_error(error):
    return "<h1>500 - Internal Server Error</h1><p>Something went wrong on our end.</p>", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)