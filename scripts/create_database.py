"""
Database creation script for Marivor app
Run this to create all the tables needed for your fish & vegetable marketplace
"""

import sqlite3
import os
from datetime import datetime
import hashlib

def create_database():
    # Create database file
    db_path = 'marivor.db'
    
    # Connect to SQLite database (creates file if doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🗄️ Creating Marivor database...")
    
    # 1. Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone_number VARCHAR(15) UNIQUE NOT NULL,
        is_verified BOOLEAN DEFAULT 0,
        is_admin BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
    ''')
    print("✅ Users table created")
    
    # 2. OTP table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS otp_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone_number VARCHAR(15) NOT NULL,
        otp_code_hash VARCHAR(64) NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        attempts INTEGER DEFAULT 0,
        is_used BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("✅ OTP codes table created")
    
    # 3. Products table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        category VARCHAR(20) NOT NULL CHECK (category IN ('Fish', 'Vegetable')),
        price DECIMAL(10,2) NOT NULL,
        stock INTEGER DEFAULT 0,
        image_url VARCHAR(255),
        description TEXT,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("✅ Products table created")
    
    # 4. Orders table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_price DECIMAL(10,2) NOT NULL,
        status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'preparing', 'out_for_delivery', 'delivered', 'cancelled')),
        delivery_address TEXT,
        phone_number VARCHAR(15),
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    print("✅ Orders table created")
    
    # 5. Order Items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price DECIMAL(10,2) NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    ''')
    print("✅ Order items table created")
    
    # 6. Cart table (for persistent cart storage)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cart_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (product_id) REFERENCES products(id),
        UNIQUE(user_id, product_id)
    )
    ''')
    print("✅ Cart items table created")
    
    # Insert sample data
    print("\n📦 Adding sample data...")
    
    # Sample products
    sample_products = [
        ('Fresh Salmon', 'Fish', 25.99, 50, '/static/images/salmon.jpg', 'Fresh Atlantic salmon, perfect for grilling'),
        ('Tuna Steaks', 'Fish', 18.50, 30, '/static/images/tuna.jpg', 'Premium tuna steaks, sushi grade'),
        ('Sea Bass', 'Fish', 22.00, 25, '/static/images/seabass.jpg', 'Whole sea bass, fresh catch'),
        ('Organic Tomatoes', 'Vegetable', 3.99, 100, '/static/images/tomatoes.jpg', 'Fresh organic tomatoes'),
        ('Green Spinach', 'Vegetable', 2.50, 80, '/static/images/spinach.jpg', 'Fresh baby spinach leaves'),
        ('Bell Peppers', 'Vegetable', 4.25, 60, '/static/images/peppers.jpg', 'Mixed color bell peppers'),
        ('Fresh Broccoli', 'Vegetable', 3.75, 45, '/static/images/broccoli.jpg', 'Organic broccoli crowns'),
        ('Red Snapper', 'Fish', 28.99, 20, '/static/images/snapper.jpg', 'Whole red snapper, market fresh')
    ]
    
    cursor.executemany('''
    INSERT OR IGNORE INTO products (name, category, price, stock, image_url, description)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', sample_products)
    
    # Create admin user (you can change this phone number)
    admin_phone = "+1234567890"  # Change this to your phone number
    cursor.execute('''
    INSERT OR IGNORE INTO users (phone_number, is_verified, is_admin)
    VALUES (?, 1, 1)
    ''', (admin_phone,))
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"\n🎉 Database created successfully!")
    print(f"📁 Database file: {os.path.abspath(db_path)}")
    print(f"📊 Sample products added: {len(sample_products)}")
    print(f"👤 Admin user created with phone: {admin_phone}")
    print("\n🔍 To view your database, you can use:")
    print("1. DB Browser for SQLite (free GUI tool)")
    print("2. sqlite3 command line")
    print("3. VS Code SQLite extension")

if __name__ == "__main__":
    create_database()