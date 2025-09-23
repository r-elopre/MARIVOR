-- Supabase SQL script to set up admin panel tables
-- Run these commands in your Supabase SQL editor

-- 1. Add admin column to users table if it doesn't exist
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;

-- 2. Create orders table
CREATE TABLE IF NOT EXISTS orders (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    items JSONB NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'processed' CHECK (status IN ('processed', 'on_delivery')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- 3. Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);

-- 4. Enable Row Level Security on orders table
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- 5. Create RLS policies for orders table
-- Users can only see their own orders
CREATE POLICY "Users can view own orders" ON orders
    FOR SELECT USING (auth.uid()::text = user_id::text);

-- Users can insert their own orders
CREATE POLICY "Users can insert own orders" ON orders
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

-- Admin users can view all orders (you'll need to implement admin detection)
-- For now, we'll allow authenticated users to view all orders for admin functionality
-- You may want to restrict this further based on your admin logic

-- 6. Add some sample data (optional)
-- INSERT INTO orders (user_id, items, total_price, status) VALUES 
-- (1, '[{"name": "Fresh Salmon", "category": "Fish", "price": 799.99, "quantity": 2}]', 1599.98, 'processed'),
-- (2, '[{"name": "Organic Spinach", "category": "Vegetable", "price": 249.99, "quantity": 1}]', 249.99, 'on_delivery');

-- 7. Update function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc'::text, NOW());
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 8. Create trigger for orders table
DROP TRIGGER IF EXISTS update_orders_updated_at ON orders;
CREATE TRIGGER update_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 9. Grant necessary permissions
GRANT ALL ON orders TO authenticated;
GRANT ALL ON orders TO anon;