"""
Currency Conversion Script - USD to PHP
Converts existing product prices from USD to Philippine Peso

Note: Run this script if you have existing products in USD that need to be converted to PHP
Exchange rate used: 1 USD = 56 PHP (approximate, update as needed)
"""

import sqlite3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Exchange rate (1 USD = X PHP)
USD_TO_PHP_RATE = 56.0

def convert_sqlite_prices():
    """Convert prices in SQLite database from USD to PHP"""
    DATABASE = os.getenv('DATABASE_URL', 'sqlite:///marivor.db').replace('sqlite:///', '')
    
    if not os.path.exists(DATABASE):
        print(f"Database file {DATABASE} not found. Skipping SQLite conversion.")
        return
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        # Check if products table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        if not cursor.fetchone():
            print("Products table not found in SQLite database.")
            return
        
        # Get all products
        cursor.execute("SELECT id, name, price FROM products")
        products = cursor.fetchall()
        
        if not products:
            print("No products found to convert.")
            return
        
        print(f"Converting {len(products)} products from USD to PHP...")
        print(f"Exchange rate: 1 USD = {USD_TO_PHP_RATE} PHP")
        print("-" * 50)
        
        for product_id, name, usd_price in products:
            php_price = round(usd_price * USD_TO_PHP_RATE, 2)
            
            # Update the price
            cursor.execute("UPDATE products SET price = ? WHERE id = ?", (php_price, product_id))
            
            print(f"  {name}: ${usd_price:.2f} → ₱{php_price:.2f}")
        
        conn.commit()
        print("-" * 50)
        print(f"✅ Successfully converted {len(products)} products to PHP!")
        
    except Exception as e:
        print(f"❌ Error converting prices: {e}")
        conn.rollback()
    finally:
        conn.close()

def create_php_sample_products():
    """Create sample products with PHP pricing"""
    DATABASE = os.getenv('DATABASE_URL', 'sqlite:///marivor.db').replace('sqlite:///', '')
    
    sample_products = [
        # Fish products (prices in PHP)
        ("Fresh Salmon", "Fish", 899.00, 25, "/static/images/salmon.jpg"),
        ("Premium Tuna", "Fish", 699.00, 20, "/static/images/tuna.jpg"),
        ("Sea Bass Fillet", "Fish", 799.00, 15, "/static/images/seabass.jpg"),
        ("Red Snapper", "Fish", 649.00, 18, "/static/images/snapper.jpg"),
        
        # Vegetable products (prices in PHP)
        ("Organic Spinach", "Vegetable", 149.00, 50, "/static/images/spinach.jpg"),
        ("Fresh Tomatoes", "Vegetable", 89.00, 60, "/static/images/tomatoes.jpg"),
        ("Bell Peppers", "Vegetable", 199.00, 40, "/static/images/peppers.jpg"),
        ("Fresh Broccoli", "Vegetable", 169.00, 35, "/static/images/broccoli.jpg"),
    ]
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        # Check if products table exists and is empty
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"Products table already has {count} products. Skipping sample product creation.")
            return
        
        print("Creating sample products with PHP pricing...")
        
        for name, category, price, stock, image_url in sample_products:
            cursor.execute("""
                INSERT INTO products (name, category, price, stock, image_url, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, 1, datetime('now'))
            """, (name, category, price, stock, image_url))
            
            print(f"  Added: {name} - ₱{price:.2f}")
        
        conn.commit()
        print(f"✅ Successfully created {len(sample_products)} sample products with PHP pricing!")
        
    except Exception as e:
        print(f"❌ Error creating sample products: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🇵🇭 Currency Conversion: USD → PHP")
    print("=" * 40)
    
    # First, try to convert existing products
    convert_sqlite_prices()
    
    print("\n" + "=" * 40)
    
    # Then, create sample products if database is empty
    create_php_sample_products()
    
    print("\n✅ Currency conversion complete!")
    print("💡 Remember to update your Supabase products table with PHP pricing as well.")