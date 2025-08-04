import sqlite3
import pandas as pd
import random
import datetime
import os

def setup_database():
    """
    Creates the database and populates it with data.
    """
    if os.path.exists('sales.db'):
        os.remove('sales.db')
        print("Old database deleted. Starting fresh.")
    
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL,
        price REAL NOT NULL,
        last_cost_per_unit REAL NOT NULL,
        stock_quantity INTEGER NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        purchase_date TEXT NOT NULL,
        quantity_added INTEGER NOT NULL,
        cost_per_unit REAL NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sales (
        sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        sale_date TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    )
    ''')
    
    products = [
        ('Pen', 10, 5, 200), ('Notebook (A5)', 30, 15, 150), ('Pencil', 5, 2, 500), 
        ('Eraser', 3, 4, 400), ('Highlighter (Yellow)', 15, 7, 100), ('Folder', 20, 10, 75), ('Stapler', 45, 20, 50), 
        ('Sticky Notes', 8, 4, 300), ('Whiteboard Markers (Pack)', 25, 12, 60), 
        ('Correction Tape', 12, 6, 120), ('Scissors', 18, 9, 80), ('Glue Stick', 7, 3, 150),
        ('Ruler (30cm)', 6, 3, 250), ('Protractor', 9, 4, 70), ('Compass Set', 22, 10, 40),
        ('Sharpener', 4, 2, 200), ('Binder Clips', 10, 5, 150), ('Paper Clips', 5, 2, 500),
        ('Index Cards', 9, 4, 250), ('Legal Pad', 18, 9, 100), ('Desk Organizer', 50, 25, 40),
        ('Calculator (Basic)', 35, 15, 30), ('USB Drive (32GB)', 60, 65, 20), 
        ('Laptop Sleeve (15")', 80, 40, 15), ('Mouse Pad', 12, 6, 100), ('Ballpoint Pen (Set)', 25, 10, 120),
        ('Mechanical Pencil', 15, 7, 80), ('Colored Pencils (Set)', 28, 14, 90),
        ('Markers (Set of 12)', 20, 9, 110), ('Drawing Pad', 15, 7, 75), ('Sketchbook', 25, 12, 60),
        ('Water Bottle', 40, 20, 50), ('Lunch Box', 35, 18, 45), ('Backpack', 150, 75, 25),
        ('Posters (Pack)', 25, 12, 80), ('Push Pins', 5, 2, 300), ('Rubber Bands', 3, 1, 500),
        ('Laminator', 120, 60, 10), ('Document Shredder', 200, 100, 5), ('Ink Cartridge', 90, 45, 20)
    ]
    cursor.executemany('INSERT INTO products (product_name, price, last_cost_per_unit, stock_quantity) VALUES (?, ?, ?, ?)', products)

    num_products = len(products)
    num_sales = 500
    sales_data = []
    start_date = datetime.date(2025, 1, 1)
    
    for _ in range(num_sales):
        random_product_id = random.randint(1, num_products)
        random_quantity = random.randint(1, 25)
        random_date_offset = random.randint(0, 180)
        sale_date = (start_date + datetime.timedelta(days=random_date_offset)).strftime('%Y-%m-%d')
        sales_data.append((random_product_id, sale_date, random_quantity))

    cursor.executemany('INSERT INTO sales (product_id, sale_date, quantity) VALUES (?, ?, ?)', sales_data)
    
    print(f"Database setup complete. Data for {num_products} products and {num_sales} sales records inserted.")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    if os.path.exists('sales.db'):
        os.remove('sales.db')
        print("Old database deleted. Starting fresh.")
    setup_database()