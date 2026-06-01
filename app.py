import os
import sqlite3
import uuid
from flask import Flask, render_template, request, session, url_for, redirect
import bcrypt
from werkzeug.utils import secure_filename

app = Flask(__name__)
DATABASE = 'webshop.db'
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'images', 'avatars')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.secret_key = 'secret_key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

# Initialize database
def init_db():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password BLOB NOT NULL,
            avatar TEXT NOT NULL
        )
    ''')
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'avatar' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN avatar TEXT NOT NULL DEFAULT 'images/default_avatar.svg'")
        conn.commit()
    conn.commit()
    conn.close()

# connect the database
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_avatar(file, username):
    extension = file.filename.rsplit('.', 1)[1].lower()
    safe_name = secure_filename(f"{username}_{uuid.uuid4().hex}.{extension}")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
    file.save(file_path)
    return f"images/avatars/{safe_name}"

@app.context_processor
def inject_user():
    return {
        'logged_in': 'user_id' in session,
        'current_username': session.get('username'),
        'current_avatar': session.get('avatar'),
    }

# select the products from the database
def get_products():
    conn = get_db_connection()
    products = conn.execute('SELECT id, name, price, image_url FROM products').fetchall()
    conn.close()
    return products

# main page
@app.route('/')
def index():
    products = get_products()
    return render_template('main.html', products=products)

# logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# login page 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return render_template('login.html', error='Username and password required')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone() # ? prevents SQL injection
        conn.close()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['avatar'] = user['avatar'] if 'avatar' in user.keys() else 'images/default_avatar.svg'
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

# signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        avatar_file = request.files.get('avatar')

        if not username or not password:
            return render_template('signup.html', error='Username and password required')
        
        if password != password_confirm:
            return render_template('signup.html', error='Passwords do not match')

        avatar_path = 'images/default_avatar.svg'
        if avatar_file and avatar_file.filename:
            if not allowed_file(avatar_file.filename):
                return render_template('signup.html', error='Allowed image types: png, jpg, jpeg, gif')
            avatar_path = save_avatar(avatar_file, username)

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, password, avatar) VALUES (?, ?, ?)', (username, hashed, avatar_path))
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            return render_template('signup.html', error='Username already exists')

        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    if user is None:
        conn.close()
        session.clear()
        return redirect(url_for('login'))

    error = None
    success = None

    if request.method == 'POST':
        avatar_file = request.files.get('avatar')
        if not avatar_file or not avatar_file.filename:
            error = 'Please choose an image to upload.'
        elif not allowed_file(avatar_file.filename):
            error = 'Allowed image types: png, jpg, jpeg, gif'
        else:
            avatar_path = save_avatar(avatar_file, user['username'])
            conn.execute('UPDATE users SET avatar = ? WHERE id = ?', (avatar_path, user['id']))
            conn.commit()
            session['avatar'] = avatar_path
            success = 'Profile picture updated successfully.'
            user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    conn.close()
    return render_template('profile.html', user=user, error=error, success=success)

@app.route('/shoplist', methods=['GET', 'POST'])
def shoplist():
    products = get_products()
    return render_template('shoplist.html', products=products)

# search page
@app.route('/search', methods=['GET', 'POST'])
def search():
    query = request.args.get('q')  # gets the search term
    return render_template('search.html', query=query)

# product page
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    if product is None:
        return "Product not found", 404
    return render_template('product.html', product=product)

if __name__ == '__main__':
    init_db()  # Initialize database
    app.run(debug=True)