import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)
DATABASE = 'webshop.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def get_products():
    conn = get_db_connection()
    products = conn.execute('SELECT id, name, price, image_url FROM products').fetchall()
    conn.close()
    return products


@app.route('/')
def index():
    products = get_products()
    return render_template('main.html', products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    return render_template('singup.html')

@app.route('/shoplist', methods=['GET', 'POST'])
def shoplist():
    products = get_products()
    return render_template('shoplist.html', products=products)

@app.route('/search', methods=['GET', 'POST'])
def search():
    query = request.args.get('q')  # gets the search term
    return render_template('search.html', query=query)
if __name__ == '__main__':
    app.run(debug=True)