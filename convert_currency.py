"""
Currency Conversion Utility - USD to PHP
Utility functions for converting product prices from USD to Philippine Peso

NOTE: This script is now for reference only since we're using Supabase.
All products should be added directly in PHP currency via the admin panel.

Exchange rate used: 1 USD = 56 PHP (approximate, update as needed)
"""

from supabase_utils import get_supabase_client

# Exchange rate (1 USD = X PHP)
USD_TO_PHP_RATE = 56.0

def convert_supabase_prices():
    """Convert prices in Supabase from USD to PHP"""
    print("🇵🇭 Currency Conversion: USD → PHP for Supabase")
    print("=" * 50)
    
    try:
        client = get_supabase_client()
        
        # Get all products
        products = client.get_all_products()
        
        if not products:
            print("No products found to convert.")
            return
        
        print(f"Converting {len(products)} products from USD to PHP...")
        print(f"Exchange rate: 1 USD = {USD_TO_PHP_RATE} PHP")
        print("-" * 50)
        
        for product in products:
            product_id = product['id']
            name = product['name']
            usd_price = product['price']
            php_price = round(usd_price * USD_TO_PHP_RATE, 2)
            
            # Update the price in Supabase
            success = client.update_product(product_id, price=php_price)
            
            if success:
                print(f"  ✅ {name}: ${usd_price:.2f} → ₱{php_price:.2f}")
            else:
                print(f"  ❌ Failed to update {name}")
        
        print("-" * 50)
        print(f"✅ Currency conversion complete!")
        
    except Exception as e:
        print(f"❌ Error converting prices: {e}")

def create_sample_php_products():
    """Add sample products with PHP pricing to Supabase"""
    print("Creating sample products with PHP pricing in Supabase...")
    
    sample_products = [
        # Fish products (prices in PHP)
        ("Fresh Salmon", "Fish", 899.00, 25, True),
        ("Premium Tuna", "Fish", 699.00, 20, True),
        ("Sea Bass Fillet", "Fish", 799.00, 15, True),
        ("Red Snapper", "Fish", 649.00, 18, True),
        
        # Vegetable products (prices in PHP)
        ("Organic Spinach", "Vegetable", 149.00, 50, False),
        ("Fresh Tomatoes", "Vegetable", 89.00, 60, False),
        ("Bell Peppers", "Vegetable", 199.00, 40, False),
        ("Fresh Broccoli", "Vegetable", 169.00, 35, False),
    ]
    
    try:
        client = get_supabase_client()
        
        for name, category, price, stock, unit in sample_products:
            result = client.add_product(name, category, price, stock)
            
            if result['success']:
                print(f"  ✅ Added: {name} - ₱{price:.2f}")
            else:
                print(f"  ❌ Failed to add: {name} - {result.get('error', 'Unknown error')}")
        
        print(f"✅ Sample products creation complete!")
        
    except Exception as e:
        print(f"❌ Error creating sample products: {e}")

if __name__ == "__main__":
    print("🇵🇭 Supabase Currency Conversion Utility")
    print("=" * 50)
    print("💡 All products should now be added directly in PHP via the admin panel.")
    print("💡 This script is for converting existing USD prices only.")
    print("")
    
    choice = input("Convert existing USD prices to PHP? (y/n): ").lower().strip()
    if choice == 'y':
        convert_supabase_prices()
    else:
        print("No conversion performed.")