import sqlite3

conn = sqlite3.connect("webshop.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS shoplist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item TEXT NOT NULL,
    price REAL NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item TEXT NOT NULL,
    price REAL NOT NULL)"""
)

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT,
    price REAL,
    image_url TEXT,
    description TEXT,
    category TEXT 
)
""")

cursor.execute("DELETE FROM products")
cursor.execute("""
    INSERT OR IGNORE INTO products (id, name, price, image_url, description, category) VALUES
    (1, 'Megadeth - Megadeth', 19.99, 'images/product1.jpeg', NULL, 'cd'),
    (2, 'Dookie - Green Day', 19.99, 'images/product2.jpeg', NULL, 'cd'),
    (3, 'Nirvana shirt', 19.99, 'images/product3.jpeg', NULL, 't-shirt'),
    (4, 'Tool shirt', 19.99, 'images/product4.jpeg', NULL, 't-shirt'),
    (5, 'American idiot - Green Day', 19.99, 'images/product5.jpeg', NULL, 'cd'),
    (6, 'Magma - Gojira', 19.99, 'images/product6.jpeg', NULL, 'cd'),
    (7, 'Octavarium - Dream Theater', 19.99, 'images/product7.jpeg', NULL, 'cd'),
    (8, 'Metropolis pt. 2 - Dream theater', 19.99, 'images/product8.jpeg', NULL, 'cd'),
    (9, 'Dark side of the moon - Pink Floyd', 19.99, 'images/product9.jpeg', NULL, 'cd'),
    (10, 'Black gives way to blue', 19.99, 'images/product10.jpeg', NULL, 'cd'),
    (11, 'Kickstart my heart - mötley cruë', 19.99, 'images/product11.jpeg', NULL, 'cd'),
    (12, 'Extension of the wish - Andromeda', 19.99, 'images/product12.jpeg', NULL, 'cd'),
    (13, 'Lateralus - TOOL', 19.99, 'images/product13.jpeg', NULL, 'cd'),
    (14, 'Would? - Alice In Chains', 19.99, 'images/product14.jpeg', NULL, 'cd'),
    (15, 'Moving pictures - Rush', 19.99, 'images/product15.jpeg', NULL, 'cd'),
    (16, 'Holy diver - Dio', 19.99, 'images/product16.jpeg', NULL, 'cd'),
    (17, 'Song for the deaf - Queens Of The Stone Age', 19.99, 'images/product17.jpeg', NULL, 'cd'),
    (18, 'From mars to sirius - Gojira', 19.99, 'images/product18.jpeg', NULL, 'cd')
""")

conn.commit()