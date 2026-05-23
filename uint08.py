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
    image_url TEXT
)
""")

cursor.execute("""
    INSERT INTO products (id, name, price, image_url) VALUES
    (1, 'Megadeth - Megadeth', 19.99, 'images/product1.jpeg'),
    (2, 'Dookie - Green Day', 19.99, 'images/product2.jpeg'),
    (3, 'Nirvana shirt', 19.99, 'images/product3.jpeg'),
    (4, 'Tool shirt', 19.99, 'images/product4.jpeg'),
    (5, 'American idiot - Green Day', 19.99, 'images/product5.jpeg'),
    (6, 'Magma - Gojira', 19.99, 'images/product6.jpeg'),
    (7, 'Octavarium - Dream Theater', 19.99, 'images/product7.jpeg'),
    (8, 'Metropolis pt. 2 - Dream theater', 19.99, 'images/product8.jpeg'),
    (9, 'Dark side of the moon - Pink Floyd', 19.99, 'images/product9.jpeg'),
    (10, 'Black gives way to blue', 19.99, 'images/product10.jpeg'),
    (11, 'Kickstart my heart - mötley cruë', 19.99, 'images/product11.jpeg'),
    (12, 'Extension of the wish - Andromeda', 19.99, 'images/product12.jpeg')
""")

conn.commit()