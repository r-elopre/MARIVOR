import sqlite3

# Connect to database
conn = sqlite3.connect('marivor.db')
cursor = conn.cursor()

# Show tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("📊 Database Tables Created:")
for table in tables:
    print(f"  ✅ {table[0]}")

print("\n🐟🥬 Sample Products:")
cursor.execute("SELECT name, category, price, stock FROM products")
products = cursor.fetchall()

for product in products:
    name, category, price, stock = product
    emoji = "🐟" if category == "Fish" else "🥬"
    print(f"  {emoji} {name} - ${price} (Stock: {stock})")

conn.close()
print(f"\n✅ Database is working perfectly!")
print(f"📁 Location: marivor.db")