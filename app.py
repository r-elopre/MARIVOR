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
    cart = session.get('cart', {})
    cart_count = cart.get('total_items', 0) if isinstance(cart, dict) else 0
    
    return {
        'is_logged_in': is_logged_in(),
        'user_phone': session.get('phone_number'),
        'user_type': session.get('user_type', 'customer'),
        'store_name': session.get('store_name'),
        'is_seller': session.get('user_type') == 'seller',
        'is_admin': session.get('is_admin', False),
        'cart_count': cart_count
    }

# Routes

# Authentication Routes
@app.route('/')
def home():
    """Home page with all products and filtering/sorting"""
    # Get query parameters
    category = request.args.get('category', 'all')  # all, Fish, Vegetables
    sort_by = request.args.get('sort', 'newest')     # newest, price_low, price_high
    search_query = request.args.get('search', '').strip()  # search by product name
    
    try:
        supabase_client = get_supabase_client()
        
        # Get products based on search or category
        if search_query:
            products = supabase_client.search_products(search_query)
            # If searching, ignore category filter (show all matching results)
            current_category = 'all'
        elif category == 'all':
            products = supabase_client.get_all_products()
            current_category = category
        else:
            products = supabase_client.get_products_by_category(category)
            current_category = category
        
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
                             current_category=current_category,
                             current_sort=sort_by,
                             current_search=search_query,
                             page_title="Fresh Fish & Vegetables - Marivor")
    
    except Exception as e:
        print(f"Error loading products: {e}")
        return render_template('home.html', 
                             products=[],
                             current_category='all',
                             current_sort='newest',
                             page_title="Fresh Fish & Vegetables - Marivor")

@app.route('/api/store/<int:seller_id>')
def get_store_api(seller_id):
    """API endpoint to get store details for modal"""
    try:
        supabase_client = get_supabase_client()
        store_details = supabase_client.get_store_details(seller_id=seller_id)
        return jsonify(store_details)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/store/official')
def get_official_store_api():
    """API endpoint to get Marivor Official store details"""
    try:
        supabase_client = get_supabase_client()
        store_details = supabase_client.get_store_details(store_name="Marivor Official")
        return jsonify(store_details)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/store/<int:seller_id>/products')
def get_store_products_api(seller_id):
    """API endpoint to get all products from a specific store"""
    try:
        supabase_client = get_supabase_client()
        products = supabase_client.get_products_by_seller(seller_id)
        return jsonify({'products': products})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/store/official/products')
def get_official_store_products_api():
    """API endpoint to get all Marivor Official products"""
    try:
        supabase_client = get_supabase_client()
        products = supabase_client.get_products_by_seller(None)  # None for Marivor Official
        return jsonify({'products': products})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cart')
def cart():
    """Shopping cart page"""
    if not is_logged_in():
        session['next_page'] = url_for('cart')
        flash('Please log in to view your cart.', 'warning')
        return redirect(url_for('login'))
    
    # Get cart from session
    cart_data = session.get('cart', {'items': [], 'total_items': 0, 'total_price': 0.0})
    
    # Make sure cart_data has all required fields
    if 'items' not in cart_data:
        cart_data['items'] = []
    if 'total_items' not in cart_data:
        cart_data['total_items'] = 0
    if 'total_price' not in cart_data:
        cart_data['total_price'] = 0.0
    
    return render_template('cart.html', 
                         cart_items=cart_data.get('items', []),
                         cart_total_items=cart_data.get('total_items', 0),
                         cart_total_price=cart_data.get('total_price', 0.0),
                         cart_data=cart_data,
                         page_title="Shopping Cart - Marivor")

# Cart API Routes
@app.route('/api/cart/add', methods=['POST'])
def api_cart_add():
    """Add item to cart"""
    try:
        if not is_logged_in():
            return jsonify({'success': False, 'error': 'Please log in to add items to cart'})
        
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        
        if not product_id:
            return jsonify({'success': False, 'error': 'Product ID is required'})
        
        # Validate product and quantity
        supabase_client = get_supabase_client()
        validation = supabase_client.validate_cart_item(product_id, quantity)
        
        if not validation['valid']:
            return jsonify({'success': False, 'error': validation['error']})
        
        product = validation['product']
        
        # Initialize cart if it doesn't exist
        if 'cart' not in session:
            session['cart'] = {'items': [], 'total_items': 0, 'total_price': 0.0}
        
        cart = session['cart']
        
        # Check if product already exists in cart
        existing_item = None
        for item in cart['items']:
            if item['product_id'] == product_id:
                existing_item = item
                break
        
        if existing_item:
            # Update quantity of existing item
            new_quantity = existing_item['quantity'] + quantity
            
            # Re-validate with new quantity
            validation = supabase_client.validate_cart_item(product_id, new_quantity)
            if not validation['valid']:
                return jsonify({'success': False, 'error': validation['error']})
            
            existing_item['quantity'] = new_quantity
        else:
            # Add new item to cart
            cart_item = {
                'product_id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'quantity': quantity,
                'image_url': product.get('image_url', ''),
                'category': product.get('category', ''),
                'seller_name': product.get('seller_store_name', 'Unknown'),
                'unit': product.get('unit', True),
                'stock': product.get('stock', 0)
            }
            cart['items'].append(cart_item)
        
        # Recalculate totals
        cart['total_items'] = sum(item['quantity'] for item in cart['items'])
        cart['total_price'] = sum(item['price'] * item['quantity'] for item in cart['items'])
        
        # Save to session
        session['cart'] = cart
        
        return jsonify({
            'success': True, 
            'message': f'"{product["name"]}" added to cart!',
            'cart_count': cart['total_items'],
            'cart_total': cart['total_price']
        })
        
    except Exception as e:
        print(f"Cart add error: {e}")
        return jsonify({'success': False, 'error': 'Failed to add item to cart'})

@app.route('/api/cart/update', methods=['POST'])
def api_cart_update():
    """Update cart item quantity"""
    try:
        if not is_logged_in():
            return jsonify({'success': False, 'error': 'Please log in to update cart'})
        
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity')
        
        if not product_id or quantity is None:
            return jsonify({'success': False, 'error': 'Product ID and quantity are required'})
        
        if 'cart' not in session:
            return jsonify({'success': False, 'error': 'Cart is empty'})
        
        cart = session['cart']
        
        # Find item in cart
        item_found = False
        for item in cart['items']:
            if item['product_id'] == product_id:
                if quantity <= 0:
                    # Remove item if quantity is 0 or less
                    cart['items'].remove(item)
                else:
                    # Validate new quantity
                    supabase_client = get_supabase_client()
                    validation = supabase_client.validate_cart_item(product_id, quantity)
                    
                    if not validation['valid']:
                        return jsonify({'success': False, 'error': validation['error']})
                    
                    item['quantity'] = quantity
                
                item_found = True
                break
        
        if not item_found:
            return jsonify({'success': False, 'error': 'Item not found in cart'})
        
        # Recalculate totals
        cart['total_items'] = sum(item['quantity'] for item in cart['items'])
        cart['total_price'] = sum(item['price'] * item['quantity'] for item in cart['items'])
        
        # Save to session
        session['cart'] = cart
        
        return jsonify({
            'success': True,
            'message': 'Cart updated successfully!',
            'cart_count': cart['total_items'],
            'cart_total': cart['total_price']
        })
        
    except Exception as e:
        print(f"Cart update error: {e}")
        return jsonify({'success': False, 'error': 'Failed to update cart'})

@app.route('/api/cart/remove', methods=['POST'])
def api_cart_remove():
    """Remove item from cart"""
    try:
        if not is_logged_in():
            return jsonify({'success': False, 'error': 'Please log in to modify cart'})
        
        data = request.get_json()
        product_id = data.get('product_id')
        
        if not product_id:
            return jsonify({'success': False, 'error': 'Product ID is required'})
        
        if 'cart' not in session:
            return jsonify({'success': False, 'error': 'Cart is empty'})
        
        cart = session['cart']
        
        # Find and remove item
        item_removed = False
        for item in cart['items']:
            if item['product_id'] == product_id:
                cart['items'].remove(item)
                item_removed = True
                break
        
        if not item_removed:
            return jsonify({'success': False, 'error': 'Item not found in cart'})
        
        # Recalculate totals
        cart['total_items'] = sum(item['quantity'] for item in cart['items'])
        cart['total_price'] = sum(item['price'] * item['quantity'] for item in cart['items'])
        
        # Save to session
        session['cart'] = cart
        
        return jsonify({
            'success': True,
            'message': 'Item removed from cart!',
            'cart_count': cart['total_items'],
            'cart_total': cart['total_price']
        })
        
    except Exception as e:
        print(f"Cart remove error: {e}")
        return jsonify({'success': False, 'error': 'Failed to remove item'})

@app.route('/api/cart/clear', methods=['POST'])
def api_cart_clear():
    """Clear entire cart"""
    try:
        if not is_logged_in():
            return jsonify({'success': False, 'error': 'Please log in to clear cart'})
        
        # Clear cart
        session['cart'] = {'items': [], 'total_items': 0, 'total_price': 0.0}
        
        return jsonify({
            'success': True,
            'message': 'Cart cleared successfully!',
            'cart_count': 0,
            'cart_total': 0.0
        })
        
    except Exception as e:
        print(f"Cart clear error: {e}")
        return jsonify({'success': False, 'error': 'Failed to clear cart'})

@app.route('/api/cart/get', methods=['GET'])
def api_cart_get():
    """Get current cart data"""
    try:
        if not is_logged_in():
            return jsonify({'success': False, 'error': 'Please log in to view cart'})
        
        cart_data = session.get('cart', {'items': [], 'total_items': 0, 'total_price': 0.0})
        
        return jsonify({
            'success': True,
            'cart': cart_data
        })
        
    except Exception as e:
        print(f"Cart get error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get cart data'})

# User API Routes
@app.route('/api/user/details', methods=['GET'])
def api_user_details():
    """Get current user details for checkout"""
    try:
        if not is_logged_in():
            return jsonify({'success': False, 'error': 'Please log in first'})
        
        phone_number = session.get('phone_number')
        if not phone_number:
            return jsonify({'success': False, 'error': 'User session invalid'})
        
        supabase_client = get_supabase_client()
        user_info = supabase_client.get_user_by_phone(phone_number)
        
        if not user_info:
            return jsonify({'success': False, 'error': 'User not found'})
        
        return jsonify({
            'success': True,
            'user': {
                'phone': user_info.get('phone'),
                'full_name': user_info.get('full_name'),
                'first_name': user_info.get('first_name'),
                'last_name': user_info.get('last_name'),
                'email': user_info.get('email'),
                'face_photo_front': user_info.get('face_photo_front')
            }
        })
        
    except Exception as e:
        print(f"User details error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get user details'})

# Order API Routes
@app.route('/api/order/create', methods=['POST'])
def api_order_create():
    """Create a new order"""
    try:
        if not is_logged_in():
            return jsonify({'success': False, 'error': 'Please log in first'})
        
        phone_number = session.get('phone_number')
        if not phone_number:
            return jsonify({'success': False, 'error': 'User session invalid'})
        
        # Get request data
        data = request.get_json()
        shipping_address = data.get('shipping_address', '').strip()
        order_notes = data.get('order_notes', '').strip()
        
        if not shipping_address:
            return jsonify({'success': False, 'error': 'Shipping address is required'})
        
        # Get cart data
        cart_data = session.get('cart', {'items': [], 'total_items': 0, 'total_price': 0.0})
        
        if not cart_data.get('items') or cart_data.get('total_items', 0) == 0:
            return jsonify({'success': False, 'error': 'Cart is empty'})
        
        # Get user info
        supabase_client = get_supabase_client()
        user_info = supabase_client.get_user_by_phone(phone_number)
        
        if not user_info:
            return jsonify({'success': False, 'error': 'User not found'})
        
        # Generate base order number for grouping
        import time
        import random
        base_timestamp = int(time.time())
        base_random = random.randint(100, 999)
        
        # Create separate order for each product
        created_orders = []
        
        for index, item in enumerate(cart_data.get('items', [])):
            # Generate unique order number for each product
            order_number = f"ORD-{base_timestamp}-{base_random}-{index + 1}"
            
            # Calculate item total (price * quantity)
            item_quantity = item.get('quantity', 1)
            item_price = item.get('price', 0.0)
            item_total = item_quantity * item_price
            
            # Prepare order data for this single product
            order_data = {
                'user_id': user_info.get('id'),  # Use user ID from database
                'order_number': order_number,
                'status': 'pending',
                'total_amount': item_total,  # Only this item's total
                'currency': 'PHP',
                'customer_name': user_info.get('full_name') or f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip(),
                'customer_phone': user_info.get('phone'),
                'shipping_address': shipping_address,
                'items': [item],  # Only this single item
                'face_photo_front': user_info.get('face_photo_front')
                # Removed seller_id - all seller info is in items JSONB
            }
            
            # Create order in database for this product
            created_order = supabase_client.create_order(order_data)
            
            if not created_order:
                return jsonify({'success': False, 'error': f'Failed to create order for {item.get("name", "product")}'})
            
            created_orders.append({
                'order_id': created_order.get('id'),
                'order_number': order_number,
                'product_name': item.get('name'),
                'total': item_total
            })
        
        # Clear cart after successful order creation
        session['cart'] = {'items': [], 'total_items': 0, 'total_price': 0.0}
        
        # Prepare response with all created orders
        total_orders = len(created_orders)
        order_numbers = [order['order_number'] for order in created_orders]
        
        return jsonify({
            'success': True,
            'message': f'{total_orders} orders created successfully!',
            'orders': created_orders,
            'order_numbers': order_numbers,
            'total_orders': total_orders
        })
        
    except Exception as e:
        print(f"Order creation error: {e}")
        return jsonify({'success': False, 'error': 'Failed to create order'})

@app.route('/api/order/create-by-seller', methods=['POST'])
def api_order_create_by_seller():
    """Create a new order for a specific seller"""
    try:
        if not is_logged_in():
            return jsonify({'success': False, 'error': 'Please log in first'})
        
        phone_number = session.get('phone_number')
        if not phone_number:
            return jsonify({'success': False, 'error': 'User session invalid'})
        
        # Get request data
        data = request.get_json()
        shipping_address = data.get('shipping_address', '').strip()
        seller_items = data.get('seller_items', [])
        seller_name = data.get('seller_name', '')
        total_amount = data.get('total_amount', 0.0)
        
        if not shipping_address:
            return jsonify({'success': False, 'error': 'Shipping address is required'})
        
        if not seller_items:
            return jsonify({'success': False, 'error': 'No items for this seller'})
        
        # Get user info
        supabase_client = get_supabase_client()
        user_info = supabase_client.get_user_by_phone(phone_number)
        
        if not user_info:
            return jsonify({'success': False, 'error': 'User not found'})
        
        # Generate base order number for grouping
        import time
        import random
        base_timestamp = int(time.time())
        base_random = random.randint(100, 999)
        
        # Create separate order for each product in seller_items
        created_orders = []
        
        for index, item in enumerate(seller_items):
            # Generate unique order number for each product
            order_number = f"ORD-{base_timestamp}-{base_random}-{index + 1}"
            
            # Calculate item total (price * quantity)
            item_quantity = item.get('quantity', 1)
            item_price = item.get('price', 0.0)
            item_total = item_quantity * item_price
            
            # Get seller_id for this specific product (only for items enhancement)
            product_seller_id = None
            product_id = item.get('product_id')
            if product_id:
                product = supabase_client.get_product_by_id(product_id)
                if product:
                    product_seller_id = product.get('seller_id')
                    # Ensure item has seller info for JSONB storage
                    if 'seller_id' not in item:
                        item['seller_id'] = product_seller_id
                    if 'seller_name' not in item:
                        item['seller_name'] = product.get('seller_name', 'Unknown Seller')
            
            # Prepare order data for this single product
            order_data = {
                'user_id': user_info.get('id'),
                'order_number': order_number,
                'status': 'pending',
                'total_amount': item_total,  # Only this item's total
                'currency': 'PHP',
                'customer_name': user_info.get('full_name') or f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip(),
                'customer_phone': user_info.get('phone'),
                'shipping_address': shipping_address,
                'items': [item],  # Only this single item with seller info
                'face_photo_front': user_info.get('face_photo_front')
                # Removed seller_id from order level - all seller info is in items JSONB
            }
            
            # Create order in database for this product
            created_order = supabase_client.create_order(order_data)
            
            if not created_order:
                return jsonify({'success': False, 'error': f'Failed to create order for {item.get("name", "product")}'})
            
            created_orders.append({
                'order_id': created_order.get('id'),
                'order_number': order_number,
                'product_name': item.get('name'),
                'total': item_total
            })
        
        # Prepare response with all created orders for this seller
        total_orders = len(created_orders)
        order_numbers = [order['order_number'] for order in created_orders]
        
        return jsonify({
            'success': True,
            'message': f'{total_orders} orders created successfully for {seller_name}!',
            'orders': created_orders,
            'order_numbers': order_numbers,
            'total_orders': total_orders,
            'seller_name': seller_name
        })
        
    except Exception as e:
        print(f"Seller order creation error: {e}")
        return jsonify({'success': False, 'error': f'Failed to create order: {str(e)}'})

@app.route('/orders')
def orders():
    """User orders page"""
    if not is_logged_in():
        flash('Please log in to view your orders.', 'error')
        return redirect(url_for('login'))
    
    try:
        phone_number = session.get('phone_number')
        supabase_client = get_supabase_client()
        
        # Get user info first
        user_info = supabase_client.get_user_by_phone(phone_number)
        if not user_info:
            flash('User not found. Please log in again.', 'error')
            return redirect(url_for('logout'))
        
        # Get user orders
        user_orders = supabase_client.get_user_orders(user_info.get('id'))
        
        return render_template('orders.html', 
                             orders=user_orders,
                             page_title="My Orders - Marivor")
    
    except Exception as e:
        print(f"Orders page error: {e}")
        flash('Error loading orders. Please try again.', 'error')
        return redirect(url_for('home'))

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
        
        # Fetch user orders
        user_orders = supabase_client.get_user_orders(session['user_id'])
        
        # Process order dates for template compatibility and add seller store names
        from datetime import datetime
        import pytz
        
        # Define Manila timezone
        manila_tz = pytz.timezone('Asia/Manila')
        utc_tz = pytz.UTC
        
        for order in user_orders:
            # Convert UTC timestamp to Manila timezone
            if order.get('created_at') and isinstance(order['created_at'], str):
                try:
                    # Parse UTC timestamp
                    utc_time = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
                    # Convert to Manila timezone
                    manila_time = utc_time.replace(tzinfo=utc_tz).astimezone(manila_tz)
                    order['created_at'] = manila_time
                except (ValueError, TypeError):
                    pass
            
            # Fetch seller store names based on parsed seller IDs from items
            seller_store_names = []
            if order.get('parsed_items') and order['parsed_items'].get('seller_ids'):
                for seller_id in order['parsed_items']['seller_ids']:
                    try:
                        seller_info = supabase_client.get_seller_by_id(int(seller_id))
                        store_name = seller_info.get('store_name', f'Store #{seller_id}') if seller_info else f'Unknown Store #{seller_id}'
                        seller_store_names.append(store_name)
                    except (ValueError, TypeError):
                        seller_store_names.append(f'Store #{seller_id}')
                
                # Add formatted seller names to order
                order['seller_store_names'] = seller_store_names
                order['formatted_sellers'] = ', '.join(seller_store_names) if seller_store_names else 'Marivor Official'
            else:
                # Fallback to original seller_id if no parsed data
                if order.get('seller_id'):
                    seller_info = supabase_client.get_seller_by_id(order['seller_id'])
                    order['formatted_sellers'] = seller_info.get('store_name', 'Unknown Store') if seller_info else 'Unknown Store'
                else:
                    order['formatted_sellers'] = 'Marivor Official'
        
        return render_template('profile.html', 
                             user_info=user_info,
                             user_orders=user_orders,
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
                return redirect(url_for('seller_products'))
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
            return redirect(url_for('seller_products'))
        
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
        pending_orders = supabase_client.get_orders_by_status('pending')
        processing_orders = supabase_client.get_orders_by_status('processing')
        delivery_orders = supabase_client.get_orders_by_status('on_delivery')
        completed_orders = supabase_client.get_orders_by_status('completed')
        
        stats = {
            'total_products': len(all_products),
            'fish_products': len([p for p in all_products if p['category'] == 'Fish']),
            'vegetable_products': len([p for p in all_products if p['category'] == 'Vegetables']),
            'pending_orders': len(pending_orders),
            'processing_orders': len(processing_orders),
            'delivery_orders': len(delivery_orders),
            'completed_orders': len(completed_orders)
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
        
        # Get orders based on filter
        if status_filter == 'all':
            # For "All Orders", exclude completed orders (only show active orders)
            orders = supabase_client.get_active_orders()
        else:
            orders = supabase_client.get_orders_by_status(status_filter)
        
        print(f"DEBUG: Got {len(orders) if orders else 0} orders")
        
        # Process orders to parse JSON items and add user info
        processed_orders = []
        if orders:
            for order in orders:
                if isinstance(order, dict):
                    processed_order = dict(order)  # Create a copy
                    
                    # Parse items JSONB if it exists
                    if order.get('items'):
                        try:
                            import json
                            if isinstance(order['items'], str):
                                processed_order['items'] = json.loads(order['items'])
                            else:
                                processed_order['items'] = order['items']
                        except (json.JSONDecodeError, TypeError) as e:
                            print(f"Error parsing items for order {order.get('id')}: {e}")
                            processed_order['items'] = []
                    else:
                        processed_order['items'] = []
                    
                    # Format currency
                    if order.get('total_amount'):
                        processed_order['total_formatted'] = f"₱{float(order['total_amount']):.2f}"
                    
                    # Get user info if customer_name is empty
                    if not order.get('customer_name') or order.get('customer_name').strip() == '':
                        try:
                            user_response = supabase_client.client.table('users').select('username, phone_number').eq('id', order.get('user_id')).execute()
                            if user_response.data and len(user_response.data) > 0:
                                user_info = user_response.data[0]
                                processed_order['customer_name'] = user_info.get('username', f'User #{order.get("user_id")}')
                                if not processed_order.get('customer_phone') or processed_order.get('customer_phone') == 'None':
                                    processed_order['customer_phone'] = user_info.get('phone_number')
                        except Exception as e:
                            print(f"Error fetching user info for order {order.get('id')}: {e}")
                            processed_order['customer_name'] = f'User #{order.get("user_id")}'
                    
                    processed_orders.append(processed_order)
        
        print(f"DEBUG: Processed {len(processed_orders)} orders")
        return render_template('admin/orders.html', orders=processed_orders, current_filter=status_filter)
        
    except Exception as e:
        print(f"ERROR in admin_orders: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error loading orders: {str(e)}', 'error')
        return render_template('admin/orders.html', orders=[], current_filter='all')

@app.route('/admin/orders/update_status/<int:order_id>', methods=['POST'])
def admin_update_order_status(order_id):
    """Update order status with validation and progression logic"""
    if not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Admin access required'})
    
    try:
        # Get the new status from the request
        if request.content_type == 'application/json':
            data = request.get_json()
            new_status = data.get('status')
        else:
            new_status = request.form.get('status')
        
        if not new_status:
            return jsonify({'success': False, 'error': 'Status is required'})
        
        # Validate status values
        valid_statuses = ['pending', 'processing', 'on_delivery', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            return jsonify({'success': False, 'error': 'Invalid status'})
        
        supabase_client = get_supabase_client()
        
        # Get current order to validate progression
        current_order = supabase_client.get_order_by_id(order_id)
        if not current_order:
            return jsonify({'success': False, 'error': 'Order not found'})
        
        current_status = current_order.get('status', 'pending')
        
        # Define valid status progressions
        status_progressions = {
            'pending': ['processing', 'cancelled'],
            'processing': ['on_delivery', 'cancelled'],
            'on_delivery': ['completed', 'cancelled'],
            'completed': [],  # Final state
            'cancelled': []   # Final state
        }
        
        # Check if the status transition is valid
        if current_status == new_status:
            return jsonify({'success': False, 'error': f'Order is already {new_status}'})
        
        if new_status not in status_progressions.get(current_status, []):
            return jsonify({'success': False, 'error': f'Cannot change status from {current_status} to {new_status}'})
        
        # Update the order status
        success = supabase_client.update_order_status(order_id, new_status)
        
        if success:
            # Create user-friendly status messages
            status_messages = {
                'processing': 'Order is now being processed',
                'on_delivery': 'Order is out for delivery',
                'completed': 'Order has been completed successfully',
                'cancelled': 'Order has been cancelled'
            }
            
            message = status_messages.get(new_status, f'Order status updated to {new_status}')
            
            flash(f'Order #{order_id} - {message}!', 'success')
            return jsonify({
                'success': True, 
                'message': message,
                'new_status': new_status,
                'order_id': order_id
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update order status in database'})
            
    except Exception as e:
        print(f"Error updating order status: {e}")
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'})

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
def seller_redirect():
    """Redirect /seller to /seller/products for simplicity"""
    return redirect(url_for('seller_products'))

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
        return redirect(url_for('seller_products'))

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
    """Seller orders page - Fixed template syntax error"""
    if session.get('user_type') != 'seller':
        flash('Seller access required!', 'error')
        return redirect(url_for('login'))
    
    try:
        supabase_client = get_supabase_client()
        seller_id = session.get('seller_id')
        
        if not seller_id:
            flash('Seller ID not found in session!', 'error')
            return render_template('seller/orders.html', orders=[])
        
        # Get orders for this seller
        orders = supabase_client.get_seller_orders(seller_id)
        
        # Process orders to add formatted data for display
        processed_orders = []
        for order in orders:
            processed_order = order.copy()
            
            # Convert created_at to Manila timezone if it exists
            if order.get('created_at'):
                try:
                    import pytz
                    from datetime import datetime
                    
                    # Parse UTC datetime
                    utc_dt = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
                    utc_dt = utc_dt.replace(tzinfo=pytz.UTC)
                    
                    # Convert to Manila timezone
                    manila_tz = pytz.timezone('Asia/Manila')
                    manila_dt = utc_dt.astimezone(manila_tz)
                    
                    processed_order['created_at_manila'] = manila_dt.strftime('%B %d, %Y at %I:%M %p')
                    processed_order['created_at_date'] = manila_dt.strftime('%Y-%m-%d')
                except Exception as e:
                    print(f"Error converting timezone: {e}")
                    processed_order['created_at_manila'] = order['created_at']
                    processed_order['created_at_date'] = order['created_at']
            
            # Format currency as PHP
            if order.get('total_amount'):
                processed_order['total_amount_formatted'] = f"₱{order['total_amount']:.2f}"
            else:
                processed_order['total_amount_formatted'] = "₱0.00"
            
            # Parse items JSON if it exists
            if order.get('items'):
                if isinstance(order['items'], str):
                    try:
                        import json
                        processed_order['items_list'] = json.loads(order['items'])
                    except:
                        processed_order['items_list'] = []
                else:
                    processed_order['items_list'] = order['items']
            else:
                processed_order['items_list'] = []
            
            # Calculate item count
            processed_order['item_count'] = len(processed_order['items_list'])
            
            # Get product information from items JSON
            if processed_order['items_list']:
                first_item = processed_order['items_list'][0]
                
                # Try to get product image using product_id from the items JSON
                product_id = first_item.get('product_id')
                if product_id:
                    try:
                        product_details = supabase_client.get_product_by_id(product_id)
                        if product_details and product_details.get('image_url'):
                            processed_order['first_product_image'] = product_details['image_url']
                        else:
                            # Fallback to image_url from items JSON if exists
                            processed_order['first_product_image'] = first_item.get('image_url', '')
                    except Exception as e:
                        print(f"Error fetching product image for product_id {product_id}: {e}")
                        processed_order['first_product_image'] = first_item.get('image_url', '')
                else:
                    # Fallback to image_url from items JSON if no product_id
                    processed_order['first_product_image'] = first_item.get('image_url', '')
                
                processed_order['first_product_name'] = first_item.get('name', 'Unknown Product')
                processed_order['first_product_price'] = first_item.get('price', 0)
                processed_order['first_product_quantity'] = first_item.get('quantity', 1)
                
                # Calculate total for all items
                total_items = 0
                total_value = 0
                for item in processed_order['items_list']:
                    quantity = item.get('quantity', 1)
                    price = item.get('price', 0)
                    total_items += quantity
                    total_value += quantity * price
                
                processed_order['total_items_count'] = total_items
                processed_order['calculated_total'] = total_value
                processed_order['calculated_total_formatted'] = f"₱{total_value:.2f}"
            else:
                processed_order['first_product_image'] = ''
                processed_order['first_product_name'] = 'No Products'
                processed_order['first_product_price'] = 0
                processed_order['first_product_quantity'] = 0
                processed_order['total_items_count'] = 0
                processed_order['calculated_total'] = 0
                processed_order['calculated_total_formatted'] = "₱0.00"
            
            processed_orders.append(processed_order)
        
        return render_template('seller/orders.html', orders=processed_orders)
        
    except Exception as e:
        print(f"Error loading seller orders: {e}")
        flash(f'Error loading orders: {str(e)}', 'error')
        return render_template('seller/orders.html', orders=[])

@app.route('/seller/orders/update_status/<int:order_id>', methods=['POST'])
def seller_update_order_status(order_id):
    """Update order status from seller panel"""
    if session.get('user_type') != 'seller':
        flash('Seller access required!', 'error')
        return redirect(url_for('login'))
    
    try:
        new_status = request.form.get('status')
        if not new_status:
            flash('Status is required!', 'error')
            return redirect(url_for('seller_orders'))
        
        # Valid status values
        valid_statuses = ['pending', 'processing', 'shipped', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            flash('Invalid status!', 'error')
            return redirect(url_for('seller_orders'))
        
        supabase_client = get_supabase_client()
        seller_id = session.get('seller_id')
        
        # First verify that this order belongs to this seller
        order = supabase_client.get_order_by_id(order_id)
        if not order:
            flash('Order not found!', 'error')
            return redirect(url_for('seller_orders'))
        
        if order.get('seller_id') != seller_id:
            flash('You can only update orders from your store!', 'error')
            return redirect(url_for('seller_orders'))
        
        # Update the order status
        success = supabase_client.update_order_status(order_id, new_status)
        
        if success:
            flash(f'Order status updated to {new_status}!', 'success')
        else:
            flash('Failed to update order status!', 'error')
            
    except Exception as e:
        print(f"Error updating order status: {e}")
        flash(f'Error updating order status: {str(e)}', 'error')
    
    return redirect(url_for('seller_orders'))

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