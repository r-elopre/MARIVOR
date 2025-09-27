"""
Supabase database utilities for Marivor
Handles database operations and file storage with Supabase
"""

import os
from typing import Optional, Dict, List, Any
from supabase import create_client, Client
from dotenv import load_dotenv
import base64
import uuid
from datetime import datetime

# Load environment variables
load_dotenv()

class SupabaseClient:
    """Wrapper class for Supabase operations"""
    
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')
        self.service_key = os.getenv('SUPABASE_SERVICE_KEY')  # Service role key for storage
        self.bucket_name = os.getenv('SUPABASE_STORAGE_BUCKET', 'faces')
        
        if not self.url or not self.key:
            raise ValueError("Supabase URL and Key must be set in environment variables")
        
        # Use service key for storage operations if available, otherwise use anon key
        storage_key = self.service_key if self.service_key else self.key
        self.client: Client = create_client(self.url, self.key)
        self.storage_client: Client = create_client(self.url, storage_key)  # Separate client for storage
    
    # User Management Methods
    def create_user(self, username: str, phone_number: str, face_login_code: str, 
                   auth_type: str = 'face', user_type: str = 'customer', seller_id: int = None) -> Dict[str, Any]:
        """Create a new user in the database"""
        try:
            user_data = {
                'username': username,
                'phone_number': phone_number,
                'face_login_code': face_login_code,
                'auth_type': auth_type,
                'user_type': user_type,
                'seller_id': seller_id,
                'is_verified': True,
                'created_at': datetime.utcnow().isoformat()
            }
            
            response = self.client.table('users').insert(user_data).execute()
            return {'success': True, 'data': response.data[0] if response.data else None}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            response = self.client.table('users').select('*').eq('id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    def get_user_by_face_code(self, face_code: str) -> Optional[Dict[str, Any]]:
        """Get user by face login code"""
        try:
            response = self.client.table('users').select('*').eq('face_login_code', face_code).eq('is_verified', True).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting user by face code: {e}")
            return None
    
    def get_user_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get user by phone number"""
        try:
            response = self.client.table('users').select('*').eq('phone_number', phone_number).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting user by phone: {e}")
            return None
    
    def update_user_photos(self, user_id: int, front_url: str, left_url: str, right_url: str) -> bool:
        """Update user's face photo URLs"""
        try:
            update_data = {
                'face_photo_front': front_url,
                'face_photo_left': left_url,
                'face_photo_right': right_url
            }
            
            response = self.client.table('users').update(update_data).eq('id', user_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error updating user photos: {e}")
            return False
    
    def set_admin_status(self, user_id: int, is_admin: bool = True) -> bool:
        """Set admin status for a user"""
        try:
            response = self.client.table('users').update({'is_admin': is_admin}).eq('id', user_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error setting admin status: {e}")
            return False
    
    def is_user_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        try:
            response = self.client.table('users').select('is_admin').eq('id', user_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0].get('is_admin', False)
            return False
        except Exception as e:
            print(f"Error checking admin status: {e}")
            return False
    
    # Product Management Methods
    def get_all_products(self) -> List[Dict[str, Any]]:
        """Get all products with seller information"""
        try:
            # First get all products
            products_response = self.client.table('products').select('*').execute()
            products = products_response.data if products_response.data else []
            
            # Get all sellers info at once for efficiency
            sellers_response = self.client.table('sellers').select('id, store_name').execute()
            sellers_dict = {seller['id']: seller['store_name'] for seller in (sellers_response.data or [])}
            
            # Add seller info to each product
            for product in products:
                if product.get('seller_id') and product['seller_id'] is not None:
                    # Seller-created product - lookup store name
                    product['seller_store_name'] = sellers_dict.get(product['seller_id'], 'Unknown Seller')
                else:
                    # Admin-created product (seller_id is NULL)
                    product['seller_store_name'] = 'Marivor Official'
                    
            return products
        except Exception as e:
            print(f"Error getting products: {e}")
            return []
    
    def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get products by category with seller information"""
        try:
            # First get products by category
            products_response = self.client.table('products').select('*').eq('category', category).execute()
            products = products_response.data if products_response.data else []
            
            # Get all sellers info at once for efficiency
            sellers_response = self.client.table('sellers').select('id, store_name').execute()
            sellers_dict = {seller['id']: seller['store_name'] for seller in (sellers_response.data or [])}
            
            # Add seller info to each product
            for product in products:
                if product.get('seller_id') and product['seller_id'] is not None:
                    # Seller-created product - lookup store name
                    product['seller_store_name'] = sellers_dict.get(product['seller_id'], 'Unknown Seller')
                else:
                    # Admin-created product (seller_id is NULL)
                    product['seller_store_name'] = 'Marivor Official'
                    
            return products
        except Exception as e:
            print(f"Error getting products by category: {e}")
            return []
    
    def search_products(self, search_query: str) -> List[Dict[str, Any]]:
        """Search products by name OR seller store name with seller information"""
        try:
            if not search_query or search_query.strip() == '':
                return []
                
            # Get all sellers first to create mapping
            sellers_response = self.client.table('sellers').select('id, store_name').execute()
            sellers_dict = {seller['id']: seller['store_name'] for seller in (sellers_response.data or [])}
            
            # Search products by name (case-insensitive)
            products_by_name = self.client.table('products').select('*').ilike('name', f'%{search_query}%').execute()
            products_by_name = products_by_name.data if products_by_name.data else []
            
            # Search sellers by store name and get their products
            sellers_matching = self.client.table('sellers').select('id, store_name').ilike('store_name', f'%{search_query}%').execute()
            sellers_matching = sellers_matching.data if sellers_matching.data else []
            
            products_by_seller = []
            for seller in sellers_matching:
                seller_products = self.client.table('products').select('*').eq('seller_id', seller['id']).execute()
                if seller_products.data:
                    products_by_seller.extend(seller_products.data)
            
            # Check if "admin" or "marivor" is in search query for admin products
            admin_keywords = ['admin', 'marivor', 'official']
            products_by_admin = []
            if any(keyword in search_query.lower() for keyword in admin_keywords):
                admin_products = self.client.table('products').select('*').is_('seller_id', 'null').execute()
                if admin_products.data:
                    products_by_admin = admin_products.data
            
            # Combine all results and remove duplicates
            all_products = products_by_name + products_by_seller + products_by_admin
            unique_products = []
            seen_ids = set()
            
            for product in all_products:
                if product['id'] not in seen_ids:
                    unique_products.append(product)
                    seen_ids.add(product['id'])
            
            # Add seller info to each product
            for product in unique_products:
                if product.get('seller_id') and product['seller_id'] is not None:
                    # Seller-created product - lookup store name
                    product['seller_store_name'] = sellers_dict.get(product['seller_id'], 'Unknown Seller')
                else:
                    # Admin-created product (seller_id is NULL)
                    product['seller_store_name'] = 'Marivor Official'
                    
            return unique_products
        except Exception as e:
            print(f"Error searching products: {e}")
            return []
    
    def get_products_by_seller(self, seller_id: int = None) -> List[Dict[str, Any]]:
        """Get all products from a specific seller (None for Marivor Official)"""
        try:
            if seller_id is None:
                # Get admin products (seller_id is NULL)
                products_response = self.client.table('products').select('*').is_('seller_id', 'null').execute()
            else:
                # Get products from specific seller
                products_response = self.client.table('products').select('*').eq('seller_id', seller_id).execute()
            
            products = products_response.data if products_response.data else []
            
            # Add seller store name to each product
            for product in products:
                if seller_id is None:
                    product['seller_store_name'] = 'Marivor Official'
                else:
                    # Get seller store name
                    seller_response = self.client.table('sellers').select('store_name').eq('id', seller_id).execute()
                    if seller_response.data and len(seller_response.data) > 0:
                        product['seller_store_name'] = seller_response.data[0]['store_name']
                    else:
                        product['seller_store_name'] = 'Unknown Seller'
                        
            return products
        except Exception as e:
            print(f"Error getting products by seller: {e}")
            return []
    
    # Store Review and Rating Methods
    def get_store_details(self, seller_id: int = None, store_name: str = None) -> Dict[str, Any]:
        """Get comprehensive store details including ratings and reviews"""
        try:
            if seller_id:
                # Get store info by seller_id
                store_response = self.client.table('sellers').select('*').eq('id', seller_id).execute()
            elif store_name == "Marivor Official":
                # Handle admin store (no seller_id)
                return {
                    'store_info': {
                        'id': None,
                        'seller_id': None,
                        'store_name': 'Marivor Official',
                        'store_image_url': None,
                        'created_at': '2024-01-01',
                        'is_active': True
                    },
                    'ratings': {'average_rating': 4.9, 'total_reviews': 127},
                    'reviews': [
                        {'customer_name': 'Maria Santos', 'rating': 5, 'comment': 'Always fresh and high quality products!', 'created_at': '2024-12-20'},
                        {'customer_name': 'Juan Dela Cruz', 'rating': 5, 'comment': 'Fast delivery and excellent service.', 'created_at': '2024-12-19'},
                        {'customer_name': 'Anna Garcia', 'rating': 4, 'comment': 'Great selection of fresh fish and vegetables.', 'created_at': '2024-12-18'}
                    ],
                    'stats': {'total_products': 15, 'avg_delivery_time': '30 mins', 'satisfaction_rate': 98}
                }
            else:
                return {}
                
            if not store_response.data:
                return {}
                
            store_info = store_response.data[0]
            # Add seller_id to store_info for JavaScript access
            store_info['seller_id'] = seller_id
            
            # Get store reviews (mock data for now - you can create a reviews table later)
            reviews = [
                {'customer_name': 'Customer 1', 'rating': 5, 'comment': 'Great quality fish!', 'created_at': '2024-12-20'},
                {'customer_name': 'Customer 2', 'rating': 4, 'comment': 'Good service and fresh products.', 'created_at': '2024-12-19'},
                {'customer_name': 'Customer 3', 'rating': 5, 'comment': 'Always reliable, will buy again!', 'created_at': '2024-12-18'}
            ]
            
            # Calculate ratings
            total_reviews = len(reviews)
            average_rating = sum(review['rating'] for review in reviews) / total_reviews if total_reviews > 0 else 0
            
            # Get store stats
            products_count = self.client.table('products').select('id', count='exact').eq('seller_id', seller_id).execute()
            total_products = len(products_count.data) if products_count.data else 0
            
            return {
                'store_info': store_info,
                'ratings': {
                    'average_rating': round(average_rating, 1),
                    'total_reviews': total_reviews
                },
                'reviews': reviews,
                'stats': {
                    'total_products': total_products,
                    'avg_delivery_time': '45 mins',
                    'satisfaction_rate': 94
                }
            }
            
        except Exception as e:
            print(f"Error getting store details: {e}")
            return {}
    
    def add_product(self, name: str, category: str, price: float, stock: int, image_url: str = "", 
                   seller_id: int = None, created_by: str = "admin", description: str = "", unit: bool = True) -> Dict[str, Any]:
        """Add a new product"""
        try:
            product_data = {
                'name': name,
                'category': category,
                'description': description,
                'price': price,
                'stock': stock,
                'unit': unit,
                'image_url': image_url,
                'seller_id': seller_id,
                'created_by': created_by,
                'created_at': datetime.utcnow().isoformat()
            }
            
            response = self.client.table('products').insert(product_data).execute()
            return {'success': True, 'data': response.data[0] if response.data else None}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def update_product(self, product_id: int, **kwargs) -> bool:
        """Update product details"""
        try:
            response = self.client.table('products').update(kwargs).eq('id', product_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error updating product: {e}")
            return False
    
    def delete_product(self, product_id: int) -> bool:
        """Delete a product"""
        try:
            response = self.client.table('products').delete().eq('id', product_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error deleting product: {e}")
            return False
    
    # Image Storage Methods
    def upload_product_image(self, file_data: bytes, filename: str, content_type: str = 'image/jpeg') -> Dict[str, Any]:
        """Upload product image to Supabase storage"""
        try:
            # Generate unique filename
            file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
            unique_filename = f"products/{uuid.uuid4()}.{file_extension}"
            
            # Upload to Supabase storage
            response = self.storage_client.storage.from_('products').upload(
                unique_filename, 
                file_data,
                file_options={'content-type': content_type}
            )
            
            if response.status_code in [200, 201]:
                # Get public URL
                public_url = self.storage_client.storage.from_('products').get_public_url(unique_filename)
                return {
                    'success': True, 
                    'url': public_url,
                    'filename': unique_filename
                }
            else:
                return {'success': False, 'error': f'Upload failed with status {response.status_code}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_product_image(self, filename: str) -> bool:
        """Delete product image from Supabase storage"""
        try:
            response = self.storage_client.storage.from_('products').remove([filename])
            return response.status_code == 200
        except Exception as e:
            print(f"Error deleting image: {e}")
            return False
    
    def add_product_with_image(self, name: str, category: str, price: float, stock: int, unit: bool,
                              image_file_data: bytes = None, image_filename: str = None, 
                              image_url: str = "", seller_id: int = None, created_by: str = "admin") -> Dict[str, Any]:
        """Add a new product with optional image upload"""
        try:
            final_image_url = image_url
            uploaded_filename = None
            
            # If image file is provided, upload it
            if image_file_data and image_filename:
                # Determine content type from filename
                content_type = 'image/jpeg'
                if image_filename.lower().endswith('.png'):
                    content_type = 'image/png'
                elif image_filename.lower().endswith('.gif'):
                    content_type = 'image/gif'
                elif image_filename.lower().endswith('.webp'):
                    content_type = 'image/webp'
                
                upload_result = self.upload_product_image(image_file_data, image_filename, content_type)
                
                if upload_result['success']:
                    final_image_url = upload_result['url']
                    uploaded_filename = upload_result['filename']
                else:
                    return {'success': False, 'error': f"Image upload failed: {upload_result['error']}"}
            
            # Create product with image URL
            product_data = {
                'name': name,
                'category': category,
                'price': price,
                'stock': stock,
                'unit': unit,
                'image_url': final_image_url,
                'seller_id': seller_id,
                'created_by': created_by,
                'created_at': datetime.utcnow().isoformat()
            }
            
            response = self.client.table('products').insert(product_data).execute()
            
            if response.data:
                return {
                    'success': True, 
                    'data': response.data[0],
                    'uploaded_filename': uploaded_filename
                }
            else:
                # If product creation failed and we uploaded an image, clean it up
                if uploaded_filename:
                    self.delete_product_image(uploaded_filename)
                return {'success': False, 'error': 'Failed to create product'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def update_product_with_image(self, product_id: int, name: str = None, category: str = None, 
                                 price: float = None, stock: int = None, unit: bool = None,
                                 image_file_data: bytes = None, image_filename: str = None, 
                                 image_url: str = None) -> Dict[str, Any]:
        """Update a product with optional image upload"""
        try:
            update_data = {}
            uploaded_filename = None
            old_image_url = None
            
            # Get current product data to check for existing image
            current_product = self.get_product_by_id(product_id)
            if current_product:
                old_image_url = current_product.get('image_url', '')
            
            # Update basic fields
            if name is not None:
                update_data['name'] = name
            if category is not None:
                update_data['category'] = category
            if price is not None:
                update_data['price'] = price
            if stock is not None:
                update_data['stock'] = stock
            if unit is not None:
                update_data['unit'] = unit
            
            # Handle image update
            if image_file_data and image_filename:
                # Upload new image
                content_type = 'image/jpeg'
                if image_filename.lower().endswith('.png'):
                    content_type = 'image/png'
                elif image_filename.lower().endswith('.gif'):
                    content_type = 'image/gif'
                elif image_filename.lower().endswith('.webp'):
                    content_type = 'image/webp'
                
                upload_result = self.upload_product_image(image_file_data, image_filename, content_type)
                
                if upload_result['success']:
                    update_data['image_url'] = upload_result['url']
                    uploaded_filename = upload_result['filename']
                else:
                    return {'success': False, 'error': f"Image upload failed: {upload_result['error']}"}
            elif image_url is not None:
                # Update with new URL (empty string to clear)
                update_data['image_url'] = image_url
            
            # Update the product
            if update_data:
                response = self.client.table('products').update(update_data).eq('id', product_id).execute()
                
                if response.data:
                    # If we uploaded a new image and the update was successful,
                    # delete the old image from storage (if it was stored in our bucket)
                    if uploaded_filename and old_image_url and 'supabase' in old_image_url and '/products/' in old_image_url:
                        try:
                            # Extract filename from old URL
                            old_filename = old_image_url.split('/products/')[-1]
                            self.delete_product_image(f"products/{old_filename}")
                        except:
                            pass  # Don't fail the update if old image deletion fails
                    
                    return {
                        'success': True, 
                        'data': response.data[0],
                        'uploaded_filename': uploaded_filename
                    }
                else:
                    # If product update failed and we uploaded an image, clean it up
                    if uploaded_filename:
                        self.delete_product_image(uploaded_filename)
                    return {'success': False, 'error': 'Failed to update product'}
            else:
                return {'success': False, 'error': 'No data to update'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific product by ID"""
        try:
            response = self.client.table('products').select('*').eq('id', product_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting product by ID: {e}")
            return None
    
    def get_product_for_cart(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get product information specifically formatted for cart operations"""
        try:
            product = self.get_product_by_id(product_id)
            if not product:
                return None
                
            # Add seller information
            if product.get('seller_id') and product['seller_id'] is not None:
                # Get seller store name
                seller_response = self.client.table('sellers').select('store_name').eq('id', product['seller_id']).execute()
                if seller_response.data and len(seller_response.data) > 0:
                    product['seller_store_name'] = seller_response.data[0]['store_name']
                else:
                    product['seller_store_name'] = 'Unknown Seller'
            else:
                product['seller_store_name'] = 'Marivor Official'
                
            return product
        except Exception as e:
            print(f"Error getting product for cart: {e}")
            return None
    
    def validate_cart_item(self, product_id: int, quantity: int) -> Dict[str, Any]:
        """Validate cart item before adding/updating"""
        try:
            # Validate quantity
            if quantity < 1:
                return {'valid': False, 'error': 'Quantity must be at least 1'}
            if quantity > 99:
                return {'valid': False, 'error': 'Maximum quantity per item is 99'}
            
            # Get product
            product = self.get_product_for_cart(product_id)
            if not product:
                return {'valid': False, 'error': 'Product not found'}
            
            # Check stock
            if product.get('stock', 0) < quantity:
                return {'valid': False, 'error': f'Only {product.get("stock", 0)} items available in stock'}
            
            return {'valid': True, 'product': product}
            
        except Exception as e:
            return {'valid': False, 'error': f'Validation error: {str(e)}'}
    
    # Order Management Methods
    def create_order(self, user_id: int, items: List[Dict], total_price: float) -> Dict[str, Any]:
        """Create a new order"""
        try:
            order_data = {
                'user_id': user_id,
                'items': items,  # Store as JSON
                'total_price': total_price,
                'status': 'processed',  # Default status
                'created_at': datetime.utcnow().isoformat()
            }
            
            response = self.client.table('orders').insert(order_data).execute()
            return {'success': True, 'data': response.data[0] if response.data else None}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_orders_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get orders by status - Fetch all columns from orders table"""
        try:
            # Select all specific columns from orders table, filter by status
            response = self.client.table('orders').select(
                'id, created_at, user_id, order_number, status, total_amount, currency, '
                'customer_name, customer_phone, shipping_address, items, face_photo_front'
            ).eq('status', status).order('created_at', desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error getting orders by status: {e}")
            return []
    
    def get_all_orders(self) -> List[Dict[str, Any]]:
        """Get all orders - Fetch all columns from orders table"""
        try:
            # Select all specific columns from orders table
            response = self.client.table('orders').select(
                'id, created_at, user_id, order_number, status, total_amount, currency, '
                'customer_name, customer_phone, shipping_address, items, face_photo_front'
            ).order('created_at', desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error getting all orders: {e}")
            return []

    def get_active_orders(self) -> List[Dict[str, Any]]:
        """Get active orders (excluding completed ones) - For 'All Orders' view"""
        try:
            # Select orders that are not completed (pending, processing, on_delivery)
            response = self.client.table('orders').select(
                'id, created_at, user_id, order_number, status, total_amount, currency, '
                'customer_name, customer_phone, shipping_address, items, face_photo_front'
            ).neq('status', 'completed').order('created_at', desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error getting active orders: {e}")
            return []
    
    def update_order_status(self, order_id: int, status: str) -> bool:
        """Update order status - Enhanced to support all status values"""
        try:
            # Updated valid statuses to match our progression system
            valid_statuses = ['pending', 'processing', 'on_delivery', 'completed', 'cancelled']
            if status not in valid_statuses:
                print(f"Invalid status: {status}. Valid statuses: {valid_statuses}")
                return False
            
            response = self.client.table('orders').update({'status': status}).eq('id', order_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error updating order status: {e}")
            return False
    
    def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        """Get orders for a specific user with enhanced product details from items JSONB"""
        try:
            response = self.client.table('orders').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
            orders = response.data if response.data else []
            
            # Process each order to extract product details from items JSONB
            for order in orders:
                if order.get('items'):
                    try:
                        import json
                        # Parse items if it's a string, otherwise assume it's already parsed
                        items = json.loads(order['items']) if isinstance(order['items'], str) else order['items']
                        
                        # Extract product details from items array
                        product_names = []
                        seller_ids = []
                        product_ids = []
                        quantities = []
                        
                        for item in items:
                            if isinstance(item, dict):
                                # Get product name (use 'name' field from JSONB)
                                if item.get('name'):
                                    product_names.append(item['name'])
                                
                                # Get seller ID
                                if item.get('seller_id'):
                                    seller_ids.append(str(item['seller_id']))
                                
                                # Get product ID
                                if item.get('product_id'):
                                    product_ids.append(str(item['product_id']))
                                
                                # Get quantity
                                if item.get('quantity'):
                                    quantities.append(item['quantity'])
                        
                        # Add parsed data to order
                        order['parsed_items'] = {
                            'product_names': product_names,
                            'seller_ids': list(set(seller_ids)),  # Remove duplicates
                            'product_ids': product_ids,
                            'quantities': quantities,
                            'total_products': len(items)
                        }
                        
                        # Create a formatted product list string for display
                        if product_names:
                            order['formatted_products'] = ', '.join(product_names[:3])  # Show first 3 products
                            if len(product_names) > 3:
                                order['formatted_products'] += f" and {len(product_names) - 3} more"
                        else:
                            order['formatted_products'] = "No products listed"
                            
                    except (json.JSONDecodeError, TypeError) as e:
                        print(f"Error parsing items JSON for order {order.get('id', 'unknown')}: {e}")
                        order['parsed_items'] = {
                            'product_names': [],
                            'seller_ids': [],
                            'product_ids': [],
                            'total_products': 0
                        }
                        order['formatted_products'] = "Error loading product details"
                else:
                    order['parsed_items'] = {
                        'product_names': [],
                        'seller_ids': [],
                        'product_ids': [],
                        'total_products': 0
                    }
                    order['formatted_products'] = "No items data"
            
            return orders
        except Exception as e:
            print(f"Error getting user orders: {e}")
            return []
    
    # Seller Management Methods
    def create_seller_account(self, store_name: str, seller_code: str) -> Dict[str, Any]:
        """Create a new seller account"""
        try:
            seller_data = {
                'seller_code': seller_code,
                'store_name': store_name,
                'is_active': True,
                'created_at': datetime.utcnow().isoformat()
            }
            
            response = self.client.table('sellers').insert(seller_data).execute()
            return {'success': True, 'data': response.data[0] if response.data else None}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_all_sellers(self) -> List[Dict[str, Any]]:
        """Get all sellers"""
        try:
            response = self.client.table('sellers').select('*').order('created_at', desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error getting sellers: {e}")
            return []
    
    def get_seller_by_code(self, seller_code: str) -> Optional[Dict[str, Any]]:
        """Get seller by seller code"""
        try:
            response = self.client.table('sellers').select('*').eq('seller_code', seller_code).eq('is_active', True).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting seller by code: {e}")
            return None
    
    def get_seller_by_id(self, seller_id: int) -> Optional[Dict[str, Any]]:
        """Get seller by ID"""
        try:
            response = self.client.table('sellers').select('*').eq('id', seller_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting seller by ID: {e}")
            return None
    
    def update_seller(self, seller_id: int, **kwargs) -> bool:
        """Update seller details"""
        try:
            response = self.client.table('sellers').update(kwargs).eq('id', seller_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error updating seller: {e}")
            return False
    
    def deactivate_seller(self, seller_id: int) -> bool:
        """Deactivate a seller account"""
        try:
            response = self.client.table('sellers').update({'is_active': False}).eq('id', seller_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error deactivating seller: {e}")
            return False
    
    def get_seller_products(self, seller_id: int) -> List[Dict[str, Any]]:
        """Get products by seller"""
        try:
            response = self.client.table('products').select('*').eq('seller_id', seller_id).order('created_at', desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error getting seller products: {e}")
            return []
    
    def upload_store_image(self, seller_id: int, image_file_data: bytes, filename: str, content_type: str = 'image/jpeg') -> Dict[str, Any]:
        """Upload store image to Supabase storage"""
        try:
            # Generate unique filename
            file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
            unique_filename = f"store_{seller_id}_{uuid.uuid4()}.{file_extension}"
            
            # Upload to Supabase storage
            response = self.storage_client.storage.from_('store').upload(
                unique_filename, 
                image_file_data,
                file_options={'content-type': content_type}
            )
            
            if response.status_code in [200, 201]:
                # Get public URL
                public_url = self.storage_client.storage.from_('store').get_public_url(unique_filename)
                return {
                    'success': True, 
                    'url': public_url,
                    'filename': unique_filename
                }
            else:
                return {'success': False, 'error': f'Upload failed with status {response.status_code}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_seller_code(self) -> str:
        """Generate a unique 6-digit seller code"""
        import random
        while True:
            code = f"{random.randint(100000, 999999)}"
            # Check if code already exists
            existing = self.get_seller_by_code(code)
            if not existing:
                return code
    
    # Storage Methods
    def upload_face_photo(self, user_id: str, photo_data: str, direction: str) -> Optional[str]:
        """
        Upload face photo to Supabase storage
        
        Args:
            user_id: Unique user identifier
            photo_data: Base64 encoded image data
            direction: 'front', 'left', or 'right'
        
        Returns:
            Public URL of uploaded photo or None if failed
        """
        try:
            # Debug: Check photo_data type and content
            print(f"Uploading {direction} photo for user {user_id}")
            print(f"Photo data type: {type(photo_data)}")
            print(f"Photo data length: {len(photo_data) if isinstance(photo_data, str) else 'N/A'}")
            
            # Validate photo_data is a string
            if not isinstance(photo_data, str):
                print(f"Error: photo_data is not a string, it's {type(photo_data)}")
                return None
            
            if not photo_data or len(photo_data) < 100:  # Too short to be valid base64 image
                print(f"Error: photo_data is empty or too short: {len(photo_data) if photo_data else 0}")
                return None
            
            # Remove data URL prefix if present
            if ',' in photo_data:
                photo_data = photo_data.split(',')[1]
            
            # Decode base64 image
            image_bytes = base64.b64decode(photo_data)
            
            # Generate unique filename
            filename = f"{user_id}_{direction}_{int(datetime.utcnow().timestamp())}.jpg"
            file_path = f"users/{user_id}/{filename}"
            
            print(f"Uploading to path: {file_path}")
            
            # Upload to Supabase storage (with upsert to allow overwriting)
            try:
                response = self.storage_client.storage.from_(self.bucket_name).upload(
                    path=file_path,
                    file=image_bytes,
                    file_options={
                        "content-type": "image/jpeg",
                        "upsert": "true"  # String instead of boolean
                    }
                )
            except Exception as upload_error:
                # If upload fails due to existing file, try removing and re-uploading
                print(f"Upload failed, trying to remove existing file: {upload_error}")
                try:
                    self.storage_client.storage.from_(self.bucket_name).remove([file_path])
                    response = self.storage_client.storage.from_(self.bucket_name).upload(
                        path=file_path,
                        file=image_bytes,
                        file_options={
                            "content-type": "image/jpeg"
                        }
                    )
                except Exception as retry_error:
                    print(f"Retry upload also failed: {retry_error}")
                    raise upload_error
            
            print(f"Upload response: {response}")
            
            if response:
                # Get public URL
                public_url = self.storage_client.storage.from_(self.bucket_name).get_public_url(file_path)
                print(f"Generated public URL: {public_url}")
                return public_url
            else:
                print("Upload response was falsy")
                return None
            
        except Exception as e:
            print(f"Error uploading photo: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_photo_url(self, file_path: str) -> str:
        """Get public URL for a stored photo"""
        try:
            return self.client.storage.from_(self.bucket_name).get_public_url(file_path)
        except Exception as e:
            print(f"Error getting photo URL: {e}")
            return ""
    
    def delete_user_photos(self, user_id: str) -> bool:
        """Delete all photos for a user"""
        try:
            # List all files for the user
            response = self.client.storage.from_(self.bucket_name).list(f"users/{user_id}")
            
            if response:
                # Delete all files
                file_paths = [f"users/{user_id}/{file['name']}" for file in response]
                delete_response = self.client.storage.from_(self.bucket_name).remove(file_paths)
                return delete_response is not None
            
            return True
        except Exception as e:
            print(f"Error deleting user photos: {e}")
            return False
    
    def upload_product_image(self, seller_id: int, image_data: bytes, filename: str) -> str:
        """Upload product image and return public URL"""
        try:
            # Generate unique filename (without products/ prefix since we're uploading to products bucket)
            file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
            unique_filename = f"{seller_id}_{uuid.uuid4()}.{file_extension}"
            
            # Upload to products bucket
            storage_response = self.client.storage.from_('products').upload(unique_filename, image_data)
            
            # Debug: Print the response to understand its structure
            print(f"Storage response: {storage_response}")
            print(f"Response type: {type(storage_response)}")
            print(f"Response attributes: {dir(storage_response)}")
            
            # For now, assume upload was successful if we got any response
            # and try to get the public URL
            try:
                public_url = self.client.storage.from_('products').get_public_url(unique_filename)
                print(f"Generated public URL: {public_url}")
                return public_url
            except Exception as url_error:
                print(f"Error getting public URL: {url_error}")
                raise Exception(f"Upload succeeded but failed to get public URL: {url_error}")
                
        except Exception as e:
            print(f"Error uploading product image: {e}")
            raise e
    
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new order in the orders table"""
        try:
            # Get cart items
            cart_items = order_data.get('items', [])
            
            # Ensure items have all necessary information
            for item in cart_items:
                # Make sure each item has seller info if missing
                if 'seller_id' not in item and item.get('product_id'):
                    product = self.get_product_by_id(item.get('product_id'))
                    if product:
                        item['seller_id'] = product.get('seller_id')
                        item['seller_name'] = product.get('seller_name', 'Unknown Seller')
            
            # Prepare the order data for insertion (only essential columns)
            insert_data = {
                'user_id': order_data.get('user_id'),
                'order_number': order_data.get('order_number'),
                'status': order_data.get('status', 'pending'),
                'total_amount': order_data.get('total_amount', 0.0),
                'currency': order_data.get('currency', 'PHP'),
                'customer_name': order_data.get('customer_name', ''),
                'customer_phone': order_data.get('customer_phone', ''),
                'shipping_address': order_data.get('shipping_address', ''),
                'items': cart_items,  # All product info is stored here as JSONB
                'face_photo_front': order_data.get('face_photo_front')
                # Removed: seller_id, products_name, products_id (deprecated)
            }
            
            # Insert the order
            response = self.client.table('orders').insert(insert_data).execute()
            
            if response.data and len(response.data) > 0:
                print(f"Order created successfully")
                print(f"Items stored in JSONB: {len(cart_items)} items")
                return response.data[0]
            else:
                print("No data returned from order creation")
                return None
                
        except Exception as e:
            print(f"Error creating order: {e}")
            return None
    
    def create_single_seller_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a single-seller order (deprecated - use create_order instead)"""
        # Just redirect to the main create_order function for consistency
        return self.create_order(order_data)
    

    
    def get_seller_orders(self, seller_id: int) -> List[Dict[str, Any]]:
        """Get all orders for a specific seller by parsing items JSONB column"""
        try:
            # Get all orders and filter by seller_id in items JSONB
            response = self.client.table('orders').select('*').order('created_at', desc=True).execute()
            all_orders = response.data if response.data else []
            
            seller_orders = []
            for order in all_orders:
                if order.get('items'):
                    try:
                        import json
                        # Parse items if it's a string, otherwise assume it's already parsed
                        items = json.loads(order['items']) if isinstance(order['items'], str) else order['items']
                        
                        # Check if any item in this order belongs to the seller
                        for item in items:
                            if isinstance(item, dict) and item.get('seller_id') == seller_id:
                                seller_orders.append(order)
                                break  # Found matching seller, add order once and move to next order
                                
                    except (json.JSONDecodeError, TypeError) as e:
                        print(f"Error parsing items JSON for order {order.get('id', 'unknown')}: {e}")
                        continue
            
            return seller_orders
        except Exception as e:
            print(f"Error getting seller orders: {e}")
            return []
    
    def get_order_by_id(self, order_id: int) -> Dict[str, Any]:
        """Get a specific order by ID"""
        try:
            response = self.client.table('orders').select('*').eq('id', order_id).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            print(f"Error getting order: {e}")
            return {}
    
    def get_product_by_id(self, product_id: int) -> Dict[str, Any]:
        """Get a specific product by ID"""
        try:
            response = self.client.table('products').select('*').eq('id', product_id).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            print(f"Error getting product: {e}")
            return {}
    
    def update_order_status(self, order_id: int, status: str) -> bool:
        """Update order status"""
        try:
            response = self.client.table('orders').update({'status': status}).eq('id', order_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error updating order status: {e}")
            return False

# Global Supabase client instance
supabase_client = None

def get_supabase_client() -> SupabaseClient:
    """Get or create Supabase client instance"""
    global supabase_client
    if supabase_client is None:
        supabase_client = SupabaseClient()
    return supabase_client

def test_connection() -> bool:
    """Test Supabase connection"""
    try:
        client = get_supabase_client()
        # Simple test query
        response = client.client.table('users').select('id').limit(1).execute()
        return True
    except Exception as e:
        print(f"Supabase connection test failed: {e}")
        return False