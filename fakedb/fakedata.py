import sqlite3
import random
from faker import Faker

# Initialize Faker for fake data generation
fake = Faker()

# Connect to SQLite (creates file if not exists)
conn = sqlite3.connect("test_db.sqlite")
cursor = conn.cursor()

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT,
    country TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    name TEXT,
    category TEXT,
    price REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    order_date TEXT,
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY(product_id) REFERENCES products(product_id)
)
""")

# Populate customers table (500 records)
for _ in range(1000):
    cursor.execute("""
    INSERT INTO customers (name, email, country) VALUES (?, ?, ?)
    """, (fake.name(), fake.email(), fake.country()))

# Populate products table (100 records)
categories = ['Electronics', 'Books', 'Clothing', 'Toys', 'Home', 'Furniture',]
for _ in range(1500):
    cursor.execute("""
    INSERT INTO products (name, category, price) VALUES (?, ?, ?)
    """, (fake.word().capitalize(), random.choice(categories), round(random.uniform(10, 500), 2)))

# Populate orders table (500+ records)
for _ in range(1500):
    cursor.execute("""
    INSERT INTO orders (customer_id, product_id, quantity, order_date) VALUES (?, ?, ?, ?)
    """, (
        random.randint(1, 1000),  # customer_id
        random.randint(1, 1500),  # product_id
        random.randint(1, 100),    # quantity
        fake.date_this_year()    # order_date
    ))

# Commit and close
conn.commit()
conn.close()

print("SQLite DB created successfully with sample data!")
